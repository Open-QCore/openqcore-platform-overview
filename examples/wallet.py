"""Illustrative wallet: reserve-then-settle accounting and graceful downgrade.

A self-contained sketch of the ideas in docs/decisions/003-wallet-downgrade.md.
Amounts are integers (for example micro-credits) to avoid floating-point error.
Written as an example for this repository; not production code.
"""
from __future__ import annotations

from dataclasses import dataclass


class InsufficientFunds(Exception):
    """A reservation would take the balance below zero."""


class QuotaExhausted(Exception):
    """Wallet is empty and the daily limit is used up (maps to HTTP 402)."""


@dataclass
class Reservation:
    amount: int
    closed: bool = False


class Wallet:
    def __init__(self, balance: int):
        self.balance = balance

    def reserve(self, amount: int, allow_negative: bool = False) -> Reservation:
        """Hold an estimated cost before the call.

        Rejected when the hold would take the balance below zero, unless
        allow_negative is set (used only for the low-cost default model).
        """
        if amount < 0:
            raise ValueError("amount must be non-negative")
        if not allow_negative and self.balance - amount < 0:
            raise InsufficientFunds
        self.balance -= amount
        return Reservation(amount)

    def settle(self, reservation: Reservation, actual: int) -> None:
        """Replace the estimate with the real cost after the call."""
        if reservation.closed:
            raise ValueError("reservation already closed")
        if actual < 0:
            raise ValueError("actual cost must be non-negative")
        self.balance += reservation.amount - actual
        reservation.closed = True

    def release(self, reservation: Reservation) -> None:
        """Return the whole hold, for example when the call failed."""
        if reservation.closed:
            raise ValueError("reservation already closed")
        self.balance += reservation.amount
        reservation.closed = True


@dataclass(frozen=True)
class Plan:
    model: str
    downgraded: bool


def choose_model(
    balance: int,
    requested: str,
    default_model: str,
    daily_used: int,
    daily_limit: int,
) -> Plan:
    """Serve the requested model while credits last, then degrade, then stop."""
    if balance > 0:
        return Plan(requested, False)
    if daily_used < daily_limit:
        return Plan(default_model, True)
    raise QuotaExhausted("wallet empty and daily limit reached")


USAGE_TIERS = (
    (100, "exhausted"),
    (95, "severe"),
    (90, "critical"),
    (85, "high"),
    (80, "elevated"),
    (70, "moderate"),
    (60, "low"),
    (50, "notice"),
)


def usage_tier(percent_used: float) -> str:
    """Map the share of credits used to a tier clients can warn on."""
    for threshold, name in USAGE_TIERS:
        if percent_used >= threshold:
            return name
    return "normal"
