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


def log_shared_mesh_targets(scene) -> None:
    batch = scene.auth_head_batch
    mesh_to_objects: dict[str, list[str]] = {}

    def track(slot_id: str) -> None:
        obj = get_registered_object(scene, slot_id)
        if obj is None or obj.type != "MESH":
            return
        mesh_to_objects.setdefault(obj.data.name, []).append(f"{slot_id} ({obj.name})")

    if batch.apply_head:
        track(HEAD_SLOT)
    if batch.apply_l_wedge:
        for slot_id in LEFT_WEDGE_SLOTS:
            track(slot_id)
    if batch.apply_r_wedge:
        for slot_id in RIGHT_WEDGE_SLOTS:
            track(slot_id)
    if batch.apply_eyes:
        for slot_id in ("l_eyes", "r_eyes"):
            track(slot_id)
    if batch.apply_hd_eyes:
        for slot_id in ("l_hd_eyes", "r_hd_eyes"):
            track(slot_id)

    for mesh_name, slots in sorted(mesh_to_objects.items()):
        if len(slots) > 1:
            log(
                scene,
                f"Shared mesh '{mesh_name}' used by: {', '.join(slots)}",
                level="WARN",
                force=True,
            )


def iter_batch_target_objects(scene):
    batch = scene.auth_head_batch
    seen_meshes = set()

    def yield_obj(obj):
        if obj is None or obj.type != "MESH":
            return
        mesh_name = obj.data.name
        if mesh_name in seen_meshes:
            return
        seen_meshes.add(mesh_name)
        yield obj

    if batch.apply_head:
        yield from yield_obj(get_registered_object(scene, HEAD_SLOT))
    if batch.apply_l_wedge:
        for slot_id in LEFT_WEDGE_SLOTS:
            yield from yield_obj(get_registered_object(scene, slot_id))
    if batch.apply_r_wedge:
        for slot_id in RIGHT_WEDGE_SLOTS:
            yield from yield_obj(get_registered_object(scene, slot_id))
    if batch.apply_eyes:
        for slot_id in ("l_eyes", "r_eyes"):
            yield from yield_obj(get_registered_object(scene, slot_id))
    if batch.apply_hd_eyes:
        for slot_id in ("l_hd_eyes", "r_hd_eyes"):
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


def _write_shape_key_coords(
    key_block,
    target_obj: bpy.types.Object,
    source_obj: bpy.types.Object,
) -> float:
    source_mesh = source_obj.data
    src_matrix = source_obj.matrix_world
    tgt_matrix_inv = target_obj.matrix_world.inverted()

    max_delta = 0.0
    for index, sk_vert in enumerate(key_block.data):
        world_co = src_matrix @ source_mesh.vertices[index].co
        local_co = tgt_matrix_inv @ world_co
        sk_vert.co = local_co
        basis_co = target_obj.data.vertices[index].co
        max_delta = max(max_delta, (local_co - basis_co).length)
    return max_delta


def add_shape_from_mesh(
    target_obj: bpy.types.Object,
    source_obj: bpy.types.Object,
    key_name: str,
    scene=None,
    applied_mesh_keys: set | None = None,
) -> str:
    mesh_name = target_obj.data.name
    mesh_token = (mesh_name, key_name)

    if applied_mesh_keys is not None and mesh_token in applied_mesh_keys:
        if scene is not None:
            log(
                scene,
                f"Skipping '{target_obj.name}' — '{key_name}' already applied to mesh '{mesh_name}'",
                force=True,
            )
        return "skipped_shared_mesh"

    if scene is not None:
        log(
            scene,
            f"Applying shape key '{key_name}': "
            f"source='{source_obj.name}' → target='{target_obj.name}' (mesh='{mesh_name}')",
            force=True,
        )

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
                force=True,
            )
        raise ValueError(
            f"Vertex count mismatch on '{target_obj.name}' "
            f"({target_vert_count} vs {source_vert_count})"
        )

    had_shape_keys = target_obj.data.shape_keys is not None
    ensure_basis(target_obj)
    if scene is not None and not had_shape_keys:
        log(scene, f"Created Basis shape key on '{target_obj.name}'", force=True)

    if shape_key_exists(target_obj, key_name):
        key_block = target_obj.data.shape_keys.key_blocks[key_name]
        action = "updated"
    else:
        key_block = target_obj.shape_key_add(name=key_name, from_mix=False)
        action = "added"

    if scene is not None:
        src_t = source_obj.matrix_world.translation
        tgt_t = target_obj.matrix_world.translation
        log(
            scene,
            f"Transforms — source world ({src_t.x:.4f}, {src_t.y:.4f}, {src_t.z:.4f}) "
            f"target world ({tgt_t.x:.4f}, {tgt_t.y:.4f}, {tgt_t.z:.4f})",
            force=True,
        )

    max_delta = _write_shape_key_coords(key_block, target_obj, source_obj)
    key_block.value = 0.0

    if applied_mesh_keys is not None:
        applied_mesh_keys.add(mesh_token)

    if scene is not None:
        log(
            scene,
            f"Shape key '{key_name}' {action} on '{target_obj.name}' "
            f"(verts={len(key_block.data)}, max delta from basis={max_delta:.6f})",
            force=True,
        )

    return action
