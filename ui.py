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
    bl_category = "Meshing"

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
        cols2m = layout.column()
        cols2m.operator(object2surf.bl_idname,text='Import surface mesh',icon='IMPORT').action='import'
        cols2m.operator(object2surf.bl_idname,icon='EXPORT').action='export'
        cols2m.operator(object2surf.bl_idname,text='Repair and close triangular mesh',icon='MOD_SUBSURF').action='repair'
        rowbool = layout.row()
        rowbool.label(text='Boolean')
        rowbool.operator(object2surf.bl_idname,text='and',icon='SELECT_INTERSECT').action='boolean-and'
        rowbool.operator(object2surf.bl_idname,text='or',icon='SELECT_EXTEND').action='boolean-or'
        rowbool.operator(object2surf.bl_idname,text='xor',icon='XRAY').action='boolean-resolve'
        rowbool2 = layout.row()
        rowbool2.operator(object2surf.bl_idname,text='diff',icon='SELECT_SUBTRACT').action='boolean-diff'
        rowbool2.operator(object2surf.bl_idname,text='1st',icon='OVERLAY').action='boolean-first'
        rowbool2.operator(object2surf.bl_idname,text='2nd',icon='MOD_MASK').action='boolean-second'
        rowbool2.operator(object2surf.bl_idname,text='simplify',icon='MOD_SIMPLIFY').action='simplify'

        layout.separator()
        layout.label(text="Multiphysics Simulation", icon='SHADING_SOLID')
        colmmc = layout.column()
        colmmc.operator(mesh2scene.bl_idname,icon='EDITMODE_HLT')
        colmmc.operator(runmmc.bl_idname,icon='LIGHT_AREA')

        layout.separator()
        layout.label(text="Tutorials and Websites", icon='SHADING_SOLID')
        colurl = layout.row()
        op=colurl.operator('wm.url_open', text='Iso2Mesh',icon='URL')
        op.url='http://iso2mesh.sf.net'
        op=colurl.operator('wm.url_open', text='JMesh spec',icon='URL')
        op.url='https://github.com/NeuroJSON/jmesh/blob/master/JMesh_specification.md'
        colurl2 = layout.row()
        op=colurl2.operator('wm.url_open', text='MMC wiki',icon='URL')
        op.url='http://mcx.space/wiki/?Learn#mmc'
        op=colurl2.operator('wm.url_open', text='Brain2Mesh',icon='URL')
        op.url='http://mcx.space/brain2mesh'
        layout.label(text="Funded by NIH R01-GM114365 & U24-NS124027", icon='HEART')
