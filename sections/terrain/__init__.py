from .terrain import *

import bpy
import bmesh


class TerrainProps(bpy.types.PropertyGroup):
    grid_points_x: bpy.props.IntProperty(name="grid_points_x", default=100, min=2)
    grid_points_y: bpy.props.IntProperty(name="grid_points_y", default=100, min=2)
    grid_size_x: bpy.props.FloatProperty(name="grid_size_x", default=100.0, min=1.0)
    grid_size_y: bpy.props.FloatProperty(name="grid_size_y", default=100.0, min=1.0)


class TerrainGenerate(bpy.types.Operator):
    bl_idname = "terrain.generate"
    bl_label = "Generate"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.terrain_props

        bm = bmesh.new()
        generate_grid(
            bm,
            props.grid_points_x,
            props.grid_points_y,
            props.grid_size_x,
            props.grid_size_y,
        )

        mesh = bpy.data.meshes.new("Terrain")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new("Terrain", mesh)
        context.collection.objects.link(obj)

        return {"FINISHED"}


class TerrainPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_Terrain"
    bl_label = "Terrain"

    bl_category = "terrain"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        props = context.scene.terrain_props

        self.layout.prop(props, "grid_points_x")
        self.layout.prop(props, "grid_points_y")
        self.layout.prop(props, "grid_size_x")
        self.layout.prop(props, "grid_size_y")
        self.layout.operator("terrain.generate")
