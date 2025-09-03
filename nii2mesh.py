"""NII2Mesh - converting a 3-D volumetric image (stored in NIfTI/JNIfTI/.mat file) to tetrahedral mesh

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
from bpy.types import PropertyGroup
from .utils import *
from .dependencies import safe_import, require_dependency, show_error_message

# Safe imports
np = safe_import("numpy")
jd = safe_import("jdata")

g_maxvol = 100
g_radbound = 10
g_distbound = 1.0
g_isovalue = 0.5
g_imagetype = "multi-label"
g_method = "auto"


class niifile(PropertyGroup):
    """File browser properties for NIfTI and surface mesh files"""

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


class nii2mesh(bpy.types.Operator):
    bl_label = "Convert 3-D image file to mesh"
    bl_description = "Click this button to convert a 3D volume stored in JNIfTI (.jnii/.bnii, see http://neurojson.org) or NIfTI (.nii/.nii.gz) or .mat file to a mesh"
    bl_idname = "blenderphotonics.creatregion"

    # creat a interface to set uesrs' model parameter.

    bl_options = {"REGISTER", "UNDO"}
    maxvol: FloatProperty(default=g_maxvol, name="Maximum tetrahedron volume")
    radbound: FloatProperty(
        default=g_radbound, name="Surface triangle maximum diameter"
    )
    distbound: FloatProperty(
        default=g_distbound, name="Maximum deviation from true boundary"
    )
    isovalue: FloatProperty(default=g_isovalue, name="Isovalue to create surface")
    imagetype: EnumProperty(
        name="Volume type",
        items=[
            ("multi-label", "multi-label", "multi-label"),
            ("binary", "binary", "binary"),
            ("grayscale", "grayscale", "grayscale"),
        ],
    )
    method: EnumProperty(
        name="Mesh extraction method",
        items=[
            ("auto", "auto", "auto"),
            ("cgalmesh", "cgalmesh", "cgalmesh"),
            ("cgalsurf", "cgalsurf", "cgalsurf"),
            ("simplify", "simplify", "simplify"),
        ],
    )

    def python_nii2mesh(self, outputdir):
        """
        Python implementation of nii2mesh functionality
        Converts NIfTI/JNIfTI files to tetrahedral mesh using iso2mesh
        """
        import re
        import urllib.request
        from .utils import log_message

        # Check dependencies
        if not require_dependency("jdata", "NIfTI file loading"):
            return False
        if not require_dependency("iso2mesh", "mesh generation"):
            return False
        if not require_dependency("numpy", "numerical operations"):
            return False

        try:
            # Load input parameters
            input_params = jd.load(os.path.join(outputdir, "niipath.json"))
            niipath = input_params["niipath"]

            if not niipath:
                show_error_message("No NIfTI file path specified", "Input Error")
                return False

            log_message(f"Processing NIfTI file: {niipath}")

            # Handle HTTP URLs (download if needed)
            if re.search(r"^http", niipath, re.IGNORECASE):
                suffix_match = re.search(
                    r"\.[jb]*nii(\.gz)*|\.mat|\.json", niipath, re.IGNORECASE
                )
                suffix = suffix_match.group(0) if suffix_match else ".json"

                local_path = os.path.join(outputdir, f"volumedata{suffix}")
                log_message(f"Downloading from URL to: {local_path}")
                urllib.request.urlretrieve(niipath, local_path)
                niipath = local_path

            # Load volume data based on file extension
            vol_data = None

            if re.search(r"\.[jb]*nii(\.gz)*$|\.json$", niipath, re.IGNORECASE):
                # JNIfTI format
                log_message("Loading JNIfTI format file")
                vol = jd.load(niipath)
                if "NIFTIData" in vol:
                    vol_data = vol["NIFTIData"]
                elif "data" in vol:
                    vol_data = vol["data"]
                else:
                    show_error_message(
                        "Invalid JNIfTI file: missing data field", "Format Error"
                    )
                    return False

            elif re.search(r"\.hdr$|\.img$|\.nii$|\.nii\.gz$", niipath, re.IGNORECASE):
                # Standard NIfTI format
                log_message("Loading standard NIfTI format file")
                try:
                    # Try to use nibabel if available
                    import nibabel as nib

                    nii = nib.load(niipath)
                    vol_data = nii.get_fdata()
                except ImportError:
                    show_error_message(
                        "nibabel required for NIfTI files. Please install: pip install nibabel",
                        "Missing Dependency",
                    )
                    return False

            elif re.search(r"\.mat$", niipath, re.IGNORECASE):
                # MATLAB format
                log_message("Loading MATLAB format file")
                try:
                    from scipy.io import loadmat

                    tmp = loadmat(niipath)
                    # Find first 3D array
                    for key, value in tmp.items():
                        if (
                            not key.startswith("__")
                            and hasattr(value, "ndim")
                            and value.ndim == 3
                        ):
                            vol_data = value
                            log_message(
                                f"Found 3D array: {key} with shape {value.shape}"
                            )
                            break
                    if vol_data is None:
                        show_error_message(
                            "No 3D array found in MATLAB file", "Format Error"
                        )
                        return False
                except ImportError:
                    show_error_message(
                        "scipy required for MATLAB files. Please install: pip install scipy",
                        "Missing Dependency",
                    )
                    return False
            else:
                show_error_message(
                    f"Unsupported file format: {niipath}", "Format Error"
                )
                return False

            if vol_data is None:
                show_error_message("Failed to load volume data", "Data Error")
                return False

            # Convert to numpy array and ensure proper data type
            vol_data = np.array(vol_data)
            log_message(f"Volume data shape: {vol_data.shape}, dtype: {vol_data.dtype}")

            # Set up meshing options
            opt = {
                "radbound": input_params.get("radbound", 10),
                "distbound": input_params.get("distbound", 1),
            }
            maxvol = input_params.get("maxvol", 100)
            method = input_params.get("method", "cgalmesh")
            isovalue = input_params.get("isovalue", 0.5)

            log_message(
                f"Meshing options: method={method}, maxvol={maxvol}, isovalue={isovalue}"
            )

            # Auto-method selection
            if method == "auto":
                unique_labels = np.unique(vol_data)
                labelnum = len(unique_labels)
                log_message(f"Auto-detection: found {labelnum} unique labels")

                if labelnum == 2 or labelnum > 64:
                    method = "cgalsurf"
                else:
                    method = "cgalmesh"

                if method == "cgalmesh" and labelnum > 64:
                    vol_data = (vol_data > isovalue).astype(np.uint8)
                    log_message("Converted to binary volume for cgalmesh")

            # Prepare data for meshing
            if method == "cgalmesh":
                vol_data = vol_data.astype(np.uint8)
                isovalue = None  # cgalmesh doesn't use isovalue

            log_message(f"Final method: {method}")
            log_message("Starting mesh generation...")

            # Generate mesh using iso2mesh
            from iso2mesh import v2m, meshreorient

            node, elem, face = v2m(vol_data, isovalue, opt, maxvol, method)

            log_message(
                f"Mesh generated: {len(node)} nodes, {len(elem)} elements, {len(face)} faces"
            )

            # Post-processing: scale mesh and reorient
            node = node[:, :3]  # Keep only x,y,z coordinates
            elem[:, :4] = meshreorient(node, elem[:, :4])

            log_message("Mesh post-processing completed")

            # Save mesh data using BlenderPhotonics format
            self.save_mesh_data(node, elem, outputdir)

            log_message("Mesh generation completed successfully")
            return True

        except Exception as e:
            log_message(f"Error in python_nii2mesh: {str(e)}", "ERROR")
            show_error_message(f"Mesh generation failed: {str(e)}", "Processing Error")
            return False

    def save_mesh_data(self, node, elem, outputdir):
        """
        Python implementation of blendersavemesh functionality
        Saves tetrahedral mesh to JMesh files for region and volume meshes
        """
        from .utils import log_message

        try:
            from iso2mesh import volface, meshface

            # Ensure elem has 5 columns (add region label if missing)
            if elem.shape[1] < 5:
                elem = np.column_stack([elem, np.ones(elem.shape[0], dtype=int)])

            # Create mesh data structure
            meshdata = {
                "_DataInfo_": {
                    "JMeshVersion": "0.5",
                    "Comment": "Created by BlenderPhotonics Python nii2mesh implementation",
                }
            }

            if node.shape[1] == 3:
                meshdata["MeshVertex3"] = node.tolist()
            else:
                meshdata["MeshNode"] = node.tolist()

            outputmesh = meshdata.copy()

            # Process each region
            max_tag = int(np.max(elem[:, 4]))
            log_message(f"Processing {max_tag} region(s)")

            for n in range(1, max_tag + 1):
                # Get elements for this region
                region_elems = elem[elem[:, 4] == n, :4]
                if len(region_elems) > 0:
                    # Extract surface faces for this region
                    fc1, _ = volface(region_elems)
                    outputmesh[f"MeshTri3({n})"] = fc1.tolist()
                    log_message(f"Processed region {n} with {len(fc1)} surface faces")

            # Save region mesh
            log_message("Saving region mesh...")
            jd.save(outputmesh, os.path.join(outputdir, "regionmesh.jmsh"))

            # Generate and save volume mesh (all faces)
            log_message("Saving volume mesh...")
            faces = meshface(elem[:, :4])

            volume_mesh = meshdata.copy()
            volume_mesh["MeshTri3"] = faces.tolist()
            volume_mesh["MeshTet4"] = elem.tolist()
            jd.save(volume_mesh, os.path.join(outputdir, "volumemesh.jmsh"))

            log_message("Mesh saving complete.")

        except Exception as e:
            log_message(f"Error saving mesh: {str(e)}", "ERROR")
            raise e

    def vol2mesh(self):
        if not require_dependency("jdata", "volume to mesh conversion"):
            return

        # Remove last .jmsh file
        outputdir = GetBPWorkFolder()
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)
        if os.path.exists(os.path.join(outputdir, "regionmesh.jmsh")):
            os.remove(os.path.join(outputdir, "regionmesh.jmsh"))
        if os.path.exists(os.path.join(outputdir, "volumemesh.jmsh")):
            os.remove(os.path.join(outputdir, "volumemesh.jmsh"))

        # nii to mesh
        niipath = bpy.context.scene.blender_photonics.path
        print(niipath)
        if len(niipath) == 0:
            return
        jd.save(
            {
                "niipath": niipath,
                "maxvol": self.maxvol,
                "radbound": self.radbound,
                "distbound": self.distbound,
                "isovalue": self.isovalue,
                "imagetype": self.imagetype,
                "method": self.method,
            },
            os.path.join(outputdir, "niipath.json"),
        )

        try:
            # Python implementation of nii2mesh functionality
            result = self.python_nii2mesh(outputdir)
            if not result:
                return

        except Exception as e:
            show_error_message(
                f"Python implementation failed: {str(e)}", "Implementation Error"
            )
            return

        # import volume mesh to blender(just for user to check the result)
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)
        bpy.ops.outliner.orphans_purge(do_recursive=True)

        # Load the generated mesh files
        from .utils import log_message

        try:
            regionmesh_path = os.path.join(outputdir, "regionmesh.jmsh")
            if os.path.exists(regionmesh_path):
                outputmesh = jd.load(regionmesh_path)
                LoadReginalMesh(outputmesh, "region_")
                log_message("Loaded regional mesh for visualization")

            volumemesh_path = os.path.join(outputdir, "volumemesh.jmsh")
            if os.path.exists(volumemesh_path):
                volumemesh = jd.load(volumemesh_path)
                LoadTetMesh(volumemesh, "Iso2Mesh")
                bpy.context.view_layer.objects.active = bpy.data.objects["Iso2Mesh"]
                log_message("Loaded tetrahedral mesh for visualization")

        except Exception as e:
            log_message(f"Error loading mesh for visualization: {str(e)}", "ERROR")
            show_error_message(
                f"Mesh generated but visualization failed: {str(e)}",
                "Visualization Error",
            )

        ShowMessageBox("Mesh generation is complete.", "BlenderPhotonics")

    def execute(self, context):
        self.vol2mesh()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


#
#   Dialog to set meshing properties
#
class setmeshingprop(bpy.types.Panel):
    bl_label = "Mesh extraction setting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global g_maxvol, g_radbound, g_distbound, g_imagetype, g_method
        self.layout.operator("object.dialog_operator")
