"""RunMMC - launch mesh-based Monte Carlo (MMC) simulations using domain configured in Blender

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
from .utils import *

G_NPHOTON = 10000
G_TEND = 5e-9
G_TSTEP = 5e-9
G_METHOD = "elem"
G_OUTPUTTYPE = "flux"
G_ISREFLECT = True
G_ISNORMALIZED = True
G_BASISORDER = 1
G_DEBUGLEVEL = "TP"
G_GPUID = "1"


class runmmc(bpy.types.Operator):
    bl_label = 'Run MMC photon simulation'
    bl_description = "Run mesh-based Monte Carlo simulation"
    bl_idname = 'blenderphotonics.runmmc'

    # create an interface to set user's model parameter.

    bl_options = {"REGISTER", "UNDO"}

    nphoton: bpy.props.FloatProperty(default=G_NPHOTON, name="Photon number")
    tend: bpy.props.FloatProperty(default=G_TEND, name="Time gate width (s)")
    tstep: bpy.props.FloatProperty(default=G_TSTEP, name="Time gate step (s)")
    isreflect: bpy.props.BoolProperty(default=G_ISREFLECT, name="Do reflection")
    isnormalized: bpy.props.BoolProperty(default=G_ISNORMALIZED, name="Normalize output")
    basisorder: bpy.props.IntProperty(default=G_BASISORDER, step=1, name="Basis order (0 or 1)")
    method: bpy.props.EnumProperty(default=G_METHOD, name="Raytracer (use elem)",
                                   items=[('elem', 'elem: Saving weight on elements', 'Saving weight on elements'),
                                          ('grid', 'grid: Dual-grid MMC (not supported)', 'Dual-grid MMC')])
    outputtype: bpy.props.EnumProperty(default=G_OUTPUTTYPE, name="Output quantity",
                                       items=[('flux', 'flux= fluence rate', 'fluence rate (J/mm^2/s)'),
                                              ('fluence', 'fluence: fluence (J/mm^2)', 'fluence in J/mm^2'),
                                              ('energy', 'energy: energy density J/mm^3', 'energy density J/mm^3')])
    gpuid: bpy.props.StringProperty(default=G_GPUID, name="GPU ID (01 mask,-1=CPU)")
    debuglevel: bpy.props.StringProperty(default=G_DEBUGLEVEL, name="Debug flag [MCBWDIOXATRPE]")

    def preparemmc(self):
        # save optical parameters and source source information
        parameters = []  # mu_a, mu_s, n, g
        cfg = []  # location, direction, photon number, Type,

        for obj in bpy.data.objects[0:-1]:
            if not ("mua" in obj):
                continue
            parameters.append([obj["mua"], obj["mus"], obj["g"], obj["n"]])

        obj = bpy.data.objects['source']
        location = np.array(obj.location).tolist()
        bpy.context.object.rotation_mode = 'QUATERNION'
        direction = np.array(bpy.context.object.rotation_quaternion).tolist()
        srcparam1 = [val for val in obj['srcparam1']]
        srcparam2 = [val for val in obj['srcparam2']]
        cfg = {'srctype': obj['srctype'], 'srcpos': location, 'srcdir': direction, 'srcparam1': srcparam1,
               'srcparam2': srcparam2, 'nphoton': self.nphoton, 'unitinmm': obj['unitinmm'],
               'tend': self.tend, 'tstep': self.tstep, 'isreflect': self.isreflect, 'isnormalized': self.isnormalized,
               'method': self.method, 'outputtype': self.outputtype, 'basisorder': self.basisorder,
               'debuglevel': self.debuglevel, 'gpuid': self.gpuid}
        print(obj['srctype'])
        outputdir = GetBPWorkFolder()
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)

        # Save MMC information
        jd.save({'prop': parameters, 'cfg': cfg}, os.path.join(outputdir, 'mmcinfo.json'))

        # run MMC
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
                'To run this feature, you must install the oct2py or matlab.engine Python modules first, based on '
                'your choice of the backend')

        oc.addpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'script'))

        try:
            oc.feval('blendermmc', os.path.join(outputdir, 'mmcinfo.json'), os.path.join(outputdir, 'meshdata.mat'),
                     nargout=0)
        except OcError1 as e:
            if 'too many outputs' in e.args[0]:
                oc.feval('blendermmc', os.path.join(outputdir, 'mmcinfo.json'), os.path.join(outputdir, 'meshdata.mat'),
                         nout=0)
            else:
                raise

        # remove all object and import all region as one object
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        outputmesh = jd.load(os.path.join(outputdir, 'volumemesh.jmsh'))
        outputmesh = JMeshFallback(outputmesh)
        if not isinstance(outputmesh['MeshTri3'], np.ndarray):
            outputmesh['MeshTri3'] = np.asarray(outputmesh['MeshTri3'], dtype=np.uint32)
        outputmesh['MeshTri3'] -= 1
        AddMeshFromNodeFace(outputmesh['MeshVertex3'], outputmesh['MeshTri3'].tolist(), "Iso2Mesh")

        # add color to blender model
        obj = bpy.data.objects['Iso2Mesh']
        mmcoutput = jd.load(os.path.join(outputdir, 'mmcoutput.json'))
        mmcoutput['logflux'] = np.asarray(mmcoutput['logflux'], dtype='float32')

        colorbit = 10
        colorkind = 2 ** colorbit - 1
        weight_data = normalize(mmcoutput['logflux'])
        weight_data_test = np.rint(weight_data * colorkind)

        new_vertex_group = obj.vertex_groups.new(name='weight')
        for i in range(colorkind + 1):
            ind = np.array(np.where(weight_data_test == i)).tolist()
            new_vertex_group.add(ind[0], i / colorkind, 'ADD')

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

        bpy.context.space_data.shading.type = 'SOLID'

        print('Finshed!, Please change intereaction mode to Weight Paint to see result!')
        print(
            '''If you prefer a perspective effect，please go to edit mode and make sure shading 'Vertex Group Weight' 
            is on.''')

    def execute(self, context):
        print("Begin to run MMC source transport simulation ...")
        self.preparemmc()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


#
#   Dialog to set meshing properties
#
class setmmcprop(bpy.types.Panel):
    bl_label = "MMC Simulation Setting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global G_NPHOTON, G_TEND, G_TSTEP, G_METHOD, G_OUTPUTTYPE, G_ISREFLECT, G_ISNORMALIZED, G_BASISORDER, G_DEBUGLEVEL, G_GPUID
        self.layout.operator("object.dialog_operator")
