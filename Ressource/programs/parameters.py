import customtkinter as ctk
import pygame
import json
import os
import time

# =========================
# Paths
# =========================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "data")
DATA_FILE = os.path.join(DATA_DIR, "data.json")
LANGUAGES_FILE = os.path.join(DATA_DIR, "languages.json")

# =========================
# Load data ONCE (OPTIMISÉ)
# =========================
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

DATA = load_json(DATA_FILE, {})
LANGUAGES = load_json(LANGUAGES_FILE, {})

# =========================
# Safe audio init
# =========================
audio_enabled = True
try:
    pygame.mixer.init()
except pygame.error as e:
    print("Audio désactivé :", e)
    audio_enabled = False

# =========================
# Helpers (FAST)
# =========================
CURRENT_LANG = DATA.get("language_selected", "en")

def get_text(key):
    return LANGUAGES.get(CURRENT_LANG, {}).get(key, key)

# =========================
# Language
# =========================
def change_lang(new_lang, app):
    DATA["language_selected"] = new_lang
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DATA, f, indent=4)
    except:
        pass
    app.destroy()

# =========================
# Volume handlers (THROTTLED)
# =========================
_last_music_update = 0
_last_sfx_update = 0

def set_volume_music(val):
    global _last_music_update
    if not audio_enabled:
        return

    now = time.time()
    if now - _last_music_update > 0.05:  # 50 ms
        pygame.mixer.music.set_volume(float(val) / 100)
        _last_music_update = now

def set_volume_sfx(val):
    global _last_sfx_update
    if not audio_enabled:
        return

    now = time.time()
    if now - _last_sfx_update > 0.05:
        try:
            pygame.mixer.Channel(0).set_volume(float(val) / 100)
        except:
            pass
        _last_sfx_update = now

# =========================
# Main
# =========================
def main():
    app = ctk.CTk()
    app.geometry("600x600")
    app.title("Settings")

    # Title
    ctk.CTkLabel(
        app,
        text=get_text("settings").upper(),
        font=("Arial", 30)
    ).pack(pady=20)

    # =========================
    # Language Frame
    # =========================
    l_frame = ctk.CTkFrame(app, fg_color="#2980B9")
    l_frame.pack(fill="x", padx=20, pady=10)

    ctk.CTkLabel(
        l_frame,
        text=get_text("language_selection"),
        text_color="white"
    ).pack(pady=5)

    btn_frame = ctk.CTkFrame(l_frame, fg_color="transparent")
    btn_frame.pack(pady=10)

    for l in ("fr", "en", "es"):
        ctk.CTkButton(
            btn_frame,
            text=l.upper(),
            width=60,
            fg_color="cyan" if l == CURRENT_LANG else "blue",
            command=lambda x=l: change_lang(x, app)
        ).pack(side="left", padx=5)

    # =========================
    # Audio Settings
    # =========================
    ctk.CTkLabel(app, text=get_text("music_volume")).pack(pady=(20, 0))

    slider_m = ctk.CTkSlider(
        app,
        from_=0,
        to=100,
        command=set_volume_music,
        state="normal" if audio_enabled else "disabled"
    )
    slider_m.set(50)
    slider_m.pack()

    ctk.CTkLabel(app, text=get_text("sfx_volume")).pack(pady=(20, 0))

    slider_s = ctk.CTkSlider(
        app,
        from_=0,
        to=100,
        command=set_volume_sfx,
        button_color="red",
        state="normal" if audio_enabled else "disabled"
    )
    slider_s.set(70)
    slider_s.pack()

    if not audio_enabled:
        ctk.CTkLabel(
            app,
            text="⚠ Audio indisponible sur ce système",
            text_color="orange"
        ).pack(pady=20)

    app.mainloop()

# =========================
if __name__ == "__main__":
    main()
