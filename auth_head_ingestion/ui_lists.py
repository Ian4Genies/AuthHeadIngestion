import bpy


class AUTHHEAD_UL_fbx_files(bpy.types.UIList):
    bl_idname = "AUTHHEAD_UL_fbx_files"

    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_propname,
        index,
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            toggle = row.row(align=True)
            toggle.enabled = bool(item.shape_key_name) and not item.already_loaded
            toggle.prop(item, "include_in_batch", text="")

            if item.already_loaded:
                row.label(text=item.filename, icon="CHECKMARK")
            elif item.shape_key_name:
                row.label(text=item.filename, icon="FILE_3D")
            else:
                row.alert = True
                row.label(text=item.filename, icon="ERROR")

            name_row = row.row()
            name_row.alignment = "RIGHT"
            if item.shape_key_name:
                name_row.label(text=item.shape_key_name)
            else:
                name_row.alert = True
                name_row.label(text="Unrecognized")
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon="FILE_3D")


class AUTHHEAD_UL_facial_features(bpy.types.UIList):
    bl_idname = "AUTHHEAD_UL_facial_features"

    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_propname,
        index,
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            row.prop(item, "name", text="", emboss=False)
            row.prop(item, "mask_vertex_group", text="", emboss=False)
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon="GROUP_VERTEX")


class AUTHHEAD_UL_auth_variants(bpy.types.UIList):
    bl_idname = "AUTHHEAD_UL_auth_variants"

    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_propname,
        index,
    ):
        viewer = context.scene.auth_head_viewer
        is_active = viewer.active_preview == item.name

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            preview = row.row(align=True)
            preview.active = is_active
            op = preview.operator(
                "auth_head_ingestion.auth_variant_preview",
                text="",
                icon="HIDE_OFF" if is_active else "HIDE_ON",
                depress=is_active,
            )
            op.shape_key_name = item.name

            row.label(text=item.name, translate=False)

            meta = row.row(align=True)
            meta.alignment = "RIGHT"
            meta.scale_x = 0.85
            meta.label(text=f"{item.mesh_count}", icon="MESH_DATA")
            if item.split_count:
                meta.label(text=f"+{item.split_count}", icon="MOD_MASK")
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon="SHAPEKEY_DATA")


CLASSES = (
    AUTHHEAD_UL_fbx_files,
    AUTHHEAD_UL_facial_features,
    AUTHHEAD_UL_auth_variants,
)
