import bpy

from .properties import ALL_SLOT_IDS
from .scene.facial_registry import ensure_registrations, remove_feature_registrations


class AUTHHEAD_OT_facial_feature_add(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.facial_feature_add"
    bl_label = "Add Feature"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        facial = context.scene.auth_head_facial
        feature = facial.features.add()
        feature.name = f"feature_{len(facial.features):02d}"
        feature.mask_vertex_group = feature.name
        facial.feature_list_index = len(facial.features) - 1
        ensure_registrations(facial)
        return {"FINISHED"}


class AUTHHEAD_OT_facial_feature_remove(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.facial_feature_remove"
    bl_label = "Remove Feature"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(context.scene.auth_head_facial.features)

    def execute(self, context):
        facial = context.scene.auth_head_facial
        index = facial.feature_list_index
        if index < 0 or index >= len(facial.features):
            return {"CANCELLED"}

        feature_name = facial.features[index].name
        remove_feature_registrations(facial, feature_name)
        facial.features.remove(index)
        facial.feature_list_index = min(index, max(0, len(facial.features) - 1))
        return {"FINISHED"}


class AUTHHEAD_OT_facial_sync_registrations(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.facial_sync_registrations"
    bl_label = "Sync Registration"
    bl_description = "Rebuild registration entries for all features and object slots"
    bl_options = {"REGISTER"}

    def execute(self, context):
        ensure_registrations(context.scene.auth_head_facial)
        self.report({"INFO"}, "Registration synced")
        return {"FINISHED"}


class AUTHHEAD_OT_facial_bake_features(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.facial_bake_features"
    bl_label = "Bake Split Shape Keys"
    bl_description = "Create masked split shape keys from ingested auth_* shapes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        facial = context.scene.auth_head_facial
        return bool(facial.features)

    def execute(self, context):
        from .scene.facial_bake import bake_all_facial_features
        from .scene.facial_registry import count_enabled_registrations

        facial = context.scene.auth_head_facial
        ensure_registrations(facial)

        if count_enabled_registrations(context.scene) == 0:
            self.report({"ERROR"}, "Enable at least one feature on a registered object")
            return {"CANCELLED"}

        try:
            result = bake_all_facial_features(
                context.scene,
                override_existing=facial.bake_override_existing,
            )
        except ValueError as exc:
            facial.bake_status = str(exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        error_count = len(result["errors"])
        facial.bake_status = (
            f"{result['created']} created, {result['updated']} updated, "
            f"{result['skipped']} skipped"
        )
        if error_count:
            facial.bake_status += f", {error_count} errors"

        if error_count:
            self.report({"WARNING"}, facial.bake_status)
            for message in result["errors"][:3]:
                self.report({"WARNING"}, message)
        else:
            self.report({"INFO"}, facial.bake_status)

        return {"FINISHED"}


class AUTHHEAD_OT_facial_enable_slot_features(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.facial_enable_slot_features"
    bl_label = "Enable All Features"
    bl_options = {"REGISTER", "UNDO"}

    object_slot: bpy.props.EnumProperty(
        items=tuple((slot_id, slot_id, "") for slot_id in ALL_SLOT_IDS),
    )
    enable: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        facial = context.scene.auth_head_facial
        ensure_registrations(facial)
        for registration in facial.registrations:
            if registration.object_slot == self.object_slot:
                registration.enabled = self.enable
        return {"FINISHED"}


CLASSES = (
    AUTHHEAD_OT_facial_feature_add,
    AUTHHEAD_OT_facial_feature_remove,
    AUTHHEAD_OT_facial_sync_registrations,
    AUTHHEAD_OT_facial_bake_features,
    AUTHHEAD_OT_facial_enable_slot_features,
)
