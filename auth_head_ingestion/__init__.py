import importlib

if "bpy" in locals():
    importlib.reload(properties)
    importlib.reload(operators_facial)
    importlib.reload(operators)
    importlib.reload(panels)
    importlib.reload(ui_lists)
    importlib.reload(core)
    importlib.reload(core.naming)
    importlib.reload(core.fbx_scan)
    importlib.reload(core.facial)
    importlib.reload(scene)
    importlib.reload(scene.registry)
    importlib.reload(scene.batch_load)
    importlib.reload(scene.fbx_import)
    importlib.reload(scene.shape_keys)
    importlib.reload(scene.batch_runner)
    importlib.reload(scene.debug_log)
    importlib.reload(scene.facial_registry)
    importlib.reload(scene.facial_bake)
    importlib.reload(core.targets)
    importlib.reload(preferences)

import bpy
from bpy.app.handlers import persistent

from . import core, operators, panels, preferences, properties, ui_lists
from .scene import registry
from .scene.debug_log import ensure_log_directory, log_dir

bl_info = {
    "name": "Auth Head Ingestion",
    "author": "Genies",
    "version": (0, 4, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Auth Head",
    "description": "Register pipeline scene objects, batch-load authored head FBX, and bake facial feature shape keys",
    "category": "Mesh",
}


@persistent
def _load_post(_dummy):
    scene = getattr(bpy.context, "scene", None)
    if scene is None:
        return
    batch = scene.auth_head_batch
    if batch.fbx_directory:
        preferences.save_fbx_directory(batch.fbx_directory)
    else:
        preferences.restore_fbx_directory_if_empty(scene)


def register():
    bpy.utils.register_class(preferences.AUTHHEAD_AddonPreferences)
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
    bpy.types.Scene.auth_head_facial = bpy.props.PointerProperty(
        type=properties.AUTHHEAD_PG_FacialFeatures,
    )

    log_path = ensure_log_directory()
    print(f"[AuthHeadIngestion] Log directory: {log_path}")

    scene = getattr(bpy.context, "scene", None)
    if scene is not None:
        preferences.restore_fbx_directory_if_empty(scene)

    if _load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_load_post)


def unregister():
    if _load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_load_post)

    del bpy.types.Scene.auth_head_facial
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
    bpy.utils.unregister_class(preferences.AUTHHEAD_AddonPreferences)
