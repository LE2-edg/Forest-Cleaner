import importlib
import subprocess
import sys

REQUIRED_PACKAGES = [
    ("customtkinter", "customtkinter"),
    ("pygame", "pygame"),
    ("opencv-python", "cv2"),
    ("ursina", "ursina"),
    ("pillow", "PIL"),
]


def is_installed(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def install_package(package_name: str) -> bool:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False


def main() -> None:
    print("=== Forest Cleaner | Runbefore ===")
    print("Checking and installing required components...\n")

    failed_packages = []

    for package_name, module_name in REQUIRED_PACKAGES:
        if is_installed(module_name):
            print(f"[OK] {package_name} is already installed")
            continue

        print(f"[INSTALL] Installing {package_name}...")
        if install_package(package_name):
            print(f"[DONE] {package_name} installed")
        else:
            print(f"[ERROR] Failed to install {package_name}")
            failed_packages.append(package_name)

    print("\n=== Result ===")
    if failed_packages:
        print("Failed to install:")
        for package in failed_packages:
            print(f"- {package}")
        sys.exit(1)

    print("All components installed successfully.")
    print("You can now run the game via main.py")


if __name__ == "__main__":
    main()
