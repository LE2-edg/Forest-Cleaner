#!/usr/bin/env python3
"""
Forest Cleaner — Universal Launcher
Automatically installs dependencies and launches the game.
Works on any PC with Python 3.8+.
"""
import importlib
import subprocess
import sys
import os

# Minimum Python version
MIN_PYTHON = (3, 8)

REQUIRED_PACKAGES = [
    ("ursina", "ursina"),
    ("pillow", "PIL"),
]


def check_python_version():
    if sys.version_info < MIN_PYTHON:
        print(f"[ERROR] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required")
        print(f"        Installed: Python {sys.version_info.major}.{sys.version_info.minor}")
        print("        Download Python: https://www.python.org/downloads/")
        input("Press Enter to exit...")
        sys.exit(1)


def is_installed(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def install_package(package_name):
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package_name],
            stdout=subprocess.DEVNULL if os.name == 'nt' else None,
            stderr=subprocess.STDOUT,
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def ensure_pip():
    """Make sure pip is available."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[INFO] pip not found, installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
        except Exception:
            print("[ERROR] Failed to install pip.")
            print("        Run manually: python -m ensurepip --upgrade")
            input("Press Enter to exit...")
            sys.exit(1)


def install_dependencies():
    failed = []
    for package_name, module_name in REQUIRED_PACKAGES:
        if is_installed(module_name):
            print(f"  [OK] {package_name}")
            continue
        print(f"  [INSTALLING] {package_name}...", end=" ", flush=True)
        if install_package(package_name):
            print("done")
        else:
            print("ERROR")
            failed.append(package_name)
    return failed


def main():
    print("=" * 50)
    print("  Forest Cleaner — Launching game")
    print("=" * 50)

    # 1. Check Python
    check_python_version()
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # 2. Check pip
    ensure_pip()

    # 3. Install dependencies
    print("\nChecking dependencies:")
    failed = install_dependencies()

    if failed:
        print(f"\n[ERROR] Failed to install: {', '.join(failed)}")
        print("Try manually:")
        for pkg in failed:
            print(f"  pip install {pkg}")
        input("Press Enter to exit...")
        sys.exit(1)

    # 4. Launch game
    print("\nLaunching Forest Cleaner...")
    game_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test", "main.py")

    if not os.path.exists(game_script):
        print(f"[ERROR] Game file not found: {game_script}")
        input("Press Enter to exit...")
        sys.exit(1)

    os.chdir(os.path.dirname(game_script))
    try:
        result = subprocess.run([sys.executable, game_script])
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n[ERROR] {e}")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
