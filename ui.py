import bpy
from .blender2mesh import scene2mesh
from .mesh2blender import mesh2scene
from .runmmc import runmmc
from .niifile import niifile
from .nii2mesh import nii2mesh
from .obj2surf import object2surf

class BlenderPhotonics_UI(bpy.types.Panel):
    bl_label = 'BlenderPhotonics v2022'
    bl_idname = 'BLENDERPHOTONICS_PT_UI'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderPhotonics"

    @classmethod
    def poll(self,context):
        return context.mode in {'EDIT_MESH','OBJECT','PAINT_WEIGHT'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        bp = scene.blender_photonics
        layout.label(text="Blender2Mesh", icon='SHADING_SOLID')
        colb2m = layout.column()
        colb2m.operator(scene2mesh.bl_idname,icon='MESH_ICOSPHERE').endstep='9'
        colb2m.operator(scene2mesh.bl_idname,text='Export scene to JMesh/JSON',icon='FILE_TICK').endstep='5'
        colb2m.operator(scene2mesh.bl_idname,text='Merge objects only',icon='MOD_BOOLEAN').endstep='4'

        layout.separator()
        layout.label(text="Volume2Mesh", icon='SHADING_SOLID')
        layout.prop(bp, "path")
        colv2m = layout.column()
        colv2m.operator(nii2mesh.bl_idname,icon='MESH_GRID')

        layout.separator()
        layout.label(text="Surface2Mesh", icon='SHADING_SOLID')
        layout.prop(bp, "surffile")
        cols2m = layout.column()
        cols2m.operator(object2surf.bl_idname,text='Import surface mesh',icon='IMPORT').action='import'
        cols2m.operator(object2surf.bl_idname,icon='SURFACE_DATA').action='export'
        cols2m.operator(object2surf.bl_idname,text='Simplify triangular mesh',icon='MOD_SIMPLIFY').action='simplify'
        cols2m.operator(object2surf.bl_idname,text='Repair and close triangular mesh',icon='MOD_SUBSURF').action='repair'
        cols2m.operator(object2surf.bl_idname,text='First triangular mesh cut by 2nd',icon='MOD_MASK').action='boolean-first'
        cols2m.operator(object2surf.bl_idname,text='Second triangular mesh cut by 1st',icon='MOD_MASK').action='boolean-second'

        layout.separator()
        layout.label(text="Multiphysics Simulation", icon='SHADING_SOLID')
        colmmc = layout.column()
        colmmc.operator(mesh2scene.bl_idname,icon='EDITMODE_HLT')
        colmmc.operator(runmmc.bl_idname,icon='LIGHT_AREA')

        layout.separator()
        layout.label(text="Tutorials and Websites", icon='SHADING_SOLID')
        colurl = layout.column()
        op=colurl.operator('wm.url_open', text='Iso2Mesh Wiki',icon='URL')
        op.url='http://iso2mesh.sf.net'
        op=colurl.operator('wm.url_open', text='JMesh Specification',icon='URL')
        op.url='https://github.com/NeuroJSON/jmesh/blob/master/JMesh_specification.md'
        op=colurl.operator('wm.url_open', text='MMC tutorials',icon='URL')
        op.url='http://mcx.space/wiki/?Learn#mmc'
        op=colurl.operator('wm.url_open', text='Brain2Mesh homepage',icon='URL')
        op.url='http://mcx.space/brain2mesh'
        layout.label(text="Funded by NIH R01-GM114365 & U24-NS124027", icon='HEART')
