import time
from typing import Callable

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.components.containers.landmark import NormalizedLandmark
import numpy as np


class HandDetector:
    def __init__(
        self,
        model_path: str,
        num_hands: int = 1,
    ) -> None:
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=num_hands,
            running_mode=vision.RunningMode.VIDEO,
        )
        self._detector = vision.HandLandmarker.create_from_options(options)

    def detect(
        self,
        frame: np.ndarray,
        timestamp_ms: int | None = None,
    ) -> list[list[NormalizedLandmark]]:
        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = self._detector.detect_for_video(mp_image, timestamp_ms)
        return result.hand_landmarks if result.hand_landmarks else []

    def close(self) -> None:
        self._detector.close()


class Camera:
    def __init__(self, index: int = 0) -> None:
        self._cap = cv2.VideoCapture(index)

    def read(self) -> tuple[bool, np.ndarray]:
        ret, frame = self._cap.read()
        return ret, frame

    def release(self) -> None:
        self._cap.release()


class GestureDetector:
    def __init__(
        self,
        detector: HandDetector,
        gesture_callback: Callable[[list[NormalizedLandmark]], bool],
    ) -> None:
        self._detector = detector
        self._callback = gesture_callback

    def process_frame(self, frame: np.ndarray) -> bool | None:
        hands = self._detector.detect(frame)
        if hands:
            return self._callback(hands[0])
        return None

    def close(self) -> None:
        self._detector.close()
