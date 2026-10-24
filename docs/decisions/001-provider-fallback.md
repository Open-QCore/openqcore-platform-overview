# 001. Provider-agnostic routing with transparent fallback

**Status:** in use, final pre-launch development.

## Problem

The platform serves models from several providers (OpenAI, Anthropic, Google). Availability, latency, and pricing differ per provider, and any of them can fail or time out. A conversation should not fail because one provider did.

## Decision

Treat models as interchangeable resources behind one interface.

- A model identifier resolves to an ordered list: a primary provider and registered fallbacks.
- Providers implement one interface, including native tool calling, so the rest of the system does not know which provider answered.
- If the primary and all registered fallbacks fail, the same request is retried against a low-cost default model before an error reaches the user. The retry is transparent to the user.
- An empty reply is treated as a failure too: the retry safety net covers both the tool path and the direct, no-tool path.

A runnable sketch of the routing logic is in [`examples/fallback_router.py`](../../examples/fallback_router.py).

## Trade-offs

- **Quality can change silently.** A fallback answer may come from a weaker model. This is accepted because an answer from a weaker model is better than an error, and the cost of the alternative (a failed conversation) is higher.
- **Every model needs pricing for every provider that can serve it.** A missing pricing row turns a successful fallback into a billing failure. This was found the hard way, see [004](004-billing-postmortem.md).
- **Retries add latency in the failure case only.** The happy path has no extra work.

## Not covered yet

A circuit breaker that skips a provider after repeated failures, so a long outage does not cost one timeout per request.
