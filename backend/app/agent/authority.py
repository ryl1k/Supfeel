"""Code-enforced agent authority (mirrors knowledge-base/policies/agent-authority.md).

The model proposes; this module decides what needs confirmation or escalation. The LLM cannot
bypass it.
"""

import json
from typing import Any

from pydantic import ValidationError

from app.agent.state import ActionRecord
from app.tools.base import money
from app.tools.registry import TOOLS

ESCALATION_LIMIT_CENTS = 20_000
AUTO_STORE_CREDIT_LIMIT_CENTS = 2_500
ALWAYS_CONFIRM = {"create_exchange", "cancel_order", "cancel_subscription", "reship_order"}
NEVER_CONFIRM = {"create_return_label", "pause_subscription", "update_address", "escalate_to_human"}


def _money_out(tool: str, args: dict, facts: dict) -> int:
    if tool == "create_refund":
        return int(args.get("amount_cents", 0))
    if tool == "issue_store_credit":
        return int(args.get("amount_cents", 0))
    if tool == "cancel_subscription" and args.get("refund_renewal"):
        sub = facts.get("subscription") or {}
        return int((sub.get("renewal_payment") or {}).get("amount_cents", 0))
    return 0


def needs_confirmation(tool: str, args: dict, facts: dict) -> bool:
    if tool in NEVER_CONFIRM:
        return False
    if tool in ALWAYS_CONFIRM:
        return True
    if tool == "create_refund":
        dupes = {d["payment_id"] for d in (facts.get("derived") or {}).get("duplicate_captured_payments", [])}
        return args.get("payment_id") not in dupes  # duplicate captured charge: refund autonomously
    if tool == "issue_store_credit":
        return int(args.get("amount_cents", 0)) > AUTO_STORE_CREDIT_LIMIT_CENTS
    return True


def describe(tool: str, args: dict, facts: dict) -> tuple[str, str]:
    """Human-readable title + description for action cards."""
    d = (facts.get("derived") or {}) if facts else {}
    if tool == "create_exchange":
        sku = args.get("new_sku", "")
        rec = next(
            (
                r
                for r in ((facts.get("recommendations") or {}).get("recommendations") or [])
                if r["sku"] == sku
            ),
            None,
        )
        new_item = f"{rec['name']} {rec['color']}, size {rec['size']:g} {rec['width']}" if rec else sku
        return f"Exchange for {new_item}", (
            f"Replace your {d.get('main_item', 'item')} with {new_item}. Ships now at no cost; "
            "send the original back within 14 days with the prepaid label."
        )
    if tool == "create_return_label":
        return "Prepaid return label", "Email a free UPS return label (PDF + QR code), valid for 14 days."
    if tool == "create_refund":
        method = (
            "store credit (+10% bonus)"
            if args.get("method") == "store_credit"
            else "your original payment method"
        )
        return (
            f"Refund {money(int(args.get('amount_cents', 0)))}",
            f"Refund to {method}. {args.get('reason', '')}".strip(),
        )
    if tool == "reship_order":
        return (
            f"Free express reship of {args.get('order_id')}",
            "Send a replacement by express shipping (1–2 business days), free.",
        )
    if tool == "cancel_order":
        return (
            f"Cancel order {args.get('order_id')}",
            "Cancel before it ships; any hold or charge is released.",
        )
    if tool == "update_address":
        a = args.get("address", {})
        return (
            f"Update address for {args.get('order_id')}",
            f"Ship to {a.get('line1')}, {a.get('city')}, {a.get('state')} {a.get('zip')}.",
        )
    if tool == "issue_store_credit":
        return f"Store credit {money(int(args.get('amount_cents', 0)))}", args.get(
            "reason", "Goodwill credit"
        )
    if tool == "pause_subscription":
        return (
            f"Pause Velora Club for {args.get('months')} month(s)",
            "No charges during the pause; benefits resume automatically.",
        )
    if tool == "cancel_subscription":
        if args.get("refund_renewal"):
            return (
                "Cancel membership + refund renewal",
                "Cancel Velora Club now and refund the latest renewal in full.",
            )
        return "Cancel membership", "Cancel Velora Club at the end of the current billing period."
    if tool == "escalate_to_human":
        return "Hand off to a specialist", "A human specialist will reply within 1 business day."
    return tool, ""


def enforce(
    planned: list[dict[str, Any]], facts: dict, conversation_id: str | None
) -> tuple[list[ActionRecord], list[str]]:
    """Validate args, attach confirmation flags, apply the escalation limit.

    Returns (actions, notes). Invalid actions are dropped with a note.
    """
    actions: list[ActionRecord] = []
    notes: list[str] = []
    total_money = 0
    for p in planned:
        tool = p["tool"]
        spec = TOOLS.get(tool)
        if spec is None or spec.kind != "write":
            notes.append(f"Dropped unknown tool {tool}.")
            continue
        try:
            raw = json.loads(p["args_json"]) if isinstance(p.get("args_json"), str) else p.get("args", {})
            args = spec.args.model_validate(raw).model_dump(exclude_none=True)
        except (json.JSONDecodeError, ValidationError) as e:
            notes.append(f"Dropped {tool}: invalid arguments ({str(e).splitlines()[0]}).")
            continue
        amount = _money_out(tool, args, facts)
        total_money += amount
        title, description = describe(tool, args, facts)
        actions.append(
            ActionRecord(
                tool=tool,
                args=args,
                reason=p.get("reason", ""),
                title=title,
                description=description,
                amount_cents=amount,
                needs_confirmation=needs_confirmation(tool, args, facts),
                status="proposed",
            )
        )

    if total_money > ESCALATION_LIMIT_CENTS:
        summary = "; ".join(f"{a['title']} ({a['reason']})" for a in actions)
        notes.append(f"Total refunds/credits {money(total_money)} exceed the $200 agent limit; escalating.")
        args = {"reason": "refund_over_limit", "summary": f"Proposed: {summary}"}
        title, description = describe("escalate_to_human", args, facts)
        actions = [
            ActionRecord(
                tool="escalate_to_human",
                args=args,
                reason="Amount above agent authority",
                title=title,
                description=description,
                amount_cents=0,
                needs_confirmation=False,
                status="proposed",
            )
        ]
    return actions, notes
