from ..core.targets import (
    HEAD_SLOT,
    LEFT_BOOLEAN_SLOTS,
    LEFT_WEDGE_SLOTS,
    RIGHT_BOOLEAN_SLOTS,
    RIGHT_WEDGE_SLOTS,
)
from .debug_log import log, log_exception, log_object
from .fbx_import import classify_imported_meshes, cleanup_import, import_fbx
from .registry import get_registered_object
from .shape_keys import (
    add_shape_from_mesh,
    log_shared_mesh_targets,
    set_active_preview_shape_key,
    zero_auth_shape_keys,
)


def _any_apply_enabled(batch) -> bool:
    return any(
        (
            batch.apply_head,
            batch.apply_l_wedge,
            batch.apply_r_wedge,
            batch.apply_eyes,
            batch.apply_hd_eyes,
            batch.apply_boolean_cutters,
        )
    )


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

    if batch.apply_eyes:
        for slot_id in ("l_eyes", "r_eyes"):
            if get_registered_object(scene, slot_id) is None:
                errors.append(f"Register {slot_id.replace('_', ' ')}")

    if batch.apply_hd_eyes:
        for slot_id in ("l_hd_eyes", "r_hd_eyes"):
            if get_registered_object(scene, slot_id) is None:
                errors.append(f"Register {slot_id.replace('_', ' ')}")

    if batch.apply_boolean_cutters:
        for slot_id in LEFT_BOOLEAN_SLOTS + RIGHT_BOOLEAN_SLOTS:
            if get_registered_object(scene, slot_id) is None:
                errors.append(f"Register {slot_id.replace('_', ' ')}")

    if not _any_apply_enabled(batch):
        errors.append("Enable at least one batch source target")

    return errors


def log_batch_settings(scene) -> None:
    batch = scene.auth_head_batch
    log(scene, "─── Batch settings ───", force=True)
    log(
        scene,
        f"apply_head={batch.apply_head} apply_l_wedge={batch.apply_l_wedge} "
        f"apply_r_wedge={batch.apply_r_wedge} apply_eyes={batch.apply_eyes} "
        f"apply_hd_eyes={batch.apply_hd_eyes} "
        f"apply_boolean_cutters={batch.apply_boolean_cutters}",
        force=True,
    )

    if batch.apply_head:
        log_object(scene, "Registered head target", get_registered_object(scene, HEAD_SLOT))
    if batch.apply_l_wedge:
        for slot_id in LEFT_WEDGE_SLOTS:
            log_object(scene, f"Registered {slot_id}", get_registered_object(scene, slot_id))
    if batch.apply_r_wedge:
        for slot_id in RIGHT_WEDGE_SLOTS:
            log_object(scene, f"Registered {slot_id}", get_registered_object(scene, slot_id))
    if batch.apply_eyes:
        for slot_id in ("l_eyes", "r_eyes"):
            log_object(scene, f"Registered {slot_id}", get_registered_object(scene, slot_id))
    if batch.apply_hd_eyes:
        for slot_id in ("l_hd_eyes", "r_hd_eyes"):
            log_object(scene, f"Registered {slot_id}", get_registered_object(scene, slot_id))
    if batch.apply_boolean_cutters:
        for slot_id in LEFT_BOOLEAN_SLOTS + RIGHT_BOOLEAN_SLOTS:
            log_object(scene, f"Registered {slot_id}", get_registered_object(scene, slot_id))

    log_shared_mesh_targets(scene)


def _apply_side_source(
    scene,
    sources: dict,
    *,
    side: str,
    source_key: str,
    shape_key_name: str,
    target_slot: str,
    label: str,
    applied_mesh_keys: set,
    missing_message: str,
) -> None:
    source = sources[source_key]
    if source is None:
        raise ValueError(missing_message)
    target = get_registered_object(scene, target_slot)
    add_shape_from_mesh(
        target,
        source,
        shape_key_name,
        scene=scene,
        applied_mesh_keys=applied_mesh_keys,
    )


def _apply_eye_side(
    scene,
    sources: dict,
    *,
    side: str,
    shape_key_name: str,
    target_slot: str,
    label: str,
    applied_mesh_keys: set,
) -> None:
    _apply_side_source(
        scene,
        sources,
        side=side,
        source_key=f"{side}_eye",
        shape_key_name=shape_key_name,
        target_slot=target_slot,
        label=label,
        applied_mesh_keys=applied_mesh_keys,
        missing_message=f"{label} eye mesh not found in FBX",
    )


def process_fbx_item(scene, item) -> dict:
    batch = scene.auth_head_batch
    shape_key_name = item.shape_key_name

    log(scene, f"─── Processing {item.filename} → '{shape_key_name}' ───", force=True)

    imported_objects, snapshot = import_fbx(item.filepath, scene=scene)

    try:
        sources = classify_imported_meshes(imported_objects, scene=scene, filename=item.filename)
        applied = []
        slot_results = []
        applied_mesh_keys: set = set()

        for slot, source in sources.items():
            if source is not None:
                log_object(scene, f"Source {slot}", source)

        if batch.apply_head:
            source = sources["head"]
            target = get_registered_object(scene, HEAD_SLOT)
            if source is None:
                raise ValueError(f"Head mesh not found in {item.filename}")
            add_shape_from_mesh(
                target,
                source,
                shape_key_name,
                scene=scene,
                applied_mesh_keys=applied_mesh_keys,
            )
            applied.append("head")

        if batch.apply_l_wedge:
            source = sources["l_wedge"]
            if source is None:
                raise ValueError(f"Left eye wedge mesh not found in {item.filename}")
            for slot_id in LEFT_WEDGE_SLOTS:
                target = get_registered_object(scene, slot_id)
                try:
                    add_shape_from_mesh(
                        target,
                        source,
                        shape_key_name,
                        scene=scene,
                        applied_mesh_keys=applied_mesh_keys,
                    )
                    slot_results.append(f"{slot_id}:ok")
                except Exception as exc:
                    slot_results.append(f"{slot_id}:FAIL({exc})")
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
                    add_shape_from_mesh(
                        target,
                        source,
                        shape_key_name,
                        scene=scene,
                        applied_mesh_keys=applied_mesh_keys,
                    )
                    slot_results.append(f"{slot_id}:ok")
                except Exception as exc:
                    slot_results.append(f"{slot_id}:FAIL({exc})")
                    log_exception(scene, f"R wedge apply failed on {slot_id}", exc)
                    raise
            applied.append("R wedge")

        if batch.apply_eyes:
            for side, slot_id in (("l", "l_eyes"), ("r", "r_eyes")):
                try:
                    _apply_eye_side(
                        scene,
                        sources,
                        side=side,
                        shape_key_name=shape_key_name,
                        target_slot=slot_id,
                        label=side.upper(),
                        applied_mesh_keys=applied_mesh_keys,
                    )
                    slot_results.append(f"{slot_id}:ok")
                except Exception as exc:
                    slot_results.append(f"{slot_id}:FAIL({exc})")
                    log_exception(scene, f"Eye apply failed on {slot_id}", exc)
                    raise
            applied.append("eyes")

        if batch.apply_hd_eyes:
            for side, slot_id in (("l", "l_hd_eyes"), ("r", "r_hd_eyes")):
                try:
                    _apply_eye_side(
                        scene,
                        sources,
                        side=side,
                        shape_key_name=shape_key_name,
                        target_slot=slot_id,
                        label=f"{side.upper()} HD",
                        applied_mesh_keys=applied_mesh_keys,
                    )
                    slot_results.append(f"{slot_id}:ok")
                except Exception as exc:
                    slot_results.append(f"{slot_id}:FAIL({exc})")
                    log_exception(scene, f"HD eye apply failed on {slot_id}", exc)
                    raise
            applied.append("HD eyes")

        if batch.apply_boolean_cutters:
            for side, slot_id in (("l", "l_boolean_cutter"), ("r", "r_boolean_cutter")):
                try:
                    _apply_side_source(
                        scene,
                        sources,
                        side=side,
                        source_key=f"{side}_boolean",
                        shape_key_name=shape_key_name,
                        target_slot=slot_id,
                        label=f"{side.upper()} boolean",
                        applied_mesh_keys=applied_mesh_keys,
                        missing_message=f"{side.upper()} boolean cutter mesh not found in FBX",
                    )
                    slot_results.append(f"{slot_id}:ok")
                except Exception as exc:
                    slot_results.append(f"{slot_id}:FAIL({exc})")
                    log_exception(scene, f"Boolean cutter apply failed on {slot_id}", exc)
                    raise
            applied.append("boolean cutters")

            if batch.sync_eye_frame:
                from .eye_frame import sync_eye_frame

                try:
                    eye_frame_result = sync_eye_frame(scene, shape_key_name)
                except Exception as exc:
                    slot_results.append(f"eye_frame:FAIL({exc})")
                    log_exception(scene, "Eye frame sync failed", exc)
                    raise

                if eye_frame_result.get("skipped"):
                    slot_results.append(f"eye_frame:skipped({eye_frame_result['skipped']})")
                else:
                    for side, count in eye_frame_result.items():
                        slot_results.append(f"eye_frame_{side}:{count}v")
                    if eye_frame_result:
                        applied.append("eye frame")

        if slot_results:
            log(scene, f"Slot results: {', '.join(slot_results)}")

        set_active_preview_shape_key(scene, shape_key_name)

        item.already_loaded = True
        item.include_in_batch = False

        log(scene, f"Success — applied: {', '.join(applied)}")

        return {
            "success": True,
            "shape_key_name": shape_key_name,
            "applied": applied,
            "slot_results": slot_results,
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
