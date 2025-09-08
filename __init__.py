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
    "name": "BlenderPhotonics",
    "author": "(c) 2021 Yuxuan (Victor) Zhang, (c) 2021 Qianqian Fang",
    "version": (1, 0),  # min plug-in version
    "blender": (4, 4, 0),  # min blender version
    "location": "Layout，UI",
    "description": "An integrated 3D mesh generation and Monte Carlo photon transport simulation environment",
    "warning": "This plug-in requires the preinstallation of Iso2Mesh (http://iso2mesh.sf.net) and MMCLAB (http://mcx.space)",
    "doc_url": "https://github.com/COTILab/BlenderPhotonics",
    "tracker_url": "https://github.com/COTILab/BlenderPhotonics/issues",
    "category": "User Interface",
}
import bpy
from .ui import (
    BlenderPhotonics_UI,
    BlenderPhotonics_Dependencies_Panel,
    BlenderPhotonics_PMMC_Panel,
    BlenderPhotonics_PMCX_Panel,
    BlenderPhotonicsSettings,
)
from .blender2tet import scene2tmesh as scene2Tmesh, BLENDER2MESH_OT_invoke_saveas
from .blender2voxel import scene2vmesh as scene2Vmesh
from .mesh2blender import mesh2sceneTmesh, mesh2sceneVmesh
from .obj2surf import object2surf
from .runmmc import runmmc, ExportMMCResult
from .runmcx import runmcx, ExportMCXResult
from .nii2tet import (
    volume2tet,
    LoadVolumeTetOperator,
    LoadOpticalParametersTetOperator,
    niitetfile,
)
from .nii2voxel import (
    volume2voxel,
    LoadVolumeOperator,
    LoadOpticalParametersOperator,
    niivoxelfile,
)
from bpy.props import PointerProperty
from .pkg import (
    InstallJData,
    InstallNumPy,
    InstallIso2Mesh,
    InstallPMCX,
    InstallPMMC,
    InstallAllDependencies,
    CheckDependencies,
)
from .dependencies import check_dependencies
from .utils import (
    BLENDERPHOTONICS_OT_show_log_window,
    BLENDERPHOTONICS_OT_clear_log,
    BLENDERPHOTONICS_OT_refresh_log,
)


def register():
    print("Registering BlenderPhotonics")

    # Check dependencies on registration
    check_dependencies()

    # Register settings property group
    bpy.utils.register_class(BlenderPhotonicsSettings)

    # Register logger operator classes
    bpy.utils.register_class(BLENDERPHOTONICS_OT_show_log_window)
    bpy.utils.register_class(BLENDERPHOTONICS_OT_clear_log)
    bpy.utils.register_class(BLENDERPHOTONICS_OT_refresh_log)

    # Register dependency management classes
    bpy.utils.register_class(InstallJData)
    bpy.utils.register_class(InstallNumPy)
    bpy.utils.register_class(InstallIso2Mesh)
    bpy.utils.register_class(InstallPMCX)
    bpy.utils.register_class(InstallPMMC)
    bpy.utils.register_class(InstallAllDependencies)
    bpy.utils.register_class(CheckDependencies)

    # Register main functionality classes
    bpy.utils.register_class(scene2Tmesh)
    bpy.utils.register_class(BLENDER2MESH_OT_invoke_saveas)
    bpy.utils.register_class(scene2Vmesh)
    bpy.utils.register_class(object2surf)
    bpy.utils.register_class(niitetfile)
    bpy.utils.register_class(LoadVolumeTetOperator)
    bpy.utils.register_class(volume2tet)
    bpy.utils.register_class(LoadOpticalParametersTetOperator)
    bpy.utils.register_class(niivoxelfile)
    bpy.utils.register_class(LoadVolumeOperator)
    bpy.utils.register_class(volume2voxel)
    bpy.utils.register_class(LoadOpticalParametersOperator)
    bpy.utils.register_class(mesh2sceneTmesh)
    bpy.utils.register_class(mesh2sceneVmesh)
    bpy.utils.register_class(runmmc)
    bpy.utils.register_class(ExportMMCResult)
    bpy.utils.register_class(runmcx)
    bpy.utils.register_class(ExportMCXResult)

    # Register UI classes
    bpy.utils.register_class(BlenderPhotonics_UI)
    bpy.utils.register_class(BlenderPhotonics_Dependencies_Panel)
    bpy.utils.register_class(BlenderPhotonics_PMMC_Panel)
    bpy.utils.register_class(BlenderPhotonics_PMCX_Panel)

    # Register property pointers
    bpy.types.Scene.blender_photonics = PointerProperty(type=niitetfile)
    bpy.types.Scene.blender_photonics_tet = PointerProperty(type=niitetfile)
    bpy.types.Scene.blender_photonics_voxel = PointerProperty(type=niivoxelfile)
    bpy.types.Scene.blender_photonics_settings = PointerProperty(
        type=BlenderPhotonicsSettings
    )


def unregister():
    print("Unregistering BlenderPhotonics")

    # Unregister logger operator classes
    bpy.utils.unregister_class(BLENDERPHOTONICS_OT_show_log_window)
    bpy.utils.unregister_class(BLENDERPHOTONICS_OT_clear_log)
    bpy.utils.unregister_class(BLENDERPHOTONICS_OT_refresh_log)

    # Unregister dependency management classes
    bpy.utils.unregister_class(InstallJData)
    bpy.utils.unregister_class(InstallNumPy)
    bpy.utils.unregister_class(InstallIso2Mesh)
    bpy.utils.unregister_class(InstallPMCX)
    bpy.utils.unregister_class(InstallPMMC)
    bpy.utils.unregister_class(InstallAllDependencies)
    bpy.utils.unregister_class(CheckDependencies)

    # Unregister main functionality classes
    bpy.utils.unregister_class(scene2Tmesh)
    bpy.utils.unregister_class(BLENDER2MESH_OT_invoke_saveas)
    bpy.utils.unregister_class(scene2Vmesh)
    bpy.utils.unregister_class(object2surf)
    bpy.utils.unregister_class(niitetfile)
    bpy.utils.unregister_class(LoadVolumeTetOperator)
    bpy.utils.unregister_class(volume2tet)
    bpy.utils.unregister_class(LoadOpticalParametersTetOperator)
    bpy.utils.unregister_class(niivoxelfile)
    bpy.utils.unregister_class(volume2voxel)
    bpy.utils.unregister_class(LoadOpticalParametersOperator)
    bpy.utils.unregister_class(LoadVolumeOperator)
    bpy.utils.unregister_class(mesh2sceneTmesh)
    bpy.utils.unregister_class(mesh2sceneVmesh)
    bpy.utils.unregister_class(runmmc)
    bpy.utils.unregister_class(ExportMMCResult)
    bpy.utils.unregister_class(runmcx)
    bpy.utils.unregister_class(ExportMCXResult)

    # Unregister UI classes
    bpy.utils.unregister_class(BlenderPhotonics_UI)
    bpy.utils.unregister_class(BlenderPhotonics_Dependencies_Panel)
    bpy.utils.unregister_class(BlenderPhotonics_PMMC_Panel)
    bpy.utils.unregister_class(BlenderPhotonics_PMCX_Panel)

    # Unregister settings property group
    bpy.utils.unregister_class(BlenderPhotonicsSettings)

    # Delete property pointers
    del bpy.types.Scene.blender_photonics
    del bpy.types.Scene.blender_photonics_tet
    del bpy.types.Scene.blender_photonics_voxel
    del bpy.types.Scene.blender_photonics_settings
