import json
import os
import sys
import subprocess

# --- Configuration des Chemins ---
DATA_FOLDER = 'Ressource/data'
DATA_FILENAME = 'data.json'
# Chemin complet pour le fichier de données
DATA_FILEPATH = os.path.join(DATA_FOLDER, DATA_FILENAME)

LANGUAGE_KEY = "language_selected" # Clé corrigée (sans 's' à la fin)
PROGRAMS_FOLDER = 'programs'
QUESTIONNARY_FILE = "questionnary.py"
INITIALE_MAIN_FILE = "initiale_main.py"

# Définition des chemins de script en utilisant os.path.join
questionnary_path = os.path.join(PROGRAMS_FOLDER, QUESTIONNARY_FILE)
initiale_main_path = os.path.join(PROGRAMS_FOLDER, INITIALE_MAIN_FILE)
imp = initiale_main_path


def questionnare_launch():
    return questionnary_path

def initial_launch():
    return imp

# --- Fonctions d'Installation/Vérification (Mises à jour) ---

def tkinter_installed():
    """Cette fonction sert à vérifier si tkinter est installé ou pas"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def tkinter_installer():
    """Installe tkinter en utilisant pip. (Note: Peut échouer car souvent intégré.)"""
    # Si cette fonction échoue (False), le programme continuera mais sans support Tkinter.
    return False

def customtkinter_installed():
    """Vérifie si le module customtkinter est installé."""
    try:
        import customtkinter
        return True
    except ImportError:
        return False

def customtkinter_installer():
    """Installe customtkinter en utilisant pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def launch_script(script_path):
    """Exécute un script Python externe."""
    if not os.path.exists(script_path):
        return False
    
    try:
        subprocess.run([sys.executable, script_path], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    if tkinter_installed() == False:
        tkinter_installer()
    if customtkinter_installed() == False:
        customtkinter_installer()

    try:
        with open(DATA_FILEPATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return questionnare_launch()

    selected_value = data.get(LANGUAGE_KEY)
    if selected_value is not None and selected_value != "None":
        return initial_launch()
    else:
        return questionnare_launch()

if __name__ == "__main__":
    script_to_run = main()
    launch_script(script_to_run)