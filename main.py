import json
import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILEPATH = os.path.join(BASE_DIR, 'Ressource', 'data', 'data.json')
PROGRAMS_FOLDER = os.path.join(BASE_DIR, 'Ressource', 'programs')

QUESTIONNARY_SCRIPT = os.path.join(PROGRAMS_FOLDER, "questionnary.py")
GAME_LAUNCHER_SCRIPT = os.path.join(PROGRAMS_FOLDER, "game_launcher.py")

LANGUAGE_KEY = "language_selected"

def install_dependencies():
    """Installe les dépendances manquantes."""
    required = ["customtkinter", "pygame", "opencv-python"]
    for package in required:
        try:
            __import__(package.split('-')[0] if package != "opencv-python" else "cv2")
        except ImportError:
            print(f"Installation de {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def launch_script(script_path):
    """Lance un script externe."""
    if not os.path.exists(script_path):
        print(f"ERREUR CRITIQUE : Le fichier {script_path} est introuvable.")
        return False
    try:
        subprocess.run([sys.executable, script_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Le script {script_path} a planté : {e}")
        return False

def main():
    print("--- Démarrage du Launcher ---")
    install_dependencies()
    lang_defined = False
    try:
        if os.path.exists(DATA_FILEPATH):
            with open(DATA_FILEPATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                val = data.get(LANGUAGE_KEY)
                if val and val != "None":
                    lang_defined = True
    except Exception as e:
        print(f"Erreur lecture data.json: {e}")

    if lang_defined:
        print("Langue détectée. Lancement du jeu.")
        launch_script(GAME_LAUNCHER_SCRIPT)
    else:
        print("Langue non définie. Lancement du questionnaire.")
        launch_script(QUESTIONNARY_SCRIPT)
        with open(DATA_FILEPATH, "r", encoding="utf-8") as f:
             if json.load(f).get(LANGUAGE_KEY):
                 launch_script(GAME_LAUNCHER_SCRIPT)

if __name__ == "__main__":
    main()