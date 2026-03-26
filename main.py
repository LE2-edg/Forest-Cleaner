"""
Forest Cleaner — Launcher
A lightweight GUI launcher that:
  • checks / installs only the packages the game actually needs
  • lets the user pick a language (default: English)
  • shows a game-themed banner (procedurally generated)
  • launches the 3-D game with one click
"""

import importlib
import json
import os
import subprocess
import sys
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Paths ──────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(BASE_DIR, "ports", "windows", "data")
DATA_FILE = os.path.join(DATA_DIR, "data.json")
LANGUAGES_FILE = os.path.join(DATA_DIR, "languages.json")
GAME_SCRIPT = os.path.join(BASE_DIR, "test", "main.py")

# ── Packages the *game* really needs (pip-name → import-name) ─────────────
GAME_PACKAGES = [
    ("ursina", "ursina"),
    ("pillow", "PIL"),
]
# The launcher itself needs customtkinter (no pygame / opencv!)
LAUNCHER_PACKAGES = [
    ("customtkinter", "customtkinter"),
]

# ── Languages (built-in fallback — works even without languages.json) ──────
BUILTIN_LANGUAGES = {
    "en": {
        "language_name": "English",
        "launcher_title": "Forest Cleaner — Launcher",
        "play": "PLAY",
        "download_resources": "Download Resources",
        "downloading": "Downloading…",
        "all_installed": "All resources already installed!",
        "install_ok": "Resources installed successfully!",
        "install_fail": "Some packages failed to install:",
        "language_label": "Language",
        "status_ready": "Ready to play",
        "status_missing": "Resources not installed",
    },
    "fr": {
        "language_name": "Français",
        "launcher_title": "Forest Cleaner — Lanceur",
        "play": "JOUER",
        "download_resources": "Télécharger les ressources",
        "downloading": "Téléchargement…",
        "all_installed": "Toutes les ressources sont déjà installées !",
        "install_ok": "Ressources installées avec succès !",
        "install_fail": "Certains paquets n'ont pas pu être installés :",
        "language_label": "Langue",
        "status_ready": "Prêt à jouer",
        "status_missing": "Ressources non installées",
    },
    "es": {
        "language_name": "Español",
        "launcher_title": "Forest Cleaner — Lanzador",
        "play": "JUGAR",
        "download_resources": "Descargar recursos",
        "downloading": "Descargando…",
        "all_installed": "¡Todos los recursos ya están instalados!",
        "install_ok": "¡Recursos instalados correctamente!",
        "install_fail": "Algunos paquetes no se pudieron instalar:",
        "language_label": "Idioma",
        "status_ready": "Listo para jugar",
        "status_missing": "Recursos no instalados",
    },
    "ru": {
        "language_name": "Русский",
        "launcher_title": "Forest Cleaner — Лаунчер",
        "play": "ИГРАТЬ",
        "download_resources": "Скачать ресурсы",
        "downloading": "Загрузка…",
        "all_installed": "Все ресурсы уже установлены!",
        "install_ok": "Ресурсы успешно установлены!",
        "install_fail": "Не удалось установить некоторые пакеты:",
        "language_label": "Язык",
        "status_ready": "Готово к игре",
        "status_missing": "Ресурсы не установлены",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════
def _load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _get_saved_lang():
    """Return the saved language code, or 'en' as default."""
    d = _load_json(DATA_FILE)
    lang = d.get("language_selected")
    if lang and lang != "None":
        return lang
    return "en"


def _set_saved_lang(code):
    d = _load_json(DATA_FILE)
    d["language_selected"] = code
    _save_json(DATA_FILE, d)


def _get_languages():
    """Merge on-disk languages.json with the built-in fallback."""
    disk = _load_json(LANGUAGES_FILE, {})
    merged = dict(BUILTIN_LANGUAGES)
    for code, texts in disk.items():
        if code in merged:
            merged[code].update(texts)
        else:
            merged[code] = texts
    return merged


def _is_installed(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def _all_game_packages_installed():
    return all(_is_installed(mod) for _, mod in GAME_PACKAGES)


def _install_package(pip_name):
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pip_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  Ensure the launcher's own dependency (customtkinter) is available
# ═══════════════════════════════════════════════════════════════════════════
def _bootstrap_launcher():
    if not _is_installed("customtkinter"):
        print("[Launcher] Installing customtkinter…")
        if not _install_package("customtkinter"):
            print("[ERROR] Could not install customtkinter.  Run:")
            print("        pip install customtkinter")
            sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
#  Procedural banner (game-themed — no external file needed)
# ═══════════════════════════════════════════════════════════════════════════
def _make_banner(width=920, height=280):
    """Draw a simple nature-themed banner with PIL.  Returns a PIL Image
    or None if PIL is not yet installed."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)

    # Sky gradient
    for y in range(height):
        t = y / height
        r = int(40 + 120 * t)
        g = int(130 + 80 * t)
        b = int(70 + 60 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Ground
    ground_y = int(height * 0.70)
    for y in range(ground_y, height):
        t = (y - ground_y) / (height - ground_y)
        r = int(34 + 20 * t)
        g = int(100 - 40 * t)
        b = int(20 + 10 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    import math, random as _rng
    _rng.seed(42)

    # Trees
    for _ in range(18):
        tx = _rng.randint(20, width - 20)
        ty = _rng.randint(ground_y - 30, ground_y + 15)
        trunk_h = _rng.randint(28, 55)
        trunk_w = _rng.randint(4, 7)
        draw.rectangle(
            [tx - trunk_w // 2, ty - trunk_h, tx + trunk_w // 2, ty],
            fill=(90 + _rng.randint(-15, 15), 60 + _rng.randint(-10, 10), 30, 255),
        )
        cw = _rng.randint(16, 32)
        ch = _rng.randint(30, 55)
        pts = [(tx, ty - trunk_h - ch),
               (tx - cw, ty - trunk_h + 5),
               (tx + cw, ty - trunk_h + 5)]
        draw.polygon(pts, fill=(30 + _rng.randint(-10, 20),
                                120 + _rng.randint(-20, 30),
                                25 + _rng.randint(-5, 15), 255))

    # Sun
    sx, sy, sr = width - 100, 55, 35
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 230, 100, 220))

    # Trash
    trash_cols = [(200, 50, 50), (50, 70, 170), (185, 155, 110), (220, 220, 235)]
    for _ in range(12):
        tx = _rng.randint(30, width - 30)
        ty = _rng.randint(ground_y + 5, height - 10)
        s = _rng.randint(4, 8)
        c = _rng.choice(trash_cols)
        draw.rectangle([tx, ty, tx + s, ty + s], fill=(*c, 255))

    # Title
    try:
        font_big = ImageFont.truetype("arial.ttf", 52)
        font_sm = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_big = ImageFont.load_default()
        font_sm = font_big

    draw.text((width // 2 + 2, 22), "Forest Cleaner",
              fill=(0, 0, 0, 160), font=font_big, anchor="mt")
    draw.text((width // 2, 20), "Forest Cleaner",
              fill=(255, 255, 255, 240), font=font_big, anchor="mt")
    draw.text((width // 2, 80), "Clean the island.  Save nature.",
              fill=(220, 240, 220, 200), font=font_sm, anchor="mt")

    return img


# ═══════════════════════════════════════════════════════════════════════════
#  Launcher GUI
# ═══════════════════════════════════════════════════════════════════════════
def _run_launcher():
    import customtkinter as ctk

    languages = _get_languages()
    current_lang = [_get_saved_lang()]

    def T(key):
        return languages.get(current_lang[0], languages["en"]).get(key, key)

    # ── Window ──
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    root = ctk.CTk()
    root.title(T("launcher_title"))
    root.geometry("960x620")
    root.resizable(False, False)

    # ── Banner ──
    banner_img = _make_banner(920, 280)
    banner_label = ctk.CTkLabel(root, text="")
    banner_label.pack(pady=(12, 0))
    if banner_img is not None:
        try:
            ctk_img = ctk.CTkImage(light_image=banner_img, dark_image=banner_img,
                                   size=(920, 280))
            banner_label.configure(image=ctk_img, text="")
        except Exception:
            banner_label.configure(text="🌲  FOREST  CLEANER  🌲",
                                   font=("Arial", 42, "bold"),
                                   text_color="#8BC34A")
    else:
        banner_label.configure(text="🌲  FOREST  CLEANER  🌲",
                               font=("Arial", 42, "bold"),
                               text_color="#8BC34A")

    # ── Status bar ──
    status_var = ctk.StringVar(value="")
    status_label = ctk.CTkLabel(root, textvariable=status_var,
                                font=("Arial", 13), text_color="#aaa")
    status_label.pack(pady=(2, 4))

    def _refresh_status():
        if _all_game_packages_installed():
            status_var.set(f"✅  {T('status_ready')}")
            play_btn.configure(state="normal")
        else:
            status_var.set(f"⚠  {T('status_missing')}")

    # ── Button row ──
    btn_frame = ctk.CTkFrame(root, fg_color="transparent")
    btn_frame.pack(pady=8)

    # -- Download resources --
    def _on_download():
        if _all_game_packages_installed():
            status_var.set(f"✅  {T('all_installed')}")
            return
        dl_btn.configure(state="disabled", text=T("downloading"))
        status_var.set(T("downloading"))

        def _worker():
            failed = []
            for pip_name, mod_name in GAME_PACKAGES:
                if _is_installed(mod_name):
                    continue
                if not _install_package(pip_name):
                    failed.append(pip_name)
            root.after(0, lambda: _download_done(failed))

        def _download_done(failed):
            dl_btn.configure(state="normal", text=T("download_resources"))
            if failed:
                status_var.set(f"❌  {T('install_fail')}  {', '.join(failed)}")
            else:
                status_var.set(f"✅  {T('install_ok')}")
            _refresh_status()

        threading.Thread(target=_worker, daemon=True).start()

    dl_btn = ctk.CTkButton(
        btn_frame, text=T("download_resources"),
        width=220, height=44, font=("Arial", 15),
        fg_color="#37474F", hover_color="#546E7A",
        command=_on_download,
    )
    dl_btn.grid(row=0, column=0, padx=12)

    # -- Language selector --
    lang_codes = list(languages.keys())
    lang_names = [languages[c].get("language_name", c) for c in lang_codes]
    current_idx = lang_codes.index(current_lang[0]) if current_lang[0] in lang_codes else 0

    def _on_lang_change(choice):
        idx = lang_names.index(choice)
        code = lang_codes[idx]
        current_lang[0] = code
        _set_saved_lang(code)
        # Refresh all translatable widgets
        root.title(T("launcher_title"))
        dl_btn.configure(text=T("download_resources"))
        play_btn.configure(text=T("play"))
        lang_label.configure(text=T("language_label"))
        _refresh_status()

    lang_label = ctk.CTkLabel(btn_frame, text=T("language_label"),
                              font=("Arial", 13))
    lang_label.grid(row=0, column=1, padx=(24, 4))

    lang_menu = ctk.CTkOptionMenu(
        btn_frame, values=lang_names,
        command=_on_lang_change,
        width=140, height=36,
        fg_color="#455A64", button_color="#546E7A",
    )
    lang_menu.set(lang_names[current_idx])
    lang_menu.grid(row=0, column=2, padx=4)

    # ── PLAY button ──
    def _on_play():
        if not os.path.exists(GAME_SCRIPT):
            status_var.set(f"❌  Game not found: {GAME_SCRIPT}")
            return
        if not _all_game_packages_installed():
            status_var.set(f"⚠  {T('status_missing')}  —  {T('download_resources')}")
            return
        root.destroy()
        os.chdir(os.path.dirname(GAME_SCRIPT))
        subprocess.run([sys.executable, GAME_SCRIPT])

    play_btn = ctk.CTkButton(
        root, text=T("play"),
        width=320, height=64,
        font=("Arial", 28, "bold"),
        fg_color="#4CAF50", hover_color="#66BB6A",
        corner_radius=16,
        command=_on_play,
    )
    play_btn.pack(pady=(16, 8))

    # ── Footer ──
    ctk.CTkLabel(
        root, text="Forest Cleaner  •  2024-2026",
        font=("Arial", 11), text_color="#666",
    ).pack(side="bottom", pady=6)

    _refresh_status()
    root.mainloop()


# ═══════════════════════════════════════════════════════════════════════════
#  Entry-point
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print("--- Forest Cleaner Launcher ---")
    _bootstrap_launcher()
    _run_launcher()


if __name__ == "__main__":
    main()