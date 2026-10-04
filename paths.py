# paths.py -- One place that knows where files live, frozen or not
import os
import shutil
import sys

APP_FOLDER = "SnakeAdventure"


def is_frozen():
    return getattr(sys, "frozen", False)


def bundle_dir():
    """Read-only folder: inside the exe when frozen, project root otherwise."""
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    """Writable folder: next to the exe when frozen, project root otherwise."""
    if not is_frozen():
        return bundle_dir()
    target = os.path.join(os.path.dirname(sys.executable), APP_FOLDER)
    os.makedirs(target, exist_ok=True)
    return target


def resource(*parts):
    """Path to a bundled asset. Never write here."""
    return os.path.join(bundle_dir(), *parts)


def user_file(*parts):
    """Path to a file the game may create or modify."""
    path = os.path.join(data_dir(), *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def levels_dir():
    """Writable levels folder, seeded from the bundle on first run."""
    target = os.path.join(data_dir(), "levels")
    os.makedirs(target, exist_ok=True)
    _seed(resource("levels"), target)
    return target


def _seed(source, target):
    """Copy bundled maps out once so the editor can edit them."""
    if not os.path.isdir(source) or os.path.abspath(source) == \
            os.path.abspath(target):
        return
    for name in os.listdir(source):
        if not name.lower().endswith(".txt"):
            continue
        destination = os.path.join(target, name)
        if not os.path.exists(destination):
            try:
                shutil.copyfile(os.path.join(source, name), destination)
            except OSError:
                pass