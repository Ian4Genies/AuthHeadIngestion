import bpy

from ..core.facial import is_base_auth_shape_key, split_shape_key_name
from ..core.targets import HEAD_SLOT
from .facial_registry import get_effective_vertex_group_name, iter_enabled_registrations, iter_registered_object_slots
from .registry import get_registered_object
from .shape_keys import ensure_basis, shape_key_exists


def list_auth_shape_keys_on_head(scene) -> list[str]:
    head = get_registered_object(scene, HEAD_SLOT)
    if head is None or head.type != "MESH" or head.data.shape_keys is None:
        return []

    keys = []
    for key_block in head.data.shape_keys.key_blocks:
        name = key_block.name
        if is_base_auth_shape_key(name):
            keys.append(name)
    return sorted(keys)


def _vertex_group_weights(mesh_obj: bpy.types.Object, group_name: str) -> list[float] | None:
    vertex_group = mesh_obj.vertex_groups.get(group_name)
    if vertex_group is None:
        return None

    weights = [0.0] * len(mesh_obj.data.vertices)
    group_index = vertex_group.index
    for vertex in mesh_obj.data.vertices:
        for group in vertex.groups:
            if group.group == group_index:
                weights[vertex.index] = group.weight
                break
    return weights


def _basis_key_block(mesh_obj: bpy.types.Object):
    shape_keys = mesh_obj.data.shape_keys
    if shape_keys is None:
        return None
    if "Basis" in shape_keys.key_blocks:
        return shape_keys.key_blocks["Basis"]
    return shape_keys.key_blocks[0]


def bake_masked_shape_key(
    mesh_obj: bpy.types.Object,
    auth_key_name: str,
    feature_name: str,
    mask_group_name: str,
    *,
    override_existing: bool,
) -> str:
    split_name = split_shape_key_name(auth_key_name, feature_name)
    shape_keys = mesh_obj.data.shape_keys
    if shape_keys is None or auth_key_name not in shape_keys.key_blocks:
        raise ValueError(f"Source shape key '{auth_key_name}' missing on '{mesh_obj.name}'")

    weights = _vertex_group_weights(mesh_obj, mask_group_name)
    if weights is None:
        raise ValueError(f"Vertex group '{mask_group_name}' not found on '{mesh_obj.name}'")

    if shape_key_exists(mesh_obj, split_name):
        if not override_existing:
            return "skipped"
        key_block = shape_keys.key_blocks[split_name]
        action = "updated"
    else:
        ensure_basis(mesh_obj)
        key_block = mesh_obj.shape_key_add(name=split_name, from_mix=False)
        action = "created"

    basis = _basis_key_block(mesh_obj)
    source = shape_keys.key_blocks[auth_key_name]

    for index, sk_vert in enumerate(key_block.data):
        influence = weights[index]
        sk_vert.co = basis.data[index].co.lerp(source.data[index].co, influence)

    key_block.value = 0.0
    return action


def bake_all_facial_features(scene, *, override_existing: bool) -> dict:
    facial = scene.auth_head_facial
    auth_keys = list_auth_shape_keys_on_head(scene)
    if not auth_keys:
        raise ValueError("No auth_* shape keys found on the registered head")

    created = 0
    updated = 0
    skipped = 0
    errors = []

    for auth_key_name in auth_keys:
        for object_slot, mesh_obj in iter_registered_object_slots(scene):
            for feature, registration in iter_enabled_registrations(scene, object_slot):
                mask_group = get_effective_vertex_group_name(facial, feature, registration)
                try:
                    result = bake_masked_shape_key(
                        mesh_obj,
                        auth_key_name,
                        feature.name,
                        mask_group,
                        override_existing=override_existing,
                    )
                except Exception as exc:
                    errors.append(
                        f"{auth_key_name} / {object_slot} / {feature.name}: {exc}"
                    )
                    continue

                if result == "created":
                    created += 1
                elif result == "updated":
                    updated += 1
                else:
                    skipped += 1

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "auth_key_count": len(auth_keys),
    }
