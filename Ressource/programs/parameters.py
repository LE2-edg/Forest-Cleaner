import customtkinter as ctk
import pygame
import json
import os
import sys

# Chemins
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), 'data')
DATA_FILE = os.path.join(DATA_DIR, 'data.json')
LANGUAGES_FILE = os.path.join(DATA_DIR, 'languages.json')

pygame.mixer.init()

def get_text(key, lang):
    try:
        with open(LANGUAGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get(lang, {}).get(key, key)
    except: return key

def change_lang(new_lang, app):
    # Sauvegarde
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: d = json.load(f)
    except: d = {}
    d["language_selected"] = new_lang
    with open(DATA_FILE, 'w', encoding='utf-8') as f: json.dump(d, f, indent=4)
    
    # Redémarrage simple : on ferme, l'utilisateur devra rouvrir (plus simple que de tout redessiner)
    app.destroy()
    # Optionnel : relancer le script
    # os.execl(sys.executable, sys.executable, *sys.argv)

def set_volume_music(val):
    pygame.mixer.music.set_volume(float(val)/100)

def set_volume_sfx(val):
    # Simulé sur le canal 0
    pygame.mixer.Channel(0).set_volume(float(val)/100)

def main():
    app = ctk.CTk()
    app.geometry("600x600")
    app.title("Settings")
    
    # Langue actuelle
    try:
        with open(DATA_FILE) as f: lang = json.load(f).get("language_selected", "en")
    except: lang = "en"
    
    # Titre
    ctk.CTkLabel(app, text=get_text("settings", lang).upper(), font=("Arial", 30)).pack(pady=20)
    
    # Cadre Langue (Bleu)
    l_frame = ctk.CTkFrame(app, fg_color="#2980B9")
    l_frame.pack(fill="x", padx=20, pady=10)
    ctk.CTkLabel(l_frame, text=get_text("language_selection", lang), text_color="white").pack()
    
    btn_frame = ctk.CTkFrame(l_frame, fg_color="transparent")
    btn_frame.pack(pady=10)
    
    langs = ["fr", "en", "es"]
    for l in langs:
        color = "cyan" if l == lang else "blue"
        ctk.CTkButton(btn_frame, text=l.upper(), width=60, fg_color=color, 
                      command=lambda x=l: change_lang(x, app)).pack(side="left", padx=5)

    # Volume
    ctk.CTkLabel(app, text=get_text("music_volume", lang)).pack(pady=(20,0))
    slider_m = ctk.CTkSlider(app, from_=0, to=100, command=set_volume_music)
    slider_m.set(50)
    slider_m.pack()
    
    ctk.CTkLabel(app, text=get_text("sfx_volume", lang)).pack(pady=(20,0))
    slider_s = ctk.CTkSlider(app, from_=0, to=100, command=set_volume_sfx, button_color="red")
    slider_s.set(70)
    slider_s.pack()

    app.mainloop()

if __name__ == "__main__":
    main()