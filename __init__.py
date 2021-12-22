bl_info = {
    "name": "BlenderPhotonics",
    "author": "Victor",
    "version": (1, 0),  # 插件版本
    "blender": (2, 91, 0),  # 支持blender版本
    "location": "Layout，UI",
    "description": "Modeling in Blender and autorun mmc in Octave",
    "warning": "work with Blender and MMC in Octave. Matlab is not support. Tested on MacOS；Save your blender file before using this add-on!",
    "doc_url": "github",
    "tracker_url": "bug report",
    "category": "Photon Simulation",
}
import bpy
from .Genert_Volumatic_Mesh import Creatregion
from .ui import Test_Panel
from .Import_Mesh import import_volum_mesh
from .RunMMC import runmmc
from .Niipath import MyProperties
from bpy.props import PointerProperty
from .Genert_mesh_from_nii import niitomesh

def register():
    print("Run MMC in Blender installed")
    bpy.utils.register_class(MyProperties)
    bpy.utils.register_class(niitomesh)
    bpy.utils.register_class(Creatregion)
    bpy.utils.register_class(import_volum_mesh)
    bpy.utils.register_class(runmmc)
    bpy.utils.register_class(Test_Panel)
    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)


def unregister():
    print("Run MMC in Blender uninstalled")
    bpy.utils.unregister_class(MyProperties)
    bpy.utils.unregister_class(niitomesh)
    bpy.utils.unregister_class(Creatregion)
    bpy.utils.unregister_class(import_volum_mesh)
    bpy.utils.unregister_class(runmmc)
    bpy.utils.unregister_class(Test_Panel)
    del bpy.types.Scene.my_tool
