import bpy
from bpy.props import StringProperty
from bpy.types import AddonPreferences


class AUTHHEAD_AddonPreferences(AddonPreferences):
    bl_idname = __package__.partition(".")[0]

    last_fbx_directory: StringProperty(
        name="Last FBX Directory",
        description="Last FBX source folder used for batch loading",
        subtype="DIR_PATH",
        default="",
    )


def get_preferences() -> AUTHHEAD_AddonPreferences | None:
    addon_key = __package__.partition(".")[0]
    addon = bpy.context.preferences.addons.get(addon_key)
    if addon is None:
        return None
    return addon.preferences


def save_fbx_directory(directory: str) -> None:
    if not directory:
        return
    prefs = get_preferences()
    if prefs is not None:
        prefs.last_fbx_directory = directory


def restore_fbx_directory_if_empty(scene) -> None:
    batch = scene.auth_head_batch
    if batch.fbx_directory:
        return

    prefs = get_preferences()
    if prefs is None or not prefs.last_fbx_directory:
        return

    batch.fbx_directory = prefs.last_fbx_directory
