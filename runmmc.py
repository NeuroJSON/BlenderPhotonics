import bpy
import oct2py as op
import numpy as np
import scipy.io
import os
import platform
import tempfile

class runmmc(bpy.types.Operator):
    bl_label = 'Run MMC'
    bl_description = "Run mesh-based Monte Carlo simulation"
    bl_idname = 'blenderphotonics.runmmc'
    
    def preparemmc(self):
        oc = op.Oct2Py()
        oc.addpath(oc.genpath(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/script'))
        ## save optical parameters and light source information
        parameters = [] # mu_a, mu_s, n, g
        light_source = [] # location, direction, photon number, Type,

        for obj in bpy.data.objects[0:-1]:
            parameters.append(obj["mu_a"])
            parameters.append(obj["mu_s"])
            parameters.append(obj["g"])
            parameters.append(obj["n"])
        parameters = np.array(parameters)

        obj = bpy.data.objects['light']
        location =  np.array(obj.location)
        bpy.context.object.rotation_mode = 'QUATERNION'
        direction =  np.array(bpy.context.object.rotation_quaternion)
        light_source.append(obj["nphoton"])
        light_source.append(obj["srctype"])
        light_source.append(obj["unitinmm"])
        light_source = np.array(light_source)

        in_dir_ply = tempfile.gettempdir()+'/iso2mesh-'+os.environ.get('USER')+'/blenderphotonics';

        # Save MMC information
        scipy.io.savemat(in_dir_ply+'/mmcinfo.mat', mdict={'Optical':parameters, 'light_location':location,'light_direction':direction,'light_info':light_source})

        #run MMC
        oc = op.Oct2Py()
        system = platform.system()

        oc.run(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/script/blendermmc.m')
        
        #remove all object and import all region as one object
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        bpy.ops.import_mesh.stl(filepath=in_dir_ply+'/volumic_mesh.stl', files=[{'name': in_dir_ply+'/volumic_mesh.stl'}], directory=in_dir_ply, filter_glob="*.stl")
        
        #add color to blender model
        obj = bpy.context.view_layer.objects.active
        weight_data = scipy.io.loadmat(in_dir_ply+'/fluxlog.mat');
        order = scipy.io.loadmat(in_dir_ply+'/nodeorder.mat');

        def normalize(x,max,min):
            x=(x-min)/(max-min);
            return(x)

        weight_data = normalize(weight_data['fluxlog'], np.max(weight_data['fluxlog']),np.min(weight_data['fluxlog']))

        new_vertex_group = obj.vertex_groups.new(name='weight')
        vertexs = [vert.co for vert in obj.data.vertices]
        for vert in vertexs:
            ind=vertexs.index(vert)
            new_vertex_group.add([ind], weight_data[int(order['nodeorder'][ind])-1], 'ADD')
        bpy.ops.paint.weight_paint_toggle()

        print('Finshed!, Please change intereaction mode to Weight Paint to see result!')
        print('''If you prefer a perspective effect，please go to edit mode and make sure shading 'Vertex Group Weight' is on.''')

    def execute(self, context):
        print("Begin to run MMC light transport simulation ...")
        self.preparemmc()
        return {"FINISHED"}
