import cv2

def extract_frames(video_path, skip_seconds=5):
    cap = cv2.VideoCapture(video_path)
    frames = []
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_interval = fps * skip_seconds

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            frames.append(frame)
        frame_idx += 1
    cap.release()
    return frames