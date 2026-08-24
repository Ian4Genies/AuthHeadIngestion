import bpy

from .properties import ALL_SLOT_IDS, SLOT_SECTIONS
from .preferences import restore_fbx_directory_if_empty
from .scene.batch_load import included_fbx_count
from .scene.debug_log import log_dir
from .scene.facial_bake import list_auth_shape_keys_on_head
from .scene.facial_registry import (
    SLOT_LABELS,
    count_enabled_registrations,
    ensure_registrations,
    find_registration,
    get_effective_vertex_group_name,
    iter_registered_object_slots,
)
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

            if section_title == "Boolean Cutters":
                sync_row = box.row(align=True)
                sync_row.enabled = bool(props.head) and bool(
                    props.l_boolean_cutter or props.r_boolean_cutter
                )
                sync_row.operator(
                    "auth_head_ingestion.sync_eye_frame",
                    text="Sync Eye Frame",
                    icon="FILE_REFRESH",
                )


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
        restore_fbx_directory_if_empty(context.scene)

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
        row_primary = sources.row(align=True)
        row_primary.prop(batch, "apply_head", toggle=True, icon="USER")
        row_primary.prop(batch, "apply_l_wedge", toggle=True, icon="TRIA_LEFT")
        row_primary.prop(batch, "apply_r_wedge", toggle=True, icon="TRIA_RIGHT")
        row_secondary = sources.row(align=True)
        row_secondary.prop(batch, "apply_eyes", toggle=True, icon="VIEWZOOM")
        row_secondary.prop(batch, "apply_hd_eyes", toggle=True, icon="VIEWZOOM")
        row_secondary.prop(batch, "apply_boolean_cutters", toggle=True, icon="MOD_BOOLEAN")

        sync_row = sources.row(align=True)
        sync_row.enabled = batch.apply_boolean_cutters
        sync_row.prop(batch, "sync_eye_frame", toggle=True, icon="FILE_REFRESH")

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
        if batch.apply_boolean_cutters:
            col.label(text="L/R Boolean  →  registered boolean cutters (L/R)", icon="DOT")
            if batch.sync_eye_frame:
                col.label(text="L/R Boolean  →  head eye socket ring (synced)", icon="DOT")

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
            run_main = run_row.row(align=True)
            run_main.enabled = included_fbx_count(context.scene) > 0 and bool(
                batch.apply_head
                or batch.apply_l_wedge
                or batch.apply_r_wedge
                or batch.apply_eyes
                or batch.apply_hd_eyes
                or batch.apply_boolean_cutters
            )
            run_main.operator(
                "auth_head_ingestion.run_batch_load",
                text=f"Run Batch ({included_fbx_count(context.scene)} files)",
                icon="PLAY",
            )
            run_reset = run_row.row(align=True)
            run_reset.enabled = bool(
                context.scene.auth_head_viewer.active_preview or batch.preview_shape_key
            )
            run_reset.operator(
                "auth_head_ingestion.auth_reset_all_previews",
                text="",
                icon="LOOP_BACK",
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


class AUTHHEAD_PT_facial_features(bpy.types.Panel):
    bl_label = "Facial Feature Shapes"
    bl_idname = "AUTHHEAD_PT_facial_features"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auth Head"
    bl_parent_id = "AUTHHEAD_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        facial = context.scene.auth_head_facial
        enabled = count_enabled_registrations(context.scene)
        self.layout.label(text=f"{len(facial.features)} / {enabled}", icon="MOD_MASK")

    def draw(self, context):
        pass


class AUTHHEAD_PT_facial_feature_list(bpy.types.Panel):
    bl_label = "Facial Feature List"
    bl_idname = "AUTHHEAD_PT_facial_feature_list"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auth Head"
    bl_parent_id = "AUTHHEAD_PT_facial_features"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        facial = context.scene.auth_head_facial

        list_box = layout.box()
        header = list_box.row()
        header.label(text="Feature")
        header.label(text="Mask Vert Group")

        list_box.template_list(
            "AUTHHEAD_UL_facial_features",
            "",
            facial,
            "features",
            facial,
            "feature_list_index",
            rows=4,
        )

        row = list_box.row(align=True)
        row.operator("auth_head_ingestion.facial_feature_add", icon="ADD", text="Add")
        row.operator("auth_head_ingestion.facial_feature_remove", icon="REMOVE", text="Remove")

        if not facial.features:
            layout.label(text="Add features to define mask vertex group names", icon="INFO")


class AUTHHEAD_PT_facial_registration(bpy.types.Panel):
    bl_label = "Shape Key Registration"
    bl_idname = "AUTHHEAD_PT_facial_registration"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auth Head"
    bl_parent_id = "AUTHHEAD_PT_facial_features"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        facial = context.scene.auth_head_facial
        ensure_registrations(facial)

        if not facial.features:
            layout.label(text="Add features in the list above", icon="INFO")
            return

        tools = layout.row(align=True)
        tools.operator(
            "auth_head_ingestion.facial_sync_registrations",
            text="Sync Registration",
            icon="FILE_REFRESH",
        )

        registered_slots = list(iter_registered_object_slots(context.scene))
        if not registered_slots:
            layout.label(text="Register mesh objects in Scene Object Registry", icon="INFO")
            return

        for object_slot, mesh_obj in registered_slots:
            box = layout.box()
            header = box.row(align=True)
            header.label(text=SLOT_LABELS.get(object_slot, object_slot), icon="MESH_DATA")

            enable_all = header.operator(
                "auth_head_ingestion.facial_enable_slot_features",
                text="All",
            )
            enable_all.object_slot = object_slot
            enable_all.enable = True

            disable_all = header.operator(
                "auth_head_ingestion.facial_enable_slot_features",
                text="None",
            )
            disable_all.object_slot = object_slot
            disable_all.enable = False

            col_header = box.row()
            col_header.scale_y = 0.85
            col_header.label(text="On")
            col_header.label(text="Feature")
            col_header.label(text="Mask")
            col_header.label(text="Override")

            for feature in facial.features:
                if not feature.name:
                    continue

                registration = find_registration(facial, object_slot, feature.name)
                if registration is None:
                    continue

                row = box.row(align=True)
                row.prop(registration, "enabled", text="")

                name_col = row.row()
                name_col.enabled = registration.enabled
                name_col.label(text=feature.name)

                mask_name = get_effective_vertex_group_name(facial, feature, registration)
                mask_col = row.row()
                mask_col.enabled = registration.enabled
                if mesh_obj.vertex_groups.get(mask_name):
                    mask_col.label(text=mask_name, icon="CHECKMARK")
                else:
                    mask_col.alert = True
                    mask_col.label(text=mask_name or "(missing)", icon="ERROR")

                override = row.row()
                override.enabled = registration.enabled
                override.prop_search(
                    registration,
                    "vertex_group_override",
                    mesh_obj,
                    "vertex_groups",
                    text="",
                )


class AUTHHEAD_PT_facial_bake(bpy.types.Panel):
    bl_label = "Bake"
    bl_idname = "AUTHHEAD_PT_facial_bake"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auth Head"
    bl_parent_id = "AUTHHEAD_PT_facial_features"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        facial = context.scene.auth_head_facial
        ensure_registrations(facial)

        auth_keys = list_auth_shape_keys_on_head(context.scene)
        enabled_regs = count_enabled_registrations(context.scene)
        bake_total = len(auth_keys) * enabled_regs

        stats = layout.box()
        col = stats.column(align=True)
        col.label(text=f"{len(auth_keys)} auth shape key(s) on head", icon="SHAPEKEY_DATA")
        col.label(text=f"{enabled_regs} enabled feature slot(s)", icon="MOD_MASK")
        if bake_total:
            col.label(text=f"Up to {bake_total} split key(s) per bake", icon="PRESET")
        elif not auth_keys:
            col.label(text="Load auth heads before baking", icon="INFO")
        elif enabled_regs == 0:
            col.label(text="Enable features in registration", icon="INFO")

        options = layout.box()
        options.prop(
            facial,
            "bake_override_existing",
            text="Override Existing Split Keys",
            icon="FILE_REFRESH",
        )

        run = layout.box()
        run_row = run.row(align=True)
        run_row.scale_y = 1.35
        run_row.enabled = bool(auth_keys) and enabled_regs > 0 and bool(facial.features)
        run_row.operator(
            "auth_head_ingestion.facial_bake_features",
            text="Bake Split Shape Keys",
            icon="RENDER_STILL",
        )

        if facial.bake_status:
            run.label(text=facial.bake_status, icon="INFO", translate=False)


class AUTHHEAD_PT_auth_viewer(bpy.types.Panel):
    bl_label = "Auth Blendshape Viewer"
    bl_idname = "AUTHHEAD_PT_auth_viewer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auth Head"
    bl_parent_id = "AUTHHEAD_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        viewer = context.scene.auth_head_viewer
        self.layout.label(text=str(len(viewer.variants)), icon="SHAPEKEY_DATA")

    def draw(self, context):
        from .scene.auth_viewer import refresh_variant_list

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        viewer = context.scene.auth_head_viewer
        batch = context.scene.auth_head_batch
        if not viewer.variants:
            refresh_variant_list(context.scene)

        tools = layout.box()
        row = tools.row(align=True)
        row.scale_y = 1.2
        row.operator(
            "auth_head_ingestion.auth_reset_all_previews",
            text="Reset All Previews",
            icon="LOOP_BACK",
        )
        row.operator(
            "auth_head_ingestion.auth_viewer_refresh",
            text="Refresh",
            icon="FILE_REFRESH",
        )

        preview = viewer.active_preview or batch.preview_shape_key or "—"
        tools.label(
            text=f"Preview: {preview}  ·  {len(viewer.variants)} variant(s)",
            icon="HIDE_OFF" if preview != "—" else "SHAPEKEY_DATA",
            translate=False,
        )

        list_box = layout.box()
        header = list_box.row(align=True)
        header.label(text="Auth Variants", icon="SHAPEKEY_DATA")
        header.prop(viewer, "show_split_keys", text="Splits")

        list_box.template_list(
            "AUTHHEAD_UL_auth_variants",
            "",
            viewer,
            "variants",
            viewer,
            "variant_list_index",
            rows=8,
        )

        if not viewer.variants:
            list_box.label(text="No auth_* shape keys on registered objects", icon="INFO")
            return

        actions = layout.box()
        row = actions.row(align=True)
        delete = row.operator(
            "auth_head_ingestion.auth_delete_variant",
            text="Delete Selected",
            icon="TRASH",
        )
        delete.include_splits = viewer.delete_include_splits

        actions.prop(
            viewer,
            "delete_include_splits",
            text="Include split keys when deleting",
            icon="MOD_MASK",
        )

        danger = layout.box()
        danger.alert = True
        delete_all = danger.row(align=True)
        delete_all.scale_y = 1.15
        op = delete_all.operator(
            "auth_head_ingestion.auth_delete_all_variants",
            text="Delete All Auth Variants",
            icon="CANCEL",
        )
        op.include_splits = viewer.delete_include_splits


class AUTHHEAD_PT_auth_viewer_weights(bpy.types.Panel):
    bl_label = "Per-Object Weights"
    bl_idname = "AUTHHEAD_PT_auth_viewer_weights"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auth Head"
    bl_parent_id = "AUTHHEAD_PT_auth_viewer"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        viewer = context.scene.auth_head_viewer
        return bool(viewer.variants) and 0 <= viewer.variant_list_index < len(viewer.variants)

    def draw(self, context):
        from .scene.auth_viewer import SLOT_LABELS, iter_registered_object_slots

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        viewer = context.scene.auth_head_viewer
        item = viewer.variants[viewer.variant_list_index]
        layout.label(text=item.name, icon="SHAPEKEY_DATA", translate=False)

        found_any = False
        for slot_id, obj in iter_registered_object_slots(context.scene):
            shape_keys = obj.data.shape_keys
            if shape_keys is None or item.name not in shape_keys.key_blocks:
                continue

            found_any = True
            key_block = shape_keys.key_blocks[item.name]
            layout.prop(
                key_block,
                "value",
                text=SLOT_LABELS.get(slot_id, slot_id),
                slider=True,
            )

        if not found_any:
            layout.label(text="Selected variant is not present on registered objects", icon="ERROR")


CLASSES = (
    AUTHHEAD_PT_main,
    AUTHHEAD_PT_scene_registry,
    AUTHHEAD_PT_load_heads_blendshape,
    AUTHHEAD_PT_facial_features,
    AUTHHEAD_PT_facial_feature_list,
    AUTHHEAD_PT_facial_registration,
    AUTHHEAD_PT_facial_bake,
    AUTHHEAD_PT_auth_viewer,
    AUTHHEAD_PT_auth_viewer_weights,
)
