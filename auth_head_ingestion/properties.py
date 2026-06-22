import bpy
from bpy.props import BoolProperty, CollectionProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup


def _on_fbx_directory_changed(self, context):
    from .preferences import save_fbx_directory
    from .scene.batch_load import rescan_fbx_directory

    if self.fbx_directory:
        save_fbx_directory(self.fbx_directory)
    rescan_fbx_directory(context.scene)


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
    l_eyes: PointerProperty(
        name="L Eyes",
        description="Left eye mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    r_eyes: PointerProperty(
        name="R Eyes",
        description="Right eye mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    l_hd_eyes: PointerProperty(
        name="L HD Eyes",
        description="Left HD eye mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    r_hd_eyes: PointerProperty(
        name="R HD Eyes",
        description="Right HD eye mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    l_boolean_cutter: PointerProperty(
        name="L Boolean Cutter",
        description="Left boolean cutter mesh",
        type=bpy.types.Object,
        poll=mesh_object_poll,
    )
    r_boolean_cutter: PointerProperty(
        name="R Boolean Cutter",
        description="Right boolean cutter mesh",
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
        "Wedges",
        "HIDE_OFF",
        (
            ("l_eye_wedge", "L Eye Wedge"),
            ("r_eye_wedge", "R Eye Wedge"),
        ),
    ),
    (
        "Eyes",
        "VIEWZOOM",
        (
            ("l_eyes", "L Eyes"),
            ("r_eyes", "R Eyes"),
        ),
    ),
    (
        "HD Eyes",
        "VIEWZOOM",
        (
            ("l_hd_eyes", "L HD Eyes"),
            ("r_hd_eyes", "R HD Eyes"),
        ),
    ),
    (
        "Boolean Cutters",
        "MOD_BOOLEAN",
        (
            ("l_boolean_cutter", "L Boolean Cutter"),
            ("r_boolean_cutter", "R Boolean Cutter"),
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

class AUTHHEAD_PG_FbxFile(PropertyGroup):
    filename: StringProperty(name="Filename")
    filepath: StringProperty(name="File Path", subtype="FILE_PATH")
    shape_key_name: StringProperty(name="Shape Key")
    include_in_batch: BoolProperty(
        name="Include",
        description="Include this FBX when running the batch load",
        default=True,
    )
    already_loaded: BoolProperty(
        name="Already Loaded",
        description="Shape key already exists on the registered head",
        default=False,
    )


class AUTHHEAD_PG_BatchLoad(PropertyGroup):
    fbx_directory: StringProperty(
        name="FBX Directory",
        description="Folder to scan for authored head FBX files",
        subtype="DIR_PATH",
        update=_on_fbx_directory_changed,
    )
    fbx_files: CollectionProperty(type=AUTHHEAD_PG_FbxFile)
    fbx_list_index: IntProperty(name="FBX List Index", default=0)

    apply_head: BoolProperty(
        name="Head",
        description="Apply imported head mesh as a shape key on the registered head",
        default=True,
    )
    apply_l_wedge: BoolProperty(
        name="L Wedge",
        description="Apply imported left eye wedge to all left wedge targets",
        default=True,
    )
    apply_r_wedge: BoolProperty(
        name="R Wedge",
        description="Apply imported right eye wedge to all right wedge targets",
        default=True,
    )
    apply_eyes: BoolProperty(
        name="Eyes",
        description="Apply imported eye meshes to registered L/R eye targets",
        default=True,
    )
    apply_hd_eyes: BoolProperty(
        name="HD Eyes",
        description="Apply imported eye meshes to registered L/R HD eye targets",
        default=True,
    )
    apply_boolean_cutters: BoolProperty(
        name="Boolean",
        description="Apply imported eye_L/R_boolean meshes to registered boolean cutter targets",
        default=True,
    )

    debug_verbose: BoolProperty(
        name="Debug Output",
        description="Print detailed batch diagnostics to the console and log panel",
        default=True,
    )
    debug_log: StringProperty(
        name="Debug Log",
        description="Recent batch debug messages",
        default="",
    )
    debug_log_file: StringProperty(
        name="Debug Log File",
        description="Path to the on-disk batch debug JSON log",
        default="",
        subtype="FILE_PATH",
    )

    preview_shape_key: StringProperty(
        name="Preview Shape Key",
        description="Currently previewed auth shape key from batch processing",
        default="",
    )

    is_running: BoolProperty(name="Batch Running", default=False)
    cancel_requested: BoolProperty(name="Cancel Requested", default=False, options={"HIDDEN"})
    progress: bpy.props.FloatProperty(name="Progress", subtype="FACTOR", min=0.0, max=1.0)
    status_message: StringProperty(name="Status", default="")
    processed_count: IntProperty(name="Processed", default=0)
    failed_count: IntProperty(name="Failed", default=0)
    run_total: IntProperty(name="Run Total", default=0)


class AUTHHEAD_PG_FacialFeature(PropertyGroup):
    name: StringProperty(
        name="Feature",
        description="Facial feature name used in split shape key suffix",
        default="",
    )
    mask_vertex_group: StringProperty(
        name="Mask Vertex Group",
        description="Vertex group on each mesh used as the normalized bake mask",
        default="",
    )


class AUTHHEAD_PG_FeatureRegistration(PropertyGroup):
    object_slot: StringProperty(name="Object Slot")
    feature_name: StringProperty(name="Feature Name")
    enabled: BoolProperty(
        name="Enabled",
        description="Bake this feature for the registered object",
        default=False,
    )
    vertex_group_override: StringProperty(
        name="Vertex Group Override",
        description="Leave empty to use the feature mask vertex group name",
        default="",
    )


class AUTHHEAD_PG_FacialFeatures(PropertyGroup):
    features: CollectionProperty(type=AUTHHEAD_PG_FacialFeature)
    feature_list_index: IntProperty(name="Feature Index", default=0)
    registrations: CollectionProperty(type=AUTHHEAD_PG_FeatureRegistration)

    bake_override_existing: BoolProperty(
        name="Override Existing",
        description="Replace split shape keys that already exist; otherwise skip them",
        default=False,
    )
    bake_status: StringProperty(name="Bake Status", default="")


class AUTHHEAD_PG_AuthVariant(PropertyGroup):
    name: StringProperty(name="Shape Key")
    mesh_count: IntProperty(name="Meshes", default=0)
    split_count: IntProperty(name="Split Keys", default=0)


def _on_show_split_keys_changed(self, context):
    from .scene.auth_viewer import refresh_variant_list

    refresh_variant_list(context.scene)


class AUTHHEAD_PG_AuthViewer(PropertyGroup):
    variants: CollectionProperty(type=AUTHHEAD_PG_AuthVariant)
    variant_list_index: IntProperty(name="Variant Index", default=0)
    active_preview: StringProperty(name="Active Preview", default="")
    show_split_keys: BoolProperty(
        name="Show Split Keys",
        description="Include facial feature split shape keys in the variant list",
        default=False,
        update=_on_show_split_keys_changed,
    )
    delete_include_splits: BoolProperty(
        name="Delete Split Keys",
        description="When deleting variants, also remove derived split feature keys",
        default=True,
    )
    status: StringProperty(name="Status", default="")


CLASSES = (
    AUTHHEAD_PG_SceneObjects,
    AUTHHEAD_PG_FbxFile,
    AUTHHEAD_PG_BatchLoad,
    AUTHHEAD_PG_FacialFeature,
    AUTHHEAD_PG_FeatureRegistration,
    AUTHHEAD_PG_FacialFeatures,
    AUTHHEAD_PG_AuthVariant,
    AUTHHEAD_PG_AuthViewer,
)
