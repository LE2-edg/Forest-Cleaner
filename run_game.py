#!/usr/bin/env python3
"""
Forest Cleaner — Universal Launcher
Автоматически устанавливает зависимости и запускает игру.
Работает на любом ПК с Python 3.8+.
"""
import importlib
import subprocess
import sys
import os

# Минимальная версия Python
MIN_PYTHON = (3, 8)

REQUIRED_PACKAGES = [
    ("ursina", "ursina"),
    ("pillow", "PIL"),
]


def check_python_version():
    if sys.version_info < MIN_PYTHON:
        print(f"[ОШИБКА] Требуется Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+")
        print(f"         Установлен: Python {sys.version_info.major}.{sys.version_info.minor}")
        print("         Скачайте Python: https://www.python.org/downloads/")
        input("Нажмите Enter для выхода...")
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
        print("[INFO] pip не найден, устанавливаю...")
        try:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
        except Exception:
            print("[ОШИБКА] Не удалось установить pip.")
            print("         Запустите вручную: python -m ensurepip --upgrade")
            input("Нажмите Enter для выхода...")
            sys.exit(1)


def install_dependencies():
    failed = []
    for package_name, module_name in REQUIRED_PACKAGES:
        if is_installed(module_name):
            print(f"  [OK] {package_name}")
            continue
        print(f"  [УСТАНОВКА] {package_name}...", end=" ", flush=True)
        if install_package(package_name):
            print("готово")
        else:
            print("ОШИБКА")
            failed.append(package_name)
    return failed


def main():
    print("=" * 50)
    print("  Forest Cleaner — Запуск игры")
    print("=" * 50)

    # 1. Проверка Python
    check_python_version()
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # 2. Проверка pip
    ensure_pip()

    # 3. Установка зависимостей
    print("\nПроверка зависимостей:")
    failed = install_dependencies()

    if failed:
        print(f"\n[ОШИБКА] Не удалось установить: {', '.join(failed)}")
        print("Попробуйте вручную:")
        for pkg in failed:
            print(f"  pip install {pkg}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

    # 4. Запуск игры
    print("\nЗапуск Forest Cleaner...")
    game_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test", "main.py")

    if not os.path.exists(game_script):
        print(f"[ОШИБКА] Не найден файл игры: {game_script}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

    os.chdir(os.path.dirname(game_script))
    try:
        result = subprocess.run([sys.executable, game_script])
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n[ОШИБКА] {e}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)


if __name__ == "__main__":
    main()
