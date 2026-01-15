# =========================
# Auto-installation de Pillow (PIL)
# =========================
import sys
import subprocess

def ensure_pillow():
    try:
        from PIL import Image, ImageTk
    except ImportError:
        print("Pillow non installé. Installation en cours...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image, ImageTk

ensure_pillow()

# =========================
# Imports
# =========================
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import random
import pygame
import cv2
import os
import json
from PIL import Image, ImageTk

# =========================
# Paths
# =========================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RESSOURCE_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(RESSOURCE_DIR, "data")

PARAMETERS_SCRIPT = os.path.join(CURRENT_DIR, "parameters.py")
NEW_GAME_SCRIPT = os.path.join(CURRENT_DIR, "new_game.py")
LANGUAGES_FILE = os.path.join(DATA_DIR, "languages.json")
DATA_FILE = os.path.join(DATA_DIR, "data.json")

VIDEO_FILES = [
    os.path.join(RESSOURCE_DIR, "screenshot_1.mp4"),
    os.path.join(RESSOURCE_DIR, "screenshot_2.mp4"),
    os.path.join(RESSOURCE_DIR, "screenshot_3.mp4"),
]

MUSIC_FILES = [
    os.path.join(RESSOURCE_DIR, "music_1.mp3"),
    os.path.join(RESSOURCE_DIR, "music_2.mp3"),
]

# =========================
# Language helpers
# =========================
def get_current_lang():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("language_selected", "en")
    except:
        return "en"

def get_text(key):
    try:
        with open(LANGUAGES_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get(get_current_lang(), {}).get(key, key)
    except:
        return key

# =========================
# Audio init (SAFE)
# =========================
audio_enabled = True
try:
    pygame.mixer.init()
except pygame.error as e:
    print("Audio désactivé :", e)
    audio_enabled = False

# =========================
# Audio & Video
# =========================
current_video_cap = None

def sound_manager():
    if not audio_enabled:
        return
    if not pygame.mixer.music.get_busy():
        tracks = [m for m in MUSIC_FILES if os.path.exists(m)]
        if tracks:
            pygame.mixer.music.load(random.choice(tracks))
            pygame.mixer.music.play()

def video_manager(label):
    global current_video_cap

    if current_video_cap is None or not current_video_cap.isOpened():
        videos = [v for v in VIDEO_FILES if os.path.exists(v)]
        if not videos:
            return
        current_video_cap = cv2.VideoCapture(random.choice(videos))

    ret, frame = current_video_cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ctk.CTkImage(img, size=(1280, 720))
        label.configure(image=imgtk, text="")
        label.image = imgtk
    else:
        current_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    label.after(33, lambda: video_manager(label))

# =========================
# Actions
# =========================
def open_parameters():
    subprocess.Popen([sys.executable, PARAMETERS_SCRIPT])

def launch_new_game_script(slot_id):
    subprocess.Popen([sys.executable, NEW_GAME_SCRIPT, str(slot_id)])

def confirm_action(slot_id, exists, root):
    title = get_text("new_game_title") if not exists else get_text("existing_game")
    msg = (
        get_text("confirm_new_game").format(slot_id=slot_id)
        if not exists
        else get_text("confirm_load_or_overwrite").format(slot_id=slot_id)
    )

    if exists:
        ans = messagebox.askyesnocancel(title, msg, parent=root)
        if ans is False:
            launch_new_game_script(slot_id)
    else:
        if messagebox.askyesno(title, msg, parent=root):
            launch_new_game_script(slot_id)

# =========================
# Save selection
# =========================
def show_save_selection(root):
    top = ctk.CTkToplevel(root)
    top.geometry("1000x400")
    top.title(get_text("select_game_title"))
    top.transient(root)

    ctk.CTkLabel(top, text=get_text("save_slots_header"), font=("Arial", 24)).pack(pady=10)

    grid = ctk.CTkFrame(top)
    grid.pack(fill="both", expand=True, padx=20, pady=20)

    for i in range(1, 5):
        save_path = os.path.join(DATA_DIR, f"save_{i}.json")
        exists = os.path.exists(save_path)

        frame = ctk.CTkFrame(grid, border_width=2, border_color="green" if exists else "gray")
        frame.grid(row=0, column=i - 1, padx=10, pady=10, sticky="nsew")
        grid.grid_columnconfigure(i - 1, weight=1)

        ctk.CTkLabel(frame, text="🌲", font=("Arial", 50)).pack(pady=20)

        text = get_text("slot_label").format(slot_id=i)
        if exists:
            try:
                with open(save_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                text += f"\n{data.get('name', '???')}"
            except:
                text += "\nErreur"
        else:
            text += f"\n{get_text('new')}"

        ctk.CTkButton(frame, text=text,
                      command=lambda x=i, y=exists: confirm_action(x, y, root)).pack(pady=10)

# =========================
# Main
# =========================
def main():
    root = ctk.CTk()
    root.geometry("1280x720")
    root.title("Forest Cleaner - Launcher")

    video_lbl = ctk.CTkLabel(root, text="Chargement...")
    video_lbl.place(relwidth=1, relheight=1)

    sound_manager()
    root.after(100, lambda: video_manager(video_lbl))

    ctk.CTkButton(root, text="≡", width=50, height=50,
                  font=("Arial", 30), fg_color="gray",
                  command=open_parameters).place(relx=0.95, rely=0.05, anchor="ne")

    ctk.CTkButton(
        root,
        text=get_text("start_button_text"),
        width=200,
        height=60,
        font=("Arial", 24, "bold"),
        fg_color="#F1C40F",
        text_color="black",
        command=lambda: show_save_selection(root)
    ).place(relx=0.95, rely=0.95, anchor="se")

    root.mainloop()

# =========================
if __name__ == "__main__":
    main()
