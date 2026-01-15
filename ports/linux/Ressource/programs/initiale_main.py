import json
import os
import sys # Ajouté pour subprocess si nécessaire, bien que main.py gère le lancement
import subprocess # Ajouté pour lancer le script

# --- Configuration des Chemins ---
RESOURCE_FOLDER = 'Ressource'
DATA_FOLDER = 'data'
DATA_FILENAME = 'data.json'
# Le chemin complet doit correspondre à la structure de main.py
data_file = os.path.join(RESOURCE_FOLDER, DATA_FOLDER, DATA_FILENAME)
lang_code = ""

# --- Fonctions de Logique ---

def get_language_code():
    """Cette fonction regarde le choix de la langue qui est dans data.json."""
    try:
        # NOTE: Le fichier n'est pas dans le même dossier que ce script, donc le chemin complet est nécessaire.
        with open(data_file, 'r', encoding='utf-8') as f:
            # Correction: utiliser .get() pour éviter KeyError
            lang_code = json.load(f).get("language_selected", "")
            return lang_code
    except FileNotFoundError:
        print(f"Erreur: Le fichier de données {data_file} est introuvable.")
        return ""
    except json.JSONDecodeError:
        print(f"Erreur: Le fichier de données {data_file} est corrompu.")
        return ""


def launch_game_interface():
    """Cette fonction lance le programme de sélection de la partie du joueur (game_launcher.py)."""
    interface_script_path = os.path.join('programs', 'game_launcher.py')
    print("Lancement du lanceur de jeu...")
    return interface_script_path

def initialization():
    """Cette fonction initialise la langue pour le reste des autre codes."""
    return get_language_code() 

def main ():
    """
    Cette fonction initialise le programme principal.
    Une fois la langue chargée, elle lance l'interface principale.
    """
    current_lang_code = initialization()
    
    if current_lang_code: 
        print(f"Langue sélectionnée : {current_lang_code}. Lancement de l'interface.")
        
        return launch_game_interface()
    else:
        print("Erreur: Langue non définie. Retour au lanceur principal.")
        return None


if __name__ == "__main__":
    script_path = main()
    if script_path:
        pass