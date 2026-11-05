import pytest
from PIL import Image

from app.capture.screen import CaptureError, CaptureMethod, grab_region, grab_window, is_blank, save_capture
from app.capture.window import GameWindow, WindowRect
from app.config import Settings


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
    assert s.observations_dir == tmp_path / "observations"


def test_is_blank_detects_black_image():
    assert is_blank(Image.new("RGB", (20, 20), "black"))
    assert not is_blank(Image.new("RGB", (20, 20), (90, 140, 200)))


def _fake_window() -> GameWindow:
    return GameWindow(hwnd=1, title="Clash of Clans", rect=WindowRect(0, 0, 10, 10))


def test_grab_window_falls_back_to_screen_when_printwindow_is_black(monkeypatch):
    import app.capture.screen as screen

    screen_image = Image.new("RGB", (10, 10), "blue")
    monkeypatch.setattr(screen, "print_window", lambda *a: Image.new("RGB", (10, 10), "black"))
    monkeypatch.setattr(screen, "grab_region", lambda rect: screen_image)

    image, used = grab_window(_fake_window(), CaptureMethod.AUTO)
    assert used is CaptureMethod.SCREEN and image is screen_image


def test_grab_window_prefers_printwindow(monkeypatch):
    import app.capture.screen as screen

    window_image = Image.new("RGB", (10, 10), "green")
    monkeypatch.setattr(screen, "print_window", lambda *a: window_image)
    monkeypatch.setattr(screen, "grab_region", lambda rect: pytest.fail("ne doit pas capturer l'écran"))

    image, used = grab_window(_fake_window(), CaptureMethod.AUTO)
    assert used is CaptureMethod.WINDOW and image is window_image


def test_grab_window_strict_mode_raises_on_black(monkeypatch):
    import app.capture.screen as screen

    monkeypatch.setattr(screen, "print_window", lambda *a: Image.new("RGB", (10, 10), "black"))
    with pytest.raises(CaptureError):
        grab_window(_fake_window(), CaptureMethod.WINDOW)
