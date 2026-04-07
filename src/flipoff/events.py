from abc import ABC
from abc import abstractmethod
import asyncio
import os
from typing import ClassVar


class Event(ABC):
    name: ClassVar[str] = "unknown"

    @abstractmethod
    async def trigger(self) -> None:
        raise NotImplementedError


class PoweroffEvent(Event):
    name = "poweroff"

    async def trigger(self) -> None:
        if os.environ.get("FLIPOFF_DRYRUN", "0") == "1":
            print("DRYRUN: Would power off")
            return
        try:
            await self._poweroff()
        except Exception as e:
            print(f"Poweroff failed: {e}")

    async def _poweroff(self) -> None:
        from dbus_next.aio.message_bus import MessageBus
        from dbus_next.constants import BusType

        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        try:
            proxy = bus.get_proxy_object(
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
                None,
            )
            manager = proxy.get_interface("org.freedesktop.login1.Manager")
            await manager.call_power_off(False)
        finally:
            await bus.disconnect()


class EventRegistry:
    _events: dict[str, type[Event]] = {}

    @classmethod
    def register(cls, event_class: type[Event]) -> type[Event]:
        cls._events[event_class.name] = event_class
        return event_class

    @classmethod
    def get(cls, name: str) -> type[Event] | None:
        return cls._events.get(name)

    @classmethod
    def all(cls) -> dict[str, type[Event]]:
        return cls._events.copy()


EventRegistry.register(PoweroffEvent)
