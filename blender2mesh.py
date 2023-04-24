"""Blender2Mesh - converting Blender objects/scene to 3-D tetrahedral mesh

* Authors: (c) 2021-2022 Qianqian Fang <q.fang at neu.edu>
           (c) 2021      Yuxuan Zhang <zhang.yuxuan1 at northeastern.edu>
* License: GNU General Public License V3 or later (GPLv3)
* Website: http://mcx.space/bp

To cite this work, please use the below information

@article{BlenderPhotonics2022,
  author = {Yuxuan Zhang and Qianqian Fang},
  title = {{BlenderPhotonics: an integrated open-source software environment for three-dimensional meshing and photon simulations in complex tissues}},
  volume = {27},
  journal = {Journal of Biomedical Optics},
  number = {8},
  publisher = {SPIE},
  pages = {1 -- 23},
  year = {2022},
  doi = {10.1117/1.JBO.27.8.083014},
  URL = {https://doi.org/10.1117/1.JBO.27.8.083014}
}
"""

import bpy
import numpy as np
import os
from bpy.utils import register_class, unregister_class
from .utils import *

g_maxvol=1.0
g_keepratio=1.0
g_mergetol=0
g_dorepair=False
g_onlysurf=False
g_convtri=True
g_endstep='9'
g_tetgenopt=""
g_voxeldiv = 50
g_colormap = 'jet'
enum_endstep=[('1','Step 1: Convert objects to mesh','Convert objects to mesh'),
             ('2','Step 2: Join all objects','Join all objects'),
             ('3','Step 3: Intersect objects','Intersect objects'),
             ('4','Step 4: Convert to triangles','Merge all visible objects, perform intersection and convert to N-gon or triangular mesh'),
             ('5','Step 5: Export to JMesh','Export the scene to a human-readable universal data exchange file encoded in the JSON format based on the JMesh specification (see http://neurojson.org)'),
             ('6','Step 6: Run Iso2Mesh and load mesh','Output tetrahedral mesh using Iso2Mesh (http://iso2mesh.sf.net)'),
             ('9','Run all steps','Create 3-D tetrahedral meshes using Iso2Mesh and Octave (please save your Blender session first!)')]

class scene2mesh(bpy.types.Operator):
    bl_label = 'Convert scene to voxel mesh'
    bl_description = "Create 3-D voxelization meshes using Iso2Mesh and Octave (please save your Blender session first!)"
    bl_idname = 'blenderphotonics.create3dmesh'

    # creat a interface to set uesrs' model parameter.

    bl_options = {"REGISTER", "UNDO"}
    maxvol: bpy.props.FloatProperty(default=g_maxvol, name="Maximum tet volume")
    keepratio: bpy.props.FloatProperty(default=g_keepratio,name="Fraction edge kept (0-1)")
    mergetol: bpy.props.FloatProperty(default=g_mergetol,name="Tolerance to merge nodes (0 to disable)")
    dorepair: bpy.props.BoolProperty(default=g_dorepair,name="Repair mesh (single object only)")
    onlysurf: bpy.props.BoolProperty(default=g_onlysurf,name="Return triangular surface mesh only (no tetrahedral mesh)")
    convtri: bpy.props.BoolProperty(default=g_convtri,name="Convert to triangular mesh first)")
    endstep: bpy.props.EnumProperty(default=g_endstep, name="Run through step", items = enum_endstep)
    tetgenopt: bpy.props.StringProperty(default=g_tetgenopt,name="Additional tetgen flags")
    voxeldiv: bpy.props.IntProperty(default=g_voxeldiv, name="division number along the shortest edge of the mesh "
                                                             "(resolution), 0 to disable")
    colormap: bpy.props.StringProperty(default=g_colormap,name="color scheme")

    @classmethod
    def description(cls, context, properties):
        hints={}
        for item in enum_endstep:
            hints[item[0]]=item[2]
        return hints[properties.endstep]

    def func(self):
        import jdata as jd

        outputdir = GetBPWorkFolder();
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)

        if(os.path.exists(os.path.join(outputdir,'regionmesh.jmsh'))):
            os.remove(os.path.join(outputdir,'regionmesh.jmsh'))
        if(os.path.exists(os.path.join(outputdir,'volumemesh.jmsh'))):
            os.remove(os.path.join(outputdir,'volumemesh.jmsh'))

        #remove camera and source
        for ob in bpy.context.scene.objects:
            ob.select_set(False)
            print(ob.type)
            if ob.type == 'CAMERA' or ob.type == 'LIGHT' or ob.type == 'EMPTY' or ob.type == 'LAMP' or ob.type == 'SPEAKER':
                ob.select_set(True)

        bpy.ops.object.delete()

        obj = bpy.context.view_layer.objects.active

        if(not self.convtri):
            bpy.ops.object.select_by_type(type='MESH')
            bpy.ops.object.select_all(action='INVERT')
        else:
            bpy.ops.object.select_all(action='SELECT')
        if len(bpy.context.selected_objects)>=1:
            bpy.ops.object.convert(target='MESH')

        # at this point, objects are converted to mesh if possible
        if(int(self.endstep)<2):
            return

        bpy.ops.object.select_all(action='SELECT')
        if len(bpy.context.selected_objects)>=2:
            bpy.ops.object.join()

        # at this point, objects are jointed
        if(int(self.endstep)<3):
            return

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        try:
            bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE', solver='EXACT')
            print("use exact intersection solver")
        except:
            bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE')
            print("use fast intersection solver")

        # at this point, overlapping objects are intersected
        if(int(self.endstep)<4):
            return

        if(self.convtri):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

        # at this point, if enabled, surfaces are converted to triangular meshes
        if(int(self.endstep)<5):
            return

        #output mesh data to Octave
        # this works only in object mode,
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        obj = bpy.context.view_layer.objects.active

        vert = np.zeros(3 * len(obj.data.vertices))
        obj.data.vertices.foreach_get('co', vert)
        v = vert.reshape(-1, 3)

        edgeslist = np.zeros(2 * len(obj.data.edges))
        obj.data.edges.foreach_get('vertices', edgeslist)
        e = (edgeslist + 1).reshape(-1, 2)

        if (self.convtri):
            faceslist = np.zeros(3 * len(obj.data.polygons))
            obj.data.polygons.foreach_get('vertices', faceslist)
            f = (faceslist + 1).reshape(-1, 3)
        else:
            faceslist = [(np.array(face.vertices[:]) + 1).tolist() for face in obj.data.polygons]
            f = faceslist

        # Save file
        meshdata={'_DataInfo_': {'JMeshVersion': '0.5', 'Comment':'Created by BlenderPhotonics (http:\/\/mcx.space\/BlenderPhotonics)'},
            'MeshVertex3':v, 'MeshPoly':f, 'param':{'keepratio':self.keepratio, 'maxvol':self.maxvol, 'mergetol':self.mergetol, 'dorepair':self.dorepair, 'tetgenopt':self.tetgenopt, 'div':self.voxeldiv}}
        jd.save(meshdata,os.path.join(outputdir,'blendermesh.jmsh'))

        if(int(self.endstep)==5):
            bpy.ops.blender2mesh.invoke_saveas('INVOKE_DEFAULT')

        # at this point, all mesh objects are saved to a jmesh file under work-dir as blendermesh.json
        if(int(self.endstep)<6):
            return

        try:
            if(bpy.context.scene.blender_photonics.backend == "octave"):
                import oct2py as op
                oc = op.Oct2Py()
            else:
                import matlab.engine as op
                oc = op.start_matlab()
        except ImportError:
            raise ImportError('To run this feature, you must install the oct2py or matlab.engine Python modulem first, based on your choice of the backend')

        oc.addpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'script'))

        oc.feval('blender2mesh',os.path.join(outputdir,'blendermesh.jmsh'), nargout=0)

        # import volum mesh to blender(just for user to check the result)
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)
        bpy.ops.outliner.orphans_purge(do_recursive=True)

        if self.voxeldiv:
            outputmesh=oc.load(os.path.join(outputdir,'ImageMesh.mat'))
            LoadVolMesh(outputmesh,'Iso2Mesh', outputdir, mode='model_view', colormap=self.colormap)
            bpy.context.view_layer.objects.active=bpy.data.objects['Iso2Mesh']
        else:
            if (not self.onlysurf):
                outputmesh = jd.load(os.path.join(outputdir, 'volumemesh.jmsh'))
                LoadTetMesh(outputmesh, 'Iso2Mesh')
                bpy.context.view_layer.objects.active = bpy.data.objects['Iso2Mesh']
            else:
                regiondata = jd.load(os.path.join(outputdir, 'regionmesh.jmsh'))
                if (len(regiondata.keys()) > 0):
                    LoadReginalMesh(regiondata, 'region_')
                    bpy.context.view_layer.objects.active = bpy.data.objects['region_1']


        # at this point, if successful, iso2mesh generated mesh objects are imported into blender
        if(int(self.endstep)<7):
            return

        ShowMessageBox("Mesh generation is complete. The combined tetrahedral mesh is imported for inspection. To set optical properties for each region, please click 'Load mesh and setup simulation'", "BlenderPhotonics")

    def execute(self, context):
        print("begin to generate mesh")
        self.func()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


#
#   Dialog to set meshing properties
#
class setmeshingprop(bpy.types.Panel):
    bl_label = "Mesh generation setting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global g_maxvol, g_keepratio, g_mergetol, g_dorepair, onlysurf, g_convtri, g_tetgenopt, g_endstep
        self.layout.operator("object.dialog_operator")

# This operator will open Blender's file chooser when invoked
# and store the selected filepath in self.filepath and print it
# to the console using window_manager.fileselect_add()
class BLENDER2MESH_OT_invoke_saveas(bpy.types.Operator):
    bl_idname = "blender2mesh.invoke_saveas"
    bl_label = "Export scene in a JMesh/JSON universal exchange file"

    filepath: bpy.props.StringProperty(default='',subtype='DIR_PATH')

    def execute(self, context):
        print(self.filepath)
        if(not (self.filepath == "")):
            if os.name == 'nt':
                os.popen("copy '"+os.path.join(GetBPWorkFolder(),'blendermesh.jmsh')+"' '"+self.filepath+"'");
            else:
                os.popen("cp '"+os.path.join(GetBPWorkFolder(),'blendermesh.jmsh')+"' '"+self.filepath+"'");
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
register_class(BLENDER2MESH_OT_invoke_saveas)
