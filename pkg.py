import bpy
import subprocess
import sys
import os
import pathlib
from .dependencies import check_dependencies, show_error_message


class InstallJData(bpy.types.Operator):
    bl_idname = "blenderphotonics.install_jdata"
    bl_label = "Install JData"
    bl_description = "Install JData package for JSON/JMesh operations"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            # Install JData
            ADDON_DIR = os.path.join(
                os.path.abspath(pathlib.Path(__file__).resolve().parent.parent),
                "modules",
            )
            if not os.path.exists(ADDON_DIR):
                os.makedirs(ADDON_DIR)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "jdata",
                    "--target=" + ADDON_DIR,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Update dependency status
                check_dependencies()
                show_error_message(
                    "JData installed successfully! ",
                    "Installation Complete",
                )
            else:
                show_error_message(
                    f"Failed to install JData: {result.stderr}", "Installation Failed"
                )

        except Exception as e:
            show_error_message(
                f"Error installing JData: {str(e)}", "Installation Error"
            )

        return {"FINISHED"}


class InstallNumPy(bpy.types.Operator):
    bl_idname = "blenderphotonics.install_numpy"
    bl_label = "Install NumPy"
    bl_description = "Install NumPy package for numerical operations"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            # Install NumPy
            ADDON_DIR = os.path.join(
                os.path.abspath(pathlib.Path(__file__).resolve().parent.parent),
                "modules",
            )
            if not os.path.exists(ADDON_DIR):
                os.makedirs(ADDON_DIR)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "numpy",
                    "--target=" + ADDON_DIR,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Update dependency status
                check_dependencies()
                show_error_message(
                    "NumPy installed successfully! ",
                    "Installation Complete",
                )
            else:
                show_error_message(
                    f"Failed to install NumPy: {result.stderr}", "Installation Failed"
                )

        except Exception as e:
            show_error_message(
                f"Error installing NumPy: {str(e)}", "Installation Error"
            )

        return {"FINISHED"}


class InstallSciPy(bpy.types.Operator):
    bl_idname = "blenderphotonics.install_scipy"
    bl_label = "Install SciPy"
    bl_description = "Install SciPy package for scientific computing operations"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            # Install SciPy
            ADDON_DIR = os.path.join(
                os.path.abspath(pathlib.Path(__file__).resolve().parent.parent),
                "modules",
            )
            if not os.path.exists(ADDON_DIR):
                os.makedirs(ADDON_DIR)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "scipy",
                    "--target=" + ADDON_DIR,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Update dependency status
                check_dependencies()
                show_error_message(
                    "SciPy installed successfully! ",
                    "Installation Complete",
                )
            else:
                show_error_message(
                    f"Failed to install SciPy: {result.stderr}", "Installation Failed"
                )

        except Exception as e:
            show_error_message(
                f"Error installing SciPy: {str(e)}", "Installation Error"
            )

        return {"FINISHED"}


class InstallIso2Mesh(bpy.types.Operator):
    bl_idname = "blenderphotonics.install_iso2mesh"
    bl_label = "Install iso2mesh"
    bl_description = "Install iso2mesh package for mesh generation operations"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            # Install scipy first (required for iso2mesh)
            ADDON_DIR = os.path.join(
                os.path.abspath(pathlib.Path(__file__).resolve().parent.parent),
                "modules",
            )
            if not os.path.exists(ADDON_DIR):
                os.makedirs(ADDON_DIR)

            # Install scipy first
            scipy_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "scipy",
                    "--target=" + ADDON_DIR,
                ],
                capture_output=True,
                text=True,
            )

            if scipy_result.returncode != 0:
                show_error_message(
                    f"Failed to install scipy (required for iso2mesh): {scipy_result.stderr}",
                    "Installation Failed",
                )
                return {"FINISHED"}

            # Install iso2mesh
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "iso2mesh",
                    "--target=" + ADDON_DIR,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Update dependency status
                check_dependencies()
                show_error_message(
                    "scipy and iso2mesh installed successfully! ",
                    "Installation Complete",
                )
            else:
                show_error_message(
                    f"Failed to install iso2mesh: {result.stderr}",
                    "Installation Failed",
                )

        except Exception as e:
            show_error_message(
                f"Error installing iso2mesh: {str(e)}", "Installation Error"
            )

        return {"FINISHED"}


class InstallPMCX(bpy.types.Operator):
    bl_idname = "blenderphotonics.install_pmcx"
    bl_label = "Install pmcx"
    bl_description = "Install pmcx package for Monte Carlo eXtreme simulations"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            # Install pmcx
            ADDON_DIR = os.path.join(
                os.path.abspath(pathlib.Path(__file__).resolve().parent.parent),
                "modules",
            )
            if not os.path.exists(ADDON_DIR):
                os.makedirs(ADDON_DIR)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "pmcx",
                    "--target=" + ADDON_DIR,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Update dependency status
                check_dependencies()
                show_error_message(
                    "pmcx installed successfully! ",
                    "Installation Complete",
                )
            else:
                show_error_message(
                    f"Failed to install pmcx: {result.stderr}", "Installation Failed"
                )

        except Exception as e:
            show_error_message(f"Error installing pmcx: {str(e)}", "Installation Error")

        return {"FINISHED"}


class InstallPMMC(bpy.types.Operator):
    bl_idname = "blenderphotonics.install_pmmc"
    bl_label = "Install pmmc"
    bl_description = "Install pmmc package for Mesh-based Monte Carlo simulations"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            # Install pmmc
            ADDON_DIR = os.path.join(
                os.path.abspath(pathlib.Path(__file__).resolve().parent.parent),
                "modules",
            )
            if not os.path.exists(ADDON_DIR):
                os.makedirs(ADDON_DIR)

            # On Windows, install sparse_numba first (required for pmmc)
            import platform

            if platform.system() == "Windows":
                sparse_numba_result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "sparse_numba",
                        "--target=" + ADDON_DIR,
                    ],
                    capture_output=True,
                    text=True,
                )

                if sparse_numba_result.returncode != 0:
                    show_error_message(
                        f"Failed to install sparse_numba (required for pmmc on Windows): {sparse_numba_result.stderr}",
                        "Installation Failed",
                    )
                    return {"FINISHED"}

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "pmmc",
                    "--target=" + ADDON_DIR,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Update dependency status
                check_dependencies()
                if platform.system() == "Windows":
                    show_error_message(
                        "sparse_numba and pmmc installed successfully! ",
                        "Installation Complete",
                    )
                else:
                    show_error_message(
                        "pmmc installed successfully! ",
                        "Installation Complete",
                    )
            else:
                show_error_message(
                    f"Failed to install pmmc: {result.stderr}", "Installation Failed"
                )

        except Exception as e:
            show_error_message(f"Error installing pmmc: {str(e)}", "Installation Error")

        return {"FINISHED"}


class InstallAllDependencies(bpy.types.Operator):
    bl_idname = "blenderphotonics.install_all_deps"
    bl_label = "Install All Dependencies"
    bl_description = "Install all required Python packages for BlenderPhotonics"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            # Install all dependencies
            ADDON_DIR = os.path.join(
                os.path.abspath(pathlib.Path(__file__).resolve().parent.parent),
                "modules",
            )
            if not os.path.exists(ADDON_DIR):
                os.makedirs(ADDON_DIR)

            import platform

            packages = ["jdata", "numpy", "scipy", "iso2mesh", "pmcx"]

            # Add Windows-specific dependency for pmmc
            if platform.system() == "Windows":
                packages.append("sparse_numba")

            packages.append("pmmc")

            failed_packages = []

            for package in packages:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        package,
                        "--target=" + ADDON_DIR,
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    failed_packages.append(package)

            # Update dependency status
            check_dependencies()

            if failed_packages:
                show_error_message(
                    f"Some packages failed to install: {', '.join(failed_packages)}. Please try installing them individually.",
                    "Partial Installation",
                )
            else:
                show_error_message(
                    "All dependencies installed successfully! ",
                    "Installation Complete",
                )

        except Exception as e:
            show_error_message(
                f"Error installing dependencies: {str(e)}", "Installation Error"
            )

        return {"FINISHED"}


class CheckDependencies(bpy.types.Operator):
    bl_idname = "blenderphotonics.check_deps"
    bl_label = "Check Dependencies"
    bl_description = "Check which dependencies are installed and available"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Check current dependency status
        deps = check_dependencies()
        missing = [dep for dep, available in deps.items() if not available]
        available = [dep for dep, available in deps.items() if available]

        if missing:
            message = f"Missing: {', '.join(missing)}\nAvailable: {', '.join(available) if available else 'None'}"
            show_error_message(message, "Dependency Status")
        else:
            show_error_message("All dependencies are available!", "Dependency Status")

        return {"FINISHED"}
