import bpy
from bpy.props import PointerProperty
from bpy.types import PropertyGroup


def mesh_object_poll(_self, obj):
    return obj is None or obj.type == "MESH"


class AUTHHEAD_PG_SceneObjects(PropertyGroup):
    head: PointerProperty(
        name="Head",
        description="Primary head mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    l_eye_wedge: PointerProperty(
        name="L Eye Wedge",
        description="Left eye wedge mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    r_eye_wedge: PointerProperty(
        name="R Eye Wedge",
        description="Right eye wedge mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    l_bake_wedge: PointerProperty(
        name="L Bake Wedge",
        description="Left bake wedge mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    r_bake_wedge: PointerProperty(
        name="R Bake Wedge",
        description="Right bake wedge mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    l_render_wedge: PointerProperty(
        name="L Render Wedge",
        description="Left render wedge mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    r_render_wedge: PointerProperty(
        name="R Render Wedge",
        description="Right render wedge mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )


SLOT_SECTIONS = (
    (
        "Primary",
        "OUTLINER_OB_MESH",
        (
            ("head", "Head"),
        ),
    ),
    (
        "Eyes",
        "HIDE_OFF",
        (
            ("l_eye_wedge", "L Eye Wedge"),
            ("r_eye_wedge", "R Eye Wedge"),
        ),
    ),
    (
        "Bake Wedges",
        "RENDERLAYERS",
        (
            ("l_bake_wedge", "L Bake Wedge"),
            ("r_bake_wedge", "R Bake Wedge"),
        ),
    ),
    (
        "Render Wedges",
        "RESTRICT_RENDER_OFF",
        (
            ("l_render_wedge", "L Render Wedge"),
            ("r_render_wedge", "R Render Wedge"),
        ),
    ),
)

ALL_SLOT_IDS = tuple(
    slot_id
    for _title, _icon, slots in SLOT_SECTIONS
    for slot_id, _label in slots
)

CLASSES = (AUTHHEAD_PG_SceneObjects,)
