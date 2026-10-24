"""Tests for the example modules. Run with: pytest examples"""
import asyncio

import pytest

from fallback_router import AllProvidersFailed, ProviderError, Router
from tool_schema import Param, Tool, ToolArgumentError, ToolRegistry, summarize_result
from wallet import (
    InsufficientFunds,
    QuotaExhausted,
    Wallet,
    choose_model,
    usage_tier,
)


# ---------- fallback router ----------

def make_router(**providers):
    routes = {
        "premium": ["a", "b"],
        "default": ["c"],
    }
    return Router(providers, routes, default_model="default", timeout_s=0.2)


def test_primary_answers_without_degrading():
    async def a(prompt):
        return "from a"

    router = make_router(a=a, b=a, c=a)
    result = asyncio.run(router.complete("premium", "hi"))
    assert (result.provider, result.degraded, result.attempts) == ("a", False, [])


def test_falls_back_to_second_provider_for_same_model():
    async def a(prompt):
        raise ProviderError("down")

    async def b(prompt):
        return "from b"

    router = make_router(a=a, b=b, c=b)
    result = asyncio.run(router.complete("premium", "hi"))
    assert result.provider == "b"
    assert result.model == "premium"
    assert result.degraded is False
    assert result.attempts == [("premium", "a", "ProviderError")]


def test_falls_back_to_default_model_when_all_providers_fail():
    async def bad(prompt):
        raise ProviderError("down")

    async def good(prompt):
        return "default answer"

    router = make_router(a=bad, b=bad, c=good)
    result = asyncio.run(router.complete("premium", "hi"))
    assert result.model == "default"
    assert result.degraded is True
    assert len(result.attempts) == 2


def test_timeout_counts_as_failure():
    async def slow(prompt):
        await asyncio.sleep(1)
        return "late"

    async def good(prompt):
        return "ok"

    router = make_router(a=slow, b=good, c=good)
    result = asyncio.run(router.complete("premium", "hi"))
    assert result.provider == "b"
    assert result.attempts[0][2] == "TimeoutError"


def test_empty_reply_counts_as_failure():
    async def empty(prompt):
        return "   "

    async def good(prompt):
        return "ok"

    router = make_router(a=empty, b=good, c=good)
    assert asyncio.run(router.complete("premium", "hi")).provider == "b"


def test_raises_when_everything_fails():
    async def bad(prompt):
        raise ProviderError("down")

    router = make_router(a=bad, b=bad, c=bad)
    with pytest.raises(AllProvidersFailed) as info:
        asyncio.run(router.complete("premium", "hi"))
    assert len(info.value.attempts) == 3


def test_default_model_is_not_retried_twice():
    async def bad(prompt):
        raise ProviderError("down")

    router = make_router(a=bad, b=bad, c=bad)
    with pytest.raises(AllProvidersFailed) as info:
        asyncio.run(router.complete("default", "hi"))
    assert len(info.value.attempts) == 1


# ---------- tool schemas ----------

def make_tool():
    return Tool(
        name="weather",
        description="Current weather",
        params=(
            Param("city", "string"),
            Param("days", "integer", required=False),
            Param("unit", "string", required=False, enum=("c", "f")),
        ),
        fn=lambda city, days=1, unit="c": {"city": city, "days": days, "unit": unit},
    )


def test_valid_arguments_run_the_tool():
    registry = ToolRegistry()
    registry.register(make_tool())
    assert registry.call("weather", {"city": "Tirana", "days": 3}) == {
        "city": "Tirana",
        "days": 3,
        "unit": "c",
    }


def test_all_problems_are_reported_together():
    tool = make_tool()
    with pytest.raises(ToolArgumentError) as info:
        tool.call({"days": "3", "unit": "k", "extra": 1})
    assert info.value.problems == [
        "missing: city",
        "days: expected integer",
        "unit: must be one of ['c', 'f']",
        "unexpected: extra",
    ]


def test_boolean_is_not_accepted_as_integer():
    with pytest.raises(ToolArgumentError):
        make_tool().call({"city": "Tirana", "days": True})


def test_duplicate_and_unknown_tools():
    registry = ToolRegistry()
    registry.register(make_tool())
    with pytest.raises(ValueError):
        registry.register(make_tool())
    with pytest.raises(KeyError):
        registry.call("missing", {})


def test_summarizer_handles_any_shape_and_bounds_size():
    assert summarize_result({"a": [1, 2]}) == '{"a": [1, 2]}'
    assert summarize_result(object.__name__) == '"object"'
    long = summarize_result(["x" * 100] * 50, max_chars=200)
    assert long.startswith("[")
    assert "truncated" in long
    assert len(long) < 300


# ---------- wallet ----------

def test_reserve_then_settle_refunds_the_difference():
    wallet = Wallet(1000)
    hold = wallet.reserve(300)
    assert wallet.balance == 700
    wallet.settle(hold, actual=120)
    assert wallet.balance == 880


def test_release_returns_the_whole_hold():
    wallet = Wallet(1000)
    hold = wallet.reserve(300)
    wallet.release(hold)
    assert wallet.balance == 1000


def test_reserve_is_strict_by_default_and_relaxed_on_request():
    wallet = Wallet(100)
    with pytest.raises(InsufficientFunds):
        wallet.reserve(150)
    hold = wallet.reserve(150, allow_negative=True)
    assert wallet.balance == -50
    wallet.settle(hold, actual=40)
    assert wallet.balance == 60


def test_a_reservation_closes_once():
    wallet = Wallet(100)
    hold = wallet.reserve(10)
    wallet.settle(hold, 5)
    with pytest.raises(ValueError):
        wallet.settle(hold, 5)
    with pytest.raises(ValueError):
        wallet.release(hold)


def test_choose_model_degrades_then_stops():
    kept = choose_model(10, "premium", "default", daily_used=0, daily_limit=20)
    assert (kept.model, kept.downgraded) == ("premium", False)

    degraded = choose_model(0, "premium", "default", daily_used=5, daily_limit=20)
    assert (degraded.model, degraded.downgraded) == ("default", True)

    with pytest.raises(QuotaExhausted):
        choose_model(0, "premium", "default", daily_used=20, daily_limit=20)


@pytest.mark.parametrize(
    "percent,tier",
    [
        (0, "normal"),
        (49.9, "normal"),
        (50, "notice"),
        (65, "low"),
        (70, "moderate"),
        (82, "elevated"),
        (85, "high"),
        (92, "critical"),
        (97, "severe"),
        (100, "exhausted"),
        (130, "exhausted"),
    ],
)
def test_usage_tiers(percent, tier):
    assert usage_tier(percent) == tier
