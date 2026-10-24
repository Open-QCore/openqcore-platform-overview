"""Illustrative tool registry with explicit parameter schemas.

Every tool declares its parameters, and arguments are validated before the
tool runs. A generic summarizer turns any result shape into bounded text for
the model. Written as an example for this repository; not production code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

_PY_TYPES: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
}


class ToolArgumentError(ValueError):
    """Raised with every problem found, not just the first."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class Param:
    name: str
    type: str  # "string" | "integer" | "number" | "boolean"
    required: bool = True
    enum: tuple[Any, ...] | None = None


@dataclass
class Tool:
    name: str
    description: str
    params: tuple[Param, ...]
    fn: Callable[..., Any]

    def validate(self, args: dict[str, Any]) -> dict[str, Any]:
        problems: list[str] = []
        known = {p.name for p in self.params}
        for p in self.params:
            if p.name not in args:
                if p.required:
                    problems.append(f"missing: {p.name}")
                continue
            value = args[p.name]
            expected = _PY_TYPES[p.type]
            is_bool = isinstance(value, bool)
            numeric = p.type in ("integer", "number")
            if (numeric and is_bool) or not isinstance(value, expected):
                problems.append(f"{p.name}: expected {p.type}")
            elif p.enum is not None and value not in p.enum:
                problems.append(f"{p.name}: must be one of {list(p.enum)}")
        for name in args:
            if name not in known:
                problems.append(f"unexpected: {name}")
        if problems:
            raise ToolArgumentError(problems)
        return args

    def call(self, args: dict[str, Any]) -> Any:
        return self.fn(**self.validate(args))


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    def call(self, name: str, args: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name].call(args)


def summarize_result(result: Any, max_chars: int = 1000) -> str:
    """Serialize any result shape and bound its size before it reaches the model."""
    text = json.dumps(result, default=str, ensure_ascii=False)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"... [truncated, {len(text) - max_chars} more characters]"
