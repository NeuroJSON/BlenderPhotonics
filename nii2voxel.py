"""NII2Voxel - converting NIfTI/JNIfTI volume data to voxel mesh for pMCX simulation

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
import os
import re
import urllib.request
from bpy.props import StringProperty, FloatProperty, EnumProperty
from bpy.types import PropertyGroup, Operator
from .utils import *
from .dependencies import safe_import, require_dependency, show_error_message

# Safe imports
np = safe_import("numpy")
jd = safe_import("jdata")
iso2mesh = safe_import("iso2mesh")

g_maxvol = 100
g_radbound = 10
g_distbound = 1.0
g_isovalue = 0.5
g_imagetype = "multi-label"
g_method = "auto"


class niivoxelfile(PropertyGroup):
    """File browser properties for NIfTI and voxel mesh files"""

    path: StringProperty(
        name="JNIfTI File",
        description="Accept NIfTI (.nii/.nii.gz), JSON based JNIfTI (.jnii/.bnii, see http://neurojson.org) and MATLAB .mat file (read the first 3D array object)",
        default="",
        maxlen=2048,
        subtype="FILE_PATH",
    )
    surffile: StringProperty(
        name="JMesh File",
        description="Accept voxel meshes stored in JSON-based JMesh (.jmsh/.bmsh, see http://neurojson.org), OFF, STL, ASC, SMF, and GTS formats",
        default="",
        maxlen=2048,
        subtype="FILE_PATH",
    )
    optical_params_file: StringProperty(
        name="Optical Parameters File",
        description="JSON file containing optical parameters for different tissue regions",
        default="",
        maxlen=2048,
        subtype="FILE_PATH",
    )


class LoadVolumeOperator(Operator):
    """Load and preview volume data from NIfTI/JNIfTI file"""

    bl_idname = "blenderphotonics.load_volume"
    bl_label = "Load Volume"
    bl_description = "Load and preview volume data from the selected file"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bp = bpy.context.scene.blender_photonics_voxel
        inputfile = bp.path

        if not inputfile or not os.path.exists(inputfile):
            show_error_message("Please select a valid input file", "File Error")
            return {"CANCELLED"}

        try:
            if not require_dependency("jdata", "volume loading"):
                return {"CANCELLED"}

            if not np:
                show_error_message(
                    "NumPy is required for volume processing", "Dependency Error"
                )
                return {"CANCELLED"}

            log_message(f"Loading volume data from: {inputfile}", "INFO")

            if inputfile.endswith(("nii", "nii.gz")):
                # Load volume data using jdata
                volume_data = jd.loadjd(inputfile)
                log_message(f"Loaded data structure: {type(volume_data)}", "INFO")
                image = volume_data["NIFTIData"]
                image = (image - np.min(image)) / (
                    np.max(image) - np.min(image)
                )  # normalize data to [0, 1]
            elif inputfile.endswith("mat"):
                log_message("Starting voxel mesh conversion from mat...", "INFO")
                volume_data = jd.loadjd(inputfile)
                image = volume_data["vol"]
                image = (image - np.min(image)) / (
                    np.max(image) - np.min(image)
                )  # normalize data to [0, 1]

                output_dir = os.path.dirname(inputfile)
                # clear all object in scence
                bpy.ops.object.select_all(action="SELECT")
                bpy.ops.object.delete()

            # Use existing ConvertMat2Vdb and volume import functions from utils
            base_name = (
                os.path.splitext(os.path.basename(inputfile))[0]
                if inputfile.endswith(("nii", "nii.gz"))
                else "MatInput"
            )
            output_dir = os.path.dirname(inputfile)

            # Convert volume array to VDB format
            LoadVolMesh(
                {"NIFTIData": image, "scale": np.eye(4)},
                base_name,
                output_dir,
                "nii_view",
            )

            ShowMessageBox(
                f"Volume loaded successfully!\nShape: {image.shape}\nRange: {image.min():.3f} to {image.max():.3f}",
                "Volume Loaded",
            )

        except Exception as e:
            log_message(f"Error loading volume: {str(e)}", "ERROR")
            show_error_message(f"Failed to load volume: {str(e)}", "Load Error")
            return {"CANCELLED"}

        return {"FINISHED"}


class volume2voxel(Operator):
    """Convert NIfTI/JNIfTI volume to voxel mesh for pMCX simulation"""

    bl_idname = "blenderphotonics.volume2voxel"
    bl_label = "Convert to Voxel Mesh"
    bl_description = "Convert loaded volume data to voxel mesh format for pMCX Monte Carlo simulation"
    bl_options = {"REGISTER", "UNDO"}

    def vol2voxel(self):
        if not require_dependency("jdata", "volume to voxel mesh conversion"):
            return
        if not require_dependency("iso2mesh", "volume to voxel mesh conversion"):
            return

        bp = bpy.context.scene.blender_photonics_voxel
        inputfile = bp.path

        if not inputfile or not os.path.exists(inputfile):
            show_error_message("Please select a valid input file", "File Error")
            return

        try:
            if inputfile.endswith((".nii", ".nii.gz")):
                log_message("Starting voxel mesh conversion...", "INFO")
                volume_data = jd.loadjd(inputfile)
                log_message(f"Loaded data structure: {type(volume_data)}", "INFO")
                image = volume_data["NIFTIData"]
                _, inverse = np.unique(
                    image, return_inverse=True
                )  # unique_vals: region labels
                image = inverse.reshape(image.shape)  # Convert to multi-label
                image = image.astype(
                    "uint8"
                )  # Ensure data type is uint8 for voxel mesh
                log_message(f"Input file: {inputfile}", "INFO")
                log_message(
                    "Starting voxel mesh conversion (no additional parameters needed)",
                    "INFO",
                )

                output_dir = os.path.dirname(inputfile)
                # clear all object in scence
                bpy.ops.object.select_all(action="SELECT")
                bpy.ops.object.delete()

                # Load the volume mesh
                LoadVolMesh(
                    {"NIFTIData": image, "scale": np.eye(4)},
                    "NiiSetup",
                    output_dir,
                    "nii_view",
                )

            elif inputfile.endswith("mat"):
                log_message("Starting voxel mesh conversion from mat...", "INFO")
                volume_data = jd.loadjd(inputfile)
                log_message(f"Loaded data structure: {type(volume_data)}", "INFO")
                image = volume_data["vol"]
                _, inverse = np.unique(
                    image, return_inverse=True
                )  # unique_vals: region labels
                image = inverse.reshape(image.shape)  # Convert to multi-label
                image = image.astype(
                    "uint8"
                )  # Ensure data type is uint8 for voxel mesh
                log_message(f"Input file: {inputfile}", "INFO")
                log_message(
                    "Starting voxel mesh conversion (no additional parameters needed)",
                    "INFO",
                )

                output_dir = os.path.dirname(inputfile)
                # clear all object in scence
                bpy.ops.object.select_all(action="SELECT")
                bpy.ops.object.delete()

                # Load the volume mesh
                LoadVolMesh(
                    {"NIFTIData": image, "scale": np.eye(4)},
                    "MatSetup",
                    output_dir,
                    "nii_view",
                )

            # Generate output filename
            output_dir = GetBPWorkFolder()
            output_path = os.path.join(output_dir, "imageVmesh.jmsh")
            image_data = {
                "_DataInfo_": {
                    "JMeshVersion": "0.5",
                    "Comment": "Created by BlenderPhotonics (http:\/\/mcx.space\/BlenderPhotonics)",
                },
                "ImageMesh": image,
                "ImageScale": np.eye(4),
            }
            jd.savejd(image_data, output_path)

        except Exception as e:
            log_message(f"Error during voxel mesh conversion: {str(e)}", "ERROR")
            show_error_message(
                f"Voxel mesh conversion failed: {str(e)}", "Conversion Error"
            )
            return

        ShowMessageBox("Voxel mesh generation is complete.", "BlenderPhotonics")

        ## add light source
        light_data = bpy.data.lights.new(name="Lightsource", type="SPOT")
        light_object = bpy.data.objects.new(name="Lightsource", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object
        light_object.location = (0, 0, 5)
        light_object.scale = (0.1, 0.1, 1)
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()

        # add cfg option
        obj = bpy.data.objects["Lightsource"]
        obj["nphoton"] = 10000
        obj["srctype"] = "pencil"
        obj["srcparam1"] = [0.0, 0.0, 0.0, 0.0]
        obj["srcparam2"] = [0.0, 0.0, 0.0, 0.0]
        obj["unitinmm"] = 1

        log_message("Light source added successfully", "INFO")

    def execute(self, context):
        self.vol2voxel()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class LoadOpticalParametersOperator(Operator):
    """Load optical parameters from JSON file"""

    bl_idname = "blenderphotonics.load_optical_params"
    bl_label = "Load Optical Parameters"
    bl_description = "Load optical parameters from JSON file for tissue regions"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bp = bpy.context.scene.blender_photonics_voxel
        params_file = bp.optical_params_file

        if not params_file or not os.path.exists(params_file):
            show_error_message(
                "Please select a valid optical parameters file", "File Error"
            )
            return {"CANCELLED"}

        try:
            if not require_dependency("jdata", "optical parameters loading"):
                return {"CANCELLED"}

            log_message(f"Loading optical parameters from: {params_file}", "INFO")

            if (
                "NiiSetup_nii" not in bpy.data.objects
                and "MatSetup_nii" not in bpy.data.objects
            ):
                show_error_message(
                    "NiiSetup_nii or MatSetup_nii object not found", "Object Error"
                )
                return {"CANCELLED"}

            if params_file.endswith(".json"):
                obj = bpy.data.objects["NiiSetup_nii"]
                optical_parameter = jd.load(params_file)
                digit = int(math.log(optical_parameter["prop"].shape[0] - 1, 10) + 1)
                for i in range(1, optical_parameter["region number"] + 1):
                    region_name = f"region_{str(i).rjust(digit, '0')}"
                    if region_name in optical_parameter["optical parameters"]:
                        obj.data["Optical_prop_" + str(i).rjust(digit, "0")] = (
                            optical_parameter["optical parameters"][region_name]
                        )
                        log_message(
                            f"Loaded parameters for {region_name}: {optical_parameter['optical parameters'][region_name]}",
                            "INFO",
                        )
                    else:
                        log_message(
                            f"Region {i} parameters not found in file", "WARNING"
                        )
            elif params_file.endswith(".mat"):
                obj = bpy.data.objects["MatSetup_nii"]
                optical_parameter = jd.loadjd(params_file)
                digit = int(math.log(optical_parameter["prop"].shape[0] - 1, 10) + 1)
                for i in range(1, optical_parameter["prop"].shape[0]):
                    region_name = f"region_{str(i).rjust(digit, '0')}"
                    obj.data["Optical_prop_" + str(i).rjust(digit, "0")] = (
                        optical_parameter["prop"][i]
                    )
                    log_message(
                        f"Loaded parameters for {region_name}: {optical_parameter['prop'][i]}",
                        "INFO",
                    )

                # Light source setup if mat contain information
                obj = bpy.data.objects["Lightsource"]
                obj["nphoton"] = (
                    optical_parameter["nphoton"]
                    if "nphoton" in optical_parameter
                    else 10000
                )
                obj["srctype"] = (
                    optical_parameter["srctype"]
                    if "srctype" in optical_parameter
                    else "pencil"
                )
                obj["srcparam1"] = (
                    optical_parameter["srcparam1"]
                    if "srcparam1" in optical_parameter
                    else [0.0, 0.0, 0.0, 0.0]
                )
                obj["srcparam2"] = (
                    optical_parameter["srcparam2"]
                    if "srcparam2" in optical_parameter
                    else [0.0, 0.0, 0.0, 0.0]
                )
                obj["unitinmm"] = (
                    optical_parameter["unitinmm"]
                    if "unitinmm" in optical_parameter
                    else 1
                )
                obj.location = (
                    optical_parameter["srcpos"][0]
                    if "srcpos" in optical_parameter
                    else (0.0, 0.0, 0.0)
                )

                log_message(
                    f"Light source parameters: nphoton={obj['nphoton']}, srctype={obj['srctype']}, srcparam1={obj['srcparam1']}, srcparam2={obj['srcparam2']}, unitinmm={obj['unitinmm']}, location={obj.location}",
                    "INFO",
                )

                import mathutils

                target_direction = (
                    mathutils.Vector(optical_parameter["srcdir"][0])
                    if "srcdir" in optical_parameter
                    else mathutils.Vector((0.0, 0.0, -1.0))
                )
                target_direction.normalize()
                rotation_quaternion = mathutils.Vector(
                    (0.0, 0.0, -1.0)
                ).rotation_difference(target_direction)
                log_message(f"rotation_quaternion: {rotation_quaternion}", "INFO")
                obj.rotation_mode = "QUATERNION"
                obj.rotation_quaternion = rotation_quaternion

            log_message("Optical parameters loaded successfully", "INFO")

        except Exception as e:
            log_message(f"Error loading optical parameters: {str(e)}", "ERROR")
            show_error_message(
                f"Failed to load optical parameters: {str(e)}", "Load Error"
            )
            return {"CANCELLED"}

        return {"FINISHED"}


#
# Define registration for Blender
#

blender_classes = [
    niivoxelfile,
    LoadVolumeOperator,
    volume2voxel,
    LoadOpticalParametersOperator,
]


def register():
    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)


def unregister():
    for blender_class in blender_classes:
        bpy.utils.unregister_class(blender_class)


if __name__ == "__main__":
    register()
