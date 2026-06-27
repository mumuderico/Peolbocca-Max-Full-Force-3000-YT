import os
import subprocess
import cv2
import numpy as np
import easyocr


def detect_text_mask(frame: np.ndarray, reader: easyocr.Reader) -> np.ndarray:
    results = reader.readtext(frame)
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    for (bbox, text, prob) in results:
        if prob < 0.3:
            continue
        pts = np.array(bbox, dtype=np.int32)
        x, y, w, h = cv2.boundingRect(pts)
        padding = 8
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(frame.shape[1], x + w + padding)
        y2 = min(frame.shape[0], y + h + padding)
        mask[y1:y2, x1:x2] = 255
    return mask


def inpaint_frame(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    if mask.max() == 0:
        return frame
    return cv2.inpaint(frame, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)


def remove_captions_local(input_path: str, output_path: str) -> str:
    reader = easyocr.Reader(["en"], gpu=True)

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    temp_path = output_path + ".noaudio.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        mask = detect_text_mask(frame, reader)
        clean_frame = inpaint_frame(frame, mask)
        out.write(clean_frame)

    cap.release()
    out.release()

    # Merge processed video with original audio (audio track is optional)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", temp_path,
            "-i", input_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0?",
            output_path,
        ],
        check=True,
        capture_output=True,
    )

    os.remove(temp_path)
    return output_path


def remove_captions(
    input_path: str,
    output_path: str,
    provider: str = "local",
    replicate_api_key: str = "",
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    if provider == "replicate":
        raise NotImplementedError(
            "Replicate provider is reserved for the SaaS version."
        )
    return remove_captions_local(input_path, output_path)
