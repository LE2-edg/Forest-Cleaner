# Forest-Cleaner

Le jeu se lance via `sources/main.py` qui ouvre un lanceur graphique (CustomTkinter). Ce lanceur permet d'installer les dépendances, de choisir la langue et de lancer le jeu 3D (`test/main.py`).

Alternativement, `sources/run_game.py` permet un lancement en ligne de commande.

Le script `sources/Runbefore.py` vérifie et installe séparément les paquets requis.

Les langues sont chargées depuis le fichier `sources/ports/windows/data/languages.json` qui contient les mots et phrases dans toutes les langues disponibles (français, anglais, espagnol, russe).
Les ressources 3D (modèles .OBJ) sont dans le dossier `data/models/`.

## Prototype 3D (dossier test / test folder)
Ce prototype ajoute un mini moteur 3D de type ray casting accessible via test/main.py. Déplacement ZQSD, rotation, sortie Échap. Fonctions clés : run() (boucle principale), handle_input() (contrôles ZQSD), cast_rays() (dessin des murs), draw_scene() (ciel/sol + mini-carte), draw_minimap() (vue top-down). Nécessite Pygame.
La carte actuelle représente une île avec un lac animé, un pont en bois, deux maisons (une à un étage, une à deux étages) avec portes et fenêtres, une grande usine fenêtrée et une voiture garée à côté. Le rendu est plus proche de Doom : nombre de rayons augmenté, motifs procéduraux (briques, tôles, bois, verre) au lieu de textures importées, dégradé ciel/sol, brouillard léger et ondulation de l'eau. Le lac est infranchissable sauf par le pont. Codes tuiles internes : 1 (bordure), H (maison 1 étage), T (maison 2 étages), W (eau), B (pont), F (usine), C (voiture), d (porte, franchissable), o (fenêtre).
This prototype adds a tiny ray-casting 3D engine available in test/main.py. Move with ZQSD, rotate, exit with Escape. The map is an island with animated lake, wooden bridge, two houses (one and two floors) featuring doors/windows, a windowed factory, and a parked car. Rendering is more Doom-inspired: higher ray density, procedural wall motifs (bricks, metal panels, wood, glass) instead of imported textures, sky/floor gradients, light fog, and water ripple. The lake blocks movement except on the bridge. Tile codes: 1 (border), H (one-floor house), T (two-floor house), W (water), B (bridge), F (factory), C (car), d (door, passable), o (window). Requires Pygame.