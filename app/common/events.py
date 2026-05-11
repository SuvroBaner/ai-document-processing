"""In-process domain event bus.

Swappable for Redis Streams / Kafka later without changing the publishing API.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class DomainEvent:
    name: str
    payload: dict[str, Any]
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actor_user_id: UUID | None = None


Subscriber = Callable[[DomainEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._wildcards: list[Subscriber] = []

    def subscribe(self, event_name: str, handler: Subscriber) -> None:
        self._subscribers[event_name].append(handler)

    def subscribe_all(self, handler: Subscriber) -> None:
        self._wildcards.append(handler)

    def publish(self, event: DomainEvent) -> None:
        logger.info("domain_event.published", event=event.name, payload=event.payload)
        for handler in self._subscribers.get(event.name, []):
            self._safe(handler, event)
        for handler in self._wildcards:
            self._safe(handler, event)

    @staticmethod
    def _safe(handler: Subscriber, event: DomainEvent) -> None:
        try:
            handler(event)
        except Exception:  # noqa: BLE001
            logger.exception("domain_event.handler_failed", event=event.name)


_bus = EventBus()


def get_event_bus() -> EventBus:
    return _bus
