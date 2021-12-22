import bpy
from bpy.props import StringProperty
from bpy.types import PropertyGroup

class MyProperties(PropertyGroup):
    my_path: StringProperty(
        name = "nii file",
        description="Choose nii file here:",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'
        )
    
