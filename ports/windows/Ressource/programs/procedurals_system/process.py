# programs/procedurals_system/process.py - MIS À JOUR

import sys
import json
import os
import time 
import subprocess 

# =========================
# Paths
# =========================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Remonter de 'procedurals_system' -> 'programs'
PROGRAMS_DIR = os.path.dirname(CURRENT_DIR)
RESOURCE_DIR = os.path.dirname(PROGRAMS_DIR)
DATA_DIR = os.path.join(RESOURCE_DIR, "data")
# Dossiers utilisateur dans 'data' (assumés)
RESSOURCES_3D_DIR = os.path.join(DATA_DIR, "3d_ressources")
# Script du système de jeu final
GAME_SYS_SCRIPT = os.path.join(PROGRAMS_DIR, "game_os", "game_os.py")

# Liste des assets pour la simulation (MISE À JOUR)
ASSETS = [
    "Tree.obj", "Stone.obj", "House_1.obj", 
    "House_2.obj", "lost_factory.obj", "Bottle.obj"
]

# =========================
# Communication Helper
# =========================
def report_progress(percent, message):
    """Communique la progression à stdout pour loading_screen.py."""
    # Format exigé par loading_screen.py: PROGRESS:<percent>:<message>
    print(f"PROGRESS:{int(percent)}:{message}", flush=True) # flush=True est crucial

# =========================
# Logique Principale
# =========================
def load_save_data(slot_id):
    """Charge les données de la sauvegarde sélectionnée."""
    file_path = os.path.join(DATA_DIR, f"save_{slot_id}.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        report_progress(0, f"Erreur: Sauvegarde {slot_id} non trouvée.")
        sys.exit(1)
    except json.JSONDecodeError:
        report_progress(0, f"Erreur: Fichier de sauvegarde {slot_id} corrompu.")
        sys.exit(1)

def procedural_generation(slot_id):
    """Effectue toutes les étapes de génération demandées."""
    save_data = load_save_data(slot_id)
    if not save_data:
        return
        
    seed = save_data.get('seed', 1) # Récupère le seed créé dans new_game.py
    
    report_progress(5, f"Initialisation du générateur avec le SEED: {seed}")
    time.sleep(0.5)

    # 1. Génération de la carte de l'île
    report_progress(20, "Génération des contours et biomes de l'île...")
    # Code réel pour la génération de la carte (ex: Perlin Noise)
    time.sleep(1.0)
    
    # 2. Placement des structures et des rochers/arbres
    total_assets_to_place = len(ASSETS)
    
    for i, asset_name in enumerate(ASSETS):
        percent = 20 + int((i+1) / total_assets_to_place * 60) # 20% à 80%
        
        # Vérification du type d'asset (Logique mise à jour pour les noms d'assets)
        if "House" in asset_name:
            task = f"Placement de la structure: {asset_name} (Maison)..."
        elif "factory" in asset_name:
            task = f"Placement de la structure: {asset_name} (Usine)..."
        elif "Tree" in asset_name:
            task = f"Distribution de la ressource naturelle: {asset_name} (Arbre)..."
        elif "Stone" in asset_name:
            task = f"Distribution de la ressource naturelle: {asset_name} (Rocher)..."
        else: # Pour "Bottle.obj" et tout autre déchet
            task = f"Chargement de l'asset: {asset_name}..."

        report_progress(percent, task)
        # Code réel pour le placement déterministe
        time.sleep(0.5)
        
    # 3. Placement des différents déchets
    # Cette étape se concentre uniquement sur les "déchets" (y compris ceux déjà listés)
    report_progress(85, "Dispersion des différents déchets...")
    # Le 'Bottle.obj' pourrait être un exemple de déchet à disperser massivement ici.
    time.sleep(1.0)
    
    # 4. Finalisation
    report_progress(95, "Nettoyage et sauvegarde finale du monde...")
    time.sleep(0.5)
    
    report_progress(100, "Génération terminée. Lancement du jeu.")
    
    # Lancement du système de jeu final (game_sys.py)
    if os.path.exists(GAME_SYS_SCRIPT):
        # Lancement du jeu principal
        subprocess.Popen([sys.executable, GAME_SYS_SCRIPT, str(slot_id)])
    else:
        # Envoie l'erreur à la console, mais le loading_screen.py va se fermer
        print(f"ERREUR CRITIQUE: {GAME_SYS_SCRIPT} est introuvable.", file=sys.stderr)
        
    sys.exit(0) # Termine le processus de génération

def main():
    if len(sys.argv) < 2:
        report_progress(0, "Erreur: ID de sauvegarde manquant pour la génération.")
        sys.exit(1)
    
    try:
        slot_id = int(sys.argv[1])
        procedural_generation(slot_id)
    except Exception as e:
        report_progress(0, f"Erreur inattendue pendant la génération: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()