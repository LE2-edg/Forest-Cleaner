import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import random
import pygame
import cv2
import os
import json
import subprocess
import sys
from PIL import Image, ImageTk
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RESSOURCE_DIR = os.path.dirname(CURRENT_DIR) 
DATA_DIR = os.path.join(RESSOURCE_DIR, 'data')

PARAMETERS_SCRIPT = os.path.join(CURRENT_DIR, 'parameters.py')
NEW_GAME_SCRIPT = os.path.join(CURRENT_DIR, 'new_game.py')
LANGUAGES_FILE = os.path.join(DATA_DIR, 'languages.json')
DATA_FILE = os.path.join(DATA_DIR, 'data.json')

VIDEO_FILES = [
    os.path.join(RESSOURCE_DIR, 'screenshot_1.mp4'),
    os.path.join(RESSOURCE_DIR, 'screenshot_2.mp4'),
    os.path.join(RESSOURCE_DIR, 'screenshot_3.mp4')
]
MUSIC_FILES = [
    os.path.join(RESSOURCE_DIR, 'music_1.mp3'),
    os.path.join(RESSOURCE_DIR, 'music_2.mp3')
]

def get_current_lang():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get("language_selected", "en")
    except: return "en"

def get_text(key):
    lang = get_current_lang()
    try:
        with open(LANGUAGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get(lang, {}).get(key, key)
    except: return key

pygame.mixer.init()
current_video_cap = None

def sound_manager():
    if not pygame.mixer.music.get_busy():
        if len(MUSIC_FILES) > 0 and os.path.exists(MUSIC_FILES[0]):
            track = random.choice(MUSIC_FILES)
            pygame.mixer.music.load(track)
            pygame.mixer.music.play()

def video_manager(label):
    global current_video_cap
    if current_video_cap is None or not current_video_cap.isOpened():
        if not VIDEO_FILES or not os.path.exists(VIDEO_FILES[0]):
            return
        current_video_cap = cv2.VideoCapture(random.choice(VIDEO_FILES))

    ret, frame = current_video_cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(1280, 720))
        label.configure(image=imgtk, text="")
    else:
        current_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    label.after(33, lambda: video_manager(label))

def open_parameters():
    subprocess.Popen([sys.executable, PARAMETERS_SCRIPT])

def launch_new_game_script(slot_id):
    subprocess.Popen([sys.executable, NEW_GAME_SCRIPT, str(slot_id)])

def confirm_action(slot_id, exists, root):
    title = get_text("new_game_title") if not exists else get_text("existing_game")
    msg = get_text("confirm_new_game").format(slot_id=slot_id) if not exists else get_text("confirm_load_or_overwrite").format(slot_id=slot_id)
    
    if exists:
        ans = messagebox.askyesnocancel(title, msg, parent=root)
        if ans is True:
            print(f"Chargement partie {slot_id}")
        elif ans is False:
            launch_new_game_script(slot_id)
    else:
        ans = messagebox.askyesno(title, msg, parent=root)
        if ans:
            launch_new_game_script(slot_id)

def show_save_selection(root):
    top = ctk.CTkToplevel(root)
    top.geometry("1000x400")
    top.title(get_text("select_game_title"))
    top.transient(root)
    
    ctk.CTkLabel(top, text=get_text("save_slots_header"), font=("Arial", 24)).pack(pady=10)
    
    grid_frame = ctk.CTkFrame(top)
    grid_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    for i in range(1, 5):
        save_path = os.path.join(DATA_DIR, f"save_{i}.json")
        exists = os.path.exists(save_path)
        
        col_frame = ctk.CTkFrame(grid_frame, border_width=2, border_color="green" if exists else "gray")
        col_frame.grid(row=0, column=i-1, padx=10, pady=10, sticky="nsew")
        grid_frame.grid_columnconfigure(i-1, weight=1)
        
        ctk.CTkLabel(col_frame, text="🌲", font=("Arial", 50)).pack(pady=20)
        
        txt = get_text("slot_label").format(slot_id=i)
        if exists:
            try:
                with open(save_path) as f: d = json.load(f)
                txt += f"\n{d.get('name', '???')}"
            except: txt += "\nErr"
        else:
            txt += f"\n{get_text('new')}"
            
        ctk.CTkButton(col_frame, text=txt, command=lambda x=i, y=exists: confirm_action(x, y, root)).pack(pady=10)

def main():
    root = ctk.CTk()
    root.geometry("1280x720")
    root.title("Forest Cleaner - Launcher")
    
    video_lbl = ctk.CTkLabel(root, text="Loading Video...")
    video_lbl.place(x=0, y=0, relwidth=1, relheight=1)
    
    sound_manager()
    root.after(100, lambda: video_manager(video_lbl))
    
    btn_param = ctk.CTkButton(root, text="≡", width=50, height=50, font=("Arial", 30), fg_color="gray", command=open_parameters)
    btn_param.place(relx=0.95, rely=0.05, anchor="ne")
    
    start_txt = get_text("start_button_text")
    btn_start = ctk.CTkButton(root, text=start_txt, width=200, height=60, font=("Arial", 24, "bold"), fg_color="#F1C40F", text_color="black", command=lambda: show_save_selection(root))
    btn_start.place(relx=0.95, rely=0.95, anchor="se")

    root.after(5000, lambda: [sound_manager(), root.after(5000, sound_manager)])
    
    root.mainloop()

if __name__ == "__main__":
    main()