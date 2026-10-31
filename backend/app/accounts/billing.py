"""Pay as you go (payments are mocked).

- Workspaces hold a prepaid credit balance in a ledger (`credit_entries`); new workspaces get a free grant.
- Each billable unit is priced (PRICES) and debited when it starts: escalated ticket, fix run, knowledge
  question, index run.
- A monthly spend limit (set by the workspace) caps usage per calendar month (UTC) and resets on the 1st.
- Top-ups go through a mock card checkout; optional auto-recharge tops up when the balance drops below a threshold.
- Claude/OpenAI cost is attributed per workspace (llm_usage.account_id) so the dashboard can show margins.
"""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select

from app.db.models import Account, CreditEntry, LlmUsage, Repo
from app.db.session import session_scope

FREE_GRANT_CENTS = 500  # $5 to try it
MIN_TOPUP_CENTS, MAX_TOPUP_CENTS = 500, 50_000
DECLINED_TEST_CARD = "4000000000000002"


@dataclass(frozen=True)
class Price:
    metric: str
    cents: int
    unit: str
    description: str


PRICES: dict[str, Price] = {
    "ticket": Price(
        "ticket", 15, "ticket", "Escalated ticket: triage, investigation, explanation or action, verification"
    ),
    "fix": Price(
        "fix", 100, "fix run", "Fix agent run: root cause, code change, regression test, pull request"
    ),
    "ask": Price("ask", 2, "question", "Knowledge question about the product (ask_product)"),
    "index": Price("index", 10, "index run", "Repository (re)index: changed files, summaries, API actions"),
}


class PaymentRequired(RuntimeError):
    """Not enough credit, or the monthly spend limit would be exceeded."""

    def __init__(self, reason: str, message: str):
        self.reason = reason  # balance | monthly_limit
        super().__init__(message)


def month_start(now: datetime | None = None) -> datetime:
    now = now or datetime.now(UTC)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def next_month_start(now: datetime | None = None) -> datetime:
    m = month_start(now)
    return m.replace(year=m.year + 1, month=1) if m.month == 12 else m.replace(month=m.month + 1)


async def balance_cents(account_id: str) -> int:
    async with session_scope() as s:
        return int(
            await s.scalar(
                select(func.coalesce(func.sum(CreditEntry.amount_cents), 0)).where(
                    CreditEntry.account_id == account_id
                )
            )
        )


async def month_spend_cents(account_id: str) -> int:
    async with session_scope() as s:
        spent = await s.scalar(
            select(func.coalesce(func.sum(CreditEntry.amount_cents), 0)).where(
                CreditEntry.account_id == account_id,
                CreditEntry.kind == "usage",
                CreditEntry.created_at >= month_start(),
            )
        )
    return -int(spent)


async def _add(account_id: str, kind: str, amount_cents: int, description: str, **kw) -> None:
    async with session_scope() as s:
        s.add(
            CreditEntry(
                account_id=account_id,
                kind=kind,
                amount_cents=amount_cents,
                description=description[:300],
                **kw,
            )
        )


async def grant(account_id: str, cents: int, description: str) -> None:
    await _add(account_id, "grant", cents, description)


async def _auto_recharge(acc: Account, balance: int, needed: int) -> int:
    cfg = acc.auto_recharge or {}
    if (
        not cfg.get("enabled")
        or not acc.payment_method
        or balance - needed >= int(cfg.get("threshold_cents", 0))
    ):
        return balance
    amount = max(int(cfg.get("amount_cents", 2000)), needed)
    await _add(
        acc.id,
        "topup",
        amount,
        f"Auto-recharge ({acc.payment_method.get('brand')} •••• {acc.payment_method.get('last4')})",
    )
    return balance + amount


async def charge(
    account_id: str | None,
    metric: str,
    *,
    quantity: int = 1,
    repo_id: str | None = None,
    ref: str | None = None,
    note: str = "",
) -> int:
    """Debit a billable unit or raise PaymentRequired. No account (operator / legacy repos) = free."""
    if not account_id:
        return 0
    price = PRICES[metric]
    cost = price.cents * quantity
    async with session_scope() as s:
        acc = await s.get(Account, account_id)
        s.expunge(acc)
    spent = await month_spend_cents(account_id)
    if spent + cost > acc.monthly_limit_cents:
        raise PaymentRequired(
            "monthly_limit",
            f"Monthly spend limit (${acc.monthly_limit_cents / 100:.2f}) reached; it resets on "
            f"{next_month_start():%b 1}. Raise it in Billing.",
        )
    balance = await _auto_recharge(acc, await balance_cents(account_id), cost)
    if balance < cost:
        raise PaymentRequired("balance", f"Not enough credit (${balance / 100:.2f} left). Top up in Billing.")
    await _add(
        account_id,
        "usage",
        -cost,
        note or price.description,
        metric=metric,
        quantity=quantity,
        repo_id=repo_id,
        ref=ref,
    )
    return cost


async def refund(account_id: str | None, metric: str, ref: str, note: str) -> None:
    """Give a unit back (e.g. a fix run that never reached Claude)."""
    if account_id:
        await _add(account_id, "refund", PRICES[metric].cents, note, metric=metric, ref=ref)


async def topup(account_id: str, cents: int, payment_method: dict) -> None:
    await _add(
        account_id,
        "topup",
        cents,
        f"Top-up ({payment_method.get('brand')} •••• {payment_method.get('last4')})",
    )


async def summary(account_id: str) -> dict:
    async with session_scope() as s:
        acc = await s.get(Account, account_id)
        by_metric = (
            await s.execute(
                select(CreditEntry.metric, func.sum(CreditEntry.quantity), func.sum(CreditEntry.amount_cents))
                .where(
                    CreditEntry.account_id == account_id,
                    CreditEntry.kind == "usage",
                    CreditEntry.created_at >= month_start(),
                )
                .group_by(CreditEntry.metric)
            )
        ).all()
        ai = await s.scalar(
            select(func.coalesce(func.sum(LlmUsage.cost_usd), 0)).where(
                LlmUsage.account_id == account_id, LlmUsage.mode == "live", LlmUsage.ts >= month_start()
            )
        )
        repos = await s.scalar(select(func.count()).select_from(Repo).where(Repo.account_id == account_id))
    return {
        "balance_cents": await balance_cents(account_id),
        "month": {
            "start": month_start().isoformat(),
            "resets_at": next_month_start().isoformat(),
            "spent_cents": await month_spend_cents(account_id),
            "limit_cents": acc.monthly_limit_cents,
            "by_metric": {m: {"quantity": int(q or 0), "cents": -int(c or 0)} for m, q, c in by_metric if m},
            "ai_cost_usd": round(float(ai or 0), 4),
        },
        "repos": int(repos or 0),
        "auto_recharge": acc.auto_recharge
        or {"enabled": False, "threshold_cents": 500, "amount_cents": 2000},
        "payment_method": acc.payment_method or None,
        "prices": [asdict(p) for p in PRICES.values()],
    }


async def statement(account_id: str, limit: int = 100) -> list[dict]:
    async with session_scope() as s:
        rows = (
            await s.scalars(
                select(CreditEntry)
                .where(CreditEntry.account_id == account_id)
                .order_by(CreditEntry.id.desc())
                .limit(limit)
            )
        ).all()
    return [
        {"id": e.id, "kind": e.kind, "metric": e.metric, "quantity": e.quantity, "amount_cents": e.amount_cents,
         "description": e.description, "repo_id": e.repo_id, "ref": e.ref, "created_at": e.created_at.isoformat()}
        for e in rows
    ]  # fmt: skip


async def update_settings(account_id: str, *, monthly_limit_cents: int | None = None, auto_recharge: dict | None = None,
                          payment_method: dict | None = None) -> None:  # fmt: skip
    async with session_scope() as s:
        acc = await s.get(Account, account_id)
        if monthly_limit_cents is not None:
            acc.monthly_limit_cents = monthly_limit_cents
        if auto_recharge is not None:
            acc.auto_recharge = auto_recharge
        if payment_method is not None:
            acc.payment_method = payment_method


def mock_card(number: str, name: str) -> dict:
    digits = "".join(c for c in number if c.isdigit())
    if len(digits) < 12:
        raise ValueError("card number looks wrong")
    if digits == DECLINED_TEST_CARD:
        raise PaymentRequired("declined", "card declined (mock test card)")
    return {
        "brand": "Visa" if digits.startswith("4") else "Mastercard" if digits.startswith("5") else "Card",
        "last4": digits[-4:],
        "name": name,
    }
