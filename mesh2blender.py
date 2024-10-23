"""Mesh2Blender - load regional mesh created by Iso2Mesh back to Blender

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


class mesh2scene(bpy.types.Operator):
    bl_label = "Load mesh and setup simulation"
    bl_description = "Import mesh to Blender. If one needs to run MMC photon simulations, please remember to set the optical properties to each region"
    bl_idname = "blenderphotonics.meshtoscene"

    def importmesh(self):
        # clear all object
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()

        # folder path for importing .jmsh files
        outputdir = GetBPWorkFolder()

        regiondata = jd.load(os.path.join(outputdir, "regionmesh.jmsh"))
        bbx = LoadReginalMesh(regiondata, "region_")

        ## add properties
        for obj in bpy.data.objects:
            obj["mua"] = 0.001
            obj["mus"] = 0.1
            obj["g"] = 0.0
            obj["n"] = 1.37

        ## add source
        light_data = bpy.data.lights.new(name="source", type="SPOT")
        light_object = bpy.data.objects.new(name="source", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object
        if (not np.any(np.isinf(bbx["min"]))) and (not np.any(np.isinf(bbx["max"]))):
            light_object.location = (
                (bbx["min"][0] + bbx["max"][0]) * 0.5,
                (bbx["min"][1] + bbx["max"][1]) * 0.5,
                bbx["max"][2] + 0.1 * (bbx["max"][2] - bbx["min"][2]),
            )
        else:
            light_object.location = (0, 0, 5)
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()

        # add cfg option
        obj = bpy.data.objects["source"]
        obj["nphoton"] = 10000
        obj["srctype"] = "pencil"
        obj["srcparam1"] = [0.0, 0.0, 0.0, 0.0]
        obj["srcparam2"] = [0.0, 0.0, 0.0, 0.0]
        obj["unitinmm"] = 1.0

    def execute(self, context):
        print("begin to import region mesh")
        self.importmesh()
        return {"FINISHED"}
