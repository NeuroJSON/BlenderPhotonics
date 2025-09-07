"""BlenderPhotonics Main Panel - BlenderPhotonics main interface

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
from .blender2tet import scene2tmesh as scene2Tmesh
from .blender2voxel import scene2vmesh as scene2Vmesh
from .mesh2blender import mesh2sceneTmesh, mesh2sceneVmesh
from .runmmc import runmmc
from .runmcx import runmcx
from .nii2tet import volume2tet, LoadVolumeTetOperator, LoadOpticalParametersTetOperator
from .nii2voxel import volume2voxel, LoadVolumeOperator, LoadOpticalParametersOperator
from .obj2surf import object2surf
from .pkg import (
    InstallJData,
    InstallNumPy,
    InstallIso2Mesh,
    InstallPMCX,
    InstallPMMC,
    InstallAllDependencies,
    CheckDependencies,
)
from .dependencies import get_missing_dependencies


# Property to control which tab is active
class BlenderPhotonicsSettings(bpy.types.PropertyGroup):
    active_tab: bpy.props.EnumProperty(
        name="Active Tab",
        description="Current active tab",
        items=[
            ("DEPS", "Dependencies", "Dependency management"),
            ("PMMC", "PMMC", "PMMC simulation tools"),
            ("PMCX", "PMCX", "PMCX simulation tools"),
        ],
        default="DEPS",
    )


class BlenderPhotonics_Dependencies_Panel(bpy.types.Panel):
    bl_label = "Dependencies"
    bl_idname = "BLENDERPHOTONICS_PT_DEPS"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderPhotonics"
    bl_parent_id = "BLENDERPHOTONICS_PT_MAIN"

    @classmethod
    def poll(cls, context):
        try:
            bp_settings = context.scene.blender_photonics_settings
            return bp_settings.active_tab == "DEPS"
        except AttributeError:
            # If the property doesn't exist, return False
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        bp_settings = scene.blender_photonics_settings

        # Dependency management section
        missing_deps = get_missing_dependencies()
        if missing_deps:
            box = layout.box()
            box.label(text="Missing Dependencies:", icon="ERROR")
            for dep in missing_deps[:3]:  # Show first 3 missing deps
                box.label(text=f"• {dep}")
            if len(missing_deps) > 3:
                box.label(text=f"• ... and {len(missing_deps) - 3} more")

            # Installation buttons
            row = box.row()
            row.operator(
                InstallAllDependencies.bl_idname, text="Install All", icon="IMPORT"
            )
            row.operator(CheckDependencies.bl_idname, text="Check", icon="FILE_REFRESH")

            # Individual install buttons - Essential packages
            row1 = box.row()
            row1.operator(InstallJData.bl_idname, text="JData", icon="FILE_TICK")
            row1.operator(InstallNumPy.bl_idname, text="NumPy", icon="FILE_TICK")

            # Individual install buttons - Simulation packages
            row2 = box.row()
            row2.operator(InstallIso2Mesh.bl_idname, text="iso2mesh", icon="FILE_TICK")
            row3 = box.row()
            row3.operator(InstallPMCX.bl_idname, text="pmcx", icon="FILE_TICK")
            row3.operator(InstallPMMC.bl_idname, text="pmmc", icon="FILE_TICK")

        else:
            # All dependencies available
            box = layout.box()
            row = box.row()
            row.operator(
                CheckDependencies.bl_idname,
                text="✓ All Dependencies Available",
                icon="CHECKMARK",
            )

        layout.separator()
        layout.label(text="Tutorials and Websites", icon="SHADING_SOLID")
        colurl = layout.row()
        op = colurl.operator("wm.url_open", text="Iso2Mesh", icon="URL")
        op.url = "http://iso2mesh.sf.net"
        op = colurl.operator("wm.url_open", text="JMesh spec", icon="URL")
        op.url = "https://github.com/NeuroJSON/jmesh/blob/master/JMesh_specification.md"
        colurl2 = layout.row()
        op = colurl2.operator("wm.url_open", text="MMC wiki", icon="URL")
        op.url = "http://mcx.space/wiki/?Learn#mmc"
        op = colurl2.operator("wm.url_open", text="Brain2Mesh", icon="URL")
        op.url = "http://mcx.space/brain2mesh"
        layout.label(text="Funded by NIH R01-GM114365 & U24-NS124027", icon="HEART")


class BlenderPhotonics_PMMC_Panel(bpy.types.Panel):
    bl_label = "PMMC Tools"
    bl_idname = "BLENDERPHOTONICS_PT_PMMC"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderPhotonics"
    bl_parent_id = "BLENDERPHOTONICS_PT_MAIN"

    @classmethod
    def poll(cls, context):
        try:
            bp_settings = context.scene.blender_photonics_settings
            return bp_settings.active_tab == "PMMC"
        except AttributeError:
            # If the property doesn't exist, return False
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Add error handling for property access
        try:
            bp = scene.blender_photonics
            bp_tet = scene.blender_photonics_tet
        except AttributeError:
            layout.label(
                text="Error: blender_photonics property not found", icon="ERROR"
            )
            return

        layout.label(text="Blender2Mesh", icon="SHADING_SOLID")
        colb2m = layout.column()
        colb2m.operator(
            scene2Tmesh.bl_idname,
            text="Convert scene to tetrahedral mesh",
            icon="MESH_ICOSPHERE",
        ).endstep = "9"
        colb2m.operator(
            scene2Tmesh.bl_idname, text="Export scene to JSON/JMesh", icon="FILE_TICK"
        ).endstep = "5"
        colb2m.operator(
            scene2Tmesh.bl_idname,
            text="Preview surface tesselation",
            icon="MOD_BOOLEAN",
        ).endstep = "4"
        colb2m.operator(mesh2sceneTmesh.bl_idname, icon="EDITMODE_HLT")

        layout.separator()
        layout.label(text="Volume2Tet", icon="SHADING_SOLID")
        layout.prop(bp_tet, "path")
        colv2t = layout.column()
        colv2t.operator(
            LoadVolumeTetOperator.bl_idname, icon="FILE_FOLDER", text="Load volume"
        )
        colv2t.operator(
            volume2tet.bl_idname, icon="MESH_GRID", text="Convert volume to tet mesh"
        )

        # Optical parameters section for tetrahedral mesh
        layout.prop(bp_tet, "optical_params_file")
        colv2t = layout.column()
        colv2t.operator(
            LoadOpticalParametersTetOperator.bl_idname,
            icon="MATERIAL",
            text="Load optical parameters",
        )

        layout.separator()
        layout.label(text="Surface2Mesh", icon="SHADING_SOLID")
        cols2m = layout.column()
        cols2m.operator(
            object2surf.bl_idname, text="Import surface mesh", icon="IMPORT"
        ).action = "import"
        cols2m.operator(
            object2surf.bl_idname, text="Export object to JSON/JMesh", icon="EXPORT"
        ).action = "export"
        cols2m.operator(
            object2surf.bl_idname,
            text="Repair and close triangular mesh",
            icon="MOD_SUBSURF",
        ).action = "repair"
        rowbool = layout.row()
        rowbool.label(text="Boolean")
        rowbool.operator(
            object2surf.bl_idname, text="and", icon="SELECT_INTERSECT"
        ).action = "boolean-and"
        rowbool.operator(
            object2surf.bl_idname, text="or", icon="SELECT_EXTEND"
        ).action = "boolean-or"
        rowbool.operator(object2surf.bl_idname, text="xor", icon="XRAY").action = (
            "boolean-resolve"
        )
        rowbool2 = layout.row()
        rowbool2.operator(
            object2surf.bl_idname, text="diff", icon="SELECT_SUBTRACT"
        ).action = "boolean-diff"
        rowbool2.operator(object2surf.bl_idname, text="1st", icon="OVERLAY").action = (
            "boolean-first"
        )
        rowbool2.operator(object2surf.bl_idname, text="2nd", icon="MOD_MASK").action = (
            "boolean-second"
        )
        rowbool2.operator(
            object2surf.bl_idname, text="simplify", icon="MOD_SIMPLIFY"
        ).action = "simplify"

        layout.separator()
        layout.label(text="PMMC Simulation", icon="SHADING_SOLID")
        colmmc = layout.column()
        colmmc.operator(runmmc.bl_idname, icon="LIGHT_AREA")
        colmmc.operator(
            "blenderphotonics.export_mmc_result",
            text="Export MMC Results",
            icon="EXPORT",
        )


class BlenderPhotonics_PMCX_Panel(bpy.types.Panel):
    bl_label = "PMCX Tools"
    bl_idname = "BLENDERPHOTONICS_PT_PMCX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderPhotonics"
    bl_parent_id = "BLENDERPHOTONICS_PT_MAIN"

    @classmethod
    def poll(cls, context):
        try:
            bp_settings = context.scene.blender_photonics_settings
            return bp_settings.active_tab == "PMCX"
        except AttributeError:
            # If the property doesn't exist, return False
            return False

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Add error handling for property access
        try:
            bp = scene.blender_photonics_voxel
        except AttributeError:
            layout.label(
                text="Error: blender_photonics_voxel property not found", icon="ERROR"
            )
            return

        layout.split(factor=0.0)  # to prevent the layout from collapsing
        layout.label(text="Blender2Mesh", icon="SHADING_SOLID")
        colb2m = layout.column()
        colb2m.operator(
            scene2Vmesh.bl_idname,
            text="convert scene to voxel mesh",
            icon="MESH_ICOSPHERE",
        ).endstep = "9"
        colb2m.operator(
            scene2Vmesh.bl_idname, text="Export scene to JSON/JMesh", icon="FILE_TICK"
        ).endstep = "5"
        colb2m.operator(
            scene2Vmesh.bl_idname,
            text="Preview surface tesselation",
            icon="MOD_BOOLEAN",
        ).endstep = "4"
        colb2m.operator(mesh2sceneVmesh.bl_idname, icon="EDITMODE_HLT")

        layout.separator()
        layout.label(text="Volume2Mesh", icon="SHADING_SOLID")
        layout.prop(bp, "path")
        colv2m = layout.column()
        colv2m.operator(
            LoadVolumeOperator.bl_idname, icon="FILE_FOLDER", text="Load volume"
        )
        colv2m.operator(
            volume2voxel.bl_idname, icon="MESH_GRID", text="Convert volume to mesh"
        )

        # Optical parameters section
        layout.prop(bp, "optical_params_file")
        colv2m = layout.column()
        colv2m.operator(
            LoadOpticalParametersOperator.bl_idname,
            icon="MATERIAL",
            text="Load optical parameters",
        )

        layout.separator()
        layout.label(text="Surface2Mesh", icon="SHADING_SOLID")
        cols2m = layout.column()
        cols2m.operator(
            object2surf.bl_idname, text="Import surface mesh", icon="IMPORT"
        ).action = "import"
        cols2m.operator(
            object2surf.bl_idname, text="Export object to JSON/JMesh", icon="EXPORT"
        ).action = "export"
        cols2m.operator(
            object2surf.bl_idname,
            text="Repair and close triangular mesh",
            icon="MOD_SUBSURF",
        ).action = "repair"
        rowbool = layout.row()
        rowbool.label(text="Boolean")
        rowbool.operator(
            object2surf.bl_idname, text="and", icon="SELECT_INTERSECT"
        ).action = "boolean-and"
        rowbool.operator(
            object2surf.bl_idname, text="or", icon="SELECT_EXTEND"
        ).action = "boolean-or"
        rowbool.operator(object2surf.bl_idname, text="xor", icon="XRAY").action = (
            "boolean-resolve"
        )
        rowbool2 = layout.row()
        rowbool2.operator(
            object2surf.bl_idname, text="diff", icon="SELECT_SUBTRACT"
        ).action = "boolean-diff"
        rowbool2.operator(object2surf.bl_idname, text="1st", icon="OVERLAY").action = (
            "boolean-first"
        )
        rowbool2.operator(object2surf.bl_idname, text="2nd", icon="MOD_MASK").action = (
            "boolean-second"
        )
        rowbool2.operator(
            object2surf.bl_idname, text="simplify", icon="MOD_SIMPLIFY"
        ).action = "simplify"

        layout.separator()
        layout.label(text="PMCX Simulation", icon="SHADING_SOLID")
        colmcx = layout.column()
        colmcx.operator(runmcx.bl_idname, text="Run PMCX Simulation", icon="LIGHT_SUN")
        colmcx.operator(
            "blenderphotonics.export_mcx_result",
            text="Export MCX Results",
            icon="EXPORT",
        )


class BlenderPhotonics_UI(bpy.types.Panel):
    bl_label = "BlenderPhotonics v2025"
    bl_idname = "BLENDERPHOTONICS_PT_MAIN"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderPhotonics"

    @classmethod
    def poll(self, context):
        return context.mode in {"EDIT_MESH", "OBJECT", "PAINT_WEIGHT"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Add error handling for property access
        try:
            bp_settings = scene.blender_photonics_settings
        except AttributeError:
            layout.label(
                text="Error: Settings not initialized. Please restart Blender.",
                icon="ERROR",
            )
            return

        # Tab selection
        row = layout.row()
        row.prop(bp_settings, "active_tab", expand=True)

        layout.separator()

        # Add log window button
        layout.operator(
            "blenderphotonics.show_log_window", text="Show Log Window", icon="CONSOLE"
        )
