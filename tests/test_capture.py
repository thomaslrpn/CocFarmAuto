import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.capture.screen import CaptureError, grab_region, save_capture  # noqa: E402
from app.capture.window import WindowRect  # noqa: E402
from app.config import Settings  # noqa: E402


def test_save_capture_writes_timestamped_png(tmp_path):
    img = Image.new("RGB", (10, 10), "red")
    path = save_capture(img, tmp_path / "shots")
    assert path.exists() and path.suffix == ".png"
    assert path.name.startswith("capture_")
    assert Image.open(path).size == (10, 10)


def test_grab_region_rejects_invalid_rect():
    with pytest.raises(CaptureError):
        grab_region(WindowRect(0, 0, 0, 100))


def test_window_rect_to_mss_region():
    assert WindowRect(1, 2, 3, 4).as_mss_region() == {"left": 1, "top": 2, "width": 3, "height": 4}


def test_settings_use_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("COC_AUTOFARM_DATA_DIR", str(tmp_path))
    s = Settings.load()
    assert s.data_dir == tmp_path
    assert s.screenshots_dir == tmp_path / "screenshots"
