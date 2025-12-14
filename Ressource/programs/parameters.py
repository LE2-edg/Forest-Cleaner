import customtkinter as ctk
import tkinter as tk
import json
import os
import pygame # Toujours nécessaire pour interagir avec le mixer

# --- Configuration des Chemins et Constantes ---
LANGUAGE_KEY = "language_selected"
DATA_FOLDER = 'Ressource/data'
DATA_FILENAME = 'data.json'
DATA_FILEPATH = os.path.join(DATA_FOLDER, DATA_FILENAME)

# --- Simulation des Langues ---
# Normalement, vous liriez ceci depuis languages.py/json, mais nous utilisons une liste pour la simplicité.
LANGUAGES = [
    {"code": "fr", "name": "Français", "label": "Langue"},
    {"code": "en", "name": "English", "label": "Language"},
    {"code": "es", "name": "Español", "label": "Idioma"}
]

# --- Fonctions de Gestion ---

def get_current_language():
    """Tente de lire le code de langue actuel dans data.json."""
    try:
        with open(DATA_FILEPATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(LANGUAGE_KEY, "en") # Retourne "en" par défaut
    except:
        return "en"

def set_language_preference(lang_code):
    """Enregistre la langue sélectionnée dans data.json."""
    
    # 1. Lire les données existantes ou initialiser
    try:
        if os.path.exists(DATA_FILEPATH):
            with open(DATA_FILEPATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
    except:
        data = {}
    
    # 2. Mettre à jour la clé de langue
    data[LANGUAGE_KEY] = lang_code
    
    # 3. Écrire le fichier (pas de try...except pour respecter la consigne)
    os.makedirs(os.path.dirname(DATA_FILEPATH), exist_ok=True)
    with open(DATA_FILEPATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    print(f"Langue changée et enregistrée: {lang_code}")


def update_music_volume(volume):
    """Met à jour le volume de la musique (canal par défaut de Pygame)."""
    # Pygame utilise une échelle de 0.0 à 1.0
    volume_level = volume / 100.0
    pygame.mixer.music.set_volume(volume_level)
    print(f"Volume Musique mis à jour: {volume}%")

def update_sfx_volume(volume):
    """Met à jour le volume des effets sonores (utilisé pour les sons généraux)."""
    # Pygame n'a pas de canal SFX séparé par défaut, on utilise un 'Channel' ou un volume général.
    # Ici, nous allons simuler un contrôle SFX en utilisant la fonction set_volume() du mixer
    # (cela affecterait tous les sons, mais simule la fonctionnalité).
    volume_level = volume / 100.0
    pygame.mixer.set_reserved(1) # Réserver un canal pour les SFX
    pygame.mixer.Channel(0).set_volume(volume_level)
    print(f"Volume Bruits mis à jour: {volume}%")

# --- Interface Utilisateur ---

def main():
    # Initialisation Pygame pour garantir que le mixer est prêt
    if not pygame.mixer.get_init():
        pygame.mixer.init()
        
    app = ctk.CTk()
    app.title("Paramètres du Jeu")
    app.geometry("800x600")
    app.resizable(False, False)
    
    current_lang = get_current_language()

    # --- Titre ---
    ctk.CTkLabel(
        app, 
        text="PARAMÈTRES", 
        font=ctk.CTkFont(size=30, weight="bold")
    ).pack(pady=(20, 10))

    # --- 1. Contrôle de la Langue ---
    
    lang_frame = ctk.CTkFrame(app, fg_color="blue", width=700, height=150)
    lang_frame.pack(pady=20, padx=20)
    lang_frame.pack_propagate(False) # Empêche la frame de se redimensionner
    
    ctk.CTkLabel(
        lang_frame, 
        text="SÉLECTION DE LA LANGUE", 
        fg_color="transparent",
        font=ctk.CTkFont(size=18, weight="bold")
    ).pack(pady=(10, 5))

    button_container = ctk.CTkFrame(lang_frame, fg_color="blue")
    button_container.pack(pady=10)
    
    # Disposition des boutons de langue dans des petits rectangles
    for lang in LANGUAGES:
        is_selected = (lang['code'] == current_lang)
        
        btn = ctk.CTkButton(
            button_container,
            text=lang["name"],
            command=lambda code=lang["code"]: set_language_preference(code),
            width=100,
            fg_color=("cyan" if is_selected else "darkblue"),
            hover_color=("teal" if not is_selected else "cyan")
        )
        btn.pack(side="left", padx=10, pady=5)
    
    # --- 2. Contrôle du Volume (Musique) ---
    
    volume_frame = ctk.CTkFrame(app)
    volume_frame.pack(pady=20, padx=20, fill="x")

    ctk.CTkLabel(
        volume_frame, 
        text="Musique :", 
        font=ctk.CTkFont(size=16)
    ).pack(pady=(10, 5))
    
    # Curseur pour la Musique (initialisé à 50%)
    music_slider = ctk.CTkSlider(
        volume_frame, 
        from_=0, 
        to=100, 
        command=update_music_volume, 
        width=500,
        button_color="darkgreen"
    )
    music_slider.set(50) 
    music_slider.pack(pady=10)
    
    # --- 3. Contrôle du Volume (Bruits/SFX) ---
    
    ctk.CTkLabel(
        volume_frame, 
        text="Bruits :", 
        font=ctk.CTkFont(size=16)
    ).pack(pady=(10, 5))
    
    # Curseur pour les Bruits (initialisé à 70%)
    sfx_slider = ctk.CTkSlider(
        volume_frame, 
        from_=0, 
        to=100, 
        command=update_sfx_volume, 
        width=500,
        button_color="darkred"
    )
    sfx_slider.set(70) 
    sfx_slider.pack(pady=10)
    
    # --- Bouton Fermer ---
    ctk.CTkButton(
        app, 
        text="Fermer et Appliquer", 
        command=app.destroy,
        fg_color="green",
        hover_color="darkgreen"
    ).pack(pady=30)
    
    app.mainloop()

if __name__ == "__main__":
    main()