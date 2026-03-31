"""
tools/export_base_meshes.py
===========================
Génère les meshes procéduraux du jeu au format .OBJ dans le dossier models/.
Ces fichiers sont identiques à ce qui s'affiche actuellement dans le jeu.
Ouvrez-les dans Blender, modifiez-les, réexportez – le jeu les chargera automatiquement.

Utilisation :
    python tools/export_base_meshes.py

Aucune dépendance extérieure (Python standard uniquement).
"""

import math
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'models', 'base')
os.makedirs(OUTPUT_DIR, exist_ok=True)

TAU = 2 * math.pi


# ──────────────────────────────────────────────────────────────────────────────
# Classe utilitaire OBJ
# ──────────────────────────────────────────────────────────────────────────────

class ObjMesh:
    def __init__(self):
        self.verts   = []   # [(x, y, z)]
        self.uvs     = []   # [(u, v)]
        self.normals = []   # [(nx, ny, nz)]
        self.faces   = []   # [[(vi, uvi, ni), ...]]  indices 0-based

    def v(self, x, y, z):
        self.verts.append((x, y, z))
        return len(self.verts) - 1

    def vt(self, u, v):
        self.uvs.append((u, v))
        return len(self.uvs) - 1

    def vn(self, nx, ny, nz):
        mag = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
        self.normals.append((nx/mag, ny/mag, nz/mag))
        return len(self.normals) - 1

    def tri(self, a, b, c):
        """a,b,c = (vi, uvi, ni) 0-based tuples. CCW winding = outward normal (OBJ standard)."""
        self.faces.append([a, c, b])  # swap b↔c → outward normal

    def quad(self, a, b, c, d):
        self.tri(a, b, c)
        self.tri(a, c, d)

    def save(self, filename, comment=''):
        path = os.path.join(OUTPUT_DIR, filename)
        name = os.path.splitext(filename)[0]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'# {filename} – Forest Cleaner base mesh\n')
            if comment:
                f.write(f'# {comment}\n')
            f.write('# Import Blender : File > Import > OBJ  Forward=-Z  Up=Y  (Blender default)\n')
            f.write('# Export Blender : File > Export > OBJ  Forward=-Z  Up=Y  + Triangulate Faces\n\n')
            f.write(f'o {name}\n\n')
            for x, y, z in self.verts:
                f.write(f'v {x:.6f} {y:.6f} {z:.6f}\n')
            f.write('\n')
            for u, v in self.uvs:
                f.write(f'vt {u:.6f} {v:.6f}\n')
            f.write('\n')
            for nx, ny, nz in self.normals:
                f.write(f'vn {nx:.6f} {ny:.6f} {nz:.6f}\n')
            f.write('\n')
            for face in self.faces:
                parts = ' '.join(f'{vi+1}/{ui+1}/{ni+1}' for vi, ui, ni in face)
                f.write(f'f {parts}\n')
        print(f'  ✓  {filename:<25}  {len(self.verts):>5} verts  {len(self.faces):>5} tris')
        return path


# ──────────────────────────────────────────────────────────────────────────────
# Générateurs de formes
# ──────────────────────────────────────────────────────────────────────────────

def make_cylinder(res=24, y0=0.0, y1=1.0, radius=0.5):
    """
    Cylindre axe Y, base à y0, sommet à y1, rayon = radius.
    Identique au make_textured_cylinder() du jeu.
    Convention : centrer sur l'axe (x=0, z=0), base à y=0, sommet à y=1.
    """
    m = ObjMesh()

    # ── Flanc : anneau inférieur + anneau supérieur (res+1 verts pour joint UV)
    bot_ring = []
    top_ring = []
    for i in range(res + 1):
        a = TAU * i / res
        cx, cz = math.cos(a) * radius, math.sin(a) * radius
        nx, nz = math.cos(a), math.sin(a)
        u = i / res

        vi_b = m.v(cx, y0, cz);  ui_b = m.vt(u, 0.0);  ni_b = m.vn(nx, 0.0, nz)
        vi_t = m.v(cx, y1, cz);  ui_t = m.vt(u, 1.0);  ni_t = m.vn(nx, 0.0, nz)
        bot_ring.append((vi_b, ui_b, ni_b))
        top_ring.append((vi_t, ui_t, ni_t))

    for i in range(res):
        bl, br = bot_ring[i], bot_ring[i+1]
        tl, tr = top_ring[i], top_ring[i+1]
        m.tri(bl, br, tr)
        m.tri(bl, tr, tl)

    # ── Calotte inférieure
    ni_dn = m.vn(0, -1, 0)
    cv = m.v(0.0, y0, 0.0);  cu = m.vt(0.5, 0.5)
    center = (cv, cu, ni_dn)
    cap = []
    for i in range(res):
        a = TAU * i / res
        vi = m.v(math.cos(a)*radius, y0, math.sin(a)*radius)
        ui = m.vt(0.5 + math.cos(a)*0.5, 0.5 + math.sin(a)*0.5)
        cap.append((vi, ui, ni_dn))
    for i in range(res):
        m.tri(center, cap[(i+1) % res], cap[i])

    # ── Calotte supérieure
    ni_up = m.vn(0, 1, 0)
    cv = m.v(0.0, y1, 0.0);  cu = m.vt(0.5, 0.5)
    center = (cv, cu, ni_up)
    cap = []
    for i in range(res):
        a = TAU * i / res
        vi = m.v(math.cos(a)*radius, y1, math.sin(a)*radius)
        ui = m.vt(0.5 + math.cos(a)*0.5, 0.5 + math.sin(a)*0.5)
        cap.append((vi, ui, ni_up))
    for i in range(res):
        m.tri(center, cap[i], cap[(i+1) % res])

    return m


def make_cone(res=16, y_base=0.0, y_tip=1.0, radius=0.5):
    """
    Cône axe Y, base à y_base (rayon=radius), pointe à y_tip.
    Identique au Cone() d'Ursina utilisé pour les arbres.
    """
    m = ObjMesh()
    h = y_tip - y_base

    # ── Flanc
    base_ring = []
    for i in range(res + 1):
        a = TAU * i / res
        cx, cz = math.cos(a) * radius, math.sin(a) * radius
        slope = math.sqrt(1.0 + (radius / h) ** 2)
        nx, ny, nz = math.cos(a)/slope, (radius/h)/slope, math.sin(a)/slope
        vi = m.v(cx, y_base, cz)
        ui = m.vt(i / res, 0.0)
        ni = m.vn(nx, ny, nz)
        base_ring.append((vi, ui, ni))

    for i in range(res):
        a_mid = TAU * (i + 0.5) / res
        slope = math.sqrt(1.0 + (radius / h) ** 2)
        nx, ny, nz = math.cos(a_mid)/slope, (radius/h)/slope, math.sin(a_mid)/slope
        vt_ = m.v(0.0, y_tip, 0.0)
        ut_ = m.vt((i + 0.5) / res, 1.0)
        nt_ = m.vn(nx, ny, nz)
        tip = (vt_, ut_, nt_)
        m.tri(base_ring[i], tip, base_ring[i+1])

    # ── Base
    ni_dn = m.vn(0, -1, 0)
    cv = m.v(0.0, y_base, 0.0);  cu = m.vt(0.5, 0.5)
    center = (cv, cu, ni_dn)
    cap = []
    for i in range(res):
        a = TAU * i / res
        vi = m.v(math.cos(a)*radius, y_base, math.sin(a)*radius)
        ui = m.vt(0.5 + math.cos(a)*0.5, 0.5 + math.sin(a)*0.5)
        cap.append((vi, ui, ni_dn))
    for i in range(res):
        m.tri(center, cap[(i+1) % res], cap[i])

    return m


def make_box(cx=0.0, cy=0.0, cz=0.0, sx=1.0, sy=1.0, sz=1.0):
    """
    Cube centré en (cx,cy,cz) avec dimensions sx×sy×sz.
    Identique au model='cube' d'Ursina (par défaut centré à l'origine, 1×1×1).
    """
    m = ObjMesh()
    hx, hy, hz = sx/2, sy/2, sz/2

    faces_def = [
        # ( normale,          quad de 4 sommets en CCW vu de l'extérieur )
        ((0, 1, 0),  [(-hx, hy,-hz), ( hx, hy,-hz), ( hx, hy, hz), (-hx, hy, hz)]),  # top
        ((0,-1, 0),  [(-hx,-hy, hz), ( hx,-hy, hz), ( hx,-hy,-hz), (-hx,-hy,-hz)]),  # bottom
        (( 1, 0, 0), [( hx,-hy,-hz), ( hx,-hy, hz), ( hx, hy, hz), ( hx, hy,-hz)]),  # right
        ((-1, 0, 0), [(-hx,-hy, hz), (-hx,-hy,-hz), (-hx, hy,-hz), (-hx, hy, hz)]),  # left
        ((0, 0, 1),  [(-hx,-hy, hz), ( hx,-hy, hz), ( hx, hy, hz), (-hx, hy, hz)]),  # front
        ((0, 0,-1),  [( hx,-hy,-hz), (-hx,-hy,-hz), (-hx, hy,-hz), ( hx, hy,-hz)]),  # back
    ]
    face_uvs = [(0,0),(1,0),(1,1),(0,1)]

    for (nx, ny, nz), vquad in faces_def:
        ni = m.vn(nx, ny, nz)
        vs = [m.v(cx+v[0], cy+v[1], cz+v[2]) for v in vquad]
        us = [m.vt(*uv) for uv in face_uvs]
        m.quad((vs[0],us[0],ni),(vs[1],us[1],ni),(vs[2],us[2],ni),(vs[3],us[3],ni))

    return m


def make_torus(res_maj=32, res_min=16, r_maj=0.32, r_min=0.18):
    """
    Tore (pneu) centré à l'origine, dans le plan XZ.
    Remplace le 'sphere' utilisé par défaut pour le pneu.
    r_maj + r_min ≈ 0.5 pour tenir dans un cube unitaire.
    """
    m = ObjMesh()

    grid_v = []
    grid_u = []
    grid_n = []

    for i in range(res_maj + 1):
        row_v, row_u, row_n = [], [], []
        theta = TAU * i / res_maj
        ct, st = math.cos(theta), math.sin(theta)
        for j in range(res_min + 1):
            phi = TAU * j / res_min
            cp, sp = math.cos(phi), math.sin(phi)

            x = (r_maj + r_min * cp) * ct
            y = r_min * sp                    # centré en y=0
            z = (r_maj + r_min * cp) * st

            nx, ny, nz = cp * ct, sp, cp * st

            row_v.append(m.v(x, y, z))
            row_u.append(m.vt(i / res_maj, j / res_min))
            row_n.append(m.vn(nx, ny, nz))

        grid_v.append(row_v)
        grid_u.append(row_u)
        grid_n.append(row_n)

    for i in range(res_maj):
        for j in range(res_min):
            bl = (grid_v[i][j],   grid_u[i][j],   grid_n[i][j])
            br = (grid_v[i+1][j], grid_u[i+1][j], grid_n[i+1][j])
            tl = (grid_v[i][j+1], grid_u[i][j+1], grid_n[i][j+1])
            tr = (grid_v[i+1][j+1], grid_u[i+1][j+1], grid_n[i+1][j+1])
            m.tri(bl, br, tr)
            m.tri(bl, tr, tl)

    return m


def lathe(profile, res=24):
    """
    Tourne un profil 2D [(rayon, y), ...] autour de l'axe Y.
    Génère des normales lisses à partir de la tangente du profil.
    Ajoute des bouchons bas/haut automatiquement quand r > 0.
    """
    m = ObjMesh()
    n = len(profile)
    rings = []

    for ri, (r, y) in enumerate(profile):
        if ri == 0:
            dr = profile[1][0] - profile[0][0];  dy = profile[1][1] - profile[0][1]
        elif ri == n - 1:
            dr = profile[-1][0] - profile[-2][0]; dy = profile[-1][1] - profile[-2][1]
        else:
            dr = profile[ri+1][0] - profile[ri-1][0]
            dy = profile[ri+1][1] - profile[ri-1][1]
        lg = math.sqrt(dr*dr + dy*dy) or 1.0
        nr_r = dy / lg;   nr_y = -dr / lg   # composantes de la normale sortante

        ring = []
        for i in range(res + 1):
            t = TAU * i / res
            ct, st = math.cos(t), math.sin(t)
            vi = m.v(ct * r, y, st * r)
            ui = m.vt(i / res, ri / (n - 1))
            ni = m.vn(ct * nr_r, nr_y, st * nr_r)
            ring.append((vi, ui, ni))
        rings.append(ring)

    # Faces latérales
    for ri in range(n - 1):
        for i in range(res):
            bl = rings[ri][i];     br = rings[ri][i + 1]
            tl = rings[ri+1][i];   tr = rings[ri+1][i + 1]
            m.tri(bl, br, tr)
            m.tri(bl, tr, tl)

    # Bouchon bas (normale −Y)
    r0, y0 = profile[0]
    if r0 > 0.001:
        nb = m.vn(0, -1, 0)
        cv = m.v(0, y0, 0); cu = m.vt(0.5, 0.5)
        ctr = (cv, cu, nb)
        cap = []
        for i in range(res):
            t = TAU * i / res
            vi = m.v(math.cos(t)*r0, y0, math.sin(t)*r0)
            ui = m.vt(0.5 + math.cos(t)*0.5, 0.5 + math.sin(t)*0.5)
            cap.append((vi, ui, nb))
        for i in range(res):
            m.tri(ctr, cap[(i+1) % res], cap[i])

    # Bouchon haut (normale +Y)
    r1, y1 = profile[-1]
    if r1 > 0.001:
        nt = m.vn(0, 1, 0)
        cv = m.v(0, y1, 0); cu = m.vt(0.5, 0.5)
        ctr = (cv, cu, nt)
        cap = []
        for i in range(res):
            t = TAU * i / res
            vi = m.v(math.cos(t)*r1, y1, math.sin(t)*r1)
            ui = m.vt(0.5 + math.cos(t)*0.5, 0.5 + math.sin(t)*0.5)
            cap.append((vi, ui, nt))
        for i in range(res):
            m.tri(ctr, cap[i], cap[(i+1) % res])

    return m


def make_sphere(lat=6, lon=10):
    """Sphère UV basse-poly centrée à l'origine, rayon=0.5. Base pour sculptage de rochers."""
    m = ObjMesh()
    rings = []
    for la in range(lat + 1):
        ph = math.pi * la / lat
        ring = []
        for lo in range(lon + 1):
            th = TAU * lo / lon
            x = math.sin(ph) * math.cos(th) * 0.5
            y = math.cos(ph) * 0.5
            z = math.sin(ph) * math.sin(th) * 0.5
            vi = m.v(x, y, z)
            ui = m.vt(lo / lon, la / lat)
            ni = m.vn(x*2, y*2, z*2)
            ring.append((vi, ui, ni))
        rings.append(ring)
    for la in range(lat):
        for lo in range(lon):
            bl = rings[la][lo];     br = rings[la][lo+1]
            tl = rings[la+1][lo];   tr = rings[la+1][lo+1]
            m.tri(bl, br, tr)
            m.tri(bl, tr, tl)
    return m


# ──────────────────────────────────────────────────────────────────────────────
# Export principal
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print(f'\nExport des meshes DISTINCTS → {os.path.abspath(OUTPUT_DIR)}\n')

    # ── CANETTE  (cylindre avec col resserré au sommet)
    lathe([
        (0.36, 0.00), (0.46, 0.025), (0.50, 0.065),
        (0.50, 0.820), (0.46, 0.860), (0.38, 0.920),
        (0.36, 0.960), (0.36, 1.000),
    ]).save('canette.obj',
        'Canette – FORME : corps cylindrique + col retreci au sommet | scale (0.12, 0.25, 0.12)')

    # ── BOUTEILLE  (corps rond + epaule + col long et fin)
    lathe([
        (0.37, 0.00), (0.40, 0.040), (0.40, 0.540),
        (0.35, 0.620), (0.19, 0.710), (0.18, 0.870),
        (0.21, 0.920), (0.22, 0.960), (0.20, 1.000),
    ]).save('bouteille.obj',
        'Bouteille – FORME : corps rond + epaule inclinee + col long | scale (0.15, 0.40, 0.15)')

    # ── BIDON  (cylindre avec 3 bagues horizontales)
    lathe([
        (0.40, 0.00), (0.50, 0.04),
        (0.50, 0.18), (0.54, 0.20), (0.50, 0.22),
        (0.50, 0.48), (0.54, 0.50), (0.50, 0.52),
        (0.50, 0.78), (0.54, 0.80), (0.50, 0.82),
        (0.46, 0.94), (0.38, 1.00),
    ]).save('bidon.obj',
        'Bidon – FORME : cylindre avec 3 bagues en relief | scale (0.25, 0.50, 0.25)')

    # ── CARTON / SAC  (cubes etiquetes – modifier proportions dans Blender)
    make_box().save('carton.obj',
        'Carton – boite aplatie | scale (0.50, 0.30, 0.40)')
    make_box().save('sac_plastique.obj',
        'Sac plastique – cube tres plat | scale (0.40, 0.05, 0.30)')

    # ── PNEU  (tore)
    make_torus().save('pneu.obj',
        'Pneu – FORME TORE | scale (0.50, 0.25, 0.50)')

    # ── TRONC  (cylindre effile, large en bas)
    lathe([
        (0.50, 0.00), (0.48, 0.20), (0.44, 0.50),
        (0.38, 0.80), (0.30, 1.00),
    ]).save('tree_trunk.obj',
        'Tronc – FORME : cylindre effile plus large a la base | scale (rayon, hauteur, rayon)')

    # ── FEUILLAGE  (cone effile)
    lathe([
        (0.50, 0.00), (0.48, 0.05), (0.32, 0.45),
        (0.10, 0.88), (0.01, 1.00),
    ], res=16).save('tree_leaves.obj',
        'Feuillage – FORME CONE | scale variable x3 niveaux')

    # ── ROCHER  (sphere basse-poly pour sculpter)
    make_sphere(lat=6, lon=10).save('rock.obj',
        'Rocher – SPHERE basse-poly a sculpter | scale aleatoire')

    # ── VEHICULE  (cubes etiquetes + roue avec jante)
    make_box().save('car_body.obj',
        'Carrosserie – CUBE | scale (2, 1, 4)')
    make_box().save('car_top.obj',
        'Toit cabine – CUBE | scale (1.8, 0.8, 2)')

    lathe([
        (0.50, 0.00), (0.50, 0.10),
        (0.30, 0.30), (0.20, 0.50),
        (0.30, 0.70), (0.50, 0.90),
        (0.50, 1.00),
    ]).save('car_wheel.obj',
        'Roue – FORME : jante large + creux central (moyeu) | scale (0.4, 0.15, 0.4) rot Z 90')

    print()
    print('=' * 60)
    print('Termine !')
    print()
    print('  BLENDER IMPORT : File > Import > Wavefront (.obj)')
    print('    Forward Axis : -Z    Up Axis : Y   (PAR DEFAUT)')
    print()
    print('  BLENDER EXPORT : File > Export > Wavefront (.obj)')
    print('    Forward Axis : -Z    Up Axis : Y')
    print('    [x] Triangulate Faces')
    print('    [ ] Write Materials')
    print()
    print('  Sauvegardez dans  models/  (pas dans models/base/).')
    print('=' * 60)


if __name__ == '__main__':
    main()
