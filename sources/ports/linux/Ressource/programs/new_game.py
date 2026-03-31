# programs/new_game.py - MODIFIÉ

import customtkinter as ctk
import sys
import os
import json
import subprocess
import random # AJOUTÉ

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), 'data')
# NOUVEAU CHEMIN: On lance l'écran de chargement
LOADING_SCREEN_SCRIPT = os.path.join(CURRENT_DIR, 'loading_screen.py') 

def create_save_and_launch(slot_id, name, root):
    """Crée le fichier JSON puis lance l'écran de chargement."""
    
    # 1. Création de la sauvegarde
    file_path = os.path.join(DATA_DIR, f"save_{slot_id}.json")
    
    # Structure de données par défaut pour une nouvelle partie
    data = {
        "id": slot_id,
        "name": name if name else f"Joueur {slot_id}",
        "progress": 0,
        "location": "forest_start",
        "time": "00:00",
        "seed": random.randint(100000, 999999) # AJOUT IMPORTANT pour le procédural
    }
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Sauvegarde créée : {file_path}")

        # NOUVEAU: Lancement de l'écran de chargement
        if os.path.exists(LOADING_SCREEN_SCRIPT):
            print(f"Lancement de l'écran de chargement : {LOADING_SCREEN_SCRIPT}...")
            # Lance loading_screen.py avec l'ID en argument
            subprocess.Popen([sys.executable, LOADING_SCREEN_SCRIPT, str(slot_id)])
            root.destroy()
        else:
            print(f"ERREUR CRITIQUE : Le fichier {LOADING_SCREEN_SCRIPT} est introuvable.")
            tk_msg_error(root, "Erreur", f"Script introuvable :\n{LOADING_SCREEN_SCRIPT}")

    except Exception as e:
        print(f"Erreur lors de la création : {e}")

def tk_msg_error(root, title, message):
    # ... (fonction inchangée)
    try:
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=root)
    except:
        pass

def main():
    slot_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    
    app = ctk.CTk()
    app.geometry("400x250")
    app.title(f"Nouvelle Partie - Slot {slot_id}")
    app.resizable(False, False)
    
    frame = ctk.CTkFrame(app)
    frame.pack(expand=True, fill="both", padx=20, pady=20)
    
    ctk.CTkLabel(frame, text="Nom du personnage :", font=("Arial", 16)).pack(pady=(20, 10))
    
    entry = ctk.CTkEntry(frame, width=200)
    entry.pack(pady=10)
    
    ctk.CTkButton(
        frame, 
        text="Commencer l'Aventure", 
        fg_color="green", 
        hover_color="darkgreen",
        command=lambda: create_save_and_launch(slot_id, entry.get(), app)
    ).pack(pady=20)
    
    app.mainloop()

if __name__ == "__main__":
    main()