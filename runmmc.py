import bpy
import oct2py as op
import numpy as np
import scipy.io
import os
import platform

class runmmc(bpy.types.Operator):
    bl_label = 'Run MMC'
    bl_description = "Click this button to star MMC!"
    bl_idname = 'a_test.runmmc'
    
    def funrmc(self):
        os.chdir(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/Model')
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
        light_source.append(obj["Type"])
        light_source.append(obj["unitinmm"])
        light_source = np.array(light_source)

        # Save MMC information
        scipy.io.savemat('MMCinfo.mat', mdict={'Optical':parameters, 'light_location':location,'light_direction':direction,'light_info':light_source})

        #run MMC
        oc = op.Oct2Py()
        oc.addpath(oc.genpath(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/iso2mesh'))
        system = platform.system()
        if system == 'Windows':
            oc.addpath(oc.genpath(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/mmc/Windows/mmc'))
        elif system == 'Darwin':
            oc.addpath(oc.genpath(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/mmc/MacOS/mmc'))
        elif system == 'Linux':
            oc.addpath(oc.genpath(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/mmc/Linux/mmc'))
        oc.run(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/Model/runmmc.m')
        
        #remove all object and import all region as one object
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        bpy.ops.import_mesh.stl(filepath='volumic_mesh.stl', files=[{'name': 'volumic_mesh.stl'}], directory=(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/Model'), filter_glob="*.stl")
        
        #add color to blender model
        obj = bpy.context.view_layer.objects.active
        weight_data = scipy.io.loadmat(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/Model/fluxlog.mat');
        order = scipy.io.loadmat(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/Model/nodeorder.mat');

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
        print("begin to run Monte Carlo Simulation")
        self.funrmc()
        return {"FINISHED"}
