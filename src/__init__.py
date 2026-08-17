import bpy
import inspect

from .terrain import *


bl_info = {
    "name": "terrain_erosion_addon",
    "author": "lucas",
    "description": "creates terrain using erosion",
    "blender": (5, 1, 2),
    "version": (0, 0, 1),
    "location": "View3D",
    "warning": "",
    "category": "Mesh",
}

classes = [
    TerrainProps,
    TerrainGenerateNoise,
    TerrainGenerateErosion,
    TerrainPanel,
]


def register():
    for c in classes:
        try:
            bpy.utils.register_class(c)
        except AttributeError as e:
            print(
                f"Encountered an error while loading your {c.__name__} module.\n"
                f"\tError: '{e}'\n"
                f"\t(Take a look in '{inspect.getfile(c)}' to find out what's missing)"
            )

    bpy.types.Scene.terrain_props = bpy.props.PointerProperty(type=TerrainProps)


def unregister():
    del bpy.types.Scene.terrain_props

    for c in classes:
        bpy.utils.unregister_class(c)
