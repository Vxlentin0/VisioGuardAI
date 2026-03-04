import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def extract_frames(
    video_path: str, skip_seconds: int = 5
) -> list[np.ndarray]:
    """Extract frames from a video at regular intervals.

    Args:
        video_path: Path to the video file.
        skip_seconds: Seconds between extracted frames.

    Returns:
        List of BGR numpy arrays (OpenCV frames).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("Failed to open video: %s", video_path)
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        logger.warning("Could not determine FPS for %s, defaulting to 30", video_path)
        fps = 30.0

    frame_interval = max(1, int(fps * skip_seconds))
    frames: list[np.ndarray] = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            frames.append(frame)
        frame_idx += 1

    cap.release()
    logger.info("Extracted %d frames from %s (every %ds)", len(frames), video_path, skip_seconds)
    return frames
