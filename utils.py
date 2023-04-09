"""BlenderPhotonics Utilities/Helper Functions

* Authors: (c) 2021-2022 Qianqian Fang <q.fang at neu.edu>
* License: GNU General Public License V3 or later (GPLv3)
* Website: http://mcx.space/bp

To cite this work, please use the below information

@article{BlenderPhotonics2022,
  author = {Yuxuan Zhang and Qianqian Fang},
  title = {{BlenderPhotonics: an integrated open-source software environment for three-dimensional meshing and photon
   simulations in complex tissues}},
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
import numpy as np

from bpy.types import Object as BlenderObject
from getpass import getuser
from tempfile import gettempdir

from typing import Any, Iterable


def show_message_box(message: str = "", title: str = "Message Box", icon: str = "INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def get_node_face_from_object(obj: BlenderObject, istrimesh: bool = True):
    vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    # edges = [edge.vertices[:] for edge in obj.data.edges]
    faces = [(np.array(face.vertices[:]) + 1).tolist() for face in obj.data.polygons]
    v = np.array(vertices)
    try:
        f = np.array(faces)
        return {"MeshVertex3": v, "MeshTri3": f}
    except ValueError:
        f = faces
    return {"_DataInfo_": {"BlenderObjectName", obj.name}, "MeshVertex3": v, "MeshPoly": f}


def add_mesh_from_node_face(node: Iterable, face: Iterable, name: str):
    # Create mesh and related object
    my_mesh = bpy.data.meshes.new(name)
    my_obj = bpy.data.objects.new(name, my_mesh)

    # Set object location in 3D space
    my_obj.location = bpy.context.scene.cursor.location

    # make collection
    root_coll = bpy.context.scene.collection.children.get("Collection")

    # Link object to the scene collection
    root_coll.objects.link(my_obj)

    # Create object using blender function
    my_mesh.from_pydata(node, [], face)
    my_mesh.update(calc_edges=True)


def get_bp_work_folder():
    return os.path.join(gettempdir(), 'iso2mesh-', getuser(), 'blenderphotonics')


def load_regional_mesh(mesh_data, name: str):
    # To import mesh.ply in batches
    bbx = {'min': np.array([np.inf, np.inf, np.inf]), 'max': np.array([-np.inf, -np.inf, -np.inf])}
    if len(mesh_data.keys()) == 2:
        surf_keys = ['MeshTri3']
    else:
        surf_keys = [f'MeshTri3({i + 1})' for i, _ in enumerate(mesh_data.keys())]

    for i, surf_key in enumerate(surf_keys):
        if not isinstance(mesh_data[surf_key], np.ndarray):
            mesh_data[surf_key] = np.asarray(mesh_data[surf_key], dtype=np.uint32)
        mesh_data[surf_key] -= 1
        bbx['min'] = np.amin(np.vstack((bbx['min'], np.amin(mesh_data['MeshVertex3'], axis=0))), axis=0)
        bbx['max'] = np.amax(np.vstack((bbx['max'], np.amax(mesh_data['MeshVertex3'], axis=0))), axis=0)
        add_mesh_from_node_face(mesh_data['MeshVertex3'], mesh_data[surf_key].tolist(), f'{name}{i + 1}')
    print(bbx)
    return bbx


def load_tet_mesh(mesh_data, name):
    if not isinstance(mesh_data['MeshTri3'], np.ndarray):
        mesh_data['MeshTri3'] = np.asarray(mesh_data['MeshTri3'], dtype=np.uint32)
    mesh_data['MeshTri3'] -= 1
    add_mesh_from_node_face(mesh_data['MeshVertex3'], mesh_data['MeshTri3'].tolist(), name)


def jmesh_fallback(mesh_obj):
    if ('MeshSurf' in mesh_obj) and (not ('MeshTri3' in mesh_obj)):
        mesh_obj['MeshTri3'] = mesh_obj.pop('MeshSurf')
    if ('MeshNode' in mesh_obj) and (not ('MeshVertex3' in mesh_obj)):
        mesh_obj['MeshVertex3'] = mesh_obj.pop('MeshNode')
    return mesh_obj


def normalize(x: Iterable, minimum: Any = None, maximum: Any = None, inplace: bool = False):
    if minimum is None:
        minimum = np.min(x)
    if maximum is None:
        maximum = np.max(x)
    if not inplace:
        try:
            return (x - minimum) / (maximum - minimum)
        except TypeError:
            tmp_x = np.array(x)
            return (tmp_x - minimum) / (maximum - minimum)
    try:
        x = (x - minimum) / (maximum - minimum)
    except TypeError:
        x = (np.array(x) - minimum) / (maximum - minimum)

    return x
