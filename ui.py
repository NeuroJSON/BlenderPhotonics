import bpy
from .blender2mesh import scene2mesh
from .mesh2blender import mesh2scene
from .runmmc import runmmc
from .niifile import niifile
from .nii2mesh import nii2mesh

class BlenderPhotonics_UI(bpy.types.Panel):
    bl_label = 'BlenderPhotonics 0.5'
    bl_idname = 'BLENDERPHOTONICS_PT_UI'
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
        bp = scene.blender_photonics
        layout.prop(bp, "path")
        col = layout.column()
        col.operator(nii2mesh.bl_idname)
        col.operator(scene2mesh.bl_idname)
        col.operator(mesh2scene.bl_idname)
        col.operator(runmmc.bl_idname)
