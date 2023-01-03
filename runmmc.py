"""RunMMC - launch mesh-based Monte Carlo (MMC) simulations using domain configured in Blender

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
import jdata as jd
import os
from .utils import *

g_nphoton=10000
g_tend=5e-9
g_tstep=5e-9
g_method="elem"
g_outputtype="flux"
g_isreflect=True
g_isnormalized=True
g_basisorder=1
g_debuglevel="TP"
g_gpuid="1"
g_colormap ="jet"


class runmmc(bpy.types.Operator):
    bl_label = 'Run MMC photon simulation'
    bl_description = "Run mesh-based Monte Carlo simulation"
    bl_idname = 'blenderphotonics.runmmc'

    # creat a interface to set uesrs' model parameter.

    bl_options = {"REGISTER", "UNDO"}
    nphoton: bpy.props.FloatProperty(default=g_nphoton, name="Photon number")
    tend: bpy.props.FloatProperty(default=g_tend,name="Time gate width (s)")
    tstep: bpy.props.FloatProperty(default=g_tstep,name="Time gate step (s)")
    isreflect: bpy.props.BoolProperty(default=g_isreflect,name="Do reflection")
    isnormalized: bpy.props.BoolProperty(default=g_isnormalized,name="Normalize output")
    basisorder: bpy.props.IntProperty(default=g_basisorder,step=1,name="Basis order (0 or 1)")
    method: bpy.props.EnumProperty(default=g_method, name="Raytracer (use elem)", items = [('elem','elem: Saving weight on elements','Saving weight on elements'),('grid','grid: Dual-grid MMC (not supported)','Dual-grid MMC')])
    outputtype: bpy.props.EnumProperty(default=g_outputtype, name="Output quantity", items = [('flux','flux: fluence rate','fluence rate (J/mm^2/s)'),('fluence','fluence: fluence (J/mm^2)','fluence in J/mm^2'),('energy','energy: energy density J/mm^3','energy density J/mm^3')])
    gpuid: bpy.props.StringProperty(default=g_gpuid,name="GPU ID (01 mask,-1=CPU)")
    debuglevel: bpy.props.StringProperty(default=g_debuglevel,name="Debug flag [MCBWDIOXATRPE]")
    colormap: bpy.props.StringProperty(default=g_colormap, name="color scheme")

    def preparemmc(self):
        ## save optical parameters and source source information
        parameters = [] # mu_a, mu_s, n, g
        cfg = [] # location, direction, photon number, Type,
        obj = bpy.data.objects["Iso2Mesh"]

        for prop in obj.data.keys():
            parameters.append(obj.data[prop].to_list())

        obj = bpy.data.objects['source']
        location =  np.array(obj.location).tolist();
        bpy.context.object.rotation_mode = 'QUATERNION'
        direction =  np.array(bpy.context.object.rotation_quaternion).tolist();
        srcparam1=[val for val in obj['srcparam1']]
        srcparam2=[val for val in obj['srcparam2']]
        cfg={'srctype':obj['srctype'],'srcpos':location, 'srcdir':direction,'srcparam1':srcparam1,
            'srcparam2':srcparam2,'nphoton': self.nphoton, 'srctype':obj["srctype"], 'unitinmm': obj['unitinmm'],
            'tend':self.tend, 'tstep':self.tstep, 'isreflect':self.isreflect, 'isnormalized':self.isnormalized,
            'method':self.method, 'outputtype':self.outputtype,'basisorder':self.basisorder, 'debuglevel':self.debuglevel, 'gpuid':self.gpuid}
        print(obj['srctype'])
        outputdir = GetBPWorkFolder();
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)

        # Save MMC information
        jd.save({'prop':parameters,'cfg':cfg}, os.path.join(outputdir,'mmcinfo.json'));

        #run MMC
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

        oc.feval('blendermcx',os.path.join(outputdir,'mmcinfo.json'), os.path.join(outputdir,'ImageMesh.mat'), nargout=0)

        #remove all object and import all region as one object
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)
        bpy.ops.outliner.orphans_purge(do_recursive=True)

        outputmesh=oc.load(os.path.join(outputdir,'Mcx_result.mat'))
        LoadVolMesh(outputmesh,'MCX_result', outputdir, mode='result_view', colormap=self.colormap)

        print('Finshed!, Please change intereaction mode to Weight Paint to see result!')
        print('''If you prefer a perspective effect，please go to edit mode and make sure shading 'Vertex Group Weight' is on.''')

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
        global g_nphoton, g_tend, g_tstep, g_method,g_outputtype, g_isreflect, g_isnormalized, g_basisorder, g_debuglevel, g_gpuid
        self.layout.operator("object.dialog_operator")
