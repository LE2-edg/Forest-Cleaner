# programs/game_os/game_sys.py - NOUVEAU FICHIER

import sys
import os

def main():
    if len(sys.argv) > 1:
        slot_id = sys.argv[1]
        print(f"--- Démarrage du système de jeu (game_sys) pour la sauvegarde {slot_id} ---")
    else:
        print("--- Démarrage du système de jeu (game_sys) ---")
    
    # =================================================================
    # ICI COMMENCERAIT LE CODE DE VOTRE MOTEUR DE JEU (BOUCLE PRINCIPALE)
    # Ex: Initialisation de Pygame et affichage du monde généré.
    # =================================================================
    
    print("Le monde est chargé. Forest Cleaner est prêt à jouer !")
    
if __name__ == "__main__":
    main()