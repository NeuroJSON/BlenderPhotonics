import bpy
import subprocess
import sys
import os
import pathlib


class InstallOct2py(bpy.types.Operator):
    bl_idname = "blenderphotonics.install_oct2py"
    bl_label = "Install Package"
    bl_description = "Install Oct2py Python package"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Install Oct2py
        ADDON_DIR = os.path.join(os.path.abspath(pathlib.Path(__file__).resolve().parent.parent), "modules")
        if not os.path.exists(ADDON_DIR):
            os.makedirs(ADDON_DIR)
        subprocess.call([sys.executable, "-m", "pip", "install", "oct2py", "--target=" + ADDON_DIR])
        return {"FINISHED"}


class InstallJData(bpy.types.Operator):
    bl_idname = "blenderphotonics.install_jdata"
    bl_label = "Install Package"
    bl_description = "Install JData package"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Install JData
        ADDON_DIR = os.path.join(os.path.abspath(pathlib.Path(__file__).resolve().parent.parent), "modules")
        if not os.path.exists(ADDON_DIR):
            os.makedirs(ADDON_DIR)
        subprocess.call([sys.executable, "-m", "pip", "install", "jdata", "--target=" + ADDON_DIR])
        return {"FINISHED"}
