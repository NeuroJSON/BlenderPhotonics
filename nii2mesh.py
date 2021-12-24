import bpy
import oct2py as op
import numpy as np
import scipy.io
import os
import tempfile

class nii2mesh(bpy.types.Operator):
    bl_label = 'Convert 3-D image file to mesh'
    bl_description = "Click this button to convert a 3D volume stored in JNIfTI (.jnii/.bnii, see http://neurojson.org) or NIfTI (.nii/.nii.gz) or .mat file to a mesh"
    bl_idname = 'blenderphotonics.creatregion'
    
    def preparenii(self):
        oc = op.Oct2Py()
        oc.addpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'script'))

        # Remove last .stl file
        outputdir = os.path.join(tempfile.gettempdir(),'iso2mesh-'+os.environ.get('USER'),'blenderphotonics');
        lst_ply = os.listdir(outputdir)
        c=0
        for item in lst_ply:
            fileName, fileExtension = os.path.splitext(lst_ply[c])
            if fileExtension == ".stl":
                os.remove(os.path.join(outputdir,item))
                print ("Delete File: " + os.path.join(outputdir,item))
            c=c+1
        
        # nii to mesh
        path = bpy.context.scene.blender_photonics.path
        if (len(path)==0):
            return
        scipy.io.savemat('niipath.mat', mdict={'path':path})

        oc.run(os.path.join(os.path.dirname(os.path.abspath(__file__)),'script','nii2mesh.m'))

        # import volum mesh to blender(just for user to check the result)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        # folder path for importing .stl files
        lst_ply = os.listdir(outputdir)

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
            bpy.ops.import_mesh.stl(filepath=candidates[i], files=[file[i]], directory=outputdir, filter_glob="*.stl")

        bpy.context.space_data.shading.type = 'WIREFRAME'

        ShowMessageBox("Mesh generation is complete. The combined tetrahedral mesh is imported for inspection. To set optical properties for each region, please click 'Load mesh and setup simulation'", "BlenderPhotonics")

    def execute(self, context):
        #print("Int ops--->funnii:")
        self.preparenii()
        return {"FINISHED"}
