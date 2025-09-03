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
import os
from .utils import *
from .dependencies import safe_import, require_dependency

# Safe imports
jd = safe_import("jdata")

g_volmeshtype = "1"
enum_volmeshtype = [
    ("1", "Rasterization Mesh", "Run MCX"),
    ("2", "Tetrahedral Mesh", "Run MMC"),
]


class mesh2sceneTmesh(bpy.types.Operator):
    bl_label = "Load tetrahedral mesh and setup simulation"
    bl_description = "Import tetrahedral mesh to Blender for MMC photon simulations. Please remember to set the optical properties to each region"
    bl_idname = "blenderphotonics.tmeshtoscene"

    def importmesh(self):
        if not require_dependency("jdata", "mesh import operations"):
            return

        # folder path for importing .jmsh files
        outputdir = GetBPWorkFolder()
        # Load tetrahedral mesh, remove all objects and load region mesh
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)
        bpy.ops.outliner.orphans_purge(do_recursive=True)
        regiondata = jd.load(os.path.join(outputdir, "regionTmesh.jmsh"))
        LoadReginalMesh(regiondata, "region_")
        for obj in bpy.data.objects:
            obj["mua"] = 0.001
            obj["mus"] = 0.1
            obj["g"] = 0.0
            obj["n"] = 1.37

        ## add light source
        light_data = bpy.data.lights.new(name="Lightsource", type="SPOT")
        light_object = bpy.data.objects.new(name="Lightsource", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object
        light_object.location = (0, 0, 5)
        light_object.scale = (0.1, 0.1, 1)
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()

        # add cfg option
        obj = bpy.data.objects["Lightsource"]
        obj["nphoton"] = 10000
        obj["srctype"] = "pencil"
        obj["srcparam1"] = [0.0, 0.0, 0.0, 0.0]
        obj["srcparam2"] = [0.0, 0.0, 0.0, 0.0]
        obj["unitinmm"] = 1

    def execute(self, context):
        print("begin to set up tetrahedral mesh and light source")
        self.importmesh()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class mesh2sceneVmesh(bpy.types.Operator):
    bl_label = "Load voxel mesh and setup simulation"
    bl_description = "Import voxel mesh to Blender for MCX photon simulations. Please remember to set the optical properties to each region"
    bl_idname = "blenderphotonics.vmeshtoscene"

    def importmesh(self):
        if not require_dependency("jdata", "mesh import operations"):
            return

        # folder path for importing .jmsh files
        outputdir = GetBPWorkFolder()
        # Load voxel mesh, remove all objects and load region mesh
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)
        bpy.ops.outliner.orphans_purge(do_recursive=True)
        regiondata = jd.load(os.path.join(outputdir, "regionVmesh.jmsh"))
        LoadReginalMesh(regiondata, "region_")
        for obj in bpy.data.objects:
            obj["mua"] = 0.001
            obj["mus"] = 0.1
            obj["g"] = 0.0
            obj["n"] = 1.37

        ## add light source
        light_data = bpy.data.lights.new(name="Lightsource", type="SPOT")
        light_object = bpy.data.objects.new(name="Lightsource", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object
        light_object.location = (0, 0, 5)
        light_object.scale = (0.1, 0.1, 1)
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()

        # add cfg option
        obj = bpy.data.objects["Lightsource"]
        obj["nphoton"] = 10000
        obj["srctype"] = "pencil"
        obj["srcparam1"] = [0.0, 0.0, 0.0, 0.0]
        obj["srcparam2"] = [0.0, 0.0, 0.0, 0.0]
        obj["unitinmm"] = 1

    def execute(self, context):
        print("begin to set up voxel mesh and light source")
        self.importmesh()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
