import bpy
import matlab.engine
import numpy as np
import jdata as jd
import os
import platform
from .utils import *


class runmmc(bpy.types.Operator):
    bl_label = 'Run MMC photon simulation'
    bl_description = "Run mesh-based Monte Carlo simulation"
    bl_idname = 'blenderphotonics.runmmc'

    def preparemmc(self):
        eng = matlab.engine.start_matlab()
        # eng.addpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'script'))
        ## save optical parameters and source source information
        parameters = []  # mu_a, mu_s, n, g
        light_source = []  # location, direction, photon number, Type,

        for obj in bpy.data.objects[0:-1]:
            if (not ("mua" in obj)):
                continue
            parameters.append([obj["mua"], obj["mus"], obj["g"], obj["n"]])

        obj = bpy.data.objects['source']
        location = np.array(obj.location).tolist();
        bpy.context.object.rotation_mode = 'QUATERNION'
        direction = np.array(bpy.context.object.rotation_quaternion).tolist();
        light_source = {'nphoton': obj["nphoton"], 'srctype': obj["srctype"], 'unitinmm': obj["unitinmm"]};

        outputdir = GetBPWorkFolder();
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)

        # Save MMC information
        jd.save({'prop': parameters, 'srcpos': location, 'srcdir': direction, 'cfg': light_source},
                os.path.join(outputdir, 'mmcinfo.json'));

        # run MMC
        system = platform.system()
        eng.blendermmc(nargout=0)
        
        # remove all object and import all region as one object
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        outputmesh = jd.load(os.path.join(outputdir, 'volumemesh.jmsh'));
        if (not isinstance(outputmesh['MeshSurf'], np.ndarray)):
            outputmesh['MeshSurf'] = np.asarray(outputmesh['MeshSurf'], dtype=np.uint32);
        outputmesh['MeshSurf'] -= 1
        AddMeshFromNodeFace(outputmesh['MeshNode'], outputmesh['MeshSurf'].tolist(), "Iso2Mesh");

        # add color to blender model
        obj = bpy.data.objects['Iso2Mesh']
        mmcoutput = jd.load(os.path.join(outputdir, 'mmcoutput.json'));
        mmcoutput['logflux'] = np.asarray(mmcoutput['logflux'], dtype='float32');

        def normalize(x, max, min):
            x = (x - min) / (max - min);
            return (x)

        weight_data = normalize(mmcoutput['logflux'], np.max(mmcoutput['logflux']), np.min(mmcoutput['logflux']))

        new_vertex_group = obj.vertex_groups.new(name='weight')
        vertexs = [vert.co for vert in obj.data.vertices]
        for vert in vertexs:
            ind = vertexs.index(vert)
            new_vertex_group.add([ind], weight_data[int(ind)], 'ADD')

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

        bpy.context.space_data.shading.type = 'SOLID'

        print('Finshed!, Please change intereaction mode to Weight Paint to see result!')
        print(
            '''If you prefer a perspective effect，please go to edit mode and make sure shading 'Vertex Group Weight' is on.''')

    def execute(self, context):
        print("Begin to run MMC source transport simulation ...")
        self.preparemmc()
        return {"FINISHED"}
