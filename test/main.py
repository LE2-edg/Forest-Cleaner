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
import os
import textwrap
import time as _time_mod
from pathlib import Path

# ── Auto-install missing packages ──────────────────────────────────────────
def _ensure_package(pip_name, import_name=None):
    """Try importing; if missing, pip-install automatically."""
    import importlib, subprocess
    mod_name = import_name or pip_name
    try:
        return importlib.import_module(mod_name)
    except ImportError:
        print(f"[AUTO] Installing {pip_name}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pip_name],
                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except Exception:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        return importlib.import_module(mod_name)

_ensure_package("ursina")
_ensure_package("pillow", "PIL")

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.models.procedural.cylinder import Cylinder
from ursina.models.procedural.cone import Cone

# ── PIL with fallback ──────────────────────────────────────────────────────
_USE_PIL = True
try:
    from PIL import Image
except Exception:
    _USE_PIL = False
    print("[WARN] Pillow unavailable – using solid-color textures (fast mode)")

# ============================================================
# Configuration
# ============================================================
ISLAND_SIZE = 80          # taille de l'île (unités)
WATER_SIZE = 200          # taille de l'eau autour
TREE_COUNT = 120          # nombre d'arbres
ROCK_COUNT = 40           # nombre de rochers
TRASH_COUNT = 62          # 12 картон + 25 металл + 25 пластик
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
# Suppress "Could not find icon" warning spam from Panda3D
from panda3d.core import WindowProperties
wp = WindowProperties()
wp.clearIconFilename()
base.win.requestProperties(wp)
# Pointer l'asset_folder vers la racine du projet pour que
# les modèles OBJ dans models/ soient trouvés par Ursina.
application.asset_folder = Path(os.path.dirname(os.path.abspath(__file__))).parent

# ============================================================
# Chargement de modèles OBJ personnalisés (Blender)
# ============================================================
# Dossier models/ à la racine du projet
_MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')

def resolve_model(name, fallback):
    """Retourne 'models/<name>' si models/<name>.obj existe, sinon le mesh fallback.
    Permet de remplacer n'importe quel objet par un .OBJ créé dans Blender."""
    if os.path.exists(os.path.join(_MODELS_DIR, name + '.obj')):
        return f'models/{name}'
    return fallback() if callable(fallback) else fallback

# ============================================================
# Textures procédurales (with solid-color fallback)
# ============================================================

def _solid_texture(r, g, b, a=255, size=4):
    """Create a tiny solid-color texture. Works even without PIL using Panda3D."""
    # Method 1: PIL (if available)
    if _USE_PIL:
        try:
            img = Image.new('RGBA', (size, size), (r, g, b, a))
            return Texture(img)
        except Exception:
            pass
    # Method 2: Raw Panda3D bytes (always available with Ursina, matches PIL path)
    try:
        from panda3d.core import Texture as PandaTexture
        ptex = PandaTexture('solid')
        ptex.setup2dTexture(size, size, PandaTexture.TUnsignedByte, PandaTexture.FRgba)
        # Panda3D stores rows bottom-to-top, BGRA order by default with setRamImage
        # Using setRamImageAs with 'RGBA' to match our byte order
        pixel = bytes([r, g, b, a])
        data = pixel * (size * size)
        ptex.setRamImageAs(data, 'RGBA')
        result = Texture(ptex)
        result.path = None
        result._cached_image = None
        return result
    except Exception as exc:
        print(f"[WARN] _solid_texture fallback failed: {exc}")
        return None


def _safe_texture(generator_func, fallback_rgba):
    """Run a PIL texture generator; on any failure return a solid color."""
    if not _USE_PIL:
        return _solid_texture(*fallback_rgba)
    try:
        tex = generator_func()
        if tex is not None:
            return tex
    except Exception as exc:
        print(f"[WARN] Texture '{generator_func.__name__}' failed: {exc}")
    return _solid_texture(*fallback_rgba)

def make_grass_texture():
    """Texture d'herbe procédurale."""
    size = 64
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
    size = 64
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
    size = 64
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
    size = 64
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
    size = 64
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
    size = 64
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
    size = 64
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

def make_red_brick_texture():
    """Texture de briques rouges pour la maison rouge."""
    size = 64
    img = Image.new('RGBA', (size, size), (180, 55, 45, 255))
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
                pixels[x, y] = (160, 150, 140, 255)  # mortier
            else:
                wear = int(math.sin(x * 0.1 + y * 0.2) * 6)
                pixels[x, y] = (
                    max(0, min(255, 180 + noise + wear)),
                    max(0, min(255, 55 + noise // 2 + wear)),
                    max(0, min(255, 45 + noise // 2)),
                    255,
                )
    return Texture(img)

def make_fabric_texture():
    """Texture de tissu — couverture / matelas avec tissage visible."""
    size = 64
    img = Image.new('RGBA', (size, size), (200, 190, 175, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-6, 6)
            # Tissage horizontal + vertical = grille douce
            weave_x = int(math.sin(x * 1.2) * 8)
            weave_y = int(math.sin(y * 1.2) * 8)
            weave = weave_x + weave_y
            # Petits noeuds du tissu
            knot = -12 if (x % 8 == 0 and y % 6 == 0) else 0
            r = max(0, min(255, 200 + noise + weave + knot))
            g = max(0, min(255, 190 + noise + weave + knot))
            b = max(0, min(255, 175 + noise + weave + knot))
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

def make_ceramic_texture():
    """Texture de céramique — surfaces lisses avec léger reflet."""
    size = 64
    img = Image.new('RGBA', (size, size), (240, 238, 232, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-3, 3)
            # Reflet doux diagonal
            gloss = int(math.sin((x + y) * 0.08) * 10)
            # Légère veine grise
            vein = int(math.sin(x * 0.15 + y * 0.05) * 5)
            r = max(0, min(255, 240 + noise + gloss + vein))
            g = max(0, min(255, 238 + noise + gloss + vein))
            b = max(0, min(255, 232 + noise + gloss))
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

def make_dark_wood_texture():
    """Texture de bois foncé — cadre de lit / meubles sombres."""
    size = 64
    img = Image.new('RGBA', (size, size), (85, 55, 30, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-6, 6)
            # Fibres longitudinales prononcées
            grain = int(math.sin(y * 0.6 + math.sin(x * 0.15) * 3) * 12)
            # Noeuds du bois
            knot_dist = math.sqrt((x - 32)**2 + (y - 48)**2)
            knot = int(math.sin(knot_dist * 0.3) * 8) if knot_dist < 15 else 0
            r = max(0, min(255, 85 + noise + grain + knot))
            g = max(0, min(255, 55 + noise + int(grain * 0.7) + knot))
            b = max(0, min(255, 30 + noise + int(grain * 0.3)))
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

def make_cushion_texture():
    """Texture de coussin / oreiller — tissu doux matelassé."""
    size = 64
    img = Image.new('RGBA', (size, size), (220, 215, 230, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-4, 4)
            # Motif matelassé (losanges)
            diamond = math.sin(x * 0.2 + y * 0.2) * math.sin(x * 0.2 - y * 0.2)
            quilt = int(diamond * 15)
            # Coutures
            seam = -18 if abs(math.sin(x * 0.2 + y * 0.2)) < 0.05 or abs(math.sin(x * 0.2 - y * 0.2)) < 0.05 else 0
            r = max(0, min(255, 220 + noise + quilt + seam))
            g = max(0, min(255, 215 + noise + quilt + seam))
            b = max(0, min(255, 230 + noise + quilt + seam))
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

def make_chrome_texture():
    """Texture métallique chromée — robinetterie."""
    size = 32
    img = Image.new('RGBA', (size, size), (190, 195, 200, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-3, 3)
            # Reflets vifs
            refl = int(math.sin((x + y) * 0.3) * 25 + math.cos(x * 0.5) * 15)
            v = max(120, min(255, 195 + noise + refl))
            pixels[x, y] = (v, v + 2, v + 5, 255)
    return Texture(img)

def make_screen_texture():
    """Texture d'écran — surface très sombre avec léger reflet."""
    size = 32
    img = Image.new('RGBA', (size, size), (15, 20, 35, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            # Léger gradient diagonal (reflet d'écran)
            gloss = int(math.sin((x + y) * 0.15) * 8)
            # Pixels LCD subtils
            lcd = 3 if (x % 3 == 0) else 0
            r = max(0, min(50, 15 + gloss))
            g = max(0, min(50, 20 + gloss + lcd))
            b = max(0, min(60, 35 + gloss))
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

def make_roof_texture():
    """Texture de toit avec tuiles."""
    size = 64
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
    size = 64
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

def make_car_paint_texture():
    """Texture de peinture auto rouge, homogène avec légère micro-variation."""
    size = 64
    img = Image.new('RGBA', (size, size), (190, 40, 40, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-6, 6)
            soft = int(math.sin((x + y) * 0.08) * 4)
            r = max(0, min(255, 190 + noise + soft))
            g = max(0, min(255, 40 + noise // 2))
            b = max(0, min(255, 40 + noise // 2))
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

def make_dark_car_paint_texture():
    """Version plus sombre de la peinture homogène (pour les rochers)."""
    size = 64
    img = Image.new('RGBA', (size, size), (95, 95, 95, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-6, 6)
            soft = int(math.sin((x + y) * 0.1) * 4)
            v = max(0, min(255, 95 + noise + soft))
            pixels[x, y] = (v, v, v, 255)
    return Texture(img)

def make_car_glass_texture():
    """Texture de vitre auto (bleutée, sans cadre bois)."""
    size = 64
    img = Image.new('RGBA', (size, size), (150, 190, 235, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-5, 5)
            refl = int(math.sin((x * 0.25) + (y * 0.18)) * 10)
            r = max(0, min(255, 150 + noise + refl))
            g = max(0, min(255, 190 + noise + refl))
            b = max(0, min(255, 235 + noise + refl))
            pixels[x, y] = (r, g, b, 255)
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
    size = 64
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
    size = 32
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

def make_textured_cylinder(resolution=16):
    """Cylinder mesh from y=0 to y=1, radius=0.5, with proper UV coordinates for texture mapping.
    Replaces Ursina's Cylinder() which generates empty UVs and cannot display textures."""
    tau = 2 * math.pi
    verts, tris, uvs = [], [], []
    # Side surface
    for i in range(resolution):
        a0 = tau * i / resolution
        a1 = tau * (i + 1) / resolution
        b = len(verts)
        verts += [
            Vec3(math.cos(a0) * .5, 0, math.sin(a0) * .5),   # BL
            Vec3(math.cos(a1) * .5, 0, math.sin(a1) * .5),   # BR
            Vec3(math.cos(a1) * .5, 1, math.sin(a1) * .5),   # TR
            Vec3(math.cos(a0) * .5, 1, math.sin(a0) * .5),   # TL
        ]
        uvs += [Vec2(i/resolution, 0), Vec2((i+1)/resolution, 0),
                Vec2((i+1)/resolution, 1), Vec2(i/resolution, 1)]
        tris += [b, b+2, b+1,  b, b+3, b+2]
    # Top cap (y=1)
    ct = len(verts)
    verts.append(Vec3(0, 1, 0)); uvs.append(Vec2(0.5, 0.5))
    for i in range(resolution):
        a = tau * i / resolution
        verts.append(Vec3(math.cos(a) * .5, 1, math.sin(a) * .5))
        uvs.append(Vec2(0.5 + math.cos(a) * 0.5, 0.5 + math.sin(a) * 0.5))
    for i in range(resolution):
        tris += [ct, ct + (i + 1) % resolution + 1, ct + i + 1]
    # Bottom cap (y=0)
    cb = len(verts)
    verts.append(Vec3(0, 0, 0)); uvs.append(Vec2(0.5, 0.5))
    for i in range(resolution):
        a = tau * i / resolution
        verts.append(Vec3(math.cos(a) * .5, 0, math.sin(a) * .5))
        uvs.append(Vec2(0.5 + math.cos(a) * 0.5, 0.5 + math.sin(a) * 0.5))
    for i in range(resolution):
        tris += [cb, cb + i + 1, cb + (i + 1) % resolution + 1]
    return Mesh(vertices=verts, triangles=tris, uvs=uvs)

# ── Tinted texture variant generators ───────────────────────────────────────
def _make_tinted_brick(br, bg, bb, mr, mg, mb):
    """Brick pattern with custom brick and mortar colours."""
    size = 64
    img = Image.new('RGBA', (size, size), (br, bg, bb, 255))
    pixels = img.load()
    brick_h, brick_w = 12, 24
    for x in range(size):
        for y in range(size):
            row = y // brick_h
            offset = (brick_w // 2) if row % 2 == 1 else 0
            bx = (x + offset) % brick_w
            noise = random.randint(-8, 8)
            if bx == 0 or y % brick_h == 0:
                pixels[x, y] = (mr, mg, mb, 255)
            else:
                wear = int(math.sin(x * 0.1 + y * 0.2) * 6)
                pixels[x, y] = (
                    max(0, min(255, br + noise + wear)),
                    max(0, min(255, bg + noise + wear)),
                    max(0, min(255, bb + noise)),
                    255,
                )
    return Texture(img)

def make_grey_brick_texture():
    """Grey brick for factory walls."""
    return _make_tinted_brick(160, 160, 165, 190, 190, 185)

def make_warm_brick_texture():
    """Warm-toned brick for furnace walls."""
    return _make_tinted_brick(210, 165, 140, 225, 215, 200)

def make_orange_brick_texture():
    """Orange glowing brick for furnace floor."""
    return _make_tinted_brick(210, 145, 95, 225, 195, 155)

def _make_tinted_metal(br, bg, bb):
    """Metal texture with custom base colour."""
    size = 64
    img = Image.new('RGBA', (size, size), (br, bg, bb, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-10, 10)
            rivet_x = x % 24 < 1
            rivet_y = y % 24 < 1
            scratch = int(math.sin(x * 0.5 + y * 0.1) * 6)
            if rivet_x or rivet_y:
                pixels[x, y] = (max(0, br - 45), max(0, bg - 45), max(0, bb - 50), 255)
            elif (x % 24 in (1, 2)) and (y % 24 in range(10, 14)):
                pixels[x, y] = (min(255, br + 30), min(255, bg + 30), min(255, bb + 25), 255)
            else:
                pixels[x, y] = (
                    max(0, min(255, br + noise + scratch)),
                    max(0, min(255, bg + noise + scratch)),
                    max(0, min(255, bb + noise)),
                    255,
                )
    return Texture(img)

def make_dark_metal_texture():
    """Dark metal for heavy machinery and anvil."""
    return _make_tinted_metal(80, 80, 90)

def make_light_metal_texture():
    """Light/white metal for printer body."""
    return _make_tinted_metal(230, 230, 235)

def make_green_screen_texture():
    """Green-tinted screen for machine indicators."""
    size = 32
    img = Image.new('RGBA', (size, size), (10, 40, 15, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            gloss = int(math.sin((x + y) * 0.15) * 8)
            lcd = 3 if (x % 3 == 0) else 0
            r = max(0, min(50, 10 + gloss))
            g = max(0, min(80, 40 + gloss + lcd))
            b = max(0, min(50, 15 + gloss))
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

def make_blue_cushion_texture():
    """Blue blanket / cushion for bed."""
    size = 64
    img = Image.new('RGBA', (size, size), (80, 100, 170, 255))
    pixels = img.load()
    for x in range(size):
        for y in range(size):
            noise = random.randint(-4, 4)
            diamond = math.sin(x * 0.2 + y * 0.2) * math.sin(x * 0.2 - y * 0.2)
            quilt = int(diamond * 15)
            seam = -18 if abs(math.sin(x * 0.2 + y * 0.2)) < 0.05 or abs(math.sin(x * 0.2 - y * 0.2)) < 0.05 else 0
            r = max(0, min(255, 80 + noise + quilt + seam))
            g = max(0, min(255, 100 + noise + quilt + seam))
            b = max(0, min(255, 170 + noise + quilt + seam))
            pixels[x, y] = (r, g, b, 255)
    return Texture(img)

# Création des textures (avec fallback couleur unie si PIL échoue)
print("Génération des textures procédurales...")
_t0 = _time_mod.time()
tex_grass  = _safe_texture(make_grass_texture, (34, 139, 34))
tex_sand   = _safe_texture(make_sand_texture, (210, 180, 140))
tex_bark   = _safe_texture(make_bark_texture, (120, 80, 45))
tex_leaves = _safe_texture(make_leaves_texture, (40, 130, 25))
tex_stone  = _safe_texture(make_stone_texture, (140, 135, 128))
tex_brick  = _safe_texture(make_brick_texture, (178, 134, 100))
tex_red_brick = _safe_texture(make_red_brick_texture, (180, 55, 45))
tex_roof   = _safe_texture(make_roof_texture, (139, 69, 19))
tex_metal  = _safe_texture(make_metal_texture, (140, 140, 155))
tex_car_paint = _safe_texture(make_car_paint_texture, (190, 40, 40))
tex_car_paint_dark = _safe_texture(make_dark_car_paint_texture, (95, 95, 95))
tex_car_glass = _safe_texture(make_car_glass_texture, (150, 190, 235))
tex_water  = _safe_texture(make_water_texture, (30, 100, 180, 200))
tex_glass  = _safe_texture(make_glass_texture, (60, 180, 70))
tex_can    = _safe_texture(make_can_texture, (200, 50, 50))
tex_cardboard = _safe_texture(make_cardboard_texture, (185, 155, 110))
tex_plastic = _safe_texture(make_plastic_texture, (220, 220, 235))
tex_rubber = _safe_texture(make_rubber_texture, (35, 35, 35))
tex_barrel = _safe_texture(make_barrel_texture, (50, 70, 170))
tex_wood_floor = _safe_texture(make_wood_floor_texture, (160, 120, 70))
tex_door = _safe_texture(make_door_texture, (110, 72, 38))
tex_window = _safe_texture(make_window_texture, (170, 210, 240))
tex_fabric     = _safe_texture(make_fabric_texture, (200, 190, 175))
tex_ceramic    = _safe_texture(make_ceramic_texture, (240, 238, 232))
tex_dark_wood  = _safe_texture(make_dark_wood_texture, (85, 55, 30))
tex_cushion    = _safe_texture(make_cushion_texture, (220, 215, 230))
tex_chrome     = _safe_texture(make_chrome_texture, (190, 195, 200))
tex_screen     = _safe_texture(make_screen_texture, (15, 20, 35))
tex_grey_brick    = _safe_texture(make_grey_brick_texture, (160, 160, 165))
tex_warm_brick    = _safe_texture(make_warm_brick_texture, (210, 165, 140))
tex_orange_brick  = _safe_texture(make_orange_brick_texture, (210, 145, 95))
tex_dark_metal    = _safe_texture(make_dark_metal_texture, (80, 80, 90))
tex_light_metal   = _safe_texture(make_light_metal_texture, (230, 230, 235))
tex_green_screen  = _safe_texture(make_green_screen_texture, (10, 40, 15))
tex_blue_cushion  = _safe_texture(make_blue_cushion_texture, (80, 100, 170))
print(f"Textures générées en {_time_mod.time() - _t0:.1f}s")

def make_tablet_body_texture():
    size = 32
    img = Image.new('RGBA', (size, size), (28, 30, 58, 255))
    pixels = img.load()
    # Рамка по краям (1 пиксель) — тёмно-серая
    for x in range(size):
        for y in range(size):
            if x < 1 or x >= size - 1 or y < 1 or y >= size - 1:
                pixels[x, y] = (80, 82, 108, 255)
    return Texture(img)

def make_tablet_screen_texture():
    size = 32
    img = Image.new('RGBA', (size, size), (22, 55, 115, 255))
    pixels = img.load()
    # Лёгкий глянцевый блик в верхней части
    for x in range(size):
        for y in range(size):
            if y < size // 3:
                v = int(18 * (1 - y / (size // 3)))
                r, g, b, _ = pixels[x, y]
                pixels[x, y] = (min(255, r + v), min(255, g + v), min(255, b + v + 8), 255)
    return Texture(img)

tex_tablet_body   = _safe_texture(make_tablet_body_texture, (28, 30, 58))
tex_tablet_screen = _safe_texture(make_tablet_screen_texture, (22, 55, 115))

# Solid-colour PIL textures for the tablet UI overlay (camera.ui quads
# ignore the color= parameter without a texture, so we bake the colour
# into a tiny image and use color=color.white on the entity).
# Фон экрана планшета (тёмный, как в мессенджере)
tex_tab_bg      = _solid_texture(18, 18, 24)
# Шапка чата (тёмно-синяя полоса)
tex_tab_header  = _solid_texture(30, 38, 55)
# Пузырь входящего сообщения (серо-синий)
tex_tab_bubble  = _solid_texture(42, 50, 68)
# Пузырь отправленного сообщения (зелёный)
tex_tab_sent    = _solid_texture(34, 85, 60)

# Текстуры кнопок машин (сплошные цвета)
tex_btn_green   = _solid_texture(50, 200, 50)
tex_btn_blue    = _solid_texture(50, 120, 220)
tex_btn_yellow  = _solid_texture(230, 200, 30)
tex_btn_red     = _solid_texture(200, 50, 50)
tex_btn_orange  = _solid_texture(255, 120, 0)

# Текстуры UI-панелей (инвентарь, материалы, миникарта)
tex_mat_bg       = _solid_texture(20, 20, 30, 230)
tex_inv_bg       = _solid_texture(0, 0, 0, 120)
tex_inv_slot     = _solid_texture(60, 60, 60, 180)
tex_inv_slot_act = _solid_texture(90, 90, 90, 220)
tex_minimap_bg   = _solid_texture(0, 0, 0, 100)

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
    w_sky, h_sky = 256, 128
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

tex_sky = _safe_texture(make_sky_texture, (135, 195, 250))
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
    color=color.white,
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
# Maisons  (3 maisons avec intérieur complet)
# ============================================================
houses = []
HOUSE_POSITIONS = [
    (0,  -20),   # 0 : maison de départ (joueur spawn ici)
    (-18, -5),   # 1 : maison résidentielle
    (22,  10),   # 2 : maison rouge (objectif 1ère tâche)
]
HOUSE_W, HOUSE_H, HOUSE_D = 7, 4, 7

for i, (hx, hz) in enumerate(HOUSE_POSITIONS):
    w, h, d = HOUSE_W, HOUSE_H, HOUSE_D
    wt = 0.15

    # Couleur des murs : rouge pour la maison 2, blanc pour les autres
    wall_color = color.white
    wall_tex   = tex_red_brick if i == 2 else tex_brick

    # ── Murs ────────────────────────────────────────────────────────────
    Entity(model='cube', scale=(w, h, wt), position=(hx, h/2, hz - d/2 + wt/2),
           texture=wall_tex, texture_scale=(4, 2), color=wall_color, collider='box')
    Entity(model='cube', scale=(wt, h, d), position=(hx - w/2 + wt/2, h/2, hz),
           texture=wall_tex, texture_scale=(2, 2), color=wall_color, collider='box')
    Entity(model='cube', scale=(wt, h, d), position=(hx + w/2 - wt/2, h/2, hz),
           texture=wall_tex, texture_scale=(2, 2), color=wall_color, collider='box')
    front_sw = (w - 1.2) / 2
    Entity(model='cube', scale=(front_sw, h, wt),
           position=(hx - w/2 + front_sw/2, h/2, hz + d/2 - wt/2),
           texture=wall_tex, texture_scale=(2, 2), color=wall_color, collider='box')
    Entity(model='cube', scale=(front_sw, h, wt),
           position=(hx + w/2 - front_sw/2, h/2, hz + d/2 - wt/2),
           texture=wall_tex, texture_scale=(2, 2), color=wall_color, collider='box')
    Entity(model='cube', scale=(1.2, h - 2.2, wt),
           position=(hx, 2.2 + (h - 2.2)/2, hz + d/2 - wt/2),
           texture=wall_tex, texture_scale=(0.5, 1), color=wall_color, collider='box')

    # ── Sol / Toit / Porte / Fenêtres ───────────────────────────────────
    Entity(model='cube', scale=(w - wt*2, 0.08, d - wt*2), position=(hx, 0.04, hz),
           texture=tex_wood_floor, texture_scale=(3, 3), color=color.white)
    Entity(model='cube', scale=(w + 0.5, 0.5, d + 0.5), position=(hx, h + 0.25, hz),
           texture=tex_roof, texture_scale=(2, 2), color=color.white)
    Entity(model='cube', scale=(1.1, 2.1, 0.06), position=(hx, 1.05, hz + d/2 + 0.03),
           texture=tex_door, texture_scale=(1, 1), color=color.white)
    for side in [-1, 1]:
        Entity(model='cube', scale=(0.06, 1.1, 1.3),
               position=(hx + (w/2 + 0.03) * side, h/2, hz),
               texture=tex_window, texture_scale=(1, 1), color=color.white)

    # ── Mobilier intérieur ───────────────────────────────────────────────
    # LIT (coin arrière-droit)
    Entity(model='cube', scale=(2.1, 0.38, 1.1), position=(hx + 2.2, 0.19, hz + 2.3),
           texture=tex_dark_wood, texture_scale=(2, 1), color=color.white)   # cadre
    Entity(model='cube', scale=(2.0, 0.16, 1.05), position=(hx + 2.2, 0.46, hz + 2.3),
           texture=tex_fabric, texture_scale=(2, 1), color=color.white)  # matelas
    Entity(model='cube', scale=(0.56, 0.13, 0.4), position=(hx + 2.72, 0.57, hz + 2.3),
           texture=tex_cushion, texture_scale=(1, 1), color=color.white)  # oreiller
    Entity(model='cube', scale=(1.4, 0.04, 0.95), position=(hx + 1.9, 0.56, hz + 2.08),
           texture=tex_blue_cushion, texture_scale=(2, 1), color=color.white)   # couverture

    # LAVABO (coin avant-gauche)
    Entity(model='cube', scale=(0.72, 0.08, 0.56), position=(hx - 2.5, 0.84, hz - 2.5),
           texture=tex_ceramic, texture_scale=(1, 1), color=color.white)  # plan de travail
    Entity(model='cube', scale=(0.42, 0.06, 0.34), position=(hx - 2.5, 0.80, hz - 2.5),
           texture=tex_ceramic, texture_scale=(1, 1), color=color.white)  # vasque
    for lx, lz in [(-0.28, -0.22), (-0.28, 0.22), (0.28, -0.22), (0.28, 0.22)]:
        Entity(model='cube', scale=(0.06, 0.84, 0.06),
               position=(hx - 2.5 + lx, 0.42, hz - 2.5 + lz),
               texture=tex_chrome, texture_scale=(1, 1), color=color.white)  # pieds
    Entity(model='cube', scale=(0.05, 0.24, 0.05),
           position=(hx - 2.5, 0.96, hz - 2.33),
           texture=tex_chrome, texture_scale=(1, 1), color=color.white)  # robinet vertical
    Entity(model='cube', scale=(0.22, 0.04, 0.04),
           position=(hx - 2.5, 1.08, hz - 2.33),
           texture=tex_chrome, texture_scale=(1, 1), color=color.white)  # bec

    # TOILETTES (coin arrière-gauche)
    Entity(model='cube', scale=(0.56, 0.46, 0.74), position=(hx - 2.5, 0.23, hz + 2.3),
           texture=tex_ceramic, texture_scale=(1, 1), color=color.white)  # cuvette
    Entity(model='cube', scale=(0.52, 0.28, 0.36), position=(hx - 2.5, 0.61, hz + 2.0),
           texture=tex_ceramic, texture_scale=(1, 1), color=color.white)  # réservoir
    Entity(model='cube', scale=(0.56, 0.04, 0.74), position=(hx - 2.5, 0.47, hz + 2.3),
           texture=tex_ceramic, texture_scale=(1, 1), color=color.white)  # siège

    # BUREAU (mur gauche, centre)
    Entity(model='cube', scale=(1.85, 0.08, 0.88), position=(hx - 2.5, 0.84, hz),
           texture=tex_dark_wood, texture_scale=(2, 1), color=color.white)   # plateau
    for dx, dz in [(-0.84, -0.38), (-0.84, 0.38), (0.84, -0.38), (0.84, 0.38)]:
        Entity(model='cube', scale=(0.08, 0.84, 0.08),
               position=(hx - 2.5 + dx, 0.42, hz + dz),
               texture=tex_dark_wood, texture_scale=(1, 1), color=color.white)  # pieds
    # Objet sur le bureau (livre / écран)
    Entity(model='cube', scale=(0.55, 0.04, 0.4), position=(hx - 2.5 + 0.5, 0.90, hz - 0.15),
           texture=tex_screen, texture_scale=(1, 1), color=color.white)     # écran plat

    # TABOURET (devant le bureau)
    # 4 ножки
    for lx, lz in [(-0.16, -0.16), (-0.16, 0.16), (0.16, -0.16), (0.16, 0.16)]:
        Entity(model='cube', scale=(0.06, 0.44, 0.06),
               position=(hx - 2.0 + lx, 0.22, hz + 0.9 + lz),
               texture=tex_dark_wood, texture_scale=(1, 1), color=color.white)
    # сиденье
    Entity(model='cube', scale=(0.44, 0.06, 0.44), position=(hx - 2.0, 0.47, hz + 0.9),
           texture=tex_dark_wood, texture_scale=(1, 1), color=color.white)
    # подушка
    Entity(model='cube', scale=(0.38, 0.04, 0.38), position=(hx - 2.0, 0.52, hz + 0.9),
           texture=tex_cushion, texture_scale=(1, 1), color=color.white)

    houses.append(Entity(visible=False))

# ── Табличка «Красный дом» над дверью дома 2 ────────────────────────────────
_rh_x, _rh_z = HOUSE_POSITIONS[2]
# Деревянная планка-вывеска
Entity(model='cube', scale=(2.6, 0.5, 0.08),
       position=(_rh_x, HOUSE_H - 0.4, _rh_z + HOUSE_D / 2 + 0.06),
       texture=tex_wood_floor, texture_scale=(2, 1), color=color.white)
# Текст на вывеске
Text(parent=scene, text='RED HOUSE', scale=(8, 8, 8),
     position=(_rh_x, HOUSE_H - 0.35, _rh_z + HOUSE_D / 2 + 0.12),
     origin=(0, 0), color=color.white)

# ── Extras maison de départ ──────────────────────────────────────────────────
_spawn_hx, _spawn_hz = HOUSE_POSITIONS[0]
_spw, _spd = HOUSE_W, HOUSE_D

# Tablette posée sur le bureau de la maison de départ
tablet_entity = Entity(
    model='cube', scale=(0.35, 0.04, 0.24),
    position=(_spawn_hx - 2.5 + 0.2, 0.89, _spawn_hz - 0.2),
    texture=tex_tablet_body, texture_scale=(1, 1),
    color=color.white, unlit=True,
)
# Экран планшета
tablet_entity.screen = Entity(
    model='cube', scale=(0.78, 0.22, 0.9),
    position=(0, 0.026, 0), parent=tablet_entity,
    texture=tex_tablet_screen, texture_scale=(1, 1),
    color=color.white, unlit=True,
)
tablet_entity_ref = [tablet_entity]
TABLET_PICKUP_RANGE = 2.5

# Bloqueur de porte invisible (retiré quand la tablette est ramassée)
door_blocker = Entity(
    model='cube', scale=(1.2, 2.2, 0.3),
    position=(_spawn_hx, 1.1, _spawn_hz + _spd/2 + 0.15),
    collider='box', visible=False,
)

# ============================================================
# Usine (bâtiment creux avec intérieur)
# ============================================================
factory_pos = (0, 0, 25)
fw, fh, fd = 18, 8, 12  # largeur, hauteur, profondeur
fx, fz = factory_pos[0], factory_pos[2]
fwt = 0.15  # épaisseur des murs

# --- Murs extérieurs creux (серый кирпич) ---
# Mur arrière
Entity(model='cube', scale=(fw, fh, fwt), position=(fx, fh/2, fz + fd/2 - fwt/2),
       texture=tex_grey_brick, texture_scale=(8, 4), color=color.white, collider='box')
# Mur gauche
Entity(model='cube', scale=(fwt, fh, fd), position=(fx - fw/2 + fwt/2, fh/2, fz),
       texture=tex_grey_brick, texture_scale=(5, 4), color=color.white, collider='box')
# Mur droit
Entity(model='cube', scale=(fwt, fh, fd), position=(fx + fw/2 - fwt/2, fh/2, fz),
       texture=tex_grey_brick, texture_scale=(5, 4), color=color.white, collider='box')
# Mur avant — partie gauche
f_front_side = (fw - 4.0) / 2
Entity(model='cube', scale=(f_front_side, fh, fwt),
       position=(fx - fw/2 + f_front_side/2, fh/2, fz - fd/2 + fwt/2),
       texture=tex_grey_brick, texture_scale=(3, 4), color=color.white, collider='box')
# Mur avant — partie droite
Entity(model='cube', scale=(f_front_side, fh, fwt),
       position=(fx + fw/2 - f_front_side/2, fh/2, fz - fd/2 + fwt/2),
       texture=tex_grey_brick, texture_scale=(3, 4), color=color.white, collider='box')
# Au-dessus de la porte
Entity(model='cube', scale=(4.0, fh - 4.5, fwt),
       position=(fx, 4.5 + (fh - 4.5)/2, fz - fd/2 + fwt/2),
       texture=tex_grey_brick, texture_scale=(2, 2), color=color.white, collider='box')
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
Entity(model=make_textured_cylinder(), scale=(1.2, 6, 1.2), position=(fx + 6, 10, fz + 3),
       texture=tex_metal, texture_scale=(1, 2), color=color.white, collider='box')

# --- Intérieur de l'usine ---

# == ПЕЧКА / FOUR (côté droit-arrière — pour le carton) ==
furnace_pos = Vec3(fx + 5.5, 0, fz + 3.5)
# Dimensions internes: largeur=2.5, hauteur=2.8, profondeur=2.0
f_fw, f_fh, f_fd = 2.5, 2.8, 2.0
f_wt = 0.12  # épaisseur des parois
# Mur arrière
Entity(model='cube', scale=(f_fw, f_fh, f_wt),
       position=(furnace_pos.x, f_fh/2, furnace_pos.z + f_fd/2 - f_wt/2),
       texture=tex_warm_brick, texture_scale=(2, 2), color=color.white, collider='box')
# Mur gauche
Entity(model='cube', scale=(f_wt, f_fh, f_fd),
       position=(furnace_pos.x - f_fw/2 + f_wt/2, f_fh/2, furnace_pos.z),
       texture=tex_warm_brick, texture_scale=(1, 2), color=color.white, collider='box')
# Mur droit
Entity(model='cube', scale=(f_wt, f_fh, f_fd),
       position=(furnace_pos.x + f_fw/2 - f_wt/2, f_fh/2, furnace_pos.z),
       texture=tex_warm_brick, texture_scale=(1, 2), color=color.white, collider='box')
# Mur avant — deux côtés autour de l'ouverture
f_door_w = 1.0
f_side_w = (f_fw - f_door_w) / 2
Entity(model='cube', scale=(f_side_w, f_fh, f_wt),
       position=(furnace_pos.x - f_fw/2 + f_side_w/2, f_fh/2, furnace_pos.z - f_fd/2 + f_wt/2),
       texture=tex_warm_brick, texture_scale=(1, 2), color=color.white, collider='box')
Entity(model='cube', scale=(f_side_w, f_fh, f_wt),
       position=(furnace_pos.x + f_fw/2 - f_side_w/2, f_fh/2, furnace_pos.z - f_fd/2 + f_wt/2),
       texture=tex_warm_brick, texture_scale=(1, 2), color=color.white, collider='box')
# Au-dessus de l'ouverture
Entity(model='cube', scale=(f_door_w, f_fh - 1.5, f_wt),
       position=(furnace_pos.x, 1.5 + (f_fh - 1.5)/2, furnace_pos.z - f_fd/2 + f_wt/2),
       texture=tex_warm_brick, texture_scale=(1, 1), color=color.white, collider='box')
# Toit du four
Entity(model='cube', scale=(f_fw, f_wt, f_fd),
       position=(furnace_pos.x, f_fh, furnace_pos.z),
       texture=tex_dark_metal, texture_scale=(2, 1), color=color.white, collider='box')
# Sol intérieur (briques rougeoyantes)
Entity(model='cube', scale=(f_fw - f_wt*2, 0.06, f_fd - f_wt*2),
       position=(furnace_pos.x, 0.03, furnace_pos.z),
       texture=tex_orange_brick, texture_scale=(1, 1), color=color.white)
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
Entity(model=make_textured_cylinder(), scale=(0.4, 3.0, 0.4),
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

# == MACHINE DE RECYCLAGE (mur arrière, centre — pour tout sauf carton) ==
recycler_pos = Vec3(fx + 1.5, 0, fz + 3.5)
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
       color=color.rgb(30, 30, 30), unlit=True)
# Panneau de contrôle (face avant — au-dessus du proём)
Entity(model='cube', scale=(1.4, 0.8, 0.08),
       position=(recycler_pos.x, r_open_bottom + r_open_h + r_top_h * 0.4,
                 recycler_pos.z - r_fd/2 - 0.02),
       texture=tex_metal, texture_scale=(1, 1), color=color.white)
# Boutons (разноцветные с PIL-текстурами)
btn_y = r_open_bottom + r_open_h + r_top_h * 0.55
for bx_off, bt in [(-0.45, tex_btn_green),
                    (-0.15, tex_btn_blue),
                    (0.15, tex_btn_yellow),
                    (0.45, tex_btn_red)]:
    Entity(model='cube', scale=(0.18, 0.18, 0.1),
           position=(recycler_pos.x + bx_off, btn_y, recycler_pos.z - r_fd/2 - 0.04),
           texture=bt, color=color.white, unlit=True)
# Écran indicateur
Entity(model='cube', scale=(0.7, 0.4, 0.08),
       position=(recycler_pos.x, r_open_bottom + r_open_h + r_top_h * 0.2,
                 recycler_pos.z - r_fd/2 - 0.04),
       texture=tex_green_screen, color=color.white, unlit=True)
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

# == MACHINE MÉTAL (mur arrière, gauche — pour canette + bidon) ==
metal_pos = Vec3(fx - 3.5, 0, fz + 3.5)
m_fw, m_fh, m_fd = 2.5, 3.0, 2.0
m_wt = 0.12
# Mur arrière
Entity(model='cube', scale=(m_fw, m_fh, m_wt),
       position=(metal_pos.x, m_fh/2, metal_pos.z + m_fd/2 - m_wt/2),
       texture=tex_dark_metal, texture_scale=(2, 2), color=color.white, collider='box')
# Mur gauche
Entity(model='cube', scale=(m_wt, m_fh, m_fd),
       position=(metal_pos.x - m_fw/2 + m_wt/2, m_fh/2, metal_pos.z),
       texture=tex_dark_metal, texture_scale=(1, 2), color=color.white, collider='box')
# Mur droit
Entity(model='cube', scale=(m_wt, m_fh, m_fd),
       position=(metal_pos.x + m_fw/2 - m_wt/2, m_fh/2, metal_pos.z),
       texture=tex_dark_metal, texture_scale=(1, 2), color=color.white, collider='box')
# Mur avant — partie basse + partie haute (ouverture centrale)
m_open_h = 1.4;  m_open_bottom = 0.4
m_top_h = m_fh - m_open_bottom - m_open_h
Entity(model='cube', scale=(m_fw, m_open_bottom, m_wt),
       position=(metal_pos.x, m_open_bottom/2, metal_pos.z - m_fd/2 + m_wt/2),
       texture=tex_dark_metal, texture_scale=(2, 1), color=color.white, collider='box')
Entity(model='cube', scale=(m_fw, m_top_h, m_wt),
       position=(metal_pos.x, m_open_bottom + m_open_h + m_top_h/2, metal_pos.z - m_fd/2 + m_wt/2),
       texture=tex_dark_metal, texture_scale=(2, 1), color=color.white, collider='box')
# Toit
Entity(model='cube', scale=(m_fw, m_wt, m_fd),
       position=(metal_pos.x, m_fh, metal_pos.z),
       texture=tex_dark_metal, texture_scale=(2, 1), color=color.white, collider='box')
# Sol intérieur (brique sombre chauffée)
Entity(model='cube', scale=(m_fw - m_wt*2, 0.06, m_fd - m_wt*2),
       position=(metal_pos.x, 0.03, metal_pos.z),
       texture=tex_stone, texture_scale=(1, 1), color=color.white)
# Entonnoir de chargement (haut)
Entity(model='cube', scale=(1.2, 0.5, 1.0),
       position=(metal_pos.x, m_fh + 0.25, metal_pos.z),
       texture=tex_dark_metal, texture_scale=(1, 1), color=color.white)
Entity(model='cube', scale=(0.8, 0.12, 0.6),   # ouverture sombre
       position=(metal_pos.x, m_fh + 0.54, metal_pos.z),
       color=color.rgb(25, 20, 15), unlit=True)
# Panneau de contrôle
Entity(model='cube', scale=(1.2, 0.7, 0.08),
       position=(metal_pos.x, m_open_bottom + m_open_h + m_top_h * 0.4,
                 metal_pos.z - m_fd/2 - 0.02),
       texture=tex_dark_metal, texture_scale=(1, 1), color=color.white)
# Boutons (разноцветные с PIL-текстурами)
for bx_off, bt in [(-0.3, tex_btn_green),
                    (0.0, tex_btn_orange),
                    (0.3, tex_btn_red)]:
    Entity(model='cube', scale=(0.2, 0.2, 0.1),
           position=(metal_pos.x + bx_off, m_open_bottom + m_open_h + m_top_h * 0.55,
                     metal_pos.z - m_fd/2 - 0.04),
           texture=bt, color=color.white, unlit=True)
# Panneau "MÉTAL"
Entity(model='cube', scale=(0.7, 0.3, 0.06),
       position=(metal_pos.x, m_open_bottom + m_open_h + m_top_h * 0.15,
                 metal_pos.z - m_fd/2 - 0.04),
       color=color.rgb(20, 20, 30), unlit=True)
# Indicateur lumineux
metal_light = Entity(model='cube', scale=(0.2, 0.2, 0.08),
       position=(metal_pos.x + 0.8, m_fh - 0.3, metal_pos.z - m_fd/2 - 0.02),
       color=color.rgb(255, 120, 0), unlit=True)
metal_inside_items = []

# Tuyaux le long du mur arrière
for pipe_x in [fx - 6, fx - 3, fx + 7]:
    Entity(model=make_textured_cylinder(), scale=(0.2, fh - 0.5, 0.2),
           position=(pipe_x, fh/2, fz + fd/2 - 0.5),
           texture=tex_metal, texture_scale=(1, 2), color=color.white)

# == НАКОВАЛЬНЯ / ENCLUME (côté gauche, devant) ==
_anvil_x, _anvil_z = fx - 6, fz - 2
# Подставка (пень)
Entity(model='cube', scale=(0.7, 0.6, 0.7), position=(_anvil_x, 0.3, _anvil_z),
       texture=tex_dark_wood, texture_scale=(1, 1), color=color.white)
# Основание наковальни (широкое)
Entity(model='cube', scale=(1.2, 0.25, 0.6), position=(_anvil_x, 0.73, _anvil_z),
       texture=tex_dark_metal, texture_scale=(1, 1), color=color.white)
# Талия (узкая часть)
Entity(model='cube', scale=(0.7, 0.2, 0.4), position=(_anvil_x, 0.95, _anvil_z),
       texture=tex_dark_metal, texture_scale=(1, 1), color=color.white)
# Рабочая поверхность (верх)
Entity(model='cube', scale=(1.4, 0.15, 0.55), position=(_anvil_x, 1.1, _anvil_z),
       texture=tex_dark_metal, texture_scale=(1, 1), color=color.white)
# Рог наковальни (конус, выступающая часть)
Entity(model='cube', scale=(0.6, 0.12, 0.22), position=(_anvil_x + 0.9, 1.08, _anvil_z),
       texture=tex_dark_metal, texture_scale=(1, 1), color=color.white)

# == ПРИНТЕР / PRINTER (противоположный угол от наковальни) ==
_printer_x, _printer_z = fx + 6, fz - 2
PRINTER_RANGE = 3.0
# Корпус принтера
Entity(model='cube', scale=(1.4, 0.5, 0.9), position=(_printer_x, 0.85, _printer_z),
       texture=tex_light_metal, texture_scale=(1, 1), color=color.white, collider='box')
# Нижняя часть (подставка)
Entity(model='cube', scale=(1.3, 0.6, 0.85), position=(_printer_x, 0.3, _printer_z),
       texture=tex_dark_metal, texture_scale=(1, 1), color=color.white, collider='box')
# Экран на передней панели
Entity(model='cube', scale=(0.5, 0.2, 0.05),
       position=(_printer_x, 1.0, _printer_z - 0.46),
       texture=tex_green_screen, color=color.white, unlit=True)
# Лоток для бумаги (входной, сверху)
Entity(model='cube', scale=(0.8, 0.03, 0.4),
       position=(_printer_x, 1.12, _printer_z + 0.15),
       texture=tex_light_metal, texture_scale=(1, 1), color=color.white)
# Лоток для бумаги (выходной, спереди)
Entity(model='cube', scale=(0.8, 0.03, 0.35),
       position=(_printer_x, 0.65, _printer_z - 0.55),
       texture=tex_light_metal, texture_scale=(1, 1), color=color.white)
# Кнопка питания
Entity(model='cube', scale=(0.1, 0.1, 0.05),
       position=(_printer_x + 0.5, 1.0, _printer_z - 0.46),
       texture=tex_btn_green, color=color.white, unlit=True)
# Индикатор
printer_light = Entity(model='cube', scale=(0.15, 0.15, 0.05),
       position=(_printer_x - 0.5, 1.0, _printer_z - 0.46),
       color=color.rgb(50, 150, 50), unlit=True)

# == ФЛЕШКА / USB в дальнем доме ==
_usb_house = HOUSE_POSITIONS[1]  # (-18, -5)
usb_entity_ref = [Entity(model='cube', scale=(0.15, 0.05, 0.4),
    position=(_usb_house[0] + 1.5, 1.05, _usb_house[1] + 1.5),
    color=color.rgb(30, 30, 30), unlit=True)]

# Distances d'interaction avec les machines
MACHINE_RANGE = 4.0

# Inventaire du joueur
inventory = []  # liste de {'name': ..., 'points': ...}
MAX_INVENTORY = 5

# Positions des voitures (définies avant arbres/rochers pour exclusion)
car_positions = [(10, -20), (-25, 5), (30, -5)]

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
            for cpx, cpz in car_positions:
                if distance_2d((tx, tz), (cpx, cpz)) < 6:
                    too_close = True
                    break
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
        model=resolve_model('tree_trunk', make_textured_cylinder), scale=(trunk_r, trunk_h, trunk_r),
        position=(tx, -0.1, tz), texture=tex_bark,
        color=color.white, collider='box',
    )

    # Cone: vertices y=-0.5..0.5, origin at center
    for level in range(3):
        cone_h = 1.5
        cone_y = trunk_h * 0.5 + level * 1.2 + cone_h / 2
        cone_scale = (2.5 - level * 0.6)
        Entity(
            model=resolve_model('tree_leaves', Cone), scale=(cone_scale, 1.5, cone_scale),
            position=(tx, cone_y, tz), texture=tex_leaves,
            color=color.white,
        )

# ============================================================
# Rochers
# ============================================================
for _ in range(ROCK_COUNT):
    attempts = 0
    while attempts < 50:
        rx, rz = random_island_pos(margin=2)
        too_close = False
        for hx, hz in HOUSE_POSITIONS:
            if distance_2d((rx, rz), (hx, hz)) < 8:
                too_close = True
                break
        if distance_2d((rx, rz), (factory_pos[0], factory_pos[2])) < 16:
            too_close = True
        if not too_close:
            for cpx, cpz in car_positions:
                if distance_2d((rx, rz), (cpx, cpz)) < 6:
                    too_close = True
                    break
        if not too_close:
            break
        attempts += 1
    else:
        continue
    scale_factor = random.uniform(0.5, 2.0)
    # Rocher principal (cube aplati et tourné)
    Entity(
        model=resolve_model('rock', 'cube'),
        scale=(
            scale_factor * random.uniform(0.8, 1.4),
            scale_factor * random.uniform(0.4, 0.7),
            scale_factor * random.uniform(0.8, 1.4),
        ),
        position=(rx, scale_factor * 0.2, rz),
        rotation=(random.uniform(-15, 15), random.uniform(0, 360), random.uniform(-10, 10)),
        texture=tex_car_paint_dark,
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
        texture=tex_car_paint_dark,
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
            texture=tex_car_paint_dark,
            texture_scale=(2, 2),
            color=color.white,
        )

# ============================================================
# Déchets (objets à ramasser)
# ============================================================
trash_items = []

TRASH_TYPES = [
    {'name': 'Bouteille', 'model': lambda: resolve_model('bouteille', make_textured_cylinder), 'scale': (0.15, 0.4, 0.15),
     'color': color.white, 'points': 10, 'texture': 'tex_glass'},
    {'name': 'Canette', 'model': lambda: resolve_model('canette', make_textured_cylinder), 'scale': (0.12, 0.25, 0.12),
     'color': color.white, 'points': 10, 'texture': 'tex_can'},
    {'name': 'Sac plastique', 'model': lambda: resolve_model('sac_plastique', 'cube'), 'scale': (0.4, 0.05, 0.3),
     'color': color.white, 'points': 5, 'texture': 'tex_plastic'},
    {'name': 'Pneu', 'model': lambda: resolve_model('pneu', 'sphere'), 'scale': (0.5, 0.25, 0.5),
     'color': color.white, 'points': 25, 'texture': 'tex_rubber'},
    {'name': 'Carton', 'model': lambda: resolve_model('carton', 'cube'), 'scale': (0.5, 0.3, 0.4),
     'color': color.white, 'points': 5, 'texture': 'tex_cardboard'},
    {'name': 'Bidon', 'model': lambda: resolve_model('bidon', make_textured_cylinder), 'scale': (0.25, 0.5, 0.25),
     'color': color.white, 'points': 15, 'texture': 'tex_barrel'},
]

# Catégories par machine
FURNACE_NAMES  = {'Carton'}
METAL_NAMES    = {'Canette', 'Bidon'}
RECYCLER_NAMES = {'Bouteille', 'Sac plastique', 'Pneu'}

# Формируем список мусора: 12 картон, 25 металл, 25 пластик
_trash_schedule = []
for _ in range(12):
    _trash_schedule.append(TRASH_TYPES[4])           # Carton
for _ in range(13):
    _trash_schedule.append(TRASH_TYPES[1])           # Canette
for _ in range(12):
    _trash_schedule.append(TRASH_TYPES[5])           # Bidon
for _ in range(9):
    _trash_schedule.append(TRASH_TYPES[0])           # Bouteille
for _ in range(8):
    _trash_schedule.append(TRASH_TYPES[2])           # Sac plastique
for _ in range(8):
    _trash_schedule.append(TRASH_TYPES[3])           # Pneu
random.shuffle(_trash_schedule)

for i in range(TRASH_COUNT):
    tx, tz = random_island_pos(margin=2)
    trash_type = _trash_schedule[i]

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
    position=(0, 1.5, -20),
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
    text='', position=(0, -0.25), origin=(0, 0), scale=1.3, color=color.yellow,
)

win_text = Text(
    text='', position=(0, 0.1), origin=(0, 0), scale=3, color=color.green,
)

crosshair = Entity(
    parent=camera.ui, model='quad', scale=0.008, color=color.white, position=(0, 0),
)

# ── Инвентарь (визуальные слоты) ────────────────────────────────────────────
_inv_slot_size = 0.065
_inv_gap = 0.008
_inv_total_w = MAX_INVENTORY * _inv_slot_size + (MAX_INVENTORY - 1) * _inv_gap
_inv_start_x = -_inv_total_w / 2
_inv_y = -0.42
_inv_bg = Entity(parent=camera.ui, model='quad',
                 scale=(_inv_total_w + 0.03, _inv_slot_size + 0.025),
                 position=(0, _inv_y), texture=tex_inv_bg, color=color.white, z=0.05)
_inv_slots_bg = []
_inv_slots_icon = []
_inv_slots_txt = []
_trash_tex_map = {
    'Bouteille': tex_glass, 'Canette': tex_can, 'Sac plastique': tex_plastic,
    'Pneu': tex_rubber, 'Carton': tex_cardboard, 'Bidon': tex_barrel,
}
_trash_short = {
    'Bouteille': 'БУТ', 'Canette': 'БАН', 'Sac plastique': 'ПАК',
    'Pneu': 'ШИН', 'Carton': 'КАР', 'Bidon': 'БИД',
}
for _si in range(MAX_INVENTORY):
    sx = _inv_start_x + _si * (_inv_slot_size + _inv_gap) + _inv_slot_size / 2
    sb = Entity(parent=camera.ui, model='quad', scale=(_inv_slot_size, _inv_slot_size),
                position=(sx, _inv_y), texture=tex_inv_slot, color=color.white, z=0.04)
    si_icon = Entity(parent=camera.ui, model='quad',
                     scale=(_inv_slot_size * 0.7, _inv_slot_size * 0.7),
                     position=(sx, _inv_y + 0.005), color=color.white, z=0.03,
                     visible=False)
    si_txt = Text(parent=camera.ui, text='', position=(sx, _inv_y - 0.025),
                  origin=(0, 0), scale=0.6, color=color.rgb(200, 200, 200), z=0.02)
    _inv_slots_bg.append(sb)
    _inv_slots_icon.append(si_icon)
    _inv_slots_txt.append(si_txt)


def _refresh_inventory_ui():
    for i in range(MAX_INVENTORY):
        if i < len(inventory):
            item = inventory[i]
            _inv_slots_icon[i].texture = _trash_tex_map.get(item['name'], tex_metal)
            _inv_slots_icon[i].visible = True
            _inv_slots_txt[i].text = _trash_short.get(item['name'], '?')
            _inv_slots_bg[i].texture = tex_inv_slot_act
        else:
            _inv_slots_icon[i].visible = False
            _inv_slots_txt[i].text = ''
            _inv_slots_bg[i].texture = tex_inv_slot


minimap_bg = Entity(
    parent=camera.ui, model='quad', scale=(0.2, 0.2),
    position=(0.7, 0.35), texture=tex_minimap_bg, color=color.white,
)
minimap_player_dot = Entity(
    parent=camera.ui, model='circle', scale=0.01,
    position=(0.7, 0.35), color=color.red, z=-0.1,
)

instructions_text = Text(
    text='ZQSD: Bouger | E: Ramasser/Charger | R: Démarrer machine | TAB: Planшет | Échap: Quitter',
    position=(0, -0.4), origin=(0, 0), scale=0.9, color=color.rgb(200, 200, 200),
    background=True,
)

# Clôture supprimée — la mer est visible depuis le bord de l'île
half_island = ISLAND_SIZE / 2

# ============================================================
# Bateau en bois (ponton angulaire)
# ============================================================
_bx = -half_island - 2
_by = 0.0
_bz = 0

# Fond de coque
Entity(model='cube', scale=(2.8, 0.2, 10.0), position=(_bx, _by + 0.1, _bz),
       color=color.rgb(112, 76, 40), texture=tex_bark, texture_scale=(2, 5), collider='box')

# Bordé gauche (flanc vertical)
Entity(model='cube', scale=(0.22, 0.74, 9.8), position=(_bx - 1.35, _by + 0.47, _bz),
       color=color.white, texture=tex_bark, texture_scale=(1, 5), collider='box')
# Bordé droit
Entity(model='cube', scale=(0.22, 0.74, 9.8), position=(_bx + 1.35, _by + 0.47, _bz),
       color=color.white, texture=tex_bark, texture_scale=(1, 5), collider='box')

# Proue — sections qui rétrécissent vers la pointe
Entity(model='cube', scale=(2.42, 0.84, 1.28), position=(_bx, _by + 0.52, _bz + 4.66),
       color=color.white, texture=tex_bark, collider='box')
Entity(model='cube', scale=(1.72, 0.84, 1.08), position=(_bx, _by + 0.52, _bz + 5.8),
       color=color.white, texture=tex_bark, collider='box')
Entity(model='cube', scale=(0.86, 0.84, 0.88), position=(_bx, _by + 0.52, _bz + 6.74),
       color=color.white, texture=tex_bark, collider='box')
# Étrave (bout de proue)
Entity(model='cube', scale=(0.28, 1.02, 0.52), position=(_bx, _by + 0.61, _bz + 7.34),
       color=color.rgb(100, 64, 28), unlit=True)

# Tableau arrière (poupe droite)
Entity(model='cube', scale=(3.04, 0.86, 0.24), position=(_bx, _by + 0.53, _bz - 5.0),
       color=color.white, texture=tex_bark, collider='box')

# Pont intérieur (planches marchables)
Entity(model='cube', scale=(2.44, 0.1, 9.2), position=(_bx, _by + 0.24, _bz),
       color=color.white, texture=tex_bark, texture_scale=(2, 5), collider='box')

# Membrures (traverses internes)
for _rz in [-3.5, -1.5, 0.5, 2.5]:
    Entity(model='cube', scale=(2.52, 0.1, 0.2), position=(_bx, _by + 0.22, _bz + _rz),
           color=color.rgb(92, 60, 26))

# Tolets (chevilles de rame)
for side in [-1, 1]:
    Entity(model='cube', scale=(0.1, 0.32, 0.1),
           position=(_bx + side * 1.3, _by + 0.84, _bz + 0.5),
           color=color.rgb(72, 46, 18), unlit=True)

# ============================================================
# Voitures (décor)
# ============================================================
car_colors = [color.rgb(200, 50, 50), color.rgb(200, 50, 50), color.rgb(200, 50, 50)]

for (cx, cz), ccolor in zip(car_positions, car_colors):
    # ── CAISSE BASSE (châssis + flancs) ─────────────────────────────────
    Entity(model=resolve_model('car_body', 'cube'), scale=(2.2, 0.55, 4.4),
           position=(cx, 0.57, cz), color=color.white,
           texture=tex_car_paint, texture_scale=(2, 3), collider='box')

    # Bas de caisse (seuils noirs)
    for side in [-1, 1]:
        Entity(model='cube', scale=(0.12, 0.24, 4.2),
               position=(cx + side * 1.06, 0.36, cz),
               texture=tex_rubber, texture_scale=(2, 1), color=color.white)

    # ── CAPOT ────────────────────────────────────────────────────────────
    Entity(model='cube', scale=(2.2, 0.1, 1.65),
           position=(cx, 0.88, cz + 1.52),
           color=color.white, texture=tex_car_paint, texture_scale=(1, 1))

    # ── COFFRE ───────────────────────────────────────────────────────────
    Entity(model='cube', scale=(1.9, 0.08, 1.12),
           position=(cx, 0.84, cz - 1.63),
           color=color.white, texture=tex_car_paint, texture_scale=(1, 1))

    # ── HABITACLE ────────────────────────────────────────────────────────
    Entity(model=resolve_model('car_top', 'cube'), scale=(1.88, 0.64, 2.22),
           position=(cx, 1.15, cz - 0.1),
           color=color.white, texture=tex_car_paint, texture_scale=(1, 1))

    # Extension arrière (ligne fastback légère)
    Entity(model='cube', scale=(1.88, 0.28, 0.38),
           position=(cx, 0.98, cz - 1.28),
           color=color.white, texture=tex_car_paint, texture_scale=(1, 1))

    # ── PARE-BRISE AVANT ─────────────────────────────────────────────────
    _fw_h = math.sqrt(0.60**2 + 1.18**2)
    _fw_a = math.degrees(math.atan2(1.18, 0.60))
    Entity(model='cube', scale=(1.72, _fw_h, 0.04),
           position=(cx, 1.15, cz + 1.0), rotation=(-_fw_a, 0, 0),
           texture=tex_car_glass, color=color.white)

    # ── LUNETTE ARRIÈRE ───────────────────────────────────────────────────
    _rw_h = math.sqrt(0.36**2 + 0.88**2)
    _rw_a = math.degrees(math.atan2(0.88, 0.36))
    Entity(model='cube', scale=(1.72, _rw_h, 0.04),
           position=(cx, 1.06, cz - 1.22), rotation=(_rw_a, 0, 0),
           texture=tex_car_glass, color=color.white)

    # ── MONTANTS A / B / C ────────────────────────────────────────────────
    for side in [-1, 1]:
        Entity(model='cube', scale=(0.11, _fw_h, 0.11),
               position=(cx + side * 0.88, 1.15, cz + 1.0),
               rotation=(-_fw_a, 0, 0), texture=tex_rubber, texture_scale=(1, 1),
               color=color.white)
        Entity(model='cube', scale=(0.1, 0.66, 0.1),
               position=(cx + side * 0.88, 0.92, cz - 0.1),
               texture=tex_rubber, texture_scale=(1, 1), color=color.white)
        Entity(model='cube', scale=(0.11, _rw_h, 0.11),
               position=(cx + side * 0.88, 1.06, cz - 1.22),
               rotation=(_rw_a, 0, 0), texture=tex_rubber, texture_scale=(1, 1),
               color=color.white)

    # ── VITRES LATÉRALES ─────────────────────────────────────────────────
    for side in [-1, 1]:
        Entity(model='cube', scale=(0.04, 0.54, 2.12),
               position=(cx + side * 0.95, 1.15, cz - 0.1),
               texture=tex_car_glass, color=color.white)

    # ── PARE-CHOCS AVANT ─────────────────────────────────────────────────
    Entity(model='cube', scale=(2.24, 0.38, 0.22),
           position=(cx, 0.3, cz + 2.21), texture=tex_rubber, texture_scale=(2, 1),
           color=color.white)
    Entity(model='cube', scale=(1.5, 0.22, 0.1),
           position=(cx, 0.42, cz + 2.32), texture=tex_chrome, texture_scale=(2, 1),
           color=color.white)  # calandre

    # ── PARE-CHOCS ARRIÈRE ────────────────────────────────────────────────
    Entity(model='cube', scale=(2.24, 0.38, 0.22),
           position=(cx, 0.3, cz - 2.21), texture=tex_rubber, texture_scale=(2, 1),
           color=color.white)

    # ── PHARES AVANT ─────────────────────────────────────────────────────
    for side in [-1, 1]:
        Entity(model='cube', scale=(0.54, 0.16, 0.1),
               position=(cx + side * 0.76, 0.71, cz + 2.26),
               color=color.rgb(255, 255, 210), unlit=True)
        Entity(model='cube', scale=(0.46, 0.06, 0.08),
               position=(cx + side * 0.76, 0.59, cz + 2.28),
               color=color.rgb(255, 255, 240), unlit=True)  # DRL

    # ── FEUX ARRIÈRE ──────────────────────────────────────────────────────
    for side in [-1, 1]:
        Entity(model='cube', scale=(0.56, 0.18, 0.1),
               position=(cx + side * 0.76, 0.73, cz - 2.2),
               color=color.rgb(195, 22, 22), unlit=True)

    # ── ARCHES DE ROUES ───────────────────────────────────────────────────
    for wx in [-1, 1]:
        for wz_off in [-1.35, 1.35]:
            Entity(model='cube', scale=(0.28, 0.55, 0.66),
                   position=(cx + wx * 1.08, 0.42, cz + wz_off),
                   texture=tex_rubber, texture_scale=(1, 1), color=color.white)

    # ── ROUES ─────────────────────────────────────────────────────────────
    for wx in [-1, 1]:
        for wz_off in [-1.35, 1.35]:
            Entity(model=resolve_model('car_wheel', make_textured_cylinder),
                   scale=(0.46, 0.19, 0.46),
                   position=(cx + wx * 1.12, 0.3, cz + wz_off),
                   rotation=(0, 0, 90), color=color.white,
                   texture=tex_rubber, texture_scale=(1, 1))

    # ── POIGNÉES DE PORTES ────────────────────────────────────────────────
    for side in [-1, 1]:
        Entity(model='cube', scale=(0.05, 0.07, 0.24),
               position=(cx + side * 1.12, 0.88, cz + 0.18),
               texture=tex_chrome, texture_scale=(1, 1), color=color.white)

# ============================================================
# Logique de jeu
# ============================================================
game_won = [False]
closest_trash = [None]
anim_time = [0.0]
near_furnace  = [False]
near_recycler = [False]
near_metal    = [False]
processed_count = [0]

# ── Crafting / Побег с острова ──────────────────────────────────────────
paper_count           = [0]    # бумага из картона
smelted_metal_count   = [0]    # переплавленный металл
recycled_plastic_count= [0]    # переработанный пластик

CRAFT_RECIPES = [
    {'name': 'wheel',   'ru': 'Штурвал',  'mat': 'metal',   'cost': 10, 'station': 'anvil'},
    {'name': 'sail',    'ru': 'Парус',     'mat': 'plastic', 'cost': 15, 'station': 'recycler'},
    {'name': 'anchor',  'ru': 'Якорь',     'mat': 'metal',   'cost': 13, 'station': 'anvil'},
    {'name': 'compass', 'ru': 'Компас',    'mat': 'metal',   'cost': 2,  'station': 'anvil'},
    {'name': 'oars',    'ru': 'Вёсла',     'mat': 'plastic', 'cost': 10, 'station': 'recycler'},
]
blueprints     = {r['name']: False for r in CRAFT_RECIPES}
crafted_parts  = {r['name']: False for r in CRAFT_RECIPES}
boat_parts_installed = {r['name']: False for r in CRAFT_RECIPES}
usb_found      = [False]
map_printed    = [False]
near_anvil     = [False]
near_boat      = [False]
near_printer   = [False]
escape_started = [False]
escape_timer   = [0.0]
ANVIL_RANGE = 3.0
BOAT_RANGE  = 5.0
boat_part_entities = []
_esc_refs = {}

# Файлы, загруженные в машины (не обработанные — ждут нажатия R)
furnace_pending  = []
recycler_pending = []
metal_pending    = []

# ── Состояние планшета / задания ────────────────────────────────────────────
tablet_picked_up    = [False]
tablet_open         = [False]
red_house_visited   = [False]
tablet_task_done    = [False]
red_house_pos       = HOUSE_POSITIONS[2]   # (22, 10)

# ── Инвентарь материалов (Q) ────────────────────────────────────────────────
materials_open = [False]
_mat_widgets = []

# ── UI планшета (чат-мессенджер) ────────────────────────────────────────────
_tab_widgets = []
_tab_refs = {}


def _build_chat_messages():
    """Возвращает список сообщений чата — задания по крафту лодки."""
    msgs = []
    msgs.append(('in', 'Построй лодку, чтобы сбежать!'))
    pp = paper_count[0]
    sm = smelted_metal_count[0]
    rp = recycled_plastic_count[0]
    # Фазы крафта: для каждого рецепта — чертёж, потом ресурсы, потом крафт
    for recipe in CRAFT_RECIPES:
        nm = recipe['name']
        ru = recipe['ru']
        # Если деталь готова — галочка
        if crafted_parts[nm]:
            msgs.append(('in', f'[+] {ru}'))
            continue
        # Ещё нет чертежа — показать шаги к чертежу
        if not blueprints[nm]:
            if pp < 2:
                msgs.append(('in', f'[ ] Переработай 2 картона в печи ({pp}/2 бумаги)'))
                return msgs
            else:
                msgs.append(('in', f'[ ] Распечатай чертеж {ru} [E принтер]'))
                return msgs
        # Есть чертёж, нужны материалы + крафт
        mt = recipe['mat']
        cost = recipe['cost']
        have = sm if mt == 'metal' else rp
        mt_ru = 'металла' if mt == 'metal' else 'пластика'
        st_ru = 'наковальня' if recipe['station'] == 'anvil' else 'рециклер'
        if have < cost:
            verb = 'Переплавь' if mt == 'metal' else 'Переработай'
            msgs.append(('in', f'[ ] {verb} {cost} {mt_ru} ({have}/{cost})'))
            return msgs
        else:
            msgs.append(('in', f'[ ] Сделай {ru} [E {st_ru}]'))
            return msgs
    # Все детали готовы
    all_crafted = all(crafted_parts.values())
    if not all_crafted:
        return msgs
    # Фаза карты: флешка + печать
    if not map_printed[0]:
        if not usb_found[0]:
            msgs.append(('in', '[ ] Найди флешку в дальнем доме'))
            return msgs
        if pp < 2:
            msgs.append(('in', f'[ ] Переработай 2 картона ({pp}/2 бумаги)'))
            return msgs
        msgs.append(('in', '[ ] Распечатай карту [E принтер]'))
        return msgs
    msgs.append(('in', '[+] Карта'))
    # Установка на лодку
    ni = sum(1 for v in boat_parts_installed.values() if v)
    if ni < len(boat_parts_installed):
        msgs.append(('in', f'>> Установи на лодку ({ni}/{len(boat_parts_installed)}) [E]'))
    else:
        msgs.append(('in', '>> Иди к лодке и отплывай! [E]'))
    return msgs


def _open_tablet():
    global _tab_refs
    tablet_open[0] = True
    mouse.locked = False

    widgets = []
    z_bg = 0.02
    z_el = -0.01

    # Фон экрана
    bg = Entity(parent=camera.ui, model='quad', scale=(0.72, 0.94),
                texture=tex_tab_bg, color=color.white, z=z_bg)
    widgets.append(bg)

    # Шапка: полоса + имя контакта + статус
    header = Entity(parent=camera.ui, model='quad', scale=(0.72, 0.09),
                    position=(0, 0.425), texture=tex_tab_header,
                    color=color.white, z=z_bg - 0.001)
    widgets.append(header)
    contact = Text(parent=camera.ui, text='anonim contact',
                   position=(-0.33, 0.44), origin=(-0.5, 0.5), scale=1.8,
                   color=color.white, z=z_el)
    widgets.append(contact)
    online = Text(parent=camera.ui, text='в сети',
                  position=(-0.33, 0.415), origin=(-0.5, 0.5), scale=1.0,
                  color=color.rgb(100, 200, 100), z=z_el)
    widgets.append(online)

    # Сообщения чата
    msgs = _build_chat_messages()
    y_pos = 0.35
    _LINE_H = 0.026
    _PAD    = 0.018
    _GAP    = 0.016
    _MAX_IN  = 28
    _MAX_OUT = 24
    _Y_MIN = -0.40
    for direction, text in msgs:
        if y_pos < _Y_MIN:
            break
        if direction == 'in':
            max_c, bub_w = _MAX_IN, 0.50
        else:
            max_c, bub_w = _MAX_OUT, 0.45
        wrapped = textwrap.fill(text, width=max_c)
        line_count = wrapped.count('\n') + 1
        bub_h = _PAD + line_count * _LINE_H
        if direction == 'in':
            bub = Entity(parent=camera.ui, model='quad',
                         scale=(bub_w, bub_h), position=(-0.07, y_pos),
                         texture=tex_tab_bubble, color=color.white, z=z_bg - 0.002)
            txt = Text(parent=camera.ui, text=wrapped,
                       position=(-0.30, y_pos + 0.004), origin=(-0.5, 0),
                       scale=1.05, color=color.rgb(220, 225, 235), z=z_el,
                       wordwrap=0)
        else:
            bub = Entity(parent=camera.ui, model='quad',
                         scale=(bub_w, bub_h), position=(0.10, y_pos),
                         texture=tex_tab_sent, color=color.white, z=z_bg - 0.002)
            txt = Text(parent=camera.ui, text=wrapped,
                       position=(0.30, y_pos + 0.004), origin=(0.5, 0),
                       scale=1.05, color=color.white, z=z_el,
                       wordwrap=0)
        widgets.extend([bub, txt])
        y_pos -= bub_h + _GAP

    # Статус-бар внизу
    hint_txt = '[TAB] Закрыть'
    hint = Text(parent=camera.ui, text=hint_txt,
                position=(0, -0.44), origin=(0, 0), scale=1.1,
                color=color.rgb(130, 130, 130), z=z_el)
    widgets.append(hint)

    # Ошибка (пустая, заполняется при неудачной попытке)
    err = Text(parent=camera.ui, text='',
               position=(0, -0.38), origin=(0, 0), scale=1.3,
               color=color.rgb(255, 90, 90), z=z_el)
    widgets.append(err)

    _tab_widgets[:] = widgets
    _tab_refs = {'error': err, 'hint': hint}


def _close_tablet():
    tablet_open[0] = False
    mouse.locked = True
    for w in _tab_widgets:
        destroy(w)
    _tab_widgets.clear()
    _tab_refs.clear()


def _submit_tablet():
    _close_tablet()
    _open_tablet()


def _check_crafting():
    pass   # crafting now happens via explicit E-key actions


def _open_materials():
    materials_open[0] = True
    mouse.locked = False
    widgets = []
    z_bg = 0.01
    z_el = -0.02
    bg = Entity(parent=camera.ui, model='quad', scale=(0.55, 0.70),
                texture=tex_mat_bg, color=color.white, z=z_bg)
    widgets.append(bg)
    title = Text(parent=camera.ui, text='Материалы [Q]',
                 position=(0, 0.30), origin=(0, 0), scale=1.6,
                 color=color.white, z=z_el)
    widgets.append(title)
    lines = []
    # Ресурсы показываем только если > 0
    has_res = paper_count[0] > 0 or smelted_metal_count[0] > 0 or recycled_plastic_count[0] > 0
    if has_res:
        lines.append('--- Ресурсы ---')
        if paper_count[0] > 0:
            lines.append(f'  Бумага: {paper_count[0]}')
        if smelted_metal_count[0] > 0:
            lines.append(f'  Металл: {smelted_metal_count[0]}')
        if recycled_plastic_count[0] > 0:
            lines.append(f'  Пластик: {recycled_plastic_count[0]}')
        lines.append('')
    # Чертежи — только полученные
    got_blueprints = [r for r in CRAFT_RECIPES if blueprints[r['name']]]
    if got_blueprints:
        lines.append('--- Чертежи ---')
        for r in got_blueprints:
            lines.append(f'  {r["ru"]}')
        lines.append('')
    # Детали — только скрафченные
    got_parts = [r for r in CRAFT_RECIPES if crafted_parts[r['name']]]
    if got_parts:
        lines.append('--- Детали ---')
        for r in got_parts:
            lines.append(f'  {r["ru"]}')
        lines.append('')
    if usb_found[0]:
        lines.append('[+] USB-флешка')
    if map_printed[0]:
        lines.append('[+] Карта')
    if not lines:
        lines.append('Пусто')
    body = Text(parent=camera.ui, text='\n'.join(lines),
                position=(-0.22, 0.22), origin=(-0.5, 0.5), scale=1.1,
                color=color.rgb(210, 215, 225), z=z_el)
    widgets.append(body)
    _mat_widgets[:] = widgets


def _close_materials():
    materials_open[0] = False
    mouse.locked = True
    for w in _mat_widgets:
        destroy(w)
    _mat_widgets.clear()


_part_ru = {r['name']: r['ru'] for r in CRAFT_RECIPES}


def _create_boat_part(part):
    if part == 'wheel':
        boat_part_entities.append(
            Entity(model=make_textured_cylinder(), scale=(0.6, 0.08, 0.6),
                   position=(_bx, _by + 1.2, _bz - 4),
                   texture=tex_dark_wood, color=color.white))
        boat_part_entities.append(
            Entity(model='cube', scale=(0.06, 0.5, 0.06),
                   position=(_bx, _by + 1.2, _bz - 4),
                   texture=tex_dark_wood, color=color.white))
    elif part == 'sail':
        # Мачта + парус
        boat_part_entities.append(
            Entity(model=make_textured_cylinder(), scale=(0.15, 8, 0.15),
                   position=(_bx, _by + 0.3, _bz),
                   texture=tex_bark, color=color.white))
        boat_part_entities.append(
            Entity(model='quad', scale=(3, 5),
                   position=(_bx + 1.5, 5, _bz),
                   texture=tex_fabric, color=color.white, double_sided=True))
        # Верёвки
        for i in range(4):
            boat_part_entities.append(
                Entity(model='cube', scale=(0.04, 2.0, 0.04),
                       position=(_bx + 0.3 * (i - 1.5), 2 + i * 1.2,
                                 _bz + i * 0.2),
                       color=color.rgb(160, 120, 60)))
    elif part == 'anchor':
        boat_part_entities.append(
            Entity(model='cube', scale=(0.15, 0.8, 0.15),
                   position=(_bx + 1.0, _by + 0.5, _bz + 6),
                   texture=tex_dark_metal, color=color.white))
        boat_part_entities.append(
            Entity(model='cube', scale=(0.5, 0.1, 0.1),
                   position=(_bx + 1.0, _by + 0.2, _bz + 6),
                   texture=tex_dark_metal, color=color.white))
    elif part == 'compass':
        boat_part_entities.append(
            Entity(model=make_textured_cylinder(), scale=(0.3, 0.05, 0.3),
                   position=(_bx, _by + 1.3, _bz - 3.5),
                   texture=tex_metal, color=color.white))
        boat_part_entities.append(
            Entity(model='cube', scale=(0.05, 0.1, 0.05),
                   position=(_bx, _by + 1.38, _bz - 3.5),
                   color=color.red, unlit=True))
    elif part == 'oars':
        for side in [-1, 1]:
            # Весло — длинная палка + лопасть
            boat_part_entities.append(
                Entity(model='cube', scale=(0.06, 3.0, 0.06),
                       position=(_bx + side * 1.2, _by + 1.5, _bz + 0.5),
                       rotation=(0, 0, side * 25),
                       texture=tex_bark, color=color.white))
            boat_part_entities.append(
                Entity(model='cube', scale=(0.25, 0.6, 0.04),
                       position=(_bx + side * 2.0, _by + 0.3, _bz + 0.5),
                       texture=tex_bark, color=color.white))


def _start_escape():
    escape_started[0] = True
    escape_timer[0] = 0.0
    game_won[0] = True
    action_text.text = ''
    score_text.visible = False
    instructions_text.visible = False
    player.speed = 0
    player.jump_height = 0
    player.gravity = 0
    player.mouse_sensitivity = Vec2(0, 0)
    mouse.locked = True
    player.position = Vec3(_bx, _by + 1.5, _bz - 3)
    player.rotation_y = -90
    camera.rotation_x = -5
    win_text.text = 'Ты сбежал с острова!'


def _update_hud():
    collected = TRASH_COUNT - trash_remaining[0]
    parts = sum(1 for v in crafted_parts.values() if v)
    score_text.text = (f'Мусор: {collected}/{TRASH_COUNT}  |  '
                       f'Бум: {paper_count[0]}  Мет: {smelted_metal_count[0]}  '
                       f'Пл: {recycled_plastic_count[0]}  |  '
                       f'Дет: {parts}/5  |  '
                       f'Инв: {len(inventory)}/{MAX_INVENTORY}')
    _refresh_inventory_ui()

def update():
    """Boucle principale – appelée chaque frame par Ursina."""
    anim_time[0] += time.dt
    update_water()

    if anim_time[0] > 10:
        instructions_text.visible = False

    if player.y < -5:
        player.position = Vec3(0, 1.5, -20)

    border = half_island + 6
    player.x = max(-border, min(border, player.x))
    player.z = max(-border, min(border, player.z))

    if game_won[0]:
        if escape_started[0]:
            escape_timer[0] += time.dt
            if escape_timer[0] < 6:
                player.x -= time.dt * 4
            elif escape_timer[0] < 8:
                if 'overlay' not in _esc_refs:
                    ov = Entity(parent=camera.ui, model='quad', scale=(3, 3),
                                color=color.rgba(0, 0, 0, 0), z=-5)
                    ov.animate_color(color.black, duration=2)
                    _esc_refs['overlay'] = ov
            else:
                if 'credits' not in _esc_refs:
                    win_text.text = ''
                    lines = [
                        'FOREST CLEANER', '',
                        'Ты очистил остров и сбежал!',
                        f'Итоговый счёт: {score[0]} очков', '',
                        'Спасибо за игру!',
                    ]
                    ct = Text(text='\n'.join(lines), position=(0, -0.5),
                              origin=(0, 0), scale=2, color=color.white, z=-6)
                    ct.animate_y(1.5, duration=10)
                    _esc_refs['credits'] = ct
        return

    # Планшет открыт — заморозить игровую логику
    if tablet_open[0]:
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

    # Проверка посещения красного дома
    if tablet_picked_up[0] and not red_house_visited[0]:
        if distance_2d(player_pos_2d, red_house_pos) < 8.0:
            red_house_visited[0] = True

    # Vérifier proximité des machines
    d_furnace  = distance_2d(player_pos_2d, (furnace_pos.x,  furnace_pos.z))
    d_recycler = distance_2d(player_pos_2d, (recycler_pos.x, recycler_pos.z))
    d_metal    = distance_2d(player_pos_2d, (metal_pos.x,    metal_pos.z))
    near_furnace[0]  = d_furnace  < MACHINE_RANGE
    near_recycler[0] = d_recycler < MACHINE_RANGE
    near_metal[0]    = d_metal    < MACHINE_RANGE

    near_anvil[0]   = distance_2d(player_pos_2d, (_anvil_x, _anvil_z)) < ANVIL_RANGE
    near_boat[0]    = distance_2d(player_pos_2d, (_bx, _bz)) < BOAT_RANGE
    near_printer[0] = distance_2d(player_pos_2d, (_printer_x, _printer_z)) < PRINTER_RANGE

    # Lumières des machines
    furnace_light.color  = color.rgb(255, 150, 50)  if near_furnace[0]  else color.rgb(255, 80, 30)
    recycler_light.color = color.rgb(100, 255, 100) if near_recycler[0] else color.rgb(50, 200, 50)
    metal_light.color    = color.rgb(255, 200, 50)  if near_metal[0]    else color.rgb(255, 120, 0)
    printer_light.color  = color.rgb(100, 200, 255) if near_printer[0]  else color.rgb(50, 100, 200)

    # Texte d'action — construction par priorités
    has_furnace_inv  = any(i['name'] in FURNACE_NAMES  for i in inventory)
    has_recycler_inv = any(i['name'] in RECYCLER_NAMES for i in inventory)
    has_metal_inv    = any(i['name'] in METAL_NAMES    for i in inventory)

    prompts = []

    # Tablette à ramasser
    if tablet_entity_ref[0] is not None:
        d_tab = distance_2d(player_pos_2d, (tablet_entity_ref[0].x, tablet_entity_ref[0].z))
        if d_tab < TABLET_PICKUP_RANGE:
            prompts.append('[E] Взять планшет с рабочего стола')

    # Rappel planшет
    if tablet_picked_up[0] and not tablet_open[0] and not tablet_task_done[0]:
        prompts.append('[TAB] Открыть планшет с заданиями')

    # Ramasser depuis le sol
    if best_trash and len(inventory) < MAX_INVENTORY:
        prompts.append(f'[E] Подобрать {best_trash.trash_name}')
        best_trash.indicator.color = color.rgb(50, 255, 50)
        best_trash.indicator.scale = 0.25
    elif best_trash:
        prompts.append('Инвентарь полон! Отнесите на завод.')
        best_trash.indicator.color = color.rgb(255, 100, 100)
        best_trash.indicator.scale = 0.2

    # Démarrer une machine (R)
    if near_furnace[0] and furnace_pending:
        prompts.append(f'[R] Переработать картон ({len(furnace_pending)})')
    if near_recycler[0] and recycler_pending:
        prompts.append(f'[R] Переработать ({len(recycler_pending)} шт.)')
    if near_metal[0] and metal_pending:
        prompts.append(f'[R] Переплавить металл ({len(metal_pending)})')

    # Charger une machine (E)
    if near_furnace[0] and has_furnace_inv and not best_trash:
        cnt = sum(1 for i in inventory if i['name'] in FURNACE_NAMES)
        prompts.append(f'[E] Загрузить {cnt} картон(а) в печь')
    if near_recycler[0] and has_recycler_inv and not best_trash:
        cnt = sum(1 for i in inventory if i['name'] in RECYCLER_NAMES)
        prompts.append(f'[E] Загрузить {cnt} пластик(а) в рециклер')
    if near_metal[0] and has_metal_inv and not best_trash:
        cnt = sum(1 for i in inventory if i['name'] in METAL_NAMES)
        prompts.append(f'[E] Загрузить {cnt} металл(а) в плавильню')

    # Наковальня — крафт
    if near_anvil[0]:
        for recipe in CRAFT_RECIPES:
            nm = recipe['name']
            if recipe['station'] != 'anvil':
                continue
            if not blueprints[nm] or crafted_parts[nm]:
                continue
            if smelted_metal_count[0] >= recipe['cost']:
                prompts.append(f'[E] Сковать {recipe["ru"]}')
            break

    # Рециклер — крафт пластиковых деталей
    if near_recycler[0] and not recycler_pending:
        for recipe in CRAFT_RECIPES:
            nm = recipe['name']
            if recipe['station'] != 'recycler':
                continue
            if not blueprints[nm] or crafted_parts[nm]:
                continue
            if recycled_plastic_count[0] >= recipe['cost']:
                prompts.append(f'[E] Сделать {recipe["ru"]}')
            break

    # Принтер
    if near_printer[0]:
        if not all(crafted_parts.values()):
            for recipe in CRAFT_RECIPES:
                nm = recipe['name']
                if blueprints[nm]:
                    continue
                if paper_count[0] >= 2:
                    prompts.append(f'[E] Распечатать чертёж «{recipe["ru"]}»')
                break
        elif usb_found[0] and not map_printed[0] and paper_count[0] >= 2:
            prompts.append('[E] Распечатать карту')

    # Флешка
    if usb_entity_ref[0] is not None and not usb_found[0]:
        d_usb = distance_2d(player_pos_2d,
                            (usb_entity_ref[0].x, usb_entity_ref[0].z))
        if d_usb < 2.5:
            prompts.append('[E] Подобрать флешку')

    # Лодка
    if near_boat[0]:
        all_crafted = all(crafted_parts.values())
        if all_crafted and map_printed[0]:
            ni = sum(1 for v in boat_parts_installed.values() if v)
            total_parts = len(boat_parts_installed)
            if ni < total_parts:
                prompts.append(f'[E] Установить деталь ({ni}/{total_parts})')
            else:
                prompts.append('[E] Отплыть!')

    action_text.text = '\n'.join(prompts)

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
        if tablet_open[0]:
            _close_tablet()
            return
        if materials_open[0]:
            _close_materials()
            return
        application.quit()

    # ── TAB = ouvrir/fermer le planшет ──────────────────────────────────────
    if key == 'tab' and tablet_picked_up[0]:
        if tablet_open[0]:
            _close_tablet()
        else:
            _open_tablet()
        return

    # ── Q = Инвентарь материалов ────────────────────────────────────────────
    if key in ('q', 'й') and tablet_picked_up[0]:
        if materials_open[0]:
            _close_materials()
        else:
            _open_materials()
        return

    # ── Входной режим планшета ──────────────────────────────────────────────
    if tablet_open[0]:
        if key == 'e' or key == 'enter':
            _submit_tablet()
        return   # потреблять все нажатия клавиш

    if materials_open[0]:
        return

    if game_won[0]:
        return

    # ── R = DÉMARRER UNE MACHINE (traitement + score) ───────────────────────
    if key == 'r':
        # Démarrer le four (carton)
        if near_furnace[0] and furnace_pending:
            items = list(furnace_pending)
            furnace_pending.clear()
            for item in items:
                score[0] += item['points']
                processed_count[0] += 1
            paper_count[0] += len(items)
            _check_crafting()
            for vis in list(furnace_inside_items):
                destroy(vis, delay=2.5)
            invoke(furnace_inside_items.clear, delay=3.0)
            flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                           color=color.rgba(255, 150, 50, 100), z=-1)
            destroy(flash, delay=0.2)
            _update_hud()
            action_text.text = f'+{len(items)} бумага из картона (всего {paper_count[0]})'
            _check_win()
            return

        # Démarrer le recycleur (plastique / verre / caoutchouc)
        if near_recycler[0] and recycler_pending:
            items = list(recycler_pending)
            recycler_pending.clear()
            for item in items:
                score[0] += item['points']
                processed_count[0] += 1
            recycled_plastic_count[0] += len(items)
            _check_crafting()
            for vis in list(recycler_inside_items):
                destroy(vis, delay=3.0)
            invoke(recycler_inside_items.clear, delay=3.5)
            flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                           color=color.rgba(100, 255, 100, 100), z=-1)
            destroy(flash, delay=0.2)
            _update_hud()
            action_text.text = f'+{len(items)} пластик (всего {recycled_plastic_count[0]})'
            _check_win()
            return

        # Démarrer la fonderie métal (canette + bidon)
        if near_metal[0] and metal_pending:
            items = list(metal_pending)
            metal_pending.clear()
            for item in items:
                score[0] += item['points']
                processed_count[0] += 1
            smelted_metal_count[0] += len(items)
            _check_crafting()
            for vis in list(metal_inside_items):
                destroy(vis, delay=2.0)
            invoke(metal_inside_items.clear, delay=2.5)
            flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                           color=color.rgba(255, 180, 50, 100), z=-1)
            destroy(flash, delay=0.2)
            _update_hud()
            action_text.text = f'+{len(items)} металл (всего {smelted_metal_count[0]})'
            _check_win()
            return
        return

    if key != 'e':
        return

    # ── E = Взять планшет ──────────────────────────────────────────────────
    if tablet_entity_ref[0] is not None:
        d_tab = distance_2d((player.x, player.z),
                            (tablet_entity_ref[0].x, tablet_entity_ref[0].z))
        if d_tab < TABLET_PICKUP_RANGE:
            tablet_picked_up[0] = True
            destroy(tablet_entity_ref[0])
            tablet_entity_ref[0] = None
            door_blocker.disable()
            action_text.text = '[TAB] Планшет получен! Нажмите TAB для просмотра.'
            return

    # ── E = CHARGER UNE MACHINE (dépôt sans traitement) ────────────────────

    # Charger le four (carton)
    if near_furnace[0] and any(i['name'] in FURNACE_NAMES for i in inventory):
        items = [i for i in inventory if i['name'] in FURNACE_NAMES]
        for idx, item in enumerate(items):
            inventory.remove(item)
            furnace_pending.append(item)
            cx = furnace_pos.x + random.uniform(-0.5, 0.5)
            cz_v = furnace_pos.z + random.uniform(-0.4, 0.4)
            vis = Entity(model='cube', scale=(0.45, 0.28, 0.35),
                         position=(cx, 0.35 + idx * 0.32, cz_v),
                         texture=tex_cardboard, texture_scale=(1, 1),
                         color=color.white,
                         rotation_y=random.uniform(-30, 30))
            furnace_inside_items.append(vis)
        _update_hud()
        action_text.text = f'{len(items)} картон(а) загружено >> [R] переработать'
        return

    # Charger le recycleur (verre / plastique / caoutchouc)
    if near_recycler[0] and any(i['name'] in RECYCLER_NAMES for i in inventory):
        items = [i for i in inventory if i['name'] in RECYCLER_NAMES]
        _tex = {'Bouteille': tex_glass, 'Sac plastique': tex_plastic, 'Pneu': tex_rubber}
        for idx, item in enumerate(items):
            inventory.remove(item)
            recycler_pending.append(item)
            rx = recycler_pos.x + random.uniform(-0.6, 0.6)
            rz_v = recycler_pos.z + random.uniform(-0.5, 0.5)
            vis = Entity(model='cube', scale=(0.35, 0.25, 0.3),
                         position=(rx, 0.35 + idx * 0.3, rz_v),
                         texture=_tex.get(item['name'], tex_metal),
                         texture_scale=(1, 1), color=color.white,
                         rotation_y=random.uniform(-40, 40))
            recycler_inside_items.append(vis)
        _update_hud()
        action_text.text = f'{len(items)} пластик(а) загружено >> [R] переработать'
        return

    # Charger la fonderie métal (canette + bidon)
    if near_metal[0] and any(i['name'] in METAL_NAMES for i in inventory):
        items = [i for i in inventory if i['name'] in METAL_NAMES]
        _tex = {'Canette': tex_can, 'Bidon': tex_barrel}
        for idx, item in enumerate(items):
            inventory.remove(item)
            metal_pending.append(item)
            mx = metal_pos.x + random.uniform(-0.5, 0.5)
            mz_v = metal_pos.z + random.uniform(-0.4, 0.4)
            vis = Entity(model='cube', scale=(0.3, 0.25, 0.3),
                         position=(mx, 0.35 + idx * 0.3, mz_v),
                         texture=_tex.get(item['name'], tex_metal),
                         texture_scale=(1, 1), color=color.white,
                         rotation_y=random.uniform(-40, 40))
            metal_inside_items.append(vis)
        _update_hud()
        action_text.text = f'{len(items)} металл(а) загружено >> [R] переплавить'
        return

    # ── E = Ковка на наковальне ────────────────────────────────────────────
    if near_anvil[0]:
        for recipe in CRAFT_RECIPES:
            nm = recipe['name']
            if recipe['station'] != 'anvil':
                continue
            if not blueprints[nm] or crafted_parts[nm]:
                continue
            if smelted_metal_count[0] >= recipe['cost']:
                smelted_metal_count[0] -= recipe['cost']
                crafted_parts[nm] = True
                flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                               color=color.rgba(200, 200, 255, 100), z=-1)
                destroy(flash, delay=0.2)
                _update_hud()
                action_text.text = f'{recipe["ru"]} скован(а)!'
                return
            break

    # ── E = Крафт на рециклере (парус, вёсла) ─────────────────────────────
    if near_recycler[0] and not recycler_pending:
        for recipe in CRAFT_RECIPES:
            nm = recipe['name']
            if recipe['station'] != 'recycler':
                continue
            if not blueprints[nm] or crafted_parts[nm]:
                continue
            if recycled_plastic_count[0] >= recipe['cost']:
                recycled_plastic_count[0] -= recipe['cost']
                crafted_parts[nm] = True
                flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                               color=color.rgba(100, 255, 200, 100), z=-1)
                destroy(flash, delay=0.2)
                _update_hud()
                action_text.text = f'{recipe["ru"]} готов(а)!'
                return
            break

    # ── E = Принтер (чертежи / карта) ──────────────────────────────────────
    if near_printer[0]:
        if not all(crafted_parts.values()):
            # Печать чертежа
            for recipe in CRAFT_RECIPES:
                nm = recipe['name']
                if blueprints[nm]:
                    continue
                if paper_count[0] >= 2:
                    paper_count[0] -= 2
                    blueprints[nm] = True
                    flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                                   color=color.rgba(200, 255, 200, 100), z=-1)
                    destroy(flash, delay=0.2)
                    _update_hud()
                    action_text.text = f'Чертёж «{recipe["ru"]}» распечатан!'
                    return
                break
        elif usb_found[0] and not map_printed[0] and paper_count[0] >= 2:
            paper_count[0] -= 2
            map_printed[0] = True
            flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                           color=color.rgba(200, 255, 200, 100), z=-1)
            destroy(flash, delay=0.2)
            _update_hud()
            action_text.text = 'Карта распечатана!'
            return

    # ── E = Подобрать флешку ───────────────────────────────────────────────
    if usb_entity_ref[0] is not None and not usb_found[0]:
        d_usb = distance_2d((player.x, player.z),
                            (usb_entity_ref[0].x, usb_entity_ref[0].z))
        if d_usb < 2.5:
            usb_found[0] = True
            destroy(usb_entity_ref[0])
            usb_entity_ref[0] = None
            action_text.text = 'USB-флешка найдена!'
            _update_hud()
            return

    # ── E = Установка деталей на лодку / Побег ─────────────────────────────
    if near_boat[0]:
        # Установка скрафченных деталей по одной
        parts_left = [k for k, v in boat_parts_installed.items()
                      if not v and crafted_parts.get(k, False)]
        if parts_left:
            part = parts_left[0]
            boat_parts_installed[part] = True
            _create_boat_part(part)
            installed_n = sum(1 for v in boat_parts_installed.values() if v)
            flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                           color=color.rgba(100, 200, 255, 100), z=-1)
            destroy(flash, delay=0.2)
            total_parts = len(boat_parts_installed)
            if installed_n >= total_parts:
                if map_printed[0]:
                    action_text.text = 'Лодка готова! [E] Отплыть!'
                else:
                    action_text.text = f'{_part_ru[part]} установлен(а)! ({installed_n}/{total_parts}) Нужна карта!'
            else:
                action_text.text = f'{_part_ru[part]} установлен(а)! ({installed_n}/{total_parts})'
            return
        # Все установлено + карта — отплытие
        all_installed = all(boat_parts_installed.values())
        if all_installed and map_printed[0]:
            _start_escape()
            return

    # ── E = Ramasser un déchet du sol ───────────────────────────────────────
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
    pass


# ============================================================
# Lancement
# ============================================================
print("=== Forest Cleaner 3D – Prototype Ursina ===")
print(f"  {TRASH_COUNT} déchets à ramasser")
print(f"  {TREE_COUNT} arbres, {ROCK_COUNT} rochers")
print("  Contrôles: ZQSD + Souris + E")
print("=============================================")

app.run()
