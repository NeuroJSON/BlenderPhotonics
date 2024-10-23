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
import os
import tempfile
import numpy as np


def ShowMessageBox(message="", title="Message Box", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def GetNodeFacefromObject(obj, istrimesh=True):
    verts = []
    for n in range(len(obj.data.vertices)):
        vert = obj.data.vertices[n].co
        v_global = obj.matrix_world @ vert
        verts.append(v_global)
    # edges = [edge.vertices[:] for edge in obj.data.edges]
    faces = [(np.array(face.vertices[:]) + 1).tolist() for face in obj.data.polygons]
    v = np.array(verts)
    try:
        f = np.array(faces)
        return {"MeshVertex3": v, "MeshTri3": f}
    except:
        f = faces
    return {
        "_DataInfo_": {"BlenderObjectName", obj.name},
        "MeshVertex3": v,
        "MeshPoly": f,
    }


def AddMeshFromNodeFace(node, face, name):

    # Create mesh and related object
    my_mesh = bpy.data.meshes.new(name)
    my_obj = bpy.data.objects.new(name, my_mesh)

    # Set object location in 3D space
    my_obj.location = bpy.context.scene.cursor.location

    # make collection
    rootcoll = bpy.context.scene.collection.children.get("Collection")

    # Link object to the scene collection
    rootcoll.objects.link(my_obj)

    # Create object using blender function
    my_mesh.from_pydata(node, [], face)
    my_mesh.update(calc_edges=True)


def GetBPWorkFolder():
    if os.name == "nt":
        return os.path.join(
            tempfile.gettempdir(),
            "iso2mesh-" + os.environ.get("UserName"),
            "blenderphotonics",
        )
    else:
        return os.path.join(
            tempfile.gettempdir(),
            "iso2mesh-" + os.environ.get("USER"),
            "blenderphotonics",
        )


def LoadReginalMesh(meshdata, name):
    n = len(meshdata.keys()) - 1

    # To import mesh.ply in batches
    bbx = {
        "min": np.array([np.inf, np.inf, np.inf]),
        "max": np.array([-np.inf, -np.inf, -np.inf]),
    }
    for i in range(0, n):
        surfkey = "MeshTri3(" + str(i + 1) + ")"
        if n == 1:
            surfkey = "MeshTri3"
        if not isinstance(meshdata[surfkey], np.ndarray):
            meshdata[surfkey] = np.asarray(meshdata[surfkey], dtype=np.uint32)
        meshdata[surfkey] -= 1
        bbx["min"] = np.amin(
            np.vstack((bbx["min"], np.amin(meshdata["MeshVertex3"], axis=0))),
            axis=0,
        )
        bbx["max"] = np.amax(
            np.vstack((bbx["max"], np.amax(meshdata["MeshVertex3"], axis=0))),
            axis=0,
        )
        AddMeshFromNodeFace(
            meshdata["MeshVertex3"],
            meshdata[surfkey].tolist(),
            name + str(i + 1),
        )
    print(bbx)
    return bbx


def LoadTetMesh(meshdata, name):
    if not isinstance(meshdata["MeshTri3"], np.ndarray):
        meshdata["MeshTri3"] = np.asarray(meshdata["MeshTri3"], dtype=np.uint32)
    meshdata["MeshTri3"] -= 1
    AddMeshFromNodeFace(meshdata["MeshVertex3"], meshdata["MeshTri3"].tolist(), name)


def JMeshFallback(meshobj):
    if ("MeshSurf" in meshobj) and (not ("MeshTri3" in meshobj)):
        meshobj["MeshTri3"] = meshobj.pop("MeshSurf")
    if ("MeshNode" in meshobj) and (not ("MeshVertex3" in meshobj)):
        meshobj["MeshVertex3"] = meshobj.pop("MeshNode")
    return meshobj
