"""Blender2Mesh - converting Blender objects/scene to 3-D voxel mesh

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
from bpy.utils import register_class, unregister_class
from .utils import *
from .dependencies import safe_import, require_dependency, show_error_message

# Safe imports
np = safe_import("numpy")
jd = safe_import("jdata")
iso2mesh = safe_import("iso2mesh")

g_maxvol = 1.0
g_keepratio = 1.0
g_mergetol = 0
g_dorepair = False
g_onlysurf = False
g_convtri = True
g_endstep = "9"
g_tetgenopt = ""
g_voxeldiv = 50
g_colormap = "jet"
enum_endstep = [
    ("1", "Step 1: Convert objects to mesh", "Convert objects to mesh"),
    ("2", "Step 2: Join all objects", "Join all objects"),
    ("3", "Step 3: Intersect objects", "Intersect objects"),
    (
        "4",
        "Step 4: Convert to triangles",
        "Merge all visible objects, perform intersection and convert to N-gon or triangular mesh",
    ),
    (
        "5",
        "Step 5: Export to JMesh",
        "Export the scene to a human-readable universal data exchange file encoded in the JSON format based on the JMesh specification (see http://neurojson.org)",
    ),
    (
        "6",
        "Step 6: Run Iso2Mesh and load mesh",
        "Output voxel mesh using Iso2Mesh (http://iso2mesh.sf.net)",
    ),
    (
        "9",
        "Run all steps",
        "Create 3-D voxel meshes using Iso2Mesh and Octave (please save your Blender session first!)",
    ),
]


class scene2vmesh(bpy.types.Operator):
    bl_label = "Convert scene to voxel mesh"
    bl_description = "Create 3-D voxelization meshes using Iso2Mesh and Octave (please save your Blender session first!)"
    bl_idname = "blenderphotonics.createvoxelmesh"

    # creat a interface to set uesrs' model parameter.

    bl_options = {"REGISTER", "UNDO"}
    maxvol: bpy.props.FloatProperty(default=g_maxvol, name="Maximum tet volume")
    keepratio: bpy.props.FloatProperty(
        default=g_keepratio, name="Fraction edge kept (0-1)"
    )
    mergetol: bpy.props.FloatProperty(
        default=g_mergetol, name="Tolerance to merge nodes (0 to disable)"
    )
    dorepair: bpy.props.BoolProperty(
        default=g_dorepair, name="Repair mesh (single object only)"
    )
    onlysurf: bpy.props.BoolProperty(
        default=g_onlysurf, name="Return triangular surface mesh only (no voxel mesh)"
    )
    convtri: bpy.props.BoolProperty(
        default=g_convtri, name="Convert to triangular mesh first"
    )
    endstep: bpy.props.EnumProperty(
        default=g_endstep, name="Run through step", items=enum_endstep
    )
    tetgenopt: bpy.props.StringProperty(
        default=g_tetgenopt, name="Additional tetgen flags"
    )
    voxeldiv: bpy.props.IntProperty(
        default=g_voxeldiv,
        name="division number along the shortest edge of the mesh "
        "(resolution), 0 to disable",
    )
    colormap: bpy.props.StringProperty(default=g_colormap, name="color scheme")

    @classmethod
    def description(cls, context, properties):
        hints = {}
        for item in enum_endstep:
            hints[item[0]] = item[2]
        return hints[properties.endstep]

    def save_region_mesh(self, node, elem, outputdir):
        """
        Python implementation of blendersavemesh.m
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
                    "Comment": "Created by BlenderPhotonics Python iso2mesh implementation",
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
            jd.save(outputmesh, os.path.join(outputdir, "regionVmesh.jmsh"))

            # Generate and save volume mesh (all faces)
            log_message("Saving volume mesh...")
            faces = meshface(elem[:, :4])

            volume_mesh = meshdata.copy()
            volume_mesh["MeshTri3"] = faces.tolist()
            volume_mesh["MeshTet4"] = elem.tolist()
            jd.save(volume_mesh, os.path.join(outputdir, "volumeVmesh.jmsh"))

            log_message("Mesh saving complete.")

        except Exception as e:
            log_message(f"Error saving mesh: {str(e)}", "ERROR")
            raise e

    def func(self):
        from .utils import log_message

        if not require_dependency("jdata", "mesh generation and export"):
            return
        if not require_dependency("numpy", "mesh processing"):
            return

        log_message("Initializing voxel mesh workspace...")
        outputdir = GetBPWorkFolder()
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)
            log_message(f"Created workspace directory: {outputdir}")

        if os.path.exists(os.path.join(outputdir, "regionVmesh.jmsh")):
            os.remove(os.path.join(outputdir, "regionVmesh.jmsh"))
            log_message("Removed existing regionVmesh.jmsh")
        if os.path.exists(os.path.join(outputdir, "volumeVmesh.jmsh")):
            os.remove(os.path.join(outputdir, "volumeVmesh.jmsh"))
            log_message("Removed existing volumeVmesh.jmsh")

        # remove camera and source
        log_message("Removing cameras, lights, and other non-mesh objects...")

        # Ensure we're in object mode for deletion operations
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        # First, clear all selections
        bpy.ops.object.select_all(action="DESELECT")

        # Select only non-mesh objects for deletion
        objects_to_delete = []
        for ob in bpy.context.scene.objects:
            log_message(f"Processing object: {ob.name} (type: {ob.type})")
            if ob.type in ["CAMERA", "LIGHT", "EMPTY", "LAMP", "SPEAKER"]:
                ob.select_set(True)
                objects_to_delete.append(ob.name)

        # Only attempt deletion if we have objects selected
        if objects_to_delete:
            log_message(
                f"Deleting {len(objects_to_delete)} non-mesh objects: {', '.join(objects_to_delete)}"
            )
            bpy.ops.object.delete()
        else:
            log_message("No non-mesh objects found to delete")

        # Ensure we have a valid active object after deletion
        obj = bpy.context.view_layer.objects.active

        # Select objects for conversion based on convtri setting
        bpy.ops.object.select_all(action="DESELECT")
        if not self.convtri:
            bpy.ops.object.select_by_type(type="MESH")
            bpy.ops.object.select_all(action="INVERT")
        else:
            bpy.ops.object.select_all(action="SELECT")

        selected_objects = bpy.context.selected_objects
        if len(selected_objects) >= 1:
            log_message(
                f"Converting {len(selected_objects)} selected objects to mesh..."
            )
            bpy.ops.object.convert(target="MESH")
        else:
            log_message("No objects selected for conversion")

        # at this point, objects are converted to mesh if possible
        if int(self.endstep) < 2:
            log_message("Stopping at step 1: Objects converted to mesh")
            return

        log_message("Joining all mesh objects...")
        bpy.ops.object.select_all(action="DESELECT")

        # Select only mesh objects for joining
        mesh_objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        for mesh_obj in mesh_objects:
            mesh_obj.select_set(True)

        selected_objects = bpy.context.selected_objects
        if len(selected_objects) >= 2:
            # Set the largest mesh as active object for joining
            if mesh_objects:
                largest_mesh = max(
                    mesh_objects, key=lambda o: len(o.data.vertices) if o.data else 0
                )
                bpy.context.view_layer.objects.active = largest_mesh

            log_message(f"Joining {len(selected_objects)} mesh objects...")
            bpy.ops.object.join()
        elif len(selected_objects) == 1:
            log_message("Only one mesh object found, no joining needed")
        else:
            log_message("Warning: No mesh objects found to join", "WARNING")

        # at this point, objects are jointed
        if int(self.endstep) < 3:
            log_message("Stopping at step 2: Objects joined")
            return

        log_message("Performing mesh intersection...")

        # Ensure we have a valid active mesh object for edit mode operations
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is None or active_obj.type != "MESH":
            mesh_objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
            if mesh_objects:
                bpy.context.view_layer.objects.active = mesh_objects[0]
                active_obj = mesh_objects[0]
                log_message(f"Set active object for intersection: {active_obj.name}")
            else:
                log_message(
                    "Error: No mesh objects available for intersection", "ERROR"
                )
                return

        # Clear selection and ensure only the active object is selected
        bpy.ops.object.select_all(action="DESELECT")
        active_obj.select_set(True)

        # Enter edit mode for intersection operations
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")

        try:
            bpy.ops.mesh.intersect(mode="SELECT", separate_mode="NONE", solver="EXACT")
            log_message("Used exact intersection solver")
        except:
            try:
                bpy.ops.mesh.intersect(mode="SELECT", separate_mode="NONE")
                log_message("Used fast intersection solver")
            except Exception as e:
                log_message(
                    f"Warning: Intersection operation failed: {str(e)}", "WARNING"
                )

        # Return to object mode
        bpy.ops.object.mode_set(mode="OBJECT")

        # at this point, overlapping objects are intersected
        if int(self.endstep) < 4:
            log_message("Stopping at step 3: Objects intersected")
            return

        if self.convtri:
            log_message("Converting polygons to triangles...")

            # Ensure we're in edit mode and have the right object selected
            active_obj = bpy.context.view_layer.objects.active
            if active_obj and active_obj.type == "MESH":
                # We should already be in object mode from the previous step
                if bpy.context.mode != "EDIT_MESH":
                    bpy.ops.object.mode_set(mode="EDIT")

                bpy.ops.mesh.select_all(action="SELECT")
                try:
                    bpy.ops.mesh.quads_convert_to_tris(
                        quad_method="BEAUTY", ngon_method="BEAUTY"
                    )
                    log_message("Successfully converted polygons to triangles")
                except Exception as e:
                    log_message(f"Warning: Triangulation failed: {str(e)}", "WARNING")

                # Return to object mode
                bpy.ops.object.mode_set(mode="OBJECT")
            else:
                log_message(
                    "Warning: No valid mesh object for triangulation", "WARNING"
                )

        # at this point, if enabled, surfaces are converted to triangular meshes
        if int(self.endstep) < 5:
            log_message("Stopping at step 4: Surface tesselation complete")
            return

        # output mesh data to Octave
        # this works only in object mode,
        log_message("Extracting mesh data...")

        # Ensure we're in object mode before proceeding
        current_mode = bpy.context.mode
        if current_mode != "OBJECT":
            log_message(
                f"Currently in {current_mode} mode, switching to OBJECT mode..."
            )
            # Handle different modes appropriately
            if current_mode.startswith("EDIT"):
                bpy.ops.object.mode_set(mode="OBJECT")
            elif current_mode.startswith("SCULPT"):
                bpy.ops.sculpt.sculptmode_toggle()
            elif current_mode.startswith("PAINT"):
                bpy.ops.object.mode_set(mode="OBJECT")
            else:
                # For any other mode, try to switch to object mode
                bpy.ops.object.mode_set(mode="OBJECT")
            log_message("Successfully switched to OBJECT mode")

        # Ensure we have mesh objects to work with
        mesh_objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        if not mesh_objects:
            log_message("Error: No mesh objects found in scene", "ERROR")
            return

        # Select all mesh objects to ensure we're working with the combined result
        bpy.ops.object.select_all(action="DESELECT")
        for mesh_obj in mesh_objects:
            mesh_obj.select_set(True)

        # Set the first mesh object as active, or keep current active if it's a mesh
        obj = bpy.context.view_layer.objects.active
        if obj is None or obj.type != "MESH" or obj not in mesh_objects:
            # Find the largest mesh object (most likely the joined result) or first one
            largest_mesh = max(
                mesh_objects, key=lambda o: len(o.data.vertices) if o.data else 0
            )
            bpy.context.view_layer.objects.active = largest_mesh
            obj = largest_mesh
            log_message(
                f"Set active object to: {obj.name} ({len(obj.data.vertices)} vertices)"
            )
        else:
            log_message(f"Using current active mesh object: {obj.name}")

        # Final validation that our object has mesh data
        if obj.data is None or len(obj.data.vertices) == 0:
            log_message(
                f"Error: Object '{obj.name}' has no mesh data or vertices", "ERROR"
            )
            return

        # Extract mesh data with proper validation
        log_message("Extracting vertex data...")
        vertex_count = len(obj.data.vertices)
        if vertex_count > 0:
            vert = np.zeros(3 * vertex_count)
            obj.data.vertices.foreach_get("co", vert)
            v = vert.reshape(-1, 3)
            log_message(f"Successfully extracted {len(v)} vertices")
        else:
            log_message("Error: Mesh has no vertices", "ERROR")
            return

        log_message("Extracting edge data...")
        edge_count = len(obj.data.edges)
        if edge_count > 0:
            edgeslist = np.zeros(2 * edge_count)
            obj.data.edges.foreach_get("vertices", edgeslist)
            e = (edgeslist + 1).reshape(-1, 2)
            log_message(f"Successfully extracted {len(e)} edges")
        else:
            log_message("Warning: Mesh has no edges, using empty edge array")
            e = np.array([]).reshape(0, 2)

        log_message("Extracting face data...")
        polygon_count = len(obj.data.polygons)
        if polygon_count > 0:
            if self.convtri:
                # For triangular faces, ensure all polygons are triangles
                non_tri_count = sum(
                    1 for poly in obj.data.polygons if len(poly.vertices) != 3
                )
                if non_tri_count > 0:
                    log_message(
                        f"Warning: Found {non_tri_count} non-triangular faces. Consider enabling triangulation.",
                        "WARNING",
                    )

                # Extract only triangular faces or pad/truncate as needed
                tri_faces = []
                for poly in obj.data.polygons:
                    if len(poly.vertices) == 3:
                        tri_faces.extend(poly.vertices)
                    elif len(poly.vertices) > 3:
                        # Take first 3 vertices for now (simple approach)
                        tri_faces.extend(poly.vertices[:3])

                if tri_faces:
                    faceslist = np.array(tri_faces)
                    f = (faceslist + 1).reshape(-1, 3)
                    log_message(f"Successfully extracted {len(f)} triangular faces")
                else:
                    log_message("Warning: No valid triangular faces found")
                    f = np.array([]).reshape(0, 3)
            else:
                # For polygonal faces, extract as lists
                f = [
                    (np.array(poly.vertices[:]) + 1).tolist()
                    for poly in obj.data.polygons
                ]
                log_message(f"Successfully extracted {len(f)} polygonal faces")
        else:
            log_message("Warning: Mesh has no faces")
            if self.convtri:
                f = np.array([]).reshape(0, 3)
            else:
                f = []

        # Save file
        log_message("Saving mesh data to JMesh format...")
        meshdata = {
            "_DataInfo_": {
                "JMeshVersion": "0.5",
                "Comment": "Created by BlenderPhotonics (http:\/\/mcx.space\/BlenderPhotonics)",
            },
            "MeshVertex3": v,
            "MeshPoly": f,
            "param": {
                "keepratio": self.keepratio,
                "maxvol": self.maxvol,
                "mergetol": self.mergetol,
                "dorepair": self.dorepair,
                "tetgenopt": self.tetgenopt,
                "div": self.voxeldiv,
            },
        }
        jd.save(meshdata, os.path.join(outputdir, "blenderVmesh.jmsh"))
        log_message(
            f"Saved mesh data to: {os.path.join(outputdir,'blenderVmesh.jmsh')}"
        )

        if int(self.endstep) == 5:
            log_message("Opening file save dialog...")
            bpy.ops.blender2mesh.invoke_saveas("INVOKE_DEFAULT")

        # at this point, all mesh objects are saved to a jmesh file under work-dir as blendermesh.json
        if int(self.endstep) < 6:
            log_message("Stopping at step 5: Mesh exported to JSON/JMesh")
            return

        # Check if Python-based iso2mesh is available
        if require_dependency("iso2mesh", "mesh generation operations"):
            try:
                # Import iso2mesh functions
                from iso2mesh import s2m, removedupnodes, meshcheckrepair, s2v

                log_message("Using Python-based iso2mesh for voxel mesh generation")

                bbx = np.array(
                    [
                        v[:, 0].min(),
                        v[:, 1].min(),
                        v[:, 2].min(),
                        v[:, 0].max(),
                        v[:, 1].max(),
                        v[:, 2].max(),
                    ]
                )
                log_message(f"Mesh bounding box: {bbx}")

                # Process vertices and faces based on parameters
                vertices, faces = v, f
                if self.mergetol > 0:
                    log_message(
                        f"Removing duplicate nodes with tolerance: {self.mergetol}"
                    )
                    vertices, faces = removedupnodes(vertices, faces, self.mergetol)

                if self.dorepair:
                    log_message("Repairing mesh...")
                    vertices, faces = meshcheckrepair(vertices, faces, "meshfix")

                # Generate tetrahedral mesh first using s2m (surface to mesh)
                log_message(
                    "Generating intermediate tetrahedral mesh... This may take a while..."
                )
                node, elem, _ = s2m(
                    vertices,
                    faces,
                    self.keepratio,
                    self.maxvol,
                    "tetgen1.5",
                    [],
                    [],
                    self.tetgenopt,
                )
                log_message(
                    f"Generated tetrahedral mesh with {len(node)} nodes and {len(elem)} elements"
                )

                # Define the heavy computation function for voxel generation
                def generate_voxel_mesh():
                    """This function runs in background thread"""
                    # Generate voxel mesh if requested
                    if self.voxeldiv > 0:
                        log_message(
                            f"Generating voxel mesh with division: {self.voxeldiv}"
                        )
                        image = s2v(node, elem, self.voxeldiv, label=1)
                    else:
                        log_message(f"Generating voxel mesh with default division: 50")
                        image = s2v(node, elem, 50, label=1)

                    log_message(
                        f"Generated voxel mesh with shape: {np.array(image).shape}"
                    )

                    # Calculate scale factors
                    image_scale = (
                        np.min(
                            np.array(
                                [bbx[3] - bbx[0], bbx[4] - bbx[1], bbx[5] - bbx[2]]
                            )
                        )
                        / self.voxeldiv
                    )
                    image_move = np.array([bbx[0], bbx[1], bbx[2]])
                    log_message(f"Image scale factors: {image_scale}")
                    log_message(f"Image offset: {image_move}")

                    # affine matrix
                    affine_matrix = np.array(
                        [
                            [image_scale, 0, 0, image_move[0]],
                            [0, image_scale, 0, image_move[1]],
                            [0, 0, image_scale, image_move[2]],
                            [0, 0, 0, 1],
                        ]
                    )
                    log_message(f"Generated affine transformation matrix")

                    return node, elem, image, affine_matrix

                # Define callback function for when voxel generation completes
                def on_voxel_complete(result):
                    """This function runs on main thread when background task completes"""
                    try:
                        node, elem, image, affine_matrix = result

                        # Save image mesh data using jdata
                        log_message("Saving voxel mesh data...")
                        image_data = {
                            "_DataInfo_": {
                                "JMeshVersion": "0.5",
                                "Comment": "Voxel mesh created by BlenderPhotonics Python iso2mesh implementation",
                            },
                            "ImageMesh": image,
                            "ImageScale": affine_matrix,
                        }
                        # Save using jdata (JSON format for mesh data)
                        jd.save(image_data, os.path.join(outputdir, "imageVmesh.jmsh"))
                        log_message(
                            f"Saved voxel mesh to: {os.path.join(outputdir, 'imageVmesh.jmsh')}"
                        )

                        # Save region mesh (surface of each region)
                        log_message("Saving region mesh...")
                        self.save_region_mesh(node, elem, outputdir)

                        # Import volume mesh to blender for visualization
                        log_message("Cleaning up existing objects...")
                        for obj in bpy.data.objects:
                            bpy.data.objects.remove(obj)
                        bpy.ops.outliner.orphans_purge(do_recursive=True)

                        log_message("Loading generated voxel mesh into Blender...")
                        LoadVolMesh(
                            {"image": image, "scale": affine_matrix},
                            "Iso2Mesh",
                            outputdir,
                            mode="model_view",
                            colormap=self.colormap,
                        )
                        if "Iso2Mesh" in bpy.data.objects:
                            bpy.context.view_layer.objects.active = bpy.data.objects[
                                "Iso2Mesh"
                            ]

                        log_message(
                            "✓ Voxel mesh generation completed successfully!", "SUCCESS"
                        )
                        show_error_message(
                            "Voxel mesh generation completed successfully using Python iso2mesh!",
                            "Success",
                        )

                    except Exception as e:
                        log_message(
                            f"Error in voxel completion callback: {str(e)}", "ERROR"
                        )
                        show_error_message(
                            f"Error in voxel completion: {str(e)}", "Completion Error"
                        )

                # Import background threading utility
                from .utils import run_in_background

                # Start background voxel generation
                success = run_in_background(
                    generate_voxel_mesh,
                    callback=on_voxel_complete,
                    thread_name="voxel_mesh_generation",
                )

                if success:
                    log_message(
                        "Voxel mesh generation started in background. Blender UI remains responsive."
                    )
                    log_message("Use 'Show Log Window' to monitor progress.")
                else:
                    log_message(
                        "Another voxel mesh generation is already running", "WARNING"
                    )

            except ImportError as e:
                log_message(f"Failed to import iso2mesh functions: {str(e)}", "ERROR")
                show_error_message(
                    f"Failed to import iso2mesh functions: {str(e)}", "Import Error"
                )
            except Exception as e:
                log_message(f"Error during voxel mesh generation: {str(e)}", "ERROR")
                show_error_message(
                    f"Error during voxel mesh generation: {str(e)}",
                    "Mesh Generation Error",
                )
        else:
            # Fallback message for missing iso2mesh
            log_message(
                "iso2mesh package is required for voxel mesh generation", "ERROR"
            )
            show_error_message(
                "iso2mesh package is required for voxel mesh generation. Please install it using the button in the BlenderPhotonics panel.",
                "Missing Dependency",
            )

        # at this point, if successful, iso2mesh generated mesh objects are imported into blender
        if int(self.endstep) < 7:
            log_message("Voxel mesh generation process completed")
            return

        log_message("All voxel mesh steps completed successfully!")
        ShowMessageBox(
            "Voxel mesh generation is complete. The combined voxel mesh is imported for inspection. To set optical properties for each region, please click 'Load mesh and setup simulation'",
            "BlenderPhotonics",
        )

    def execute(self, context):
        from .utils import log_message, clear_log

        # Clear previous log and log start message
        clear_log()
        log_message("Starting voxel mesh generation process...")
        print("=== BlenderPhotonics: Starting voxel mesh generation ===")
        print("Tip: Use 'Show Log Window' button to view detailed progress")

        print("begin to generate voxel mesh")
        self.func()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


#
#   Dialog to set meshing properties
#
class setmeshingprop(bpy.types.Panel):
    bl_label = "Mesh generation setting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global g_maxvol, g_keepratio, g_mergetol, g_dorepair, onlysurf, g_convtri, g_tetgenopt, g_endstep
        self.layout.operator("object.dialog_operator")


# This operator will open Blender's file chooser when invoked
# and store the selected filepath in self.filepath and print it
# to the console using window_manager.fileselect_add()
class BLENDER2MESH_OT_invoke_saveas(bpy.types.Operator):
    bl_idname = "blender2mesh.invoke_saveas"
    bl_label = "Export scene in a JMesh/JSON universal exchange file"

    filepath = bpy.props.StringProperty(default="", subtype="DIR_PATH")

    def execute(self, context):
        from .utils import log_message

        print(self.filepath)
        if not (self.filepath == ""):
            source_file = os.path.join(GetBPWorkFolder(), "blenderVmesh.jmsh")

            # Validate source file exists
            if not os.path.exists(source_file):
                log_message(f"Error: Source file not found: {source_file}", "ERROR")
                return {"CANCELLED"}

            try:
                if os.name == "nt":
                    import shutil

                    shutil.copy2(source_file, self.filepath)
                else:
                    import shutil

                    shutil.copy2(source_file, self.filepath)
                log_message(f"File successfully copied to: {self.filepath}")
            except Exception as e:
                log_message(f"Error copying file: {str(e)}", "ERROR")
                return {"CANCELLED"}
        else:
            log_message("No file path selected", "WARNING")
            return {"CANCELLED"}
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}
