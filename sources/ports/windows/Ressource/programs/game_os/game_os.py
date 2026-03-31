"""
Forest Cleaner – Moteur de jeu 3D avec Ursina Engine (Panda3D).
Lancé depuis le système procédural après génération du monde.

Objectif : Ramasser tous les déchets sur l'île.

Contrôles :
  ZQSD / WASD  – Se déplacer
  Souris       – Regarder autour
  E            – Ramasser un déchet proche
  P            – Pause / Reprendre
  Échap        – Quitter et sauvegarder
"""

import math
import random
import sys
import os
import json

# =========================
# Paths
# =========================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROGRAMS_DIR = os.path.dirname(CURRENT_DIR)
RESOURCE_DIR = os.path.dirname(PROGRAMS_DIR)
DATA_DIR = os.path.join(RESOURCE_DIR, "data")

# =========================
# Installation automatique d'Ursina
# =========================
import subprocess

def ensure_ursina():
    try:
        import ursina
    except ImportError:
        print("Ursina non installé. Installation en cours...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ursina"])

ensure_ursina()

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.models.procedural.cylinder import Cylinder
from ursina.models.procedural.cone import Cone
from PIL import Image

# ============================================================
# Chargement de la sauvegarde
# ============================================================
def load_save(slot_id):
    """Charge les données de sauvegarde."""
    path = os.path.join(DATA_DIR, f"save_{slot_id}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur chargement sauvegarde {slot_id}: {e}")
        return {"seed": 42, "name": "Joueur", "progress": 0}

def save_game(slot_id, save_data):
    """Sauvegarde la progression."""
    path = os.path.join(DATA_DIR, f"save_{slot_id}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False)
        print(f"Partie sauvegardée: {path}")
    except Exception as e:
        print(f"Erreur de sauvegarde: {e}")

def load_language():
    """Charge la langue active."""
    try:
        data_path = os.path.join(DATA_DIR, "data.json")
        with open(data_path, "r", encoding="utf-8") as f:
            lang = json.load(f).get("language_selected", "fr")
        lang_path = os.path.join(DATA_DIR, "languages.json")
        with open(lang_path, "r", encoding="utf-8") as f:
            all_langs = json.load(f)
        return all_langs.get(lang, {})
    except:
        return {}

# ============================================================
# Configuration
# ============================================================
ISLAND_SIZE = 80
WATER_SIZE = 200
TREE_COUNT = 120
ROCK_COUNT = 40
TRASH_COUNT = 30
PICKUP_RANGE = 3.0

# ============================================================
# Textures procédurales
# ============================================================
def make_grass_texture():
    size = 64
    img = Image.new('RGB', (size, size), (34, 139, 34))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-20, 20)
            pixels[x, y] = (
                max(0, min(255, 34 + noise // 2)),
                max(0, min(255, 100 + noise)),
                max(0, min(255, 20 + noise // 3)),
            )
    return Texture(img)

def make_sand_texture():
    size = 64
    img = Image.new('RGB', (size, size), (210, 180, 140))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-15, 15)
            pixels[x, y] = (
                max(0, min(255, 210 + n)),
                max(0, min(255, 180 + n)),
                max(0, min(255, 140 + n)),
            )
    return Texture(img)

def make_bark_texture():
    size = 32
    img = Image.new('RGB', (size, size), (101, 67, 33))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-15, 15)
            pixels[x, y] = (
                max(0, min(255, 101 + n)),
                max(0, min(255, 67 + n)),
                max(0, min(255, 33 + n)),
            )
    return Texture(img)

def make_leaves_texture():
    size = 32
    img = Image.new('RGB', (size, size), (34, 120, 15))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-25, 25)
            pixels[x, y] = (
                max(0, min(255, 34 + n)),
                max(0, min(255, 120 + n)),
                max(0, min(255, 15 + n)),
            )
    return Texture(img)

def make_stone_texture():
    size = 32
    img = Image.new('RGB', (size, size), (130, 130, 130))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            v = max(0, min(255, 130 + random.randint(-20, 20)))
            pixels[x, y] = (v, v, v)
    return Texture(img)

def make_brick_texture():
    size = 64
    img = Image.new('RGB', (size, size), (178, 134, 100))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            row = y // 8
            offset = 8 if row % 2 else 0
            bx = (x + offset) % 16
            n = random.randint(-8, 8)
            if bx == 0 or y % 8 == 0:
                pixels[x, y] = (180, 180, 170)
            else:
                pixels[x, y] = (
                    max(0, min(255, 178 + n)),
                    max(0, min(255, 134 + n)),
                    max(0, min(255, 100 + n)),
                )
    return Texture(img)

def make_roof_texture():
    size = 32
    img = Image.new('RGB', (size, size), (139, 69, 19))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-10, 10)
            pixels[x, y] = (100, 50, 15) if y % 6 < 1 else (
                max(0, min(255, 139 + n)),
                max(0, min(255, 69 + n)),
                max(0, min(255, 19 + n)),
            )
    return Texture(img)

def make_metal_texture():
    size = 32
    img = Image.new('RGB', (size, size), (140, 140, 155))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-10, 10)
            pixels[x, y] = (100, 100, 110) if x % 10 < 1 else (
                max(0, min(255, 140 + n)),
                max(0, min(255, 140 + n)),
                max(0, min(255, 155 + n)),
            )
    return Texture(img)

def make_water_texture():
    size = 64
    img = Image.new('RGB', (size, size), (30, 100, 180))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            w = int(10 * math.sin(x * 0.3 + y * 0.2))
            pixels[x, y] = (
                max(0, min(255, 30 + w)),
                max(0, min(255, 100 + w)),
                max(0, min(255, 180 + w)),
            )
    return Texture(img)


# ============================================================
# Fonctions utilitaires
# ============================================================
def random_island_pos(margin=5):
    half = ISLAND_SIZE / 2 - margin
    return (random.uniform(-half, half), random.uniform(-half, half))

def distance_2d(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


# ============================================================
# Construction du monde 3D
# ============================================================
HOUSE_POSITIONS = [
    (-15, -10), (-15, -5), (-10, -10),
    (20, 15), (25, 15), (20, 20),
]

FACTORY_POS = (0, 0, 25)

TRASH_TYPES = [
    {'name': 'Bouteille', 'model': Cylinder, 'scale': (0.15, 0.4, 0.15),
     'color_rgb': (50, 180, 50), 'points': 10},
    {'name': 'Canette', 'model': Cylinder, 'scale': (0.12, 0.25, 0.12),
     'color_rgb': (200, 50, 50), 'points': 10},
    {'name': 'Sac plastique', 'model': 'cube', 'scale': (0.4, 0.05, 0.3),
     'color_rgb': (220, 220, 230), 'points': 5},
    {'name': 'Pneu', 'model': 'sphere', 'scale': (0.5, 0.25, 0.5),
     'color_rgb': (40, 40, 40), 'points': 25},
    {'name': 'Carton', 'model': 'cube', 'scale': (0.5, 0.3, 0.4),
     'color_rgb': (180, 150, 100), 'points': 5},
    {'name': 'Bidon', 'model': Cylinder, 'scale': (0.25, 0.5, 0.25),
     'color_rgb': (60, 80, 180), 'points': 15},
]


def build_world(seed_value):
    """Construit le monde 3D complet. Retourne la liste des déchets."""
    random.seed(seed_value)

    # Textures
    tex_grass  = make_grass_texture()
    tex_sand   = make_sand_texture()
    tex_bark   = make_bark_texture()
    tex_leaves = make_leaves_texture()
    tex_stone  = make_stone_texture()
    tex_brick  = make_brick_texture()
    tex_roof   = make_roof_texture()
    tex_metal  = make_metal_texture()
    tex_water  = make_water_texture()

    # Éclairage
    sun = DirectionalLight()
    sun.look_at(Vec3(1, -1, -1))
    sun.color = color.rgb(255, 244, 214)
    AmbientLight(color=color.rgb(100, 100, 120))
    Sky(color=color.rgb(135, 190, 240))

    scene.fog_color = color.rgb(180, 200, 220)
    scene.fog_density = 0.008

    # Terrain
    Entity(
        model='plane', scale=(ISLAND_SIZE, 1, ISLAND_SIZE),
        texture=tex_grass, texture_scale=(ISLAND_SIZE // 4, ISLAND_SIZE // 4),
        color=color.white, collider='box', position=(0, 0, 0),
    )
    Entity(
        model='plane', scale=(ISLAND_SIZE + 10, 1, ISLAND_SIZE + 10),
        texture=tex_sand, texture_scale=(ISLAND_SIZE // 4, ISLAND_SIZE // 4),
        color=color.white, collider='box', position=(0, -0.05, 0),
    )
    water_entity = Entity(
        model='plane', scale=(WATER_SIZE, 1, WATER_SIZE),
        texture=tex_water, texture_scale=(WATER_SIZE // 8, WATER_SIZE // 8),
        color=color.rgba(30, 100, 180, 180), position=(0, -0.3, 0),
    )

    # Maisons
    for hx, hz in HOUSE_POSITIONS:
        h = random.uniform(3, 5)
        w = random.uniform(4, 6)
        d = random.uniform(4, 6)
        Entity(model='cube', scale=(w, h, d), position=(hx, h / 2, hz),
               texture=tex_brick, texture_scale=(2, 2), color=color.white, collider='box')
        Entity(model='cube', scale=(w + 0.5, 0.5, d + 0.5), position=(hx, h + 0.25, hz),
               texture=tex_roof, texture_scale=(2, 1), color=color.white)
        Entity(model='cube', scale=(1, 2, 0.1), position=(hx, 1, hz + d / 2 + 0.05),
               color=color.rgb(101, 67, 33))
        for side in [-1, 1]:
            Entity(model='cube', scale=(0.1, 1, 1),
                   position=(hx + (w / 2 + 0.05) * side, h / 2, hz),
                   color=color.rgb(180, 220, 240))

    # Usine
    Entity(model='cube', scale=(12, 6, 8), position=(FACTORY_POS[0], 3, FACTORY_POS[2]),
           texture=tex_metal, texture_scale=(3, 2), color=color.white, collider='box')
    Entity(model=Cylinder(), scale=(1, 5, 1), position=(FACTORY_POS[0] + 4, 8, FACTORY_POS[2] + 2),
           color=color.rgb(100, 100, 100), collider='box')
    Entity(model='cube', scale=(3, 4, 0.1), position=(FACTORY_POS[0], 2, FACTORY_POS[2] - 4.05),
           color=color.rgb(80, 80, 90))

    # Arbres
    for _ in range(TREE_COUNT):
        attempts = 0
        while attempts < 50:
            tx, tz = random_island_pos(margin=3)
            too_close = any(distance_2d((tx, tz), (hx, hz)) < 8 for hx, hz in HOUSE_POSITIONS)
            if distance_2d((tx, tz), (FACTORY_POS[0], FACTORY_POS[2])) < 12:
                too_close = True
            if not too_close:
                break
            attempts += 1
        else:
            continue

        trunk_h = random.uniform(3, 6)
        trunk_r = random.uniform(0.2, 0.4)
        Entity(model=Cylinder(), scale=(trunk_r, trunk_h / 2, trunk_r),
               position=(tx, trunk_h / 2, tz), texture=tex_bark, color=color.white, collider='box')
        for level in range(3):
            Entity(model=Cone(), scale=(2.5 - level * 0.6, 1.5, 2.5 - level * 0.6),
                   position=(tx, trunk_h + level * 1.2, tz), texture=tex_leaves,
                   color=color.rgb(random.randint(20, 50), random.randint(100, 160), random.randint(10, 40)))

    # Rochers
    for _ in range(ROCK_COUNT):
        rx, rz = random_island_pos(margin=2)
        sf = random.uniform(0.5, 2.0)
        Entity(model='sphere', scale=(sf * random.uniform(0.8, 1.2), sf * random.uniform(0.5, 0.8),
               sf * random.uniform(0.8, 1.2)), position=(rx, sf * 0.3, rz), texture=tex_stone,
               color=color.rgb(random.randint(110, 150), random.randint(110, 150), random.randint(110, 150)),
               collider='box')

    # Clôture
    half = ISLAND_SIZE / 2
    for i in range(int(ISLAND_SIZE)):
        x = -half + i + 0.5
        for zs in [-1, 1]:
            Entity(model='cube', scale=(1, 1.5, 0.15), position=(x, 0.75, half * zs),
                   color=color.rgb(139, 90, 43))
        for xs in [-1, 1]:
            Entity(model='cube', scale=(0.15, 1.5, 1), position=(half * xs, 0.75, x),
                   color=color.rgb(139, 90, 43))

    # Pont
    Entity(model='cube', scale=(4, 0.3, 12), position=(-half - 2, 0.15, 0),
           color=color.rgb(160, 120, 80), texture=tex_bark, collider='box')
    for side in [-1, 1]:
        Entity(model='cube', scale=(0.2, 1.2, 12), position=(-half - 2 + side * 1.8, 0.6, 0),
               color=color.rgb(139, 90, 43))

    # Voitures
    car_data = [((10, -20), (200, 50, 50)), ((-25, 5), (50, 50, 200)), ((30, -5), (220, 180, 30))]
    for (cx, cz), cc in car_data:
        cc_color = color.rgb(*cc)
        Entity(model='cube', scale=(2, 1, 4), position=(cx, 0.7, cz), color=cc_color, collider='box')
        Entity(model='cube', scale=(1.8, 0.8, 2), position=(cx, 1.6, cz), color=cc_color * 0.85)
        for wx in [-1, 1]:
            for wz in [-1.2, 1.2]:
                Entity(model=Cylinder(), scale=(0.4, 0.15, 0.4),
                       position=(cx + wx * 1.1, 0.3, cz + wz), rotation=(0, 0, 90),
                       color=color.rgb(30, 30, 30))

    # Déchets
    trash_list = []
    for _ in range(TRASH_COUNT):
        tx, tz = random_island_pos(margin=2)
        tt = random.choice(TRASH_TYPES)
        model_val = tt['model']() if callable(tt['model']) else tt['model']
        e = Entity(model=model_val, scale=tt['scale'],
                   position=(tx, tt['scale'][1] / 2 + 0.01, tz),
                   color=color.rgb(*tt['color_rgb']), collider='box')
        e.trash_name = tt['name']
        e.trash_points = tt['points']
        e.original_y = e.y
        ind = Entity(model='sphere', scale=0.15,
                     position=(tx, tt['scale'][1] + 0.8, tz),
                     color=color.rgb(255, 255, 100), unlit=True)
        e.indicator = ind
        trash_list.append(e)

    return trash_list, water_entity


# ============================================================
# Point d'entrée principal
# ============================================================
def main():
    slot_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    save_data = load_save(slot_id)
    seed_value = save_data.get('seed', 42)
    player_name = save_data.get('name', 'Joueur')
    initial_progress = save_data.get('progress', 0)
    lang = load_language()

    print(f"=== Forest Cleaner 3D ===")
    print(f"  Joueur: {player_name}")
    print(f"  Seed: {seed_value}")
    print(f"  Slot: {slot_id}")
    print(f"=========================")

    # Ursina app
    app = Ursina(
        title=f'Forest Cleaner - {player_name}',
        borderless=False,
        fullscreen=False,
        size=(1280, 720),
        development_mode=False,
    )

    # Construire le monde
    print("Construction du monde 3D...")
    trash_items, water_entity = build_world(seed_value)

    # Joueur
    player = FirstPersonController(
        position=(0, 2, -30),
        speed=8,
        jump_height=2,
        mouse_sensitivity=Vec2(80, 80),
    )
    player.cursor.visible = False

    # HUD
    total_points = sum(t.trash_points for t in trash_items)
    score = [0]
    trash_remaining = [len(trash_items)]
    game_won = [False]
    closest_trash = [None]
    anim_time = [0.0]
    paused = [False]

    score_bg = Entity(parent=camera.ui, model='quad', scale=(0.4, 0.08),
                      position=(-0.5, 0.45), color=color.rgba(0, 0, 0, 150))
    score_text = Text(text=f'{player_name}  |  Déchets: {initial_progress}/{TRASH_COUNT}  |  Score: 0',
                      position=(-0.7, 0.47), scale=1.1, color=color.white)

    action_text = Text(text='', position=(0, -0.3), origin=(0, 0), scale=1.5, color=color.yellow)
    win_text = Text(text='', position=(0, 0.1), origin=(0, 0), scale=3, color=color.green)
    pause_text = Text(text='', position=(0, 0.05), origin=(0, 0), scale=2.5, color=color.white)

    Entity(parent=camera.ui, model='quad', scale=0.008, color=color.white)

    minimap_bg = Entity(parent=camera.ui, model='quad', scale=(0.2, 0.2),
                        position=(0.7, 0.35), color=color.rgba(0, 0, 0, 100))
    minimap_dot = Entity(parent=camera.ui, model='circle', scale=0.01,
                         position=(0.7, 0.35), color=color.red, z=-0.1)

    instr_bg = Entity(parent=camera.ui, model='quad', scale=(0.5, 0.12),
                      position=(0, -0.42), color=color.rgba(0, 0, 0, 120))
    instr_text = Text(
        text='ZQSD: Bouger | Souris: Regarder | E: Ramasser | P: Pause | Échap: Quitter',
        position=(0, -0.4), origin=(0, 0), scale=0.9, color=color.rgb(200, 200, 200))

    half_island = ISLAND_SIZE / 2
    water_time = [0.0]

    def update():
        anim_time[0] += time.dt

        if anim_time[0] > 10:
            instr_bg.visible = False
            instr_text.visible = False

        if paused[0]:
            return

        # Eau animée
        water_time[0] += time.dt
        water_entity.y = -0.3 + math.sin(water_time[0] * 0.5) * 0.1

        # Limites
        if player.y < -5:
            player.position = Vec3(0, 2, -30)
        border = half_island + 6
        player.x = max(-border, min(border, player.x))
        player.z = max(-border, min(border, player.z))

        if game_won[0]:
            return

        best_dist = PICKUP_RANGE + 1
        best = None
        pp = (player.x, player.z)

        for t in trash_items:
            d = distance_2d(pp, (t.x, t.z))
            t.y = t.original_y + math.sin(anim_time[0] * 2 + t.x) * 0.05
            t.indicator.y = t.y + 0.7
            if d < PICKUP_RANGE and d < best_dist:
                best_dist = d
                best = t

        closest_trash[0] = best
        if best:
            action_text.text = f'[E] Ramasser {best.trash_name}'
            best.indicator.color = color.rgb(50, 255, 50)
            best.indicator.scale = 0.25
        else:
            action_text.text = ''

        for t in trash_items:
            if t != best:
                t.indicator.color = color.rgb(255, 255, 100)
                t.indicator.scale = 0.15

        ms = 0.2 / ISLAND_SIZE
        minimap_dot.x = 0.7 + player.x * ms
        minimap_dot.y = 0.35 + player.z * ms

    def input(key):
        if key == 'p':
            paused[0] = not paused[0]
            pause_text.text = '⏸ PAUSE' if paused[0] else ''
            player.enabled = not paused[0]
            mouse.locked = not paused[0]

        if key == 'e' and closest_trash[0] and not game_won[0] and not paused[0]:
            t = closest_trash[0]
            score[0] += t.trash_points
            trash_items.remove(t)
            destroy(t.indicator)
            destroy(t)
            trash_remaining[0] -= 1

            collected = TRASH_COUNT - trash_remaining[0]
            score_text.text = f'{player_name}  |  Déchets: {collected}/{TRASH_COUNT}  |  Score: {score[0]}/{total_points}'
            action_text.text = ''
            closest_trash[0] = None

            flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                           color=color.rgba(255, 255, 200, 80), z=-1)
            destroy(flash, delay=0.15)

            # Sauvegarder la progression
            save_data['progress'] = collected
            save_game(slot_id, save_data)

            if trash_remaining[0] <= 0:
                game_won[0] = True
                win_text.text = 'BRAVO ! Île nettoyée !'
                Text(text=f'Score final: {score[0]} points', position=(0, 0),
                     origin=(0, 0), scale=2, color=color.white)

        if key == 'escape':
            collected = TRASH_COUNT - trash_remaining[0]
            save_data['progress'] = collected
            save_game(slot_id, save_data)
            application.quit()

    app.update = update
    app.input = input

    print("=== Le monde est prêt ! ===")
    app.run()


if __name__ == "__main__":
    main()