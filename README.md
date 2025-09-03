![](http://neurojson.org/wiki/upload/blenderphotonics_header.png)

BlenderPhotonics
========================

-   **Author**: Qianqian Fang (q.fang at neu.edu) and Yuxuan Zhang (zhang.yuxuan1 at northeastern.edu)
-   **License**: GNU General Public License version 3 (GPLv3)
-   **Version**: v2023 (Beta)
-   **Website**: <http://mcx.space/BlenderPhotonics>
-   **Acknowledgement**: This project is funded by NIH awards 
      [R01-GM114365](https://grantome.com/grant/NIH/R01-GM114365-06) and 
      [U24-NS124027](https://reporter.nih.gov/search/dXkcyoaEQkaRrkpQoOnEBw/project-details/10308329)

Introduction
-------------
BlenderPhotonics is a Blender addon to enable 3-D tetrahedral mesh generation (via Iso2Mesh) and mesh-based Monte Carlo (MMC) photon simulations (via MMCLAB) and voxel-based Monte Carlo (MCX) photon simulation inside the Blender environment.

BlenderPhotonics supports three processing workflows: 1) converting 3-D Blender objects to region-labeled tetrahedral meshes and triangular surfaces; 2) converting a volumetric image stored in a NIfTI file to a multi-labeled tetrahedral mesh, and 3) defining optical properties of each region and a light source to execute and render MMC simulation results. Each feature can be achieved via a single click on the GUI.

BlenderPhotonics combines the interactive 3-D shape creation/editing and advanced modeling capabilities provided by Blender with state-of-the-art Monte Carlo (MC) light simulation techniques and GPU acceleration. It uses Blender's user-friendly computer-aided-design (CAD) interface as the front-end to allow creations of complex domains, making it easy-to-use for less-experienced users to create sophisticated optical simulations needed for a wide range of biophotonics applications.

If you use BlenderPhotonics in your research, please cite the below paper:

Yuxuan Zhang and Qianqian Fang, "BlenderPhotonics: an integrated open-source software environment for three-dimensional meshing and photon simulations in complex tissues", J. of Biomedical Optics, 27(8), 083014 (2022) doi: https://doi.org/10.1117/1.JBO.27.8.083014

Installation
-------------
1. Install Blender (4.4 or higher)
2. Download BlenderPhotonics as zip
3. Install BlenderPhotnics in Blender: Edit->Preference->Add-ons->Install from Disk. Select BlenderPhotnics.zip to install
4. Navigate to the main page, where BlenderPhotonics should appear in the sidebar. Open BlenderPhotonics, and the Dependencies tab will automatically verify the installation of the required dependencies.
5. Click "Install All", wait a while (~ 5 min) to finished all preparation work
6. Dependencies tap will display 'All dependencies available'. Restart Blender to initialize BlenderPhotonics.

![](http://neurojson.org/wiki/upload/blenderphotonics_install.png)

Quick Start
-------------
1. Construct the model: At 3D Viewport Shift + A, select Mesh->Cube. Add a cube to the scene.
2. Open the PMCX tab in BlenderPhotonics and click "convert scene to voxel mesh".
3. Change 3D Viewport to "Rendered", to check voxel mesh quility
4. Click "Load voxel mesh and setup simulation" button.
5. Setup light source position, direction and then setup light source paramater at Lightsource's custom properties.
6. Setup optocial paramater for each region.
7. Click "Run PMCX Simulation" to start mcx simulation.
8. Once the simulation is finished, the results will be automatically loaded into Blender.