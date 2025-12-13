import tkinter as tk
import json
import os

# --- Configuration des Chemins ---
DATA_FOLDER = 'data'
LANGUAGES_FILE = 'languages.json'
LANGUAGES_FILEPATH = os.path.join(DATA_FOLDER, LANGUAGES_FILE)

# --- Configuration des Styles ---
BACKGROUND_COLOR = '#E0F0E0' # Vert clair tirant sur le blanc (Hex: #E0F0E0)
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
MAX_WIDTH = 7680
MAX_HEIGHT = 4320

# ----------------------------------------------------------------------
# 1. Fonctions de Chargement (Inchangées)
# ----------------------------------------------------------------------

def load_languages(filepath):
    """Charge les données de langues depuis le fichier JSON."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erreur : Le fichier {filepath} est introuvable. Utilisation des langues par défaut.")
        return [
            {"code": "en", "name": "English"},
            {"code": "fr", "name": "Français"}
        ]
    except json.JSONDecodeError:
        print(f"Erreur : Le fichier {filepath} n'est pas un JSON valide.")
        return []

def select_language(lang_code):
    """Fonction appelée lorsqu'un bouton de langue est cliqué."""
    print(f"Langue sélectionnée : {lang_code}")
    root.destroy()

# ----------------------------------------------------------------------
# 2. Configuration de l'Interface Utilisateur
# ----------------------------------------------------------------------

# Initialisation de la fenêtre Tkinter
root = tk.Tk()
root.title("Sélection de la Langue")

# --- 🛠️ 1. DIMENSIONS ET FOND ---

# 1.1 Définir la taille par défaut (geometry)
root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")

# 1.2 Définir les tailles minimale et maximale
root.minsize(DEFAULT_WIDTH, DEFAULT_HEIGHT) # Minimum = Taille par défaut
root.maxsize(MAX_WIDTH, MAX_HEIGHT)

# 1.3 Définir la couleur de fond
root.configure(bg=BACKGROUND_COLOR)

# S'assurer que les cellules de la grille s'étendent pour le centrage
root.grid_columnconfigure(0, weight=1) # Colonne principale pour centrer

# --- Variables et Structures ---

LANGUAGES = load_languages(LANGUAGES_FILEPATH)

# --- Affichage des messages de bienvenue ---

# 🛠️ 2. ALIGNEMENT À GAUCHE (Sticky="w")

label1 = tk.Label(
    root,
    text="Welcome, please select your language",
    bg=BACKGROUND_COLOR, # Appliquer la couleur de fond au Label
    justify=tk.LEFT,     # Justifier le texte à gauche (important si le texte s'étend sur plusieurs lignes)
    anchor="w"           # Ancrer le widget à l'Ouest (Left/Gauche)
)
# Utiliser sticky='w' (West/Ouest) pour pousser le widget à gauche de sa cellule.
label1.grid(column=0, row=0, padx=(20, 10), pady=10, sticky="w")

label2 = tk.Label(
    root,
    text="Bienvenu, veuillez sélectionner votre langue",
    bg=BACKGROUND_COLOR, # Appliquer la couleur de fond au Label
    justify=tk.LEFT,
    anchor="w"
)
label2.grid(column=0, row=1, padx=(20, 10), pady=5, sticky="w")

# --- 🛠️ 3. ALIGNEMENT DES BOUTONS (Centrés dans la partie basse) ---

# Nous allons créer une ligne vide pour pousser les boutons vers le bas (row 2)
# et leur donner une nouvelle ligne de départ (row 3).
BUTTON_START_ROW = 3

# Pousser les widgets vers le bas : on donne un poids élevé à la ligne au-dessus des boutons
# Ce poids fait en sorte que cette ligne prenne tout l'espace vertical disponible.
root.grid_rowconfigure(2, weight=1)

row_counter = BUTTON_START_ROW

for lang in LANGUAGES:
    lang_name = lang["name"]
    lang_code = lang["code"]

    btn = tk.Button(
        root,
        text=lang_name,
        command=lambda code=lang_code: select_language(code),
        width=25 # Largeur fixe pour le centrage visuel
    )
    # Les boutons sont placés au centre (sticky="") de la seule colonne disponible.
    btn.grid(column=0, row=row_counter, padx=10, pady=5, sticky="")
    row_counter += 1

# --- Lancement de la boucle principale ---

root.mainloop()

print("Programme terminé après sélection de la langue.")
