from dataclasses import dataclass
from typing import Callable
from typing import ClassVar

from mediapipe.tasks.python.components.containers.landmark import NormalizedLandmark


@dataclass
class GestureResult:
    name: str
    detected: bool


class Gesture:
    name: ClassVar[str] = "unknown"

    def detect(self, hand: list[NormalizedLandmark]) -> bool:
        raise NotImplementedError


class GestureRegistry:
    _gestures: dict[str, type[Gesture]] = {}

    @classmethod
    def register(cls, gesture_class: type[Gesture]) -> type[Gesture]:
        cls._gestures[gesture_class.name] = gesture_class
        return gesture_class

    @classmethod
    def get(cls, name: str) -> type[Gesture] | None:
        return cls._gestures.get(name)

    @classmethod
    def all(cls) -> dict[str, type[Gesture]]:
        return cls._gestures.copy()


def _check_y_values(
    hand: list[NormalizedLandmark],
    *indices: int,
) -> bool:
    for idx in indices:
        if hand[idx].y is None:
            return False
    return True


@GestureRegistry.register
class FlippingOffGesture(Gesture):
    name = "flipping_off"

    def detect(self, hand: list[NormalizedLandmark]) -> bool:
        if not _check_y_values(hand, 12, 10, 8, 6, 16, 14, 20, 18):
            return False
        return bool(
            hand[12].y < hand[10].y
            and hand[8].y > hand[6].y
            and hand[16].y > hand[14].y
            and hand[20].y > hand[18].y
        )
