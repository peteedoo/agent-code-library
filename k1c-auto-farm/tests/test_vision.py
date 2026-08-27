"""Unit tests for bed-clear vision helpers (no printer required)."""

from __future__ import annotations

import numpy as np

from ai_detector import analyze_bed_clear


def _gray_bgr(value: int, h: int = 120, w: int = 160) -> np.ndarray:
    img = np.full((h, w, 3), value, dtype=np.uint8)
    return img


def test_identical_frames_are_clear():
    ref = _gray_bgr(40)
    cur = _gray_bgr(40)
    is_clear, confidence, pct = analyze_bed_clear(ref, cur, threshold=12.0)
    assert is_clear is True
    assert pct < 1.0
    assert confidence > 0.5


def test_large_blob_is_occupied():
    ref = _gray_bgr(40)
    cur = _gray_bgr(40)
    cur[20:100, 30:130] = 220  # bright rectangle ≈ part on bed
    is_clear, confidence, pct = analyze_bed_clear(ref, cur, threshold=12.0)
    assert is_clear is False
    assert pct > 12.0
    assert confidence < 0.5


def test_missing_images_not_clear():
    is_clear, confidence, pct = analyze_bed_clear(None, None)
    assert is_clear is False
    assert pct == 100.0
