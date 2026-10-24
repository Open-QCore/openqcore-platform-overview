# Engineering decisions

Short records of design decisions and one post-mortem from building OpenQCore. Each one states the problem, what was decided, and the trade-offs. Numbers come from measurements on the running system.

| # | Record | Topic |
|---|---|---|
| 001 | [Provider-agnostic routing with transparent fallback](001-provider-fallback.md) | Reliability |
| 002 | [Cutting time-to-first-token from 7.9 s to 3.0 s](002-latency.md) | Performance |
| 003 | [Graceful downgrade when a wallet runs out](003-wallet-downgrade.md) | Billing |
| 004 | [Post-mortem: pricing lookup failed for some models](004-billing-postmortem.md) | Incident |

Runnable sketches of the ideas in 001 and 003, with tests, are in [`examples/`](../../examples/).

[Back to the platform overview](../../README.md)
