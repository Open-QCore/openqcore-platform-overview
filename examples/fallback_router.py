"""Illustrative provider router with transparent fallback.

A small, self-contained sketch of the routing idea described in
docs/decisions/001-provider-fallback.md. It is written for this repository
as an example and is not production code.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Iterator

Provider = Callable[[str], Awaitable[str]]
Attempt = tuple[str, str, str]  # (model, provider, error type)


class ProviderError(Exception):
    """Raised by a provider call that failed."""


class AllProvidersFailed(Exception):
    """Raised when the requested model and the default model both failed."""

    def __init__(self, attempts: list[Attempt]):
        super().__init__(f"all providers failed: {attempts}")
        self.attempts = attempts


@dataclass
class Result:
    text: str
    model: str  # the model that actually answered
    provider: str  # the provider that actually answered
    degraded: bool  # True when the default model answered instead
    attempts: list[Attempt] = field(default_factory=list)  # failures before success


class Router:
    """Resolve a model to ordered providers, then fall back to a default model."""

    def __init__(
        self,
        providers: dict[str, Provider],
        routes: dict[str, list[str]],
        default_model: str,
        timeout_s: float = 30.0,
    ):
        if default_model not in routes:
            raise ValueError("default_model must have a route")
        self.providers = providers
        self.routes = routes
        self.default_model = default_model
        self.timeout_s = timeout_s

    def _plan(self, model: str) -> Iterator[tuple[str, bool]]:
        yield model, False
        if model != self.default_model:
            yield self.default_model, True

    async def complete(self, model: str, prompt: str) -> Result:
        if model not in self.routes:
            raise ValueError(f"unknown model: {model}")
        attempts: list[Attempt] = []
        for candidate, degraded in self._plan(model):
            for provider_name in self.routes[candidate]:
                try:
                    text = await asyncio.wait_for(
                        self.providers[provider_name](prompt), self.timeout_s
                    )
                    if not text.strip():  # an empty reply counts as a failure
                        raise ProviderError("empty reply")
                except (ProviderError, asyncio.TimeoutError) as exc:
                    attempts.append((candidate, provider_name, type(exc).__name__))
                    continue
                return Result(text, candidate, provider_name, degraded, attempts)
        raise AllProvidersFailed(attempts)
