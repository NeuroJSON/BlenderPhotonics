import bpy
from .blender2mesh import scene2mesh
from .mesh2blender import mesh2scene
from .runmmc import runmmc
from .niifile import niifile
from .nii2mesh import nii2mesh

class BlenderPhotonics_UI(bpy.types.Panel):
    bl_label = 'BlenderPhotonics v2022'
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
        layout.label(text="Blender2Mesh", icon='SHADING_SOLID')
        colb2m = layout.column()
        colb2m.operator(scene2mesh.bl_idname,icon='MESH_ICOSPHERE')

        layout.separator()
        layout.label(text="Volume2Mesh", icon='SHADING_SOLID')
        layout.prop(bp, "path")
        colv2m = layout.column()
        colv2m.operator(nii2mesh.bl_idname,icon='MESH_GRID')

        layout.separator()
        layout.label(text="Surface2Mesh", icon='SHADING_SOLID')

        layout.separator()
        layout.label(text="MMC Photon Simulation", icon='SHADING_SOLID')

        colmmc = layout.column()
        colmmc.operator(mesh2scene.bl_idname,icon='EDITMODE_HLT')
        colmmc.operator(runmmc.bl_idname,icon='LIGHT_AREA')

        layout.separator()
        layout.label(text="Tutorials and Websites", icon='SHADING_SOLID')
        colurl = layout.column()
        op=colurl.operator('wm.url_open', text='Iso2Mesh Wiki',icon='URL')
        op.url='http://iso2mesh.sf.net'
        op=colurl.operator('wm.url_open', text='MMC tutorials',icon='URL')
        op.url='http://mcx.space/wiki/?Learn#mmc'
        op=colurl.operator('wm.url_open', text='Brain2Mesh homepage',icon='URL')
        op.url='http://mcx.space/brain2mesh'
