"""Tests de la surveillance du processus parent."""
import subprocess
import sys
import threading

from app.parent_watch import watch_parent


def test_callback_when_parent_exits():
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.5)"])
    done = threading.Event()
    watch_parent(child.pid, done.set)
    assert done.wait(timeout=10)
    child.wait()


def test_callback_when_parent_already_gone():
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    done = threading.Event()
    watch_parent(child.pid, done.set)
    assert done.wait(timeout=10)
