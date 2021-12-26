import bpy
import oct2py as op
import numpy as np
import jdata as jd
import os
from .utils import *

g_maxvol=100
g_radbound=10
g_distbound=1.0
g_isovalue=0.5
g_imagetype="multi-label"
g_method="auto"

class nii2mesh(bpy.types.Operator):
    bl_label = 'Convert 3-D image file to mesh'
    bl_description = "Click this button to convert a 3D volume stored in JNIfTI (.jnii/.bnii, see http://neurojson.org) or NIfTI (.nii/.nii.gz) or .mat file to a mesh"
    bl_idname = 'blenderphotonics.creatregion'

    # creat a interface to set uesrs' model parameter.

    bl_options = {"REGISTER", "UNDO"}
    maxvol: bpy.props.FloatProperty(default=g_maxvol, name="Maximum tetrahedron volume")
    radbound: bpy.props.FloatProperty(default=g_radbound,name="Surface triangle maximum diameter")
    distbound: bpy.props.FloatProperty(default=g_distbound,name="Maximum deviation from true boundary")
    isovalue: bpy.props.FloatProperty(default=g_isovalue,name="Isovalue to create surface")
    imagetype: bpy.props.EnumProperty(name="Volume type", items = [('multi-label','multi-label','multi-label'), ('binary','binary','binary'), ('grayscale','grayscale','grayscale')])
    method: bpy.props.EnumProperty(name="Mesh extraction method", items = [('auto','auto','auto'),('cgalmesh','cgalmesh','cgalmesh'), ('cgalsurf','cgalsurf','cgalsurf'), ('simplify','simplify','simplify')])
 
    def vol2mesh(self):
        oc = op.Oct2Py()
        oc.addpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'script'))

        # Remove last .jmsh file
        outputdir = GetBPWorkFolder()
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)
        if(os.path.exists(os.path.join(outputdir,'regionmesh.jmsh'))):
            os.remove(os.path.join(outputdir,'regionmesh.jmsh'))
        if(os.path.exists(os.path.join(outputdir,'volumemesh.jmsh'))):
            os.remove(os.path.join(outputdir,'volumemesh.jmsh'))

        # nii to mesh
        niipath = bpy.context.scene.blender_photonics.path
        print(niipath)
        if (len(niipath)==0):
            return
        jd.save({'niipath':niipath, 'maxvol':self.maxvol, 'radbound':self.radbound,'distbound':self.distbound, 'isovalue':self.isovalue,'imagetype':self.imagetype,'method':self.method},os.path.join(outputdir,'niipath.json'));

        oc.run(os.path.join(os.path.dirname(os.path.abspath(__file__)),'script','nii2mesh.m'))

        # import volum mesh to blender(just for user to check the result)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        regiondata=jd.load(os.path.join(outputdir,'regionmesh.jmsh'));
        n=len(regiondata.keys())-1

        # To import mesh.ply in batches
        for i in range (0,n):
            surfkey='MeshSurf('+str(i+1)+')'
            if(n==1):
                surfkey='MeshSurf'
            if (not isinstance(regiondata[surfkey], np.ndarray)):
                regiondata[surfkey]=np.asarray(regiondata[surfkey],dtype=np.uint32);
            regiondata[surfkey]-=1
            AddMeshFromNodeFace(regiondata['MeshNode'],regiondata[surfkey].tolist(),'region_'+str(i+1));

        bpy.context.space_data.shading.type = 'WIREFRAME'

        ShowMessageBox("Mesh generation is complete. The combined tetrahedral mesh is imported for inspection. To set optical properties for each region, please click 'Load mesh and setup simulation'", "BlenderPhotonics")

    def execute(self, context):
        self.vol2mesh()
        return {"FINISHED"}

    def invoke(self, context, event):
        global g_maxvol, g_radbound, g_distbound, g_imagetype, g_method
        self.maxvol = g_maxvol
        self.radbound = g_distbound
        self.distbound = g_distbound
        self.imagetype = g_imagetype
        self.method = g_method
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