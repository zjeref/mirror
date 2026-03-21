"""Flow registry - maps flow IDs to flow classes."""

from typing import Type

from app.chat.flows.base import BaseFlow

_registry: dict[str, Type[BaseFlow]] = {}


def register_flow(flow_class: Type[BaseFlow]) -> Type[BaseFlow]:
    """Decorator to register a flow class."""
    _registry[flow_class.flow_id] = flow_class
    return flow_class


def get_flow_class(flow_id: str) -> Type[BaseFlow] | None:
    return _registry.get(flow_id)


def get_all_flows() -> dict[str, Type[BaseFlow]]:
    return dict(_registry)
