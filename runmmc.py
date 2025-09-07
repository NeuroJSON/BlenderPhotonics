"""RunMMC - launch mesh-based Monte Carlo (MMC) simulations using domain configured in Blender

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
import time
from bpy_extras.io_utils import ExportHelper
from .utils import *
from .dependencies import safe_import, require_dependency, show_error_message

# Safe imports
np = safe_import("numpy")
jd = safe_import("jdata")
pmmc = safe_import("pmmc")

g_nphoton = 10000
g_tend = 5e-9
g_tstep = 5e-9
g_method = "grid"
g_outputtype = "flux"
g_isreflect = True
g_isnormalized = True
g_basisorder = 1
g_debuglevel = "TP"
g_gpuid = "1"
g_colormap = "jet"


class runmmc(bpy.types.Operator):
    bl_label = "Run MMC photon simulation"
    bl_description = "Run mesh-based Monte Carlo simulation"
    bl_idname = "blenderphotonics.runmmc"

    # creat a interface to set uesrs' model parameter.

    bl_options = {"REGISTER", "UNDO"}
    nphoton: bpy.props.FloatProperty(default=g_nphoton, name="Photon number")
    tend: bpy.props.FloatProperty(default=g_tend, name="Time gate width (s)")
    tstep: bpy.props.FloatProperty(default=g_tstep, name="Time gate step (s)")
    isreflect: bpy.props.BoolProperty(default=g_isreflect, name="Do reflection")
    isnormalized: bpy.props.BoolProperty(
        default=g_isnormalized, name="Normalize output"
    )
    basisorder: bpy.props.IntProperty(
        default=g_basisorder, step=1, name="Basis order (0 or 1)"
    )
    method: bpy.props.EnumProperty(
        default=g_method,
        name="Raytracer (use elem)",
        items=[
            ("elem", "elem: Saving weight on elements", "Saving weight on elements"),
            ("grid", "grid: Dual-grid MMC", "voxel-based results"),
        ],
    )
    outputtype: bpy.props.EnumProperty(
        default=g_outputtype,
        name="Output quantity",
        items=[
            ("flux", "flux: fluence rate", "fluence rate (J/mm^2/s)"),
            ("fluence", "fluence: fluence (J/mm^2)", "fluence in J/mm^2"),
            ("energy", "energy: energy density J/mm^3", "energy density J/mm^3"),
        ],
    )
    gpuid: bpy.props.StringProperty(default=g_gpuid, name="GPU ID (01 mask,-1=CPU)")
    debuglevel: bpy.props.StringProperty(
        default=g_debuglevel, name="Debug flag [MCBWDIOXATRPE]"
    )
    colormap: bpy.props.StringProperty(default=g_colormap, name="color scheme")

    def preparemmc(self):
        from .utils import log_message

        if not require_dependency("jdata", "MMC simulation preparation"):
            return
        if not require_dependency("numpy", "numerical operations"):
            return

        log_message("Preparing MMC simulation configuration...")

        ## save optical parameters and source source information
        parameters = []  # mu_a, mu_s, n, g

        log_message("Extracting optical parameters from objects...")
        try:
            obj = bpy.data.objects["Iso2Mesh"]
            for prop in obj.data.keys():
                parameters.append(obj.data[prop].to_list())
            log_message(
                f"Loaded {len(parameters)} optical properties from Iso2Mesh object"
            )
        except:
            for i in range(
                len([obj for obj in bpy.data.objects if obj.type == "MESH"])
            ):
                obj = bpy.data.objects["region_" + str(i + 1)]
                if not ("mua" in obj):
                    continue
                parameters.append([obj["mua"], obj["mus"], obj["g"], obj["n"]])
                log_message(f"Loaded optical properties from mesh object: {obj.name}")
            log_message(
                f"Loaded {len(parameters)} optical properties from mesh objects"
            )

        log_message("Configuring light source...")
        obj = bpy.data.objects["Lightsource"]
        location = np.array(obj.location).tolist()
        bpy.context.object.rotation_mode = "QUATERNION"
        direction = np.array(bpy.context.object.rotation_quaternion).tolist()
        srcparam1 = [val for val in obj["srcparam1"]]
        srcparam2 = [val for val in obj["srcparam2"]]

        log_message(f"Light source type: {obj['srctype']}")
        log_message(f"Light source position: {location}")

        mmc_cfg = {
            "srctype": obj["srctype"],
            "srcpos": location,
            "srcdir": direction,
            "srcparam1": srcparam1,
            "srcparam2": srcparam2,
            "nphoton": self.nphoton,
            "unitinmm": obj["unitinmm"],
            "tend": self.tend,
            "tstep": self.tstep,
            "isreflect": self.isreflect,
            "isnormalized": self.isnormalized,
            "method": self.method,
            "outputtype": self.outputtype,
            "basisorder": self.basisorder,
            "debuglevel": self.debuglevel,
            "gpuid": self.gpuid,
        }
        print(obj["srctype"])
        outputdir = GetBPWorkFolder()
        log_message(f"Output directory: {outputdir}")

        # Check if Python-based simulation libraries are available
        if require_dependency("pmmc", "MMC photon simulation"):
            log_message("Using Python-based pmmc for MMC simulation")
        else:
            log_message("pmmc package is required for MMC simulations", "ERROR")
            show_error_message(
                "pmmc package is required for MMC simulations. Please install it using the button in the BlenderPhotonics panel.",
                "Missing Dependency",
            )
            return

        try:
            # Load mesh data (tetrahedral mesh)
            meshfile = os.path.join(outputdir, "volumeTmesh.jmsh")
            log_message(f"Loading tetrahedral mesh from: {meshfile}")
            if not os.path.exists(meshfile):
                log_message(f"Tetrahedral mesh file not found: {meshfile}", "ERROR")
                show_error_message(
                    f"Tetrahedral mesh file not found: {meshfile}",
                    "Missing Mesh File",
                )
                return

            meshdata = jd.load(meshfile)
            log_message(
                f"Loaded mesh with {len(meshdata.get('MeshNode', []))} vertices and {len(meshdata.get('MeshElem', []))} tetrahedra"
            )

            # Pre-processing data - build property matrix
            propbk = [0, 0, 1, 1]  # Background property
            prop = [propbk] + parameters
            log_message(f"Built property matrix with {len(prop)} materials")

            # Convert quaternion to rotation matrix and get direction
            Q = mmc_cfg["srcdir"]
            w, x, y, z = Q[0], Q[1], Q[2], Q[3]

            # Rotation matrix from quaternion
            R = np.array(
                [
                    [
                        1 - 2 * y**2 - 2 * z**2,
                        2 * x * y - 2 * z * w,
                        2 * x * z + 2 * y * w,
                    ],
                    [
                        2 * x * y + 2 * z * w,
                        1 - 2 * x**2 - 2 * z**2,
                        2 * y * z - 2 * x * w,
                    ],
                    [
                        2 * x * z - 2 * y * w,
                        2 * y * z + 2 * x * w,
                        1 - 2 * x**2 - 2 * y**2,
                    ],
                ]
            )

            # Apply rotation to default direction [0, 0, -1]
            direction = R @ np.array([0, 0, -1])
            log_message(f"Calculated light direction: {direction}")

            # ADD node/elem/prop info to MMC configuration
            mmc_cfg["srcdir"] = direction
            mmc_cfg["node"] = meshdata["MeshNode"]
            mmc_cfg["elem"] = np.array(meshdata["MeshElem"])[
                :, :4
            ]  # First 4 columns are tetrahedral indices
            if np.min(mmc_cfg["elem"]) == 0:
                mmc_cfg["elem"] = mmc_cfg["elem"] + 1
            mmc_cfg["elemprop"] = (
                np.array(meshdata["MeshElem"])[:, 4]
                if len(meshdata["MeshElem"][0]) > 4
                else np.ones(len(meshdata["MeshElem"]))
            )
            mmc_cfg["prop"] = prop

            # Handle source position for different source types
            if mmc_cfg["srctype"] in ["pencil", "isotropic", "cone"]:
                log_message("Finding source element for point source...")
                # Find the element containing the source position
                try:
                    from scipy.spatial import Delaunay

                    tri = Delaunay(np.array(mmc_cfg["node"]))
                    simplex = tri.find_simplex(mmc_cfg["srcpos"])
                    if simplex >= 0:
                        mmc_cfg["e0"] = simplex
                        log_message(f"Source located in element {simplex}")
                    else:
                        log_message("Source position outside mesh domain", "WARNING")
                        if mmc_cfg["srctype"] == "pencil":
                            mmc_cfg["e0"] = 0  # Will be handled by pmmc
                except ImportError:
                    log_message(
                        "scipy not available for source element search", "WARNING"
                    )
                    mmc_cfg["e0"] = 0

            # Save MMC configuration for debugging
            log_message("Saving MMC configuration...")
            jd.save(mmc_cfg, os.path.join(outputdir, "mmccfg.json"))

            # Define the heavy computation function for MMC simulation
            def run_mmc_simulation():
                """This function runs in background thread"""
                log_message("Starting MMC simulation... This may take a while...")

                try:
                    flux = pmmc.run(mmc_cfg)
                    log_message("MMC simulation completed successfully!")
                except Exception as e:
                    log_message(f"Error occurred during MMC simulation: {e}", "ERROR")
                    return {
                        "success": False,
                        "error": f"MMC simulation failed: {str(e)}",
                        "method": mmc_cfg["method"],
                    }

                # Check if simulation returned flux data
                if "flux" in flux and mmc_cfg["method"] == "elem":
                    fluxlog = np.log10(flux["flux"] + 1)
                    jd.save(
                        {"fluxlog": fluxlog, "scale": None},
                        os.path.join(outputdir, "MMC_result.json"),
                    )

                    return {
                        "success": True,
                        "fluxlog": fluxlog,
                        "method": mmc_cfg["method"],
                        "scale": None,
                    }
                elif "flux" in flux and mmc_cfg["method"] == "grid":
                    fluxlog = np.log10(
                        flux["flux"][:, :, :, 0] + 1
                    )  # convert -inf to 0 for color

                    jd.save(
                        {"fluxlog": fluxlog, "scale": np.eye(4)},
                        os.path.join(outputdir, "MMC_result.json"),
                    )
                    return {
                        "success": False,
                        "fluxlog": fluxlog,
                        "error": "No flux data returned",
                        "method": mmc_cfg["method"],
                        "scale": np.eye(4),
                    }

            # Define callback function for when MMC simulation completes
            def on_mmc_complete(result):
                """This function runs on main thread when background task completes"""
                try:
                    # Safety check for None result
                    if result is None:
                        log_message(
                            "Error: MMC simulation returned None result", "ERROR"
                        )
                        show_error_message(
                            "MMC simulation failed: No result returned from simulation",
                            "Simulation Error",
                        )
                        return

                    # Load and visualize results
                    # remove all object and import all region as one object
                    log_message("Cleaning up scene and loading results...")
                    for obj in bpy.data.objects:
                        bpy.data.objects.remove(obj)
                    bpy.ops.outliner.orphans_purge(do_recursive=True)

                    if result["method"] == "elem":
                        log_message("Loading region mesh results...")
                        outputmesh = jd.load(
                            os.path.join(outputdir, "volumeTmesh.jmsh")
                        )
                        outputmesh = JMeshFallback(outputmesh)

                        # Ensure proper data types for Blender compatibility
                        if not isinstance(outputmesh["MeshFace"], np.ndarray):
                            outputmesh["MeshFace"] = np.asarray(
                                outputmesh["MeshFace"],
                                dtype=np.int32,  # Use int32 instead of uint32
                            )
                        else:
                            outputmesh["MeshFace"] = outputmesh["MeshFace"].astype(
                                np.int32
                            )

                        # Convert to 0-based indexing and ensure int32
                        if np.min(outputmesh["MeshFace"]) == 1:
                            outputmesh["MeshFace"] = (
                                outputmesh["MeshFace"] - 1
                            ).astype(np.int32)

                        # Convert mesh nodes to float32 for better compatibility
                        mesh_nodes = np.asarray(
                            outputmesh["MeshNode"], dtype=np.float32
                        )
                        mesh_faces = outputmesh["MeshFace"].tolist()

                        log_message(
                            f"Mesh nodes shape: {mesh_nodes.shape}, faces shape: {outputmesh['MeshFace'].shape}"
                        )

                        AddMeshFromNodeFace(
                            mesh_nodes.tolist(),
                            mesh_faces,
                            "MMC_result",
                        )

                        # add color to blender model
                        log_message("Applying simulation results as vertex colors...")
                        obj = bpy.data.objects["MMC_result"]
                        # Use fluxlog data directly from result instead of loading from file
                        fluxlog_data = np.asarray(result["fluxlog"], dtype="float32")
                        log_message(f"Fluxlog data shape: {fluxlog_data.shape}")
                        log_message(f"Mesh vertices count: {len(obj.data.vertices)}")

                        # Flatten fluxlog if it's 2D with single column
                        if fluxlog_data.ndim == 2 and fluxlog_data.shape[1] == 1:
                            fluxlog_data = fluxlog_data.flatten()
                            log_message(
                                f"Flattened fluxlog shape: {fluxlog_data.shape}"
                            )

                        # Ensure we have the right number of flux values for vertices
                        if len(fluxlog_data) != len(obj.data.vertices):
                            log_message(
                                f"Warning: Flux data length ({len(fluxlog_data)}) doesn't match vertex count ({len(obj.data.vertices)})",
                                "WARNING",
                            )
                            # Truncate or pad as needed
                            if len(fluxlog_data) > len(obj.data.vertices):
                                fluxlog_data = fluxlog_data[: len(obj.data.vertices)]
                            else:
                                # Pad with zeros if needed
                                padded_data = np.zeros(
                                    len(obj.data.vertices), dtype=np.float32
                                )
                                padded_data[: len(fluxlog_data)] = fluxlog_data
                                fluxlog_data = padded_data
                            log_message(f"Adjusted fluxlog shape: {fluxlog_data.shape}")

                        color_data = normalize(fluxlog_data)
                        color_bits = 1024
                        color_data = np.rint(color_data * (color_bits - 1))

                        # Ultra-fast vertex color assignment using foreach_set
                        log_message("Assigning vertex colors...")
                        obj = bpy.data.objects["MMC_result"]

                        if "weight" not in obj.vertex_groups:
                            weight_group = obj.vertex_groups.new(name="weight")
                            weight_group.remove(
                                range(len(obj.data.vertices))
                            )  # Clear existing weights
                        else:
                            weight_group = obj.vertex_groups["weight"]

                        for i in range(color_bits + 1):
                            ind = np.array(np.where(color_data == i)).tolist()
                            weight_group.add(ind[0], i / color_bits, "ADD")
                        log_message("Vertex colors assigned successfully")
                        # TODO: switch to weight paint mode

                    elif result["method"] == "grid":
                        log_message("Loading grid-based results...")
                        LoadVolMesh(
                            {"fluxlog": result["fluxlog"], "scale": result["scale"]},
                            "MMCResult",
                            outputdir,
                            mode="result_view",
                            colormap=self.colormap,
                        )
                        log_message("Grid-based MMC result visualization completed")

                    log_message("MMC simulation process completed!")

                except Exception as e:
                    log_message(f"Error in MMC completion callback: {str(e)}", "ERROR")
                    show_error_message(
                        f"Error in MMC completion: {str(e)}", "Completion Error"
                    )

            # Import background threading utility
            from .utils import run_in_background

            # Start background MMC simulation
            success = run_in_background(
                run_mmc_simulation,
                callback=on_mmc_complete,
                thread_name="mmc_simulation",
            )

            if success:
                log_message(
                    "MMC simulation started in background. Blender UI remains responsive."
                )
                log_message("Use 'Show Log Window' to monitor progress.")
            else:
                log_message("Another MMC simulation is already running", "WARNING")

        except Exception as e:
            error_msg = f"Error in MMC simulation setup: {str(e)}"
            log_message(error_msg, "ERROR")
            show_error_message(error_msg, "Setup Error")

        log_message("MMC simulation process completed!")

    def execute(self, context):
        from .utils import log_message, clear_log

        # Clear previous log and start new simulation log
        clear_log()
        log_message("Starting MMC (Mesh-based Monte Carlo) simulation...")
        log_message(f"Configuration: {self.nphoton} photons, method: {self.method}")
        print("=== BlenderPhotonics: Starting MMC simulation ===")
        print("Tip: Use 'Show Log Window' button to view detailed progress")

        print("Begin to run MMC source transport simulation ...")
        self.preparemmc()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ExportMMCResult(bpy.types.Operator, ExportHelper):
    """Export MMC simulation results to JSON file"""

    bl_idname = "blenderphotonics.export_mmc_result"
    bl_label = "Export MMC Results"
    bl_description = "Export MMC simulation configuration and flux data to JSON file"
    bl_options = {"REGISTER", "UNDO"}

    # Required by ExportHelper
    filename_ext = ".json"

    # Simple file path selector with MMC default
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Choose export file path",
        subtype="FILE_PATH",
        default="MMC_Simulation_Result.json",
    )

    def execute(self, context):
        from .utils import log_message, GetBPWorkFolder

        if not require_dependency("jdata", "result export"):
            return {"CANCELLED"}

        log_message("Starting MMC result export...")

        # Check if MMC_result.json exists
        outputdir = GetBPWorkFolder()
        mmc_result_path = os.path.join(outputdir, "MMC_result.json")
        mmc_cfg_path = os.path.join(outputdir, "mmccfg.json")

        if not os.path.exists(mmc_result_path):
            show_error_message(
                "MMC_result.json not found. Please run a PMMC simulation first.",
                "Export Error",
            )
            log_message("Export failed: MMC_result.json not found", "ERROR")
            return {"CANCELLED"}

        if not os.path.exists(mmc_cfg_path):
            show_error_message(
                "mmccfg.json not found. Please run a PMMC simulation first.",
                "Export Error",
            )
            log_message("Export failed: mmccfg.json not found", "ERROR")
            return {"CANCELLED"}

        try:
            log_message("Loading MMC simulation results...")
            # Load the MMC result data
            mmc_result = jd.load(mmc_result_path)
            log_message("Loading MMC configuration...")
            # Load the MMC configuration
            mmc_cfg = jd.load(mmc_cfg_path)

            # Helper function to convert numpy arrays to lists for JSON serialization
            def convert_numpy_to_list(obj):
                if hasattr(obj, "tolist"):  # numpy array
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {
                        key: convert_numpy_to_list(value) for key, value in obj.items()
                    }
                elif isinstance(obj, list):
                    return [convert_numpy_to_list(item) for item in obj]
                else:
                    return obj

            # Prepare export data and convert numpy arrays
            export_data = {
                "mmc_cfg": convert_numpy_to_list(mmc_cfg),
                "flux": convert_numpy_to_list(
                    mmc_result.get("fluxlog", None)
                ),  # Use fluxlog from result
                "metadata": {
                    "export_timestamp": time.time(),
                    "export_version": "1.0",
                    "blenderphotonics_version": "2025",
                    "description": "MMC simulation results exported from BlenderPhotonics",
                },
            }

            # If fluxlog is not available, try to get flux data from result
            if export_data["flux"] is None and "flux" in mmc_result:
                export_data["flux"] = convert_numpy_to_list(mmc_result["flux"])
                log_message("Using flux data from MMC result")

            log_message(f"Saving export data to: {self.filepath}")

            # Check if filepath has .json extension, add it if missing
            export_path = self.filepath
            if not export_path.lower().endswith(".json"):
                export_path += ".json"
                log_message(f"Added .json extension: {export_path}")

            # Simply pass the corrected path to jdata
            jd.save(export_data, export_path)

            log_message("✓ MMC results exported successfully!", "SUCCESS")
            show_error_message(
                f"MMC results exported successfully to:\n{export_path}",
                "Export Complete",
            )

        except Exception as e:
            error_msg = f"Failed to export MMC results: {str(e)}"
            log_message(error_msg, "ERROR")
            show_error_message(error_msg, "Export Error")
            return {"CANCELLED"}

        return {"FINISHED"}

    def invoke(self, context, event):
        from .utils import log_message, GetBPWorkFolder

        # Check if required files exist before opening dialog
        outputdir = GetBPWorkFolder()
        mmc_result_path = os.path.join(outputdir, "MMC_result.json")
        mmc_cfg_path = os.path.join(outputdir, "mmccfg.json")

        if not os.path.exists(mmc_result_path):
            show_error_message(
                "MMC_result.json not found. Please run a PMMC simulation first.",
                "Export Error",
            )
            log_message("Export cancelled: MMC_result.json not found", "ERROR")
            return {"CANCELLED"}

        if not os.path.exists(mmc_cfg_path):
            show_error_message(
                "mmccfg.json not found. Please run a PMMC simulation first.",
                "Export Error",
            )
            log_message("Export cancelled: mmccfg.json not found", "ERROR")
            return {"CANCELLED"}

        # Open file selection dialog
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


#
#   Dialog to set meshing properties
#
class setmmcprop(bpy.types.Panel):
    bl_label = "MMC Simulation Setting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global g_nphoton, g_tend, g_tstep, g_method, g_outputtype, g_isreflect, g_isnormalized, g_basisorder, g_debuglevel, g_gpuid
        self.layout.operator("object.dialog_operator")
