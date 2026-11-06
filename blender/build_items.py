"""Builds the 20 memorable objects the player places in the palace.

Run with either:
    blender -b -P blender/build_items.py
    python blender/build_items.py

Each object is exported as a node named `item_<id>` (base at z=0) into
blender/.cache/models/items.glb, and a studio thumbnail is rendered with
Cycles into blender/.cache/thumbs/<id>.png (pass --no-thumbs to skip them).
`npm run assets:optimize` converts both into web-ready files under public/.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from lib import geo, materials as mt, textures as tx  # noqa: E402
from lib.geo import T, Rx, Ry, Rz, box, lathe, cylinder, sphere, torus, tube, prism  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..'))
RAW_DIR = os.path.join(HERE, '.cache', 'models')
THUMBS = os.path.join(HERE, '.cache', 'thumbs')


def D(x, y, z):
    return Matrix.Diagonal((x, y, z, 1.0))


def mushroom_tex(n=512):
    d1, _, _ = tx.voronoi(n, 26, 5)
    xs, ys = tx.grid(n)
    spots = 1 - tx.smoothstep(0.035, 0.045, d1)
    spots *= ys > 0.25
    color = tx.lerp(tx.rgb('#b3171b'), tx.rgb('#d33a2a'), tx.n01(tx.fbm(n, 2.0, 3)))
    color = tx.lerp(color, tx.rgb('#f4ecd8'), spots)
    color = tx.lerp(color, tx.rgb('#efe2c4'), (ys < 0.18).astype(float))
    return dict(color=color, rough=0.5)


def build_materials():
    M = {}
    M['apple'] = mt.make('it_apple', color='#a3161b', rough=0.3)
    M['leaf'] = mt.make('it_leaf', color='#3f7a2a', rough=0.5)
    M['wood'] = mt.make('it_wood', tx.wood_grain(n=512, seed=71), rough=0.5)
    M['gold'] = mt.make('it_gold', color='#e2b04f', rough=0.22, metal=1.0)
    M['brass'] = mt.make('it_brass', color='#c49a4a', rough=0.32, metal=1.0)
    M['bronze'] = mt.make('it_bronze', color='#a86b35', rough=0.3, metal=1.0)
    M['silver'] = mt.make('it_silver', color='#d6d8dc', rough=0.18, metal=1.0)
    M['steel'] = mt.make('it_steel', color='#9aa1a8', rough=0.25, metal=1.0)
    M['iron'] = mt.make('it_iron', color='#2b2c2f', rough=0.5, metal=0.9)
    M['wax'] = mt.make('it_wax', color='#f1e7d0', rough=0.45)
    M['flame'] = mt.make('it_flame', color='#ffd38a', emission='#ffb04a', emission_strength=14.0)
    M['leather'] = mt.make('it_leather', color='#5d1a17', rough=0.6)
    M['leather_brown'] = mt.make('it_leather_brown', color='#4a2c1a', rough=0.65)
    M['paper'] = mt.make('it_paper', color='#efe3c6', rough=0.8)
    M['velvet'] = mt.make('it_velvet', color='#6a0f1a', rough=0.9)
    M['ruby'] = mt.make('it_ruby', color='#c0102a', rough=0.05)
    M['sapphire'] = mt.make('it_sapphire', color='#1840b0', rough=0.05)
    M['emerald'] = mt.make('it_emerald', color='#118050', rough=0.05)
    M['glass'] = mt.make('it_glass', color='#e6f2f5', rough=0.03, alpha=0.25)
    M['sand'] = mt.make('it_sand', color='#d8b878', rough=0.9)
    M['terracotta'] = mt.make('it_terracotta', tx.terracotta())
    M['earth'] = mt.make('it_earth', tx.earth_map())
    M['mushroom'] = mt.make('it_mushroom', mushroom_tex())
    M['stem'] = mt.make('it_stem', color='#efe6d2', rough=0.7)
    M['ivory'] = mt.make('it_ivory', tx.dice_face())
    M['porcelain'] = mt.make('it_porcelain', color='#f4f4f0', rough=0.12)
    M['cobalt'] = mt.make('it_cobalt', color='#21468f', rough=0.15)
    M['pear'] = mt.make('it_pear', color='#b9b83f', rough=0.4)
    return M


# ---------------------------------------------------------------------------
# Items: each function receives a geo.Scene and fills it
# ---------------------------------------------------------------------------

def apple(s):
    lathe(s['apple'], [(0, 0.012), (0.03, 0.0), (0.07, 0.015), (0.094, 0.05), (0.1, 0.085), (0.092, 0.118),
                       (0.065, 0.14), (0.03, 0.136), (0.008, 0.124), (0, 0.12)], 32, sharp_deg=70)
    tube(s['wood'], [(0, 0, 0.12), (0.004, 0, 0.15), (0.012, 0, 0.175)], 0.0055, 6)
    sphere(s['leaf'], 0.03, 12, 8, T(0.032, 0, 0.165) @ Ry(-35) @ D(1.5, 0.6, 0.12))


def key(s):
    torus(s['brass'], 0.036, 0.009, 32, 8, T(0, 0, 0.205) @ Rx(90))
    torus(s['brass'], 0.014, 0.006, 20, 6, T(0, 0, 0.205) @ Rx(90))
    cylinder(s['brass'], 0.008, 0.0, 0.17, 12)
    for z in (0.15, 0.162):
        torus(s['brass'], 0.009, 0.004, 16, 6, T(0, 0, z))
    box(s['brass'], (0.006, -0.004, 0.0), (0.048, 0.004, 0.018))
    box(s['brass'], (0.006, -0.004, 0.026), (0.04, 0.004, 0.044))
    box(s['brass'], (0.03, -0.004, 0.018), (0.048, 0.004, 0.026))


def book(s):
    w, h, t = 0.17, 0.24, 0.055
    box(s['leather'], (-t / 2, -w / 2, 0), (-t / 2 + 0.006, w / 2, h))
    box(s['leather'], (t / 2 - 0.006, -w / 2, 0), (t / 2, w / 2, h))
    lathe(s['leather'], [(t / 2, 0), (t / 2, h)], 16, T(0, -w / 2, 0), arc=(math.pi / 2, 3 * math.pi / 2),
          cap_bottom=False, cap_top=False)
    box(s['paper'], (-t / 2 + 0.006, -w / 2 - 0.004, 0.006), (t / 2 - 0.006, w / 2 - 0.006, h - 0.006))
    for z in (0.05, h - 0.05):
        lathe(s['gold'], [(t / 2 + 0.001, z - 0.006), (t / 2 + 0.001, z + 0.006)], 16, T(0, -w / 2, 0),
              arc=(math.pi / 2, 3 * math.pi / 2), cap_bottom=False, cap_top=False)
    for zz in (0, h - 0.025):
        box(s['gold'], (-t / 2 - 0.002, w / 2 - 0.03, zz), (t / 2 + 0.002, w / 2 + 0.002, zz + 0.025))
    sphere(s['gold'], 0.018, 16, 8, T(t / 2 + 0.001, 0, h / 2) @ D(0.25, 1, 1))


def candle(s):
    lathe(s['brass'], [(0, 0), (0.075, 0), (0.08, 0.012), (0.07, 0.016), (0.03, 0.022), (0.02, 0.05),
                       (0.036, 0.06), (0.03, 0.062)], 32)
    torus(s['brass'], 0.022, 0.005, 16, 6, T(0.085, 0, 0.012) @ Rx(90))
    cylinder(s['wax'], 0.022, 0.06, 0.24, 20)
    for a, z in ((0.3, 0.2), (2.1, 0.17), (4.0, 0.21)):
        sphere(s['wax'], 0.007, 8, 6, T(0.022 * math.cos(a), 0.022 * math.sin(a), z) @ D(1, 1, 3))
    cylinder(s['iron'], 0.0015, 0.24, 0.255, 4)
    lathe(s['flame'], [(0, 0.248), (0.012, 0.262), (0.014, 0.278), (0.007, 0.3), (0, 0.32)], 12, sharp_deg=80)


def crown(s):
    lathe(s['gold'], [(0.095, 0.0), (0.104, 0.0), (0.104, 0.06), (0.095, 0.06), (0.095, 0.0)], 40, sharp_deg=20)
    for k in range(8):
        a = 2 * math.pi * k / 8
        x, y = 0.1 * math.cos(a), 0.1 * math.sin(a)
        lathe(s['gold'], [(0.016, 0), (0.0, 0.065)], 10, T(x, y, 0.058))
        sphere(s['silver' if k % 2 else 'gold'], 0.009, 10, 6, T(x, y, 0.128))
        gem = ('ruby', 'sapphire', 'emerald', 'ruby')[k % 4]
        sphere(s[gem], 0.011, 10, 6, T(x * 1.04, y * 1.04, 0.03) @ Rz(math.degrees(a)) @ D(0.5, 1, 1))
    sphere(s['velvet'], 0.093, 24, 12, T(0, 0, 0.055) @ D(1, 1, 0.9))
    for k in range(2):
        a = math.pi / 2 * k
        torus(s['gold'], 0.095, 0.006, 24, 6, T(0, 0, 0.055) @ Rz(math.degrees(a)) @ Rx(90), arc=math.pi)
    lathe(s['gold'], [(0.018, 0.14), (0.0, 0.16)], 10)
    box(s['gold'], (-0.004, -0.004, 0.155), (0.004, 0.004, 0.2))
    box(s['gold'], (-0.017, -0.004, 0.175), (0.017, 0.004, 0.183))


def hourglass(s):
    for z in (0.0, 0.225):
        cylinder(s['wood'], 0.075, z, z + 0.018, 6)
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 6
        cylinder(s['wood'], 0.007, 0.018, 0.225, 8, T(0.06 * math.cos(a), 0.06 * math.sin(a)))
    lathe(s['sand'], [(0, 0.018), (0.046, 0.022), (0.03, 0.05), (0, 0.068)], 20)
    lathe(s['sand'], [(0, 0.15), (0.032, 0.152), (0.008, 0.125), (0, 0.12)], 20, cap_bottom=False)
    cylinder(s['sand'], 0.0025, 0.06, 0.125, 6)
    lathe(s['glass'], [(0.0, 0.018), (0.05, 0.022), (0.056, 0.065), (0.012, 0.12), (0.056, 0.175),
                       (0.05, 0.222), (0.0, 0.225)], 24, sharp_deg=50)


def sword(s):
    blade = [(-0.022, 0.0), (0.022, 0.0), (0.019, 0.38), (0.0, 0.44), (-0.019, 0.38)]
    prism(s['steel'], blade, -0.004, 0.004, M=T(0, 0, 0.125) @ Rx(90))
    box(s['steel'], (-0.004, -0.0045, 0.13), (0.004, 0.0045, 0.48))
    box(s['gold'], (-0.095, -0.013, 0.105), (0.095, 0.013, 0.125))
    for sx in (-1, 1):
        sphere(s['gold'], 0.014, 12, 8, T(sx * 0.098, 0, 0.115))
    lathe(s['leather_brown'], [(0.013, 0.025), (0.015, 0.06), (0.013, 0.105)], 12)
    for z in (0.04, 0.06, 0.08):
        torus(s['gold'], 0.0145, 0.002, 12, 4, T(0, 0, z))
    sphere(s['gold'], 0.022, 14, 10, T(0, 0, 0.022))


def bell(s):
    lathe(s['bronze'], [(0.0, 0.2), (0.04, 0.198), (0.055, 0.17), (0.06, 0.12), (0.075, 0.06), (0.1, 0.02),
                        (0.106, 0.0), (0.096, 0.0), (0.09, 0.016), (0.068, 0.06), (0.052, 0.12),
                        (0.046, 0.168), (0.032, 0.188), (0.0, 0.19)], 36, sharp_deg=50)
    lathe(s['wood'], [(0.014, 0.2), (0.011, 0.25), (0.02, 0.29), (0.016, 0.31), (0.0, 0.315)], 16)
    sphere(s['iron'], 0.018, 12, 8, T(0, 0, 0.035))
    cylinder(s['iron'], 0.003, 0.05, 0.19, 6)
    for r, z in ((0.098, 0.03), (0.0615, 0.13)):
        lathe(s['bronze'], [(r, z - 0.004), (r + 0.004, z), (r, z + 0.004)], 36, cap_bottom=False, cap_top=False)


def amphora(s):
    lathe(s['terracotta'], [(0.0, 0.0), (0.04, 0.0), (0.05, 0.02), (0.035, 0.04), (0.065, 0.08),
                            (0.1, 0.16), (0.11, 0.22), (0.095, 0.3), (0.05, 0.36), (0.04, 0.4), (0.05, 0.42),
                            (0.048, 0.43), (0.035, 0.43), (0.03, 0.4)], 32, uv_unit=True, cap_top=False, sharp_deg=50)
    for sx in (-1, 1):
        tube(s['terracotta'], [(sx * 0.042, 0, 0.395), (sx * 0.085, 0, 0.405), (sx * 0.1, 0, 0.37),
                               (sx * 0.09, 0, 0.32)], 0.009, 8)


def chalice(s):
    lathe(s['gold'], [(0, 0), (0.065, 0), (0.068, 0.01), (0.035, 0.025), (0.013, 0.06), (0.012, 0.12),
                      (0.026, 0.13), (0.012, 0.142), (0.015, 0.16), (0.05, 0.188), (0.066, 0.235),
                      (0.069, 0.275), (0.063, 0.275), (0.059, 0.24), (0.044, 0.2), (0, 0.192)], 36, sharp_deg=50)
    for k in range(4):
        a = 2 * math.pi * k / 4
        gem = ('ruby', 'sapphire')[k % 2]
        sphere(s[gem], 0.011, 10, 6, T(0.062 * math.cos(a), 0.062 * math.sin(a), 0.235)
               @ Rz(math.degrees(a)) @ D(0.5, 1, 1))
        sphere(s['ruby'], 0.008, 8, 6, T(0.026 * math.cos(a + 0.7), 0.026 * math.sin(a + 0.7), 0.13))


def anchor(s):
    cylinder(s['iron'], 0.012, 0.04, 0.33, 12)
    torus(s['iron'], 0.026, 0.007, 20, 8, T(0, 0, 0.355) @ Rx(90))
    box(s['iron'], (-0.075, -0.01, 0.28), (0.075, 0.01, 0.3))
    for sx in (-1, 1):
        sphere(s['iron'], 0.013, 10, 6, T(sx * 0.078, 0, 0.29))
    pts = []
    for i in range(17):
        a = math.radians(200 + 140 * i / 16)
        pts.append((0.11 * math.cos(a), 0, 0.13 + 0.11 * math.sin(a)))
    tube(s['iron'], pts, 0.012, 10)
    for sx in (-1, 1):
        p = pts[0] if sx < 0 else pts[-1]
        prism(s['iron'], [(0.0, -0.03), (0.022, 0.03), (-0.022, 0.03)], -0.006, 0.006,
              M=T(p[0], 0, p[2] + 0.01) @ Rx(90) @ Rz(sx * 30))


def globe(s):
    lathe(s['wood'], [(0, 0), (0.08, 0.0), (0.08, 0.015), (0.05, 0.03), (0.02, 0.04), (0.015, 0.06)], 24)
    cylinder(s['brass'], 0.008, 0.06, 0.075, 10)
    G = T(0, 0, 0.18) @ Ry(23)
    sphere(s['earth'], 0.1, 40, 20, G, uv_unit=True)
    torus(s['brass'], 0.108, 0.005, 40, 6, G @ Rx(90), arc=math.pi * 1.2)
    cylinder(s['brass'], 0.004, -0.112, 0.112, 6, G)


def lantern(s):
    box(s['iron'], (-0.07, -0.07, 0), (0.07, 0.07, 0.02))
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(s['iron'], (sx * 0.06 - 0.006, sy * 0.06 - 0.006, 0.02), (sx * 0.06 + 0.006, sy * 0.06 + 0.006, 0.2))
    box(s['iron'], (-0.07, -0.07, 0.2), (0.07, 0.07, 0.215))
    lathe(s['iron'], [(0.1, 0.215), (0.0, 0.29)], 4, Rz(45), sharp_deg=10)
    torus(s['iron'], 0.025, 0.005, 16, 6, T(0, 0, 0.31) @ Rx(90))
    for (a, b) in (((-0.055, -0.058, 0.02), (0.055, -0.056, 0.2)), ((-0.055, 0.056, 0.02), (0.055, 0.058, 0.2)),
                   ((-0.058, -0.055, 0.02), (-0.056, 0.055, 0.2)), ((0.056, -0.055, 0.02), (0.058, 0.055, 0.2))):
        box(s['glass'], a, b)
    cylinder(s['wax'], 0.018, 0.02, 0.09, 16)
    lathe(s['flame'], [(0, 0.09), (0.011, 0.102), (0.013, 0.118), (0.006, 0.138), (0, 0.155)], 12, sharp_deg=80)


def mushroom(s):
    lathe(s['stem'], [(0.042, 0), (0.046, 0.012), (0.032, 0.05), (0.033, 0.106)], 24, cap_top=False)
    lathe(s['mushroom'], [(0.03, 0.1), (0.115, 0.108), (0.126, 0.125), (0.108, 0.165), (0.062, 0.19),
                          (0.0, 0.197)], 36, uv_unit=True, cap_bottom=True, sharp_deg=60)


def ring(s):
    torus(s['gold'], 0.05, 0.011, 40, 10, T(0, 0, 0.062) @ Rx(90))
    lathe(s['gold'], [(0.012, 0.105), (0.02, 0.118)], 8, cap_bottom=True, cap_top=False)
    lathe(s['ruby'], [(0, 0.11), (0.024, 0.122), (0.02, 0.134), (0, 0.138)], 8, sharp_deg=10)


def dice(s):
    a = 0.12
    cells = {1: '+z', 6: '-z', 2: '+x', 5: '-x', 3: '+y', 4: '-y'}
    faces = {
        '+x': ([(a, 0, 0), (a, a, 0), (a, a, a), (a, 0, a)], (1, 0, 0)),
        '-x': ([(0, a, 0), (0, 0, 0), (0, 0, a), (0, a, a)], (-1, 0, 0)),
        '+y': ([(a, a, 0), (0, a, 0), (0, a, a), (a, a, a)], (0, 1, 0)),
        '-y': ([(0, 0, 0), (a, 0, 0), (a, 0, a), (0, 0, a)], (0, -1, 0)),
        '+z': ([(0, 0, a), (a, 0, a), (a, a, a), (0, a, a)], (0, 0, 1)),
        '-z': ([(0, a, 0), (a, a, 0), (a, 0, 0), (0, 0, 0)], (0, 0, -1)),
    }
    M = T(-a / 2, -a / 2, 0)
    for num, key_ in cells.items():
        pts, n = faces[key_]
        u0, v0 = ((num - 1) % 3) / 3.0, ((num - 1) // 3) / 2.0
        uvs = [(u0, v0), (u0 + 1 / 3, v0), (u0 + 1 / 3, v0 + 0.5), (u0, v0 + 0.5)]
        s['ivory'].poly([M @ Vector(p) for p in pts], uvs, [n] * 4)


def teapot(s):
    lathe(s['porcelain'], [(0, 0), (0.06, 0), (0.065, 0.008), (0.1, 0.035), (0.112, 0.075), (0.1, 0.112),
                           (0.07, 0.136), (0.046, 0.14)], 36, cap_top=False, sharp_deg=50)
    lathe(s['cobalt'], [(0.1125, 0.065), (0.1135, 0.075), (0.1125, 0.085)], 36, cap_bottom=False, cap_top=False)
    lathe(s['porcelain'], [(0.05, 0.136), (0.05, 0.146), (0.036, 0.162), (0.012, 0.166), (0.014, 0.176),
                           (0.016, 0.186), (0.0, 0.192)], 28, sharp_deg=50)
    tube(s['porcelain'], [(0.09, 0, 0.045), (0.125, 0, 0.07), (0.15, 0, 0.11), (0.172, 0, 0.14)], 0.012, 10)
    tube(s['porcelain'], [(-0.098, 0, 0.115), (-0.135, 0, 0.12), (-0.155, 0, 0.09), (-0.14, 0, 0.055),
                          (-0.1, 0, 0.04)], 0.009, 8)


def horseshoe(s):
    pts = []
    for i in range(25):
        a = math.radians(160 + 220 * i / 24)
        pts.append((0.085 * math.cos(a), 0, 0.1 + 0.09 * math.sin(a)))
    tube(s['iron'], pts, 0.014, 8)
    for i in (4, 7, 17, 20):
        p = Vector(pts[i])
        sphere(s['steel'], 0.006, 8, 6, T(p.x, -0.012, p.z))


def pear(s):
    lathe(s['pear'], [(0, 0.004), (0.04, 0.004), (0.064, 0.03), (0.07, 0.06), (0.058, 0.1), (0.04, 0.135),
                      (0.032, 0.165), (0.018, 0.188), (0, 0.194)], 32, sharp_deg=70)
    tube(s['wood'], [(0, 0, 0.19), (0.004, 0, 0.215), (0.014, 0, 0.235)], 0.005, 6)
    sphere(s['leaf'], 0.028, 12, 8, T(-0.025, 0, 0.215) @ Ry(40) @ D(1.5, 0.6, 0.12))


def hammer(s):
    lathe(s['wood'], [(0.016, 0), (0.017, 0.02), (0.014, 0.15), (0.013, 0.29)], 14)
    H = T(0, 0, 0.3) @ Ry(90)
    cylinder(s['steel'], 0.024, -0.055, 0.035, 20, H)
    lathe(s['steel'], [(0.03, 0.035), (0.03, 0.06)], 20, H)
    prism(s['steel'], [(0.0, -0.022), (0.075, -0.004), (0.075, 0.004), (0.0, 0.022)], -0.018, 0.018,
          M=T(-0.055, 0, 0.3) @ Rz(180) @ Rx(90))


ITEMS = ['apple', 'key', 'book', 'candle', 'crown', 'hourglass', 'sword', 'bell', 'amphora', 'chalice',
         'anchor', 'globe', 'lantern', 'mushroom', 'ring', 'dice', 'teapot', 'horseshoe', 'pear', 'hammer']


def render_thumbs(roots):
    os.makedirs(THUMBS, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = 256
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Punchy'
    world = bpy.data.worlds.new('studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.48, 0.45, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
    scene.world = world
    for name, loc, energy, size in (('key', (0.6, -0.8, 1.0), 120, 0.6), ('fill', (-1.0, -0.4, 0.5), 40, 1.0),
                                    ('rim', (0.0, 1.0, 0.9), 80, 0.5)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.size = size
        ob = bpy.data.objects.new(name, ld)
        ob.location = loc
        ob.rotation_euler = (-Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        scene.collection.objects.link(ob)
    cam_d = bpy.data.cameras.new('cam')
    cam_d.lens = 85
    cam = bpy.data.objects.new('cam', cam_d)
    scene.collection.objects.link(cam)
    scene.camera = cam
    for item, root in roots.items():
        for other in roots.values():
            for ch in other.children:
                ch.hide_render = other is not root
        pts = [ch.matrix_world @ Vector(c) for ch in root.children for c in ch.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        center = (lo + hi) / 2
        radius = (hi - lo).length / 2
        dist = radius / math.tan(cam_d.angle / 2) * 1.08
        d = Vector((0.55, -1.0, 0.45)).normalized()
        cam.location = center + d * dist
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(THUMBS, f'{item}.png')
        bpy.ops.render.render(write_still=True)
        print('thumb', item)


def main():
    mt.reset_scene()
    mats = build_materials()
    roots = {}
    for item in ITEMS:
        root = bpy.data.objects.new(f'item_{item}', None)
        bpy.context.scene.collection.objects.link(root)
        s = geo.Scene()
        globals()[item](s)
        s.build(mats, prefix=f'{item}_', parent=root)
        roots[item] = root
    os.makedirs(RAW_DIR, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(RAW_DIR, 'items.glb'), export_format='GLB',
                              export_yup=True, export_lights=False, export_cameras=False,
                              export_image_format='AUTO')
    print(f'Exported {len(roots)} items')
    if '--no-thumbs' not in sys.argv:
        render_thumbs(roots)


if __name__ == '__main__':
    main()
