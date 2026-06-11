import bpy

from .properties import ALL_SLOT_IDS, SLOT_SECTIONS
from .scene.registry import all_slots_filled, registered_count


def _draw_slot_row(layout, context, props, slot_id, label):
    obj = getattr(props, slot_id)
    row = layout.row(align=True)

    status = row.row(align=True)
    status.scale_x = 0.3
    if obj:
        status.label(text="", icon="CHECKMARK")
    else:
        status.alert = True
        status.label(text="", icon="BLANK1")

    row.prop(props, slot_id, text=label)

    assign = row.row(align=True)
    assign.enabled = context.active_object is not None
    op = assign.operator(
        "auth_head_ingestion.assign_scene_object",
        text="",
        icon="EYEDROPPER",
    )
    op.slot = slot_id

    if obj:
        op = row.operator(
            "auth_head_ingestion.select_scene_object",
            text="",
            icon="RESTRICT_SELECT_OFF",
        )
        op.slot = slot_id
        op = row.operator(
            "auth_head_ingestion.clear_scene_object",
            text="",
            icon="X",
        )
        op.slot = slot_id


def _draw_progress_row(layout, props):
    row = layout.row(align=True)
    row.scale_y = 0.85
    for slot_id in ALL_SLOT_IDS:
        cell = row.row(align=True)
        cell.scale_x = 0.55
        if getattr(props, slot_id):
            cell.label(text="", icon="RADIOBUT_ON")
        else:
            cell.alert = True
            cell.label(text="", icon="RADIOBUT_OFF")


class AUTHHEAD_PT_scene_registry(bpy.types.Panel):
    bl_label = "Auth Head Ingestion"
    bl_idname = "AUTHHEAD_PT_scene_registry"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auth Head"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        props = context.scene.auth_head_objects
        total = len(ALL_SLOT_IDS)
        filled = registered_count(context.scene)

        header = layout.box()
        col = header.column(align=True)
        title = col.row(align=True)
        title.label(text="Scene Object Registry", icon="OUTLINER_COLLECTION")
        title.label(text=f"{filled} / {total}")

        _draw_progress_row(col, props)

        if all_slots_filled(context.scene):
            col.label(text="All slots registered — saved with this .blend", icon="FILE_TICK")
        else:
            col.label(text=f"{total - filled} slot(s) remaining", icon="INFO")

        tools = layout.box()
        row = tools.row(align=True)
        row.scale_y = 1.15
        row.operator(
            "auth_head_ingestion.assign_all_from_selection",
            text="Auto-Match Selection",
            icon="AUTO",
        )

        for section_title, section_icon, slots in SLOT_SECTIONS:
            box = layout.box()
            box.label(text=section_title, icon=section_icon)
            col = box.column(align=True)
            for slot_id, label in slots:
                _draw_slot_row(col, context, props, slot_id, label)


CLASSES = (AUTHHEAD_PT_scene_registry,)
