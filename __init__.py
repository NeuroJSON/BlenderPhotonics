bl_info = {
    "name": "BlenderPhotonics",
    "author": "(c) 2021 Yuxuan (Victor) Zhang, (c) 2021 Qianqian Fang",
    "version": (1, 0),  # min plug-in version
    "blender": (2, 82, 0),  # min blender version
    "location": "Layout，UI",
    "description": "An integrated 3D mesh generation and Monte Carlo photon transport simulation environment",
    "warning": "This plug-in requires the preinstallation of Iso2Mesh (http://iso2mesh.sf.net) and MMCLAB (http://mcx.space)",
    "doc_url": "https://github.com/COTILab/BlenderPhotonics",
    "tracker_url": "https://github.com/COTILab/BlenderPhotonics/issues",
    "category": "User Interface",
}
import bpy
from .ui import BlenderPhotonics_UI
from .blender2mesh import scene2mesh
from .mesh2blender import mesh2scene
from .runmmc import runmmc
from .niifile import niifile
from .nii2mesh import nii2mesh
from bpy.props import PointerProperty

def register():
    print("Registering BlenderPhotonics")
    bpy.utils.register_class(scene2mesh)
    bpy.utils.register_class(niifile)
    bpy.utils.register_class(nii2mesh)
    bpy.utils.register_class(mesh2scene)
    bpy.utils.register_class(runmmc)
    bpy.utils.register_class(BlenderPhotonics_UI)
    bpy.types.Scene.blender_photonics = PointerProperty(type=niifile)


def unregister():
    print("Unregistering BlenderPhotonics")
    bpy.utils.unregister_class(scene2mesh)
    bpy.utils.unregister_class(niifile)
    bpy.utils.unregister_class(nii2mesh)
    bpy.utils.unregister_class(mesh2scene)
    bpy.utils.unregister_class(runmmc)
    bpy.utils.unregister_class(BlenderPhotonics_UI)
    del bpy.types.Scene.blender_photonics
