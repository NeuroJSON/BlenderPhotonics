"""BlenderPhotonics - a Blender addon for 3-D mesh generation and Monte Carlo simulation

* Authors: (c) 2021-2022 Qianqian Fang <q.fang at neu.edu>
	   (c) 2021	 Yuxuan Zhang <zhang.yuxuan1 at northeastern.edu>
* License: GNU General Public License V3 or later (GPLv3)
* Version: v2022 (v0.6.0)
* Website: http://mcx.space/bp
* Acknowledgement: This project is funded by NIH awards R01-GM114365 and U24-NS124027

BlenderPhotonics is a Blender addon to enable 3-D tetrahedral mesh generation
(via Iso2Mesh [1]) and mesh-based Monte Carlo (MMC) photon simulations (via
MMCLAB [2]) inside the Blender environment. Both Iso2Mesh and MMCLAB are executed in
GNU Octave, which interoperates with Blender via the "oct2py" module and the
"bpy" Python interface. BlenderPhotonics also supports using MATLAB as the
backend to run Iso2Mesh and MMCLAB via "matlab.engine" if installed.

BlenderPhotonics combines the interactive 3-D shape creation/editing and
advanced modeling capabilities provided by Blender with state-of-the-art
Monte Carlo (MC) light simulation techniques and GPU acceleration. It uses
Blender's user-friendly computer-aided-design (CAD) interface as the front-end
to allow creations of complex domains, making it easy-to-use for less-experienced
users to create sophisticated optical simulations needed for a wide range of
biophotonics applications.

Installing this module via Blender menu "Edit\Preference\Add-ons\Install..."
enables the BlenderPhotonics panel. The BlenderPhotonics panel contains
the following 4 submodules:

* Blender2Mesh: converting Blender scene to volumetric tetrahedral mesh models
* Volume2Mesh:  converting NIfTI/JNIfTI/.mat 3D volumes to tetrahedral mesh
* Surface2Mesh: converting and processing triangular surface meshes
* Multiphysics Simulations: configuring and executing MMC photon simulation

For each module, a dialog showing detailed parameters and sub-feature allow
users to adjust the meshing parameters or perform various modeling tasks.

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

[1] Iso2Mesh: http://iso2mesh.sf.net
[2] MMCLAB:   http://mcx.space

"""

bl_info = {
    "name": "BlenderPhotonics_mcx",
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
from .obj2surf import object2surf
from .runmmc import runmmc
from .niifile import niifile
from .nii2mesh import nii2mesh
from bpy.props import PointerProperty

def register():
    print("Registering BlenderPhotonics_mcx")
    bpy.utils.register_class(scene2mesh)
    bpy.utils.register_class(object2surf)
    bpy.utils.register_class(niifile)
    bpy.utils.register_class(nii2mesh)
    bpy.utils.register_class(mesh2scene)
    bpy.utils.register_class(runmmc)
    bpy.utils.register_class(BlenderPhotonics_UI)
    bpy.types.Scene.blender_photonics = PointerProperty(type=niifile)


def unregister():
    print("Unregistering BlenderPhotonics_mcx")
    bpy.utils.unregister_class(scene2mesh)
    bpy.utils.unregister_class(object2surf)
    bpy.utils.unregister_class(niifile)
    bpy.utils.unregister_class(nii2mesh)
    bpy.utils.unregister_class(mesh2scene)
    bpy.utils.unregister_class(runmmc)
    bpy.utils.unregister_class(BlenderPhotonics_UI)
    del bpy.types.Scene.blender_photonics

