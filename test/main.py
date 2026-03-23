"""
Prototype de déplacement 3D minimal avec ray casting.
Minimal 3D movement prototype using ray casting.
"""
import math
import sys
from typing import List, Tuple

import pygame

# Constantes de fenêtre / Window constants
WIDTH, HEIGHT = 960, 540
FOV = math.pi / 3  # Champ de vision / Field of view (60°)
HALF_FOV = FOV / 2
TILE_SIZE = 64
MAX_DEPTH = TILE_SIZE * 16
NUM_RAYS = WIDTH  # plus dense pour un rendu façon Doom / denser rays for a Doom-like look
DELTA_ANGLE = FOV / NUM_RAYS
DIST_PLANE = (WIDTH / 2) / math.tan(HALF_FOV)
RAY_STEP = 2
MOVE_SPEED = 180  # pixels par seconde / pixels per second
ROT_SPEED = 1.4  # radians par seconde / radians per second

# Carte simple (1 = mur, . = vide) / Simple map (1 = wall, . = empty)
WORLD_MAP: List[str] = [
    "1111111111111111111111",
    "1....................1",
    "1....HoH...o.........1",
    "1....HdH.....o.......1",
    "1....HHH....o........1",
    "1....................1",
    "1.........WWWBBWWW...1",
    "1.........W.....W....1",
    "1.........WW.WWWWW...1",
    "1.........W.....W....1",
    "1.........WWWWWWW....1",
    "1....................1",
    "1...TTTTT........o...1",
    "1...T...T.....d......1",
    "1...TTTTT....o.......1",
    "1....................1",
    "1....................1",
    "1....................1",
    "1..FFoFFFFFoF.C..o...1",
    "1..F....o....F.C..o..1",
    "1..FFoFFFFoFF.C......1",
    "1111111111111111111111",
]

Color = Tuple[int, int, int]
SKY_TOP: Color = (135, 181, 232)
SKY_BOTTOM: Color = (90, 140, 185)
FLOOR_NEAR: Color = (70, 70, 70)
FLOOR_FAR: Color = (40, 40, 40)
WALL_BASE: Color = (230, 230, 230)
FOG_COLOR: Color = (80, 100, 120)
FOG_DISTANCE = MAX_DEPTH * 0.8
MINIMAP_SCALE = 0.2
MINIMAP_TILE = int(TILE_SIZE * MINIMAP_SCALE)
TILE_COLORS: dict[str, Color] = {
    "1": (230, 230, 230),  # Bordures / island border
    "H": (205, 170, 125),  # Maison 1 étage / one-floor house
    "T": (185, 140, 95),   # Maison 2 étages / two-floor house
    "W": (80, 120, 190),   # Eau / water (lac)
    "B": (160, 120, 80),   # Pont bois / wooden bridge
    "F": (140, 140, 150),  # Usine / factory
    "C": (200, 60, 60),    # Voiture / car
    "d": (170, 110, 70),   # Porte / door
    "o": (170, 210, 235),  # Fenêtre / window
}
PASSABLE = {".", "B", "d"}


def can_move(px: float, py: float) -> bool:
    """Vérifie les collisions avec les murs / Check wall collisions."""
    grid_x = int(px // TILE_SIZE)
    grid_y = int(py // TILE_SIZE)
    if grid_y < 0 or grid_y >= len(WORLD_MAP):
        return False
    if grid_x < 0 or grid_x >= len(WORLD_MAP[0]):
        return False
    return WORLD_MAP[grid_y][grid_x] in PASSABLE


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_color(c1: Color, c2: Color, t: float) -> Color:
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)), int(lerp(c1[2], c2[2], t)))


def texture_sample(tile: str, base: Color, hx: float, hy: float, vy: float) -> Color:
    """Échantillon simple de texture procédurale / Simple procedural texturing."""
    # Coordonnées locales pour motifs / local coords for patterns
    tx = int(hx) % TILE_SIZE
    ty = int(hy) % TILE_SIZE
    r, g, b = base

    if tile in {"H", "T"}:  # briques simples
        brick = ((tx // 8) + (ty // 8)) % 2
        if brick == 0:
            r = int(r * 0.8)
            g = int(g * 0.8)
            b = int(b * 0.8)
    elif tile == "F":  # tôles verticales
        if tx % 10 < 2:
            r = int(r * 0.65)
            g = int(g * 0.65)
            b = int(b * 0.75)
    elif tile == "B":  # planches bois
        plank = (tx // 12) % 2
        if plank == 0:
            r = int(r * 0.85)
            g = int(g * 0.8)
            b = int(b * 0.75)
    elif tile == "d":  # veines bois porte
        grain = (tx % 6) < 3
        if grain:
            r = int(r * 0.75)
            g = int(g * 0.7)
            b = int(b * 0.65)
    elif tile == "o":  # reflets verre
        band = (ty // 6) % 2
        if band == 0:
            r = min(255, int(r * 1.1))
            g = min(255, int(g * 1.05))
            b = min(255, int(b * 1.15))

    # léger assombrissement vertical pour relief / vertical darkening for relief
    vshade = 0.9 + 0.1 * vy
    return (int(r * vshade), int(g * vshade), int(b * vshade))


def handle_input(dt: float, pos: Tuple[float, float], angle: float) -> Tuple[Tuple[float, float], float]:
    """Gestion des commandes ZQSD et rotation / Handle ZQSD movement and rotation."""
    keys = pygame.key.get_pressed()
    x, y = pos
    direction_x = math.cos(angle)
    direction_y = math.sin(angle)

    if keys[pygame.K_z]:
        nx = x + direction_x * MOVE_SPEED * dt
        ny = y + direction_y * MOVE_SPEED * dt
        if can_move(nx, ny):
            x, y = nx, ny
    if keys[pygame.K_s]:
        nx = x - direction_x * MOVE_SPEED * dt
        ny = y - direction_y * MOVE_SPEED * dt
        if can_move(nx, ny):
            x, y = nx, ny
    if keys[pygame.K_q]:
        angle -= ROT_SPEED * dt
    if keys[pygame.K_d]:
        angle += ROT_SPEED * dt
    return (x, y), angle


def cast_rays(screen: pygame.Surface, pos: Tuple[float, float], angle: float, t: float) -> None:
    """Dessine les murs avec un ray casting simple / Draw walls with a simple ray casting."""
    ox, oy = pos
    ray_width = WIDTH / NUM_RAYS
    for ray in range(NUM_RAYS):
        ray_angle = angle - HALF_FOV + ray * DELTA_ANGLE
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        depth = 0
        hit_tile = None
        hit_x = ox
        hit_y = oy
        while depth < MAX_DEPTH and hit_tile is None:
            depth += RAY_STEP
            target_x = ox + depth * cos_a
            target_y = oy + depth * sin_a
            map_x = int(target_x // TILE_SIZE)
            map_y = int(target_y // TILE_SIZE)
            if map_y < 0 or map_y >= len(WORLD_MAP) or map_x < 0 or map_x >= len(WORLD_MAP[0]):
                hit_tile = "1"
                hit_x, hit_y = target_x, target_y
                continue
            tile = WORLD_MAP[map_y][map_x]
            if tile != ".":
                hit_tile = tile
                hit_x, hit_y = target_x, target_y

        if hit_tile is not None:
            depth_corrected = depth * math.cos(angle - ray_angle)
            depth_corrected = max(depth_corrected, 0.0001)
            wall_height = int((TILE_SIZE / depth_corrected) * DIST_PLANE)
            wall_height = min(wall_height, HEIGHT)

            base_color = TILE_COLORS.get(hit_tile, WALL_BASE)
            if hit_tile == "W":
                wave = 0.85 + 0.15 * math.sin(t * 2.0 + hit_x * 0.02 + hit_y * 0.02)
                base_color = (int(base_color[0] * wave), int(base_color[1] * wave), int(base_color[2] * wave))

            view_shade = 0.6 + 0.4 * max(0.0, math.cos(ray_angle - angle))
            distance_shade = 1 / (1 + depth_corrected * 0.01)
            shade_factor = max(0.12, min(1.0, view_shade * distance_shade))

            fog_t = max(0.0, min(1.0, depth_corrected / FOG_DISTANCE))

            x_pos = int(ray * ray_width)
            top = HEIGHT // 2 - wall_height // 2
            bottom = HEIGHT // 2 + wall_height // 2
            for screen_y in range(top, bottom):
                vy = (screen_y - top) / max(1, wall_height)
                tex_color = texture_sample(hit_tile, base_color, hit_x, hit_y, vy)
                shaded = (
                    int(tex_color[0] * shade_factor),
                    int(tex_color[1] * shade_factor),
                    int(tex_color[2] * shade_factor),
                )
                color: Color = lerp_color(shaded, FOG_COLOR, fog_t)
                pygame.draw.line(screen, color, (x_pos, screen_y), (x_pos + math.ceil(ray_width), screen_y))


def draw_minimap(screen: pygame.Surface, pos: Tuple[float, float]) -> None:
    """Affiche une mini-carte pour s'orienter / Render a minimap to orient the player."""
    for j, row in enumerate(WORLD_MAP):
        for i, cell in enumerate(row):
            color = TILE_COLORS.get(cell, (180, 180, 180)) if cell != "." else (210, 210, 210)
            pygame.draw.rect(screen, color, (i * MINIMAP_TILE, j * MINIMAP_TILE, MINIMAP_TILE - 1, MINIMAP_TILE - 1))
    px, py = pos
    pygame.draw.circle(
        screen,
        (220, 80, 80),
        (int(px * MINIMAP_SCALE), int(py * MINIMAP_SCALE)),
        max(3, MINIMAP_TILE // 4),
    )


def draw_sky_and_floor(screen: pygame.Surface) -> None:
    """Dégradé ciel/sol pour un rendu plus doux / Gradient sky/floor for softer look."""
    half_h = HEIGHT // 2
    for y in range(half_h):
        t = y / max(1, half_h - 1)
        pygame.draw.line(screen, lerp_color(SKY_TOP, SKY_BOTTOM, t), (0, y), (WIDTH, y))
    for y in range(half_h, HEIGHT):
        t = (y - half_h) / max(1, half_h - 1)
        pygame.draw.line(screen, lerp_color(FLOOR_NEAR, FLOOR_FAR, t), (0, y), (WIDTH, y))


def draw_scene(screen: pygame.Surface, pos: Tuple[float, float], angle: float, t: float) -> None:
    """Rendu principal : ciel, sol, murs, mini-carte / Main render: sky, floor, walls, minimap."""
    draw_sky_and_floor(screen)
    cast_rays(screen, pos, angle, t)
    draw_minimap(screen, pos)


def run() -> None:
    """Boucle principale du prototype / Main loop of the prototype."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Prototype 3D - ZQSD")
    clock = pygame.time.Clock()

    player_pos = (TILE_SIZE * 1.5, TILE_SIZE * 1.5)
    player_angle = 0.0
    total_time = 0.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        total_time += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        player_pos, player_angle = handle_input(dt, player_pos, player_angle)
        draw_scene(screen, player_pos, player_angle, total_time)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
