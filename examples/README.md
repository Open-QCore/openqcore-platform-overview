# Examples

Small, self-contained sketches of ideas used in OpenQCore. They were written for this repository to illustrate the design, they have no external dependencies, and they are not production code.

| File | Illustrates | Decision record |
|---|---|---|
| [`fallback_router.py`](fallback_router.py) | Ordered providers per model, then a low-cost default model, with timeouts and empty-reply handling | [001](../docs/decisions/001-provider-fallback.md) |
| [`tool_schema.py`](tool_schema.py) | Tools that declare parameters, validation that reports every problem, and a generic result summarizer | n/a |
| [`wallet.py`](wallet.py) | Reserve-then-settle accounting, the downgrade rule, and usage tiers | [003](../docs/decisions/003-wallet-downgrade.md) |

## Run the tests

```bash
pip install pytest
pytest examples
```

The same command runs in continuous integration on every push.
