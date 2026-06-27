import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from modules.caption_remover import (
    detect_text_mask,
    inpaint_frame,
    remove_captions,
)


def test_detect_text_mask_no_text_returns_zero_mask():
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    mock_reader = MagicMock()
    mock_reader.readtext.return_value = []

    mask = detect_text_mask(frame, mock_reader)

    assert mask.shape == (100, 200)
    assert mask.dtype == np.uint8
    assert mask.max() == 0


def test_detect_text_mask_with_text_marks_region():
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    mock_reader = MagicMock()
    mock_reader.readtext.return_value = [
        ([[10, 80], [100, 80], [100, 95], [10, 95]], "Hello", 0.95)
    ]

    mask = detect_text_mask(frame, mock_reader)

    assert mask.max() == 255
    assert mask[87, 55] == 255  # center of the bbox should be masked


def test_detect_text_mask_ignores_low_confidence():
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    mock_reader = MagicMock()
    mock_reader.readtext.return_value = [
        ([[10, 80], [100, 80], [100, 95], [10, 95]], "blurry", 0.1)
    ]

    mask = detect_text_mask(frame, mock_reader)

    assert mask.max() == 0


def test_inpaint_frame_empty_mask_returns_original():
    frame = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
    mask = np.zeros((100, 200), dtype=np.uint8)

    result = inpaint_frame(frame, mask)

    np.testing.assert_array_equal(result, frame)


def test_inpaint_frame_with_mask_modifies_masked_region():
    frame = np.ones((100, 200, 3), dtype=np.uint8) * 200
    frame[80:95, 10:100] = 0  # black text region on white background
    mask = np.zeros((100, 200), dtype=np.uint8)
    mask[80:95, 10:100] = 255

    result = inpaint_frame(frame, mask)

    assert result.shape == frame.shape
    # Masked region should have been reconstructed (not stay black)
    assert not np.array_equal(result[80:95, 10:100], frame[80:95, 10:100])


def test_remove_captions_local_provider_calls_local(tmp_path, mocker):
    input_path = str(tmp_path / "input.mp4")
    output_path = str(tmp_path / "output.mp4")
    with open(input_path, "wb") as f:
        f.write(b"fake video data")

    mock_local = mocker.patch(
        "modules.caption_remover.remove_captions_local",
        return_value=output_path,
    )

    result = remove_captions(input_path, output_path, provider="local")

    assert result == output_path
    mock_local.assert_called_once_with(input_path, output_path)


def test_remove_captions_replicate_provider_raises_not_implemented(tmp_path):
    with pytest.raises(NotImplementedError, match="SaaS"):
        remove_captions("input.mp4", "output.mp4", provider="replicate")
