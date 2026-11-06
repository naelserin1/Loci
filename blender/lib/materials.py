"""Blender material creation (Principled BSDF) from procedural textures.

Texture maps are written to blender/.cache/textures as JPEG and loaded as
image textures, so the glTF exporter embeds them in the GLB. The node layout
follows the conventions the Blender glTF exporter understands:
  * Base Color  <- Image (sRGB)
  * Roughness   <- Separate Color(G) <- Image (Non-Color, packed ORM)
  * Normal      <- Normal Map <- Image (Non-Color)
"""

import os

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, '..', '.cache', 'textures')
MAX_DATA_RES = 512  # normal / roughness maps


def _save(name, arr, kind):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.abspath(os.path.join(CACHE, f'{name}_{kind}.jpg'))
    if kind != 'color':
        while arr.shape[0] > MAX_DATA_RES and arr.shape[0] % 2 == 0 and arr.shape[1] % 2 == 0:
            arr = 0.25 * (arr[0::2, 0::2] + arr[1::2, 0::2] + arr[0::2, 1::2] + arr[1::2, 1::2])
    h, w = arr.shape[:2]
    if arr.ndim == 2:
        arr = np.dstack([arr, arr, arr])
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = np.clip(arr, 0, 1)
    img = bpy.data.images.new(f'{name}_{kind}', w, h, alpha=False)
    img.colorspace_settings.name = 'sRGB' if kind == 'color' else 'Non-Color'
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = 'JPEG'
    img.save(filepath=path, quality=88)
    img.source = 'FILE'
    img.filepath = path
    img.reload()
    return img


def make(name, tex=None, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0,
         emission=None, emission_strength=0.0, normal_strength=1.0, alpha=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*_lin(color), 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if tex is not None:
        if 'color' in tex:
            img = _save(name, tex['color'], 'color')
            n = nt.nodes.new('ShaderNodeTexImage')
            n.image = img
            nt.links.new(n.outputs['Color'], bsdf.inputs['Base Color'])
        if 'rough' in tex and np.ndim(tex['rough']) == 2:
            r = np.clip(tex['rough'], 0.02, 1.0)
            orm = np.dstack([np.ones_like(r), r, np.full_like(r, metal)])
            img = _save(name, orm, 'orm')
            n = nt.nodes.new('ShaderNodeTexImage')
            n.image = img
            sep = nt.nodes.new('ShaderNodeSeparateColor')
            nt.links.new(n.outputs['Color'], sep.inputs['Color'])
            nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
            if metal > 0:
                nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
        elif 'rough' in tex:
            bsdf.inputs['Roughness'].default_value = float(tex['rough'])
        if 'normal' in tex:
            img = _save(name, tex['normal'], 'normal')
            n = nt.nodes.new('ShaderNodeTexImage')
            n.image = img
            nm = nt.nodes.new('ShaderNodeNormalMap')
            nm.inputs['Strength'].default_value = normal_strength
            nt.links.new(n.outputs['Color'], nm.inputs['Color'])
            nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    if emission is not None:
        bsdf.inputs['Emission Color'].default_value = (*_lin(emission), 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    if alpha is not None:
        bsdf.inputs['Alpha'].default_value = alpha
        mat.surface_render_method = 'BLENDED'
    return mat


def _lin(c):
    """sRGB -> linear for socket default values."""
    if isinstance(c, str):
        c = tuple(int(c.lstrip('#')[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    def f(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(f(v) for v in c)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
