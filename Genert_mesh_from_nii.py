import bpy
import oct2py as op
import numpy as np
import scipy.io
import os

class niitomesh(bpy.types.Operator):
    bl_label = 'Genert_mesh_from_nii'
    bl_description = "Click this button to get mesh from nii file"
    bl_idname = 'a_test.niitomesh'
    
    def funnii(self):
        os.chdir(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/Model')
        
        # Remove last .stl file
        in_dir_ply = (bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/Model/stlfile')
        lst_ply = os.listdir(in_dir_ply)
        c=0
        for item in lst_ply:
            fileName, fileExtension = os.path.splitext(lst_ply[c])
            if fileExtension == ".stl":
                os.remove(os.path.join(in_dir_ply,item))
                print ("Delete File: " + os.path.join(in_dir_ply,item))
            c=c+1
        
        # nii to mesh
        oc = op.Oct2Py()
        path = bpy.context.scene.my_tool.my_path
        scipy.io.savemat('path.mat', mdict={'path':path})
        oc.run(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/Model/Nii_to_mesh.m')
        
        # import volum mesh to blender(just for user to check the result)
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

        # To import mesh.ply in batches
        for i in range (0,n):
            bpy.ops.import_mesh.stl(filepath=candidates[i], files=[file[i]], directory=in_dir_ply, filter_glob="*.stl")

    def execute(self, context):
        print("Int ops--->funnii:")
        self.funnii()
        return {"FINISHED"}
