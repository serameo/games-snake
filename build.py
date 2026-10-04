# build.py -- One command build, clean and verify
import os
import shutil
import subprocess
import sys

DIST = "dist"
BUILD = "build"
EXE = os.path.join(DIST, "SnakeAdventure.exe")


def clean():
    for folder in (DIST, BUILD, "__pycache__"):
        if os.path.isdir(folder):
            shutil.rmtree(folder, ignore_errors=True)
            print("removed", folder)


def build():
    print("building, this takes about a minute...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "snake.spec", "--noconfirm"],
        check=False)
    if result.returncode != 0:
        print("BUILD FAILED")
        return False
    return True


def report():
    if not os.path.isfile(EXE):
        print("exe not found")
        return
    size_mb = os.path.getsize(EXE) / (1024 * 1024)
    print("\nDone!")
    print("  file: %s" % os.path.abspath(EXE))
    print("  size: %.1f MB" % size_mb)
    print("\nSend the single exe file to a friend. On first run it")
    print("creates a SnakeAdventure folder beside itself for maps")
    print("and high scores.")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    if build():
        report()