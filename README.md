# Forest-Cleaner

Le jeu se lance sur "main.py" qui vérifie si les dépendances python nécessaire pour ce projet soit bien installés sinon elle les installe. Après cette
vérification, elle renvoie à un autre programme selon s'il y a une langue définie dans le fichier "Ressource/data/data.json" ou non. S'il n'y a pas de langue
définie, le programme lance "questionnary.py" qui demande à l'utilisateur de choisir une langue parmi celles disponibles. Sinon, le programme lance directement
"game_launcher.py" qui démarre le jeu.
Le script "game_launcher.py" initialise les paramètres du jeu, charge les ressources nécessaires et lance la boucle principale du jeu avec une interface graphique
créée avec Pygame et des captures vidéos de parties qu'on aura crées (ici se sont 3 fois la même vidéos de captures d'écran du code qui ne font rien). Il y a deux
boutons dans le menu principal : "Jouer" et les paramètres. Le bouton "Jouer" lance une page de séléction de sauvegardes qui permet de choisir une sauvegarde.
Si aucune sauvegarde n'existe, il y a un bouton "Nouvelle partie" qui permet de créer une nouvelle sauvegarde. Le bouton des paramètres ouvre une page qui permet
de modifier les paramètres du jeu (volume, langue). Lors de la création d'une nouvelle partie, le joueur peut choisir son nom. Ensuite, le code crée une sauvegarde
dans le dossier data avec le nom, l'avancement, etc. Ensuite le fichier "process.py" est lancé pour faire la création du monde avec un système de génération procédurale.

Les langues sont chargés depuis le fichier "Ressource/data/languages.json" qui contient les mots et phrases dans toutes les langues disponibles.
Les ressources 3D sont dans le dossier "Ressource/data/3d_ressources".

## Prototype 3D (dossier test / test folder)
Ce prototype ajoute un mini moteur 3D de type ray casting accessible via test/main.py. Déplacement ZQSD, rotation, sortie Échap. Fonctions clés : run() (boucle principale), handle_input() (contrôles ZQSD), cast_rays() (dessin des murs), draw_scene() (ciel/sol + mini-carte), draw_minimap() (vue top-down). Nécessite Pygame.
La carte actuelle représente une île avec un lac animé, un pont en bois, deux maisons (une à un étage, une à deux étages) avec portes et fenêtres, une grande usine fenêtrée et une voiture garée à côté. Le rendu est plus proche de Doom : nombre de rayons augmenté, motifs procéduraux (briques, tôles, bois, verre) au lieu de textures importées, dégradé ciel/sol, brouillard léger et ondulation de l'eau. Le lac est infranchissable sauf par le pont. Codes tuiles internes : 1 (bordure), H (maison 1 étage), T (maison 2 étages), W (eau), B (pont), F (usine), C (voiture), d (porte, franchissable), o (fenêtre).
This prototype adds a tiny ray-casting 3D engine available in test/main.py. Move with ZQSD, rotate, exit with Escape. The map is an island with animated lake, wooden bridge, two houses (one and two floors) featuring doors/windows, a windowed factory, and a parked car. Rendering is more Doom-inspired: higher ray density, procedural wall motifs (bricks, metal panels, wood, glass) instead of imported textures, sky/floor gradients, light fog, and water ripple. The lake blocks movement except on the bridge. Tile codes: 1 (border), H (one-floor house), T (two-floor house), W (water), B (bridge), F (factory), C (car), d (door, passable), o (window). Requires Pygame.