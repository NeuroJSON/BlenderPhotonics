import bpy
import oct2py as op
import numpy as np
import jdata as jd
import os
from bpy.utils import register_class, unregister_class
from .utils import *

g_actionlevel=1.0
g_convtri=True
g_tetgenopt=""
g_action='repair'

class object2surf(bpy.types.Operator):
    bl_label = 'Selected objects to surfaces'
    bl_description = "Create surface meshes from selected objects and refine (smoothing, refine, Boolean, repair and simplification)"
    bl_idname = 'blenderphotonics.object2surf'

    # creat a interface to set uesrs' model parameter.

    bl_options = {"REGISTER", "UNDO"}
    convtri: bpy.props.BoolProperty(default=g_convtri,name="Convert to triangular mesh first)")
    action: bpy.props.EnumProperty(default=g_action, name="Run through step", 
                                    items = [('import','Import surface mesh from file','Import surface mesh from JMesh/STL/OFF/SMF/ASC/MEDIT/GTS to Blender'), 
                                             ('export','Export selected to JSON/JMesh','Export selected objects to JSON/JMesh exchange file'), 
                                             ('boolean','Perform Boolean operation','Perform Boolean operation'), 
                                             ('smooth','Smooth selected mesh object','Smooth selected mesh object'), 
                                             ('reorient','Reorient all triangles','Reorient all triangles in counter-clockwise'),
                                             ('repair','Fix self-intersection and holes','Fix self-intersection and holes by calling meshfix'),
                                             ('simplify','Surface simplification', 'Surface simplification')])
    actionlevel: bpy.props.FloatProperty(default=0, name="Action parameter (boolean-1:union)")
    tetgenopt: bpy.props.StringProperty(default=g_tetgenopt,name="Additional tetgen flags")

    @classmethod
    def description(cls, context, properties):
        hints={'import': 'Import surface mesh from JMesh/STL/OFF/SMF/ASC/MEDIT/GTS to Blender', 
               'export': 'Export selected objects to JSON/JMesh exchange file',
               'boolean': 'Perform Boolean operation',
               'smooth': 'Smooth selected mesh object',
               'reorient': 'Reorient all triangles in counter-clockwise',
               'repair': 'Fix self-intersection and holes by calling meshfix',
               'simplify': 'Surface simplification'
               }
        return hints[properties.action]

    def func(self):
        oc = op.Oct2Py()
        oc.addpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'script'))

        outputdir = GetBPWorkFolder();
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)

        if(os.path.exists(os.path.join(outputdir,'surfacemesh.jmsh'))):
            os.remove(os.path.join(outputdir,'surfacemesh.jmsh'))

        if len(bpy.context.selected_objects)<1:
            ShowMessageBox("Must select at least one object (for Boolean operations, select two)", "BlenderPhotonics")
            return;

        #remove camera and source
        for ob in bpy.context.selected_objects:
            print(ob.type)
            if ob.type == 'CAMERA' or ob.type == 'LIGHT' or ob.type == 'EMPTY' or ob.type == 'LAMP' or ob.type == 'SPEAKER':
                ob.select_set(False)

        bpy.ops.object.convert(target='MESH')

        if(self.convtri):
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

        if len(bpy.context.selected_objects)<1:
            ShowMessageBox("No mesh-like object was selected, skip", "BlenderPhotonics")
            return;

        surfdata={'_DataInfo_': {'JMeshVersion': '0.5', 'Comment':'Object surface mesh created by BlenderPhotonics (http:\/\/mcx.space\/BlenderPhotonics)'}};
        surfdata['MeshGroup']=[]
        idx=0
        for ob in bpy.context.selected_objects:
            objsurf=GetNodeFacefromObject(obj, self.convtri)
            surfdata['BlenderObject'][idx]={ob.name:objsurf}
            idx+=1

        surfdata['param']={'action':self.action, 'level':self.actionlevel}

        jd.save(surfdata,os.path.join(outputdir,'blendersurf.jmsh',indent=2))

        # at this point, objects are converted to mesh if possible
        if(self.action == 'export'):
            bpy.ops.obj2mesh.invoke_export('INVOKE_DEFAULT')
            return

        oc.run(os.path.join(os.path.dirname(os.path.abspath(__file__)),'script','blender2surf.m'))

        # import volum mesh to blender(just for user to check the result)
        if len(bpy.context.selected_objects)>=1:
            bpy.ops.object.delete()

        regiondata=jd.load(os.path.join(outputdir,'surfacemesh.jmsh'))
        if(len(regiondata.keys())>0):
            LoadReginalMesh(regiondata,'region_')
            bpy.context.view_layer.objects.active=bpy.data.objects['region_1']
        
        bpy.context.space_data.shading.type = 'WIREFRAME'


        ShowMessageBox("Mesh generation is complete. The combined surface mesh is imported for inspection.", "BlenderPhotonics")

    def execute(self, context):
        print("begin to process object surface mesh")
        self.func()
        return {"FINISHED"}

    def invoke(self, context, event):
        global g_action, g_actionlevel, g_convtri, g_tetgenopt
        self.action = g_action
        self.actionlevel = g_actionlevel
        self.convtri = g_convtri
        self.tetgenopt = g_tetgenopt
        return context.window_manager.invoke_props_dialog(self)


#
#   Dialog to set meshing properties
#
class setmeshingprop(bpy.types.Panel):
    bl_label = "Object surface mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global g_action, g_actionlevel, g_convtri, g_tetgenopt
        self.layout.operator("object.dialog_operator")

# This operator will open Blender's file chooser when invoked
# and store the selected filepath in self.filepath and print it
# to the console using window_manager.fileselect_add()
class OBJ2SURF_OT_invoke_export(bpy.types.Operator):
    bl_idname = "obj2surf.invoke_export"
    bl_label = "Export scene in a JMesh/JSON universal exchange file"

    filepath: bpy.props.StringProperty(default='',subtype='DIR_PATH')

    def execute(self, context):
        print(self.filepath)
        if(not (self.filepath == "")):
            if os.name == 'nt':
                os.popen("copy '"+os.path.join(GetBPWorkFolder(),'blendersurf.jmsh')+"' '"+self.filepath+"'");
            else:
                os.popen("cp '"+os.path.join(GetBPWorkFolder(),'blendersurf.jmsh')+"' '"+self.filepath+"'");
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
register_class(OBJ2SURF_OT_invoke_export)


# This operator will open Blender's file chooser when invoked
# and store the selected filepath in self.filepath and print it
# to the console using window_manager.fileselect_add()
class OBJ2SURF_OT_invoke_import(bpy.types.Operator):
    bl_idname = "obj2surf.invoke_import"
    bl_label = "Import object surface mesh in a JMesh/JSON universal exchange file"

    filepath: bpy.props.StringProperty(default='',subtype='DIR_PATH')

    def execute(self, context):
        print(self.filepath)
        if(not (self.filepath == "")):
            print(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
register_class(OBJ2SURF_OT_invoke_import)
