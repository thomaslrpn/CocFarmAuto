"""Le numéro de version doit être identique partout (mis à jour par desktop/scripts/release.ps1)."""
import json
import re
from pathlib import Path

from app.config import APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")


def _json_version(relative: str) -> str:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))["version"]


def _toml_package_version(relative: str) -> str:
    match = re.search(r'^\[package\][^\[]*?^version = "([^"]+)"', (ROOT / relative).read_text(encoding="utf-8"),
                      re.MULTILINE | re.DOTALL)
    assert match, f"version introuvable dans {relative}"
    return match.group(1)


def test_version_is_semver():
    assert SEMVER.match(APP_VERSION)


def test_versions_are_consistent():
    lock = (ROOT / "desktop/src-tauri/Cargo.lock").read_text(encoding="utf-8")
    lock_version = re.search(r'name = "coc-autofarm"\r?\nversion = "([^"]+)"', lock)
    assert lock_version
    versions = {
        "backend/app/config.py": APP_VERSION,
        "desktop/src-tauri/tauri.conf.json": _json_version("desktop/src-tauri/tauri.conf.json"),
        "desktop/src-tauri/Cargo.toml": _toml_package_version("desktop/src-tauri/Cargo.toml"),
        "desktop/src-tauri/Cargo.lock": lock_version.group(1),
        "desktop/package.json": _json_version("desktop/package.json"),
        "frontend/package.json": _json_version("frontend/package.json"),
    }
    assert len(set(versions.values())) == 1, versions


def test_changelog_has_current_version():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert re.search(rf"^## {re.escape(APP_VERSION)}\b", changelog, re.MULTILINE)
