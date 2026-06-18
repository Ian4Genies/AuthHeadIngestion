import bpy

from .properties import ALL_SLOT_IDS, SLOT_SECTIONS
from .scene.batch_load import included_fbx_count
from .scene.debug_log import log_dir
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


class AUTHHEAD_PT_main(bpy.types.Panel):
    bl_label = "Auth Head Ingestion"
    bl_idname = "AUTHHEAD_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auth Head"

    def draw(self, context):
        self.layout.label(text="Pipeline tools", icon="OUTLINER_OB_GROUP_INSTANCE")


class AUTHHEAD_PT_scene_registry(bpy.types.Panel):
    bl_label = "Scene Object Registry"
    bl_idname = "AUTHHEAD_PT_scene_registry"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auth Head"
    bl_parent_id = "AUTHHEAD_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        props = context.scene.auth_head_objects
        filled = registered_count(context.scene)
        total = len(ALL_SLOT_IDS)
        self.layout.label(text=f"{filled}/{total}", icon="OUTLINER_COLLECTION")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        props = context.scene.auth_head_objects
        total = len(ALL_SLOT_IDS)
        filled = registered_count(context.scene)

        header = layout.box()
        col = header.column(align=True)
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


class AUTHHEAD_PT_load_heads_blendshape(bpy.types.Panel):
    bl_label = "Load Heads as Blendshape"
    bl_idname = "AUTHHEAD_PT_load_heads_blendshape"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auth Head"
    bl_parent_id = "AUTHHEAD_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        batch = context.scene.auth_head_batch
        included = included_fbx_count(context.scene)
        total = len(batch.fbx_files)
        self.layout.label(text=f"{included}/{total}", icon="SHAPEKEY_DATA")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        batch = context.scene.auth_head_batch

        actions = layout.box()
        row = actions.row(align=True)
        row.scale_y = 1.2
        row.operator(
            "auth_head_ingestion.compare_to_loaded",
            text="Compare to Loaded",
            icon="ZOOM_PREVIOUS",
        )

        directory = layout.box()
        directory.label(text="Source Directory", icon="FILE_FOLDER")
        directory.prop(batch, "fbx_directory", text="")
        row = directory.row(align=True)
        row.operator(
            "auth_head_ingestion.scan_fbx_directory",
            text="Rescan",
            icon="FILE_REFRESH",
        )

        if not batch.fbx_files:
            layout.label(text="No FBX files found", icon="INFO")
            return

        stats = layout.box()
        col = stats.column(align=True)
        col.label(
            text=f"{len(batch.fbx_files)} file(s) — {included_fbx_count(context.scene)} queued",
            icon="PRESET",
        )
        loaded_count = sum(1 for item in batch.fbx_files if item.already_loaded)
        if loaded_count:
            col.label(text=f"{loaded_count} already on registered head", icon="CHECKMARK")

        toggles = layout.row(align=True)
        toggles.operator("auth_head_ingestion.fbx_include_all", text="Enable All")
        toggles.operator("auth_head_ingestion.fbx_exclude_all", text="Disable All")

        list_box = layout.box()
        list_box.label(text="FBX Files", icon="FILE_3D")
        list_box.template_list(
            "AUTHHEAD_UL_fbx_files",
            "",
            batch,
            "fbx_files",
            batch,
            "fbx_list_index",
            rows=8,
        )

        layout.separator()

        run_box = layout.box()
        run_box.label(text="Batch Apply", icon="PLAY")

        sources = run_box.box()
        sources.label(text="Source Meshes", icon="MODIFIER_DATA")
        row = sources.row(align=True)
        row.prop(batch, "apply_head", toggle=True, icon="USER")
        row.prop(batch, "apply_l_wedge", toggle=True, icon="TRIA_LEFT")
        row.prop(batch, "apply_r_wedge", toggle=True, icon="TRIA_RIGHT")
        row.prop(batch, "apply_eyes", toggle=True, icon="VIEWZOOM")
        row.prop(batch, "apply_hd_eyes", toggle=True, icon="VIEWZOOM")

        targets = run_box.box()
        targets.label(text="Target Mapping", icon="ARROW_LEFTRIGHT")
        col = targets.column(align=True)
        col.scale_y = 0.9
        if batch.apply_head:
            col.label(text="Head  →  registered head", icon="DOT")
        if batch.apply_l_wedge:
            col.label(text="L Wedge  →  eye / bake / render (L)", icon="DOT")
        if batch.apply_r_wedge:
            col.label(text="R Wedge  →  eye / bake / render (R)", icon="DOT")
        if batch.apply_eyes:
            col.label(text="L/R Eye  →  registered eyes (L/R)", icon="DOT")
        if batch.apply_hd_eyes:
            col.label(text="L/R Eye  →  registered HD eyes (L/R)", icon="DOT")

        if batch.is_running:
            progress = run_box.box()
            col = progress.column(align=True)
            col.label(text=batch.status_message, icon="TIME")
            if batch.preview_shape_key:
                col.label(text=f"Preview: {batch.preview_shape_key}", icon="SHAPEKEY_DATA")
            col.prop(batch, "progress", text="Progress", slider=True)
            stats = col.row(align=True)
            stats.label(text=f"{batch.processed_count} ok")
            stats.label(text=f"{batch.failed_count} failed")
            stats.label(text=f"{batch.run_total} total")
            cancel = col.row(align=True)
            cancel.scale_y = 1.3
            cancel.operator(
                "auth_head_ingestion.cancel_batch_load",
                text="Cancel",
                icon="PANEL_CLOSE",
            )
        else:
            if batch.status_message:
                run_box.label(text=batch.status_message, icon="INFO")

            run_row = run_box.row(align=True)
            run_row.scale_y = 1.45
            run_row.enabled = included_fbx_count(context.scene) > 0 and bool(
                batch.apply_head
                or batch.apply_l_wedge
                or batch.apply_r_wedge
                or batch.apply_eyes
                or batch.apply_hd_eyes
            )
            run_row.operator(
                "auth_head_ingestion.run_batch_load",
                text=f"Run Batch ({included_fbx_count(context.scene)} files)",
                icon="PLAY",
            )

        debug_box = layout.box()
        header = debug_box.row(align=True)
        header.prop(batch, "debug_verbose", text="Debug Output", icon="CONSOLE")
        header.operator(
            "auth_head_ingestion.copy_debug_log",
            text="",
            icon="COPYDOWN",
        )
        header.operator(
            "auth_head_ingestion.clear_debug_log",
            text="",
            icon="TRASH",
        )

        debug_box.label(text=f"Log folder: {log_dir()}", icon="FILE_FOLDER", translate=False)

        if batch.debug_log_file:
            debug_box.label(text=f"Log: {batch.debug_log_file}", icon="FILE_TEXT", translate=False)

        if batch.debug_verbose and batch.debug_log:
            log_col = debug_box.column(align=True)
            log_col.scale_y = 0.75
            for line in batch.debug_log.splitlines()[-18:]:
                if "[ERROR]" in line or "[WARN]" in line:
                    row = log_col.row()
                    row.alert = True
                    row.label(text=line, translate=False)
                else:
                    log_col.label(text=line, translate=False)
            if len(batch.debug_log.splitlines()) > 18:
                debug_box.label(
                    text="(panel preview — full log in logs/batch_debug.json)",
                    icon="INFO",
                )


CLASSES = (
    AUTHHEAD_PT_main,
    AUTHHEAD_PT_scene_registry,
    AUTHHEAD_PT_load_heads_blendshape,
)
