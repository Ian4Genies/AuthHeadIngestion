from ..properties import ALL_SLOT_IDS


def get_scene_objects(scene):
    return scene.auth_head_objects


def get_registered_object(scene, slot_id):
    if slot_id not in ALL_SLOT_IDS:
        raise KeyError(f"Unknown slot: {slot_id}")
    return getattr(get_scene_objects(scene), slot_id)


def registered_count(scene):
    props = get_scene_objects(scene)
    return sum(1 for slot_id in ALL_SLOT_IDS if getattr(props, slot_id))


def all_slots_filled(scene):
    return registered_count(scene) == len(ALL_SLOT_IDS)
