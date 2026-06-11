import importlib

if "bpy" in locals():
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(panels)
    importlib.reload(scene)
    importlib.reload(scene.registry)

import bpy

from . import operators, panels, properties
from .scene import registry

bl_info = {
    "name": "Auth Head Ingestion",
    "author": "Genies",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Auth Head",
    "description": "Register and persist pipeline scene objects in the blend file",
    "category": "Mesh",
}


def register():
    for cls in properties.CLASSES:
        bpy.utils.register_class(cls)
    for cls in operators.CLASSES:
        bpy.utils.register_class(cls)
    for cls in panels.CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.auth_head_objects = bpy.props.PointerProperty(
        type=properties.AUTHHEAD_PG_SceneObjects,
    )


def unregister():
    del bpy.types.Scene.auth_head_objects

    for cls in reversed(panels.CLASSES):
        bpy.utils.unregister_class(cls)
    for cls in reversed(operators.CLASSES):
        bpy.utils.unregister_class(cls)
    for cls in reversed(properties.CLASSES):
        bpy.utils.unregister_class(cls)
