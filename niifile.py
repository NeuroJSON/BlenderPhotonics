import bpy
from bpy.props import StringProperty
from bpy.types import PropertyGroup

class niifile(PropertyGroup):
    path: StringProperty(
        name = "NIfTI",
        description="NIfTI file name:",
        default="",
        maxlen=2048,
        subtype='FILE_PATH'
        )
    
