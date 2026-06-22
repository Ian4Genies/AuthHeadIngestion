from ..core.targets import HEAD_SLOT
from ..properties import ALL_SLOT_IDS, SLOT_SECTIONS
from .registry import get_registered_object

SLOT_LABELS = {
    slot_id: label
    for _title, _icon, slots in SLOT_SECTIONS
    for slot_id, label in slots
}


def _registration_key(object_slot: str, feature_name: str) -> str:
    return f"{object_slot}::{feature_name}"


def find_registration(facial, object_slot: str, feature_name: str):
    for registration in facial.registrations:
        if registration.object_slot == object_slot and registration.feature_name == feature_name:
            return registration
    return None


def ensure_registrations(facial) -> None:
    existing = {
        _registration_key(reg.object_slot, reg.feature_name)
        for reg in facial.registrations
    }

    for feature in facial.features:
        if not feature.name:
            continue
        for object_slot in ALL_SLOT_IDS:
            key = _registration_key(object_slot, feature.name)
            if key in existing:
                continue
            registration = facial.registrations.add()
            registration.object_slot = object_slot
            registration.feature_name = feature.name
            registration.enabled = object_slot == HEAD_SLOT
            existing.add(key)

    stale = []
    valid_features = {feature.name for feature in facial.features if feature.name}
    for index, registration in enumerate(facial.registrations):
        if registration.feature_name not in valid_features:
            stale.append(index)
        elif registration.object_slot not in ALL_SLOT_IDS:
            stale.append(index)

    for index in reversed(stale):
        facial.registrations.remove(index)


def rename_feature_registrations(facial, old_name: str, new_name: str) -> None:
    for registration in facial.registrations:
        if registration.feature_name == old_name:
            registration.feature_name = new_name


def remove_feature_registrations(facial, feature_name: str) -> None:
    indices = [
        index
        for index, registration in enumerate(facial.registrations)
        if registration.feature_name == feature_name
    ]
    for index in reversed(indices):
        facial.registrations.remove(index)


def get_effective_vertex_group_name(facial, feature, registration) -> str:
    if registration.vertex_group_override:
        return registration.vertex_group_override
    if feature.mask_vertex_group:
        return feature.mask_vertex_group
    return feature.name


def iter_registered_object_slots(scene):
    for object_slot in ALL_SLOT_IDS:
        obj = get_registered_object(scene, object_slot)
        if obj is not None and obj.type == "MESH":
            yield object_slot, obj


def iter_enabled_registrations(scene, object_slot: str):
    facial = scene.auth_head_facial
    for feature in facial.features:
        if not feature.name:
            continue
        registration = find_registration(facial, object_slot, feature.name)
        if registration is None or not registration.enabled:
            continue
        yield feature, registration


def count_enabled_registrations(scene) -> int:
    total = 0
    for object_slot, _obj in iter_registered_object_slots(scene):
        for _feature, _registration in iter_enabled_registrations(scene, object_slot):
            total += 1
    return total
