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


def remove_captions_local(
    input_path: str,
    output_path: str,
    ocr_every_n_frames: int = 8,
    caption_zone: float = 0.35,
    progress_callback=None,
) -> str:
    reader = easyocr.Reader(["en"], gpu=True)

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Only scan the bottom portion of the frame where captions live
    roi_top = int(height * (1.0 - caption_zone))

    temp_path = output_path + ".noaudio.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

    current_mask = np.zeros((height, width), dtype=np.uint8)
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Re-run OCR only every N frames — captions don't change every frame
        if frame_idx % ocr_every_n_frames == 0:
            roi = frame[roi_top:, :]
            roi_mask = detect_text_mask(roi, reader)
            current_mask = np.zeros((height, width), dtype=np.uint8)
            current_mask[roi_top:, :] = roi_mask

        clean_frame = inpaint_frame(frame, current_mask)
        out.write(clean_frame)
        frame_idx += 1

        if progress_callback and total_frames > 0:
            progress_callback(frame_idx / total_frames)

    cap.release()
    out.release()

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
    ocr_every_n_frames: int = 8,
    caption_zone: float = 0.35,
    progress_callback=None,
) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    if provider == "replicate":
        raise NotImplementedError("Replicate provider is reserved for the SaaS version.")
    return remove_captions_local(
        input_path,
        output_path,
        ocr_every_n_frames=ocr_every_n_frames,
        caption_zone=caption_zone,
        progress_callback=progress_callback,
    )
