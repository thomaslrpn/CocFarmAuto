"""Surveillance du processus parent (l'application de bureau).

Si l'application se ferme brutalement (plantage, fin de tâche), elle ne peut pas
demander l'arrêt du moteur : sans cette surveillance, le moteur resterait
orphelin en arrière-plan. Ici, un thread attend la fin du parent puis déclenche
l'arrêt propre du moteur.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)

SYNCHRONIZE = 0x00100000  # droit Windows « attendre la fin du processus »
INFINITE = 0xFFFFFFFF
POLL_INTERVAL_S = 2.0


def _wait_windows(pid: int) -> bool:
    """Bloque jusqu'à la fin du processus `pid`. False si on ne peut pas le surveiller."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        return False
    try:
        kernel32.WaitForSingleObject(handle, INFINITE)
    finally:
        kernel32.CloseHandle(handle)
    return True


def _wait_posix(pid: int) -> bool:
    while True:
        try:
            os.kill(pid, 0)  # signal 0 : teste seulement l'existence du processus
        except OSError:
            return True
        time.sleep(POLL_INTERVAL_S)


def watch_parent(pid: int, on_parent_exit: Callable[[], None]) -> threading.Thread:
    """Lance la surveillance dans un thread ; `on_parent_exit` est appelé à la fin du parent."""
    def run() -> None:
        watched = _wait_windows(pid) if sys.platform == "win32" else _wait_posix(pid)
        if not watched:
            logger.warning("Processus parent %d introuvable : arrêt du moteur", pid)
        else:
            logger.info("Application fermée (processus %d) : arrêt du moteur", pid)
        on_parent_exit()

    thread = threading.Thread(target=run, name="parent-watch", daemon=True)
    thread.start()
    return thread
