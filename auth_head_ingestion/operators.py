import bpy

from .properties import ALL_SLOT_IDS


class AUTHHEAD_OT_assign_scene_object(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.assign_scene_object"
    bl_label = "Assign Active Object"
    bl_description = "Assign the active object to this slot"
    bl_options = {"REGISTER", "UNDO"}

    slot: bpy.props.EnumProperty(
        items=tuple((slot_id, slot_id, "") for slot_id in ALL_SLOT_IDS),
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        props = context.scene.auth_head_objects
        setattr(props, self.slot, obj)
        self.report({"INFO"}, f"Assigned '{obj.name}'")
        return {"FINISHED"}


class AUTHHEAD_OT_clear_scene_object(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.clear_scene_object"
    bl_label = "Clear Slot"
    bl_description = "Remove the object assigned to this slot"
    bl_options = {"REGISTER", "UNDO"}

    slot: bpy.props.EnumProperty(
        items=tuple((slot_id, slot_id, "") for slot_id in ALL_SLOT_IDS),
    )

    def execute(self, context):
        props = context.scene.auth_head_objects
        setattr(props, self.slot, None)
        self.report({"INFO"}, "Slot cleared")
        return {"FINISHED"}


class AUTHHEAD_OT_select_scene_object(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.select_scene_object"
    bl_label = "Select Registered Object"
    bl_description = "Select and activate the object in this slot"
    bl_options = {"REGISTER", "UNDO"}

    slot: bpy.props.EnumProperty(
        items=tuple((slot_id, slot_id, "") for slot_id in ALL_SLOT_IDS),
    )

    def execute(self, context):
        obj = getattr(context.scene.auth_head_objects, self.slot)
        if obj is None:
            self.report({"WARNING"}, "This slot is empty")
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}


class AUTHHEAD_OT_assign_all_from_selection(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.assign_all_from_selection"
    bl_label = "Auto-Match Selection"
    bl_description = (
        "Try to match selected objects to slots by name "
        "(head, eye wedge, bake wedge, render wedge)"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        props = context.scene.auth_head_objects
        name_map = {
            "head": "head",
            "l_eye_wedge": ("l eye wedge", "left eye wedge", "eye wedge l"),
            "r_eye_wedge": ("r eye wedge", "right eye wedge", "eye wedge r"),
            "l_bake_wedge": ("l bake wedge", "left bake wedge", "bake wedge l"),
            "r_bake_wedge": ("r bake wedge", "right bake wedge", "bake wedge r"),
            "l_render_wedge": ("l render wedge", "left render wedge", "render wedge l"),
            "r_render_wedge": ("r render wedge", "right render wedge", "render wedge r"),
        }

        assigned = 0
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            normalized = obj.name.lower().replace("_", " ").replace("-", " ")
            for slot_id, patterns in name_map.items():
                if isinstance(patterns, str):
                    patterns = (patterns,)
                if any(pattern in normalized for pattern in patterns):
                    if getattr(props, slot_id) is None:
                        setattr(props, slot_id, obj)
                        assigned += 1
                    break

        if assigned:
            self.report({"INFO"}, f"Auto-matched {assigned} slot(s)")
        else:
            self.report({"WARNING"}, "No new matches found in selection")
        return {"FINISHED"}


CLASSES = (
    AUTHHEAD_OT_assign_scene_object,
    AUTHHEAD_OT_clear_scene_object,
    AUTHHEAD_OT_select_scene_object,
    AUTHHEAD_OT_assign_all_from_selection,
)
