import json
import os
import sys
import subprocess

# --- Configuration des Chemins ---
DATA_FOLDER = 'Ressource/data'
DATA_FILENAME = 'data.json'
# Chemin complet pour le fichier de données
DATA_FILEPATH = os.path.join(DATA_FOLDER, DATA_FILENAME)

LANGUAGE_KEY = "language_selected"
PROGRAMS_FOLDER = 'programs'
QUESTIONNARY_FILE = "questionnary.py"
INITIALE_MAIN_FILE = "initiale_main.py"

# Définition des chemins de script en utilisant os.path.join
initiale_main_path = os.path.join(PROGRAMS_FOLDER, INITIALE_MAIN_FILE)
imp = initiale_main_path


def questionnare_launch():
    print("Launching questionnary...")
    # NOTE: Pour la robustesse, il est préférable de retourner le chemin complet du fichier
    return os.path.join(PROGRAMS_FOLDER, QUESTIONNARY_FILE)

def initial_launch():
    print("Launching initiale main...")
    return imp

# --- Fonctions d'Installation/Vérification ---

def check_and_install_module(module_name, import_name=None):
    """Vérifie si un module est installé et tente de l'installer si non."""
    if import_name is None:
        import_name = module_name
        
    print(f"Checking {import_name} installation...")
    
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"{import_name} not installed. Installing {module_name}...")
        try:
            # Utiliser la version du package pour pip
            subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
            print(f"{import_name} installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing {module_name}: {e}")
            return False
        except FileNotFoundError:
            print(f"Error: pip not found for installing {module_name}.")
            return False

def tkinter_installed():
    """Cette fonction sert à vérifier si tkinter est installé ou pas"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def tkinter_installer():
    """Installe tkinter en utilisant pip. (Souvent impossible/inutile)."""
    return False

# --- Nouvelle Fonction pour Gérer Toutes les Dépendances ---

def install_required_dependencies():
    """Vérifie et installe toutes les dépendances requises."""
    
    # Dépendances requises pour l'interface, l'audio et la vidéo
    
    # 1. Tkinter (Vérification spéciale car installation par pip impossible)
    if not tkinter_installed():
        tkinter_installer()
        
    # 2. customtkinter (Interface)
    check_and_install_module("customtkinter")
    
    # 3. pygame (Audio)
    check_and_install_module("pygame")
    
    # 4. opencv-python (Vidéo)
    check_and_install_module("opencv-python", import_name="cv2")
    
    print("All dependency checks completed.")

def launch_script(script_path):
    print("Launching script:", script_path)
    """Exécute un script Python externe."""
    if not os.path.exists(script_path):
        print(f"Error: Script {script_path} not found.")
        return False
    
    try:
        subprocess.run([sys.executable, script_path], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    print("Main launched")
    
    # 🛠️ AJOUT CRITIQUE : Vérification et installation de toutes les dépendances
    install_required_dependencies()
    
    # Lecture du fichier de configuration
    try:
        with open(DATA_FILEPATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error reading {DATA_FILEPATH}. Launching questionnary for initialization.")
        return questionnare_launch()

    # Logique de sélection de la langue
    selected_value = data.get(LANGUAGE_KEY)
    if selected_value is not None and selected_value != "None":
        return initial_launch()
    else:
        return questionnare_launch()

if __name__ == "__main__":
    script_to_run = main()
    launch_script(script_to_run)