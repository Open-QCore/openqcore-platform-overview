# 003. Graceful downgrade when a wallet runs out

**Status:** in use, final pre-launch development.

## Problem

Paid users consume a monthly credit balance. When the balance reaches zero, blocking chat completely is a poor experience, and it pushes users away exactly when they are engaged.

## Decision

Do not block. Degrade.

- Every personal subscription and every workspace has **its own wallet**.
- When a wallet reaches zero, requests are served by the low-cost default model under the same daily limit that free users get.
- When that daily limit is also used up, the request is rejected with a payment-required response and an upgrade or add-on prompt.
- The model change is not announced in the interface. This mirrors how consumer AI products behave when a plan's top model runs out, and it keeps the experience smooth.
- Clients receive the balance, the percentage used, and a usage tier from a single startup call, so the interface can warn earlier. Tiers escalate from `normal` through `notice`, `low`, `moderate`, `elevated`, `high`, `critical`, and `severe` to `exhausted`, at thresholds between 50% and 100%.

Accounting is **reserve, then settle**: an estimated cost is held before the call, and the real cost is settled afterwards. A runnable sketch, including the downgrade rule and the tiers, is in [`examples/wallet.py`](../../examples/wallet.py).

## Detail that mattered

Reservations are normally rejected when they would take the balance below zero. The downgrade path itself needs to reserve against an empty wallet, so that check is relaxed for the default model only. Every other model keeps the strict check.

## Trade-offs

- **Silent downgrade can surprise users** who notice a change in answer quality. Showing the tier in the interface partly offsets this.
- **The default model must always be billable and available.** The downgrade path depends on it, which is why [004](004-billing-postmortem.md) mattered.
