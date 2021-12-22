import bpy
import oct2py as op
import numpy as np
import scipy.io
import os
import tempfile

class mesh2scene(bpy.types.Operator):
    bl_label = 'Load Mesh to Scene'
    bl_description = 'Import mesh to Blender. If one needs to run MMC photon simulations, please remember to set the optical properties to each region'
    bl_idname = 'blenderphotonics.meshtoscene'
    
    def importmesh(self):
        # clear all object
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        
        # folder path for importing .stl files
        in_dir_ply = tempfile.gettempdir()+'/iso2mesh-'+os.environ.get('USER')+'/blenderphotonics';
        lst_ply = os.listdir(in_dir_ply)

        # Filter file list by valid file types.
        candidates = []
        candidates_name = []
        c=0
        for item in lst_ply:
            fileName, fileExtension = os.path.splitext(lst_ply[c])
            if fileExtension == ".stl":
                candidates.append(item)
                candidates_name.append(fileName)
            c=c+1

        file = [{"name":i} for i in candidates]
        n = len(file)
        print(n)

        # To import mesh.ply in batches
        for i in range (0,n):
            bpy.ops.import_mesh.stl(filepath=candidates[i], files=[file[i]], directory=in_dir_ply, filter_glob="*.stl")


        ## add properties
        for obj in bpy.data.objects:
            obj["mu_a"] = 0.01
            obj["mu_s"] = 1
            obj["g"] = 0.0
            obj["n"] = 1.37

        ## add light
        light_data = bpy.data.lights.new(name="light", type='SPOT')
        light_object = bpy.data.objects.new(name="light", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object
        light_object.location = (0, 0, 5)
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()

        ## add cfg option
        obj = bpy.data.objects['light']
        obj["nphoton"] = 100
        obj["unitinmm"] = 1.0
        obj["srctype"] = 1 # pencil:'1'  disk:'2'

    def execute(self, context):
        print("begin to import region mesh")
        self.importmesh()
        return {"FINISHED"}
