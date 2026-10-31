"""LangGraph resolution agent.

message turn:  understand → investigate → policy → plan → (act → verify) → respond
confirm turn:  act → verify → respond      (pending actions restored from the conversation)
"""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent import authority, brain
from app.agent.events import emit, step
from app.agent.facts import investigate
from app.agent.state import ActionRecord, AgentState
from app.rag.retrieve import retrieve
from app.tools import registry

MAX_VERIFY_RETRIES = 1


async def understand_node(state: AgentState) -> dict[str, Any]:
    step("understand", "running", "Reading your message")
    intent, used = await brain.understand(
        state["user_message"], state.get("history", []), state.get("previous", {}), state["conversation_id"]
    )
    out: dict[str, Any] = {"intent": intent.model_dump(), "brain": used}
    if intent.needs_clarification:
        out["outcome"] = "asked"
        out["plan"] = {
            "decision": "ask",
            "question": intent.clarifying_question,
            "rationale": "",
            "actions": [],
        }
    step("understand", "done", intent.summary, intent=intent.intent, brain=used)
    return out


async def investigate_node(state: AgentState) -> dict[str, Any]:
    step("investigate", "running", "Checking your account")
    facts = await investigate(state["intent"], state["customer_id"])
    target = facts.get("target_order")
    d = facts["derived"]
    detail = "Looked up your account"
    if target:
        detail = f"Order {target['order_id']}: {target['status']}"
        if d.get("days_since_delivery") is not None:
            detail += f", delivered {d['days_since_delivery']} days ago"
        if d.get("shipment_assessment") in ("lost", "delayed"):
            detail += f", no tracking update for {d.get('business_days_since_last_scan')} business days"
    if d.get("duplicate_captured_payments"):
        detail += " · duplicate charge found"
    if d.get("membership_status"):
        detail = f"Velora Club: {d['membership_status']}" + (f" · {detail}" if target else "")
    step("investigate", "done", detail, calls=facts["calls"])
    return {"facts": facts}


async def policy_node(state: AgentState) -> dict[str, Any]:
    step("policy", "running", "Checking Velora policy")
    intent = state["intent"]
    chunks = await retrieve(f"{intent['summary']} {intent['search_query']}", k=4, audience="customer")
    policies = [c.to_dict() for c in chunks]
    step(
        "policy",
        "done",
        ", ".join(dict.fromkeys(c.doc_title for c in chunks)),
        citations=[c.cite() for c in chunks],
    )
    return {"policies": policies}


async def plan_node(state: AgentState) -> dict[str, Any]:
    step("plan", "running", "Deciding on the best fix")
    plan, used = await brain.plan(
        state["intent"],
        state["facts"],
        state.get("policies", []),
        state.get("previous", {}),
        state.get("history", []),
        state["conversation_id"],
    )
    actions, notes = authority.enforce(
        [a.model_dump() for a in plan.actions], state["facts"], state["conversation_id"]
    )
    decision = plan.decision
    if decision in ("act", "escalate") and not actions:
        decision = "inform"

    outcome = {"ask": "asked", "inform": "answered", "decline": "not_allowed"}.get(decision)
    if actions:
        confirm = any(a["needs_confirmation"] for a in actions)
        for a in actions:
            a["needs_confirmation"] = confirm  # the plan is approved as one unit
            a["action_id"] = await registry.propose(
                a["tool"], a["args"], conversation_id=state["conversation_id"], needs_confirmation=confirm
            )
        if confirm:
            outcome = "awaiting_confirmation"
            emit("action_proposed", actions=[_public(a) for a in actions])

    recs = (state["facts"].get("recommendations") or {}).get("recommendations")
    if plan.offer_recommendations and recs:
        emit("recommendations", provider=state["facts"]["recommendations"]["provider"], items=recs)

    plan_dict = plan.model_dump()
    plan_dict["decision"] = decision
    plan_dict["notes"] = notes
    step(
        "plan",
        "done",
        plan.rationale,
        decision=decision,
        citations=plan.policy_citations,
        brain=used,
        actions=[a["title"] for a in actions],
    )
    update: dict[str, Any] = {"plan": plan_dict, "actions": actions}
    if outcome:
        update["outcome"] = outcome
    return update


def _public(a: ActionRecord) -> dict[str, Any]:
    return {
        k: a.get(k)
        for k in (
            "action_id",
            "tool",
            "title",
            "description",
            "amount_cents",
            "needs_confirmation",
            "status",
            "result",
            "error",
            "verification",
        )
    }


async def act_node(state: AgentState) -> dict[str, Any]:
    actions = [dict(a) for a in state.get("actions", [])]
    if state.get("mode") == "confirm" and not state.get("approved"):
        for a in actions:
            if a["status"] == "proposed":
                a["status"] = "declined"
                await registry.set_status(a["action_id"], "declined")
        step("act", "done", "Nothing changed: you declined")
        return {"actions": actions, "outcome": "declined"}

    step("act", "running", "Taking action")
    for a in actions:
        if a["status"] != "proposed":
            continue
        await registry.set_status(a["action_id"], "approved")
        res = await registry.execute(
            a["action_id"],
            customer_id=state["customer_id"],
            conversation_id=state["conversation_id"],
            verify_after=False,
        )
        a["status"] = "done" if res["ok"] else "failed"
        a["result"] = res.get("result")
        a["error"] = res.get("error")
        emit("action_done", action=_public(a))
    done = sum(a["status"] == "done" for a in actions)
    step("act", "done", f"{done} of {len(actions)} action(s) completed")
    return {"actions": actions}


async def verify_node(state: AgentState) -> dict[str, Any]:
    step("verify", "running", "Double-checking it worked")
    actions = [dict(a) for a in state.get("actions", [])]
    problems = []
    for a in actions:
        if a["status"] != "done":
            if a["status"] == "failed":
                problems.append(a)
            continue
        verification = await registry.verify_action(a["action_id"])
        for _ in range(MAX_VERIFY_RETRIES):
            if verification["ok"]:
                break
            verification = await registry.verify_action(a["action_id"])
        a["verification"] = verification
        emit(
            "verified",
            action_id=a["action_id"],
            title=a["title"],
            ok=verification["ok"],
            checks=verification["checks"],
        )
        if not verification["ok"]:
            problems.append(a)

    outcome = "resolved"
    if problems and not any(a["tool"] == "escalate_to_human" for a in actions):
        summary = "; ".join(
            f"{a['title']}: {(a.get('error') or {}).get('message', 'verification failed')}" for a in problems
        )
        args = {"reason": "verification_failed", "summary": summary[:500]}
        title, description = authority.describe("escalate_to_human", args, state.get("facts", {}))
        esc = ActionRecord(
            tool="escalate_to_human", args=args, reason="Automatic handoff", title=title, description=description,
            amount_cents=0, needs_confirmation=False, status="proposed",
        )  # fmt: skip
        esc["action_id"] = await registry.propose(
            "escalate_to_human", args, conversation_id=state["conversation_id"], needs_confirmation=False
        )
        res = await registry.execute(
            esc["action_id"], customer_id=state["customer_id"], conversation_id=state["conversation_id"]
        )
        esc["status"] = "done" if res["ok"] else "failed"
        esc["result"], esc["verification"] = res.get("result"), res.get("verification")
        emit("action_done", action=_public(esc))
        actions.append(esc)
        outcome = "partially_resolved" if any(a["status"] == "done" for a in actions[:-1]) else "escalated"
    elif any(a["tool"] == "escalate_to_human" and a["status"] == "done" for a in actions):
        outcome = "escalated"

    ok = sum(1 for a in actions if (a.get("verification") or {}).get("ok"))
    step("verify", "done", f"{ok} of {len(actions)} verified")
    return {"actions": actions, "outcome": outcome}


async def respond_node(state: AgentState) -> dict[str, Any]:
    step("respond", "running", "Writing reply")
    parts: list[str] = []
    async for chunk in brain.respond(dict(state)):
        parts.append(chunk)
        emit("token", text=chunk)
    step("respond", "done", "")
    return {"reply": "".join(parts)}


def _route_start(state: AgentState) -> str:
    return "act" if state.get("mode") == "confirm" else "understand"


def _after_understand(state: AgentState) -> str:
    return "respond" if state.get("outcome") == "asked" else "investigate"


def _after_plan(state: AgentState) -> str:
    return "respond" if state.get("outcome") else "act"


def _after_act(state: AgentState) -> str:
    return "respond" if state.get("outcome") == "declined" else "verify"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("understand", understand_node)
    g.add_node("investigate", investigate_node)
    g.add_node("policy", policy_node)
    g.add_node("plan", plan_node)
    g.add_node("act", act_node)
    g.add_node("verify", verify_node)
    g.add_node("respond", respond_node)
    g.add_conditional_edges(START, _route_start, {"act": "act", "understand": "understand"})
    g.add_conditional_edges(
        "understand", _after_understand, {"respond": "respond", "investigate": "investigate"}
    )
    g.add_edge("investigate", "policy")
    g.add_edge("policy", "plan")
    g.add_conditional_edges("plan", _after_plan, {"respond": "respond", "act": "act"})
    g.add_conditional_edges("act", _after_act, {"respond": "respond", "verify": "verify"})
    g.add_edge("verify", "respond")
    g.add_edge("respond", END)
    return g.compile()


GRAPH = build_graph()
