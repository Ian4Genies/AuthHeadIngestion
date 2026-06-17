from ..core.targets import HEAD_SLOT, LEFT_WEDGE_SLOTS, RIGHT_WEDGE_SLOTS
from .debug_log import clear_log, log, log_exception, log_object
from .fbx_import import classify_imported_meshes, cleanup_import, import_fbx
from .registry import get_registered_object
from .shape_keys import add_shape_from_mesh, set_active_preview_shape_key, zero_auth_shape_keys


def validate_batch_ready(scene) -> list[str]:
    batch = scene.auth_head_batch
    errors = []

    if not batch.fbx_directory:
        errors.append("Set an FBX source directory")

    queued = [item for item in batch.fbx_files if item.include_in_batch and item.shape_key_name]
    if not queued:
        errors.append("No FBX files queued for batch")

    if batch.apply_head and get_registered_object(scene, HEAD_SLOT) is None:
        errors.append("Register the head mesh")

    if batch.apply_l_wedge:
        for slot_id in LEFT_WEDGE_SLOTS:
            if get_registered_object(scene, slot_id) is None:
                errors.append(f"Register {slot_id.replace('_', ' ')}")

    if batch.apply_r_wedge:
        for slot_id in RIGHT_WEDGE_SLOTS:
            if get_registered_object(scene, slot_id) is None:
                errors.append(f"Register {slot_id.replace('_', ' ')}")

    if not batch.apply_head and not batch.apply_l_wedge and not batch.apply_r_wedge:
        errors.append("Enable at least one source target (Head, L Wedge, or R Wedge)")

    return errors


def log_batch_settings(scene) -> None:
    batch = scene.auth_head_batch
    log(scene, "─── Batch settings ───", force=True)
    log(scene, f"apply_head={batch.apply_head} apply_l_wedge={batch.apply_l_wedge} apply_r_wedge={batch.apply_r_wedge}", force=True)

    if batch.apply_head:
        log_object(scene, "Registered head target", get_registered_object(scene, HEAD_SLOT))
    if batch.apply_l_wedge:
        for slot_id in LEFT_WEDGE_SLOTS:
            log_object(scene, f"Registered {slot_id}", get_registered_object(scene, slot_id))
    if batch.apply_r_wedge:
        for slot_id in RIGHT_WEDGE_SLOTS:
            log_object(scene, f"Registered {slot_id}", get_registered_object(scene, slot_id))


def process_fbx_item(scene, item) -> dict:
    batch = scene.auth_head_batch
    shape_key_name = item.shape_key_name

    log(scene, f"─── Processing {item.filename} → '{shape_key_name}' ───", force=True)

    imported_objects, snapshot = import_fbx(item.filepath, scene=scene)

    try:
        sources = classify_imported_meshes(imported_objects, scene=scene, filename=item.filename)
        applied = []
        wedge_results = []

        for slot, source in sources.items():
            if source is not None:
                log_object(scene, f"Source {slot}", source)

        if batch.apply_head:
            source = sources["head"]
            target = get_registered_object(scene, HEAD_SLOT)
            if source is None:
                raise ValueError(f"Head mesh not found in {item.filename}")
            add_shape_from_mesh(target, source, shape_key_name, scene=scene)
            applied.append("head")

        if batch.apply_l_wedge:
            source = sources["l_wedge"]
            if source is None:
                raise ValueError(f"Left eye wedge mesh not found in {item.filename}")
            for slot_id in LEFT_WEDGE_SLOTS:
                target = get_registered_object(scene, slot_id)
                try:
                    add_shape_from_mesh(target, source, shape_key_name, scene=scene)
                    wedge_results.append(f"{slot_id}:ok")
                except Exception as exc:
                    wedge_results.append(f"{slot_id}:FAIL({exc})")
                    log_exception(scene, f"L wedge apply failed on {slot_id}", exc)
                    raise
            applied.append("L wedge")

        if batch.apply_r_wedge:
            source = sources["r_wedge"]
            if source is None:
                raise ValueError(f"Right eye wedge mesh not found in {item.filename}")
            for slot_id in RIGHT_WEDGE_SLOTS:
                target = get_registered_object(scene, slot_id)
                try:
                    add_shape_from_mesh(target, source, shape_key_name, scene=scene)
                    wedge_results.append(f"{slot_id}:ok")
                except Exception as exc:
                    wedge_results.append(f"{slot_id}:FAIL({exc})")
                    log_exception(scene, f"R wedge apply failed on {slot_id}", exc)
                    raise
            applied.append("R wedge")

        if wedge_results:
            log(scene, f"Wedge slot results: {', '.join(wedge_results)}")

        set_active_preview_shape_key(scene, shape_key_name)

        item.already_loaded = True
        item.include_in_batch = False

        log(scene, f"Success — applied: {', '.join(applied)}")

        return {
            "success": True,
            "shape_key_name": shape_key_name,
            "applied": applied,
            "wedge_results": wedge_results,
        }
    finally:
        log(scene, "Cleaning up imported FBX data", force=True)
        cleanup_import(snapshot)


def queued_fbx_items(scene):
    return [
        item
        for item in scene.auth_head_batch.fbx_files
        if item.include_in_batch and item.shape_key_name
    ]
