import asyncio
import os
import time

import cv2
from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import BusType
import mediapipe as mp  # type: ignore[import-untyped]
from mediapipe.tasks import python  # type: ignore[import-untyped]
from mediapipe.tasks.python import vision  # type: ignore[import-untyped]
import numpy as np


from mediapipe.tasks.python.components.containers.landmark import (  # type: ignore[import-untyped]  # isort: skip
    NormalizedLandmark,
)

MODEL_PATH = os.environ.get("FLIPOFF_MODEL_PATH")
DEBUG = os.environ.get("FLIPOFF_DRYRUN", "0") == "1"


async def poweroff() -> None:
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    proxy = bus.get_proxy_object(
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        None,
    )
    manager = proxy.get_interface("org.freedesktop.login1.Manager")
    await manager.call_power_off(False)


def is_flipping_off(hand: list[NormalizedLandmark]) -> bool:
    y_12 = hand[12].y
    y_10 = hand[10].y
    y_8 = hand[8].y
    y_6 = hand[6].y
    y_16 = hand[16].y
    y_14 = hand[14].y
    y_20 = hand[20].y
    y_18 = hand[18].y
    if (
        y_12 is None
        or y_10 is None
        or y_8 is None
        or y_6 is None
        or y_16 is None
        or y_14 is None
        or y_20 is None
        or y_18 is None
    ):
        return False
    return bool(y_12 < y_10 and y_8 > y_6 and y_16 > y_14 and y_20 > y_18)


async def async_poweroff() -> None:
    if DEBUG:
        print("DRYRUN: Would power off")
        return
    try:
        await poweroff()
    except Exception as e:
        print(f"Poweroff failed: {e}")


def main() -> None:
    if not MODEL_PATH:
        raise RuntimeError("FLIPOFF_MODEL_PATH environment variable not set")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        running_mode=vision.RunningMode.VIDEO,
    )

    detector = vision.HandLandmarker.create_from_options(options)
    cap: cv2.VideoCapture = cv2.VideoCapture(0)
    last_trigger: float = 0.0

    while True:
        ret: bool
        frame: np.ndarray
        ret, frame = cap.read()
        if not ret:
            break

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = detector.detect_for_video(mp_image, int(time.time() * 1000))

        if result.hand_landmarks:
            hand: list[NormalizedLandmark] = result.hand_landmarks[0]

            if DEBUG:
                for landmark in hand:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

            flipping = is_flipping_off(hand)
            if DEBUG:
                text = "FLIPPING OFF DETECTED" if flipping else "Waiting for gesture..."
                color = (0, 0, 255) if flipping else (0, 255, 0)
                cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            if flipping:
                now: float = time.time()
                if now - last_trigger > 2:
                    last_trigger = now
                    loop.run_until_complete(async_poweroff())

        cv2.imshow("Gesture Poweroff", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    loop.close()


if __name__ == "__main__":
    main()
