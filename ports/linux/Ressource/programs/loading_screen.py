# programs/loading_screen.py - NOUVEAU FICHIER

import customtkinter as ctk
import sys
import os
import subprocess
from threading import Thread
import time
import random
import json

# =========================
# Paths
# =========================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Assumer que les fichiers data/languages.json sont 2 niveaux au-dessus
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), 'data')
LANGUAGES_FILE = os.path.join(DATA_DIR, "languages.json")
# Chemin vers le script de génération
PROCESS_SCRIPT_PATH = os.path.join(CURRENT_DIR, 'procedurals_system', 'process.py')

# =========================
# Classe Écran de Chargement
# =========================
class LoadingScreen(ctk.CTk):
    def __init__(self, slot_id):
        super().__init__()
        self.slot_id = slot_id
        self.title("Forest Cleaner - Chargement Procédural")
        self.geometry("800x600")
        self.resizable(False, False)
        
        # Élément de l'interface
        ctk.CTkLabel(self, text="Génération du Monde Forest Cleaner...", font=("Arial", 24)).pack(pady=30)
        
        # Barre de progression
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", width=700)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=20)
        
        # Texte de progression
        self.progress_label = ctk.CTkLabel(self, text="Initialisation...", font=("Arial", 16))
        self.progress_label.pack(pady=10)

        # Frame pour l'animation des logos
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent", width=700, height=350)
        self.logo_frame.pack(pady=20, fill="x", padx=50, expand=True)
        self.logo_frame.pack_propagate(False)
        
        # Simuler des "logos de nature"
        # Vous devrez remplacer ces emojis (🌳, ⛰️, 💧, 🏭) par des images réelles si besoin
        self.logos = []
        for text in ["🌳", "⛰️", "💧", "🏭"]:
            lbl = ctk.CTkLabel(self.logo_frame, text=text, font=("Arial", 40))
            lbl.place(x=random.randint(50, 650), y=random.randint(50, 300))
            self.logos.append(lbl)
            
        self.process = None # Le sous-processus de process.py
        
        # Démarrer les actions
        self.after(50, self.animate_logos)
        self.after(100, self.start_procedural_process)

    def animate_logos(self):
        """Anime les logos (mouvement aléatoire)."""
        frame_width = self.logo_frame.winfo_width()
        frame_height = self.logo_frame.winfo_height()
        
        for lbl in self.logos:
            current_x = lbl.winfo_x()
            current_y = lbl.winfo_y()
            
            # Petit mouvement aléatoire entre -5 et 5 pixels
            new_x = max(0, min(frame_width - 50, current_x + random.randint(-5, 5)))
            new_y = max(0, min(frame_height - 50, current_y + random.randint(-5, 5)))
            
            lbl.place(x=new_x, y=new_y)
            
        self.after(50, self.animate_logos)

    def start_procedural_process(self):
        """Lance process.py et démarre le monitoring."""
        if not os.path.exists(PROCESS_SCRIPT_PATH):
            self.progress_label.configure(text=f"ERREUR: Script {PROCESS_SCRIPT_PATH} introuvable.")
            self.progress_bar.configure(fg_color="red")
            return

        try:
            # Lancer process.py avec capture de la sortie
            self.process = subprocess.Popen(
                [sys.executable, PROCESS_SCRIPT_PATH, str(self.slot_id)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            # Lire la sortie dans un thread séparé pour ne pas bloquer l'UI
            self.check_thread = Thread(target=self.read_process_output, daemon=True)
            self.check_thread.start()

        except Exception as e:
            self.progress_label.configure(text=f"Erreur de lancement: {e}")
            self.progress_bar.configure(fg_color="red")
    
    def read_process_output(self):
        """Lit la sortie du processus process.py et met à jour l'UI."""
        while True:
            # Lire une ligne de la sortie
            output = self.process.stdout.readline()
            
            # Si la sortie est vide et le processus est terminé, sortir de la boucle
            if output == '' and self.process.poll() is not None:
                break
            
            if output:
                # Le générateur de process.py envoie la progression au format: PROGRESS:<percent>:<message>
                if output.startswith("PROGRESS:"):
                    try:
                        _, percent_str, message = output.strip().split(':', 2)
                        percent = int(percent_str) / 100.0
                        
                        # Mettre à jour l'UI (doit être fait dans le thread principal de Tkinter)
                        self.after(0, self.update_progress_ui, percent, message)
                        
                    except ValueError:
                        print(f"Format de progression invalide: {output.strip()}")

        # Une fois le processus de génération terminé
        self.after(0, self.on_process_finished)

    def update_progress_ui(self, percent, message):
        """Fonction appelée dans le thread principal pour mettre à jour les widgets."""
        self.progress_bar.set(percent)
        self.progress_label.configure(text=message)
        
    def on_process_finished(self):
        """Ferme l'écran de chargement."""
        self.update_progress_ui(1.0, "Génération terminée. Lancement du jeu...")
        time.sleep(1) # Laisser le temps à l'utilisateur de voir le message final
        self.destroy()

def main():
    if len(sys.argv) < 2:
        print("Erreur: ID de slot manquant.")
        sys.exit(1)
        
    try:
        slot_id = int(sys.argv[1])
        app = LoadingScreen(slot_id)
        app.mainloop()
    except ValueError:
        print("Erreur: L'ID de slot doit être un entier.")
        sys.exit(1)

if __name__ == "__main__":
    main()