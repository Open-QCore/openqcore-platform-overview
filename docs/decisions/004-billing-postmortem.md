# 004. Post-mortem: pricing lookup failed for some models

**Status:** resolved. Found and fixed during pre-launch development.

## Summary

Billing settlement failed with a "no pricing configuration" error for any model whose provider had no provider-level fallback pricing row. That included the platform's default model, which the wallet downgrade path depends on ([003](003-wallet-downgrade.md)).

## Impact

Requests served by affected models could not be billed. Only two providers had a provider-level fallback pricing row. The Google provider did not, so every Google-backed model was affected, including the default model.

## Root cause

The pricing lookup matches a row by provider and, when available, by the concrete backend model. The settlement function never accepted or forwarded the backend model to the billing call, so lookups could only succeed through a provider-level row. Providers without one failed.

The cause was a missing parameter along one path, not a data problem. It stayed hidden because the providers that had fallback rows worked, so the common cases passed.

## Fix

- Added the backend model parameter to the settlement function and passed it at its single call site.
- Found a second issue while tracing the downgrade path: reservations were rejected against an empty wallet, which blocked the path's own reservation step. The check is now relaxed for the default model only, and every other model keeps the strict check.

## What made it hard to see

- The affected path (downgrade) was the least exercised path in the system.
- The failure depended on data configuration (which providers had fallback rows), so it did not show up with the first provider tested.

## Lessons and follow-ups

- A lookup that silently depends on fallback rows is a hidden coupling. Make the dependency explicit or remove it.
- Test the rarely used path, not only the common one.
- Planned: a regression test that settles one billing call for every configured model and fails if any model has no resolvable price.
