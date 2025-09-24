"""BlenderPhotonics Utilities/Helper Functions

* Authors: (c) 2021-2022 Qianqian Fang <q.fang at neu.edu>
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
import math
import os
import tempfile
import copy
import time
import threading
from .dependencies import safe_import, require_dependency, show_error_message

# Safe imports with fallbacks
np = safe_import("numpy")
import openvdb as vdb  # OpenVDB is included in Blender by default

jd = safe_import("jdata")
iso2mesh = safe_import("iso2mesh")
pmcx = safe_import("pmcx")
pmmc = safe_import("pmmc")

# Global variable to store log messages
_log_messages = []
_log_window_open = False
_active_threads = {}  # Track active background threads


def ShowMessageBox(message="", title="Message Box", icon="INFO"):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


# Threading utilities for non-blocking operations
def run_in_background(
    func, args=(), kwargs={}, callback=None, thread_name="background_task"
):
    """
    Run a function in a background thread to prevent UI freezing

    Args:
        func: Function to run in background
        args: Arguments for the function
        kwargs: Keyword arguments for the function
        callback: Function to call when background task completes
        thread_name: Name for the thread (for tracking)
    """

    def wrapper():
        try:
            log_message(f"Starting background task: {thread_name}")
            result = func(*args, **kwargs)
            log_message(f"Background task completed: {thread_name}")

            # Schedule callback on main thread if provided
            if callback:
                bpy.app.timers.register(lambda: callback(result), first_interval=0.1)

        except Exception as e:
            error_msg = f"Background task failed: {thread_name} - {str(e)}"
            log_message(error_msg, "ERROR")
            bpy.app.timers.register(
                lambda: show_error_message(error_msg, "Background Task Error"),
                first_interval=0.1,
            )
        finally:
            # Remove from active threads
            if thread_name in _active_threads:
                del _active_threads[thread_name]

    # Check if thread is already running
    if thread_name in _active_threads and _active_threads[thread_name].is_alive():
        log_message(f"Background task already running: {thread_name}", "WARNING")
        return False

    # Start new thread
    thread = threading.Thread(target=wrapper, name=thread_name)
    thread.daemon = True  # Dies when main thread dies
    _active_threads[thread_name] = thread
    thread.start()
    return True


def is_background_task_running(thread_name):
    """Check if a specific background task is still running"""
    return thread_name in _active_threads and _active_threads[thread_name].is_alive()


def get_active_background_tasks():
    """Get list of currently running background tasks"""
    active = []
    for name, thread in _active_threads.items():
        if thread.is_alive():
            active.append(name)
    return active


# Logger functions for popup terminal
def clear_log():
    """Clear all log messages"""
    global _log_messages
    _log_messages = []


def log_message(message, level="INFO"):
    """Add a message to the log with timestamp"""
    global _log_messages
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    log_entry = f"[{timestamp}] {level}: {message}"
    _log_messages.append(log_entry)
    print(log_entry)  # Also print to console


def get_log_messages():
    """Get all log messages"""
    global _log_messages
    return _log_messages


def show_log_popup():
    """Show the log popup window"""
    global _log_window_open
    if not _log_window_open:
        try:
            # Check if the operator is available
            if hasattr(bpy.ops, "blenderphotonics") and hasattr(
                bpy.ops.blenderphotonics, "show_log_window"
            ):
                bpy.ops.blenderphotonics.show_log_window("INVOKE_DEFAULT")
            else:
                raise RuntimeError("Log window operator not registered")
        except Exception as e:
            print(f"Warning: Could not show log popup window: {e}")
            # Fallback: just print the current messages to console
            messages = get_log_messages()
            if messages:
                print("=== BlenderPhotonics Log Messages ===")
                for msg in messages:
                    print(msg)
                print("======================================")
            else:
                print("=== BlenderPhotonics: No log messages yet ===")


class BLENDERPHOTONICS_OT_show_log_window(bpy.types.Operator):
    """Show BlenderPhotonics log window"""

    bl_idname = "blenderphotonics.show_log_window"
    bl_label = "BlenderPhotonics Log"
    bl_options = {"REGISTER"}

    def execute(self, context):
        global _log_window_open
        _log_window_open = False
        return {"FINISHED"}

    def invoke(self, context, event):
        global _log_window_open
        _log_window_open = True
        return context.window_manager.invoke_props_dialog(self, width=600)

    def cancel(self, context):
        global _log_window_open
        _log_window_open = False
        return {"CANCELLED"}

    def draw(self, context):
        layout = self.layout

        # Title
        layout.label(text="BlenderPhotonics Operations Log", icon="CONSOLE")
        layout.separator()

        # Log messages area
        box = layout.box()
        col = box.column()

        messages = get_log_messages()
        if not messages:
            col.label(text="No log messages yet...")
        else:
            # Show last 20 messages to avoid UI overflow
            for message in messages[-20:]:
                # Split long messages if needed
                if len(message) > 80:
                    words = message.split()
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 80:
                            current_line += word + " "
                        else:
                            if current_line:
                                col.label(text=current_line.strip())
                            current_line = word + " "
                    if current_line:
                        col.label(text=current_line.strip())
                else:
                    col.label(text=message)

        layout.separator()

        # Control buttons
        row = layout.row()
        row.operator("blenderphotonics.clear_log", text="Clear Log", icon="TRASH")
        row.operator(
            "blenderphotonics.refresh_log", text="Refresh", icon="FILE_REFRESH"
        )


class BLENDERPHOTONICS_OT_clear_log(bpy.types.Operator):
    """Clear the log messages"""

    bl_idname = "blenderphotonics.clear_log"
    bl_label = "Clear Log"
    bl_options = {"REGISTER"}

    def execute(self, context):
        clear_log()
        log_message("Log cleared by user")
        return {"FINISHED"}


class BLENDERPHOTONICS_OT_refresh_log(bpy.types.Operator):
    """Refresh the log window"""

    bl_idname = "blenderphotonics.refresh_log"
    bl_label = "Refresh Log"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # Force UI update
        for area in bpy.context.screen.areas:
            area.tag_redraw()
        return {"FINISHED"}


def GetNodeFacefromObject(obj, istrimesh=True):
    if not require_dependency("numpy", "mesh operations"):
        return None

    verts = []
    for n in range(len(obj.data.vertices)):
        vert = obj.data.vertices[n].co
        v_global = obj.matrix_world @ vert
        verts.append(v_global)
    # edges = [edge.vertices[:] for edge in obj.data.edges]
    faces = [(np.array(face.vertices[:]) + 1).tolist() for face in obj.data.polygons]
    v = np.array(verts)
    try:
        f = np.array(faces)
        return {"MeshVertex3": v, "MeshTri3": f}
    except:
        f = faces
    return {
        "_DataInfo_": {"BlenderObjectName", obj.name},
        "MeshVertex3": v,
        "MeshPoly": f,
    }


def AddMeshFromNodeFace(node, face, name):

    # Create mesh and related object
    my_mesh = bpy.data.meshes.new(name)
    my_obj = bpy.data.objects.new(name, my_mesh)

    # Set object location in 3D space
    my_obj.location = bpy.context.scene.cursor.location

    # check if "BlenderPhotonics" collection is exit
    if "BlenderPhotonics" not in bpy.context.scene.collection.children:
        rootcoll = bpy.data.collections.new("BlenderPhotonics")
        bpy.context.scene.collection.children.link(rootcoll)
    else:
        rootcoll = bpy.context.scene.collection.children.get("BlenderPhotonics")

    # Link object to the scene collection
    rootcoll.objects.link(my_obj)

    # Create object using blender function
    my_mesh.from_pydata(node, [], face)
    my_mesh.update(calc_edges=True)


def GetBPWorkFolder():
    if os.name == "nt":
        return os.path.join(
            tempfile.gettempdir(),
            "iso2mesh-" + os.environ.get("UserName"),
            "blenderphotonics",
        )
    else:
        return os.path.join(
            tempfile.gettempdir(),
            "iso2mesh-" + os.environ.get("USER"),
            "blenderphotonics",
        )


def LoadReginalMesh(meshdata, name):
    if not require_dependency("numpy", "mesh loading operations"):
        return None

    n = len(meshdata.keys()) - 2

    for i in range(0, n):
        print("Loading regional mesh:", name + str(i + 1))
        surfkey = "MeshTri3(" + str(i + 1) + ")"
        if not isinstance(meshdata[surfkey], np.ndarray):
            meshdata[surfkey] = np.asarray(meshdata[surfkey], dtype=np.uint32)
        meshdata[surfkey] -= 1
        AddMeshFromNodeFace(
            meshdata["MeshVertex3"], meshdata[surfkey].tolist(), name + str(i + 1)
        )

    return


def LoadTetMesh(meshdata, name):
    if not require_dependency("numpy", "tetrahedral mesh loading"):
        return None

    if not isinstance(meshdata["MeshTri3"], np.ndarray):
        meshdata["MeshTri3"] = np.asarray(meshdata["MeshTri3"], dtype=np.uint32)
    meshdata["MeshTri3"] -= 1
    AddMeshFromNodeFace(meshdata["MeshVertex3"], meshdata["MeshTri3"].tolist(), name)


def JMeshFallback(meshobj):
    if ("MeshSurf" in meshobj) and (not ("MeshTri3" in meshobj)):
        meshobj["MeshTri3"] = meshobj.pop("MeshSurf")
    if ("MeshNode" in meshobj) and (not ("MeshVertex3" in meshobj)):
        meshobj["MeshVertex3"] = meshobj.pop("MeshNode")
    return meshobj


def normalize(x):
    if not require_dependency("numpy", "data normalization"):
        return x
    x = (x - np.min(x)) / (np.max(x) - np.min(x))
    return x


def ConvertMat2Vdb(meshdata, name, path, mode):
    if not require_dependency("numpy", "volume data conversion"):
        return None, 0, 1

    if (not isinstance(meshdata, np.ndarray)) or not meshdata.dtype == np.float32:
        meshdata = np.asarray(meshdata, dtype=np.float32)
    if mode == "model_view" :
        mesh = meshdata
    elif mode == "result_view" or mode == "nii_view":
        mesh = meshdata.transpose(2, 1, 0)
    grid_list = []
    model = vdb.FloatGrid()
    mesh = normalize(mesh)
    model.copyFromArray(mesh)
    model.name = "density"
    grid_list.append(model)
    if mode == "model_view":
        digit = int(math.log((int(mesh.max() + 1 - int(mesh.min()))), 10) + 1)
        for index in range(int(mesh.min()), int(mesh.max() + 1)):
            grid = vdb.FloatGrid()
            grid.name = str(int(index) + 1).rjust(digit, "0")
            grid.copyFromArray(mesh == index)
            grid = copy.deepcopy(grid)
            grid_list.append(grid)
        filename = os.path.join(path, "Iso2Mesh.vdb")
    elif mode == "result_view":
        filename = os.path.join(path, f"{name}.vdb")
        digit = 1
    elif mode == "nii_view":
        unique_vals, _ = np.unique(
            meshdata, return_inverse=True
        )  # unique_vals: region labels
        digit = int(math.log(len(unique_vals), 10) + 1)
        for i, val in enumerate(unique_vals):
            grid = vdb.FloatGrid()
            grid.name = "region_" + str(int(i) + 1).rjust(digit, "0")
            grid.copyFromArray(mesh == val)
            grid = copy.deepcopy(grid)
            grid_list.append(grid)
        filename = os.path.join(path, name + "_nii.vdb")
    vdb.write(filename, grids=grid_list)
    return filename, len(grid_list) - 1, digit


def LoadVolMesh(mesh_np, id, path, mode, colormap="jet"):
    if not require_dependency("numpy", "volume mesh loading"):
        return

    if mode == "model_view":
        filename, region_n, digit = ConvertMat2Vdb(mesh_np["image"], id, path, mode)
        if filename is None:
            return
        try:
            bpy.data.materials["model_material"]
        except:
            AddMaterial(
                id="model_material", alpha=0.05, r_number=region_n, colormap_id=colormap
            )

    elif mode == "result_view":
        filename, region_n, digit = ConvertMat2Vdb(mesh_np["fluxlog"], id, path, mode)
        if filename is None:
            return
        try:
            bpy.data.materials["mcx_material"]
        except:
            AddMaterial(id="mcx_material", alpha=0.05, colormap_id=colormap)

    elif mode == "nii_view":
        filename, region_n, digit = ConvertMat2Vdb(mesh_np["NIFTIData"], id, path, mode)
        if filename is None:
            return
        try:
            bpy.data.materials["nii_material"]
        except:
            AddMaterial(id="nii_material", alpha=0.05, colormap_id=colormap)
    bpy.ops.object.volume_import(filepath=filename, align="WORLD")

    if mode == "model_view":
        obj = bpy.data.objects["Iso2Mesh"]
        for ind in range(region_n):
            obj.data["Optical_prop_" + str(ind + 1).rjust(digit, "0")] = [
                0.001,
                0.1,
                0.0,
                1.37,
            ]
        obj.data.materials.append(bpy.data.materials["model_material"])
    elif mode == "result_view":
        obj = bpy.data.objects[id]
        obj.data.materials.append(bpy.data.materials["mcx_material"])

    elif mode == "nii_view":
        obj = bpy.data.objects[id + "_nii"]
        for ind in range(region_n):
            obj.data["Optical_prop_" + str(ind + 1).rjust(digit, "0")] = [
                0.001,
                0.1,
                0.0,
                1.37,
            ]
        obj.data.materials.append(bpy.data.materials["nii_material"])

    obj.scale = [mesh_np["scale"][0, 0], mesh_np["scale"][1, 1], mesh_np["scale"][2, 2]]
    obj.location.x += mesh_np["scale"][0, 3]
    obj.location.y += mesh_np["scale"][1, 3]
    obj.location.z += mesh_np["scale"][2, 3]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    if mode == "result_view" or mode == "nii_view":
        bpy.ops.transform.rotate(value=-math.pi / 2, orient_axis="Y")
        bpy.ops.transform.mirror(
            orient_type="GLOBAL",
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type="GLOBAL",
            constraint_axis=(False, False, True),
        )

    bpy.context.scene.render.engine = "CYCLES"
    try:
        bpy.context.scene.cycles.device = "GPU"
    except:
        pass
    AdjestWorld()

    # Only set shading type if we have access to space_data (UI context available)
    try:
        if bpy.context.space_data and hasattr(bpy.context.space_data, "shading"):
            bpy.context.space_data.shading.type = "RENDERED"
        else:
            log_message("UI context not available - skipping viewport shading change")
    except AttributeError:
        log_message("Could not set viewport shading - UI context not available")


def AddMaterial(id, alpha, r_number=1, colormap_id="jet"):
    if not require_dependency("jdata", "material creation"):
        return

    bpy.data.materials.new(name=id)
    color_assert_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "colormap_assest.json"
    )

    try:
        colorlist = jd.load(color_assert_path)["colormap"][colormap_id]
    except Exception as e:
        show_error_message(f"Failed to load colormap: {str(e)}", "Colormap Error")
        return

    color = [(int(color_HEX, 16), alpha) for color_HEX in colorlist]

    def to_blender_color(c):  # gamma correction
        c = min(max(0, c), 255) / 255
        return c / 12.92 if c < 0.04045 else math.pow((c + 0.055) / 1.055, 2.4)

    blend_color = [
        (
            to_blender_color(c[0] >> 16),
            to_blender_color(c[0] >> 8 & 0xFF),
            to_blender_color(c[0] & 0xFF),
            c[1],
        )
        for c in color
    ]
    color_count = len(color)

    mat = bpy.data.materials[id]  # choose material name here
    mat.use_nodes = True

    tree = mat.node_tree
    nodes = tree.nodes
    mat.node_tree.nodes.clear()

    if id == "model_material":
        node1 = nodes.new(type="ShaderNodeVolumeInfo")
        node2 = nodes.new(type="ShaderNodeValToRGB")  # add color ramp node
        node3 = nodes.new(type="ShaderNodeVolumePrincipled")
        node4 = nodes.new(type="ShaderNodeOutputMaterial")
        node5 = nodes.new(type="ShaderNodeMapRange")
        tree.links.new(node1.outputs["Density"], node5.inputs["Value"])
        tree.links.new(node5.outputs["Result"], node2.inputs["Fac"])
        tree.links.new(node2.outputs["Color"], node3.inputs["Color"])
        tree.links.new(node2.outputs["Alpha"], node3.inputs["Density"])
        tree.links.new(node3.outputs[0], node4.inputs[1])
        tree.links.new(node2.outputs["Color"], node3.inputs["Emission Color"])
        tree.links.new(node5.outputs["Result"], node3.inputs["Emission Strength"])
        node5.inputs["From Max"].default_value = r_number

    elif id == "mcx_material":
        # add render material part nodes
        node1 = nodes.new(type="ShaderNodeVolumeInfo")
        node2 = nodes.new(type="ShaderNodeValToRGB")  # add color ramp node
        node3 = nodes.new(type="ShaderNodeVolumePrincipled")
        node4 = nodes.new(type="ShaderNodeOutputMaterial")
        node5 = nodes.new(type="ShaderNodeMath")
        node5.operation = "MULTIPLY"
        node5.inputs[1].default_value = 1
        # link render material part
        tree.links.new(node1.outputs["Density"], node5.inputs[0])
        tree.links.new(node5.outputs["Value"], node2.inputs["Fac"])
        tree.links.new(node2.outputs["Color"], node3.inputs["Color"])
        tree.links.new(node2.outputs["Alpha"], node3.inputs["Density"])
        tree.links.new(node3.outputs[0], node4.inputs[1])
        tree.links.new(node2.outputs["Color"], node3.inputs["Emission Color"])
        tree.links.new(node5.outputs["Value"], node3.inputs["Emission Strength"])
        # add slice material part nodes
        node6 = nodes.new(type="ShaderNodeNewGeometry")
        node7 = nodes.new(type="ShaderNodeSeparateXYZ")
        node8 = nodes.new(type="ShaderNodeMapRange")
        node8.interpolation_type = "STEPPED"
        node8.inputs[5].default_value = 1
        # link render material part
        tree.links.new(node6.outputs["Position"], node7.inputs["Vector"])
        tree.links.new(node7.outputs["X"], node8.inputs["Value"])

    elif id == "nii_material":
        # add render material part nodes
        node1 = nodes.new(type="ShaderNodeVolumeInfo")
        node2 = nodes.new(type="ShaderNodeValToRGB")  # add color ramp node
        node3 = nodes.new(type="ShaderNodeVolumePrincipled")
        node4 = nodes.new(type="ShaderNodeOutputMaterial")
        node5 = nodes.new(type="ShaderNodeMath")
        node5.operation = "MULTIPLY"
        node5.inputs[1].default_value = 1
        # link render material part
        tree.links.new(node1.outputs["Density"], node5.inputs[0])
        tree.links.new(node5.outputs["Value"], node2.inputs["Fac"])
        tree.links.new(node2.outputs["Color"], node3.inputs["Color"])
        tree.links.new(node2.outputs["Alpha"], node3.inputs["Density"])
        tree.links.new(node3.outputs[0], node4.inputs[1])
        tree.links.new(node2.outputs["Color"], node3.inputs["Emission Color"])
        tree.links.new(node5.outputs["Value"], node3.inputs["Emission Strength"])
        # add slice material part nodes
        node6 = nodes.new(type="ShaderNodeNewGeometry")
        node7 = nodes.new(type="ShaderNodeSeparateXYZ")
        node8 = nodes.new(type="ShaderNodeMapRange")
        node8.interpolation_type = "STEPPED"
        node8.inputs[5].default_value = 1
        # link render material part
        tree.links.new(node6.outputs["Position"], node7.inputs["Vector"])
        tree.links.new(node7.outputs["X"], node8.inputs["Value"])

    ramp = node2.color_ramp
    el = ramp.elements

    dis = 1 / (color_count - 1)
    x = dis
    for r in range(color_count - 2):
        el.new(x)
        x += dis

    for i, e in enumerate(el):
        e.color = blend_color[i]
    return


def AdjestWorld():
    ### add light source and world material ###
    mat = bpy.data.worlds["World"]
    mat.use_nodes = True
    tree = mat.node_tree
    nodes = tree.nodes
    node1 = nodes["Background"]
    node1.inputs["Color"].default_value = (0, 0, 0, 1)
    return
