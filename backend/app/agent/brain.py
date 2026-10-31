"""Brain = understand / plan / respond. LLM-backed with automatic fallback to the rule brain."""

import json
from collections.abc import AsyncIterator
from typing import Any

from app.agent import rules
from app.agent.events import emit
from app.agent.prompts import PLAN_INSTRUCTIONS, RESPOND_INSTRUCTIONS, UNDERSTAND_INSTRUCTIONS, system_prompt
from app.agent.schemas import Intent, Plan
from app.config import get_settings
from app.llm.client import BudgetExceeded, LlmUnavailable, complete_json, stream_text


def llm_enabled() -> bool:
    s = get_settings()
    return s.llm_mode != "mock" and bool(s.anthropic_api_key)


def _fallback_notice(node: str, err: Exception) -> None:
    kind = "budget" if isinstance(err, BudgetExceeded) else "fallback"
    emit(
        "notice",
        kind=kind,
        node=node,
        message="Using offline reasoning for this step.",
        detail=str(err)[:200],
    )


def _history_text(history: list[dict[str, str]]) -> str:
    return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history[-8:]) or "(no earlier messages)"


def _compact_facts(facts: dict[str, Any]) -> dict[str, Any]:
    """Drop noise to keep the plan prompt small (cost)."""
    out = {k: v for k, v in facts.items() if k not in ("calls",) and v not in (None, [], {})}
    target = out.get("target_order")
    if target and target.get("shipment"):
        target = {**target, "shipment": {k: v for k, v in target["shipment"].items() if k != "events"}}
        out["target_order"] = target
    return out


async def understand(
    message: str, history: list[dict[str, str]], previous: dict[str, Any], conversation_id: str
) -> tuple[Intent, str]:
    if llm_enabled():
        user = (
            f"{UNDERSTAND_INSTRUCTIONS}\n\n<previous_turn_context>\n{json.dumps(previous, default=str)}\n"
            f"</previous_turn_context>\n\n<conversation>\n{_history_text(history)}\n</conversation>\n\n"
            f"<latest_customer_message>\n{message}\n</latest_customer_message>"
        )
        try:
            intent = await complete_json(
                node="understand",
                system=system_prompt(),
                user=user,
                schema=Intent,
                max_tokens=700,
                conversation_id=conversation_id,
            )
            return intent, "llm"
        except (LlmUnavailable, BudgetExceeded, ValueError) as e:
            _fallback_notice("understand", e)
    return rules.understand(message, previous), "rules"


async def plan(
    intent: dict[str, Any],
    facts: dict[str, Any],
    policies: list[dict[str, Any]],
    previous: dict[str, Any],
    history: list[dict[str, str]],
    conversation_id: str,
) -> tuple[Plan, str]:
    if llm_enabled():
        policy_text = "\n\n".join(f"[{p['doc_title']} › {p['heading']}]\n{p['text']}" for p in policies)
        user = (
            f"{PLAN_INSTRUCTIONS}\n\n<intent>\n{json.dumps(intent)}\n</intent>\n\n"
            f"<facts>\n{json.dumps(_compact_facts(facts), default=str)}\n</facts>\n\n"
            f"<policy>\n{policy_text}\n</policy>\n\n"
            f"<previous_turn_context>\n{json.dumps(previous, default=str)}\n</previous_turn_context>\n\n"
            f"<conversation>\n{_history_text(history)}\n</conversation>"
        )
        try:
            result = await complete_json(
                node="plan",
                system=system_prompt(),
                user=user,
                schema=Plan,
                max_tokens=3000,
                conversation_id=conversation_id,
                effort="low",
            )
            return result, "llm"
        except (LlmUnavailable, BudgetExceeded, ValueError) as e:
            _fallback_notice("plan", e)
    return rules.plan(intent, facts, previous), "rules"


def _respond_payload(state: dict[str, Any]) -> dict[str, Any]:
    facts = state.get("facts") or {}
    return {
        "customer_first_name": ((facts.get("customer") or {}).get("name") or "").split(" ")[0],
        "customer_message": state.get("user_message"),
        "mode": state.get("mode"),
        "customer_approved": state.get("approved"),
        "intent": state.get("intent"),
        "outcome": state.get("outcome"),
        "decision": (state.get("plan") or {}).get("decision"),
        "rationale": (state.get("plan") or {}).get("rationale"),
        "question_to_ask": (state.get("plan") or {}).get("question"),
        "actions": [
            {
                k: a.get(k)
                for k in (
                    "title",
                    "description",
                    "status",
                    "needs_confirmation",
                    "result",
                    "error",
                    "verification",
                )
            }
            for a in state.get("actions") or []
        ],
        "recommendations_shown": bool((state.get("plan") or {}).get("offer_recommendations")),
        "policy_titles": [f"{p['doc_title']} › {p['heading']}" for p in (state.get("policies") or [])[:3]],
        "policy_text": [p["text"] for p in (state.get("policies") or [])[:2]]
        if (state.get("plan") or {}).get("decision") == "inform"
        else [],
    }


async def respond(state: dict[str, Any]) -> AsyncIterator[str]:
    if llm_enabled():
        user = (
            f"{RESPOND_INSTRUCTIONS}\n\n<turn>\n{json.dumps(_respond_payload(state), default=str)}\n</turn>\n\n"
            f"<conversation>\n{_history_text(state.get('history') or [])}\n</conversation>"
        )
        produced = False
        try:
            async for chunk in stream_text(
                node="respond",
                system=system_prompt(),
                user=user,
                max_tokens=700,
                conversation_id=state.get("conversation_id"),
            ):
                produced = True
                yield chunk
            return
        except (LlmUnavailable, BudgetExceeded) as e:
            if produced:
                return
            _fallback_notice("respond", e)
    text = rules.respond(state)
    for i in range(0, len(text), 18):
        yield text[i : i + 18]
