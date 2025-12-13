import json
import os
DATA_FOLDER = 'Ressource/data'
DATA_FILENAME = 'data.json'
data_file = os.path.join(DATA_FOLDER, DATA_FILENAME)
data = {}
lang_code = ""

def game_lancher_ini():
    #Cette fonction lance le programme de sélection de la partie du joueur.
    print("Lancement du lanceur de jeu...")
    return "game_lancher.py"

def initialization():
    #Cette fonction initialise la langue pour le reste des autre codes
    return get_language_code() 

def get_language_code():
    #Cette fonction regarde le choix de la langue qui est dans data.json.
    with open(data_file, 'r', encoding='utf-8') as f:
        lang_code = json.load(f).get("language_selected", "")
        return lang_code


def main ():
    #Cette fonction initialise le programme principal. 
    #Une fois la langue chargée, elle affiche l'interface principale.
    #Une fois que la partie du joueur est sélectionnée, elle lance la partie du joueur.
    #Si le joueur n'a pas de partie déjà créée, elle lance la création de partie.
    current_lang_code = initialization()
    if current_lang_code: 
        print(f"Langue sélectionnée : {current_lang_code}")
        return game_lancher_ini()


if __name__ == "__main__":
    main()