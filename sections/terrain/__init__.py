import bpy
import bmesh

from .terrain import *


def regenerate_terrain(context: bpy.types.Context) -> None:
    props = context.scene.terrain_props

    bm = bmesh.new()
    generate_grid(
        bm,
        props.grid_points_x,
        props.grid_points_y,
    )

    apply_heightmap_noise(
        bm,
        props.noise_scale,
        props.noise_height,
        props.layer_amount,
        props.offset_x,
        props.offset_y,
    )

    debug_bmeshes: list[bmesh.types.BMesh] = []
    erosion_simulation(
        bm,
        props.grid_points_x,
        props.grid_points_y,
        debug_bmeshes,
    )

    # ---------------------------------------------------------

    # remove old droplet debug objects from the previous run
    for obj in list(bpy.data.objects):
        if obj.name.startswith("ErosionDroplet_"):
            old_mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if old_mesh is not None and old_mesh.users == 0:
                bpy.data.meshes.remove(old_mesh)

    # put the circle debug bmeshes into the scene
    droplet_mat = get_droplet_material()
    for i, orb_bm in enumerate(debug_bmeshes):
        orb_mesh = bpy.data.meshes.new(f"ErosionDroplet_{i}")
        orb_bm.to_mesh(orb_mesh)
        orb_bm.free()
        orb_mesh.materials.append(droplet_mat)

        orb_obj = bpy.data.objects.new(f"ErosionDroplet_{i}", orb_mesh)
        context.collection.objects.link(orb_obj)

    # -------------------------------------------------------------------

    # put the bmesh into the
    mesh = bpy.data.meshes.new("Terrain")
    bm.to_mesh(mesh)
    bm.free()

    # if we found an existing mesh object of name Terrain then use it
    obj = bpy.data.objects.get("Terrain")
    if obj is not None and obj.type == "MESH":
        old_mesh = obj.data
        obj.data = mesh

        # remove old mesh if no one is using it
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    # if no such mesh object was found then make a new one
    else:
        obj = bpy.data.objects.new("Terrain", mesh)
        context.collection.objects.link(obj)


# ----------------------------------------------------------------


def get_droplet_material() -> bpy.types.Material:
    mat = bpy.data.materials.get("ErosionDropletRed")
    if mat is None:
        mat = bpy.data.materials.new("ErosionDropletRed")
        mat.diffuse_color = (1.0, 0.0, 0.0, 1.0)
    return mat


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


def _on_prop_update(self, context: bpy.types.Context) -> None:
    if self.auto_regenerate:
        regenerate_terrain(context)


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


class TerrainProps(bpy.types.PropertyGroup):
    auto_regenerate: bpy.props.BoolProperty(name="Auto Regenerate", default=False)

    grid_points_x: bpy.props.IntProperty(
        name="grid_points_x", default=255, min=2, update=_on_prop_update
    )
    grid_points_y: bpy.props.IntProperty(
        name="grid_points_y", default=255, min=2, update=_on_prop_update
    )
    noise_scale: bpy.props.FloatProperty(
        name="Noise Scale", default=0.01, min=0.0, update=_on_prop_update
    )
    noise_height: bpy.props.FloatProperty(
        name="Noise Height", default=30.0, min=0.0, update=_on_prop_update
    )
    layer_amount: bpy.props.IntProperty(
        name="layer_amount", default=4, min=1, update=_on_prop_update
    )
    offset_x: bpy.props.FloatProperty(
        name="offset_x", default=0.0, min=-9999.0, update=_on_prop_update
    )
    offset_y: bpy.props.FloatProperty(
        name="offset_y", default=0.0, min=-9999.0, update=_on_prop_update
    )


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


class TerrainGenerate(bpy.types.Operator):
    bl_idname = "terrain.generate"
    bl_label = "Generate"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        regenerate_terrain(context)
        return {"FINISHED"}


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


class TerrainPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_Terrain"
    bl_label = "Terrain"

    bl_category = "terrain"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        props = context.scene.terrain_props

        self.layout.prop(props, "auto_regenerate")
        self.layout.prop(props, "grid_points_x")
        self.layout.prop(props, "grid_points_y")
        self.layout.prop(props, "noise_scale")
        self.layout.prop(props, "noise_height")
        self.layout.prop(props, "layer_amount")
        self.layout.prop(props, "offset_x")
        self.layout.prop(props, "offset_y")
        self.layout.operator("terrain.generate")
