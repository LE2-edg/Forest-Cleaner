# Forest Cleaner — Présentation du projet

## Description

**Forest Cleaner** est un jeu vidéo éducatif en 3D dont l'objectif est de nettoyer une île de tous ses déchets. Le joueur explore un environnement en vue à la première personne, ramasse les détritus (bouteilles, canettes, sacs plastiques, pneus, cartons, bidons), les transforme dans une usine de recyclage et fabrique les pièces d'un bateau pour s'échapper de l'île.

## Fonctionnalités principales

- **Moteur 3D** basé sur Ursina Engine (Panda3D) avec génération procédurale du monde.
- **Système de recyclage** : le joueur charge les déchets dans différentes machines (recycleur, fonderie, machine à carton) pour obtenir des matériaux (papier, plastique, métal).
- **Fabrication** : les matériaux permettent de forger ou fabriquer les pièces du bateau (barre, voile, ancre, boussole, rames).
- **Missions** : un système de tablette guide le joueur dans les étapes de construction.
- **Multilingue** : interface disponible en français, anglais, espagnol et russe.
- **Lanceur graphique** : un launcher basé sur CustomTkinter permet d'installer les dépendances, de choisir la langue et de lancer le jeu.
- **Modèles 3D éditables** : les meshes procéduraux peuvent être remplacés par des fichiers .OBJ créés dans Blender.

## Technologies utilisées

- **Python 3.8+**
- **Ursina Engine** (moteur 3D)
- **Pillow** (génération d'images procédurales)
- **CustomTkinter** (interface du lanceur)
- **Pygame** (prototype ray-casting)

## Comment lancer le jeu

1. Exécuter `sources/main.py` pour ouvrir le lanceur graphique.
2. Cliquer sur « Télécharger les ressources » pour installer les dépendances.
3. Cliquer sur « JOUER » pour démarrer le jeu.

Alternativement, exécuter `sources/run_game.py` pour un lancement en ligne de commande.

## Structure du dépôt

| Élément | Description |
|---|---|
| `présentation.md` | Ce fichier |
| `readme.md` | Documentation technique du projet |
| `licence.txt` | Licence du projet |
| `requirements.txt` | Dépendances Python |
| `sources/` | Code source (lanceur, ports, outils) |
| `data/` | Données du projet (modèles 3D) |
| `test/` | Prototype 3D et fichiers de test |

## Auteurs

Projet réalisé dans le cadre du Trophée NSI.
