"""NIIFile - panel file browser properties

* Authors: (c) 2021-2022 Qianqian Fang <q.fang at neu.edu>
           (c) 2021      Yuxuan Zhang <zhang.yuxuan1 at northeastern.edu>
* License: GNU General Public License V3 or later (GPLv3)
* Website: http://mcx.space/bp

To cite this work, please use the below information

@article {BlenderPhotonics2022,
  author = {Zhang, Yuxuang and Fang, Qianqian},
  title = {{BlenderPhotonics -- a versatile environment for 3-D complex bio-tissue modeling and light transport simulations based on Blender}},
  elocation-id = {2022.01.12.476124},
  year = {2022},
  doi = {10.1101/2022.01.12.476124},
  publisher = {Cold Spring Harbor Laboratory},
  URL = {https://www.biorxiv.org/content/early/2022/01/14/2022.01.12.476124},
  eprint = {https://www.biorxiv.org/content/early/2022/01/14/2022.01.12.476124.full.pdf},
  journal = {bioRxiv}
}
"""

import bpy
from bpy.props import StringProperty, EnumProperty
from bpy.types import PropertyGroup

class niifile(PropertyGroup):
    path: StringProperty(
        name = "JNIfTI File",
        description="Accept NIfTI (.nii/.nii.gz), JSON based JNIfTI (.jnii/.bnii, see http://neurojson.org) and MATLAB .mat file (read the first 3D array object)",
        default="",
        maxlen=2048,
        subtype='FILE_PATH'
        )
    surffile: StringProperty(
        name = "JMesh File",
        description="Accept triangular surfaces stored in JSON-based JMesh (.jmsh/.bmsh, see http://neurojson.org), OFF, STL, ASC, SMF, and GTS",
        default="",
        maxlen=2048,
        subtype='FILE_PATH'
        )
    backend: EnumProperty(
        name = "Backend",
        description="Select either Octave or MATLAB as the backend to run Iso2Mesh and MMCLAB",
        default="octave",
        items = (('octave','Octave','Use oct2py to call Iso2Mesh/MMCLAB from GNU Octave'),('matlab','MATLAB','Use matlab.engine to call Iso2Mesh/MMCLAB from MATLAB'))
        )
