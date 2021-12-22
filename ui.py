import bpy
from .Genert_Volumatic_Mesh import Creatregion
from .Import_Mesh import import_volum_mesh
from .RunMMC import runmmc
from .Niipath import MyProperties
from .Genert_mesh_from_nii import niitomesh

class Test_Panel(bpy.types.Panel):
    bl_label = 'BlenderPhotonics'
    bl_idname = 'A_TEST_PL'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderPhotonics"
    bl_context = "objectmode"

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        layout.prop(mytool, "my_path")
        col = layout.column()
        col.operator(niitomesh.bl_idname)
        col.operator(Creatregion.bl_idname)
        col.operator(import_volum_mesh.bl_idname)
        col.operator(runmmc.bl_idname)
