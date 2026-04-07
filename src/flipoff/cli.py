import argparse
import asyncio
import os
import time

import cv2

from flipoff.detector import Camera
from flipoff.detector import HandDetector
from flipoff.events import EventRegistry
from flipoff.gesture import Gesture
from flipoff.gesture import GestureRegistry


def _get_callback(
    gesture_cls: type[Gesture],
    event_instance: object,
    cooldown: float,
    last_trigger: list[float],
) -> callable:
    def callback(hand: object) -> bool:
        gesture_detected = gesture_cls().detect(hand)
        if gesture_detected:
            now = time.time()
            if now - last_trigger[0] > cooldown:
                last_trigger[0] = now
                asyncio.create_task(event_instance.trigger())  # type: ignore[attr-defined]
        return gesture_detected

    return callback


def run(
    gesture_name: str,
    event_name: str,
    headless: bool,
    camera_index: int,
    cooldown: float,
    debug: bool,
) -> None:
    model_path = os.environ.get("FLIPOFF_MODEL_PATH")
    if not model_path:
        raise RuntimeError("FLIPOFF_MODEL_PATH environment variable not set")

    gesture_cls = GestureRegistry.get(gesture_name)
    if not gesture_cls:
        raise ValueError(f"Unknown gesture: {gesture_name}")
    event_cls = EventRegistry.get(event_name)
    if not event_cls:
        raise ValueError(f"Unknown event: {event_name}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    detector = HandDetector(model_path)
    camera = Camera(camera_index)
    event_instance = event_cls()

    gesture_instance = gesture_cls()
    last_trigger = [0.0]

    callback = _get_callback(gesture_cls, event_instance, cooldown, last_trigger)

    while True:
        ret, frame = camera.read()
        if not ret:
            break

        hands = detector.detect(frame)
        if hands:
            callback(hands[0])

            if debug:
                for landmark in hands[0]:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

                flipping = gesture_instance.detect(hands[0])
                text = f"{gesture_name.upper()} DETECTED" if flipping else "Waiting for gesture..."
                color = (0, 0, 255) if flipping else (0, 255, 0)
                cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        if not headless:
            cv2.imshow("Gesture Poweroff", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    camera.release()
    if not headless:
        cv2.destroyAllWindows()
    detector.close()
    loop.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Hand gesture event utility")
    parser.add_argument(
        "--gesture",
        type=str,
        default="flipping_off",
        choices=list(GestureRegistry.all().keys()),
        help="Gesture to detect",
    )
    parser.add_argument(
        "--event",
        type=str,
        default="poweroff",
        choices=list(EventRegistry.all().keys()),
        help="Event to trigger on gesture",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Hide GUI window and run in headless mode",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera index to use",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=2.0,
        help="Cooldown between event triggers in seconds",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug visualizations",
    )
    args = parser.parse_args()

    run(
        gesture_name=args.gesture,
        event_name=args.event,
        headless=args.headless,
        camera_index=args.camera,
        cooldown=args.cooldown,
        debug=args.debug or os.environ.get("FLIPOFF_DRYRUN", "0") == "1",
    )


if __name__ == "__main__":
    main()
