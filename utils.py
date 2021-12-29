import bpy
import os
import tempfile
import numpy as np

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
        return {'MeshNode':v, 'MeshSurf':f}
    except:
        f = faces
    return {'MeshNode':v, 'MeshPoly':f}

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
    for i in range (0,n):
        surfkey='MeshSurf('+str(i+1)+')'
        if(n==1):
            surfkey='MeshSurf'
        if (not isinstance(meshdata[surfkey], np.ndarray)):
            meshdata[surfkey]=np.asarray(meshdata[surfkey],dtype=np.uint32);
        meshdata[surfkey]-=1
        AddMeshFromNodeFace(meshdata['MeshNode'],meshdata[surfkey].tolist(),name+str(i+1));

def LoadTetMesh(meshdata,name):
        if (not isinstance(meshdata['MeshSurf'], np.ndarray)):
            meshdata['MeshSurf']=np.asarray(meshdata['MeshSurf'],dtype=np.uint32);
        meshdata['MeshSurf']-=1
        AddMeshFromNodeFace(meshdata['MeshNode'],meshdata['MeshSurf'].tolist(),name);