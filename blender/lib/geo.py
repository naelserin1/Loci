"""Geometry helpers for building low-poly-but-detailed scenes with bpy.

Geometry is accumulated per material in MeshBuilder objects (positions, UVs
and explicit per-corner normals) and turned into real Blender meshes at the
end. This keeps the exported glTF to roughly one draw call per material.
"""

import math
from collections import defaultdict

import bpy
from mathutils import Matrix, Vector

IDENTITY = Matrix.Identity(4)


class MeshBuilder:
    def __init__(self):
        self.verts = []
        self.faces = []
        self.uvs = []
        self.normals = []

    def poly(self, pts, uvs, normals):
        i = len(self.verts)
        self.verts.extend(tuple(p) for p in pts)
        self.faces.append(tuple(range(i, i + len(pts))))
        self.uvs.extend(tuple(u) for u in uvs)
        self.normals.extend(tuple(n) for n in normals)

    def empty(self):
        return not self.faces

    def to_object(self, name, material, collection=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        uvl = me.uv_layers.new(name='UVMap')
        flat = [c for uv in self.uvs for c in uv]
        uvl.data.foreach_set('uv', flat)
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.normals_split_custom_set([Vector(n).normalized() for n in self.normals])
        me.materials.append(material)
        me.update()
        ob = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        return ob


class Scene:
    """Registry of mesh builders keyed by material name."""

    def __init__(self):
        self.builders = defaultdict(MeshBuilder)

    def __getitem__(self, mat):
        return self.builders[mat]

    def build(self, materials, prefix='', collection=None, parent=None):
        objs = []
        for mat_name, mb in self.builders.items():
            if mb.empty():
                continue
            ob = mb.to_object(f'{prefix}{mat_name}', materials[mat_name], collection)
            if parent is not None:
                ob.parent = parent
            objs.append(ob)
        return objs


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def _xf(M, p):
    return M @ Vector(p)


def _xn(M, n):
    return (M.to_3x3() @ Vector(n)).normalized()


def world_uv(p, n, tile):
    ax = max(range(3), key=lambda i: abs(n[i]))
    if ax == 2:
        return (p[0] / tile, p[1] / tile)
    if ax == 0:
        return (p[1] / tile, p[2] / tile)
    return (p[0] / tile, p[2] / tile)


def box(mb, lo, hi, tile=1.0, M=IDENTITY, skip=(), uv=None):
    """Axis-aligned (in local space) box from corner lo to corner hi.

    skip: faces to omit, any of '+x','-x','+y','-y','+z','-z'.
    uv  : None for world-space projection, or 'unit' to map each face 0..1.
    """
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    faces = {
        '+x': ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0)),
        '-x': ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], (-1, 0, 0)),
        '+y': ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0, 1, 0)),
        '-y': ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
        '+z': ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)),
        '-z': ([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], (0, 0, -1)),
    }
    unit = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for key, (pts, n) in faces.items():
        if key in skip:
            continue
        wp = [_xf(M, p) for p in pts]
        wn = _xn(M, n)
        if uv == 'unit':
            uvs = unit
        else:
            uvs = [world_uv(p, wn, tile) for p in wp]
        mb.poly(wp, uvs, [wn] * 4)


def quad(mb, pts, uvs, M=IDENTITY):
    wp = [_xf(M, p) for p in pts]
    n = (wp[1] - wp[0]).cross(wp[2] - wp[0]).normalized()
    mb.poly(wp, uvs, [n] * len(wp))


def lathe(mb, profile, segs=24, M=IDENTITY, tile=1.0, cap_bottom=True, cap_top=True,
          sharp_deg=35.0, arc=(0.0, 2 * math.pi), uv_unit=False):
    """Revolve a (radius, z) profile around local Z.

    Profile points go bottom -> top. Normals are smoothed along the profile
    unless the turn is sharper than sharp_deg.
    """
    pr = [(float(r), float(z)) for r, z in profile]
    nseg = len(pr) - 1
    seg_n = []
    for i in range(nseg):
        (r0, z0), (r1, z1) = pr[i], pr[i + 1]
        dr, dz = r1 - r0, z1 - z0
        L = math.hypot(dr, dz) or 1.0
        seg_n.append((dz / L, -dr / L))
    n_start, n_end = [], []
    cos_lim = math.cos(math.radians(sharp_deg))
    for i in range(nseg):
        def blend(a, b):
            if a[0] * b[0] + a[1] * b[1] > cos_lim:
                x, y = a[0] + b[0], a[1] + b[1]
                L = math.hypot(x, y) or 1.0
                return (x / L, y / L)
            return a
        n_start.append(blend(seg_n[i], seg_n[i - 1]) if i > 0 else seg_n[i])
        n_end.append(blend(seg_n[i], seg_n[i + 1]) if i < nseg - 1 else seg_n[i])
    rmax = max(r for r, _ in pr) or 1.0
    lens = [0.0]
    for i in range(nseg):
        lens.append(lens[-1] + math.hypot(pr[i + 1][0] - pr[i][0], pr[i + 1][1] - pr[i][1]))
    a0, a1 = arc
    full = abs((a1 - a0) - 2 * math.pi) < 1e-6
    angs = [a0 + (a1 - a0) * k / segs for k in range(segs + 1)]
    for i in range(nseg):
        (r0, z0), (r1, z1) = pr[i], pr[i + 1]
        if r0 < 1e-6 and r1 < 1e-6:
            continue
        for k in range(segs):
            A, B = angs[k], angs[k + 1]
            ca, sa, cb, sb = math.cos(A), math.sin(A), math.cos(B), math.sin(B)
            pts = [(r0 * ca, r0 * sa, z0), (r0 * cb, r0 * sb, z0),
                   (r1 * cb, r1 * sb, z1), (r1 * ca, r1 * sa, z1)]
            ns = [(n_start[i][0] * ca, n_start[i][0] * sa, n_start[i][1]),
                  (n_start[i][0] * cb, n_start[i][0] * sb, n_start[i][1]),
                  (n_end[i][0] * cb, n_end[i][0] * sb, n_end[i][1]),
                  (n_end[i][0] * ca, n_end[i][0] * sa, n_end[i][1])]
            if uv_unit:
                uvs = [(k / segs, lens[i] / lens[-1]), ((k + 1) / segs, lens[i] / lens[-1]),
                       ((k + 1) / segs, lens[i + 1] / lens[-1]), (k / segs, lens[i + 1] / lens[-1])]
            else:
                uvs = [(A * rmax / tile, lens[i] / tile), (B * rmax / tile, lens[i] / tile),
                       (B * rmax / tile, lens[i + 1] / tile), (A * rmax / tile, lens[i + 1] / tile)]
            if r0 < 1e-6:
                pts, ns, uvs = pts[1:], ns[1:], uvs[1:]
            elif r1 < 1e-6:
                pts, ns, uvs = pts[:3], ns[:3], uvs[:3]
            mb.poly([_xf(M, p) for p in pts], uvs, [_xn(M, n) for n in ns])
    if not full:
        return

    def cap(r, z, up):
        if r < 1e-6:
            return
        ks = range(segs) if up else range(segs - 1, -1, -1)
        pts = [(r * math.cos(angs[k]), r * math.sin(angs[k]), z) for k in ks]
        uvs = [(p[0] / tile, p[1] / tile) for p in pts]
        n = _xn(M, (0, 0, 1 if up else -1))
        mb.poly([_xf(M, p) for p in pts], uvs, [n] * len(pts))

    if cap_bottom:
        cap(pr[0][0], pr[0][1], False)
    if cap_top:
        cap(pr[-1][0], pr[-1][1], True)


def cylinder(mb, r, z0, z1, segs=24, M=IDENTITY, tile=1.0, **kw):
    lathe(mb, [(r, z0), (r, z1)], segs, M, tile, **kw)


def sphere(mb, r, segs=24, rings=12, M=IDENTITY, tile=1.0, squash=1.0, uv_unit=False):
    prof = [(r * math.sin(math.pi * i / rings), -r * math.cos(math.pi * i / rings) * squash)
            for i in range(rings + 1)]
    lathe(mb, prof, segs, M, tile, cap_bottom=False, cap_top=False, sharp_deg=80, uv_unit=uv_unit)


def tube(mb, path, radius, segs=12, closed=False, M=IDENTITY, tile=1.0, up=(0, 0, 1), caps=True):
    """Sweep a circle along a polyline path (list of 3D points)."""
    P = [Vector(p) for p in path]
    n = len(P)
    tangents = []
    for i in range(n):
        if closed:
            t = P[(i + 1) % n] - P[i - 1]
        else:
            t = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]
        tangents.append(t.normalized())
    upv = Vector(up)
    frames = []
    ref = upv if abs(tangents[0].dot(upv)) < 0.95 else Vector((1, 0, 0))
    b = tangents[0].cross(ref).normalized()
    for i in range(n):
        t = tangents[i]
        nrm = b.cross(t).normalized()
        b = t.cross(nrm).normalized()
        frames.append((nrm, b))
    rings = []
    for i in range(n):
        nrm, bn = frames[i]
        ring = []
        for k in range(segs + 1):
            a = 2 * math.pi * k / segs
            d = nrm * math.cos(a) + bn * math.sin(a)
            ring.append((P[i] + d * radius, d))
        rings.append(ring)
    count = n if closed else n - 1
    dist = [0.0]
    for i in range(1, n + 1 if closed else n):
        dist.append(dist[-1] + (P[i % n] - P[i - 1]).length)
    for i in range(count):
        r0, r1 = rings[i], rings[(i + 1) % n]
        for k in range(segs):
            pts = [r0[k][0], r0[k + 1][0], r1[k + 1][0], r1[k][0]]
            ns = [r0[k][1], r0[k + 1][1], r1[k + 1][1], r1[k][1]]
            uvs = [(k / segs, dist[i] / tile), ((k + 1) / segs, dist[i] / tile),
                   ((k + 1) / segs, dist[i + 1] / tile), (k / segs, dist[i + 1] / tile)]
            mb.poly([_xf(M, p) for p in pts], uvs, [_xn(M, v) for v in ns])
    if caps and not closed:
        for idx, sign in ((0, -1), (n - 1, 1)):
            ring = rings[idx][:-1]
            pts = [p for p, _ in ring]
            if sign < 0:
                pts = pts[::-1]
            nn = tangents[idx] * sign
            mb.poly([_xf(M, p) for p in pts], [(0, 0)] * len(pts), [_xn(M, nn)] * len(pts))


def torus(mb, R, r, segs=32, tube_segs=12, M=IDENTITY, tile=1.0, arc=2 * math.pi):
    closed = abs(arc - 2 * math.pi) < 1e-6
    steps = segs if closed else segs + 1
    path = [(R * math.cos(arc * i / segs), R * math.sin(arc * i / segs), 0) for i in range(steps)]
    tube(mb, path, r, tube_segs, closed=closed, M=M, tile=tile)


def prism(mb, poly2d, z0, z1, M=IDENTITY, tile=1.0, cap_bottom=True, cap_top=True, smooth=False):
    """Extrude a CCW 2D polygon along local Z."""
    pts = [Vector((x, y, 0)) for x, y in poly2d]
    n = len(pts)
    dist = 0.0
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        e = b - a
        nn = Vector((e.y, -e.x, 0)).normalized()
        q = [(a.x, a.y, z0), (b.x, b.y, z0), (b.x, b.y, z1), (a.x, a.y, z1)]
        L = e.length
        uvs = [(dist / tile, z0 / tile), ((dist + L) / tile, z0 / tile),
               ((dist + L) / tile, z1 / tile), (dist / tile, z1 / tile)]
        dist += L
        mb.poly([_xf(M, p) for p in q], uvs, [_xn(M, nn)] * 4)
    if cap_top:
        q = [(p.x, p.y, z1) for p in pts]
        mb.poly([_xf(M, p) for p in q], [(p[0] / tile, p[1] / tile) for p in q], [_xn(M, (0, 0, 1))] * n)
    if cap_bottom:
        q = [(p.x, p.y, z0) for p in pts[::-1]]
        mb.poly([_xf(M, p) for p in q], [(p[0] / tile, p[1] / tile) for p in q], [_xn(M, (0, 0, -1))] * n)


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def Rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def Rx(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'X')


def Ry(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Y')


def S(s):
    return Matrix.Scale(s, 4)
