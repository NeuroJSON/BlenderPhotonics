import bpy
import matlab.engine
import numpy as np
import jdata as jd
import os
from .utils import *

class mesh2scene(bpy.types.Operator):
    bl_label = 'Load mesh and setup simulation'
    bl_description = 'Import mesh to Blender. If one needs to run MMC photon simulations, please remember to set the optical properties to each region'
    bl_idname = 'blenderphotonics.meshtoscene'
    
    def importmesh(self):
        # clear all object
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # folder path for importing .jmsh files
        outputdir = GetBPWorkFolder();
        
        regiondata=jd.load(os.path.join(outputdir,'regionmesh.jmsh'));
        n=len(regiondata.keys())-1

        # To import mesh.ply in batches
        for i in range (0,n):
            surfkey='MeshSurf('+str(i+1)+')'
            if(n==1):
                surfkey='MeshSurf'
            if (not isinstance(regiondata[surfkey], np.ndarray)):
                regiondata[surfkey]=np.asarray(regiondata[surfkey],dtype=np.uint32);
            regiondata[surfkey]-=1
            AddMeshFromNodeFace(regiondata['MeshNode'],regiondata[surfkey].tolist(),'region_'+str(i+1));

        ## add properties
        for obj in bpy.data.objects:
            obj["mua"] = 0.001
            obj["mus"] = 0.1
            obj["g"] = 0.0
            obj["n"] = 1.37

        ## add source
        light_data = bpy.data.lights.new(name="source", type='SPOT')
        light_object = bpy.data.objects.new(name="source", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object
        light_object.location = (0, 0, 5)
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()

        ## add cfg option
        obj = bpy.data.objects['source']
        obj["nphoton"] = 10000
        obj["unitinmm"] = 1.0
        obj["srctype"] = 1 # pencil:'1'  disk:'2'

    def execute(self, context):
        print("begin to import region mesh")
        self.importmesh()
        return {"FINISHED"}
