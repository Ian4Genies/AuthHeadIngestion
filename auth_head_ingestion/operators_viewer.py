import bpy


class AUTHHEAD_OT_auth_viewer_refresh(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.auth_viewer_refresh"
    bl_label = "Refresh List"
    bl_description = "Rescan registered objects for auth_* shape keys"
    bl_options = {"REGISTER"}

    def execute(self, context):
        from .scene.auth_viewer import refresh_variant_list

        count = refresh_variant_list(context.scene)
        viewer = context.scene.auth_head_viewer
        viewer.status = f"{count} variant(s) found"
        self.report({"INFO"}, viewer.status)
        return {"FINISHED"}


class AUTHHEAD_OT_auth_reset_all_previews(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.auth_reset_all_previews"
    bl_label = "Reset All Previews"
    bl_description = "Set all auth_* shape key weights to 0 on registered objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from .scene.auth_viewer import refresh_variant_list, zero_all_auth_shape_keys

        count = zero_all_auth_shape_keys(context.scene)
        refresh_variant_list(context.scene)
        viewer = context.scene.auth_head_viewer
        viewer.status = f"Reset {count} active weight(s)"
        self.report({"INFO"}, viewer.status)
        return {"FINISHED"}


class AUTHHEAD_OT_auth_variant_preview(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.auth_variant_preview"
    bl_label = "Preview Variant"
    bl_description = "Solo-preview this auth variant across all registered objects"
    bl_options = {"REGISTER", "UNDO"}

    shape_key_name: bpy.props.StringProperty()

    def execute(self, context):
        from .scene.auth_viewer import clear_variant_preview, refresh_variant_list, set_solo_preview

        viewer = context.scene.auth_head_viewer
        if viewer.active_preview == self.shape_key_name:
            clear_variant_preview(context.scene, self.shape_key_name)
            viewer.status = f"Preview off — {self.shape_key_name}"
        else:
            set_solo_preview(context.scene, self.shape_key_name)
            viewer.status = f"Preview — {self.shape_key_name}"
        refresh_variant_list(context.scene)
        return {"FINISHED"}


class AUTHHEAD_OT_auth_delete_variant(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.auth_delete_variant"
    bl_label = "Delete Selected Variant"
    bl_description = "Remove the selected auth variant from all registered objects"
    bl_options = {"REGISTER", "UNDO"}

    include_splits: bpy.props.BoolProperty(
        name="Include Split Keys",
        description="Also delete facial feature split keys derived from this variant",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return bool(context.scene.auth_head_viewer.variants)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        from .scene.auth_viewer import delete_selected_variant

        try:
            result = delete_selected_variant(
                context.scene,
                include_splits=self.include_splits,
            )
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        viewer = context.scene.auth_head_viewer
        viewer.status = (
            f"Deleted {result['shape_key_name']} "
            f"({len(result['deleted_keys'])} key name(s), {result['removed']} block(s))"
        )
        self.report({"INFO"}, viewer.status)
        return {"FINISHED"}


class AUTHHEAD_OT_auth_delete_all_variants(bpy.types.Operator):
    bl_idname = "auth_head_ingestion.auth_delete_all_variants"
    bl_label = "Delete All Auth Variants"
    bl_description = "Remove every auth_* shape key from all registered objects"
    bl_options = {"REGISTER", "UNDO"}

    include_splits: bpy.props.BoolProperty(
        name="Include Split Keys",
        description="Also delete split feature shape keys",
        default=True,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        from .scene.auth_viewer import delete_all_auth_variants

        try:
            result = delete_all_auth_variants(
                context.scene,
                include_splits=self.include_splits,
            )
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        viewer = context.scene.auth_head_viewer
        viewer.status = (
            f"Deleted {len(result['deleted_keys'])} key name(s), "
            f"{result['removed']} block(s) removed"
        )
        self.report({"INFO"}, viewer.status)
        return {"FINISHED"}


CLASSES = (
    AUTHHEAD_OT_auth_viewer_refresh,
    AUTHHEAD_OT_auth_reset_all_previews,
    AUTHHEAD_OT_auth_variant_preview,
    AUTHHEAD_OT_auth_delete_variant,
    AUTHHEAD_OT_auth_delete_all_variants,
)
