import bpy
import oct2py as op
import numpy as np
import scipy.io
import os

class import_volum_mesh(bpy.types.Operator):
    bl_label = 'Import Tetrahedral mesh'
    bl_description = "This botton can import tetrahedral mesh, please give the optical parameter to each region. Light should be in the model, otherwise, mmc will change the light source location."
    bl_idname = 'a_test.import_volum_mesh'
    
    def funivm(self):
        # clear all object
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        
        # folder path for importing .stl files
        in_dir_ply = (bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/Model/stlfile')
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
            obj["mu_a"] = 0.1
            obj["mu_s"] = 0.1
            obj["n"] = 1.37
            obj["g"] = 0.89

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
        obj["Type"] = 1 # pencil:'1'  disk:'2'

    def execute(self, context):
        print("begin to Import Region Mesh")
        self.funivm()
        return {"FINISHED"}
