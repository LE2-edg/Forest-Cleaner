import customtkinter as ctk
import sys
import os
import json
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), 'data')
PROCESS_SCRIPT_PATH = os.path.join(CURRENT_DIR, 'procedurals_system', 'process.py')

def create_save_and_launch(slot_id, name, root):
    """Crée le fichier JSON puis lance process.py"""
    
    # 1. Création de la sauvegarde
    file_path = os.path.join(DATA_DIR, f"save_{slot_id}.json")
    
    # Structure de données par défaut pour une nouvelle partie
    data = {
        "id": slot_id,
        "name": name if name else f"Joueur {slot_id}",
        "progress": 0,
        "location": "forest_start",
        "time": "00:00"
    }
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Sauvegarde créée : {file_path}")

        if os.path.exists(PROCESS_SCRIPT_PATH):
            print(f"Lancement de {PROCESS_SCRIPT_PATH}...")
            subprocess.Popen([sys.executable, PROCESS_SCRIPT_PATH, str(slot_id)])
            root.destroy()
        else:
            print(f"ERREUR CRITIQUE : Le fichier {PROCESS_SCRIPT_PATH} est introuvable.")
            tk_msg_error(root, "Erreur", f"Script introuvable :\n{PROCESS_SCRIPT_PATH}")

    except Exception as e:
        print(f"Erreur lors de la création : {e}")

def tk_msg_error(root, title, message):
    """Affiche une petite popup d'erreur si besoin (sans bloquer tout le script)"""
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