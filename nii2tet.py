"""NII2Tet - converting NIfTI/JNIfTI volume data to tetrahedral mesh for pMMC simulation

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
import math
from bpy.props import StringProperty, FloatProperty, EnumProperty
from bpy.types import PropertyGroup, Operator
from .utils import *
from .dependencies import safe_import, require_dependency, show_error_message

# Safe imports
np = safe_import("numpy")
jd = safe_import("jdata")
iso2mesh = safe_import("iso2mesh")

g_maxvol = 100
g_dofix = False
g_method = "cgalmesh"


class niitetfile(PropertyGroup):
    """File browser properties for NIfTI and tetrahedral mesh files"""

    path: StringProperty(
        name="JNIfTI File",
        description="Accept NIfTI (.nii/.nii.gz), JSON based JNIfTI (.jnii/.bnii, see http://neurojson.org) and MATLAB .mat file (read the first 3D array object)",
        default="",
        maxlen=2048,
        subtype="FILE_PATH",
    )
    surffile: StringProperty(
        name="JMesh File",
        description="Accept tetrahedral meshes stored in JSON-based JMesh (.jmsh/.bmsh, see http://neurojson.org), OFF, STL, ASC, SMF, and GTS formats",
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


class LoadVolumeTetOperator(Operator):
    """Load and preview volume data from NIfTI/JNIfTI file for tetrahedral mesh generation"""

    bl_idname = "blenderphotonics.load_volume_tet"
    bl_label = "Load Volume"
    bl_description = "Load and preview volume data from the selected file for tetrahedral mesh generation"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bp = bpy.context.scene.blender_photonics_tet
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
                base_name = os.path.splitext(os.path.basename(inputfile))[0]
                output_dir = os.path.dirname(inputfile)
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

            elif inputfile.endswith("mat"):
                log_message("Starting tetrahedral mesh conversion from mat...", "INFO")
                outputdir = GetBPWorkFolder()
                volume_data = jd.loadjd(inputfile)
                node = volume_data["node"]
                elem = np.hstack([volume_data["elem"], volume_data["elemprop"].T])

                meshdata = {
                    "_DataInfo_": {
                        "JMeshVersion": "0.5",
                        "Comment": "Created by BlenderPhotonics Python iso2mesh implementation",
                    }
                }

                meshdata["MeshVertex3"] = node.tolist()

                outputmesh = meshdata.copy()
                region_labels = np.unique(elem[:, 4])
                # clear all object in scence
                bpy.ops.object.select_all(action="SELECT")
                bpy.ops.object.delete()
                for i in region_labels:
                    # Get elements for this region
                    region_elems = elem[elem[:, 4] == i, :4]
                    if len(region_elems) > 0:
                        # Extract surface faces for this region
                        fc1, _ = iso2mesh.volface(region_elems)
                        outputmesh[f"MeshTri3({i})"] = fc1.tolist()
                        log_message(
                            f"Processed region {i} with {len(fc1)} surface faces"
                        )
                        AddMeshFromNodeFace(node, fc1, f"region_{int(i)}")
                log_message("Saving region mesh...")
                jd.save(outputmesh, os.path.join(outputdir, "regionTmesh.jmsh"))

                volume_mesh = meshdata.copy()
                volume_mesh["MeshNode"] = node.tolist()
                volume_mesh["MeshFace"] = iso2mesh.meshface(elem)
                volume_mesh["MeshElem"] = elem.tolist()
                volume_mesh["MeshTet4"] = elem.tolist()
                jd.save(volume_mesh, os.path.join(outputdir, "volumeTmesh.jmsh"))

                ShowMessageBox(
                    f"Volume mesh saved successfully!\nRegion Mesh: regionTmesh.jmsh\nVolume Mesh: volumeTmesh.jmsh",
                    "Mesh Saved",
                )

        except Exception as e:
            log_message(f"Error loading volume: {str(e)}", "ERROR")
            show_error_message(f"Failed to load volume: {str(e)}", "Load Error")
            return {"CANCELLED"}

        return {"FINISHED"}


class volume2tet(Operator):
    """Convert NIfTI/JNIfTI volume to tetrahedral mesh for pMMC simulation"""

    bl_idname = "blenderphotonics.volume2tet"
    bl_label = "Convert to Tetrahedral Mesh"
    bl_description = "Convert loaded volume data to tetrahedral mesh format for pMMC Monte Carlo simulation"
    bl_options = {"REGISTER", "UNDO"}

    maxvol: bpy.props.FloatProperty(default=g_maxvol, name="Maximum tet volume")
    dofix: bpy.props.BoolProperty(default=g_dofix, name="Fix mesh")
    method: bpy.props.EnumProperty(
        default=g_method,
        name="Method",
        items=[
            ("cgalsurf", "CGAL Surface", "Use CGAL surface mesher"),
            ("simplify", "Simplify", "Use binsurface and then simplify"),
            (
                "cgalmesh",
                "CGAL Mesh",
                "Use CGAL 3.5 3D mesher for direct mesh generation",
            ),
        ],
    )

    def vol2tet(self):
        if not require_dependency("jdata", "volume to tetrahedral mesh conversion"):
            return
        if not require_dependency("iso2mesh", "volume to tetrahedral mesh conversion"):
            return

        bp = bpy.context.scene.blender_photonics_tet
        inputfile = bp.path

        if not inputfile or not os.path.exists(inputfile):
            show_error_message("Please select a valid input file", "File Error")
            return

        try:
            if inputfile.endswith((".nii", ".nii.gz")):
                log_message("Starting tetrahedral mesh conversion...", "INFO")
                volume_data = jd.loadjd(inputfile)
                log_message(f"Loaded data structure: {type(volume_data)}", "INFO")
                image = volume_data["NIFTIData"]
                node, elem, face = iso2mesh.v2m(
                    image, maxvol=self.maxvol, dofix=self.dofix, method=self.method
                )

                log_message(f"Input file: {inputfile}", "INFO")
                log_message("Starting tetrahedral mesh conversion", "INFO")

                output_dir = os.path.dirname(inputfile)
                # clear all object in scence
                bpy.ops.object.select_all(action="SELECT")
                bpy.ops.object.delete()

                # Load the volume mesh
                LoadVolMesh(
                    {"NIFTIData": image, "scale": np.eye(4)},
                    "NiiTetSetup",
                    output_dir,
                    "nii_view",
                )

                # Generate output filename
                output_dir = GetBPWorkFolder()
                output_path = os.path.join(output_dir, "imageTmesh.jmsh")
                image_data = {
                    "_DataInfo_": {
                        "JMeshVersion": "0.5",
                        "Comment": "Created by BlenderPhotonics (http:\/\/mcx.space\/BlenderPhotonics)",
                    },
                    "ImageMesh": image,
                    "ImageScale": np.eye(4),
                }
                jd.savejd(image_data, output_path)

                meshdata = {
                    "_DataInfo_": {
                        "JMeshVersion": "0.5",
                        "Comment": "Created by BlenderPhotonics Python iso2mesh implementation",
                    }
                }

                meshdata["MeshVertex3"] = node.tolist()

                outputmesh = meshdata.copy()
                region_labels = np.unique(elem[:, 4])
                # clear all object in scence
                bpy.ops.object.select_all(action="SELECT")
                bpy.ops.object.delete()
                for i in region_labels:
                    # Get elements for this region
                    region_elems = elem[elem[:, 4] == i, :4]
                    if len(region_elems) > 0:
                        # Extract surface faces for this region
                        fc1, _ = iso2mesh.volface(region_elems)
                        outputmesh[f"MeshTri3({i})"] = fc1.tolist()
                        log_message(
                            f"Processed region {i} with {len(fc1)} surface faces"
                        )
                        AddMeshFromNodeFace(node, fc1, f"region_{int(i)}")
                log_message("Saving region mesh...")
                jd.save(outputmesh, os.path.join(output_dir, "regionTmesh.jmsh"))

                volume_mesh = meshdata.copy()
                volume_mesh["MeshNode"] = node.tolist()
                volume_mesh["MeshFace"] = face.tolist()
                volume_mesh["MeshElem"] = elem.tolist()
                volume_mesh["MeshTet4"] = elem.tolist()
                jd.save(volume_mesh, os.path.join(output_dir, "volumeTmesh.jmsh"))

            elif inputfile.endswith("mat"):
                log_message("Starting tetrahedral mesh conversion from mat...", "INFO")
                log_message(f"There is no need to convert .mat files", "INFO")

        except Exception as e:
            log_message(f"Error during tetrahedral mesh conversion: {str(e)}", "ERROR")
            show_error_message(
                f"Tetrahedral mesh conversion failed: {str(e)}", "Conversion Error"
            )
            return

        ShowMessageBox("Tetrahedral mesh generation is complete.", "BlenderPhotonics")

        ## add light source
        light_data = bpy.data.lights.new(name="Lightsource", type="SPOT")
        light_object = bpy.data.objects.new(name="Lightsource", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object
        light_object.location = (0, 0, 5)
        light_object.scale = (0.1, 0.1, 1)
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()

        # add cfg option for pMMC
        obj = bpy.data.objects["Lightsource"]
        obj["nphoton"] = 10000
        obj["srctype"] = "pencil"
        obj["srcparam1"] = [0.0, 0.0, 0.0, 0.0]
        obj["srcparam2"] = [0.0, 0.0, 0.0, 0.0]
        obj["unitinmm"] = 1

        log_message("Light source added successfully for pMMC", "INFO")

    def execute(self, context):
        self.vol2tet()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class LoadOpticalParametersTetOperator(Operator):
    """Load optical parameters from JSON file for tetrahedral mesh"""

    bl_idname = "blenderphotonics.load_optical_params_tet"
    bl_label = "Load Optical Parameters"
    bl_description = (
        "Load optical parameters from JSON file for tissue regions in tetrahedral mesh"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bp = bpy.context.scene.blender_photonics_tet
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
                "NiiTetSetup_nii" not in bpy.data.objects
                and "MatTetSetup_nii" not in bpy.data.objects
            ):
                show_error_message(
                    "NiiTetSetup_nii or MatTetSetup_nii object founded, voxel to tet workflow",
                    "INFO",
                )
            elif "region_1" not in bpy.data.objects:
                show_error_message("region_1 object founded, load mat workflow", "INFO")
            else:
                show_error_message("Unknown workflow", "INFO")
                return {"CANCELLED"}

            if params_file.endswith(".json"):
                obj = bpy.data.objects["NiiTetSetup_nii"]
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
                optical_parameter = jd.loadjd(params_file)
                region_labels = np.unique(optical_parameter["elemprop"])
                for index, i in enumerate(region_labels):
                    if i == 0:
                        log_message(f"Skipping background region {int(i)}", "INFO")
                        continue
                    else:
                        log_message(
                            f"Processing region {int(i)} with index {index}", "INFO"
                        )

                    obj = bpy.data.objects[f"region_{int(i)}"]
                    obj["mua"] = optical_parameter["prop"][i][0]
                    obj["mus"] = optical_parameter["prop"][i][1]
                    obj["g"] = optical_parameter["prop"][i][2]
                    obj["n"] = optical_parameter["prop"][i][3]
                    log_message(
                        f"Loaded parameters for region_{int(i)}: {optical_parameter['prop'][i]}",
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
                optical_parameter["srctype"][0]
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
                optical_parameter["unitinmm"].item()
                if "unitinmm" in optical_parameter
                else 1.0
            )
            obj.location = (
                optical_parameter["srcpos"][0]
                if "srcpos" in optical_parameter
                else (0.0, 0.0, 0.0)
            )

            log_message(
                f"Light source parameters for pMMC: nphoton={obj['nphoton']}, srctype={obj['srctype']}, srcparam1={obj['srcparam1']}, srcparam2={obj['srcparam2']}, unitinmm={obj['unitinmm']}, location={obj.location}",
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

            log_message(
                "Optical parameters loaded successfully for tetrahedral mesh", "INFO"
            )

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
    niitetfile,
    LoadVolumeTetOperator,
    volume2tet,
    LoadOpticalParametersTetOperator,
]


def register():
    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)


def unregister():
    for blender_class in blender_classes:
        bpy.utils.unregister_class(blender_class)


if __name__ == "__main__":
    register()
