import json
import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LANGUAGE_KEY = "language_selected"


def resolve_resource_paths():
    """Résout les bons chemins de ressources selon l'OS et la structure du projet."""
    resource_candidates = []

    if os.name == "nt":
        resource_candidates.append(os.path.join(BASE_DIR, "ports", "windows", "Ressource"))
        resource_candidates.append(os.path.join(BASE_DIR, "ports", "linux", "Ressource"))
    else:
        resource_candidates.append(os.path.join(BASE_DIR, "ports", "linux", "Ressource"))
        resource_candidates.append(os.path.join(BASE_DIR, "ports", "windows", "Ressource"))

    resource_candidates.append(os.path.join(BASE_DIR, "Ressource"))

    for ressource_dir in resource_candidates:
        programs_folder = os.path.join(ressource_dir, "programs")
        questionnary_script = os.path.join(programs_folder, "questionnary.py")
        game_launcher_script = os.path.join(programs_folder, "game_launcher.py")
        if os.path.exists(questionnary_script) and os.path.exists(game_launcher_script):
            data_filepath = os.path.join(ressource_dir, "data", "data.json")
            return data_filepath, questionnary_script, game_launcher_script

    fallback_ressource = os.path.join(BASE_DIR, "Ressource")
    fallback_programs = os.path.join(fallback_ressource, "programs")
    return (
        os.path.join(fallback_ressource, "data", "data.json"),
        os.path.join(fallback_programs, "questionnary.py"),
        os.path.join(fallback_programs, "game_launcher.py"),
    )


DATA_FILEPATH, QUESTIONNARY_SCRIPT, GAME_LAUNCHER_SCRIPT = resolve_resource_paths()


def install_dependencies():
    """Installe les dépendances manquantes."""
    required = ["customtkinter", "pygame", "opencv-python", "ursina", "pillow"]
    for package in required:
        try:
            if package == "opencv-python":
                module_name = "cv2"
            elif package == "pillow":
                module_name = "PIL"
            else:
                module_name = package.split('-')[0]

            __import__(module_name)
        except ImportError:
            print(f"Installation de {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except subprocess.CalledProcessError as e:
                print(f"Échec installation {package}: {e}")
                return False
            except KeyboardInterrupt:
                print("Installation interrompue par l'utilisateur.")
                return False
    return True

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
    if not install_dependencies():
        print("Dépendances incomplètes. Lance Runbefore.py puis réessaie.")
        return

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
        if launch_script(QUESTIONNARY_SCRIPT) and os.path.exists(DATA_FILEPATH):
            try:
                with open(DATA_FILEPATH, "r", encoding="utf-8") as f:
                    if json.load(f).get(LANGUAGE_KEY):
                        launch_script(GAME_LAUNCHER_SCRIPT)
            except Exception as e:
                print(f"Erreur lecture data.json après questionnaire: {e}")

if __name__ == "__main__":
    main()