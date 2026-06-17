import bpy

from .debug_log import log, log_import_inventory, record_import_inventory


def snapshot_datablocks():
    return {
        "objects": set(bpy.data.objects),
        "meshes": set(bpy.data.meshes),
        "materials": set(bpy.data.materials),
        "images": set(bpy.data.images),
        "armatures": set(bpy.data.armatures),
        "actions": set(bpy.data.actions),
        "node_groups": set(bpy.data.node_groups),
    }


def import_fbx(filepath: str, scene=None) -> tuple[list[bpy.types.Object], dict]:
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    if scene is not None:
        log(scene, f"Importing FBX: {filepath}", force=True)

    before = snapshot_datablocks()
    bpy.ops.import_scene.fbx(
        filepath=filepath,
        use_custom_normals=False,
        use_anim=False,
        ignore_leaf_bones=True,
        automatic_bone_orientation=False,
    )
    imported_objects = [
        obj for obj in bpy.data.objects if obj not in before["objects"]
    ]

    if scene is not None:
        log_import_inventory(scene, imported_objects)

    return imported_objects, before


def cleanup_import(before: dict) -> None:
    new_objects = [obj for obj in bpy.data.objects if obj not in before["objects"]]
    for obj in new_objects:
        bpy.data.objects.remove(obj, do_unlink=True)

    for collection_name, datablock_attr in (
        ("meshes", "meshes"),
        ("materials", "materials"),
        ("images", "images"),
        ("armatures", "armatures"),
        ("actions", "actions"),
        ("node_groups", "node_groups"),
    ):
        before_set = before[collection_name]
        datablocks = getattr(bpy.data, datablock_attr)
        for block in datablocks:
            if block not in before_set and block.users == 0:
                datablocks.remove(block)


def _normalize_name(name: str) -> str:
    return name.lower().replace("-", "_")


def _is_l_wedge(name: str) -> bool:
    normalized = _normalize_name(name)
    if "eye" not in normalized:
        return False
    if "wedge" not in normalized and "wedges" not in normalized:
        return False
    return any(
        token in normalized
        for token in (
            "eyewedges_l",
            "eye_wedges_l",
            "eyewedge_l",
            "eye_wedge_l",
            "wedges_l",
            "wedge_l",
            "_l_",
        )
    ) and "_r_" not in normalized and "wedges_r" not in normalized and "wedge_r" not in normalized


def _is_r_wedge(name: str) -> bool:
    normalized = _normalize_name(name)
    if "eye" not in normalized:
        return False
    if "wedge" not in normalized and "wedges" not in normalized:
        return False
    return any(
        token in normalized
        for token in (
            "eyewedges_r",
            "eye_wedges_r",
            "eyewedge_r",
            "eye_wedge_r",
            "wedges_r",
            "wedge_r",
            "_r_",
        )
    ) and "_l_" not in normalized and "wedges_l" not in normalized and "wedge_l" not in normalized


def _is_head(name: str) -> bool:
    normalized = _normalize_name(name)
    if "eyewedge" in normalized or "eye_wedge" in normalized:
        return False
    if "lopoly_head" in normalized:
        return True
    return "_head_" in normalized and normalized.endswith("_geo")


def classify_imported_meshes(objects, scene=None, filename: str = "") -> dict[str, bpy.types.Object | None]:
    result = {"head": None, "l_wedge": None, "r_wedge": None}
    unmatched_meshes = []

    for obj in objects:
        if obj.type != "MESH":
            continue

        name = obj.name
        if _is_l_wedge(name):
            result["l_wedge"] = obj
            if scene is not None:
                log(scene, f"Classified L wedge: '{obj.name}'", force=True)
        elif _is_r_wedge(name):
            result["r_wedge"] = obj
            if scene is not None:
                log(scene, f"Classified R wedge: '{obj.name}'", force=True)
        elif _is_head(name):
            result["head"] = obj
            if scene is not None:
                log(scene, f"Classified head: '{obj.name}'", force=True)
        else:
            unmatched_meshes.append(name)

    if scene is not None:
        for slot, obj in result.items():
            if obj is None:
                log(scene, f"Classification miss — no {slot} mesh matched", level="WARN", force=True)
        if unmatched_meshes:
            log(
                scene,
                f"Unmatched imported meshes ({len(unmatched_meshes)}): "
                f"{unmatched_meshes}",
                level="WARN",
                force=True,
            )
        record_import_inventory(scene, filename, objects, result)

    return result
