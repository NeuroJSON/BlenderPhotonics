"""NIIFile - panel file browser properties

* Authors: (c) 2021-2022 Qianqian Fang <q.fang at neu.edu>
           (c) 2021      Yuxuan Zhang <zhang.yuxuan1 at northeastern.edu>
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
from bpy.props import StringProperty, EnumProperty
from bpy.types import PropertyGroup


class niifile(PropertyGroup):
    path: StringProperty(
        name="JNIfTI File",
        description="Accept NIfTI (.nii/.nii.gz), JSON based JNIfTI (.jnii/.bnii, see http://neurojson.org) and MATLAB .mat file (read the first 3D array object)",
        default="",
        maxlen=2048,
        subtype="FILE_PATH",
    )
    surffile: StringProperty(
        name="JMesh File",
        description="Accept triangular surfaces stored in JSON-based JMesh (.jmsh/.bmsh, see http://neurojson.org), OFF, STL, ASC, SMF, and GTS",
        default="",
        maxlen=2048,
        subtype="FILE_PATH",
    )
    backend: EnumProperty(
        name="Backend",
        description="Select either Octave or MATLAB as the backend to run Iso2Mesh and MMCLAB",
        default="octave",
        items=(
            (
                "octave",
                "Octave",
                "Use oct2py to call Iso2Mesh/MMCLAB from GNU Octave",
            ),
            (
                "matlab",
                "MATLAB",
                "Use matlab.engine to call Iso2Mesh/MMCLAB from MATLAB",
            ),
        ),
    )
