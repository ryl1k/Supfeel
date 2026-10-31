"""Deterministic rule brain.

Used when LLM_MODE=mock (development, tests, UI work: zero API spend) and as the automatic fallback
when Claude is unavailable or the budget cap is hit. Same inputs/outputs as the LLM brain.
"""

import json
import re
from typing import Any

from app.agent.schemas import Intent, Plan, PlannedAction
from app.tools.base import money

ORDER_RE = re.compile(r"\b(V[XR]?-?[A-Z0-9]{4,6})\b", re.I)
ADDRESS_RE = re.compile(
    r"(?P<line1>\d+\s+[^,\n]+),\s*(?P<city>[^,\n]+),\s*(?P<state>[A-Za-z]{2})\s+(?P<zip>\d{5})", re.I
)

INTENT_KEYWORDS: list[tuple[str, list[str]]] = [
    ("human_request", ["human", "real person", "representative", "speak to someone", "talk to someone", "live agent"]),
    ("double_charge", ["charged twice", "double charge", "double charged", "two charges", "duplicate", "billed twice", "charged me twice"]),
    ("cancel_membership", ["cancel my membership", "cancel membership", "cancel my subscription", "cancel the club",
                           "cancel velora club", "didn't mean to renew", "did not mean to renew", "unexpected renewal", "renewal charge"]),
    ("pause_membership", ["pause my membership", "pause membership", "pause the club", "pause my subscription", "pause it", "pause instead"]),
    ("cancel_order", ["cancel my order", "cancel the order", "cancel order", "cancel my new order"]),
    ("change_address", ["change my address", "change the address", "update my address", "update address", "wrong address",
                        "ship it to", "ship to a different", "new address", "moved", "ship my order to", "ship my new order to"]),
    ("damaged_or_defective", ["sole", "separat", "broken", "defect", "falling apart", "ripped", "damaged", "torn", "came apart", "coming apart"]),
    ("lost_or_delayed", ["where is my", "hasn't arrived", "has not arrived", "not arrived", "never arrived", "lost", "stuck",
                         "late", "delayed", "still waiting", "not received", "hasn't come", "no update"]),
    ("comfort_exchange", ["uncomfortable", "not comfortable", "narrow", "too tight", "tight", "pinch", "hurt", "too wide",
                          "too big", "too small", "heel slip", "blister", "doesn't fit", "don't fit", "do not fit", "fit"]),
    ("return_refund", ["return", "refund", "money back", "send back", "send them back", "send it back"]),
    ("billing_question", ["charge", "charged", "pending", "bill", "payment", "invoice"]),
    ("order_status", ["order status", "track", "tracking", "when will"]),
    ("product_question", ["size", "sizing", "wash", "clean", "care", "width", "wide fit"]),
    ("policy_question", ["policy", "how long", "can i", "do you", "warranty", "shipping cost", "gift card", "loyalty"]),
]  # fmt: skip

FIT_KEYWORDS: list[tuple[str, list[str]]] = [
    ("narrow", ["narrow", "tight", "pinch", "squeez", "cramped", "sides"]),
    ("wide", ["too wide", "loose", "too big", "roomy"]),
    ("short", ["too small", "toes hit", "too short", "cramp"]),
    ("long", ["too long", "heel slip", "slipping", "slips"]),
    ("arch", ["arch"]),
    ("stiff", ["stiff", "hard", "firm"]),
]

PREFERENCE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("store_credit", ["store credit", "credit"]),
    ("refund", ["refund", "money back"]),
    ("exchange", ["exchange", "swap", "different size", "replace", "replacement"]),
    ("reship", ["reship", "send another", "send it again", "resend"]),
    ("pause", ["pause"]),
    ("cancel", ["cancel", "just cancel", "no thanks", "no, cancel"]),
]

GREETINGS = {"hi", "hello", "hey", "hiya", "good morning", "good evening"}
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "1": 1, "2": 2, "3": 3}


def _match(text: str, table: list[tuple[str, list[str]]]) -> str | None:
    for name, words in table:
        if any(w in text for w in words):
            return name
    return None


def _search_query(intent: str, text: str) -> str:
    base = {
        "comfort_exchange": "comfort guarantee exchange uncomfortable shoes fit width",
        "return_refund": "return window refund returns policy",
        "lost_or_delayed": "lost package delayed tracking reship refund",
        "order_status": "shipping delivery tracking",
        "damaged_or_defective": "warranty defect sole separation replacement",
        "double_charge": "duplicate charges authorization hold billing error refund",
        "billing_question": "authorization hold pending charge payments",
        "cancel_membership": "cancel membership pause renewal refund velora club",
        "pause_membership": "pause membership velora club",
        "cancel_order": "order cancellation processing",
        "change_address": "address change processing order",
        "human_request": "escalation human specialist support hours",
    }.get(intent, "")
    return f"{base} {text}".strip()[:300]


def understand(message: str, previous: dict[str, Any] | None = None) -> Intent:
    previous = previous or {}
    text = message.lower().strip()
    intent = _match(text, INTENT_KEYWORDS) or ("greeting" if text.strip("!. ") in GREETINGS else "other")
    fit = _match(text, FIT_KEYWORDS)
    pref = _match(text, PREFERENCE_KEYWORDS)
    order = ORDER_RE.search(message)
    addr = ADDRESS_RE.search(message)
    prev_intent = (previous.get("intent") or {}).get("intent")

    # Combinations the keyword table can't express.
    membership_words = ("membership", "velora club", "the club", "subscription")
    if any(w in text for w in membership_words) and "cancel" in text:
        intent = "cancel_membership"
    elif any(w in text for w in membership_words) and "pause" in text:
        intent = "pause_membership"
    elif (
        addr
        and intent in ("other", "change_address")
        and ("ship" in text or "send" in text or "address" in text)
    ):
        intent = "change_address"

    # Changing the resolution of an open proposal ("can I get a refund instead?") keeps the problem.
    if (
        previous.get("outcome") == "awaiting_confirmation"
        and prev_intent in ("lost_or_delayed", "comfort_exchange", "damaged_or_defective")
        and intent in ("other", "return_refund")
        and pref
    ):
        intent = prev_intent
        order_id = (previous.get("intent") or {}).get("order_id")
        if order_id and not order:
            order = ORDER_RE.search(order_id)

    # Follow-up to our clarifying question or pause offer: keep the earlier intent.
    if previous.get("outcome") == "asked" and prev_intent:
        if prev_intent == "cancel_membership" and pref in ("pause",):
            intent = "pause_membership"
        elif prev_intent == "cancel_membership" and (pref == "cancel" or text in ("no", "nope", "cancel")):
            intent = "cancel_membership"
        elif intent in ("other", "comfort_exchange", "greeting", "product_question") or (
            prev_intent == "change_address" and addr
        ):
            intent = prev_intent
        fit = fit or (previous.get("intent") or {}).get("fit_problem")
        pref = pref or (previous.get("intent") or {}).get("preferred_resolution")
        if not order and (previous.get("intent") or {}).get("order_id"):
            order_id = previous["intent"]["order_id"]
        else:
            order_id = order.group(1).upper() if order else None
    else:
        order_id = order.group(1).upper() if order else None

    if intent == "cancel_membership" and ("didn't mean" in text or "did not mean" in text or "renew" in text):
        pref = pref or "refund"

    new_address = addr.group(0) if addr else None
    needs, question = False, None
    if intent == "comfort_exchange" and not fit:
        needs = True
        question = "I'm sorry they're not comfortable. What feels off: too narrow or tight, too loose, or something else like the arch?"
    elif intent == "change_address" and not new_address:
        needs = True
        question = "Sure. What's the new address? Please include street, city, state and ZIP."

    summaries = {
        "comfort_exchange": f"Shoes are uncomfortable{f' ({fit})' if fit else ''}; customer wants a better fit.",
        "return_refund": "Customer wants to return an item for a refund.",
        "lost_or_delayed": "Order has not arrived; tracking may be stalled.",
        "order_status": "Customer wants an update on an order.",
        "damaged_or_defective": "Item appears defective or damaged.",
        "double_charge": "Customer sees duplicate charges for one order.",
        "billing_question": "Customer has a question about a charge.",
        "cancel_membership": "Customer wants to cancel Velora Club.",
        "pause_membership": "Customer wants to pause Velora Club.",
        "cancel_order": "Customer wants to cancel an order before it ships.",
        "change_address": "Customer wants to change the shipping address.",
        "human_request": "Customer asked to speak with a human.",
        "greeting": "Customer said hello.",
    }
    return Intent(
        intent=intent,
        summary=summaries.get(intent, f"General question: {message[:120]}"),
        order_id=order_id,
        fit_problem=fit if intent == "comfort_exchange" else None,
        preferred_resolution=pref,
        new_address=new_address,
        needs_clarification=needs,
        clarifying_question=question,
        search_query=_search_query(intent, message),
    )


# --------------------------------------------------------------------------- planning


def _a(tool: str, why: str, **args: Any) -> PlannedAction:
    return PlannedAction(tool=tool, args_json=json.dumps(args), reason=why)


def _plan(decision: str, rationale: str, cites: list[str], actions=None, question=None, recs=False) -> Plan:
    return Plan(
        decision=decision,
        rationale=rationale,
        policy_citations=cites,
        actions=actions or [],
        question=question,
        offer_recommendations=recs,
    )


def _parse_address(raw: str) -> dict | None:
    m = ADDRESS_RE.search(raw or "")
    if not m:
        return None
    return {
        "line1": m["line1"].strip(),
        "city": m["city"].strip(),
        "state": m["state"].upper(),
        "zip": m["zip"],
        "country": "US",
    }


def plan(intent: dict[str, Any], facts: dict[str, Any], previous: dict[str, Any] | None = None) -> Plan:
    previous = previous or {}
    name = intent["intent"]
    d = facts.get("derived", {})
    target = facts.get("target_order")
    pref = intent.get("preferred_resolution")

    if name == "human_request":
        return _plan(
            "escalate",
            "Customer explicitly asked for a human.",
            ["Agent authority › Actions that require human escalation"],
            [
                _a(
                    "escalate_to_human",
                    "Customer request",
                    reason="customer_request",
                    summary="Customer asked for a human specialist.",
                )
            ],
        )

    if name == "comfort_exchange":
        if not target:
            return _plan(
                "ask",
                "No delivered order found.",
                [],
                question="Which order is this about? The order number starts with V.",
            )
        if not d.get("return_window_open"):
            return _plan(
                "decline",
                f"Delivered {d.get('days_since_delivery')} days ago; the 30-day comfort guarantee has passed.",
                ["Returns and exchanges › 30-day comfort guarantee (footwear)"],
            )
        if not d.get("comfort_guarantee_available"):
            return _plan(
                "decline",
                "The comfort guarantee was already used for this item.",
                ["Returns and exchanges › 30-day comfort guarantee (footwear)"],
            )
        item_id = d["main_item_id"]
        if pref in ("refund", "store_credit"):
            return _plan(
                "act",
                "Comfort guarantee: worn items can't get a cash refund, but full store credit is allowed.",
                ["Returns and exchanges › 30-day comfort guarantee (footwear)", "Refunds › Refund methods"],
                [
                    _a("create_return_label", "Free comfort-guarantee return", order_item_id=item_id),
                    _a("issue_store_credit", "Comfort guarantee refund as store credit",
                       amount_cents=d["main_item_price_cents"], reason="Comfort guarantee: full value as store credit"),
                ],
            )  # fmt: skip
        recs = ((facts.get("recommendations") or {}).get("recommendations")) or []
        if not recs:
            return _plan(
                "act",
                "No in-stock alternative in that fit; a free return keeps the customer whole.",
                ["Returns and exchanges › 30-day comfort guarantee (footwear)"],
                [_a("create_return_label", "Free comfort-guarantee return", order_item_id=item_id)],
            )
        best = recs[0]
        return _plan(
            "act",
            f"Delivered {d.get('days_since_delivery')} days ago, within the 30-day comfort guarantee, which hasn't been used. "
            f"{best['name']} in {best['width']} width fixes the '{intent.get('fit_problem')}' fit.",
            ["Returns and exchanges › 30-day comfort guarantee (footwear)", "Sizing and fit › Width options"],
            [
                _a("create_exchange", "Comfort guarantee exchange for a better fit", order_item_id=item_id,
                   new_sku=best["sku"], reason=f"Comfort guarantee: {intent.get('fit_problem')} fit", use_comfort_guarantee=True),
                _a("create_return_label", "Prepaid label to send the original back", order_item_id=item_id),
            ],
            recs=True,
        )  # fmt: skip

    if name == "return_refund":
        if not target:
            return _plan(
                "ask", "No delivered order found.", [], question="Which order would you like to return?"
            )
        if d.get("final_sale"):
            return _plan(
                "decline",
                "Final-sale items can't be returned unless defective.",
                ["Returns and exchanges › Non-returnable items"],
            )
        if not d.get("return_window_open"):
            return _plan(
                "decline",
                f"Delivered {d.get('days_since_delivery')} days ago, outside the 30-day return window.",
                ["Returns and exchanges › Standard return window"],
            )
        return _plan(
            "act",
            "Within the 30-day return window. Refund is issued within 2 business days after the warehouse receives it.",
            [
                "Returns and exchanges › Standard return window",
                "Returns and exchanges › Return refund timing",
            ],
            [_a("create_return_label", "Return within 30 days", order_item_id=d["main_item_id"])],
        )

    if name in ("lost_or_delayed", "order_status"):
        assessment = d.get("shipment_assessment")
        if target and assessment == "lost":
            if pref in ("refund", "store_credit"):
                pay = next((p for p in target["payments"] if p["status"] == "captured"), None)
                if pay:
                    return _plan(
                        "act",
                        f"No tracking update for {d.get('business_days_since_last_scan')} business days, so the package counts as lost. Customer prefers a refund.",
                        ["Shipping and delivery › Lost packages", "Refunds › Refunds for undelivered orders"],
                        [_a("create_refund", "Lost package: full refund", payment_id=pay["payment_id"],
                            amount_cents=pay["amount_cents"] - pay["refunded_cents"], method="original",
                            reason=f"Order {target['order_id']} lost in transit")],
                    )  # fmt: skip
            return _plan(
                "act",
                f"No tracking update for {d.get('business_days_since_last_scan')} business days (lost after 7). Free express reship.",
                ["Shipping and delivery › Lost packages"],
                [
                    _a(
                        "reship_order",
                        "Lost in transit",
                        order_id=target["order_id"],
                        reason="No tracking update for 7+ business days",
                    )
                ],
            )
        return _plan(
            "inform", f"Shipment status: {assessment or 'unknown'}.", ["Shipping and delivery › Tracking"]
        )

    if name == "damaged_or_defective":
        if not target or not d.get("main_item_id"):
            return _plan("ask", "Need the order.", [], question="Which order is the defective item from?")
        days = d.get("days_since_delivery") or 0
        if days > 365:
            return _plan(
                "decline", "Outside the 12-month warranty.", ["Warranty and defects › Warranty coverage"]
            )
        item = next(i for i in target["items"] if i["order_item_id"] == d["main_item_id"])
        actions = [
            _a("create_exchange", "Warranty replacement, same item", order_item_id=item["order_item_id"],
               new_sku=item["sku"], reason="Manufacturing defect (warranty)", use_comfort_guarantee=False),
        ]  # fmt: skip
        if item["price_cents"] >= 10_000 or days <= 30:
            actions.append(
                _a(
                    "create_return_label",
                    "Send the defective pair back free",
                    order_item_id=item["order_item_id"],
                )
            )
        return _plan(
            "act",
            f"Sole separation is a covered manufacturing defect; delivered {days} days ago, within the 12-month warranty.",
            ["Warranty and defects › Warranty coverage", "Warranty and defects › Making a warranty claim"],
            actions,
        )

    if name in ("double_charge", "billing_question"):
        dupes = d.get("duplicate_captured_payments") or []
        if dupes:
            dup = dupes[0]
            return _plan(
                "act",
                f"Two captured payments of {money(dup['amount_cents'])} for the same order: a billing error. Refund the duplicate immediately.",
                ["Payments and billing › Duplicate charges"],
                [_a("create_refund", "Duplicate captured charge", payment_id=dup["payment_id"],
                    amount_cents=dup["amount_cents"], method="original", reason=f"Duplicate of {dup['duplicate_of']}")],
            )  # fmt: skip
        if d.get("authorization_holds"):
            return _plan(
                "inform",
                "Only pending authorization holds, not charges; they drop off in 3–7 business days.",
                ["Payments and billing › Authorization holds vs. charges"],
            )
        return _plan(
            "inform", "No duplicate captured charges found.", ["Payments and billing › Duplicate charges"]
        )

    if name == "cancel_membership":
        sub = facts.get("subscription")
        if not sub or sub["status"] == "cancelled":
            return _plan("inform", "No active membership.", ["Velora Club membership › Cancelling"])
        eligible = d.get("renewal_refund_eligible")
        pause_offered = previous.get("pause_offered")
        if not pause_offered and d.get("pause_available") and pref != "refund":
            q = "Before I cancel: would a free pause for 1–3 months work instead? Billing stops during the pause."
            if eligible:
                q += f" If you'd still like to cancel, I can also refund your recent {sub['price']} renewal."
            return _plan(
                "ask",
                "Policy: offer a pause once before cancelling.",
                ["Velora Club membership › Pausing"],
                question=q,
            )
        return _plan(
            "act",
            "Renewal charged within 14 days with no benefits used, so it qualifies for a full refund."
            if eligible
            else "Cancel at the end of the current period.",
            ["Velora Club membership › Cancelling", "Velora Club membership › Unexpected renewal charges"],
            [
                _a(
                    "cancel_subscription",
                    "Customer wants to cancel",
                    refund_renewal=bool(eligible),
                    reason="Customer request",
                )
            ],
        )

    if name == "pause_membership":
        if not d.get("pause_available", True):
            return _plan(
                "decline",
                "A pause was already used in the last 12 months.",
                ["Velora Club membership › Pausing"],
            )
        months = 1
        m = re.search(
            r"\b(one|two|three|1|2|3)\s+month",
            (intent.get("summary") or "") + " " + (previous.get("last_message") or ""),
        )
        if m:
            months = NUMBER_WORDS[m.group(1)]
        return _plan(
            "act",
            "Members can pause once per 12 months for up to 3 months at no cost.",
            ["Velora Club membership › Pausing"],
            [_a("pause_subscription", "Pause instead of cancelling", months=months)],
        )

    if name == "cancel_order":
        if target and target["status"] == "processing":
            return _plan(
                "act",
                "Order is still processing, so it can be cancelled for a full refund.",
                ["Refunds › Order cancellations"],
                [
                    _a(
                        "cancel_order",
                        "Customer request",
                        order_id=target["order_id"],
                        reason="Customer request",
                    )
                ],
            )
        return _plan(
            "decline",
            "The order has already shipped; it can be returned once delivered.",
            ["Refunds › Order cancellations"],
        )

    if name == "change_address":
        if not target or target["status"] != "processing":
            return _plan(
                "decline",
                "The order has shipped; the address can no longer be changed.",
                ["Shipping and delivery › Address changes"],
            )
        address = _parse_address(intent.get("new_address") or "")
        if not address:
            return _plan(
                "ask",
                "Need the full new address.",
                [],
                question="What's the new address (street, city, state, ZIP)?",
            )
        return _plan(
            "act",
            "Order is still processing, so the address can be changed.",
            ["Shipping and delivery › Address changes"],
            [_a("update_address", "Customer moved", order_id=target["order_id"], address=address)],
        )

    return _plan("inform", "Informational question.", [])


# --------------------------------------------------------------------------- reply


def respond(state: dict[str, Any]) -> str:
    facts = state.get("facts") or {}
    name = ((facts.get("customer") or {}).get("name") or "there").split()[0]
    outcome = state.get("outcome")
    plan_ = state.get("plan") or {}
    intent = state.get("intent") or {}
    actions = state.get("actions") or []
    policies = state.get("policies") or []

    if outcome == "asked":
        return plan_.get("question") or intent.get("clarifying_question") or "Could you tell me a bit more?"

    if outcome == "awaiting_confirmation":
        pending = [a for a in actions if a.get("needs_confirmation") and a.get("status") == "proposed"]
        plan_titles = " and ".join(f"**{a['title']}**" for a in pending)
        return (
            f"Thanks, {name}. I checked your account. {plan_.get('rationale', '')}\n\n"
            f"Here's my plan: {plan_titles}. Approve it below and I'll take care of everything."
        )

    if outcome == "declined":
        return "No problem, I haven't changed anything. Is there another way I can help?"

    done = [a for a in actions if a.get("status") == "done"]
    failed = [a for a in actions if a.get("status") == "failed"]
    if outcome in ("resolved", "partially_resolved", "escalated") and done:
        lines = [f"All set, {name}. Here's what I did:"]
        for a in done:
            ok = (a.get("verification") or {}).get("ok")
            lines.append(f"- {a['title']}{' ✓ verified' if ok else ''}")
        details = _result_details(done)
        if details:
            lines += ["", *details]
        if failed:
            lines += ["", "One step didn't go through, so I've passed it to a specialist."]
        lines += ["", "Anything else I can help with?"]
        return "\n".join(lines)

    if outcome == "not_allowed":
        msg = f"I looked into it, {name}. {plan_.get('rationale', '')}"
        if intent.get("intent") == "return_refund":
            msg += " If something's wrong with the item itself, it may be covered by our 12-month warranty. Just tell me what happened."
        else:
            msg += " I'm sorry I can't do more here. Is there anything else I can help with?"
        return msg

    # inform / answered
    rationale = plan_.get("rationale", "")
    if policies and intent.get("intent") in ("product_question", "policy_question", "other", "order_status"):
        top = policies[0]
        snippet = " ".join(top["text"].split())[:420]
        return f"{snippet}\n\n(From our {top['doc_title']} policy.) Anything else I can help with?"
    if intent.get("intent") == "greeting":
        return f"Hi {name}! I'm Supfeel. Tell me what's going on with your order, delivery, billing or membership, and I'll take care of it."
    return f"{rationale} Anything else I can help with?".strip()


def _result_details(done: list[dict]) -> list[str]:
    out = []
    for a in done:
        r = a.get("result") or {}
        t = a["tool"]
        if t == "create_exchange":
            out.append(f"Your {r.get('new_item')} ships today as order {r.get('new_order_id')}.")
        elif t == "create_return_label":
            out.append(
                f"Your prepaid return label ({r.get('tracking_no')}) is in your email, valid for 14 days."
            )
        elif t == "create_refund":
            out.append(f"Refund {r.get('refund_id')} for {r.get('amount')}: {r.get('eta')}.")
        elif t == "reship_order":
            out.append(f"Replacement order {r.get('new_order_id')} ships by express (1–2 business days).")
        elif t == "cancel_subscription":
            rr = r.get("renewal_refund")
            out.append(
                "Your membership is cancelled"
                + (f" and {rr['amount']} is on its way back to you." if rr else ".")
            )
        elif t == "pause_subscription":
            out.append(f"Your membership is paused until {str(r.get('paused_until', ''))[:10]}.")
        elif t == "escalate_to_human":
            out.append(f"Case {r.get('escalation_id')}: a specialist will reply within 1 business day.")
        elif t == "issue_store_credit":
            out.append(f"{r.get('amount')} store credit is available now.")
        elif t == "cancel_order":
            out.append("Your order is cancelled and any hold on your card is released.")
        elif t == "update_address":
            a2 = r.get("shipping_address", {})
            out.append(f"It will ship to {a2.get('line1')}, {a2.get('city')}.")
    return out
