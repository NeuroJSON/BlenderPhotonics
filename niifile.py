import bpy
from bpy.props import StringProperty
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
