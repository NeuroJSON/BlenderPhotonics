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
