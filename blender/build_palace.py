"""Builds the memory palace and exports it for the game.

Run with either:
    blender -b -P blender/build_palace.py
    python blender/build_palace.py          (with the `bpy` module installed)

Outputs:
    blender/.cache/models/palace.glb  raw export (run `npm run assets:optimize`
                                      to produce public/models/palace.glb)
    public/models/palace.json  loci, lights, colliders, rooms, spawn point

Blender works Z-up; the JSON is written in glTF/three.js coordinates
(Y-up): (x, y, z)_blender -> (x, z, -y)_three.
"""

import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

from lib import geo, materials as mt, textures as tx  # noqa: E402
from lib.geo import T, Rz, Rx, box, lathe, cylinder, sphere, torus, tube  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..'))
OUT_DIR = os.path.join(ROOT, 'public', 'models')
RAW_DIR = os.path.join(HERE, '.cache', 'models')

WT = 0.5          # wall thickness
HW = WT / 2

rng = random.Random(42)
sc = geo.Scene()
LIGHTS = []
LOCI = []
COLLIDERS = []


def to3(x, y, z=0.0):
    return [round(x, 4), round(z, 4), round(-y, 4)]


def col_rect(x0, y0, x1, y1):
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    COLLIDERS.append({'type': 'rect', 'min': [round(x0, 3), round(-y1, 3)],
                      'max': [round(x1, 3), round(-y0, 3)]})


def col_circle(x, y, r):
    COLLIDERS.append({'type': 'circle', 'c': [round(x, 3), round(-y, 3)], 'r': round(r, 3)})


def light(x, y, z, color='#ffb46b', intensity=20.0, distance=12.0, flicker=False, shadow=False):
    LIGHTS.append({'pos': to3(x, y, z), 'color': color, 'intensity': intensity,
                   'distance': distance, 'flicker': flicker, 'shadow': shadow})


def locus(room, place, x, y, z, radius=0.6):
    LOCI.append({'id': len(LOCI) + 1, 'room': room, 'place': place,
                 'pos': to3(x, y, z), 'radius': radius})


def frame(px, py, n, z=0.0):
    """Matrix whose local -Y points along n (into the room), origin on the wall."""
    ang = {(0, 1): 180, (0, -1): 0, (1, 0): 90, (-1, 0): -90}[n]
    return T(px, py, z) @ Rz(ang)


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

def build_materials():
    M = {}
    M['floor_marble'] = mt.make('floor_marble', tx.marble_checker(seed=1), normal_strength=1.0)
    M['floor_hall'] = mt.make('floor_hall', tx.marble_checker(seed=31))
    M['floor_wood'] = mt.make('floor_wood', tx.wood_planks(seed=2))
    M['floor_gallery'] = mt.make('floor_gallery', tx.wood_planks(seed=22, rows=14, tint=('#b0814f', '#7f5531')))
    M['plaster'] = mt.make('plaster', tx.plaster(seed=4))
    M['plaster_red'] = mt.make('plaster_red', tx.plaster(seed=24, base=('#7c2a24', '#6a211c')))
    M['plaster_green'] = mt.make('plaster_green', tx.plaster(seed=25, base=('#3f5a48', '#344c3c')))
    M['ceiling'] = mt.make('ceiling', tx.plaster(seed=44, base=('#efe7d8', '#e0d5c2')))
    M['stone_wall'] = mt.make('stone_wall', tx.stone_blocks(seed=7))
    M['limestone'] = mt.make('limestone', tx.limestone(seed=6))
    M['marble_white'] = mt.make('marble_white', tx.marble_plain(seed=5))
    M['marble_green'] = mt.make('marble_green', tx.marble_plain(seed=55, base=('#2e463b', '#1d2e27'), vein='#cfd8cc'))
    M['wood_dark'] = mt.make('wood_dark', tx.wood_grain(seed=3))
    M['wood_panel'] = mt.make('wood_panel', tx.wood_grain(seed=33, tint=('#7a4a2a', '#4a2a17')))
    M['grass'] = mt.make('grass', tx.grass(seed=8))
    M['flagstones'] = mt.make('flagstones', tx.flagstones(seed=9))
    M['leaves'] = mt.make('leaves', tx.leaves(seed=10))
    M['bark'] = mt.make('bark', tx.bark(seed=11))
    M['carpet'] = mt.make('carpet', tx.carpet(seed=12))
    M['rug'] = mt.make('rug', tx.carpet(seed=13, base='#1f3b5a', trim='#d8b56a'))
    M['banner'] = mt.make('banner', tx.banner(seed=13))
    for i in range(4):
        M[f'painting_{i}'] = mt.make(f'painting_{i}', tx.painting(i + 1))
    M['gold'] = mt.make('gold', color='#d9aa52', rough=0.28, metal=1.0)
    M['iron'] = mt.make('iron', color='#2a2a2c', rough=0.55, metal=0.9)
    M['bronze'] = mt.make('bronze', color='#a8743f', rough=0.35, metal=1.0)
    M['velvet'] = mt.make('velvet', color='#6e1219', rough=0.85)
    M['velvet_blue'] = mt.make('velvet_blue', color='#1d2f52', rough=0.85)
    M['wax'] = mt.make('wax', color='#efe5cf', rough=0.45)
    M['flame'] = mt.make('flame', color='#ffcf7a', emission='#ffb04a', emission_strength=12.0)
    M['ember'] = mt.make('ember', color='#5a1a06', emission='#ff5a14', emission_strength=4.0, rough=0.9)
    M['water'] = mt.make('water', color='#20404a', rough=0.04)
    M['glass'] = mt.make('glass', color='#cfe3ea', rough=0.05, alpha=0.18)
    M['terracotta'] = mt.make('terracotta', color='#a5522d', rough=0.8)
    M['soil'] = mt.make('soil', color='#3b2a1d', rough=1.0)
    M['ground'] = mt.make('ground', tx.grass(seed=81))
    M['roof'] = mt.make('roof', color='#6b5b4b', rough=0.9)
    for name, col in [('book_red', '#7a1d1d'), ('book_green', '#244a2f'), ('book_blue', '#1f3355'),
                      ('book_brown', '#5a3a22'), ('book_ochre', '#a07a2a'), ('book_black', '#1d1b1a')]:
        M[name] = mt.make(name, color=col, rough=0.65)
    return M


BOOKS = ['book_red', 'book_green', 'book_blue', 'book_brown', 'book_ochre', 'book_black']

# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------

ROOMS = [
    dict(id='vestibule', x=(-6, 6), y=(0, 12), h=6.0, floor='floor_marble', floor_tile=2.0),
    dict(id='library', x=(6, 18), y=(0, 12), h=5.5, floor='floor_wood', floor_tile=2.0),
    dict(id='courtyard', x=(6, 18), y=(12, 24), h=None, floor='grass', floor_tile=2.0),
    dict(id='gallery', x=(-6, 6), y=(12, 24), h=5.5, floor='floor_gallery', floor_tile=2.0),
    dict(id='hall', x=(-6, 6), y=(24, 38), h=8.0, floor='floor_hall', floor_tile=3.0),
]

SIDE_STYLE = {
    # wall material, (wainscot material, height) or None, baseboard material, plinth
    'vestibule': dict(wall='plaster', wains=('marble_green', 1.0), base='marble_white', cornice=True),
    'library': dict(wall='plaster_green', wains=None, base='wood_dark', cornice=True),
    'gallery': dict(wall='plaster_red', wains=('wood_panel', 0.95), base='wood_dark', cornice=True),
    'hall': dict(wall='stone_wall', wains=('wood_panel', 1.4), base='wood_dark', cornice=True),
    'courtyard': dict(wall='stone_wall', wains=None, base=None, plinth=True),
    'ext': dict(wall='stone_wall', wains=None, base=None, plinth=True),
}
ROOM_H = {r['id']: (r['h'] or 6.0) for r in ROOMS}
ROOM_H['ext'] = 6.0


def wall(axis, c, s0, s1, h, left, right, openings=()):
    """Axis-aligned wall.

    axis='x': wall runs along x at y=c; left = south (-y) side, right = north.
    axis='y': wall runs along y at x=c; left = west (-x) side, right = east.
    openings: dicts with a, b (along the wall), bottom, top, door(bool), passable.
    """
    s0e, s1e = s0 - HW, s1 + HW
    ops = sorted(openings, key=lambda o: o['a'])
    pieces = []  # (sa, sb, z0, z1, full)
    cur = s0e
    for o in ops:
        pieces.append((cur, o['a'], 0.0, h, True))
        if o['bottom'] > 0:
            pieces.append((o['a'], o['b'], 0.0, o['bottom'], False))
        pieces.append((o['a'], o['b'], o['top'], h, False))
        cur = o['b']
    pieces.append((cur, s1e, 0.0, h, True))

    lm = SIDE_STYLE[left]['wall']
    rm = SIDE_STYLE[right]['wall']

    def bx(sa, sb, z0, z1, d0, d1):
        """Box in wall-local (s along, d across) coords -> world lo/hi."""
        if axis == 'x':
            return (sa, c + d0, z0), (sb, c + d1, z1)
        return (c + d0, sa, z0), (c + d1, sb, z1)

    pos = '+y' if axis == 'x' else '+x'
    for sa, sb, z0, z1, full in pieces:
        if sb - sa < 1e-4:
            continue
        lo, hi = bx(sa, sb, z0, z1, -HW, HW)
        box(sc[lm], lo, hi, tile=2.0, skip=(pos,))
        box(sc[rm], lo, hi, tile=2.0, skip=tuple(k for k in ('+x', '-x', '+y', '-y', '+z', '-z') if k != pos))

    # colliders: everything except passable openings
    cur = s0e
    for o in ops:
        if o.get('passable'):
            lo, hi = bx(cur, o['a'], 0, 1, -HW, HW)
            col_rect(lo[0], lo[1], hi[0], hi[1])
            cur = o['b']
    lo, hi = bx(cur, s1e, 0, 1, -HW, HW)
    col_rect(lo[0], lo[1], hi[0], hi[1])

    # trims on both sides
    for side, sign in ((left, -1), (right, 1)):
        st = SIDE_STYLE[side]
        face = sign * HW
        for sa, sb, z0, z1, full in pieces:
            if not full:
                continue
            sa2 = max(sa, s0 + HW) if sa <= s0e + 1e-6 else sa
            sb2 = min(sb, s1 - HW) if sb >= s1e - 1e-6 else sb
            if sb2 - sa2 < 0.05:
                continue
            if st.get('wains'):
                m, wh = st['wains']
                lo, hi = bx(sa2, sb2, 0, wh, face, face + sign * 0.03)
                box(sc[m], lo, hi, tile=1.0)
                lo, hi = bx(sa2, sb2, wh, wh + 0.06, face, face + sign * 0.06)
                box(sc['wood_dark' if m != 'marble_green' else 'marble_white'], lo, hi, tile=1.0)
            if st.get('base'):
                lo, hi = bx(sa2, sb2, 0, 0.16, face, face + sign * 0.05)
                box(sc[st['base']], lo, hi, tile=1.0)
            if st.get('plinth'):
                lo, hi = bx(sa2, sb2, 0, 0.45, face, face + sign * 0.07)
                box(sc['limestone'], lo, hi, tile=1.0)
        if st.get('cornice'):
            rh = ROOM_H[side]
            a2, b2 = s0 + HW, s1 - HW
            lo, hi = bx(a2, b2, rh - 0.3, rh, face, face + sign * 0.12)
            box(sc['limestone'], lo, hi, tile=1.0)
            lo, hi = bx(a2, b2, rh - 0.42, rh - 0.3, face, face + sign * 0.06)
            box(sc['limestone'], lo, hi, tile=1.0)

    # opening dressing
    for o in ops:
        a, b, bot, top = o['a'], o['b'], o['bottom'], o['top']
        if o.get('door'):
            for sign in (-1, 1):
                face = sign * HW
                for s_lo, s_hi in ((a - 0.22, a), (b, b + 0.22)):
                    lo, hi = bx(s_lo, s_hi, 0, top, face, face + sign * 0.07)
                    box(sc['limestone'], lo, hi, tile=1.0)
                lo, hi = bx(a - 0.3, b + 0.3, top, top + 0.3, face, face + sign * 0.1)
                box(sc['limestone'], lo, hi, tile=1.0)
            lo, hi = bx(a, b, -0.2, 0.012, -HW, HW)
            box(sc['limestone'], lo, hi, tile=1.0)
        else:
            lo, hi = bx(a - 0.1, b + 0.1, bot - 0.1, bot, -HW - 0.08, HW + 0.08)
            box(sc['limestone'], lo, hi, tile=1.0)
            mid = (a + b) / 2
            lo, hi = bx(mid - 0.03, mid + 0.03, bot, top, -0.03, 0.03)
            box(sc['iron'], lo, hi)
            for zz in (bot + (top - bot) * 0.35, bot + (top - bot) * 0.7):
                lo, hi = bx(a, b, zz - 0.025, zz + 0.025, -0.03, 0.03)
                box(sc['iron'], lo, hi)
            lo, hi = bx(a, b, bot, top, -0.005, 0.005)
            box(sc['glass'], lo, hi, uv='unit', skip=('+z', '-z'))


def door(a, b, top=3.8, passable=True):
    return dict(a=a, b=b, bottom=0.0, top=top, door=True, passable=passable)


def window(a, b, bottom=1.5, top=4.3):
    return dict(a=a, b=b, bottom=bottom, top=top)


def build_walls():
    # exterior south
    wall('x', 0, -6, 6, 6.0, 'ext', 'vestibule',
         [door(-1.5, 1.5, 4.2, passable=False), window(-4.6, -2.6, 1.6, 4.4), window(2.6, 4.6, 1.6, 4.4)])
    wall('x', 0, 6, 18, 6.0, 'ext', 'library')
    wall('y', -6, 0, 12, 6.0, 'ext', 'vestibule', [window(2.5, 4.5, 1.6, 4.4), window(7.5, 9.5, 1.6, 4.4)])
    wall('y', 6, 0, 12, 6.0, 'vestibule', 'library', [door(4.5, 7.5)])
    wall('y', 18, 0, 12, 6.0, 'library', 'ext', [window(1.8, 4.6, 1.3, 4.1), window(7.4, 10.2, 1.3, 4.1)])
    wall('x', 12, -6, 6, 6.0, 'vestibule', 'gallery')
    wall('x', 12, 6, 18, 6.0, 'library', 'courtyard', [door(10.5, 13.5)])
    wall('y', -6, 12, 24, 6.0, 'ext', 'gallery', [window(14.0, 16.4, 1.4, 4.2), window(19.6, 22.0, 1.4, 4.2)])
    wall('y', 6, 12, 24, 6.0, 'gallery', 'courtyard',
         [door(16.5, 19.5), window(13.2, 15.2, 1.4, 4.0), window(20.8, 22.8, 1.4, 4.0)])
    wall('y', 18, 12, 24, 6.0, 'courtyard', 'ext')
    wall('x', 24, -6, 6, 8.0, 'gallery', 'hall', [door(-1.5, 1.5, 4.2)])
    wall('x', 24, 6, 18, 6.0, 'courtyard', 'ext')
    wall('y', -6, 24, 38, 8.0, 'ext', 'hall',
         [window(25.8, 27.8, 2.0, 6.2), window(30.4, 32.4, 2.0, 6.2), window(35.0, 37.0, 2.6, 6.2)])
    wall('y', 6, 24, 38, 8.0, 'hall', 'ext',
         [window(25.8, 27.8, 2.0, 6.2), window(30.4, 32.4, 2.0, 6.2), window(35.0, 37.0, 2.6, 6.2)])
    wall('x', 38, -6, 6, 8.0, 'hall', 'ext', [window(-1.3, 1.3, 4.6, 7.3)])


def build_floors_ceilings():
    for r in ROOMS:
        (x0, x1), (y0, y1) = r['x'], r['y']
        box(sc[r['floor']], (x0, y0, -0.2), (x1, y1, 0.0), tile=r['floor_tile'], skip=('-z',))
        if r['h']:
            h = r['h']
            box(sc['ceiling'], (x0, y0, h), (x1, y1, h + 0.3), tile=2.0, skip=('+z',))
            box(sc['roof'], (x0 - HW, y0 - HW, h + 0.3), (x1 + HW, y1 + HW, h + 0.35), tile=4.0, skip=('-z',))
    # surrounding land
    box(sc['ground'], (-80, -60, -0.3), (100, 100, -0.21), tile=3.0, skip=('-z',))


# ---------------------------------------------------------------------------
# Props
# ---------------------------------------------------------------------------

def column(x, y, h, r=0.32, shaft='marble_white'):
    box(sc['limestone'], (x - 0.45, y - 0.45, 0), (x + 0.45, y + 0.45, 0.22), skip=('-z',))
    lathe(sc['limestone'], [(0.42, 0.22), (0.42, 0.3), (0.36, 0.36), (0.38, 0.42), (r + 0.02, 0.48)],
          28, T(x, y), cap_bottom=False, cap_top=False)
    prof = []
    top = h - 0.7
    for i in range(9):
        t = i / 8
        prof.append((r * (1 - 0.12 * t * t), 0.48 + (top - 0.48) * t))
    lathe(sc[shaft], prof, 28, T(x, y), cap_bottom=False, cap_top=False, sharp_deg=60)
    lathe(sc['limestone'], [(r * 0.88 + 0.03, top), (r * 0.88 + 0.03, top + 0.08), (r + 0.02, top + 0.2),
                            (r + 0.18, top + 0.38), (r + 0.18, top + 0.42)],
          28, T(x, y), cap_bottom=False, cap_top=False)
    box(sc['limestone'], (x - 0.55, y - 0.55, top + 0.42), (x + 0.55, y + 0.55, h))
    col_circle(x, y, 0.5)


def pedestal(x, y, h=1.1, mat='marble_white', base='limestone'):
    box(sc[base], (x - 0.32, y - 0.32, 0), (x + 0.32, y + 0.32, 0.14), skip=('-z',))
    lathe(sc[mat], [(0.26, 0.14), (0.26, 0.2), (0.18, 0.28), (0.16, h - 0.24), (0.2, h - 0.16), (0.26, h - 0.1)],
          24, T(x, y), cap_bottom=False, cap_top=False)
    box(sc[base], (x - 0.3, y - 0.3, h - 0.1), (x + 0.3, y + 0.3, h))
    col_circle(x, y, 0.38)


def flame(x, y, z, s=1.0):
    lathe(sc['flame'], [(0, 0), (0.022 * s, 0.025 * s), (0.026 * s, 0.05 * s), (0.014 * s, 0.09 * s), (0, 0.13 * s)],
          10, T(x, y, z), cap_bottom=False, cap_top=False, sharp_deg=80)


def candle(x, y, z, h=0.16, r=0.028):
    cylinder(sc['wax'], r, 0, h, 12, T(x, y, z))
    cylinder(sc['iron'], 0.003, h, h + 0.02, 4, T(x, y, z))
    flame(x, y, z + h + 0.01, 0.8)


def chandelier(x, y, ceiling, drop, R=1.0, n=8, lum=40.0, dist=14.0):
    z = ceiling - drop
    torus(sc['iron'], R, 0.035, 40, 8, T(x, y, z))
    torus(sc['gold'], R * 0.55, 0.025, 32, 8, T(x, y, z + 0.18))
    cylinder(sc['iron'], 0.03, z - 0.25, ceiling, 8, T(x, y))
    lathe(sc['gold'], [(0, -0.4), (0.09, -0.3), (0.06, -0.1), (0.04, 0.1)], 16, T(x, y, z))
    for k in range(3):
        a = 2 * math.pi * k / 3
        tube(sc['iron'], [(x + R * math.cos(a), y + R * math.sin(a), z), (x, y, z + 0.9)], 0.012, 6)
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        cx, cy = x + R * math.cos(a), y + R * math.sin(a)
        lathe(sc['gold'], [(0, -0.04), (0.06, 0.0), (0.05, 0.02)], 12, T(cx, cy, z + 0.02), cap_top=True)
        candle(cx, cy, z + 0.02)
    for k in range(n // 2):
        a = 2 * math.pi * k / (n // 2)
        cx, cy = x + R * 0.55 * math.cos(a), y + R * 0.55 * math.sin(a)
        candle(cx, cy, z + 0.2, 0.12, 0.024)
    light(x, y, z - 0.1, '#ffb768', lum, dist, flicker=True)


def sconce(px, py, n, z=2.7, lum=6.0):
    M = frame(px, py, n, z)
    box(sc['iron'], (-0.08, -0.03, -0.18), (0.08, 0.0, 0.18), M=M)
    tube(sc['iron'], [(0, -0.02, -0.08), (0, -0.18, -0.06), (0, -0.26, 0.02)], 0.014, 6, M=M)
    lathe(sc['gold'], [(0, 0), (0.07, 0.02), (0.075, 0.04)], 12, M @ T(0, -0.26, 0.02))
    w = (M @ T(0, -0.26, 0.06)).to_translation()
    candle(w.x, w.y, w.z, 0.14)
    lp = (M @ T(0, -0.32, 0.35)).to_translation()
    light(lp.x, lp.y, lp.z, '#ffad5c', lum, 7.0, flicker=True)


def table(x, y, w, d, h=0.78, top='wood_dark', rot=0, legs='wood_dark'):
    M = T(x, y) @ Rz(rot)
    box(sc[top], (-w / 2, -d / 2, h - 0.06), (w / 2, d / 2, h), M=M)
    box(sc[top], (-w / 2 + 0.06, -d / 2 + 0.06, h - 0.16), (w / 2 - 0.06, d / 2 - 0.06, h - 0.06), M=M)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = sx * (w / 2 - 0.12), sy * (d / 2 - 0.12)
            lathe(sc[legs], [(0.04, 0), (0.05, 0.08), (0.035, 0.2), (0.045, 0.45), (0.035, h - 0.2), (0.05, h - 0.16)],
                  10, M @ T(lx, ly), cap_bottom=False)
    c = math.cos(math.radians(rot))
    s = math.sin(math.radians(rot))
    ex, ey = abs(w / 2 * c) + abs(d / 2 * s), abs(w / 2 * s) + abs(d / 2 * c)
    col_rect(x - ex, y - ey, x + ex, y + ey)


def round_table(x, y, r=0.55, h=0.78, mat='wood_dark', top=None):
    cylinder(sc[top or mat], r, h - 0.05, h, 32, T(x, y))
    lathe(sc[mat], [(0.3, 0), (0.3, 0.04), (0.08, 0.12), (0.06, 0.4), (0.09, h - 0.15), (0.2, h - 0.05)],
          16, T(x, y), cap_bottom=False, cap_top=False)
    col_circle(x, y, r)


def chair(x, y, rot, mat='wood_dark', seat='velvet'):
    M = T(x, y) @ Rz(rot)
    box(sc[seat], (-0.24, -0.24, 0.42), (0.24, 0.24, 0.5), M=M)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(sc[mat], (sx * 0.2 - 0.025, sy * 0.2 - 0.025, 0), (sx * 0.2 + 0.025, sy * 0.2 + 0.025, 0.42), M=M)
        box(sc[mat], (sx * 0.2 - 0.025, 0.175, 0.5), (sx * 0.2 + 0.025, 0.225, 1.05), M=M)
    box(sc[mat], (-0.2, 0.18, 0.75), (0.2, 0.22, 1.02), M=M)
    col_circle(x, y, 0.3)


def bookshelf(px, py, n, L, H=3.2, D=0.42):
    M = frame(px, py, n)
    m = sc['wood_dark']
    box(m, (-L / 2, -D, 0), (-L / 2 + 0.06, 0, H), M=M)
    box(m, (L / 2 - 0.06, -D, 0), (L / 2, 0, H), M=M)
    box(m, (-L / 2, -D - 0.04, H - 0.08), (L / 2, 0, H), M=M)
    box(m, (-L / 2, -D, 0), (L / 2, 0, 0.14), M=M)
    box(m, (-L / 2, -0.03, 0), (L / 2, 0, H), M=M)
    shelves = 6
    step = (H - 0.24) / shelves
    nbays = max(1, round(L / 1.1))
    for b in range(1, nbays):
        xx = -L / 2 + L * b / nbays
        box(m, (xx - 0.025, -D, 0.14), (xx + 0.025, -0.03, H - 0.08), M=M)
    for s in range(shelves):
        z = 0.14 + s * step
        if s > 0:
            box(m, (-L / 2 + 0.06, -D, z - 0.03), (L / 2 - 0.06, -0.03, z), M=M)
        for b in range(nbays):
            xa = -L / 2 + L * b / nbays + 0.04
            xb = -L / 2 + L * (b + 1) / nbays - 0.04
            x = xa
            while x < xb - 0.03:
                bw = rng.uniform(0.03, 0.065)
                if x + bw > xb:
                    break
                if rng.random() < 0.06:
                    x += rng.uniform(0.05, 0.15)
                    continue
                bh = rng.uniform(0.6, 0.85) * (step - 0.03)
                bd = rng.uniform(0.22, 0.3)
                mat = rng.choice(BOOKS)
                box(sc[mat], (x, -0.03 - bd, z), (x + bw, -0.03, z + bh), M=M, skip=('-z', '+y'), tile=0.3)
                if rng.random() < 0.5:
                    gz = z + bh * rng.uniform(0.7, 0.85)
                    box(sc['gold'], (x, -0.031 - bd, gz), (x + bw, -0.03 - bd + 0.004, gz + 0.012), M=M,
                        skip=('-z', '+y'))
                x += bw + 0.002
    # collider
    c = M.to_translation()
    if n[0] == 0:
        col_rect(c.x - L / 2, c.y, c.x + L / 2, c.y + n[1] * D)
    else:
        col_rect(c.x, c.y - L / 2, c.x + n[0] * D, c.y + L / 2)


def painting(px, py, n, idx, w=2.2, h=1.6, zc=2.6):
    M = frame(px, py, n, zc)
    box(sc[f'painting_{idx}'], (-w / 2, -0.06, -h / 2), (w / 2, -0.02, h / 2), M=M, uv='unit',
        skip=('+x', '-x', '+z', '-z', '+y'))
    fw = 0.12
    for (a, b, c, d) in ((-w / 2 - fw, -h / 2 - fw, w / 2 + fw, -h / 2), (-w / 2 - fw, h / 2, w / 2 + fw, h / 2 + fw),
                         (-w / 2 - fw, -h / 2, -w / 2, h / 2), (w / 2, -h / 2, w / 2 + fw, h / 2)):
        box(sc['gold'], (a, -0.1, b), (c, 0, d), M=M, skip=('+y',))
    # small picture lamp
    tube(sc['bronze'], [(0, 0, h / 2 + fw + 0.1), (0, -0.25, h / 2 + fw + 0.2)], 0.012, 6, M=M)
    cylinder(sc['bronze'], 0.04, -0.06, 0.06, 10, M @ T(0, -0.28, h / 2 + fw + 0.2) @ Rx(-60))


def banner(px, py, n, z0=3.0, w=1.2, h=2.6):
    M = frame(px, py, n, z0)
    box(sc['banner'], (-w / 2, -0.05, 0), (w / 2, -0.04, h), M=M, uv='unit', skip=('+x', '-x', '+z', '-z', '+y'))
    cylinder(sc['gold'], 0.025, -w / 2 - 0.1, w / 2 + 0.1, 8, M @ T(0, -0.06, h + 0.04) @ geo.Ry(90))
    for sx in (-1, 1):
        sphere(sc['gold'], 0.045, 10, 6, M @ T(sx * (w / 2 + 0.12), -0.06, h + 0.04))


def bench(x, y, rot, L=1.8, mat='limestone'):
    M = T(x, y) @ Rz(rot)
    box(sc[mat], (-L / 2, -0.25, 0.38), (L / 2, 0.25, 0.48), M=M)
    for sx in (-1, 1):
        box(sc[mat], (sx * (L / 2 - 0.2) - 0.12, -0.2, 0), (sx * (L / 2 - 0.2) + 0.12, 0.2, 0.38), M=M, skip=('-z',))
    c, s = abs(math.cos(math.radians(rot))), abs(math.sin(math.radians(rot)))
    ex, ey = L / 2 * c + 0.25 * s, L / 2 * s + 0.25 * c
    col_rect(x - ex, y - ey, x + ex, y + ey)


def potted_plant(x, y, scale=1.0):
    M = T(x, y)
    lathe(sc['terracotta'], [(0.22 * scale, 0), (0.3 * scale, 0.5 * scale), (0.34 * scale, 0.55 * scale),
                             (0.3 * scale, 0.58 * scale)], 20, M, cap_bottom=False, cap_top=False)
    cylinder(sc['soil'], 0.29 * scale, 0.5 * scale, 0.52 * scale, 20, M, cap_bottom=False)
    for k in range(5):
        a = 2 * math.pi * k / 5 + rng.random()
        rr = 0.18 * scale
        sphere(sc['leaves'], rng.uniform(0.25, 0.33) * scale, 12, 8,
               T(x + rr * math.cos(a), y + rr * math.sin(a), (0.85 + rng.uniform(0, 0.35)) * scale), tile=0.6)
    sphere(sc['leaves'], 0.32 * scale, 12, 8, T(x, y, 1.2 * scale), tile=0.6)
    col_circle(x, y, 0.36 * scale)


def tree(x, y, h=3.2):
    lathe(sc['bark'], [(0.32, 0), (0.2, 0.3), (0.16, h * 0.6), (0.12, h)], 12, T(x, y), cap_bottom=False, tile=1.0)
    for k in range(7):
        a = 2 * math.pi * k / 7
        rr = rng.uniform(0.6, 1.0)
        sphere(sc['leaves'], rng.uniform(0.8, 1.15), 16, 10,
               T(x + rr * math.cos(a), y + rr * math.sin(a), h + rng.uniform(-0.2, 0.6)), tile=0.8)
    sphere(sc['leaves'], 1.3, 16, 10, T(x, y, h + 0.9), tile=0.8)
    col_circle(x, y, 0.4)


def hedge(x0, y0, x1, y1, h=0.95):
    box(sc['leaves'], (x0, y0, 0), (x1, y1, h), tile=0.7, skip=('-z',))
    col_rect(x0, y0, x1, y1)


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

def vestibule():
    for x in (-2.6, 2.6):
        for y in (3.0, 6.0, 9.0):
            column(x, y, 6.0)
    # coffered ceiling beams
    for x in (-4.3, 0.0, 4.3):
        box(sc['limestone'], (x - 0.15, 0.25, 5.65), (x + 0.15, 11.75, 6.0))
    for y in (3.0, 6.0, 9.0):
        box(sc['limestone'], (-5.75, y - 0.15, 5.65), (5.75, y + 0.15, 6.0))
    chandelier(0, 6.0, 6.0, 1.9, R=1.1, n=10, lum=55, dist=16)
    sconce(-5.75, 6.0, (1, 0), lum=5)
    sconce(-5.75, 11.0, (1, 0), lum=5)
    sconce(5.75, 2.6, (-1, 0), lum=5)
    sconce(5.75, 9.6, (-1, 0), 2.6, lum=5)
    # main door (closed, decorative)
    M = T(0, 0.25)
    for sx in (-1, 1):
        box(sc['wood_panel'], (sx * 0.02 if sx > 0 else -1.5, -0.06, 0), (1.5 if sx > 0 else -0.02, 0.06, 4.2), M=M)
        for zz in (0.4, 2.3):
            px0, px1 = (0.25, 1.25) if sx > 0 else (-1.25, -0.25)
            box(sc['wood_dark'], (px0, 0.06, zz), (px1, 0.1, zz + 1.5), M=M)
        torus(sc['iron'], 0.12, 0.015, 20, 6, M @ T(sx * 0.3, 0.13, 1.6) @ Rx(90))
    col_rect(-1.5, 0.0, 1.5, 0.35)
    potted_plant(-4.6, 1.3)
    potted_plant(4.6, 1.3)
    potted_plant(-4.9, 11.0, 0.9)
    # loci
    pedestal(-4.4, 4.5)
    locus('vestibule', 'pedestal', -4.4, 4.5, 1.1)
    round_table(0, 7.4, 0.6, 0.86, mat='bronze', top='marble_green')
    locus('vestibule', 'round_table', 0, 7.4, 0.86)
    M = frame(5.75, 9.6, (-1, 0))
    box(sc['marble_white'], (-0.8, -0.45, 0.85), (0.8, 0, 0.92), M=M)
    for sx in (-0.7, 0.7):
        lathe(sc['gold'], [(0.05, 0), (0.07, 0.05), (0.04, 0.3), (0.05, 0.85)], 10, M @ T(sx, -0.35), cap_bottom=False)
        box(sc['gold'], (sx - 0.04, -0.05, 0.6), (sx + 0.04, 0, 0.85), M=M)
    col_rect(5.75 - 0.45, 8.8, 5.75, 10.4)
    locus('vestibule', 'console', 5.75 - 0.25, 9.6, 0.92)


def library():
    # bookshelves
    bookshelf(12.0, 0.25, (0, 1), 11.4)
    bookshelf(8.3, 11.75, (0, -1), 3.9)
    bookshelf(15.7, 11.75, (0, -1), 3.9)
    bookshelf(6.25, 2.3, (1, 0), 3.6)
    bookshelf(6.25, 9.7, (1, 0), 3.6)
    for x in range(7, 18, 2):
        box(sc['wood_dark'], (x - 0.15, 0.25, 5.2), (x + 0.15, 11.75, 5.5))
    # rug + table + chairs
    geo.quad(sc['rug'], [(9.0, 3.2, 0.012), (15.0, 3.2, 0.012), (15.0, 6.8, 0.012), (9.0, 6.8, 0.012)],
             [(0, 0), (3, 0), (3, 1), (0, 1)])
    table(12.0, 5.0, 3.2, 1.3)
    for x in (10.9, 12.0, 13.1):
        chair(x, 3.9, 0)
        chair(x, 6.1, 180)
    for x in (10.6, 13.4):
        candle(x, 5.0, 0.78, 0.2, 0.03)
        light(x, 5.0, 1.25, '#ffb060', 2.5, 4.0, flicker=True)
    locus('library', 'reading_table', 12.0, 5.0, 0.78)
    chandelier(10.0, 5.0, 5.5, 1.6, R=0.7, n=6, lum=22, dist=10)
    chandelier(14.0, 5.0, 5.5, 1.6, R=0.7, n=6, lum=22, dist=10)
    # lectern
    lx, ly = 16.7, 8.6
    box(sc['wood_dark'], (lx - 0.25, ly - 0.25, 0), (lx + 0.25, ly + 0.25, 0.08))
    lathe(sc['wood_dark'], [(0.09, 0.08), (0.07, 0.3), (0.06, 1.0), (0.1, 1.1)], 12, T(lx, ly), cap_bottom=False)
    box(sc['wood_dark'], (-0.32, -0.25, -0.03), (0.32, 0.25, 0.03), M=T(lx, ly, 1.14) @ Rz(90) @ Rx(-12))
    col_circle(lx, ly, 0.35)
    locus('library', 'lectern', lx, ly, 1.18)
    cylinder(sc['iron'], 0.02, 0, 1.5, 8, T(17.3, 10.2))
    lathe(sc['iron'], [(0.18, 0), (0.05, 0.08)], 12, T(17.3, 10.2), cap_bottom=True)
    candle(17.3, 10.2, 1.5, 0.22, 0.035)
    light(17.3, 10.2, 1.9, '#ffad5c', 3, 5, flicker=True)
    # reading corner by the north door
    round_table(15.4, 9.9, 0.42, 0.72)
    chair(16.3, 9.2, -45)
    locus('library', 'side_table', 15.4, 9.9, 0.72)
    potted_plant(9.4, 10.9, 0.9)


def courtyard():
    box(sc['flagstones'], (11.0, 12.25, 0), (13.0, 23.75, 0.025), tile=2.0, skip=('-z',))
    box(sc['flagstones'], (6.25, 17.0, 0), (17.75, 19.0, 0.024), tile=2.0, skip=('-z',))
    # fountain
    fx, fy = 12.0, 18.0
    lathe(sc['limestone'], [(1.95, 0), (2.0, 0.08), (1.95, 0.5), (2.05, 0.55), (2.05, 0.62), (1.82, 0.62),
                            (1.8, 0.1)], 40, T(fx, fy), cap_bottom=False, cap_top=False)
    cylinder(sc['water'], 1.8, 0.42, 0.44, 40, T(fx, fy), cap_bottom=False)
    lathe(sc['limestone'], [(0.35, 0.42), (0.3, 0.6), (0.18, 0.75), (0.16, 1.0), (0.22, 1.08), (0.7, 1.18),
                            (0.72, 1.28), (0.62, 1.28), (0.25, 1.2), (0.12, 1.25), (0.12, 1.42), (0.22, 1.5),
                            (0.22, 1.55)], 32, T(fx, fy), cap_bottom=False, cap_top=True)
    cylinder(sc['water'], 0.63, 1.24, 1.25, 28, T(fx, fy), cap_bottom=False)
    col_circle(fx, fy, 2.05)
    locus('courtyard', 'fountain', fx, fy, 1.55, radius=0.8)
    # benches
    bench(16.6, 15.2, 90)
    locus('courtyard', 'bench', 16.6, 15.2, 0.48)
    bench(7.5, 15.0, 90)
    bench(16.6, 21.0, 90)
    # sundial
    sx, sy = 8.8, 21.4
    lathe(sc['limestone'], [(0.35, 0), (0.35, 0.12), (0.22, 0.2), (0.16, 0.85), (0.32, 0.95), (0.34, 1.0)],
          24, T(sx, sy), cap_bottom=False)
    cylinder(sc['bronze'], 0.3, 1.0, 1.02, 32, T(sx, sy), cap_bottom=False)
    geo.prism(sc['bronze'], [(0, 0.1), (0.18, 0.28), (0, 0.28)], -0.006, 0.006,
              M=T(sx, sy, 1.02) @ geo.Ry(-90))
    col_circle(sx, sy, 0.4)
    locus('courtyard', 'sundial', sx, sy - 0.08, 1.02)
    # greenery
    tree(8.4, 14.4)
    tree(15.6, 21.8, 3.6)
    for (x0, y0, x1, y1) in ((6.25, 12.25, 10.4, 12.85), (6.25, 12.85, 6.85, 16.2),
                             (13.6, 12.25, 17.75, 12.85), (17.15, 12.85, 17.75, 14.0),
                             (6.25, 23.15, 10.4, 23.75), (6.25, 19.8, 6.85, 23.15),
                             (13.6, 23.15, 17.75, 23.75), (17.15, 22.6, 17.75, 23.15)):
        hedge(x0, y0, x1, y1)
    for (x, y) in ((10.4, 16.4), (13.6, 16.4), (10.4, 19.6), (13.6, 19.6)):
        potted_plant(x, y, 0.8)
    sconce(6.25, 13.4, (1, 0), 2.8, lum=3)
    sconce(17.75, 18.0, (-1, 0), 2.8, lum=3)


def gallery():
    painting(-2.6, 12.25, (0, 1), 0)
    painting(2.6, 12.25, (0, 1), 1)
    painting(-3.9, 23.75, (0, -1), 2, w=2.0, h=1.5)
    painting(3.9, 23.75, (0, -1), 3, w=2.0, h=1.5)
    pedestal(3.6, 13.6, 1.05, mat='marble_white')
    locus('gallery', 'pedestal_south', 3.6, 13.6, 1.05)
    M = T(0, 18.0)
    box(sc['velvet'], (-1.3, -0.4, 0.34), (1.3, 0.4, 0.5), M=M)
    for sx in (-1.15, 1.15):
        for sy in (-0.3, 0.3):
            lathe(sc['gold'], [(0.04, 0), (0.05, 0.06), (0.03, 0.2), (0.05, 0.34)], 10, M @ T(sx, sy), cap_bottom=False)
    col_rect(-1.3, 17.6, 1.3, 18.4)
    locus('gallery', 'ottoman', 0, 18.0, 0.5)
    pedestal(-4.5, 22.5, 1.05, mat='marble_green')
    locus('gallery', 'pedestal_north', -4.5, 22.5, 1.05)
    # decorative urns
    for (x, y) in ((-4.8, 13.2), (4.6, 22.9)):
        box(sc['limestone'], (x - 0.3, y - 0.3, 0), (x + 0.3, y + 0.3, 0.5), skip=('-z',))
        lathe(sc['marble_white'], [(0.12, 0.5), (0.26, 0.65), (0.3, 0.85), (0.18, 1.1), (0.14, 1.2), (0.2, 1.3)],
              24, T(x, y), cap_bottom=False, cap_top=False)
        col_circle(x, y, 0.4)
    chandelier(0, 15.0, 5.5, 1.5, R=0.8, n=8, lum=26, dist=11)
    chandelier(0, 21.0, 5.5, 1.5, R=0.8, n=8, lum=26, dist=11)
    for y in range(13, 24, 2):
        box(sc['ceiling'], (-5.75, y - 0.12, 5.2), (5.75, y + 0.12, 5.5))


def hall():
    for x in (-3.6, 3.6):
        for y in (27.0, 30.2, 33.4):
            column(x, y, 8.0, r=0.4, shaft='marble_green')
    for y in range(25, 38, 2):
        box(sc['wood_dark'], (-5.75, y - 0.2, 7.55), (5.75, y + 0.2, 8.0))
    # carpet runner (u along y, v across x)
    x0, x1, y0, y1 = -1.0, 1.0, 24.4, 35.0
    geo.quad(sc['carpet'], [(x1, y0, 0.012), (x1, y1, 0.012), (x0, y1, 0.012), (x0, y0, 0.012)],
             [(0, 0), ((y1 - y0) / 2.0, 0), ((y1 - y0) / 2.0, 1), (0, 1)])
    # dais and throne
    box(sc['marble_white'], (-3.2, 35.0, 0), (3.2, 37.75, 0.2), tile=1.5, skip=('-z',))
    box(sc['marble_white'], (-2.6, 35.6, 0.2), (2.6, 37.75, 0.4), tile=1.5, skip=('-z',))
    geo.quad(sc['carpet'], [(1.0, 35.0, 0.201), (1.0, 35.6, 0.201), (-1.0, 35.6, 0.201), (-1.0, 35.0, 0.201)],
             [(0, 0), (0.3, 0), (0.3, 1), (0, 1)])
    tx_, ty = 0.0, 36.6
    M = T(tx_, ty, 0.4)
    box(sc['wood_dark'], (-0.55, -0.45, 0), (0.55, 0.5, 0.42), M=M)
    box(sc['velvet'], (-0.5, -0.45, 0.42), (0.5, 0.45, 0.52), M=M)
    box(sc['wood_dark'], (-0.55, 0.42, 0.42), (0.55, 0.62, 2.4), M=M)
    box(sc['velvet'], (-0.42, 0.36, 0.6), (0.42, 0.42, 2.1), M=M)
    for sx in (-1, 1):
        box(sc['wood_dark'], (sx * 0.55 - 0.08, -0.45, 0.42), (sx * 0.55 + 0.08, 0.45, 0.85), M=M)
        sphere(sc['gold'], 0.08, 12, 8, M @ T(sx * 0.55, -0.45, 0.9))
        lathe(sc['gold'], [(0.0, 0), (0.07, 0.05), (0.04, 0.2), (0, 0.32)], 12, M @ T(sx * 0.5, 0.52, 2.4))
    lathe(sc['gold'], [(0, 0), (0.14, 0.08), (0.1, 0.25), (0, 0.45)], 16, M @ T(0, 0.52, 2.4))
    col_rect(-0.7, 36.05, 0.7, 37.3)
    locus('hall', 'throne', tx_, ty - 0.05, 0.92)
    # braziers
    for sx in (-2.4, 2.4):
        bx_, by = sx, 35.35
        lathe(sc['iron'], [(0.25, 0.2), (0.25, 0.26), (0.08, 0.35), (0.06, 0.9), (0.1, 1.0), (0.38, 1.12),
                           (0.42, 1.25), (0.36, 1.25), (0.0, 1.15)], 20, T(bx_, by), cap_bottom=True, cap_top=False)
        cylinder(sc['ember'], 0.34, 1.18, 1.2, 16, T(bx_, by), cap_bottom=False)
        for k in range(5):
            a = 2 * math.pi * k / 5
            fx, fy = bx_ + 0.15 * math.cos(a), by + 0.15 * math.sin(a)
            flame(fx, fy, 1.2, 3.2)
        flame(bx_, by, 1.2, 4.2)
        col_circle(bx_, by, 0.45)
        light(bx_, by, 1.8, '#ff8a3a', 14, 9, flicker=True)
    # banquet table (west) and altar (east)
    table(-2.5, 29.8, 1.1, 4.2, rot=0)
    for y in (28.4, 29.8, 31.2):
        candle(-2.5, y, 0.78, 0.2, 0.03)
    bench(-1.6, 29.8, 90, L=3.6, mat='wood_dark')
    locus('hall', 'banquet_table', -2.5, 28.6, 0.78)
    ax, ay = 2.6, 31.4
    box(sc['marble_white'], (ax - 0.6, ay - 0.45, 0), (ax + 0.6, ay + 0.45, 0.15), skip=('-z',))
    box(sc['marble_green'], (ax - 0.5, ay - 0.35, 0.15), (ax + 0.5, ay + 0.35, 0.92))
    box(sc['marble_white'], (ax - 0.58, ay - 0.42, 0.92), (ax + 0.58, ay + 0.42, 1.0))
    for sx in (-0.45, 0.45):
        lathe(sc['gold'], [(0.06, 0), (0.03, 0.05), (0.02, 0.25), (0.04, 0.27)], 10, T(ax + sx, ay + 0.25, 1.0))
        candle(ax + sx, ay + 0.25, 1.27, 0.14)
    col_rect(ax - 0.6, ay - 0.45, ax + 0.6, ay + 0.45)
    light(ax, ay + 0.3, 1.8, '#ffb060', 3, 5, flicker=True)
    locus('hall', 'altar', ax, ay - 0.05, 1.0)
    # banners & lights
    for y in (29.1, 33.7):
        banner(-5.75, y, (1, 0))
        banner(5.75, y, (-1, 0))
        sconce(-5.75, y, (1, 0), 2.6, lum=5)
        sconce(5.75, y, (-1, 0), 2.6, lum=5)
    chandelier(0, 28.0, 8.0, 2.6, R=1.3, n=12, lum=60, dist=16)
    chandelier(0, 33.0, 8.0, 2.6, R=1.3, n=12, lum=60, dist=16)


# ---------------------------------------------------------------------------

def main():
    mt.reset_scene()
    mats = build_materials()
    build_walls()
    build_floors_ceilings()
    vestibule()
    library()
    courtyard()
    gallery()
    hall()
    objs = sc.build(mats, prefix='palace_')
    print(f'Built {len(objs)} meshes, {sum(len(o.data.polygons) for o in objs)} polygons')

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(RAW_DIR, 'palace.glb'), export_format='GLB',
                              export_yup=True, export_apply=False, export_lights=False,
                              export_cameras=False, export_extras=False, export_image_format='AUTO')
    rooms = [{'id': r['id'], 'min': [r['x'][0], -r['y'][1]], 'max': [r['x'][1], -r['y'][0]],
              'outdoor': r['h'] is None} for r in ROOMS]
    data = {
        'spawn': {'pos': to3(0, 2.0, 0), 'yaw': 0.0},
        'rooms': rooms,
        'loci': LOCI,
        'lights': LIGHTS,
        'colliders': COLLIDERS,
        'sun': {'dir': to3(-0.45, -0.6, 0.66)},
    }
    with open(os.path.join(OUT_DIR, 'palace.json'), 'w') as f:
        json.dump(data, f, indent=1)
    print(f'{len(LOCI)} loci, {len(LIGHTS)} lights, {len(COLLIDERS)} colliders')


if __name__ == '__main__':
    main()
