import bpy

from ..core.facial import is_auth_shape_key, is_base_auth_shape_key, is_split_auth_shape_key
from ..properties import ALL_SLOT_IDS, SLOT_SECTIONS
from .registry import get_registered_object

SLOT_LABELS = {
    slot_id: label
    for _title, _icon, slots in SLOT_SECTIONS
    for slot_id, label in slots
}


def iter_registered_mesh_objects(scene):
    seen_meshes: set[str] = set()
    for slot_id in ALL_SLOT_IDS:
        obj = get_registered_object(scene, slot_id)
        if obj is None or obj.type != "MESH":
            continue
        mesh_name = obj.data.name
        if mesh_name in seen_meshes:
            continue
        seen_meshes.add(mesh_name)
        yield obj


def iter_registered_object_slots(scene):
    for slot_id in ALL_SLOT_IDS:
        obj = get_registered_object(scene, slot_id)
        if obj is not None and obj.type == "MESH":
            yield slot_id, obj


def _object_has_shape_key(obj: bpy.types.Object, name: str) -> bool:
    shape_keys = obj.data.shape_keys
    return shape_keys is not None and name in shape_keys.key_blocks


def count_split_keys_for_base(scene, base_name: str) -> int:
    prefix = f"{base_name}_"
    split_names: set[str] = set()
    for obj in iter_registered_mesh_objects(scene):
        shape_keys = obj.data.shape_keys
        if shape_keys is None:
            continue
        for key_block in shape_keys.key_blocks:
            if key_block.name.startswith(prefix) and is_split_auth_shape_key(key_block.name):
                split_names.add(key_block.name)
    return len(split_names)


def collect_auth_shape_key_names(scene, *, include_splits: bool = False) -> list[str]:
    names: set[str] = set()
    for obj in iter_registered_mesh_objects(scene):
        shape_keys = obj.data.shape_keys
        if shape_keys is None:
            continue
        for key_block in shape_keys.key_blocks:
            name = key_block.name
            if not is_auth_shape_key(name):
                continue
            if include_splits:
                names.add(name)
            elif is_base_auth_shape_key(name):
                names.add(name)
    return sorted(names)


def get_variant_mesh_count(scene, shape_key_name: str) -> int:
    count = 0
    for obj in iter_registered_mesh_objects(scene):
        if _object_has_shape_key(obj, shape_key_name):
            count += 1
    return count


def get_keys_to_delete(scene, shape_key_name: str, *, include_splits: bool) -> set[str]:
    keys = {shape_key_name}
    if include_splits and is_base_auth_shape_key(shape_key_name):
        prefix = f"{shape_key_name}_"
        for obj in iter_registered_mesh_objects(scene):
            shape_keys = obj.data.shape_keys
            if shape_keys is None:
                continue
            for key_block in shape_keys.key_blocks:
                if key_block.name.startswith(prefix) and is_auth_shape_key(key_block.name):
                    keys.add(key_block.name)
    return keys


def zero_all_auth_shape_keys(scene) -> int:
    count = 0
    for obj in iter_registered_mesh_objects(scene):
        shape_keys = obj.data.shape_keys
        if shape_keys is None:
            continue
        for key_block in shape_keys.key_blocks:
            if is_auth_shape_key(key_block.name) and key_block.value != 0.0:
                key_block.value = 0.0
                count += 1

    _sync_preview_state(scene, "")
    return count


def set_solo_preview(scene, shape_key_name: str) -> None:
    for obj in iter_registered_mesh_objects(scene):
        shape_keys = obj.data.shape_keys
        if shape_keys is None:
            continue
        for key_block in shape_keys.key_blocks:
            if not is_auth_shape_key(key_block.name):
                continue
            if key_block.name == shape_key_name:
                key_block.value = 1.0
            else:
                key_block.value = 0.0

    _sync_preview_state(scene, shape_key_name)


def clear_variant_preview(scene, shape_key_name: str) -> None:
    for obj in iter_registered_mesh_objects(scene):
        shape_keys = obj.data.shape_keys
        if shape_keys is None or shape_key_name not in shape_keys.key_blocks:
            continue
        shape_keys.key_blocks[shape_key_name].value = 0.0

    viewer = scene.auth_head_viewer
    if viewer.active_preview == shape_key_name:
        _sync_preview_state(scene, "")


def _sync_preview_state(scene, shape_key_name: str) -> None:
    viewer = scene.auth_head_viewer
    viewer.active_preview = shape_key_name
    scene.auth_head_batch.preview_shape_key = shape_key_name


def refresh_variant_list(scene) -> int:
    viewer = scene.auth_head_viewer
    include_splits = viewer.show_split_keys
    selected_name = ""
    if viewer.variants and 0 <= viewer.variant_list_index < len(viewer.variants):
        selected_name = viewer.variants[viewer.variant_list_index].name

    key_names = collect_auth_shape_key_names(scene, include_splits=include_splits)
    viewer.variants.clear()
    for key_name in key_names:
        item = viewer.variants.add()
        item.name = key_name
        item.mesh_count = get_variant_mesh_count(scene, key_name)
        if is_base_auth_shape_key(key_name):
            item.split_count = count_split_keys_for_base(scene, key_name)
        else:
            item.split_count = 0

    if selected_name:
        for index, item in enumerate(viewer.variants):
            if item.name == selected_name:
                viewer.variant_list_index = index
                break
    else:
        viewer.variant_list_index = min(viewer.variant_list_index, max(0, len(viewer.variants) - 1))

    if viewer.active_preview and viewer.active_preview not in key_names:
        _sync_preview_state(scene, "")

    return len(viewer.variants)


def mark_fbx_loaded_state(scene, shape_key_name: str, *, loaded: bool) -> None:
    for item in scene.auth_head_batch.fbx_files:
        if item.shape_key_name == shape_key_name:
            item.already_loaded = loaded
            if not loaded:
                item.include_in_batch = True


def delete_auth_shape_keys(
    scene,
    shape_key_names: set[str],
) -> dict:
    removed = 0
    affected_objects: set[str] = set()

    for obj in iter_registered_mesh_objects(scene):
        shape_keys = obj.data.shape_keys
        if shape_keys is None:
            continue
        for key_name in sorted(shape_key_names, key=lambda name: name.count("_"), reverse=True):
            if key_name not in shape_keys.key_blocks:
                continue
            obj.shape_key_remove(shape_keys.key_blocks[key_name])
            removed += 1
            affected_objects.add(obj.name)

    for key_name in shape_key_names:
        if is_base_auth_shape_key(key_name):
            mark_fbx_loaded_state(scene, key_name, loaded=False)

    viewer = scene.auth_head_viewer
    if viewer.active_preview in shape_key_names:
        _sync_preview_state(scene, "")

    refresh_variant_list(scene)
    return {
        "removed": removed,
        "objects": sorted(affected_objects),
    }


def delete_selected_variant(scene, *, include_splits: bool) -> dict:
    viewer = scene.auth_head_viewer
    if not viewer.variants:
        raise ValueError("No auth shape keys in the viewer list")

    index = viewer.variant_list_index
    if index < 0 or index >= len(viewer.variants):
        raise ValueError("No auth variant selected")

    shape_key_name = viewer.variants[index].name
    keys = get_keys_to_delete(scene, shape_key_name, include_splits=include_splits)
    result = delete_auth_shape_keys(scene, keys)
    result["shape_key_name"] = shape_key_name
    result["deleted_keys"] = sorted(keys)
    return result


def delete_all_auth_variants(scene, *, include_splits: bool) -> dict:
    base_names = collect_auth_shape_key_names(scene, include_splits=False)
    keys: set[str] = set()
    for base_name in base_names:
        keys.update(get_keys_to_delete(scene, base_name, include_splits=include_splits))

    if include_splits:
        keys.update(collect_auth_shape_key_names(scene, include_splits=True))

    if not keys:
        raise ValueError("No auth shape keys found on registered objects")

    result = delete_auth_shape_keys(scene, keys)
    result["deleted_keys"] = sorted(keys)
    return result
