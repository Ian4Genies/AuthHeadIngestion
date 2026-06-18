import json
import os
import traceback
from datetime import datetime, timezone

import bpy

_PREFIX = "[AuthHeadIngestion]"

_session: dict | None = None


def _addon_root() -> str:
    path = os.path.dirname(os.path.abspath(__file__))
    while path and os.path.basename(path) != "auth_head_ingestion":
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    if os.path.basename(path) == "auth_head_ingestion":
        return path
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _project_root() -> str:
    addon_root = _addon_root()
    if os.path.basename(addon_root) == "auth_head_ingestion":
        return os.path.dirname(addon_root)
    return addon_root


def log_dir() -> str:
    return os.path.join(_project_root(), "logs")


def log_txt_path() -> str:
    return os.path.join(log_dir(), "batch_debug.txt")


def log_json_path() -> str:
    return os.path.join(log_dir(), "batch_debug.json")


def is_enabled(scene) -> bool:
    return bool(scene.auth_head_batch.debug_verbose)


def _ensure_log_dir() -> str:
    path = log_dir()
    os.makedirs(path, exist_ok=True)
    return path


def ensure_log_directory() -> str:
    path = _ensure_log_dir()
    readme_path = os.path.join(path, "README.txt")
    if not os.path.isfile(readme_path):
        with open(readme_path, "w", encoding="utf-8") as handle:
            handle.write(
                "Auth Head Ingestion batch logs\n"
                "==============================\n\n"
                "Written on each batch run:\n"
                "  batch_debug.json  — structured log with full import inventory\n"
                "  batch_debug.txt   — plain-text mirror\n"
            )
    return path


def _write_session_files(scene) -> None:
    if _session is None:
        return

    _ensure_log_dir()

    with open(log_txt_path(), "w", encoding="utf-8") as handle:
        for entry in _session["entries"]:
            handle.write(
                f"{entry['time']} [{entry['level']}] {entry['message']}\n"
            )

    payload = dict(_session)
    payload["log_txt"] = log_txt_path()
    payload["log_json"] = log_json_path()

    with open(log_json_path(), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    scene.auth_head_batch.debug_log_file = log_json_path()


def begin_file_session(scene, *, queued_count: int) -> None:
    global _session

    _ensure_log_dir()
    _session = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "blend_file": bpy.data.filepath or None,
        "queued_count": queued_count,
        "processed_count": 0,
        "failed_count": 0,
        "status": "running",
        "entries": [],
        "imports": [],
    }
    _write_session_files(scene)
    log(scene, f"Debug log file: {log_json_path()}", force=True)


def end_file_session(
    scene,
    *,
    status: str,
    processed_count: int,
    failed_count: int,
) -> None:
    global _session

    if _session is None:
        return

    _session["finished_at"] = datetime.now(timezone.utc).isoformat()
    _session["status"] = status
    _session["processed_count"] = processed_count
    _session["failed_count"] = failed_count
    _write_session_files(scene)
    log(scene, f"Debug log saved to {log_json_path()}", force=True)
    _session = None


def record_import_inventory(scene, filename: str, objects, classification: dict) -> None:
    if _session is None:
        return

    imported = []
    for obj in sorted(objects, key=lambda item: item.name.lower()):
        entry = {
            "name": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "children": [child.name for child in obj.children],
            "hierarchy": _object_hierarchy(obj),
        }
        if obj.type == "MESH" and obj.data is not None:
            entry["mesh"] = obj.data.name
            entry["verts"] = len(obj.data.vertices)
            entry["faces"] = len(obj.data.polygons)
        imported.append(entry)

    _session["imports"].append(
        {
            "filename": filename,
            "object_count": len(objects),
            "objects": imported,
            "classification": {
                slot: (obj.name if obj else None)
                for slot, obj in classification.items()
            },
        }
    )
    _write_session_files(scene)


def log(scene, message: str, *, level: str = "INFO", force: bool = False) -> None:
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
    }

    if _session is not None:
        _session["entries"].append(entry)
        _write_session_files(scene)

    if not force and not is_enabled(scene):
        return

    line = f"{_PREFIX}[{level}] {message}"
    print(line)

    batch = scene.auth_head_batch
    existing = batch.debug_log
    batch.debug_log = f"{existing}\n{line}" if existing else line
    if len(batch.debug_log) > 12000:
        batch.debug_log = batch.debug_log[-12000:]


def log_exception(scene, context: str, exc: BaseException) -> None:
    log(scene, f"{context}: {exc}", level="ERROR", force=True)
    for tb_line in traceback.format_exc().strip().splitlines():
        log(scene, tb_line, level="TRACE", force=True)


def _object_hierarchy(obj) -> str:
    parts = []
    current = obj
    while current is not None:
        parts.append(f"{current.name} ({current.type})")
        current = current.parent
    return " / ".join(reversed(parts))


def log_object(scene, label: str, obj) -> None:
    if obj is None:
        log(scene, f"{label}: <none>", force=True)
        return

    mesh = obj.data
    shape_key_count = len(mesh.shape_keys.key_blocks) if mesh.shape_keys else 0
    shape_key_names = (
        [kb.name for kb in mesh.shape_keys.key_blocks[:8]]
        if mesh.shape_keys
        else []
    )
    suffix = "…" if mesh.shape_keys and len(mesh.shape_keys.key_blocks) > 8 else ""

    log(
        scene,
        f"{label}: object='{obj.name}' mesh='{mesh.name}' "
        f"verts={len(mesh.vertices)} faces={len(mesh.polygons)} "
        f"shape_keys={shape_key_count} parent="
        f"'{obj.parent.name if obj.parent else '<root>'}' "
        f"hierarchy='{_object_hierarchy(obj)}' "
        f"matrix_world.translation="
        f"({obj.matrix_world.translation.x:.4f}, "
        f"{obj.matrix_world.translation.y:.4f}, "
        f"{obj.matrix_world.translation.z:.4f})",
        force=True,
    )
    if shape_key_names:
        log(scene, f"{label} shape keys (first): {shape_key_names}{suffix}", force=True)


def log_import_inventory(scene, objects) -> None:
    meshes = [obj for obj in objects if obj.type == "MESH"]
    empties = [obj for obj in objects if obj.type == "EMPTY"]
    other = [obj for obj in objects if obj.type not in {"MESH", "EMPTY"}]

    log(
        scene,
        f"Import inventory: {len(objects)} object(s) — "
        f"{len(meshes)} mesh, {len(empties)} empty, {len(other)} other",
        force=True,
    )

    for obj in sorted(objects, key=lambda item: item.name.lower()):
        parent = obj.parent.name if obj.parent else "<root>"
        children = [child.name for child in obj.children]
        details = (
            f"  [{obj.type}] '{obj.name}' parent='{parent}' "
            f"children={json.dumps(children)} hierarchy='{_object_hierarchy(obj)}'"
        )
        if obj.type == "MESH" and obj.data is not None:
            details += (
                f" mesh='{obj.data.name}' verts={len(obj.data.vertices)} "
                f"faces={len(obj.data.polygons)}"
            )
        log(scene, details, force=True)

    roots = [
        obj
        for obj in objects
        if obj.parent is None or obj.parent not in set(objects)
    ]
    log(scene, f"Import roots ({len(roots)}): {[obj.name for obj in roots]}", force=True)


def clear_log(scene) -> None:
    global _session

    scene.auth_head_batch.debug_log = ""
    scene.auth_head_batch.debug_log_file = ""
    _session = None

    for path in (log_txt_path(), log_json_path()):
        if os.path.isfile(path):
            os.remove(path)


def get_log_text_for_clipboard(scene) -> str:
    json_path = log_json_path()
    if os.path.isfile(json_path):
        with open(json_path, encoding="utf-8") as handle:
            return handle.read()

    txt_path = log_txt_path()
    if os.path.isfile(txt_path):
        with open(txt_path, encoding="utf-8") as handle:
            return handle.read()

    return scene.auth_head_batch.debug_log or ""
