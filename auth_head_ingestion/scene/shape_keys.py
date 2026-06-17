import bpy

from ..core.naming import AUTH_SHAPE_KEY_PREFIX
from ..core.targets import HEAD_SLOT, LEFT_WEDGE_SLOTS, RIGHT_WEDGE_SLOTS
from .debug_log import log
from .registry import get_registered_object


def ensure_basis(obj: bpy.types.Object) -> None:
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
        obj.data.shape_keys.use_relative = True


def shape_key_exists(obj: bpy.types.Object, name: str) -> bool:
    if obj.data.shape_keys is None:
        return False
    return name in obj.data.shape_keys.key_blocks


def _is_auth_shape_key(name: str) -> bool:
    return name.startswith(AUTH_SHAPE_KEY_PREFIX)


def iter_batch_target_objects(scene):
    batch = scene.auth_head_batch
    seen = set()

    def yield_obj(obj):
        if obj is None or obj.name in seen:
            return
        seen.add(obj.name)
        yield obj

    if batch.apply_head:
        yield from yield_obj(get_registered_object(scene, HEAD_SLOT))
    if batch.apply_l_wedge:
        for slot_id in LEFT_WEDGE_SLOTS:
            yield from yield_obj(get_registered_object(scene, slot_id))
    if batch.apply_r_wedge:
        for slot_id in RIGHT_WEDGE_SLOTS:
            yield from yield_obj(get_registered_object(scene, slot_id))


def zero_auth_shape_keys(scene) -> None:
    for obj in iter_batch_target_objects(scene):
        shape_keys = obj.data.shape_keys
        if shape_keys is None:
            continue
        for key_block in shape_keys.key_blocks:
            if _is_auth_shape_key(key_block.name):
                key_block.value = 0.0


def set_active_preview_shape_key(scene, shape_key_name: str) -> None:
    for obj in iter_batch_target_objects(scene):
        shape_keys = obj.data.shape_keys
        if shape_keys is None:
            continue
        for key_block in shape_keys.key_blocks:
            if _is_auth_shape_key(key_block.name):
                key_block.value = 1.0 if key_block.name == shape_key_name else 0.0

    batch = scene.auth_head_batch
    batch.preview_shape_key = shape_key_name

    if batch.debug_verbose:
        log(scene, f"Preview shape key set to '{shape_key_name}'", force=True)


def add_shape_from_mesh(
    target_obj: bpy.types.Object,
    source_obj: bpy.types.Object,
    key_name: str,
    scene=None,
) -> None:
    if scene is not None:
        log(
            scene,
            f"Applying shape key '{key_name}': "
            f"source='{source_obj.name}' → target='{target_obj.name}'",
        )

    if shape_key_exists(target_obj, key_name):
        raise ValueError(f"Shape key '{key_name}' already exists on '{target_obj.name}'")

    source_mesh = source_obj.data
    target_vert_count = len(target_obj.data.vertices)
    source_vert_count = len(source_mesh.vertices)

    if target_vert_count != source_vert_count:
        if scene is not None:
            log(
                scene,
                f"Vertex count mismatch: target '{target_obj.name}'={target_vert_count} "
                f"source '{source_obj.name}'={source_vert_count}",
                level="ERROR",
            )
        raise ValueError(
            f"Vertex count mismatch on '{target_obj.name}' "
            f"({target_vert_count} vs {source_vert_count})"
        )

    had_shape_keys = target_obj.data.shape_keys is not None
    ensure_basis(target_obj)
    if scene is not None and not had_shape_keys:
        log(scene, f"Created Basis shape key on '{target_obj.name}'")

    key_block = target_obj.shape_key_add(name=key_name, from_mix=False)

    src_matrix = source_obj.matrix_world
    tgt_matrix_inv = target_obj.matrix_world.inverted()

    if scene is not None:
        src_t = src_matrix.translation
        tgt_t = target_obj.matrix_world.translation
        log(
            scene,
            f"Transforms — source world ({src_t.x:.4f}, {src_t.y:.4f}, {src_t.z:.4f}) "
            f"target world ({tgt_t.x:.4f}, {tgt_t.y:.4f}, {tgt_t.z:.4f})",
        )

    max_delta = 0.0
    for index, sk_vert in enumerate(key_block.data):
        world_co = src_matrix @ source_mesh.vertices[index].co
        local_co = tgt_matrix_inv @ world_co
        sk_vert.co = local_co
        basis_co = target_obj.data.vertices[index].co
        max_delta = max(max_delta, (local_co - basis_co).length)

    if scene is not None:
        log(
            scene,
            f"Shape key '{key_name}' added on '{target_obj.name}' "
            f"(verts={len(key_block.data)}, max delta from basis={max_delta:.6f})",
        )

    key_block.value = 0.0
