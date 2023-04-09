"""Blender2Mesh - converting Blender objects/scene to 3-D tetrahedral mesh

* Authors: (c) 2021-2022 Qianqian Fang <q.fang at neu.edu>
           (c) 2021      Yuxuan Zhang <zhang.yuxuan1 at northeastern.edu>
* License: GNU General Public License V3 or later (GPLv3)
* Website: http://mcx.space/bp

To cite this work, please use the below information

@article{BlenderPhotonics2022,
  author = {Yuxuan Zhang and Qianqian Fang},
  title = {{BlenderPhotonics: an integrated open-source software environment for three-dimensional meshing and photon
   simulations in complex tissues}},
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
import jdata as jd
import os
from bpy.utils import register_class, unregister_class
from .utils import *

G_MAXVOL = 1.0
G_KEEPRATIO = 1.0
G_MERGETOL = 0
G_DOREPAIR = False
G_ONLYSURF = False
G_CONVTRI = True
G_ENDSTEP = '9'
G_TETGENOPT = ""
ENUM_ENDSTEP = [('1', 'Step 1: Convert objects to mesh', 'Convert objects to mesh'),
                ('2', 'Step 2: Join all objects', 'Join all objects'),
                ('3', 'Step 3: Intersect objects', 'Intersect objects'),
                ('4', 'Step 4: Convert to triangles',
                 'Merge all visible objects, perform intersection and convert to N-gon or triangular mesh'),
                ('5', 'Step 5: Export to JMesh',
                 'Export the scene to a human-readable universal data exchange file encoded in the JSON format based '
                 'on the JMesh specification (see http://neurojson.org)'),
                ('6', 'Step 6: Run Iso2Mesh and load mesh',
                 'Output tetrahedral mesh using Iso2Mesh (http://iso2mesh.sf.net)'),
                ('9', 'Run all steps',
                 'Create 3-D tetrahedral meshes using Iso2Mesh and Octave (please save your Blender session first!)')]


class scene2mesh(bpy.types.Operator):
    bl_label = 'Convert scene to tetra mesh'
    bl_description = "Create 3-D tetrahedral meshes using Iso2Mesh and Octave (please save your Blender session first!)"
    bl_idname = 'blenderphotonics.create3dmesh'

    # create an interface to set user's model parameter.

    bl_options = {"REGISTER", "UNDO"}

    maxvol: bpy.props.FloatProperty(default=G_MAXVOL, name="Maximum tet volume")
    keepratio: bpy.props.FloatProperty(default=G_KEEPRATIO, name="Fraction edge kept (0-1)")
    mergetol: bpy.props.FloatProperty(default=G_MERGETOL, name="Tolerance to merge nodes (0 to disable)")
    dorepair: bpy.props.BoolProperty(default=G_DOREPAIR, name="Repair mesh (single object only)")
    onlysurf: bpy.props.BoolProperty(default=G_ONLYSURF,
                                     name="Return triangular surface mesh only (no tetrahedral mesh)")
    convtri: bpy.props.BoolProperty(default=G_CONVTRI, name="Convert to triangular mesh first)")
    endstep: bpy.props.EnumProperty(default=G_ENDSTEP, name="Run through step", items=ENUM_ENDSTEP)
    tetgenopt: bpy.props.StringProperty(default=G_TETGENOPT, name="Additional tetgen flags")

    @classmethod
    def description(cls, context, properties):
        return [desc for idx, _, desc in ENUM_ENDSTEP if idx == properties.endstep][0]

    def func(self):
        outputdir = GetBPWorkFolder()
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)

        if os.path.exists(os.path.join(outputdir, 'regionmesh.jmsh')):
            os.remove(os.path.join(outputdir, 'regionmesh.jmsh'))
        if os.path.exists(os.path.join(outputdir, 'volumemesh.jmsh')):
            os.remove(os.path.join(outputdir, 'volumemesh.jmsh'))

        # remove camera and source
        for ob in bpy.context.scene.objects:
            ob.select_set(False)
            print(ob.type)
            if ob.type in ('CAMERA', 'LIGHT', 'EMPTY', 'LAMP', 'SPEAKER'):
                ob.select_set(True)

        bpy.ops.object.delete()

        obj = bpy.context.view_layer.objects.active

        if not self.convtri:
            bpy.ops.object.select_by_type(type='MESH')
            bpy.ops.object.select_all(action='INVERT')
        else:
            bpy.ops.object.select_all(action='SELECT')
        if len(bpy.context.selected_objects) >= 1:
            bpy.ops.object.convert(target='MESH')

        # at this point, objects are converted to mesh if possible
        if self.endstep < '2':
            return

        bpy.ops.object.select_all(action='SELECT')
        if len(bpy.context.selected_objects) >= 2:
            bpy.ops.object.join()

        # at this point, objects are jointed
        if self.endstep < '3':
            return

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        try:
            bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE', solver='EXACT')
            print("use exact intersection solver")
        except RuntimeError:
            bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE')
            print("use fast intersection solver")

        # at this point, overlapping objects are intersected
        if self.endstep < '4':
            return

        if self.convtri:
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

        # at this point, if enabled, surfaces are converted to triangular meshes
        if self.endstep < '5':
            return

        # output mesh data to Octave
        # this works only in object mode,
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        obj = bpy.context.view_layer.objects.active
        verts = [obj.matrix_world @ vert.co for vert in obj.data.vertices]
        edges = [edge.vertices[:] for edge in obj.data.edges]
        faces = [(np.array(face.vertices[:]) + 1).tolist() for face in obj.data.polygons]
        v = np.array(verts)
        if self.convtri:
            f = np.array(faces)
        else:
            f = faces

        # Save file
        meshdata = {'_DataInfo_': {'JMeshVersion': '0.5',
                                   'Comment': 'Created by BlenderPhotonics (http://mcx.space/BlenderPhotonics)'},
                    'MeshVertex3': v, 'MeshPoly': f,
                    'param': {'keepratio': self.keepratio, 'maxvol': self.maxvol, 'mergetol': self.mergetol,
                              'dorepair': self.dorepair, 'tetgenopt': self.tetgenopt}}
        jd.save(meshdata, os.path.join(outputdir, 'blendermesh.jmsh'))

        if self.endstep == '5':
            bpy.ops.blender2mesh.invoke_saveas('INVOKE_DEFAULT')

        # at this point, all mesh objects are saved to a jmesh file under work-dir as blendermesh.json
        if self.endstep < '6':
            return

        try:
            if bpy.context.scene.blender_photonics.backend == "octave":
                import oct2py as op
                oc = op.Oct2Py()
            else:
                import matlab.engine as op
                oc = op.start_matlab()
        except ImportError:
            raise ImportError(
                'To run this feature, you must install the oct2py or matlab.engine Python modulem first, based on '
                'your choice of the backend')

        oc.addpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'script'))

        oc.feval('blender2mesh', os.path.join(outputdir, 'blendermesh.jmsh'), nout=0)

        # import volume mesh to blender(just for user to check the result)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        if not self.onlysurf:
            outputmesh = jd.load(os.path.join(outputdir, 'volumemesh.jmsh'))
            LoadTetMesh(outputmesh, 'Iso2Mesh')
            bpy.context.view_layer.objects.active = bpy.data.objects['Iso2Mesh']
        else:
            regiondata = jd.load(os.path.join(outputdir, 'regionmesh.jmsh'))
            if len(regiondata.keys()) > 0:
                LoadReginalMesh(regiondata, 'region_')
                bpy.context.view_layer.objects.active = bpy.data.objects['region_1']

        bpy.context.space_data.shading.type = 'WIREFRAME'

        # at this point, if successful, iso2mesh generated mesh objects are imported into blender
        if self.endstep < '7':
            return

        ShowMessageBox(
            "Mesh generation is complete. The combined tetrahedral mesh is imported for inspection. To set optical "
            "properties for each region, please click 'Load mesh and setup simulation'",
            "BlenderPhotonics")

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
        global G_MAXVOL, G_KEEPRATIO, G_MERGETOL, G_DOREPAIR, G_ONLYSURF, G_CONVTRI, G_TETGENOPT, G_ENDSTEP
        self.layout.operator("object.dialog_operator")


# This operator will open Blender's file chooser when invoked
# and store the selected filepath in self.filepath and print it
# to the console using window_manager.fileselect_add()
class BLENDER2MESH_OT_invoke_saveas(bpy.types.Operator):
    bl_idname = "blender2mesh.invoke_saveas"
    bl_label = "Export scene in a JMesh/JSON universal exchange file"

    filepath: bpy.props.StringProperty(default='', subtype='DIR_PATH')

    def execute(self, context):
        print(self.filepath)
        if not (self.filepath == ""):
            if os.name == 'nt':
                os.popen("copy '" + os.path.join(GetBPWorkFolder(), 'blendermesh.jmsh') + "' '" + self.filepath + "'")
            else:
                os.popen("cp '" + os.path.join(GetBPWorkFolder(), 'blendermesh.jmsh') + "' '" + self.filepath + "'")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


register_class(BLENDER2MESH_OT_invoke_saveas)
