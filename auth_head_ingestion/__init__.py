import importlib

if "bpy" in locals():
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(panels)
    importlib.reload(ui_lists)
    importlib.reload(core)
    importlib.reload(core.naming)
    importlib.reload(core.fbx_scan)
    importlib.reload(scene)
    importlib.reload(scene.registry)
    importlib.reload(scene.batch_load)

import bpy

from . import core, operators, panels, properties, ui_lists
from .scene import registry

bl_info = {
    "name": "Auth Head Ingestion",
    "author": "Genies",
    "version": (0, 2, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Auth Head",
    "description": "Register pipeline scene objects and batch-load authored head FBX as shape keys",
    "category": "Mesh",
}


def register():
    for cls in properties.CLASSES:
        bpy.utils.register_class(cls)
    for cls in ui_lists.CLASSES:
        bpy.utils.register_class(cls)
    for cls in operators.CLASSES:
        bpy.utils.register_class(cls)
    for cls in panels.CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.auth_head_objects = bpy.props.PointerProperty(
        type=properties.AUTHHEAD_PG_SceneObjects,
    )
    bpy.types.Scene.auth_head_batch = bpy.props.PointerProperty(
        type=properties.AUTHHEAD_PG_BatchLoad,
    )


def unregister():
    del bpy.types.Scene.auth_head_batch
    del bpy.types.Scene.auth_head_objects

    for cls in reversed(panels.CLASSES):
        bpy.utils.unregister_class(cls)
    for cls in reversed(operators.CLASSES):
        bpy.utils.unregister_class(cls)
    for cls in reversed(ui_lists.CLASSES):
        bpy.utils.unregister_class(cls)
    for cls in reversed(properties.CLASSES):
        bpy.utils.unregister_class(cls)
