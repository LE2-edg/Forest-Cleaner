================================================================
  Forest Cleaner – Dossier des modèles 3D personnalisés (.OBJ)
================================================================

STRUCTURE :
  models/           ← Fichiers OBJ chargés par le JEU  (placez vos fichiers ici)
  models/base/      ← Fichiers OBJ de BASE générés automatiquement (référence Blender)

  Si un fichier n'est PAS présent dans models/, le jeu utilise le mesh procédural.
  Les fichiers dans models/base/ sont ignorés par le jeu – ils servent uniquement
  de point de départ pour Blender.

----------------------------------------------------------------
WORKFLOW
----------------------------------------------------------------
  1. python tools/export_base_meshes.py
        → génère tous les meshes de base dans models/base/

  2. Ouvrez models/base/<nom>.obj dans Blender.
  3. Modifiez le mesh comme vous voulez.
  4. Exportez dans models/<nom>.obj  (PAS dans base/) avec les paramètres :
       Forward: Y   Up: Z
       ✓ Triangulate Faces
       ✗ Write Materials
  5. Lancez le jeu – votre modèle apparaît automatiquement.

----------------------------------------------------------------
ПАРАМЕТРЫ ИМПОРТА В BLENDER
----------------------------------------------------------------
  File > Import > Wavefront (.obj)
    Forward Axis : -Z   ← НЕ менять
    Up Axis      :  Y   ← НЕ менять  (это настройки ПО УМОЛЧАНИЮ)

  После импорта: цилиндры стоят вертикально, кубы правильные.

ПАРАМЕТРЫ ЭКСПОРТА ИЗ BLENDER
----------------------------------------------------------------
  File > Export > Wavefront (.obj)
    Forward Axis : -Z
    Up Axis      :  Y
    ✓ Triangulate Faces
    ✗ Write Materials

----------------------------------------------------------------
LISTE DES FICHIERS SUPPORTÉS
----------------------------------------------------------------

DÉCHETS (objets à ramasser sur l'île) :
  canette.obj       – Canette métallique    (scale 0.12 × 0.25 × 0.12)
  bouteille.obj     – Bouteille en verre    (scale 0.15 × 0.40 × 0.15)
  bidon.obj         – Bidon métallique      (scale 0.25 × 0.50 × 0.25)
  pneu.obj          – Pneu usagé            (scale 0.50 × 0.25 × 0.50)
  carton.obj        – Boîte en carton       (scale 0.50 × 0.30 × 0.40)
  sac_plastique.obj – Sac plastique         (scale 0.40 × 0.05 × 0.30)

NATURE :
  tree_trunk.obj    – Tronc d'arbre (cylindre, base Y=0, sommet Y=1)
  tree_leaves.obj   – Feuillage / cône (même convention Y)

ROCHERS :
  rock.obj          – Rocher principal

VOITURES :
  car_body.obj      – Carrosserie principale  (scale 2 × 1 × 4)
  car_top.obj       – Toit / habitacle        (scale 1.8 × 0.8 × 2)
  car_wheel.obj     – Roue (cylindre couché)  (scale 0.4 × 0.15 × 0.4)
================================================================
