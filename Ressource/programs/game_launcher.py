from initiale_main import lang_code
import tkinter as tk
import customtkinter as ctk
import random
import pygame 
import cv2 
import os
import json

# --- Configuration et Chemins ---
RESOURCE_FOLDER = 'Ressource'
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
    
# --- Fonctions de Logique (Docstrings Retrouvés) ---

def language_selection():
    """Cette fonction sert à sélectionner la langue du jeu."""
    pass

def launch_parameters():
    """Cette fonction sert à lancer les paramètres du jeu."""
    pass

def selection_parameters():
    """Cette fonction sert à afficher les paramètres du jeu."""
    pass

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
    global current_start_text
    
    # 🛠️ Correction de la lecture de la langue
    with open(LANGUAGE_FILEPATH, "r", encoding="utf-8") as f:
        # NOTE: Le fichier JSON doit contenir une clé pour le texte "Start"
        language_data = json.load(f)
        # Supposons que la clé est 'start_button_text'
        current_start_text = language_data.get("start_button_text", "START")
    
    # --- Configuration de la Fenêtre CTk ---
    
    root = ctk.CTk()
    root.title("Lanceur de Jeu")
    root.configure(bg=BACKGROUND_COLOR)
    
    # Configuration des dimensions
    root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
    root.minsize(DEFAULT_WIDTH, DEFAULT_HEIGHT) 
    root.maxsize(MAX_WIDTH, MAX_HEIGHT)
    
    # Configuration de la grille pour l'étirement
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    # --- Frame Principale ---
    main_frame = ctk.CTkFrame(root, fg_color=BACKGROUND_COLOR)
    main_frame.grid(row=0, column=0, sticky="nsew")
    
    # Configuration des lignes et colonnes pour aligner les boutons dans les coins
    main_frame.grid_columnconfigure(0, weight=1) 
    main_frame.grid_columnconfigure(1, weight=0) 
    main_frame.grid_rowconfigure(0, weight=0) 
    main_frame.grid_rowconfigure(1, weight=1) # Espace central
    main_frame.grid_rowconfigure(2, weight=0) 
    
    # --- Composants Média ---
    
    # Placeholder Vidéo 
    video_placeholder = ctk.CTkLabel(main_frame, text="", bg_color="transparent")
    video_placeholder.grid(row=0, column=0, rowspan=3, columnspan=2, sticky="nsew")
    
    # Lancement des gestionnaires de média
    sound_manager() 
    video_manager(video_placeholder) 

    # Lancement de l'interface
    body_game(main_frame)
    
    # Appel périodique pour gérer le son (re-boucle de la musique)
    root.after(10000, lambda: sound_manager()) 
    root.mainloop()

if __name__ == "__main__":
    main()