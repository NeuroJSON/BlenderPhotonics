"""Blender2Surf - extracting, converting and processing Blender object surfaces

* Authors: (c) 2021-2022 Qianqian Fang <q.fang at neu.edu>
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
from bpy_extras.io_utils import ImportHelper
import numpy as np
import jdata as jd
import os
from bpy.utils import register_class, unregister_class
from .utils import *

G_ACTION = 'repair'
G_ACTIONPARAM = 1.0
G_CONVTRI = True
ENUM_ACTION = [
    ('import', 'Import surface mesh from file', 'Import surface mesh from JMesh/STL/OFF/SMF/ASC/MEDIT/GTS to Blender'),
    ('export', 'Export selected to JSON/JMesh', 'Export selected objects to JSON/JMesh exchange file'),
    ('boolean-resolve', 'Boolean-resolve: Two meshes slice each other',
     'Output both objects, with each surface intersected by the other'),
    (
        'boolean-first', 'Boolean-first: 1st mesh sliced by the 2nd',
        'Return the 1st object but sliced by the 2nd object'),
    ('boolean-second', 'Boolean-second: 2nd mesh sliced by the 1st',
     'Return the 2nd object but sliced by the 1st object'),
    ('boolean-diff', 'Boolean-diff: 1st mesh subtract 2nd', 'Return the 1st object subtracted by the 2nd'),
    ('boolean-and', 'Boolean-and: Space in both objects', 'Return the surface of the overlapping region'),
    ('boolean-or', 'Boolean-or: Space for joint/union space', 'Return the outer surface of the merged object'),
    ('boolean-decouple', 'Boolean-decouple: Decouple two shell meshes',
     'Insert a small gap between two touching objects'),
    ('simplify', 'Surface simplification', 'Simplifing a surface by decimating edges'),
    ('remesh', 'Remesh surface', 'Remesh surface and remove badly shaped triangles'),
    ('smooth', 'Smooth selected objects', 'Smooth selected mesh object'),
    ('reorient', 'Reorient all triangles', 'Reorient all triangles in counter-clockwise direction'),
    ('repair', 'Fix self-intersection and holes', 'Fix self-intersection and fill holes of a closed object')]


class object2surf(bpy.types.Operator):
    bl_label = 'Process selected object surfaces'
    bl_description = "Create surface meshes from selected objects (smoothing, refine, Boolean, repairing, " \
                     "simplification, ...) "
    bl_idname = 'blenderphotonics.blender2surf'

    # create an interface to set user's model parameter.

    bl_options = {"REGISTER", "UNDO"}

    action: bpy.props.EnumProperty(default=G_ACTION, name="Operation", items=ENUM_ACTION)
    actionparam: bpy.props.FloatProperty(default=G_ACTIONPARAM, name="Operation parameter")
    convtri: bpy.props.BoolProperty(default=G_CONVTRI, name="Convert to triangular mesh first")

    @classmethod
    def description(cls, context, properties):
        return [desc for idx, _, desc in ENUM_ACTION if idx == properties.action][0]

    def func(self):
        outputdir = get_bp_work_folder()
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)

        if os.path.exists(os.path.join(outputdir, 'surfacemesh.jmsh')):
            os.remove(os.path.join(outputdir, 'surfacemesh.jmsh'))

        if len(bpy.context.selected_objects) < 1:
            show_message_box("Must select at least one object (for Boolean operations, select two)", "BlenderPhotonics")
            return

        # remove camera and light objects
        for ob in bpy.context.selected_objects:
            print(ob.type)
            if ob.type in ('CAMERA', 'LIGHT', 'EMPTY', 'LAMP', 'SPEAKER'):
                ob.select_set(False)

        bpy.ops.object.convert(target='MESH')

        bpy.ops.object.mode_set(mode='EDIT')
        if self.convtri:
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

        if len(bpy.context.selected_objects) < 1:
            show_message_box("No mesh-like object was selected, skip", "BlenderPhotonics")
            return

        bpy.ops.object.mode_set(mode='OBJECT')

        surfdata = {'_DataInfo_': {'JMeshVersion': '0.5',
                                   'Comment': 'Object surface mesh created by BlenderPhotonics ('
                                              'http://mcx.space/BlenderPhotonics)'},
                    'MeshGroup': []}
        for ob in bpy.context.selected_objects:
            objsurf = get_node_face_from_object(ob, self.convtri)
            surfdata['MeshGroup'].append(objsurf)

        surfdata['param'] = {'action': self.action, 'level': self.actionparam}

        jd.save(surfdata, os.path.join(outputdir, 'blendersurf.jmsh'))

        # at this point, objects are converted to mesh if possible
        if self.action == 'export':
            bpy.ops.object2surf.invoke_export('INVOKE_DEFAULT')
            return

        try:
            if bpy.context.scene.blender_photonics.backend == "octave":
                import oct2py as op
                from oct2py.utils import Oct2PyError as OcError1
                OcError2 = OcError1
                oc = op.Oct2Py()
            else:
                import matlab.engine as op
                from matlab.engine import MatlabExecutionError as OcError1, RejectedExecutionError as OcError2
                oc = op.start_matlab()
        except ImportError:
            raise ImportError(
                'To run this feature, you must install the oct2py or matlab.engine Python modulem first, based on '
                'your choice of the backend')

        oc.addpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'script'))

        try:
            oc.feval('blender2surf', os.path.join(outputdir, 'blendersurf.jmsh'), nargout=0)
        except OcError1 as e:
            if 'too many outputs' in e.args[0]:
                oc.feval('blender2surf', os.path.join(outputdir, 'blendersurf.jmsh'), nout=0)
            else:
                raise

        # import volum mesh to blender(just for user to check the result)
        if len(bpy.context.selected_objects) >= 1:
            bpy.ops.object.delete()

        surfdata = jd.load(os.path.join(outputdir, 'surfacemesh.jmsh'))
        idx = 1
        if len(surfdata['MeshGroup']) > 0:
            ob = surfdata['MeshGroup']
            objname = 'surf_' + str(idx)
            if 'MeshVertex3' in ob:
                if ('_DataInfo_' in ob) and ('BlenderObjectName' in ob['_DataInfo_']):
                    objname = ob['_DataInfo_']['BlenderObjectName']
                add_mesh_from_node_face(ob['MeshVertex3'], (np.array(ob['MeshTri3']) - 1).tolist(), objname)
                bpy.context.view_layer.objects.active = bpy.data.objects[objname]
            else:
                for ob in surfdata['MeshGroup']:
                    objname = 'surf_' + str(idx)
                    if ('_DataInfo_' in ob) and ('BlenderObjectName' in ob['_DataInfo_']):
                        objname = ob['_DataInfo_']['BlenderObjectName']
                    add_mesh_from_node_face(ob['MeshVertex3'], (np.array(ob['MeshTri3']) - 1).tolist(), objname)
                    bpy.context.view_layer.objects.active = bpy.data.objects[objname]
                    idx += 1

        bpy.context.space_data.shading.type = 'WIREFRAME'

        show_message_box("Mesh generation is complete. The combined surface mesh is imported for inspection.",
                       "BlenderPhotonics")

    def execute(self, context):
        print("begin to process object surface mesh")
        self.func()
        return {"FINISHED"}

    def invoke(self, context, event):
        if not self.action == 'import':
            return context.window_manager.invoke_props_dialog(self)
        else:
            return bpy.ops.object2surf.invoke_import('INVOKE_DEFAULT')


#
#   Dialog to set meshing properties
#
class setmeshingprop(bpy.types.Panel):
    bl_label = "Object surface mesh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global G_ACTION, G_ACTIONPARAM, G_CONVTRI
        self.layout.operator("object.dialog_operator")


# This operator will open Blender's file chooser when invoked
# and store the selected filepath in self.filepath and print it
# to the console using window_manager.fileselect_add()
class OBJECT2SURF_OT_invoke_export(bpy.types.Operator):
    bl_idname = "object2surf.invoke_export"
    bl_label = "Export to JMesh"
    bl_description = "Export mesh in the JSON/JMesh format"

    filepath: bpy.props.StringProperty(default='', subtype='DIR_PATH')

    def execute(self, context):
        print(self.filepath)
        if not (self.filepath == ""):
            if os.name == 'nt':
                os.popen("copy '" + os.path.join(get_bp_work_folder(), 'blendersurf.jmsh') + "' '" + self.filepath + "'")
            else:
                os.popen("cp '" + os.path.join(get_bp_work_folder(), 'blendersurf.jmsh') + "' '" + self.filepath + "'")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


register_class(OBJECT2SURF_OT_invoke_export)


# This operator will open Blender's file chooser when invoked
# and store the selected filepath in self.filepath and print it
# to the console using window_manager.fileselect_add()
class OBJECT2SURF_OT_invoke_import(bpy.types.Operator, ImportHelper):
    bl_idname = "object2surf.invoke_import"
    bl_label = "Import Mesh"
    bl_description = "Import triangular surfaces in .json,.jmsh,.bmsh,.off,.medit,.stl,.smf,.gts"

    filename_ext: bpy.props.StringProperty(default="*.json;*.jmsh;*.bmsh;*.off;*.medit;*.stl;*.smf;*.gts")
    filepath: bpy.props.StringProperty(default='', subtype='DIR_PATH')
    filter_glob: bpy.props.StringProperty(
        default="*.json;*.jmsh;*.bmsh;*.off;*.medit;*.stl;*.smf;*.gts",
        options={'HIDDEN'},
        description="Reading triangular surface mesh from *.json;*.jmsh;*.bmsh;*.off;*.medit;*.stl;*.smf;*.gts",
        maxlen=2048,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
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
        surfdata = oc.feval('surf2jmesh', self.filepath)
        add_mesh_from_node_face(surfdata['MeshVertex3'], (np.array(surfdata['MeshTri3']) - 1).tolist(), 'importedsurf')

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


register_class(OBJECT2SURF_OT_invoke_import)
