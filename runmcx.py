"""RunPMCX - launch Monte Carlo eXtreme (MCX) simulations using domain configured in Blender

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
pmcx = safe_import("pmcx")

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


class runmcx(bpy.types.Operator):
    bl_label = "Run PMCX photon simulation"
    bl_description = "Run Monte Carlo eXtreme (MCX) simulation"
    bl_idname = "blenderphotonics.run_pmcx"

    # create a interface to set users' model parameter.

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
        name="Raytracer (use grid)",
        items=[
            (
                "elem",
                "elem: Saving weight on elements (not supported)",
                "Saving weight on elements",
            ),
            ("grid", "grid: Grid-based MCX", "Grid-based MCX"),
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

    def preparepmcx(self):
        from .utils import log_message

        if not require_dependency("jdata", "MCX simulation preparation"):
            return
        if not require_dependency("numpy", "numerical operations"):
            return

        log_message("Preparing PMCX simulation configuration...")

        ## save optical parameters and source source information
        parameters = []  # mu_a, mu_s, n, g

        outputdir = GetBPWorkFolder()
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)
        log_message(f"Output directory: {outputdir}")

        if os.path.exists(os.path.join(outputdir, "mcxinfo.json")):
            os.remove(os.path.join(outputdir, "mcxinfo.json"))

        log_message("Extracting optical parameters from objects...")
        if "Iso2Mesh" in bpy.data.objects:
            obj = bpy.data.objects["Iso2Mesh"]
            for prop in obj.data.keys():
                parameters.append(obj.data[prop].to_list())
            log_message(
                f"Loaded {len(parameters)} optical properties from Iso2Mesh object"
            )
        elif "NiiSetup_nii" in bpy.data.objects:
            obj = bpy.data.objects["NiiSetup_nii"]
            for prop in obj.data.keys():
                parameters.append(obj.data[prop].to_list())
            log_message(
                f"Loaded {len(parameters)} optical properties from NiiSetup_nii object"
            )
        else:
            for obj in [obj for obj in bpy.data.objects if obj.type == "MESH"]:
                if not ("mua" in obj):
                    log_message(f"Mesh object missing optical properties: {obj.name}")
                    continue
                parameters.append([obj["mua"], obj["mus"], obj["g"], obj["n"]])
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

        if require_dependency("pmcx", "PMCX simulation"):
            log_message("Using python-based pmcx for MCX simulation")

            meshfile = os.path.join(outputdir, "imageVmesh.jmsh")
            log_message(f"Loading volume mesh from: {meshfile}")
            if not os.path.exists(meshfile):
                log_message(f"Mesh file not found: {meshfile}", "ERROR")
                return
            else:
                meshdata = jd.load(meshfile)
                vol = meshdata["ImageMesh"]
                affine_matrix = meshdata["ImageScale"]
                move = np.array(
                    [affine_matrix[0, 3], affine_matrix[1, 3], affine_matrix[2, 3]]
                )
                scale = np.array(
                    [affine_matrix[0, 0], affine_matrix[1, 1], affine_matrix[2, 2]]
                )
                log_message(f"Loaded volume mesh with shape: {np.array(vol).shape}")
                log_message(f"Volume scale: {scale}, offset: {move}")

            # Pre-processing data - build property matrix
            propbk = [0, 0, 1, 1]  # Background property
            prop = [propbk] + parameters
            log_message(f"Built property matrix with {len(prop)} materials")

            # Convert quaternion to rotation matrix and get direction
            Q = direction
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
        else:
            log_message("pmcx is not installed, please install it first", "ERROR")
            return

        mcx_cfg = {
            "vol": vol,
            "prop": prop,
            "srctype": obj["srctype"],
            "srcpos": (location - move) / scale,
            "srcdir": direction,
            "srcparam1": srcparam1 / np.append(scale, [1]),
            "srcparam2": srcparam2 / np.append(scale, [1]),
            "nphoton": self.nphoton,
            "srctype": obj["srctype"],
            "unitinmm": obj["unitinmm"] * scale[0],
            "tstart": 0,
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
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)

        # Save MCX configuration for debugging
        log_message("Saving MCX configuration...")
        jd.save(mcx_cfg, os.path.join(outputdir, "mcxcfg.json"))

        # Define the heavy computation function for MCX simulation
        def run_mcx_simulation():
            """This function runs in background thread"""
            log_message("Starting MCX simulation... This may take a while...")
            log_message(f"Simulating {self.nphoton} photons with {self.method} method")

            flux = pmcx.run(mcx_cfg)

            # Post-processing simulation result
            if "flux" in flux:
                log_message("Processing simulation results...")
                fluxlog = np.log10(
                    flux["flux"][:, :, :, 0] / flux["stat"]["normalizer"] + 1
                )  # convert -inf to 0 for color

                # Save for grid-based method
                jd.save(
                    {"fluxlog": fluxlog, "scale": meshdata["ImageScale"]},
                    os.path.join(outputdir, "MCX_result.json"),
                )
                log_message("✓ MCX grid simulation completed!", "SUCCESS")

                return {
                    "success": True,
                    "flux": flux,
                    "fluxlog": fluxlog,
                    "scale": meshdata["ImageScale"],
                }
            else:
                log_message(
                    "MCX simulation completed but no flux data was returned", "WARNING"
                )
                return {"success": False, "error": "No flux data returned"}

        # Define callback function for when MCX simulation completes
        def on_mcx_complete(result):
            """This function runs on main thread when background task completes"""
            try:
                if result["success"]:
                    show_error_message(
                        "MCX simulation completed successfully! Results saved to MCX_result.json",
                        "Simulation Complete",
                    )

                    # remove all object and import all region as one object
                    log_message("Cleaning up scene and loading results...")
                    for obj in bpy.data.objects:
                        bpy.data.objects.remove(obj)
                    bpy.ops.outliner.orphans_purge(do_recursive=True)

                    # visualize results
                    log_message("Loading visualization results...")
                    LoadVolMesh(
                        {"fluxlog": result["fluxlog"], "scale": result["scale"]},
                        "MCXResult",
                        outputdir,
                        mode="result_view",
                        colormap=self.colormap,
                    )
                    log_message("MCX simulation process completed!")
                else:
                    show_error_message(
                        f"MCX simulation failed: {result.get('error', 'Unknown error')}",
                        "Simulation Warning",
                    )
            except Exception as e:
                log_message(f"Error in MCX completion callback: {str(e)}", "ERROR")
                show_error_message(
                    f"Error in MCX completion: {str(e)}", "Completion Error"
                )

        # Import background threading utility
        from .utils import run_in_background

        # Start background MCX simulation
        success = run_in_background(
            run_mcx_simulation, callback=on_mcx_complete, thread_name="mcx_simulation"
        )

        if success:
            log_message(
                "MCX simulation started in background. Blender UI remains responsive."
            )
            log_message("Use 'Show Log Window' to monitor progress.")
        else:
            log_message("Another MCX simulation is already running", "WARNING")

    def execute(self, context):
        from .utils import log_message, clear_log

        # Clear previous log and start new simulation log
        clear_log()
        log_message("Starting PMCX (Monte Carlo eXtreme) simulation...")
        log_message(f"Configuration: {self.nphoton} photons, method: {self.method}")
        print("=== BlenderPhotonics: Starting PMCX simulation ===")
        print("Tip: Use 'Show Log Window' button to view detailed progress")

        print("Begin to run PMCX photon transport simulation ...")
        self.preparepmcx()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ExportMCXResult(bpy.types.Operator, ExportHelper):
    """Export MCX simulation results to JSON file"""

    bl_idname = "blenderphotonics.export_mcx_result"
    bl_label = "Export MCX Results"
    bl_description = "Export MCX simulation configuration and flux data to JSON file"
    bl_options = {"REGISTER", "UNDO"}

    # Required by ExportHelper
    filename_ext = ".json"

    # Simple file path selector - no extension filtering
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Choose export file path",
        subtype="FILE_PATH",
        default="MCX_Simulation_Result.json",
    )

    def execute(self, context):
        from .utils import log_message, GetBPWorkFolder

        if not require_dependency("jdata", "result export"):
            return {"CANCELLED"}

        log_message("Starting MCX result export...")

        # Check if MCX_result.json exists
        outputdir = GetBPWorkFolder()
        mcx_result_path = os.path.join(outputdir, "MCX_result.json")
        mcx_cfg_path = os.path.join(outputdir, "mcxcfg.json")

        if not os.path.exists(mcx_result_path):
            show_error_message(
                "MCX_result.json not found. Please run a PMCX simulation first.",
                "Export Error",
            )
            log_message("Export failed: MCX_result.json not found", "ERROR")
            return {"CANCELLED"}

        if not os.path.exists(mcx_cfg_path):
            show_error_message(
                "mcxcfg.json not found. Please run a PMCX simulation first.",
                "Export Error",
            )
            log_message("Export failed: mcxcfg.json not found", "ERROR")
            return {"CANCELLED"}

        try:
            log_message("Loading MCX simulation results...")
            # Load the MCX result data
            mcx_result = jd.load(mcx_result_path)
            log_message("Loading MCX configuration...")
            # Load the MCX configuration
            mcx_cfg = jd.load(mcx_cfg_path)

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
                "mcx_cfg": convert_numpy_to_list(mcx_cfg),
                "flux": convert_numpy_to_list(
                    mcx_result.get("fluxlog", None)
                ),  # Use fluxlog from result
                "metadata": {
                    "export_timestamp": time.time(),
                    "export_version": "1.0",
                    "blenderphotonics_version": "2025",
                    "description": "MCX simulation results exported from BlenderPhotonics",
                },
            }

            # If fluxlog is not available, try to get flux data from result
            if export_data["flux"] is None and "flux" in mcx_result:
                export_data["flux"] = convert_numpy_to_list(mcx_result["flux"])
                log_message("Using flux data from MCX result")

            log_message(f"Saving export data to: {self.filepath}")

            # Check if filepath has .json extension, add it if missing
            export_path = self.filepath
            if not export_path.lower().endswith(".json"):
                export_path += ".json"
                log_message(f"Added .json extension: {export_path}")

            # Simply pass the corrected path to jdata
            jd.save(export_data, export_path)

            log_message("✓ MCX results exported successfully!", "SUCCESS")
            show_error_message(
                f"MCX results exported successfully to:\n{export_path}",
                "Export Complete",
            )

        except Exception as e:
            error_msg = f"Failed to export MCX results: {str(e)}"
            log_message(error_msg, "ERROR")
            show_error_message(error_msg, "Export Error")
            return {"CANCELLED"}

        return {"FINISHED"}

    def invoke(self, context, event):
        from .utils import log_message, GetBPWorkFolder

        # Check if required files exist before opening dialog
        outputdir = GetBPWorkFolder()
        mcx_result_path = os.path.join(outputdir, "MCX_result.json")
        mcx_cfg_path = os.path.join(outputdir, "mcxcfg.json")

        if not os.path.exists(mcx_result_path):
            show_error_message(
                "MCX_result.json not found. Please run a PMCX simulation first.",
                "Export Error",
            )
            log_message("Export cancelled: MCX_result.json not found", "ERROR")
            return {"CANCELLED"}

        if not os.path.exists(mcx_cfg_path):
            show_error_message(
                "mcxcfg.json not found. Please run a PMCX simulation first.",
                "Export Error",
            )
            log_message("Export cancelled: mcxcfg.json not found", "ERROR")
            return {"CANCELLED"}

        # Open file selection dialog
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


#
#   Dialog to set PMCX simulation properties
#
class setpmcxprop(bpy.types.Panel):
    bl_label = "PMCX Simulation Setting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global g_nphoton, g_tend, g_tstep, g_method, g_outputtype, g_isreflect, g_isnormalized, g_basisorder, g_debuglevel, g_gpuid
        self.layout.operator("object.dialog_operator")
