HEAD_SLOT = "head"

LEFT_WEDGE_SLOTS = (
    "l_eye_wedge",
    "l_bake_wedge",
    "l_render_wedge",
)

RIGHT_WEDGE_SLOTS = (
    "r_eye_wedge",
    "r_bake_wedge",
    "r_render_wedge",
)

LEFT_EYE_SLOTS = (
    "l_eyes",
    "l_hd_eyes",
)

RIGHT_EYE_SLOTS = (
    "r_eyes",
    "r_hd_eyes",
)

LEFT_BOOLEAN_SLOTS = (
    "l_boolean_cutter",
)

RIGHT_BOOLEAN_SLOTS = (
    "r_boolean_cutter",
)

ALL_SHAPE_KEY_TARGETS = (
    (HEAD_SLOT,)
    + LEFT_WEDGE_SLOTS
    + RIGHT_WEDGE_SLOTS
    + LEFT_EYE_SLOTS
    + RIGHT_EYE_SLOTS
    + LEFT_BOOLEAN_SLOTS
    + RIGHT_BOOLEAN_SLOTS
)
