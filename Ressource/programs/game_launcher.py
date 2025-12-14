# L'importation doit être corrigée pour éviter les erreurs de module, car ce script est
# probablement lancé par subprocess et n'a pas accès à la variable lang_code facilement.
# from initiale_main import lang_code 
import tkinter as tk
import customtkinter as ctk
import random
import pygame 
import cv2 
import os
import json
import subprocess
import sys

# --- Configuration et Chemins ---
RESOURCE_FOLDER = 'Ressource'
PROGRAMS_FOLDER = 'programs'
PARAMETERS_SCRIPT = os.path.join(PROGRAMS_FOLDER, 'parameters.py') 
NEW_GAME_SCRIPT = os.path.join(PROGRAMS_FOLDER, 'new_game.py')

VIDEO_FILES = [
    os.path.join(RESOURCE_FOLDER, 'screenshot_1.mp4'),
    os.path.join(RESOURCE_FOLDER, 'screenshot_2.mp4'),
    os.path.join(RESOURCE_FOLDER, 'screenshot_3.mp4')
]
MUSIC_FILES = [
    os.path.join(RESOURCE_FOLDER, 'music_1.mp3'),
    os.path.join(RESOURCE_FOLDER, 'music_2.mp3')
]
LANGUAGE_FILEPATH = os.path.join(RESOURCE_FOLDER, 'data', 'languages.json') 
SAVE_FILES_PATH = os.path.join(RESOURCE_FOLDER, 'data') 
MAX_SAVES = 4 

# Configurations d'affichage
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
MAX_WIDTH = 7680
MAX_HEIGHT = 4320
BACKGROUND_COLOR = "gray20"

# Initialisation de Pygame pour le son
pygame.mixer.init()
global current_video_cap
current_language_code = "EN"
current_start_text = "START" 
current_root_window = None 

# --- Fonctions Audio et Vidéo Minimales ---

def sound_manager():
    """Cette fonction sert à gérer les sons du jeu."""
    if not pygame.mixer.music.get_busy():
        next_music = random.choice(MUSIC_FILES)
        pygame.mixer.music.load(next_music)
        pygame.mixer.music.play()

def video_manager(video_label):
    """Cette fonction sert à gérer la lecture et la boucle des vidéos."""
    global current_video_cap

    if 'current_video_cap' not in globals() or not current_video_cap.isOpened():
        next_video_file = random.choice(VIDEO_FILES)
        current_video_cap = cv2.VideoCapture(next_video_file)

    ret, frame = current_video_cap.read()
    
    if not ret:
        current_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
    video_label.after(33, lambda: video_manager(video_label))
    
# --- Fonctions de Logique ---

def language_selection():
    """Cette fonction sert à sélectionner la langue du jeu."""
    pass

def launch_parameters():
    """Cette fonction sert à lancer les paramètres du jeu."""
    # Lance le script parameters.py
    print(f"Lancement du script de paramètres: {PARAMETERS_SCRIPT}")
    subprocess.Popen([sys.executable, PARAMETERS_SCRIPT])


def selection_parameters():
    """Cette fonction sert à afficher les paramètres du jeu."""
    pass

def launch_game(save_file):
    """Cette fonction sert à lancer la partie sélectionnée."""
    print(f"Lancement de la partie avec le fichier de sauvegarde: {save_file}")
    if current_root_window:
        current_root_window.destroy()

def launch_new_game(slot_id):
    """Lance le script de création d'une nouvelle partie."""
    print(f"Lancement de la création de nouvelle partie pour l'emplacement {slot_id}: {NEW_GAME_SCRIPT}")
    if current_root_window:
        current_root_window.destroy() 
    
    # Lance le script new_game.py
    subprocess.Popen([sys.executable, NEW_GAME_SCRIPT, str(slot_id)])

def confirm_action(slot_id, is_existing):
    """Gère le pop-up de confirmation pour lancer ou écraser."""
    
    if is_existing:
        action = tk.messagebox.askyesnocancel(
            "Partie Existante",
            f"Voulez-vous lancer la partie sauvegardée n°{slot_id} ou créer une nouvelle partie (écraser) ?",
            icon='question',
            type='yesnocancel',
            default='yes',
            master=current_root_window
        )
        
        if action is True:
            launch_game(os.path.join(SAVE_FILES_PATH, f'save_{slot_id}.json'))
        elif action is False:
            launch_new_game(slot_id)
        
    else:
        # Nouvelle partie : Confirmer la création
        action = tk.messagebox.askyesno(
            "Nouvelle Partie",
            f"Voulez-vous créer une nouvelle partie sur l'emplacement n°{slot_id} ?",
            master=current_root_window
        )
        if action is True:
            launch_new_game(slot_id)


def selection_game():
    """Cette fonction sert à afficher la sélection des parties."""
    global current_root_window
    
    if current_root_window:
        current_root_window.withdraw() 

    # --- Nouvelle Fenêtre pour la Sélection ---
    select_window = ctk.CTkToplevel(current_root_window)
    select_window.title("Sélection de Partie")
    select_window.geometry("1100x400")
    select_window.configure(bg=BACKGROUND_COLOR)
    select_window.transient(current_root_window)

    select_window.grid_rowconfigure(0, weight=0) 
    select_window.grid_rowconfigure(1, weight=1) # Ligne principale des slots
    select_window.grid_rowconfigure(2, weight=0)
    
    # S'assurer que les colonnes des slots sont égales
    for i in range(1, MAX_SAVES + 1):
        select_window.grid_columnconfigure(i, weight=1)

    header = ctk.CTkLabel(select_window, text="Emplacements de Sauvegarde", font=ctk.CTkFont(size=24, weight="bold"))
    header.grid(row=0, column=0, columnspan=MAX_SAVES + 1, pady=(20, 10))

    # Boucle pour créer les 4 slots horizontalement
    for i in range(1, MAX_SAVES + 1):
        slot_id = i
        save_file = os.path.join(SAVE_FILES_PATH, f'save_{slot_id}.json')
        
        is_existing = os.path.exists(save_file)
        slot_text = f"Emplacement {slot_id}\n(Nouveau)"
        image_color = "gray" 
        
        if is_existing:
            try:
                with open(save_file, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)
                    slot_name = save_data.get('name', f"Partie {slot_id}")
                    slot_text = f"{slot_name}\nTemps: {save_data.get('time', 'N/A')}"
                image_color = "green" 
            except:
                slot_text = f"Emplacement {slot_id}\n(Fichier corrompu)"
                image_color = "red"
        
        # --- Création du Slot ---
        
        frame_slot = ctk.CTkFrame(select_window, fg_color=BACKGROUND_COLOR, border_width=2, border_color=image_color)
        # Disposition en ligne : row=1, column=i
        frame_slot.grid(row=1, column=i, padx=10, pady=20, sticky="nsew") 

        # Placeholder Dessin de Nature (Rectangle Vertical)
        nature_placeholder = ctk.CTkLabel(
            frame_slot, 
            text="[Nature]",
            fg_color=image_color,
            text_color="white",
            height=150, 
            width=200 
        )
        nature_placeholder.pack(padx=10, pady=10)
        
        # Bouton d'action
        action_button = ctk.CTkButton(
            frame_slot, 
            text=f"Slot {slot_id}",
            command=lambda id=slot_id, existing=is_existing: confirm_action(id, existing), 
            width=200
        )
        action_button.pack(padx=10, pady=(0, 10))

    # Fonction pour revenir à la fenêtre principale
    def close_select_window():
        select_window.destroy()
        if current_root_window:
            current_root_window.deiconify() 

    # Bouton de retour
    ctk.CTkButton(select_window, text="Retour", command=close_select_window).grid(row=2, column=0, columnspan=MAX_SAVES + 1, pady=30)
    

def launch_game():
    """Cette fonction sert à lancer la partie sélectionnée."""
    pass

def selection_game():
    """Cette fonction sert à afficher la sélection des parties."""
    pass

def body_game(root_frame):
    """Cette fonction sert à afficher le bouton qui mène à la sélection des parties ou des paramètres"""
    global current_start_text 
    
    # Bouton Paramètres (Haut Droit)
    settings_button = ctk.CTkButton(
        root_frame,
        text="≡", 
        command=launch_parameters, 
        width=50,
        height=50,
        fg_color="gray", 
        text_color="white",
        font=ctk.CTkFont(size=24)
    )
    settings_button.grid(row=0, column=1, padx=20, pady=20, sticky="ne")

    # Bouton Lancement de Partie (Bas Droit)
    game_launch_button = ctk.CTkButton(
        root_frame,
        text=current_start_text,
        command=selection_game, 
        width=200,
        height=60,
        fg_color="yellow", 
        text_color="black",
        font=ctk.CTkFont(size=28, weight="bold")
    )
    game_launch_button.grid(row=2, column=1, padx=20, pady=20, sticky="se")

def main():
    global current_start_text, current_root_window
    
    # Chargement de la Langue
    try:
        with open(LANGUAGE_FILEPATH, "r", encoding="utf-8") as f:
            language_data = json.load(f)
            current_start_text = language_data.get("start_button_text", "START")
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Configuration de la Fenêtre CTk
    root = ctk.CTk()
    current_root_window = root 
    root.title("Lanceur de Jeu")
    root.configure(bg=BACKGROUND_COLOR)
    
    # Configuration des dimensions
    root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
    root.minsize(DEFAULT_WIDTH, DEFAULT_HEIGHT) 
    root.maxsize(MAX_WIDTH, MAX_HEIGHT)
    
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    # Frame Principale
    main_frame = ctk.CTkFrame(root, fg_color=BACKGROUND_COLOR)
    main_frame.grid(row=0, column=0, sticky="nsew")
    
    main_frame.grid_columnconfigure(0, weight=1) 
    main_frame.grid_columnconfigure(1, weight=0) 
    main_frame.grid_rowconfigure(0, weight=0) 
    main_frame.grid_rowconfigure(1, weight=1) 
    main_frame.grid_rowconfigure(2, weight=0) 
    
    # Composants Média
    video_placeholder = ctk.CTkLabel(main_frame, text="", bg_color="transparent")
    video_placeholder.grid(row=0, column=0, rowspan=3, columnspan=2, sticky="nsew")
    
    sound_manager() 
    if 'current_video_cap' not in globals():
        global current_video_cap
        # Initialisation de la capture vidéo
        current_video_cap = cv2.VideoCapture(random.choice(VIDEO_FILES))
    
    video_manager(video_placeholder) 

    # Lancement de l'interface
    body_game(main_frame)
    
    # Boucle de son et Mainloop
    root.after(10000, lambda: sound_manager()) 
    root.mainloop()

if __name__ == "__main__":
    main()