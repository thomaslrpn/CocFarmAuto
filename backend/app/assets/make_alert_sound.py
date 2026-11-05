"""Génère app/assets/alert.wav : carillon doux de deux notes montantes (la5 puis mi6).

Son original, calculé (aucun fichier tiers). Pour le modifier : changer les notes ou
la durée ci-dessous, puis `python -m app.assets.make_alert_sound` dans backend\.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

RATE = 44_100
NOTES = ((880.0, 0.00), (1318.5, 0.16))  # (fréquence en Hz, départ en secondes)
DURATION = 0.9
VOLUME = 0.45  # crête : volontairement modéré


def render() -> np.ndarray:
    t = np.arange(int(RATE * DURATION)) / RATE
    signal = np.zeros_like(t)
    for freq, start in NOTES:
        local = np.clip(t - start, 0, None)
        active = t >= start
        envelope = np.minimum(local / 0.006, 1.0) * np.exp(-local * 5.5)  # attaque 6 ms, extinction douce
        tone = np.sin(2 * np.pi * freq * local) + 0.25 * np.sin(2 * np.pi * 2 * freq * local)  # timbre de cloche
        signal += np.where(active, envelope * tone, 0.0)
    signal *= VOLUME / np.abs(signal).max()
    return (signal * 32767).astype(np.int16)


def main() -> None:
    target = Path(__file__).with_name("alert.wav")
    with wave.open(str(target), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(render().tobytes())
    print(f"Son écrit : {target}")


if __name__ == "__main__":
    main()
