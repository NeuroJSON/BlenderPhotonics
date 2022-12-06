"""NII2Mesh - converting a 3-D volumetric image (stored in NIfTI/JNIfTI/.mat file) to tetrahedral mesh

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

G_MAXVOL = 100
G_RADBOUND = 10
G_DISTBOUND = 1.0
G_ISOVALUE = 0.5
G_IMAGETYPE = "multi-label"
G_METHOD = "auto"


class nii2mesh(bpy.types.Operator):
    bl_label = 'Convert 3-D image file to mesh'
    bl_description = "Click this button to convert a 3D volume stored in JNIfTI (.jnii/.bnii, " \
                     "see http://neurojson.org) or NIfTI (.nii/.nii.gz) or .mat file to a mesh "
    bl_idname = 'blenderphotonics.creatregion'

    # create an interface to set user's model parameter.

    bl_options = {"REGISTER", "UNDO"}

    maxvol: bpy.props.FloatProperty(default=G_MAXVOL, name="Maximum tetrahedron volume")
    radbound: bpy.props.FloatProperty(default=G_RADBOUND, name="Surface triangle maximum diameter")
    distbound: bpy.props.FloatProperty(default=G_DISTBOUND, name="Maximum deviation from true boundary")
    isovalue: bpy.props.FloatProperty(default=G_ISOVALUE, name="Isovalue to create surface")
    imagetype: bpy.props.EnumProperty(name="Volume type", items=[('multi-label', 'multi-label', 'multi-label'),
                                                                 ('binary', 'binary', 'binary'),
                                                                 ('grayscale', 'grayscale', 'grayscale')])
    method: bpy.props.EnumProperty(name="Mesh extraction method",
                                   items=[('auto', 'auto', 'auto'), ('cgalmesh', 'cgalmesh', 'cgalmesh'),
                                          ('cgalsurf', 'cgalsurf', 'cgalsurf'), ('simplify', 'simplify', 'simplify')])

    def vol2mesh(self):
        # Remove last .jmsh file
        outputdir = GetBPWorkFolder()
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)
        if os.path.exists(os.path.join(outputdir, 'regionmesh.jmsh')):
            os.remove(os.path.join(outputdir, 'regionmesh.jmsh'))
        if os.path.exists(os.path.join(outputdir, 'volumemesh.jmsh')):
            os.remove(os.path.join(outputdir, 'volumemesh.jmsh'))

        # nii to mesh
        niipath = bpy.context.scene.blender_photonics.path
        print(niipath)
        if len(niipath) == 0:
            return
        jd.save({'niipath': niipath, 'maxvol': self.maxvol, 'radbound': self.radbound, 'distbound': self.distbound,
                 'isovalue': self.isovalue, 'imagetype': self.imagetype, 'method': self.method},
                os.path.join(outputdir, 'niipath.json'))

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
                'To run this feature, you must install the `oct2py` or `matlab.engine` Python module first, '
                'based on your choice of the backend')

        oc.addpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'script'))
        try:
            oc.feval('nii2mesh', os.path.join(outputdir, 'niipath.json'), nargout=0)
        except OcError1 as e:
            if 'too many outputs' in e.args[0]:
                oc.feval('nii2mesh', os.path.join(outputdir, 'niipath.json'), nout=0)
            else:
                raise

        # import volum mesh to blender(just for user to check the result)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        regiondata = jd.load(os.path.join(outputdir, 'regionmesh.jmsh'))
        regiondata = JMeshFallback(regiondata)
        n = len(regiondata.keys()) - 1

        # To import mesh.ply in batches
        for i in range(n):
            surfkey = 'MeshTri3' if n == 1 else f'MeshTri3({i + 1})'
            if not isinstance(regiondata[surfkey], np.ndarray):
                regiondata[surfkey] = np.asarray(regiondata[surfkey], dtype=np.uint32)
            regiondata[surfkey] -= 1
            AddMeshFromNodeFace(regiondata['MeshVertex3'], regiondata[surfkey].tolist(), 'region_' + str(i + 1))

        bpy.context.space_data.shading.type = 'WIREFRAME'

        ShowMessageBox(
            "Mesh generation is complete. The combined tetrahedral mesh is imported for inspection. To set optical "
            "properties for each region, please click 'Load mesh and setup simulation'",
            "BlenderPhotonics")

    def execute(self, context):
        self.vol2mesh()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


#
#   Dialog to set meshing properties
#
class setmeshingprop(bpy.types.Panel):
    bl_label = "Mesh extraction setting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global G_MAXVOL, G_RADBOUND, G_DISTBOUND, G_IMAGETYPE, G_METHOD
        self.layout.operator("object.dialog_operator")
