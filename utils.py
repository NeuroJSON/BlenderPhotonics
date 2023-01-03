"""BlenderPhotonics Utilities/Helper Functions

* Authors: (c) 2021-2022 Qianqian Fang <q.fang at neu.edu>
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
import math
import os
import tempfile
import numpy as np
import pyopenvdb as vdb
import copy
import jdata as jd

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def GetNodeFacefromObject(obj, istrimesh=True):
    verts = []
    for n in range(len(obj.data.vertices)):
        vert = obj.data.vertices[n].co
        v_global = obj.matrix_world @ vert
        verts.append(v_global)
    #edges = [edge.vertices[:] for edge in obj.data.edges]
    faces = [(np.array(face.vertices[:])+1).tolist() for face in obj.data.polygons]
    v = np.array(verts)
    try:
        f = np.array(faces)
        return {'MeshVertex3':v, 'MeshTri3':f}
    except:
        f = faces
    return {'_DataInfo_':{'BlenderObjectName',obj.name},'MeshVertex3':v, 'MeshPoly':f}

def AddMeshFromNodeFace(node,face,name):

    # Create mesh and related object
    my_mesh=bpy.data.meshes.new(name)
    my_obj=bpy.data.objects.new(name,my_mesh)

    # Set object location in 3D space
    my_obj.location = bpy.context.scene.cursor.location 

    # make collection
    rootcoll=bpy.context.scene.collection.children.get("Collection")

    # Link object to the scene collection
    rootcoll.objects.link(my_obj)

    # Create object using blender function
    my_mesh.from_pydata(node,[],face)
    my_mesh.update(calc_edges=True)

def GetBPWorkFolder():
    if os.name == 'nt':
        return os.path.join(tempfile.gettempdir(),'iso2mesh-'+os.environ.get('UserName'),'blenderphotonics')
    else:
        return os.path.join(tempfile.gettempdir(),'iso2mesh-'+os.environ.get('USER'),'blenderphotonics')

def LoadReginalMesh(meshdata, name):
    n=len(meshdata.keys())-1

    # To import mesh.ply in batches
    bbx={'min': np.array([np.inf, np.inf, np.inf]), 'max': np.array([-np.inf, -np.inf, -np.inf])}
    for i in range (0,n):
        surfkey='MeshTri3('+str(i+1)+')'
        if(n==1):
            surfkey='MeshTri3'
        if (not isinstance(meshdata[surfkey], np.ndarray)):
            meshdata[surfkey]=np.asarray(meshdata[surfkey],dtype=np.uint32);
        meshdata[surfkey]-=1
        bbx['min']=np.amin(np.vstack((bbx['min'], np.amin(meshdata['MeshVertex3'],axis=0))), axis=0)
        bbx['max']=np.amax(np.vstack((bbx['max'], np.amax(meshdata['MeshVertex3'],axis=0))), axis=0)
        AddMeshFromNodeFace(meshdata['MeshVertex3'],meshdata[surfkey].tolist(),name+str(i+1))
    print(bbx)
    return bbx

def LoadTetMesh(meshdata,name):
        if (not isinstance(meshdata['MeshTri3'], np.ndarray)):
            meshdata['MeshTri3']=np.asarray(meshdata['MeshTri3'],dtype=np.uint32);
        meshdata['MeshTri3']-=1
        AddMeshFromNodeFace(meshdata['MeshVertex3'],meshdata['MeshTri3'].tolist(),name);

def JMeshFallback(meshobj):
        if('MeshSurf' in meshobj) and (not ('MeshTri3' in meshobj)):
            meshobj['MeshTri3']=meshobj.pop('MeshSurf')
        if('MeshNode' in meshobj) and (not ('MeshVertex3' in meshobj)):
            meshobj['MeshVertex3']=meshobj.pop('MeshNode')
        return meshobj

def normalize(x):
    x = (x - np.min(x)) / (np.max(x) - np.min(x))
    return x

def ConvertMat2Vdb(meshdata, name, path, mode):
    if (not isinstance(meshdata, np.ndarray)) or not meshdata.dtype==np.float32:
        meshdata = np.asarray(meshdata, dtype=np.float32)
    mesh = meshdata.transpose(2,1,0)
    #mesh = meshdata
    grid_list = []
    model = vdb.FloatGrid()
    if mode == 'result_view':
        mesh = normalize(mesh)
    model.copyFromArray(mesh)
    model.name = 'density'
    grid_list.append(model)
    if mode == 'model_view' :
        digit = int(math.log((int(mesh.max()+1-int(mesh.min()))), 10)+1)
        for index in range(int(mesh.min()), int(mesh.max()+1)):
            grid = vdb.FloatGrid()
            grid.name = str(int(index)+1).rjust(digit,'0')
            grid.copyFromArray(mesh == index)
            grid = copy.deepcopy(grid)
            grid_list.append(grid)
        filename = os.path.join(path, 'Iso2Mesh.vdb')
    elif mode == 'result_view':
        filename = os.path.join(path, 'MCX_result.vdb')
        digit = 1
    vdb.write(filename, grids=grid_list)
    return filename, len(grid_list)-1, digit

def LoadVolMesh(mesh_np, id, path, mode, colormap='jet'):
    if mode == 'model_view':
        filename, region_n, digit = ConvertMat2Vdb(mesh_np['image'], id, path, mode)
        try:
            bpy.data.materials["model_material"]
        except:
            AddMaterial(id="model_material", alpha=0.05, r_number=region_n, colormap_id=colormap)

    elif mode == 'result_view':
        filename, region_n, digit = ConvertMat2Vdb(mesh_np['fluxlog'], id, path, mode)
        try:
            bpy.data.materials["mcx_material"]
        except:
            AddMaterial(id="mcx_material", alpha=0.05, colormap_id=colormap)
    bpy.ops.object.volume_import(filepath=filename, align='WORLD')


    if mode == 'model_view':
        obj = bpy.data.objects['Iso2Mesh']
        for ind in range(region_n):
            obj.data['Optical_prop_'+str(ind+1).rjust(digit,'0')] = [0.001, 0.1, 0.0, 1.37]
        obj.data.materials.append(bpy.data.materials["model_material"])
    elif mode == 'result_view':
        obj = bpy.data.objects['MCX_result']
        obj.data.materials.append(bpy.data.materials["mcx_material"])

    obj.scale = [mesh_np['scale'][0, 0], mesh_np['scale'][1, 1], mesh_np['scale'][2, 2]]
    bpy.ops.transform.rotate(value=-math.pi/2, orient_axis='Y')
    bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                             orient_matrix_type='GLOBAL', constraint_axis=(False, False, True))
    bpy.ops.transform.translate(value=(mesh_np['scale'][0, 3], mesh_np['scale'][1, 3], mesh_np['scale'][2, 3]),
                                orient_axis_ortho='X', orient_type='GLOBAL',
                                orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)))

    bpy.context.scene.render.engine = 'CYCLES'
    try:
        bpy.context.scene.cycles.device = 'GPU'
    except:
        pass
    AdjestWorld()
    bpy.context.space_data.shading.type = 'RENDERED'


def AddMaterial(id, alpha, r_number=1, colormap_id='jet'):
    bpy.data.materials.new(name=id)
    color_assert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets','colormap_assest.json')
    colorlist = jd.load(color_assert_path)['colormap'][colormap_id]
    color = [(int(color_HEX,16), alpha) for color_HEX in colorlist]

    def to_blender_color(c):  # gamma correction
        c = min(max(0, c), 255) / 255
        return c / 12.92 if c < 0.04045 else math.pow((c + 0.055) / 1.055, 2.4)

    blend_color = [(
        to_blender_color(c[0] >> 16),
        to_blender_color(c[0] >> 8 & 0xff),
        to_blender_color(c[0] & 0xff),
        c[1]) for c in color]
    color_count = len(color)

    mat = bpy.data.materials[id]  # choose material name here
    mat.use_nodes = True

    tree = mat.node_tree
    nodes = tree.nodes
    mat.node_tree.nodes.clear()

    if id == "model_material":
        node1 = nodes.new(type='ShaderNodeVolumeInfo')
        node2 = nodes.new(type='ShaderNodeValToRGB')  # add color ramp node
        node3 = nodes.new(type='ShaderNodeVolumePrincipled')
        node4 = nodes.new(type='ShaderNodeOutputMaterial')
        node5 = nodes.new(type='ShaderNodeMapRange')
        tree.links.new(node1.outputs["Density"], node5.inputs["Value"])
        tree.links.new(node5.outputs["Result"], node2.inputs["Fac"])
        tree.links.new(node2.outputs["Color"], node3.inputs["Color"])
        tree.links.new(node2.outputs["Alpha"], node3.inputs["Density"])
        tree.links.new(node3.outputs[0], node4.inputs[1])
        tree.links.new(node2.outputs["Color"], node3.inputs["Emission Color"])
        tree.links.new(node5.outputs["Result"], node3.inputs["Emission Strength"])
        node5.inputs["From Max"].default_value = r_number

    elif id == "mcx_material":
        # add render material part nodes
        node1 = nodes.new(type='ShaderNodeVolumeInfo')
        node2 = nodes.new(type='ShaderNodeValToRGB')  # add color ramp node
        node3 = nodes.new(type='ShaderNodeVolumePrincipled')
        node4 = nodes.new(type='ShaderNodeOutputMaterial')
        node5 = nodes.new(type='ShaderNodeMath')
        node5.operation = 'MULTIPLY'
        node5.inputs[1].default_value = 1
        # link render material part
        tree.links.new(node1.outputs["Density"], node5.inputs[0])
        tree.links.new(node5.outputs["Value"], node2.inputs["Fac"])
        tree.links.new(node2.outputs["Color"], node3.inputs["Color"])
        tree.links.new(node2.outputs["Alpha"], node3.inputs["Density"])
        tree.links.new(node3.outputs[0], node4.inputs[1])
        tree.links.new(node2.outputs["Color"], node3.inputs["Emission Color"])
        tree.links.new(node5.outputs["Value"], node3.inputs["Emission Strength"])
        # add slice material part nodes
        node6 = nodes.new(type='ShaderNodeNewGeometry')
        node7 = nodes.new(type='ShaderNodeSeparateXYZ')
        node8 = nodes.new(type='ShaderNodeMapRange')
        node8.interpolation_type='STEPPED'
        node8.inputs[5].default_value=1
        # link render material part
        tree.links.new(node6.outputs["Position"], node7.inputs["Vector"])
        tree.links.new(node7.outputs["X"], node8.inputs["Value"])



    ramp = node2.color_ramp
    el = ramp.elements

    dis = 1 / (color_count - 1)
    x = dis
    for r in range(color_count - 2):
        el.new(x)
        x += dis

    for i, e in enumerate(el):
        e.color = blend_color[i]
    return

def AdjestWorld():
    ### add light source and world material ###
    mat = bpy.data.worlds['World']
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    node1 = nodes["Background"]
    node1.inputs["Color"].default_value=(0,0,0,1)
    return