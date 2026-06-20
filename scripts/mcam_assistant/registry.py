from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class Adapter(Protocol):
    name: str
    family: str


@dataclass
class PluginRegistry:
    """Small adapter registry for future CAM, machine, control, and report modules."""

    adapters: dict[str, dict[str, Adapter]] = field(default_factory=dict)

    def register(self, adapter: Adapter) -> None:
        self.adapters.setdefault(adapter.family, {})[adapter.name] = adapter

    def get(self, family: str, name: str) -> Adapter:
        return self.adapters[family][name]

    def first(self, family: str) -> Adapter:
        family_adapters = self.adapters.get(family, {})
        if not family_adapters:
            raise KeyError(f"No adapters registered for family '{family}'")
        return next(iter(family_adapters.values()))

    def describe(self) -> dict[str, list[str]]:
        return {family: sorted(items) for family, items in sorted(self.adapters.items())}
