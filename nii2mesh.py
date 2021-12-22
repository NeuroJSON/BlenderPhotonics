import bpy
import oct2py as op
import numpy as np
import scipy.io
import os
import tempfile

class nii2mesh(bpy.types.Operator):
    bl_label = 'Create Mesh from NIfTI'
    bl_description = "Click this button to get mesh from nii file"
    bl_idname = 'blenderphotonics.creatregion'
    
    def preparenii(self):
        oc.addpath(oc.genpath(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/script'))
        
        # Remove last .stl file
        in_dir_ply = tempfile.gettempdir()+'/iso2mesh-'+os.environ.get('USER')+'/blenderphotonics';
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
        path = bpy.context.scene.blenderphotonics.path
        scipy.io.savemat('niipath.mat', mdict={'path':path})
        oc.run(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/script/nii2mesh.m')
        
        # import volum mesh to blender(just for user to check the result)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        # folder path for importing .stl files
        lst_ply = os.listdir(in_dir_ply)

        # Filter file list by valid file types.
        candidates = []
        candidates_name = []
        c=0
        for item in lst_ply:
            fileName, fileExtension = os.path.splitext(lst_ply[c])
            if fileExtension == ".stl" and (not fileName.startswith('volumic_mesh')):
                candidates.append(item)
                candidates_name.append(fileName)
            c=c+1

        file = [{"name":i} for i in candidates]
        n = len(file)

        # To import mesh.ply in batches
        for i in range (0,n):
            bpy.ops.import_mesh.stl(filepath=candidates[i], files=[file[i]], directory=in_dir_ply, filter_glob="*.stl")

    def execute(self, context):
        #print("Int ops--->funnii:")
        self.preparenii()
        return {"FINISHED"}
