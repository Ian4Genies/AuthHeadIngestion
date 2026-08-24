from mathutils.kdtree import KDTree

from ..core.facial import is_auth_shape_key
from ..core.targets import HEAD_SLOT
from .debug_log import log
from .registry import get_registered_object
from .shape_keys import ensure_basis

SIDE_BOOLEAN_SLOTS = {
    "l": "l_boolean_cutter",
    "r": "r_boolean_cutter",
}


def _basis_world_positions(obj):
    matrix = obj.matrix_world
    return [matrix @ vertex.co for vertex in obj.data.vertices]


def build_ring_vertex_map(head_obj, cutter_obj, *, tolerance=1e-3, scene=None, label=""):
    head_positions = _basis_world_positions(head_obj)
    tree = KDTree(len(head_positions))
    for index, co in enumerate(head_positions):
        tree.insert(co, index)
    tree.balance()

    vertex_map = []
    used_head_indices: dict[int, int] = {}
    unmatched = 0

    for cutter_index, co in enumerate(_basis_world_positions(cutter_obj)):
        _co, head_index, distance = tree.find(co)
        if head_index is None or distance > tolerance:
            unmatched += 1
            continue
        if head_index in used_head_indices:
            if scene is not None:
                log(
                    scene,
                    f"{label}: head vertex {head_index} matched by cutter vertices "
                    f"{used_head_indices[head_index]} and {cutter_index} — keeping the first",
                    level="WARN",
                    force=True,
                )
            continue
        used_head_indices[head_index] = cutter_index
        vertex_map.append((cutter_index, head_index))

    if scene is not None:
        log(
            scene,
            f"{label}: matched {len(vertex_map)}/{len(cutter_obj.data.vertices)} ring vertex(es) "
            f"('{cutter_obj.name}' → '{head_obj.name}', tolerance={tolerance})",
            force=True,
        )
        if unmatched:
            log(
                scene,
                f"{label}: {unmatched} cutter vertex(es) had no head match within tolerance",
                level="WARN",
                force=True,
            )

    return vertex_map


def apply_ring_shape_from_cutter(head_obj, cutter_obj, key_name, vertex_map, scene=None) -> int:
    cutter_shape_keys = cutter_obj.data.shape_keys
    if cutter_shape_keys is None or key_name not in cutter_shape_keys.key_blocks:
        raise ValueError(f"'{key_name}' not found on cutter '{cutter_obj.name}'")

    ensure_basis(head_obj)
    head_shape_keys = head_obj.data.shape_keys
    if key_name in head_shape_keys.key_blocks:
        head_key = head_shape_keys.key_blocks[key_name]
    else:
        head_key = head_obj.shape_key_add(name=key_name, from_mix=False)

    cutter_key = cutter_shape_keys.key_blocks[key_name]
    cutter_matrix = cutter_obj.matrix_world
    head_matrix_inv = head_obj.matrix_world.inverted()

    for cutter_index, head_index in vertex_map:
        world_co = cutter_matrix @ cutter_key.data[cutter_index].co
        head_key.data[head_index].co = head_matrix_inv @ world_co

    head_key.value = 0.0

    if scene is not None:
        log(
            scene,
            f"Eye frame sync '{key_name}': updated {len(vertex_map)} ring vertex(es) "
            f"on '{head_obj.name}' from '{cutter_obj.name}'",
            force=True,
        )

    return len(vertex_map)


def sync_eye_frame(scene, shape_key_name: str, *, sides=("l", "r")) -> dict:
    head_obj = get_registered_object(scene, HEAD_SLOT)
    if head_obj is None:
        return {"skipped": "head not registered"}

    results: dict = {}
    for side in sides:
        cutter_obj = get_registered_object(scene, SIDE_BOOLEAN_SLOTS[side])
        if cutter_obj is None:
            continue
        cutter_shape_keys = cutter_obj.data.shape_keys
        if cutter_shape_keys is None or shape_key_name not in cutter_shape_keys.key_blocks:
            continue

        vertex_map = build_ring_vertex_map(
            head_obj,
            cutter_obj,
            scene=scene,
            label=f"{side.upper()} eye frame",
        )
        results[side] = apply_ring_shape_from_cutter(
            head_obj,
            cutter_obj,
            shape_key_name,
            vertex_map,
            scene=scene,
        )

    return results


def sync_all_eye_frames(scene) -> dict:
    head_obj = get_registered_object(scene, HEAD_SLOT)
    if head_obj is None:
        raise ValueError("Register the head mesh first")

    cutters = {
        side: get_registered_object(scene, slot_id)
        for side, slot_id in SIDE_BOOLEAN_SLOTS.items()
    }
    if all(obj is None for obj in cutters.values()):
        raise ValueError("Register at least one boolean cutter mesh")

    shape_key_names: set[str] = set()
    for obj in cutters.values():
        if obj is None or obj.data.shape_keys is None:
            continue
        for key_block in obj.data.shape_keys.key_blocks:
            if is_auth_shape_key(key_block.name):
                shape_key_names.add(key_block.name)

    vertex_updates = 0
    for shape_key_name in sorted(shape_key_names):
        result = sync_eye_frame(scene, shape_key_name)
        vertex_updates += sum(count for count in result.values() if isinstance(count, int))

    return {
        "shape_keys": sorted(shape_key_names),
        "vertex_updates": vertex_updates,
    }
