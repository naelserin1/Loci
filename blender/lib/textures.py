"""Procedural, seamlessly tileable PBR textures generated with numpy.

Every generator returns a dict with:
    color  : (H, W, 3) float array, sRGB values in [0, 1]
    normal : (H, W, 3) float array, tangent-space OpenGL normal map in [0, 1]
             (optional)
    rough  : (H, W) float array in [0, 1] (optional)

Arrays follow Blender's pixel order: row 0 is the BOTTOM of the image, so
"+v" in UV space is "+row" here. All noise is built in the frequency domain,
which makes it periodic and therefore tileable by construction.
"""

import numpy as np

TAU = 2.0 * np.pi


# ---------------------------------------------------------------------------
# Noise primitives
# ---------------------------------------------------------------------------

def grid(n, m=None):
    m = m or n
    ys, xs = np.mgrid[0:n, 0:m].astype(np.float64)
    return (xs + 0.5) / m, (ys + 0.5) / n


def fbm(n, beta=2.0, seed=0, aniso=(1.0, 1.0), lowcut=0.0, m=None):
    """Periodic fractal noise (spectral synthesis). Zero mean, unit std.

    beta   : spectral slope; higher = smoother.
    aniso  : (ax, ay) frequency weights; ax > ay stretches features along x.
    lowcut : removes frequencies below this (in cycles per texture).
    """
    m = m or n
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((n, m))
    fy = np.fft.fftfreq(n)[:, None] * n * aniso[1]
    fx = np.fft.fftfreq(m)[None, :] * m * aniso[0]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1.0
    spec = np.fft.fft2(w) / f ** (beta / 2.0)
    spec[0, 0] = 0.0
    if lowcut > 0:
        spec[f < lowcut] = 0.0
    r = np.real(np.fft.ifft2(spec))
    r -= r.mean()
    r /= r.std() + 1e-9
    return r


def fbm1d(n, beta=2.0, seed=0):
    rng = np.random.default_rng(seed)
    w = rng.standard_normal(n)
    f = np.abs(np.fft.fftfreq(n) * n)
    f[0] = 1.0
    spec = np.fft.fft(w) / f ** (beta / 2.0)
    spec[0] = 0.0
    r = np.real(np.fft.ifft(spec))
    return (r - r.mean()) / (r.std() + 1e-9)


def voronoi(n, count, seed=0):
    """Periodic Voronoi: returns (F1, F2, cell index)."""
    rng = np.random.default_rng(seed)
    pts = rng.random((count, 2))
    xs, ys = grid(n)
    d1 = np.full((n, n), 9.0)
    d2 = np.full((n, n), 9.0)
    idx = np.zeros((n, n), dtype=np.int32)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(xs - px)
        dx = np.minimum(dx, 1.0 - dx)
        dy = np.abs(ys - py)
        dy = np.minimum(dy, 1.0 - dy)
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < d1
        d2 = np.where(closer, d1, np.minimum(d2, d))
        idx = np.where(closer, i, idx)
        d1 = np.where(closer, d, d1)
    return d1, d2, idx


def n01(a):
    lo, hi = a.min(), a.max()
    return (a - lo) / (hi - lo + 1e-9)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def blur(a, passes=1):
    """Cheap periodic box blur."""
    for _ in range(passes):
        a = (a + np.roll(a, 1, 0) + np.roll(a, -1, 0)
             + np.roll(a, 1, 1) + np.roll(a, -1, 1)) / 5.0
    return a


def lerp(a, b, t):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if np.ndim(t) == 2:
        t = t[..., None]
    return a + (b - a) * t


def normal_from_height(h, relief):
    """h in [0,1]; relief = height range expressed in texture widths."""
    n, m = h.shape
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * m * relief
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * n * relief
    nz = np.ones_like(h)
    v = np.dstack([-dx, -dy, nz])
    v /= np.linalg.norm(v, axis=2, keepdims=True)
    return v * 0.5 + 0.5


def rgb(hex_or_tuple):
    if isinstance(hex_or_tuple, str):
        h = hex_or_tuple.lstrip('#')
        return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])
    return np.array(hex_or_tuple, dtype=np.float64)


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

def marble_field(n, seed, freq=(2, 3), turb=3.0):
    xs, ys = grid(n)
    t = fbm(n, 2.4, seed)
    t2 = fbm(n, 1.8, seed + 7)
    v = np.sin(TAU * (freq[0] * xs + freq[1] * ys) + turb * t)
    veins = np.exp(-np.abs(v) / 0.16) * (0.6 + 0.4 * n01(t2))
    v2 = np.sin(TAU * (3 * xs - 2 * ys) + 4.0 * t2)
    veins2 = np.exp(-np.abs(v2) / 0.05) * 0.5
    cloud = n01(fbm(n, 2.0, seed + 3))
    return np.clip(veins + veins2, 0, 1), cloud


def marble_checker(n=1024, seed=1):
    """2x2 checkerboard of polished marble tiles (texture = 2 m)."""
    va, ca = marble_field(n, seed)
    vb, cb = marble_field(n, seed + 20, freq=(1, 2), turb=4.0)
    white = lerp(lerp(rgb('#f0ebe1'), rgb('#d6cebf'), ca), rgb('#77736d'), va * 0.85)
    dark = lerp(lerp(rgb('#1f2a27'), rgb('#33403a'), cb), rgb('#c9c3b5'), vb * 0.55)
    xs, ys = grid(n)
    cell = ((np.floor(xs * 2) + np.floor(ys * 2)) % 2).astype(bool)
    color = np.where(cell[..., None], dark, white)
    fx = (xs * 2) % 1.0
    fy = (ys * 2) % 1.0
    edge = np.minimum(np.minimum(fx, 1 - fx), np.minimum(fy, 1 - fy))
    grout = 1.0 - smoothstep(0.002, 0.006, edge)
    color = lerp(color, rgb('#6f6a62'), grout)
    h = 1.0 - grout + 0.02 * fbm(n, 2.2, seed + 9)
    rough = 0.12 + 0.25 * grout + 0.06 * n01(fbm(n, 2.0, seed + 11))
    return dict(color=color, normal=normal_from_height(blur(h), 0.0015), rough=rough)


def marble_plain(n=1024, seed=5, base=('#efebe3', '#dcd5c8'), vein='#9a948c'):
    v, c = marble_field(n, seed, freq=(1, 2), turb=3.5)
    color = lerp(lerp(rgb(base[0]), rgb(base[1]), c), rgb(vein), v * 0.75)
    rough = 0.18 + 0.05 * n01(fbm(n, 2.0, seed + 1))
    h = 0.5 + 0.02 * fbm(n, 2.0, seed + 2)
    return dict(color=color, normal=normal_from_height(h, 0.0005), rough=rough)


def wood_planks(n=1024, seed=2, rows=10, tint=('#9a6a3f', '#6e4526'), gap='#2a1a10'):
    """Floor planks running along x (texture = 2 m)."""
    rng = np.random.default_rng(seed)
    xs, ys = grid(n)
    grain = fbm(n, 2.0, seed, aniso=(14.0, 1.0))
    fine = fbm(n, 1.4, seed + 1, aniso=(30.0, 1.0))
    row = np.floor(ys * rows).astype(int)
    color = np.zeros((n, n, 3))
    h = np.ones((n, n))
    rough = np.zeros((n, n))
    shift = rng.random(rows)
    tints = rng.random(rows)
    rolls = rng.integers(0, n, rows)
    for r in range(rows):
        mask = row == r
        g = np.roll(grain, rolls[r], axis=1)
        f = np.roll(fine, rolls[r] // 2, axis=1)
        rings = 0.5 + 0.5 * np.sin(g * 6.0 + f * 1.2)
        c = lerp(rgb(tint[0]), rgb(tint[1]), np.clip(rings * 0.7 + tints[r] * 0.5, 0, 1))
        c *= (0.92 + 0.16 * tints[r])
        color[mask] = c[mask]
        joint = (xs + shift[r]) % 1.0
        je = np.minimum(joint, 1 - joint)
        jm = 1.0 - smoothstep(0.0015, 0.004, je)
        h[mask] = np.minimum(h[mask], (1.0 - jm)[mask])
        rough[mask] = (0.45 + 0.15 * rings)[mask]
    fy = (ys * rows) % 1.0
    ge = np.minimum(fy, 1 - fy)
    gm = 1.0 - smoothstep(0.01, 0.035, ge)
    h = np.minimum(h, 1.0 - gm)
    color = lerp(color, rgb(gap), (1.0 - h) * 0.85)
    h = h + 0.03 * fine
    return dict(color=np.clip(color, 0, 1), normal=normal_from_height(blur(h), 0.0012), rough=rough)


def wood_grain(n=1024, seed=3, tint=('#6e4128', '#3a1f12')):
    grain = fbm(n, 2.0, seed, aniso=(10.0, 1.0))
    fine = fbm(n, 1.3, seed + 1, aniso=(25.0, 1.0))
    rings = 0.5 + 0.5 * np.sin(grain * 8.0 + fine * 1.0)
    color = lerp(rgb(tint[0]), rgb(tint[1]), rings ** 1.5)
    h = 0.5 + 0.1 * fine
    return dict(color=color, normal=normal_from_height(h, 0.0008), rough=0.35 + 0.2 * rings)


def plaster(n=1024, seed=4, base=('#e6dccb', '#d3c6b0')):
    c = n01(fbm(n, 2.6, seed))
    speck = n01(fbm(n, 1.0, seed + 1))
    color = lerp(rgb(base[0]), rgb(base[1]), c * 0.8 + speck * 0.2)
    h = n01(fbm(n, 1.6, seed + 2))
    return dict(color=color, normal=normal_from_height(blur(h), 0.0006), rough=0.85 + 0.1 * speck)


def limestone(n=1024, seed=6, base=('#d9cfbd', '#b8ab95')):
    c = n01(fbm(n, 2.2, seed))
    pores = smoothstep(0.82, 0.95, n01(fbm(n, 0.8, seed + 1)))
    color = lerp(lerp(rgb(base[0]), rgb(base[1]), c), rgb('#8a7f6d'), pores * 0.5)
    h = n01(fbm(n, 1.7, seed + 2)) - pores * 0.5
    return dict(color=color, normal=normal_from_height(blur(h), 0.001), rough=0.8 - 0.1 * c)


def stone_blocks(n=1024, seed=7, rows=4, per_row=2, base=('#cbbfa8', '#a8987d')):
    """Ashlar masonry (texture = 2 m)."""
    rng = np.random.default_rng(seed)
    xs, ys = grid(n)
    r = np.floor(ys * rows)
    off = (r % 2) * 0.5 / per_row
    bx = (xs + off) * per_row
    col = np.floor(bx) % per_row
    block_id = (r * per_row + col).astype(int)
    tints = rng.random(rows * per_row)
    fx = bx % 1.0
    fy = (ys * rows) % 1.0
    ex = np.minimum(fx, 1 - fx) / per_row
    ey = np.minimum(fy, 1 - fy) / rows
    e = np.minimum(ex, ey)
    rough_edge = 0.004 * fbm(n, 1.5, seed + 1)
    mortar = 1.0 - smoothstep(0.004, 0.009, e + rough_edge)
    noise = n01(fbm(n, 2.0, seed + 2))
    t = tints[block_id]
    color = lerp(rgb(base[0]), rgb(base[1]), np.clip(t * 0.7 + noise * 0.4, 0, 1))
    color = lerp(color, rgb('#8c8270'), mortar)
    bevel = smoothstep(0.0, 0.03, e)
    h = bevel * (1 - mortar) + 0.08 * fbm(n, 1.6, seed + 3)
    return dict(color=color, normal=normal_from_height(h, 0.003), rough=0.9 - 0.1 * noise)


def grass(n=1024, seed=8):
    a = n01(fbm(n, 2.4, seed))
    b = n01(fbm(n, 1.2, seed + 1))
    blades = smoothstep(0.6, 0.9, n01(fbm(n, 0.6, seed + 2)))
    color = lerp(rgb('#3d5a22'), rgb('#6b8a35'), a)
    color = lerp(color, rgb('#2a3f16'), (1 - b) * 0.5)
    color = lerp(color, rgb('#9bb05a'), blades * 0.35)
    h = b * 0.6 + blades * 0.4
    return dict(color=color, normal=normal_from_height(h, 0.002), rough=0.95)


def flagstones(n=1024, seed=9):
    d1, d2, idx = voronoi(n, 22, seed)
    rng = np.random.default_rng(seed)
    tints = rng.random(22)
    edge = d2 - d1
    gap = 1.0 - smoothstep(0.004, 0.012, edge)
    noise = n01(fbm(n, 2.0, seed + 1))
    t = tints[idx]
    color = lerp(rgb('#b9ad97'), rgb('#8f8572'), np.clip(t * 0.8 + noise * 0.3, 0, 1))
    moss = n01(fbm(n, 2.2, seed + 2))
    color = lerp(color, lerp(rgb('#57503f'), rgb('#56603a'), moss * 0.6), gap)
    h = smoothstep(0.0, 0.03, edge) + 0.1 * fbm(n, 1.5, seed + 3)
    return dict(color=color, normal=normal_from_height(blur(h), 0.003), rough=0.85)


def leaves(n=512, seed=10):
    d1, d2, idx = voronoi(n, 160, seed)
    rng = np.random.default_rng(seed)
    t = rng.random(160)[idx]
    shade = 1.0 - smoothstep(0.0, 0.05, d1)
    color = lerp(rgb('#1f3a14'), rgb('#4b7228'), np.clip(t * 0.8 + shade * 0.4, 0, 1))
    gaps = 1.0 - smoothstep(0.0, 0.01, d2 - d1)
    color = lerp(color, rgb('#0e1a09'), gaps * 0.7)
    h = shade - gaps * 0.5
    return dict(color=color, normal=normal_from_height(blur(h), 0.004), rough=0.7)


def bark(n=512, seed=11):
    g = fbm(n, 2.0, seed, aniso=(1.0, 8.0))
    cracks = smoothstep(0.55, 0.8, n01(np.abs(g)))
    color = lerp(rgb('#5a4330'), rgb('#3a2a1c'), n01(g))
    color = lerp(color, rgb('#1d140c'), cracks)
    h = 1.0 - cracks + 0.2 * fbm(n, 1.5, seed + 1)
    return dict(color=color, normal=normal_from_height(h, 0.006), rough=0.95)


def carpet(n=1024, seed=12, base='#7a1418', trim='#c9a24a'):
    """u runs along the carpet (tileable), v across it (0..1, NOT tiled)."""
    xs, ys = grid(n)
    weave = 0.5 + 0.5 * np.sin(TAU * xs * 256) * np.sin(TAU * ys * 256)
    noise = n01(fbm(n, 2.0, seed))
    color = lerp(rgb(base), rgb('#5c0d10'), noise * 0.5)
    d = np.abs(ys - 0.5)
    border = smoothstep(0.38, 0.385, d) * (1 - smoothstep(0.43, 0.435, d))
    edge = smoothstep(0.465, 0.47, d)
    diamond = np.abs(((xs * 4) % 1.0) - 0.5) + np.abs(ys - 0.5) * 2.2
    motif = smoothstep(0.30, 0.31, diamond) * (1 - smoothstep(0.34, 0.35, diamond))
    color = lerp(color, rgb(trim), np.clip(border + edge * 0.8 + motif * (d < 0.36) * 0.8, 0, 1))
    color *= (0.9 + 0.1 * weave)[..., None]
    h = weave * 0.5 + noise * 0.5
    return dict(color=np.clip(color, 0, 1), normal=normal_from_height(h, 0.0004), rough=0.95)


def banner(w=256, h=512, seed=13, base='#6d1016', trim='#d4af5a'):
    xs, ys = grid(h, w)
    noise = n01(fbm(h, 2.0, seed, m=w))
    color = lerp(rgb(base), rgb('#4a0a0e'), noise * 0.6)
    bx = np.minimum(xs, 1 - xs)
    by = np.minimum(ys, 1 - ys) * (h / w)
    b = np.minimum(bx, by)
    border = smoothstep(0.04, 0.045, b) * (1 - smoothstep(0.07, 0.075, b))
    cx, cy = 0.5, 0.58
    px = (xs - cx)
    py = (ys - cy) * (h / w)
    r = np.sqrt(px * px + py * py)
    ring = smoothstep(0.27, 0.28, r) * (1 - smoothstep(0.31, 0.32, r))
    ang = np.arctan2(py, px)
    star_r = 0.12 + 0.1 * (0.5 + 0.5 * np.cos(ang * 8))
    star = 1 - smoothstep(star_r - 0.01, star_r, r)
    color = lerp(color, rgb(trim), np.clip(border + ring + star, 0, 1))
    return dict(color=color, rough=0.9)


def painting(seed, w=512, h=384):
    """Small romantic landscape. Not tileable."""
    rng = np.random.default_rng(seed)
    xs, ys = grid(h, w)
    palettes = [
        ('#f6c27a', '#d9735a', '#3b4a6b', '#20283d'),
        ('#cfe3f0', '#8fb3cf', '#3d5a4a', '#1d2a22'),
        ('#f3d9a4', '#c58d5b', '#5d4b3a', '#2a2018'),
        ('#e8c3c9', '#9b7fb0', '#3d3b5c', '#171628'),
    ]
    hz, sky, far, near = palettes[seed % len(palettes)]
    color = lerp(rgb(hz), rgb(sky), smoothstep(0.35, 1.0, ys))
    sx, sy = 0.25 + 0.5 * rng.random(), 0.55 + 0.25 * rng.random()
    d = np.sqrt(((xs - sx) * w / h) ** 2 + (ys - sy) ** 2)
    color = lerp(color, rgb('#fff4d6'), (1 - smoothstep(0.035, 0.045, d)))
    color = lerp(color, rgb('#fff1c9'), np.exp(-d * 6) * 0.35)
    clouds = smoothstep(0.55, 0.85, n01(fbm(h, 2.4, seed + 5, aniso=(1.0, 3.0), m=w)))
    color = lerp(color, rgb('#fbf3e6'), clouds * smoothstep(0.5, 0.8, ys) * 0.5)
    layers = 4
    for i in range(layers):
        k = i / (layers - 1)
        ridge = 0.62 - 0.16 * i + (0.10 - 0.02 * i) * fbm1d(w, 2.2 + 0.2 * i, seed * 10 + i)
        mask = ys < ridge[None, :]
        c = lerp(lerp(rgb(hz), rgb(far), 0.55), rgb(near), k)
        color = np.where(mask[..., None], c, color)
    brush = fbm(h, 1.2, seed + 9, aniso=(3.0, 1.0), m=w)
    color = color * (1 + 0.05 * brush[..., None])
    vig = smoothstep(0.85, 0.3, np.sqrt((xs - 0.5) ** 2 + (ys - 0.5) ** 2))
    color = color * (0.75 + 0.25 * vig[..., None])
    craq = smoothstep(0.0, 0.02, voronoi(128, 90, seed)[1] - voronoi(128, 90, seed)[0])
    craq = np.kron(craq, np.ones((h // 128 + 1, w // 128 + 1)))[:h, :w]
    color = color * (0.93 + 0.07 * craq[..., None])
    return dict(color=np.clip(color, 0, 1), rough=0.6)


def earth_map(w=1024, h=512, seed=14):
    """Equirectangular antique globe map."""
    xs, ys = grid(h, w)
    land = fbm(h, 2.6, seed, m=w)
    lat = np.abs(ys - 0.5) * 2
    land = land - lat * 0.6
    is_land = smoothstep(0.35, 0.45, land)
    ocean = lerp(rgb('#335a6e'), rgb('#4c7a87'), n01(fbm(h, 2.0, seed + 1, m=w)))
    ground = lerp(rgb('#c9b27a'), rgb('#8d8a4e'), n01(fbm(h, 2.0, seed + 2, m=w)))
    color = lerp(ocean, ground, is_land)
    coast = smoothstep(0.30, 0.35, land) * (1 - smoothstep(0.45, 0.5, land))
    color = lerp(color, rgb('#5d4a2a'), coast * 0.6)
    gx = np.abs(((xs * 12) % 1.0) - 0.5)
    gy = np.abs(((ys * 6) % 1.0) - 0.5)
    lines = np.maximum(smoothstep(0.48, 0.5, gx), smoothstep(0.48, 0.5, gy))
    color = lerp(color, rgb('#e8dcb5'), lines * 0.35)
    return dict(color=np.clip(color, 0, 1), rough=0.5)


def terracotta(w=512, h=512, seed=15):
    """Amphora surface: terracotta with a black meander band (v = height)."""
    xs, ys = grid(h, w)
    noise = n01(fbm(h, 2.0, seed, m=w))
    color = lerp(rgb('#b5582e'), rgb('#9a4422'), noise)
    band = (ys > 0.48) & (ys < 0.66)
    color = np.where(band[..., None], rgb('#1b1411'), color)
    u = (xs * 16) % 1.0
    v = (ys - 0.48) / 0.18
    key = ((u < 0.15) | (v < 0.15) | ((v > 0.75) & (u < 0.7)) | ((u > 0.55) & (u < 0.7) & (v > 0.3))
           | ((v > 0.3) & (v < 0.45) & (u > 0.3) & (u < 0.7)))
    color = np.where((band & key)[..., None], rgb('#c4683a'), color)
    for y0 in (0.25, 0.78, 0.82):
        color = lerp(color, rgb('#1b1411'), (np.abs(ys - y0) < 0.008).astype(float))
    return dict(color=color, rough=0.75)


def dice_face(n=256):
    """Ivory with six pip layouts in a 3x2 atlas (w = 3n, h = 2n)."""
    w, h = 3 * n, 2 * n
    xs, ys = grid(h, w)
    color = np.ones((h, w, 3)) * rgb('#f3ede0')
    layouts = {
        1: [(0.5, 0.5)],
        2: [(0.25, 0.25), (0.75, 0.75)],
        3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
        4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
        5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],
        6: [(0.25, 0.22), (0.75, 0.22), (0.25, 0.5), (0.75, 0.5), (0.25, 0.78), (0.75, 0.78)],
    }
    pip = np.zeros((h, w))
    for k, pts in layouts.items():
        cx0 = ((k - 1) % 3) / 3.0
        cy0 = ((k - 1) // 3) / 2.0
        for px, py in pts:
            dx = (xs - (cx0 + px / 3.0)) * 3
            dy = (ys - (cy0 + py / 2.0)) * 2
            r = np.sqrt(dx * dx + dy * dy)
            pip = np.maximum(pip, 1 - smoothstep(0.08, 0.095, r))
    color = lerp(color, rgb('#1d1a18'), pip)
    h_map = 1 - pip
    return dict(color=color, normal=normal_from_height(blur(h_map), 0.01), rough=0.35)
