"""Renders still images of the palace with Cycles (for checks and docs).

Usage:
    python blender/render_views.py [out_dir] [width] [samples] [view ...]
Reads blender/.cache/models/palace.glb and public/models/palace.json.
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))

VIEWS = {
    'vestibule': ((0.0, 1.0, 1.65), (0.0, 8.0, 1.9)),
    'library': ((7.0, 1.4, 1.7), (13.0, 6.5, 1.2)),
    'courtyard': ((12.0, 12.8, 1.7), (12.0, 18.0, 1.6)),
    'gallery': ((5.2, 18.0, 1.7), (-1.0, 14.5, 1.8)),
    'hall': ((0.0, 24.6, 1.7), (0.0, 36.0, 2.2)),
}


def from3(p):
    x, y, z = p
    return (x, -z, y)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    out = os.path.abspath(argv[0]) if argv else os.path.join(ROOT, 'docs')
    width = int(argv[1]) if len(argv) > 1 else 960
    samples = int(argv[2]) if len(argv) > 2 else 48
    views = argv[3:] or list(VIEWS)
    os.makedirs(out, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, '.cache', 'models', 'palace.glb'))
    data = json.load(open(os.path.join(ROOT, 'public', 'models', 'palace.json')))
    scene = bpy.context.scene

    for i, l in enumerate(data['lights']):
        ld = bpy.data.lights.new(f'L{i}', 'POINT')
        ld.energy = l['intensity'] * 6.0
        ld.shadow_soft_size = 0.15
        c = l['color'].lstrip('#')
        ld.color = tuple(int(c[k:k + 2], 16) / 255 for k in (0, 2, 4))
        ob = bpy.data.objects.new(f'L{i}', ld)
        ob.location = from3(l['pos'])
        scene.collection.objects.link(ob)

    sun = bpy.data.lights.new('sun', 'SUN')
    sun.energy = 4.5
    sun.angle = math.radians(1.5)
    sun.color = (1.0, 0.93, 0.82)
    sob = bpy.data.objects.new('sun', sun)
    d = Vector(from3(data['sun']['dir'])).normalized()
    sob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    scene.collection.objects.link(sob)

    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.45, 0.62, 0.95, 1)
    bg.inputs['Strength'].default_value = 0.7
    scene.world = world

    cam_d = bpy.data.cameras.new('cam')
    cam_d.lens = 20
    cam = bpy.data.objects.new('cam', cam_d)
    scene.collection.objects.link(cam)
    scene.camera = cam

    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.render.resolution_x = width
    scene.render.resolution_y = int(width * 9 / 16)
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.3
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 90

    for name in views:
        eye, target = VIEWS[name]
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(out, f'{name}.jpg')
        bpy.ops.render.render(write_still=True)
        print('rendered', name)


if __name__ == '__main__':
    main()
