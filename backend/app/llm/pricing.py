"""USD per million tokens. Source: docs/project/budget.md (checked 2026-10-31)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    input: float
    output: float
    cache_write: float
    cache_read: float


PRICES: dict[str, Price] = {
    "claude-sonnet-5-5": Price(input=2.00, output=10.00, cache_write=2.50, cache_read=0.20),
    "text-embedding-3-small": Price(input=0.02, output=0.0, cache_write=0.0, cache_read=0.0),
}

# Unknown models are priced pessimistically so the budget guard errs on the safe side.
_FALLBACK = Price(input=10.00, output=50.00, cache_write=12.50, cache_read=1.00)


def price_for(model: str) -> Price:
    return PRICES.get(model, _FALLBACK)


def cost_usd(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_write_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> float:
    p = price_for(model)
    return (
        input_tokens * p.input
        + output_tokens * p.output
        + cache_write_tokens * p.cache_write
        + cache_read_tokens * p.cache_read
    ) / 1_000_000
