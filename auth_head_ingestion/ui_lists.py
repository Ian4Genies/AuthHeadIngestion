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


CLASSES = (AUTHHEAD_UL_fbx_files,)
