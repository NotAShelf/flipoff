from typing import ClassVar

from mediapipe.tasks.python.components.containers.landmark import NormalizedLandmark


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


@GestureRegistry.register
class FlippingOffGesture(Gesture):
    name = "flipping_off"

    def detect(self, hand: list[NormalizedLandmark]) -> bool:
        # MediaPipe always returns 21 landmarks; guard against malformed results.
        if len(hand) < 21:
            return False
        return bool(
            hand[12].y < hand[10].y  # middle tip above middle PIP (extended)
            and hand[8].y > hand[6].y  # index tip below index PIP (curled)
            and hand[16].y > hand[14].y  # ring tip below ring PIP (curled)
            and hand[20].y > hand[18].y  # pinky tip below pinky PIP (curled)
        )
