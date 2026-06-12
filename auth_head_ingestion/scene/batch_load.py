import os

import bpy

from ..core.fbx_scan import list_fbx_files
from ..core.naming import fbx_filename_to_shape_key
from .registry import get_registered_object


def rescan_fbx_directory(scene) -> dict:
    batch = scene.auth_head_batch
    batch.fbx_files.clear()

    directory = bpy_path(batch.fbx_directory)
    if not directory or not os.path.isdir(directory):
        return {"count": 0, "skipped": 0}

    skipped = 0
    for filepath in list_fbx_files(directory):
        filename = os.path.basename(filepath)
        shape_key_name = fbx_filename_to_shape_key(filename)
        item = batch.fbx_files.add()
        item.filename = filename
        item.filepath = filepath
        item.shape_key_name = shape_key_name or ""
        item.include_in_batch = shape_key_name is not None
        item.already_loaded = False
        if shape_key_name is None:
            skipped += 1

    return {"count": len(batch.fbx_files), "skipped": skipped}


def compare_fbx_to_head_shape_keys(scene) -> dict:
    head = get_registered_object(scene, "head")
    if head is None or head.type != "MESH":
        return {"error": "no_head", "matched": 0}

    mesh = head.data
    if mesh.shape_keys is None:
        existing = set()
    else:
        existing = {key_block.name for key_block in mesh.shape_keys.key_blocks}

    matched = 0
    for item in scene.auth_head_batch.fbx_files:
        if item.shape_key_name and item.shape_key_name in existing:
            item.include_in_batch = False
            item.already_loaded = True
            matched += 1
        else:
            item.already_loaded = False

    return {"matched": matched, "total_keys": len(existing)}


def included_fbx_count(scene) -> int:
    batch = scene.auth_head_batch
    return sum(1 for item in batch.fbx_files if item.include_in_batch)


def bpy_path(path: str) -> str:
    return os.path.normpath(bpy.path.abspath(path)) if path else ""
