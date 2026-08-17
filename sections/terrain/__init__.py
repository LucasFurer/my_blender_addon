import bpy
import bmesh

from .terrain import *


def regenerate_terrain_noise(context: bpy.types.Context) -> None:
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

    # ---------------------------------------------------------

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


def regenerate_terrain_erosion(context: bpy.types.Context) -> None:
    props = context.scene.terrain_props

    obj = bpy.data.objects.get("Terrain")
    if obj is not None and obj.type == "MESH":
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        debug_bmeshes: list[bmesh.types.BMesh] = []
        erosion_simulation(
            bm,
            props.grid_points_x,
            props.grid_points_y,
            debug_bmeshes,
            props.iteration_amount,
            props.maxpath,
            props.inertia,
            props.capacity,
            props.minslope,
            props.gravity,
            props.evaporation,
            props.radius,
            props.erosion,
            props.deposition,
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

        # put the bmesh into the
        bm.to_mesh(mesh)
        bm.free()

    else:
        print("couldnt find the Terrain object")


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
    if self.auto_regenerate_noise:
        regenerate_terrain_noise(context)

    if self.auto_regenerate_erosion:
        regenerate_terrain_erosion(context)


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


class TerrainProps(bpy.types.PropertyGroup):
    auto_regenerate_noise: bpy.props.BoolProperty(
        name="Auto Regenerate noise terrain", default=False
    )

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

    auto_regenerate_erosion: bpy.props.BoolProperty(
        name="Auto Regenerate erosion terrain", default=False
    )

    iteration_amount: bpy.props.IntProperty(
        name="iteration_amount", default=10000, min=1, update=_on_prop_update
    )

    maxpath: bpy.props.IntProperty(
        name="maxpath", default=30, min=1, update=_on_prop_update
    )

    inertia: bpy.props.FloatProperty(
        name="inertia", default=0.3, min=0.0, update=_on_prop_update
    )

    capacity: bpy.props.FloatProperty(
        name="capacity", default=4, min=0.0, update=_on_prop_update
    )

    minslope: bpy.props.FloatProperty(
        name="minslope", default=0.01, min=0.0, update=_on_prop_update
    )

    gravity: bpy.props.FloatProperty(
        name="gravity", default=10.0, min=0.0, update=_on_prop_update
    )

    evaporation: bpy.props.FloatProperty(
        name="evaporation", default=0.05, min=0.0, update=_on_prop_update
    )

    radius: bpy.props.FloatProperty(
        name="radius", default=4.0, min=0.0, update=_on_prop_update
    )

    erosion: bpy.props.FloatProperty(
        name="erosion", default=0.01, min=0.0, update=_on_prop_update
    )

    deposition: bpy.props.FloatProperty(
        name="deposition", default=0.1, min=0.0, update=_on_prop_update
    )


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


class TerrainGenerateNoise(bpy.types.Operator):
    bl_idname = "noiseterrain.generate"
    bl_label = "Generate noise terrain"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        regenerate_terrain_noise(context)
        return {"FINISHED"}


class TerrainGenerateErosion(bpy.types.Operator):
    bl_idname = "erosionterrain.generate"
    bl_label = "Generate erosion terrain"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        regenerate_terrain_erosion(context)
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

        self.layout.prop(props, "auto_regenerate_noise")
        self.layout.prop(props, "grid_points_x")
        self.layout.prop(props, "grid_points_y")
        self.layout.prop(props, "noise_scale")
        self.layout.prop(props, "noise_height")
        self.layout.prop(props, "layer_amount")
        self.layout.prop(props, "offset_x")
        self.layout.prop(props, "offset_y")
        self.layout.operator("noiseterrain.generate")
        self.layout.prop(props, "auto_regenerate_erosion")
        self.layout.prop(props, "iteration_amount")
        self.layout.prop(props, "maxpath")
        self.layout.prop(props, "inertia")
        self.layout.prop(props, "capacity")
        self.layout.prop(props, "minslope")
        self.layout.prop(props, "gravity")
        self.layout.prop(props, "evaporation")
        self.layout.prop(props, "radius")
        self.layout.prop(props, "erosion")
        self.layout.prop(props, "deposition")
        self.layout.operator("erosionterrain.generate")
