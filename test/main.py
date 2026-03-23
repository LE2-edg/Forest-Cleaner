"""
Forest Cleaner – Prototype 3D complet avec Ursina Engine (Panda3D).
Objectif : Ramasser tous les déchets sur l'île.

Contrôles :
  ZQSD / WASD  – Se déplacer
  Souris       – Regarder autour
  E            – Ramasser un déchet proche
  Échap        – Quitter
"""

import math
import random
import sys
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.models.procedural.cylinder import Cylinder
from ursina.models.procedural.cone import Cone
from PIL import Image

# ============================================================
# Configuration
# ============================================================
ISLAND_SIZE = 80          # taille de l'île (unités)
WATER_SIZE = 200          # taille de l'eau autour
TREE_COUNT = 120          # nombre d'arbres
ROCK_COUNT = 40           # nombre de rochers
TRASH_COUNT = 30          # nombre de déchets à ramasser
PICKUP_RANGE = 3.0        # distance max pour ramasser
SEED = 42

random.seed(SEED)

# ============================================================
# Application Ursina
# ============================================================
app = Ursina(
    title='Forest Cleaner - 3D Prototype',
    borderless=False,
    fullscreen=False,
    size=(1280, 720),
    development_mode=False,
)

# ============================================================
# Textures procédurales
# ============================================================

def make_grass_texture():
    """Texture d'herbe procédurale."""
    size = 128
    img = Image.new('RGBA', (size, size), (34, 139, 34, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-20, 20)
            blade = int(math.sin(x * 0.6 + y * 0.3) * 10 + math.cos(x * 0.2) * 8)
            g = max(0, min(255, 100 + noise + blade))
            r = max(0, min(255, 34 + noise // 2))
            b = max(0, min(255, 20 + noise // 3))
            if random.random() > 0.95:
                g = min(255, g + 40)
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

def make_sand_texture():
    """Texture de sable procédurale."""
    size = 128
    img = Image.new('RGBA', (size, size), (210, 180, 140, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-15, 15)
            ripple = int(math.sin(x * 0.3 + y * 0.15) * 8)
            pixels[x, y] = (
                max(0, min(255, 210 + noise + ripple)),
                max(0, min(255, 180 + noise + ripple)),
                max(0, min(255, 140 + noise)),
                255,
            )
    return Texture(img)

def make_bark_texture():
    """Texture d'écorce brune avec fibres verticales et crevasses."""
    size = 128
    img = Image.new('RGBA', (size, size), (120, 80, 45, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-8, 8)
            base_r = 120 + noise
            base_g = 80 + noise
            base_b = 45 + noise
            # Fibres verticales
            fiber = int(math.sin(x * 1.5 + math.sin(y * 0.1) * 2) * 12)
            base_r += fiber
            base_g += int(fiber * 0.7)
            base_b += int(fiber * 0.4)
            # Crevasses sombres verticales
            crack = math.sin(x * 0.8 + math.sin(y * 0.15) * 3)
            if abs(crack) > 0.88:
                base_r -= 45
                base_g -= 35
                base_b -= 20
            # Variation horizontale (anneaux)
            ring = int(math.sin(y * 0.3) * 6)
            base_r += ring
            base_g += int(ring * 0.6)
            pixels[x, y] = (
                max(0, min(255, base_r)),
                max(0, min(255, base_g)),
                max(0, min(255, base_b)),
                255,
            )
    return Texture(img)

def make_leaves_texture():
    """Texture de feuillage détaillée avec variation de vert."""
    size = 128
    img = Image.new('RGBA', (size, size), (40, 130, 25, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-15, 15)
            # Variation de tons de vert
            cluster = math.sin(x * 0.2 + y * 0.15) * 20 + math.cos(x * 0.3 - y * 0.25) * 15
            # Ombres entre les feuilles
            shadow = -20 if math.sin(x * 0.5 + y * 0.4) * math.cos(x * 0.35) > 0.6 else 0
            # Highlights
            highlight = 25 if math.sin(x * 0.15 - y * 0.2) > 0.85 else 0
            r = max(0, min(255, 35 + noise + int(cluster * 0.3) + shadow))
            g = max(0, min(255, 130 + noise + int(cluster) + shadow + highlight))
            b = max(0, min(255, 20 + noise + int(cluster * 0.2) + shadow))
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

def make_stone_texture():
    """Texture de pierre haute-contraste avec fissures visibles."""
    size = 128
    img = Image.new('RGBA', (size, size), (140, 135, 128, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-15, 15)
            # Base grise avec variation
            base = 140 + noise
            # Veines foncées
            vein1 = math.sin(x * 0.25 + y * 0.12) * 25
            vein2 = math.cos(x * 0.15 - y * 0.3) * 15
            # Fissures nettes
            crack = 0
            if abs(math.sin(x * 0.4 + y * 0.08 + math.sin(y * 0.1) * 3)) > 0.92:
                crack = -50
            # Taches sombres
            spot = math.sin(x * 0.07) * math.cos(y * 0.09) * 30
            v = int(max(50, min(200, base + vein1 + vein2 + crack + spot)))
            r = max(0, min(255, v + random.randint(-3, 5)))
            g = max(0, min(255, v - 2 + random.randint(-3, 3)))
            b = max(0, min(255, v - 6 + random.randint(-2, 2)))
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

def make_wood_floor_texture():
    """Texture de plancher en bois."""
    size = 128
    img = Image.new('RGBA', (size, size), (160, 120, 70, 255))
    pixels = img.load()
    plank_w = 16
    for x in range(size):
        for y in range(size):
            noise = random.randint(-8, 8)
            if x % plank_w == 0:
                pixels[x, y] = (90, 60, 30, 255)
            else:
                grain = int(math.sin(y * 0.5 + x * 0.1) * 8)
                knot = int(math.sin(x * 0.15) * math.cos(y * 0.12) * 12)
                pixels[x, y] = (
                    max(0, min(255, 160 + noise + grain + knot)),
                    max(0, min(255, 120 + noise + grain + knot)),
                    max(0, min(255, 70 + noise)),
                    255,
                )
    return Texture(img)

def make_brick_texture():
    """Texture de briques pour les maisons."""
    size = 128
    img = Image.new('RGBA', (size, size), (178, 134, 100, 255))
    pixels = img.load()
    brick_h = 12
    brick_w = 24
    for x in range(size):
        for y in range(size):
            row = y // brick_h
            offset = (brick_w // 2) if row % 2 == 1 else 0
            bx = (x + offset) % brick_w
            noise = random.randint(-8, 8)
            if bx == 0 or y % brick_h == 0:
                pixels[x, y] = (180, 180, 170, 255)  # mortier
            else:
                wear = int(math.sin(x * 0.1 + y * 0.2) * 6)
                pixels[x, y] = (
                    max(0, min(255, 178 + noise + wear)),
                    max(0, min(255, 134 + noise + wear)),
                    max(0, min(255, 100 + noise)),
                    255,
                )
    return Texture(img)

def make_roof_texture():
    """Texture de toit avec tuiles."""
    size = 128
    img = Image.new('RGBA', (size, size), (139, 69, 19, 255))
    pixels = img.load()
    tile_h = 10
    tile_w = 16
    for x in range(size):
        for y in range(size):
            noise = random.randint(-10, 10)
            row = y // tile_h
            offset = (tile_w // 2) if row % 2 == 1 else 0
            tx = (x + offset) % tile_w
            if y % tile_h < 1 or tx == 0:
                pixels[x, y] = (90, 40, 10, 255)
            else:
                shadow = int(math.sin(tx * 0.3) * 10)
                pixels[x, y] = (
                    max(0, min(255, 139 + noise + shadow)),
                    max(0, min(255, 69 + noise + shadow)),
                    max(0, min(255, 19 + noise)),
                    255,
                )
    return Texture(img)

def make_metal_texture():
    """Texture métallique pour l'usine."""
    size = 128
    img = Image.new('RGBA', (size, size), (140, 140, 155, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-10, 10)
            # Rivets / joints
            rivet_x = x % 24 < 1
            rivet_y = y % 24 < 1
            scratch = int(math.sin(x * 0.5 + y * 0.1) * 6)
            if rivet_x or rivet_y:
                pixels[x, y] = (95, 95, 105, 255)
            elif (x % 24 in (1, 2)) and (y % 24 in range(10, 14)):
                pixels[x, y] = (170, 170, 180, 255)  # rivet highlight
            else:
                pixels[x, y] = (
                    max(0, min(255, 140 + noise + scratch)),
                    max(0, min(255, 140 + noise + scratch)),
                    max(0, min(255, 155 + noise)),
                    255,
                )
    return Texture(img)

def make_water_texture():
    """Texture d'eau avec vagues."""
    size = 128
    img = Image.new('RGBA', (size, size), (30, 100, 180, 200))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            wave1 = int(12 * math.sin(x * 0.25 + y * 0.15))
            wave2 = int(6 * math.cos(x * 0.15 - y * 0.3))
            foam = 25 if math.sin(x * 0.3 + y * 0.08) > 0.9 else 0
            pixels[x, y] = (
                max(0, min(255, 30 + wave1 + foam)),
                max(0, min(255, 100 + wave1 + wave2 + foam)),
                max(0, min(255, 180 + wave2 + foam)),
                200,
            )
    return Texture(img)

def make_glass_texture():
    """Texture de verre (bouteille)."""
    size = 64
    img = Image.new('RGBA', (size, size), (60, 180, 70, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-15, 15)
            highlight = int(math.sin(x * 0.4) * 25) if (x + y) % 12 < 3 else 0
            refract = int(math.sin(y * 0.2) * 10)
            pixels[x, y] = (
                max(0, min(255, 60 + n + highlight)),
                max(0, min(255, 180 + n + highlight + refract)),
                max(0, min(255, 70 + n + highlight)),
                255,
            )
    return Texture(img)

def make_can_texture():
    """Texture de canette métallique."""
    size = 64
    img = Image.new('RGBA', (size, size), (200, 50, 50, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-10, 10)
            if y < 6 or y > size - 7:
                pixels[x, y] = (max(0, 180 + n), max(0, 180 + n), max(0, 180 + n), 255)
            elif y % 8 < 1:
                pixels[x, y] = (min(255, 220 + n), max(0, 60 + n), max(0, 60 + n), 255)
            else:
                shine = int(math.sin(x * 0.3) * 15)
                pixels[x, y] = (
                    max(0, min(255, 200 + n + shine)),
                    max(0, min(255, 50 + n)),
                    max(0, min(255, 50 + n)),
                    255,
                )
    return Texture(img)

def make_cardboard_texture():
    """Texture de carton."""
    size = 64
    img = Image.new('RGBA', (size, size), (185, 155, 110, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-12, 12)
            corrugation = int(math.sin(y * 0.8) * 6)
            if x % 10 < 1:
                pixels[x, y] = (max(0, 160 + n), max(0, 130 + n), max(0, 90 + n), 255)
            else:
                pixels[x, y] = (
                    max(0, min(255, 185 + n + corrugation)),
                    max(0, min(255, 155 + n + corrugation)),
                    max(0, min(255, 110 + n)),
                    255,
                )
    return Texture(img)

def make_plastic_texture():
    """Texture de plastique froissé (sac)."""
    size = 64
    img = Image.new('RGBA', (size, size), (220, 220, 235, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-20, 20)
            wrinkle = int(math.sin(x * 0.5 + y * 0.3) * 15 + math.cos(x * 0.2 - y * 0.4) * 10)
            pixels[x, y] = (
                max(0, min(255, 220 + n + wrinkle)),
                max(0, min(255, 220 + n + wrinkle)),
                max(0, min(255, 235 + n)),
                255,
            )
    return Texture(img)

def make_rubber_texture():
    """Texture de caoutchouc (pneu)."""
    size = 64
    img = Image.new('RGBA', (size, size), (35, 35, 35, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-8, 8)
            groove = 15 if (x + y * 2) % 6 < 1 else 0
            tread = int(math.sin(x * 0.4) * 8) if y % 4 == 0 else 0
            v = max(0, min(255, 35 + n + groove + tread))
            pixels[x, y] = (v, v, v, 255)
    return Texture(img)

def make_barrel_texture():
    """Texture de bidon métallique."""
    size = 64
    img = Image.new('RGBA', (size, size), (50, 70, 170, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            n = random.randint(-10, 10)
            rust = int(math.sin(x * 0.15 + y * 0.08) * 12)
            if y % 12 < 1:
                pixels[x, y] = (80, 80, 90, 255)  # cerclage
            else:
                pixels[x, y] = (
                    max(0, min(255, 50 + n + rust)),
                    max(0, min(255, 70 + n)),
                    max(0, min(255, 170 + n - abs(rust))),
                    255,
                )
    return Texture(img)

def make_door_texture():
    """Texture de porte en bois avec panneaux et poignée."""
    size = 128
    img = Image.new('RGBA', (size, size), (110, 72, 38, 255))
    pixels = img.load()
    panel_margin = 12
    panel_gap = 6
    mid_y = size // 2
    for x in range(size):
        for y in range(size):
            noise = random.randint(-6, 6)
            grain = int(math.sin(y * 0.6 + x * 0.05) * 5)
            r_base = 110 + noise + grain
            g_base = 72 + noise + grain
            b_base = 38 + noise
            # Cadre autour de la porte
            if x < 5 or x >= size - 5 or y < 5 or y >= size - 5:
                r_base -= 30
                g_base -= 20
                b_base -= 12
            # Deux panneaux (haut et bas)
            in_panel_top = (panel_margin < x < size - panel_margin and
                           panel_margin < y < mid_y - panel_gap)
            in_panel_bot = (panel_margin < x < size - panel_margin and
                           mid_y + panel_gap < y < size - panel_margin)
            if in_panel_top or in_panel_bot:
                # Bord du panneau
                px = x - panel_margin
                py = y - (panel_margin if in_panel_top else mid_y + panel_gap)
                pw = size - 2 * panel_margin
                ph = (mid_y - panel_gap - panel_margin) if in_panel_top else (size - panel_margin - mid_y - panel_gap)
                if px < 3 or px > pw - 4 or py < 3 or py > ph - 4:
                    r_base -= 18
                    g_base -= 12
                    b_base -= 8
                else:
                    r_base += 8
                    g_base += 5
                    b_base += 3
            # Poignée (petit cercle doré)
            dx = x - (size - 25)
            dy = y - (mid_y)
            if dx * dx + dy * dy < 16:
                r_base = 200 + noise
                g_base = 170 + noise
                b_base = 50 + noise
            pixels[x, y] = (
                max(0, min(255, r_base)),
                max(0, min(255, g_base)),
                max(0, min(255, b_base)),
                255,
            )
    return Texture(img)

def make_window_texture():
    """Texture de vitre avec reflets."""
    size = 64
    img = Image.new('RGBA', (size, size), (170, 210, 240, 255))
    pixels = img.load()
    frame = 4
    cross_w = 2
    mid = size // 2
    for x in range(size):
        for y in range(size):
            noise = random.randint(-4, 4)
            # Cadre en bois
            if x < frame or x >= size - frame or y < frame or y >= size - frame:
                pixels[x, y] = (90 + noise, 60 + noise, 35 + noise, 255)
            # Croisillon
            elif abs(x - mid) < cross_w or abs(y - mid) < cross_w:
                pixels[x, y] = (95 + noise, 65 + noise, 38 + noise, 255)
            else:
                # Vitre avec reflet diagonal
                refl = int(math.sin((x + y) * 0.15) * 18)
                pixels[x, y] = (
                    max(0, min(255, 170 + noise + refl)),
                    max(0, min(255, 210 + noise + refl)),
                    max(0, min(255, 240 + noise + refl)),
                    255,
                )
    return Texture(img)

# Création des textures
print("Génération des textures procédurales...")
tex_grass  = make_grass_texture()
tex_sand   = make_sand_texture()
tex_bark   = make_bark_texture()
tex_leaves = make_leaves_texture()
tex_stone  = make_stone_texture()
tex_brick  = make_brick_texture()
tex_roof   = make_roof_texture()
tex_metal  = make_metal_texture()
tex_water  = make_water_texture()
tex_glass  = make_glass_texture()
tex_can    = make_can_texture()
tex_cardboard = make_cardboard_texture()
tex_plastic = make_plastic_texture()
tex_rubber = make_rubber_texture()
tex_barrel = make_barrel_texture()
tex_wood_floor = make_wood_floor_texture()
tex_door = make_door_texture()
tex_window = make_window_texture()

# ============================================================
# Éclairage et environnement
# ============================================================
sun = DirectionalLight()
sun.look_at(Vec3(1, -1, -1))
sun.color = color.rgb(255, 244, 214)

ambient = AmbientLight(color=color.rgb(100, 100, 120))

# Ciel – sphère avec texture procédurale (gradient + nuages)
def make_sky_texture():
    """Texture de ciel avec gradient et nuages statiques."""
    w_sky, h_sky = 512, 256
    img = Image.new('RGBA', (w_sky, h_sky), (135, 195, 250, 255))
    pixels = img.load()
    for y in range(h_sky):
        t = y / h_sky  # 0 = haut, 1 = bas (horizon)
        # Gradient: bleu foncé en haut → bleu clair en bas
        r = int(50 + 140 * t)
        g = int(120 + 110 * t)
        b = int(220 + 35 * (1 - t))
        for x in range(w_sky):
            pr, pg, pb = r, g, b
            # Nuages procéduraux (somme de sinus multi-fréquence)
            cx = x / w_sky * math.pi * 2
            cy = y / h_sky * math.pi
            cloud = (
                math.sin(cx * 3 + 0.5) * math.cos(cy * 2 + 1.0) * 0.35
                + math.sin(cx * 7 + 2.0) * math.cos(cy * 5 - 0.8) * 0.2
                + math.sin(cx * 5 - 1.5) * math.sin(cy * 3 + 2.0) * 0.25
                + math.cos(cx * 11 + 3.0) * math.sin(cy * 4 + 1.5) * 0.12
                + math.sin(cx * 2 + cy * 1.5) * 0.18
            )
            # Nuages uniquement dans la moitié supérieure du ciel
            cloud_zone = max(0.0, 1.0 - t * 1.8)
            cloud_val = max(0.0, cloud) * cloud_zone
            if cloud_val > 0.15:
                blend = min(1.0, (cloud_val - 0.15) * 3.5)
                pr = int(pr + (255 - pr) * blend)
                pg = int(pg + (255 - pg) * blend)
                pb = int(pb + (255 - pb) * blend * 0.95)
            # Petit bruit
            n = random.randint(-3, 3)
            pixels[x, y] = (
                max(0, min(255, pr + n)),
                max(0, min(255, pg + n)),
                max(0, min(255, pb + n)),
                255,
            )
    return Texture(img)

tex_sky = make_sky_texture()
sky_entity = Entity(
    model='sphere',
    scale=(-500, 500, -500),
    texture=tex_sky,
    color=color.white,
    unlit=True,
)

scene.fog_color = color.rgb(160, 190, 220)
scene.fog_density = 0.006

# ============================================================
# Terrain – île et eau
# ============================================================
ground = Entity(
    model='plane',
    scale=(ISLAND_SIZE, 1, ISLAND_SIZE),
    texture=tex_grass,
    texture_scale=(ISLAND_SIZE // 4, ISLAND_SIZE // 4),
    color=color.white,
    collider='box',
    position=(0, 0, 0),
)

beach = Entity(
    model='plane',
    scale=(ISLAND_SIZE + 10, 1, ISLAND_SIZE + 10),
    texture=tex_sand,
    texture_scale=(ISLAND_SIZE // 4, ISLAND_SIZE // 4),
    color=color.white,
    collider='box',
    position=(0, -0.05, 0),
)

water = Entity(
    model='plane',
    scale=(WATER_SIZE, 1, WATER_SIZE),
    texture=tex_water,
    texture_scale=(WATER_SIZE // 8, WATER_SIZE // 8),
    color=color.rgba(30, 100, 180, 180),
    position=(0, -0.3, 0),
)

water_time = [0.0]
def update_water():
    water_time[0] += time.dt
    water.y = -0.3 + math.sin(water_time[0] * 0.5) * 0.1

# ============================================================
# Helpers
# ============================================================
def random_island_pos(margin=5):
    half = ISLAND_SIZE / 2 - margin
    return (random.uniform(-half, half), random.uniform(-half, half))

def distance_2d(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

# ============================================================
# Maisons
# ============================================================
houses = []
HOUSE_POSITIONS = [
    (-15, -10), (-15, -5), (-10, -10),
    (20, 15), (25, 15), (20, 20),
]

for i, (hx, hz) in enumerate(HOUSE_POSITIONS):
    h = random.uniform(3, 5)
    w = random.uniform(4, 6)
    d = random.uniform(4, 6)
    wt = 0.15  # épaisseur des murs

    # --- 4 murs fins (creux à l'intérieur) ---
    # Mur arrière
    Entity(
        model='cube', scale=(w, h, wt), position=(hx, h / 2, hz - d / 2 + wt / 2),
        texture=tex_brick, texture_scale=(2, 2), color=color.white, collider='box',
    )
    # Mur gauche
    Entity(
        model='cube', scale=(wt, h, d), position=(hx - w / 2 + wt / 2, h / 2, hz),
        texture=tex_brick, texture_scale=(2, 2), color=color.white, collider='box',
    )
    # Mur droit
    Entity(
        model='cube', scale=(wt, h, d), position=(hx + w / 2 - wt / 2, h / 2, hz),
        texture=tex_brick, texture_scale=(2, 2), color=color.white, collider='box',
    )
    # Mur avant — partie gauche
    front_side_w = (w - 1.2) / 2
    Entity(
        model='cube', scale=(front_side_w, h, wt),
        position=(hx - w / 2 + front_side_w / 2, h / 2, hz + d / 2 - wt / 2),
        texture=tex_brick, texture_scale=(1, 2), color=color.white, collider='box',
    )
    # Mur avant — partie droite
    Entity(
        model='cube', scale=(front_side_w, h, wt),
        position=(hx + w / 2 - front_side_w / 2, h / 2, hz + d / 2 - wt / 2),
        texture=tex_brick, texture_scale=(1, 2), color=color.white, collider='box',
    )
    # Mur avant — au-dessus de la porte
    Entity(
        model='cube', scale=(1.2, h - 2.2, wt),
        position=(hx, 2.2 + (h - 2.2) / 2, hz + d / 2 - wt / 2),
        texture=tex_brick, texture_scale=(0.5, 1), color=color.white, collider='box',
    )

    # --- Sol intérieur (plancher bois) ---
    Entity(
        model='cube', scale=(w - wt * 2, 0.08, d - wt * 2),
        position=(hx, 0.04, hz),
        texture=tex_wood_floor, texture_scale=(2, 2), color=color.white,
    )

    # --- Toit ---
    Entity(
        model='cube', scale=(w + 0.5, 0.5, d + 0.5), position=(hx, h + 0.25, hz),
        texture=tex_roof, texture_scale=(2, 1), color=color.white,
    )

    # --- Porte ---
    Entity(
        model='cube', scale=(1.1, 2.1, 0.06), position=(hx, 1.05, hz + d / 2 + 0.03),
        texture=tex_door, texture_scale=(1, 1), color=color.white,
    )

    # --- Fenêtres ---
    for side in [-1, 1]:
        Entity(
            model='cube', scale=(0.06, 1, 1),
            position=(hx + (w / 2 + 0.03) * side, h / 2, hz),
            texture=tex_window, texture_scale=(1, 1), color=color.white,
        )

    # --- Mobilier intérieur ---
    # Table
    Entity(
        model='cube', scale=(1.0, 0.06, 0.6),
        position=(hx - w * 0.15, 0.78, hz - d * 0.15),
        color=color.rgb(139, 90, 43),
    )
    Entity(
        model='cube', scale=(0.12, 0.75, 0.12),
        position=(hx - w * 0.15, 0.375, hz - d * 0.15),
        color=color.rgb(120, 75, 35),
    )
    # Chaises
    for cx_off in [-0.55, 0.55]:
        Entity(
            model='cube', scale=(0.32, 0.45, 0.32),
            position=(hx - w * 0.15 + cx_off, 0.225, hz - d * 0.15),
            color=color.rgb(110, 70, 30),
        )
        Entity(
            model='cube', scale=(0.32, 0.4, 0.06),
            position=(hx - w * 0.15 + cx_off, 0.65, hz - d * 0.15 - 0.15),
            color=color.rgb(110, 70, 30),
        )
    # Lit
    Entity(
        model='cube', scale=(1.6, 0.35, 0.85),
        position=(hx + w * 0.2, 0.175, hz + d * 0.2),
        color=color.rgb(180, 140, 110),
    )
    # Couverture
    Entity(
        model='cube', scale=(1.5, 0.06, 0.8),
        position=(hx + w * 0.2, 0.38, hz + d * 0.2),
        color=color.rgb(100, 60, 60),
    )
    # Oreiller
    Entity(
        model='cube', scale=(0.35, 0.1, 0.25),
        position=(hx + w * 0.2 + 0.55, 0.42, hz + d * 0.2),
        color=color.rgb(230, 230, 230),
    )

    houses.append(Entity(visible=False))  # placeholder pour la liste

# ============================================================
# Usine (bâtiment creux avec intérieur)
# ============================================================
factory_pos = (0, 0, 25)
fw, fh, fd = 18, 8, 12  # largeur, hauteur, profondeur
fx, fz = factory_pos[0], factory_pos[2]
fwt = 0.15  # épaisseur des murs

# --- Murs extérieurs creux ---
# Mur arrière
Entity(model='cube', scale=(fw, fh, fwt), position=(fx, fh/2, fz + fd/2 - fwt/2),
       texture=tex_brick, texture_scale=(8, 4), color=color.white, collider='box')
# Mur gauche
Entity(model='cube', scale=(fwt, fh, fd), position=(fx - fw/2 + fwt/2, fh/2, fz),
       texture=tex_brick, texture_scale=(5, 4), color=color.white, collider='box')
# Mur droit
Entity(model='cube', scale=(fwt, fh, fd), position=(fx + fw/2 - fwt/2, fh/2, fz),
       texture=tex_brick, texture_scale=(5, 4), color=color.white, collider='box')
# Mur avant — partie gauche
f_front_side = (fw - 4.0) / 2
Entity(model='cube', scale=(f_front_side, fh, fwt),
       position=(fx - fw/2 + f_front_side/2, fh/2, fz - fd/2 + fwt/2),
       texture=tex_brick, texture_scale=(3, 4), color=color.white, collider='box')
# Mur avant — partie droite
Entity(model='cube', scale=(f_front_side, fh, fwt),
       position=(fx + fw/2 - f_front_side/2, fh/2, fz - fd/2 + fwt/2),
       texture=tex_brick, texture_scale=(3, 4), color=color.white, collider='box')
# Au-dessus de la porte
Entity(model='cube', scale=(4.0, fh - 4.5, fwt),
       position=(fx, 4.5 + (fh - 4.5)/2, fz - fd/2 + fwt/2),
       texture=tex_brick, texture_scale=(2, 2), color=color.white, collider='box')
# Toit
Entity(model='cube', scale=(fw + 0.3, 0.2, fd + 0.3), position=(fx, fh + 0.1, fz),
       texture=tex_metal, texture_scale=(4, 3), color=color.white, collider='box')
# Sol intérieur (béton gris texturé)
Entity(model='cube', scale=(fw - fwt*2, 0.08, fd - fwt*2), position=(fx, 0.04, fz),
       texture=tex_stone, texture_scale=(4, 3), color=color.white)
# Porte
Entity(model='cube', scale=(3.8, 4.4, 0.06), position=(fx, 2.2, fz - fd/2 - 0.03),
       texture=tex_door, texture_scale=(1, 1), color=color.white)
# Cheminée
Entity(model=Cylinder(), scale=(1.2, 6, 1.2), position=(fx + 6, 10, fz + 3),
       texture=tex_metal, texture_scale=(1, 2), color=color.white, collider='box')

# --- Intérieur de l'usine ---

# == TABLE DE TRAVAIL (côté gauche) ==
Entity(model='cube', scale=(4.0, 0.1, 2.0), position=(fx - 5.5, 1.0, fz + 3.0),
       texture=tex_wood_floor, texture_scale=(2, 1), color=color.white)
# Pieds de la table
for tx_off, tz_off in [(-1.8, -0.8), (1.8, -0.8), (-1.8, 0.8), (1.8, 0.8)]:
    Entity(model='cube', scale=(0.12, 1.0, 0.12),
           position=(fx - 5.5 + tx_off, 0.5, fz + 3.0 + tz_off),
           texture=tex_wood_floor, texture_scale=(1, 1), color=color.white)
# Objets sur la table
Entity(model='cube', scale=(0.4, 0.2, 0.3), position=(fx - 6.2, 1.15, fz + 3.0),
       texture=tex_metal, texture_scale=(1, 1), color=color.white)  # outil
Entity(model='cube', scale=(0.6, 0.1, 0.5), position=(fx - 5.0, 1.1, fz + 2.8),
       texture=tex_cardboard, texture_scale=(1, 1), color=color.white)  # papiers
Entity(model=Cylinder(), scale=(0.12, 0.25, 0.12), position=(fx - 4.5, 1.2, fz + 3.3),
       texture=tex_can, texture_scale=(1, 1), color=color.white)  # canette

# Étagère au mur gauche
Entity(model='cube', scale=(3.0, 0.08, 0.6), position=(fx - 8.7, 2.5, fz + 2.0),
       texture=tex_wood_floor, texture_scale=(2, 1), color=color.white)
Entity(model='cube', scale=(3.0, 0.08, 0.6), position=(fx - 8.7, 3.5, fz + 2.0),
       texture=tex_wood_floor, texture_scale=(2, 1), color=color.white)
# Boîtes sur étagères
for shelf_y, offsets in [(2.58, [-0.8, 0.2, 1.0]), (3.58, [-0.5, 0.6])]:
    for bx_off in offsets:
        Entity(model='cube', scale=(0.5, 0.4, 0.4),
               position=(fx - 8.7 + bx_off, shelf_y + 0.2, fz + 2.0),
               texture=tex_cardboard, texture_scale=(1, 1), color=color.white)

# == ПЕЧКА / FOUR (côté droit-arrière — pour le carton) ==
furnace_pos = Vec3(fx + 5.5, 0, fz + 3.5)
# Dimensions internes: largeur=2.5, hauteur=2.8, profondeur=2.0
f_fw, f_fh, f_fd = 2.5, 2.8, 2.0
f_wt = 0.12  # épaisseur des parois
# Mur arrière
Entity(model='cube', scale=(f_fw, f_fh, f_wt),
       position=(furnace_pos.x, f_fh/2, furnace_pos.z + f_fd/2 - f_wt/2),
       texture=tex_brick, texture_scale=(2, 2), color=color.rgb(255, 220, 200), collider='box')
# Mur gauche
Entity(model='cube', scale=(f_wt, f_fh, f_fd),
       position=(furnace_pos.x - f_fw/2 + f_wt/2, f_fh/2, furnace_pos.z),
       texture=tex_brick, texture_scale=(1, 2), color=color.rgb(255, 220, 200), collider='box')
# Mur droit
Entity(model='cube', scale=(f_wt, f_fh, f_fd),
       position=(furnace_pos.x + f_fw/2 - f_wt/2, f_fh/2, furnace_pos.z),
       texture=tex_brick, texture_scale=(1, 2), color=color.rgb(255, 220, 200), collider='box')
# Mur avant — deux côtés autour de l'ouverture
f_door_w = 1.0
f_side_w = (f_fw - f_door_w) / 2
Entity(model='cube', scale=(f_side_w, f_fh, f_wt),
       position=(furnace_pos.x - f_fw/2 + f_side_w/2, f_fh/2, furnace_pos.z - f_fd/2 + f_wt/2),
       texture=tex_brick, texture_scale=(1, 2), color=color.rgb(255, 220, 200), collider='box')
Entity(model='cube', scale=(f_side_w, f_fh, f_wt),
       position=(furnace_pos.x + f_fw/2 - f_side_w/2, f_fh/2, furnace_pos.z - f_fd/2 + f_wt/2),
       texture=tex_brick, texture_scale=(1, 2), color=color.rgb(255, 220, 200), collider='box')
# Au-dessus de l'ouverture
Entity(model='cube', scale=(f_door_w, f_fh - 1.5, f_wt),
       position=(furnace_pos.x, 1.5 + (f_fh - 1.5)/2, furnace_pos.z - f_fd/2 + f_wt/2),
       texture=tex_brick, texture_scale=(1, 1), color=color.rgb(255, 220, 200), collider='box')
# Toit du four
Entity(model='cube', scale=(f_fw, f_wt, f_fd),
       position=(furnace_pos.x, f_fh, furnace_pos.z),
       texture=tex_metal, texture_scale=(2, 1), color=color.rgb(80, 75, 70), collider='box')
# Sol intérieur (briques rougeoyantes)
Entity(model='cube', scale=(f_fw - f_wt*2, 0.06, f_fd - f_wt*2),
       position=(furnace_pos.x, 0.03, furnace_pos.z),
       texture=tex_brick, texture_scale=(1, 1), color=color.rgb(255, 180, 120))
# Grille de la porte — barreaux verticaux (fer forgé)
for gx in range(6):
    Entity(model='cube', scale=(0.06, 1.5, 0.08),
           position=(furnace_pos.x - 0.4 + gx * 0.16, 0.75, furnace_pos.z - f_fd/2 + 0.02),
           texture=tex_metal, texture_scale=(1, 3), color=color.white)
# Grille de la porte — traverses horizontales
for gy in range(3):
    Entity(model='cube', scale=(0.9, 0.06, 0.08),
           position=(furnace_pos.x, 0.25 + gy * 0.5, furnace_pos.z - f_fd/2 + 0.02),
           texture=tex_metal, texture_scale=(3, 1), color=color.white)
# Cheminée du four
Entity(model=Cylinder(), scale=(0.4, 3.0, 0.4),
       position=(furnace_pos.x + 0.7, 4.0, furnace_pos.z + 0.5),
       texture=tex_metal, texture_scale=(1, 1), color=color.white)
# Base en brique
Entity(model='cube', scale=(2.7, 0.3, 2.2), position=(furnace_pos.x, 0.15, furnace_pos.z),
       texture=tex_brick, texture_scale=(2, 1), color=color.white)
# Indicateur lumineux
furnace_light = Entity(model='cube', scale=(0.2, 0.2, 0.08),
       position=(furnace_pos.x + 0.9, 2.2, furnace_pos.z - f_fd/2 - 0.02),
       color=color.rgb(255, 80, 30), unlit=True)
furnace_label = Text(text='', position=(0, -0.25), origin=(0, 0), scale=1.3,
                     color=color.orange)
# Список визуальных предметов внутри печи
furnace_inside_items = []

# == MACHINE DE RECYCLAGE (au centre — pour tout sauf carton) ==
recycler_pos = Vec3(fx + 1.5, 0, fz - 2.0)
# Dimensions internes: largeur=3.0, hauteur=3.5, profondeur=2.5
r_fw, r_fh, r_fd = 3.0, 3.5, 2.5
r_wt = 0.12  # épaisseur des parois
# Mur arrière
Entity(model='cube', scale=(r_fw, r_fh, r_wt),
       position=(recycler_pos.x, r_fh/2, recycler_pos.z + r_fd/2 - r_wt/2),
       texture=tex_metal, texture_scale=(2, 2), color=color.white, collider='box')
# Mur gauche
Entity(model='cube', scale=(r_wt, r_fh, r_fd),
       position=(recycler_pos.x - r_fw/2 + r_wt/2, r_fh/2, recycler_pos.z),
       texture=tex_metal, texture_scale=(1, 2), color=color.white, collider='box')
# Mur droit
Entity(model='cube', scale=(r_wt, r_fh, r_fd),
       position=(recycler_pos.x + r_fw/2 - r_wt/2, r_fh/2, recycler_pos.z),
       texture=tex_metal, texture_scale=(1, 2), color=color.white, collider='box')
# Mur avant — только нижняя и верхняя части (середина открыта)
r_open_h = 1.6  # высота проёма
r_open_bottom = 0.5
# Нижняя панель (под проёмом)
Entity(model='cube', scale=(r_fw, r_open_bottom, r_wt),
       position=(recycler_pos.x, r_open_bottom/2, recycler_pos.z - r_fd/2 + r_wt/2),
       texture=tex_metal, texture_scale=(2, 1), color=color.white, collider='box')
# Верхняя панель (над проёмом)
r_top_h = r_fh - r_open_bottom - r_open_h
Entity(model='cube', scale=(r_fw, r_top_h, r_wt),
       position=(recycler_pos.x, r_open_bottom + r_open_h + r_top_h/2, recycler_pos.z - r_fd/2 + r_wt/2),
       texture=tex_metal, texture_scale=(2, 1), color=color.white, collider='box')
# Боковые стойки проёма
for side_x in [-1, 1]:
    Entity(model='cube', scale=(0.15, r_open_h, r_wt),
           position=(recycler_pos.x + side_x * (r_fw/2 - 0.075), r_open_bottom + r_open_h/2,
                     recycler_pos.z - r_fd/2 + r_wt/2),
           texture=tex_metal, texture_scale=(1, 1), color=color.white, collider='box')
# Toit
Entity(model='cube', scale=(r_fw, r_wt, r_fd),
       position=(recycler_pos.x, r_fh, recycler_pos.z),
       texture=tex_metal, texture_scale=(2, 1), color=color.white, collider='box')
# Sol intérieur
Entity(model='cube', scale=(r_fw - r_wt*2, 0.06, r_fd - r_wt*2),
       position=(recycler_pos.x, 0.03, recycler_pos.z),
       texture=tex_stone, texture_scale=(1, 1), color=color.white)
# Trémie d'alimentation (haut)
Entity(model='cube', scale=(1.5, 0.6, 1.2),
       position=(recycler_pos.x, r_fh + 0.3, recycler_pos.z),
       texture=tex_metal, texture_scale=(1, 1), color=color.white)
# Ouverture trémie
Entity(model='cube', scale=(1.0, 0.12, 0.8),
       position=(recycler_pos.x, r_fh + 0.64, recycler_pos.z),
       color=color.rgb(30, 30, 30))
# Panneau de contrôle (face avant — au-dessus du proём)
Entity(model='cube', scale=(1.4, 0.8, 0.08),
       position=(recycler_pos.x, r_open_bottom + r_open_h + r_top_h * 0.4,
                 recycler_pos.z - r_fd/2 - 0.02),
       texture=tex_metal, texture_scale=(1, 1), color=color.white)
# Boutons
btn_y = r_open_bottom + r_open_h + r_top_h * 0.55
for bx_off, bc in [(-0.35, color.rgb(50, 200, 50)),
                    (0.35, color.rgb(200, 50, 50))]:
    Entity(model='cube', scale=(0.2, 0.2, 0.1),
           position=(recycler_pos.x + bx_off, btn_y, recycler_pos.z - r_fd/2 - 0.04),
           color=bc, unlit=True)
# Écran indicateur
Entity(model='cube', scale=(0.7, 0.4, 0.08),
       position=(recycler_pos.x, r_open_bottom + r_open_h + r_top_h * 0.2,
                 recycler_pos.z - r_fd/2 - 0.04),
       color=color.rgb(20, 60, 20), unlit=True)
# Bande de sortie (bas)
Entity(model='cube', scale=(0.8, 0.3, 1.5),
       position=(recycler_pos.x + 1.8, 0.3, recycler_pos.z),
       texture=tex_rubber, texture_scale=(1, 2), color=color.white)
# Indicateur lumineux
recycler_light = Entity(model='cube', scale=(0.2, 0.2, 0.08),
       position=(recycler_pos.x - 1.0, r_fh - 0.3, recycler_pos.z - r_fd/2 - 0.02),
       color=color.rgb(50, 200, 50), unlit=True)
recycler_label = Text(text='', position=(0, -0.25), origin=(0, 0), scale=1.3,
                      color=color.green)
# Список визуальных предметов внутри машины
recycler_inside_items = []

# Tuyaux le long du mur arrière
for pipe_x in [fx - 6, fx - 3, fx + 7]:
    Entity(model=Cylinder(), scale=(0.2, fh - 0.5, 0.2),
           position=(pipe_x, fh/2, fz + fd/2 - 0.5),
           texture=tex_metal, texture_scale=(1, 2), color=color.white)

# Distances d'interaction avec les machines
MACHINE_RANGE = 4.0

# Inventaire du joueur
inventory = []  # liste de {'name': ..., 'points': ...}
MAX_INVENTORY = 5

# ============================================================
# Arbres
# ============================================================
tree_positions = []
for _ in range(TREE_COUNT):
    attempts = 0
    while attempts < 50:
        tx, tz = random_island_pos(margin=3)
        too_close = False
        for hx, hz in HOUSE_POSITIONS:
            if distance_2d((tx, tz), (hx, hz)) < 8:
                too_close = True
                break
        if distance_2d((tx, tz), (factory_pos[0], factory_pos[2])) < 16:
            too_close = True
        if not too_close:
            break
        attempts += 1
    else:
        continue

    tree_positions.append((tx, tz))
    trunk_h = random.uniform(3, 6)
    trunk_r = random.uniform(0.2, 0.4)

    # Cylinder: vertices y=0..1, origin at base. scale.y = height, position.y = 0
    # Tronc blanc style bouleau
    Entity(
        model=Cylinder(), scale=(trunk_r, trunk_h, trunk_r),
        position=(tx, -0.1, tz), texture=tex_bark,
        color=color.white, collider='box',
    )

    # Cone: vertices y=-0.5..0.5, origin at center
    for level in range(3):
        cone_h = 1.5
        cone_y = trunk_h * 0.5 + level * 1.2 + cone_h / 2
        cone_scale = (2.5 - level * 0.6)
        Entity(
            model=Cone(), scale=(cone_scale, 1.5, cone_scale),
            position=(tx, cone_y, tz), texture=tex_leaves,
            color=color.white,
        )

# ============================================================
# Rochers
# ============================================================
for _ in range(ROCK_COUNT):
    rx, rz = random_island_pos(margin=2)
    scale_factor = random.uniform(0.5, 2.0)
    # Rocher principal (cube aplati et tourné)
    Entity(
        model='cube',
        scale=(
            scale_factor * random.uniform(0.8, 1.4),
            scale_factor * random.uniform(0.4, 0.7),
            scale_factor * random.uniform(0.8, 1.4),
        ),
        position=(rx, scale_factor * 0.2, rz),
        rotation=(random.uniform(-15, 15), random.uniform(0, 360), random.uniform(-10, 10)),
        texture=tex_stone,
        texture_scale=(2, 2),
        color=color.white,
        collider='box',
    )
    # Deuxième bloc superposé pour effet anguleux
    Entity(
        model='cube',
        scale=(
            scale_factor * random.uniform(0.5, 0.9),
            scale_factor * random.uniform(0.3, 0.6),
            scale_factor * random.uniform(0.5, 0.9),
        ),
        position=(rx + random.uniform(-0.2, 0.2), scale_factor * 0.45, rz + random.uniform(-0.2, 0.2)),
        rotation=(random.uniform(-25, 25), random.uniform(0, 360), random.uniform(-20, 20)),
        texture=tex_stone,
        texture_scale=(2, 2),
        color=color.white,
    )
    # Troisième petit bloc pour détail
    if random.random() > 0.4:
        Entity(
            model='cube',
            scale=(
                scale_factor * random.uniform(0.3, 0.5),
                scale_factor * random.uniform(0.2, 0.4),
                scale_factor * random.uniform(0.3, 0.5),
            ),
            position=(rx + random.uniform(-0.3, 0.3), scale_factor * 0.6, rz + random.uniform(-0.3, 0.3)),
            rotation=(random.uniform(-30, 30), random.uniform(0, 360), random.uniform(-25, 25)),
            texture=tex_stone,
            texture_scale=(2, 2),
            color=color.white,
        )

# ============================================================
# Déchets (objets à ramasser)
# ============================================================
trash_items = []

TRASH_TYPES = [
    {'name': 'Bouteille', 'model': Cylinder, 'scale': (0.15, 0.4, 0.15),
     'color': color.white, 'points': 10, 'texture': 'tex_glass'},
    {'name': 'Canette', 'model': Cylinder, 'scale': (0.12, 0.25, 0.12),
     'color': color.white, 'points': 10, 'texture': 'tex_can'},
    {'name': 'Sac plastique', 'model': 'cube', 'scale': (0.4, 0.05, 0.3),
     'color': color.white, 'points': 5, 'texture': 'tex_plastic'},
    {'name': 'Pneu', 'model': 'sphere', 'scale': (0.5, 0.25, 0.5),
     'color': color.white, 'points': 25, 'texture': 'tex_rubber'},
    {'name': 'Carton', 'model': 'cube', 'scale': (0.5, 0.3, 0.4),
     'color': color.white, 'points': 5, 'texture': 'tex_cardboard'},
    {'name': 'Bidon', 'model': Cylinder, 'scale': (0.25, 0.5, 0.25),
     'color': color.white, 'points': 15, 'texture': 'tex_barrel'},
]

for i in range(TRASH_COUNT):
    tx, tz = random_island_pos(margin=2)
    trash_type = random.choice(TRASH_TYPES)

    # R\u00e9soudre la texture par nom
    tex_map = {
        'tex_glass': tex_glass, 'tex_can': tex_can, 'tex_plastic': tex_plastic,
        'tex_rubber': tex_rubber, 'tex_cardboard': tex_cardboard, 'tex_barrel': tex_barrel,
    }
    model_val = trash_type['model']() if callable(trash_type['model']) else trash_type['model']
    trash_entity = Entity(
        model=model_val,
        scale=trash_type['scale'],
        position=(tx, trash_type['scale'][1] / 2 + 0.01, tz),
        color=trash_type['color'],
        texture=tex_map.get(trash_type.get('texture')),
        collider='box',
    )
    trash_entity.trash_name = trash_type['name']
    trash_entity.trash_points = trash_type['points']
    trash_entity.original_y = trash_entity.y

    indicator = Entity(
        model='sphere', scale=0.15,
        position=(tx, trash_type['scale'][1] + 0.8, tz),
        color=color.rgb(255, 255, 100), unlit=True,
    )
    trash_entity.indicator = indicator
    trash_items.append(trash_entity)

# ============================================================
# Joueur (First Person Controller)
# ============================================================
player = FirstPersonController(
    position=(0, 2, -30),
    speed=8,
    jump_height=2,
    mouse_sensitivity=Vec2(80, 80),
)
player.cursor.visible = False

# ============================================================
# Interface (HUD)
# ============================================================
score = [0]
total_points = sum(t.trash_points for t in trash_items)
trash_remaining = [len(trash_items)]

score_text = Text(
    text=f'Déchets: 0/{TRASH_COUNT}  |  Score: 0  |  Inventaire: 0/{MAX_INVENTORY}',
    position=(-0.85, 0.47), scale=1.1, color=color.white,
    background=True,
)

action_text = Text(
    text='', position=(0, -0.3), origin=(0, 0), scale=1.5, color=color.yellow,
)

win_text = Text(
    text='', position=(0, 0.1), origin=(0, 0), scale=3, color=color.green,
)

crosshair = Entity(
    parent=camera.ui, model='quad', scale=0.008, color=color.white, position=(0, 0),
)

minimap_bg = Entity(
    parent=camera.ui, model='quad', scale=(0.2, 0.2),
    position=(0.7, 0.35), color=color.rgba(0, 0, 0, 100),
)
minimap_player_dot = Entity(
    parent=camera.ui, model='circle', scale=0.01,
    position=(0.7, 0.35), color=color.red, z=-0.1,
)

instructions_text = Text(
    text='ZQSD: Bouger | Souris: Regarder | E: Ramasser/Déposer | Échap: Quitter',
    position=(0, -0.4), origin=(0, 0), scale=0.9, color=color.rgb(200, 200, 200),
    background=True,
)

# ============================================================
# Clôture de l'île
# ============================================================
fence_height = 1.5
half_island = ISLAND_SIZE / 2
for i in range(int(ISLAND_SIZE)):
    x = -half_island + i + 0.5
    for z_sign in [-1, 1]:
        Entity(
            model='cube', scale=(1, fence_height, 0.15),
            position=(x, fence_height / 2, half_island * z_sign),
            color=color.rgb(139, 90, 43),
        )
    for x_sign in [-1, 1]:
        Entity(
            model='cube', scale=(0.15, fence_height, 1),
            position=(half_island * x_sign, fence_height / 2, x),
            color=color.rgb(139, 90, 43),
        )

# ============================================================
# Pont en bois
# ============================================================
bridge = Entity(
    model='cube', scale=(4, 0.3, 12),
    position=(-half_island - 2, 0.15, 0),
    color=color.rgb(160, 120, 80), texture=tex_bark, collider='box',
)
for side in [-1, 1]:
    Entity(
        model='cube', scale=(0.2, 1.2, 12),
        position=(-half_island - 2 + side * 1.8, 0.6, 0),
        color=color.rgb(139, 90, 43),
    )

# ============================================================
# Voitures (décor)
# ============================================================
car_positions = [(10, -20), (-25, 5), (30, -5)]
car_colors = [color.rgb(200, 50, 50), color.rgb(50, 50, 200), color.rgb(220, 180, 30)]

for (cx, cz), ccolor in zip(car_positions, car_colors):
    Entity(
        model='cube', scale=(2, 1, 4), position=(cx, 0.7, cz),
        color=ccolor, collider='box',
    )
    Entity(
        model='cube', scale=(1.8, 0.8, 2), position=(cx, 1.6, cz),
        color=ccolor * 0.85,
    )
    for wx in [-1, 1]:
        for wz in [-1.2, 1.2]:
            Entity(
                model=Cylinder(), scale=(0.4, 0.15, 0.4),
                position=(cx + wx * 1.1, 0.3, cz + wz),
                rotation=(0, 0, 90), color=color.rgb(30, 30, 30),
            )

# ============================================================
# Logique de jeu
# ============================================================
game_won = [False]
closest_trash = [None]
anim_time = [0.0]
near_furnace = [False]
near_recycler = [False]
processed_count = [0]  # nombre de déchets traités dans les machines

def _update_hud():
    collected = TRASH_COUNT - trash_remaining[0]
    score_text.text = (f'Déchets: {collected}/{TRASH_COUNT}  |  '
                       f'Score: {score[0]}/{total_points}  |  '
                       f'Inventaire: {len(inventory)}/{MAX_INVENTORY}')

def update():
    """Boucle principale – appelée chaque frame par Ursina."""
    anim_time[0] += time.dt
    update_water()

    if anim_time[0] > 10:
        instructions_text.visible = False

    if player.y < -5:
        player.position = Vec3(0, 2, -30)

    border = half_island + 6
    player.x = max(-border, min(border, player.x))
    player.z = max(-border, min(border, player.z))

    if game_won[0]:
        return

    best_dist = PICKUP_RANGE + 1
    best_trash = None
    player_pos_2d = (player.x, player.z)

    for trash in trash_items:
        d = distance_2d(player_pos_2d, (trash.x, trash.z))
        trash.y = trash.original_y + math.sin(anim_time[0] * 2 + trash.x) * 0.05
        trash.indicator.y = trash.y + 0.7

        if d < PICKUP_RANGE and d < best_dist:
            best_dist = d
            best_trash = trash

    closest_trash[0] = best_trash

    # Vérifier proximité des machines
    d_furnace = distance_2d(player_pos_2d, (furnace_pos.x, furnace_pos.z))
    d_recycler = distance_2d(player_pos_2d, (recycler_pos.x, recycler_pos.z))
    near_furnace[0] = d_furnace < MACHINE_RANGE
    near_recycler[0] = d_recycler < MACHINE_RANGE

    # Lumières des machines
    furnace_light.color = color.rgb(255, 150, 50) if near_furnace[0] else color.rgb(255, 80, 30)
    recycler_light.color = color.rgb(100, 255, 100) if near_recycler[0] else color.rgb(50, 200, 50)

    # Texte d'action
    has_cardboard = any(item['name'] == 'Carton' for item in inventory)
    has_other = any(item['name'] != 'Carton' for item in inventory)

    if best_trash and len(inventory) < MAX_INVENTORY:
        action_text.text = f'[E] Ramasser {best_trash.trash_name}'
        best_trash.indicator.color = color.rgb(50, 255, 50)
        best_trash.indicator.scale = 0.25
    elif best_trash and len(inventory) >= MAX_INVENTORY:
        action_text.text = f'Inventaire plein ! Déposez à l\'usine.'
        best_trash.indicator.color = color.rgb(255, 100, 100)
        best_trash.indicator.scale = 0.2
    elif near_furnace[0] and has_cardboard:
        count_c = sum(1 for i in inventory if i['name'] == 'Carton')
        action_text.text = f'[E] Brûler {count_c} carton(s) dans le four'
    elif near_recycler[0] and has_other:
        count_o = sum(1 for i in inventory if i['name'] != 'Carton')
        action_text.text = f'[E] Recycler {count_o} déchet(s)'
    elif near_furnace[0] and not has_cardboard and inventory:
        action_text.text = 'Le four accepte uniquement le carton'
    elif near_recycler[0] and not has_other and inventory:
        action_text.text = 'Le recycleur accepte tout sauf le carton'
    else:
        action_text.text = ''

    for trash in trash_items:
        if trash != best_trash:
            trash.indicator.color = color.rgb(255, 255, 100)
            trash.indicator.scale = 0.15

    map_scale = 0.2 / ISLAND_SIZE
    minimap_player_dot.x = 0.7 + player.x * map_scale
    minimap_player_dot.y = 0.35 + player.z * map_scale


def input(key):
    """Gestion des entrées."""
    if key == 'escape':
        application.quit()

    if key != 'e' or game_won[0]:
        return

    # 1) Déposer du carton dans le four
    if near_furnace[0] and any(i['name'] == 'Carton' for i in inventory):
        cardboard_items = [i for i in inventory if i['name'] == 'Carton']
        for idx, item in enumerate(cardboard_items):
            score[0] += item['points']
            inventory.remove(item)
            processed_count[0] += 1
            # Créer un carton visible à l'intérieur du four
            cx = furnace_pos.x + random.uniform(-0.5, 0.5)
            cz = furnace_pos.z + random.uniform(-0.4, 0.4)
            cy = 0.35 + idx * 0.32
            vis = Entity(model='cube', scale=(0.45, 0.28, 0.35),
                         position=(cx, cy, cz),
                         texture=tex_cardboard, texture_scale=(1, 1),
                         color=color.white,
                         rotation_y=random.uniform(-30, 30))
            furnace_inside_items.append(vis)
            # Le carton brûle après un délai
            destroy(vis, delay=2.5 + idx * 0.3)
        # Nettoyer la liste après le délai
        invoke(furnace_inside_items.clear, delay=3.5 + len(cardboard_items) * 0.3)
        # Effet visuel
        flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                       color=color.rgba(255, 150, 50, 100), z=-1)
        destroy(flash, delay=0.2)
        _update_hud()
        action_text.text = f'{len(cardboard_items)} carton(s) brûlé(s) !'
        _check_win()
        return

    # 2) Déposer dans le recycleur (tout sauf carton)
    if near_recycler[0] and any(i['name'] != 'Carton' for i in inventory):
        other_items = [i for i in inventory if i['name'] != 'Carton']
        # Карта текстур по имени
        _name_tex = {
            'Bouteille': tex_glass, 'Canette': tex_can,
            'Sac plastique': tex_plastic, 'Pneu': tex_rubber,
            'Bidon': tex_barrel,
        }
        for idx, item in enumerate(other_items):
            score[0] += item['points']
            inventory.remove(item)
            processed_count[0] += 1
            # Créer un objet visible à l'intérieur du recycleur
            rx = recycler_pos.x + random.uniform(-0.6, 0.6)
            rz = recycler_pos.z + random.uniform(-0.5, 0.5)
            ry = 0.35 + idx * 0.3
            vis = Entity(model='cube', scale=(0.35, 0.25, 0.3),
                         position=(rx, ry, rz),
                         texture=_name_tex.get(item['name'], tex_metal),
                         texture_scale=(1, 1), color=color.white,
                         rotation_y=random.uniform(-40, 40))
            recycler_inside_items.append(vis)
            # L'objet disparaît après traitement
            destroy(vis, delay=3.0 + idx * 0.3)
        invoke(recycler_inside_items.clear, delay=4.0 + len(other_items) * 0.3)
        flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                       color=color.rgba(100, 255, 100, 100), z=-1)
        destroy(flash, delay=0.2)
        _update_hud()
        action_text.text = f'{len(other_items)} déchet(s) recyclé(s) !'
        _check_win()
        return

    # 3) Ramasser un déchet du sol
    if closest_trash[0] and len(inventory) < MAX_INVENTORY:
        trash = closest_trash[0]
        inventory.append({'name': trash.trash_name, 'points': trash.trash_points})
        trash_items.remove(trash)
        destroy(trash.indicator)
        destroy(trash)
        trash_remaining[0] -= 1
        closest_trash[0] = None

        flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                       color=color.rgba(255, 255, 200, 80), z=-1)
        destroy(flash, delay=0.15)
        _update_hud()


def _check_win():
    if trash_remaining[0] <= 0 and len(inventory) == 0:
        game_won[0] = True
        win_text.text = 'BRAVO ! Île nettoyée !'
        Text(text=f'Score final: {score[0]} points',
             position=(0, 0), origin=(0, 0), scale=2, color=color.white)


# ============================================================
# Lancement
# ============================================================
print("=== Forest Cleaner 3D – Prototype Ursina ===")
print(f"  {TRASH_COUNT} déchets à ramasser")
print(f"  {TREE_COUNT} arbres, {ROCK_COUNT} rochers")
print("  Contrôles: ZQSD + Souris + E")
print("=============================================")

app.run()
