import bpy
import oct2py as op
import numpy as np
import scipy.io
import os
import tempfile
from .dialogs import ShowMessageBox

g_maxvol=1.0
g_keepratio=1.0
g_mergetol=0
g_dorepair=False
g_tetgenopt=""

class scene2mesh(bpy.types.Operator):
    bl_label = 'Convert scene to tetra mesh'
    bl_description = "Create 3-D tetrahedral meshes using Iso2Mesh and Octave (please save your Blender session first!)"
    bl_idname = 'blenderphotonics.create3dmesh'

    # creat a interface to set uesrs' model parameter.

    bl_options = {"REGISTER", "UNDO"}
    maxvol: bpy.props.FloatProperty(default=g_maxvol, name="Maximum tetrahedron volume")
    keepratio: bpy.props.FloatProperty(default=g_keepratio,name="Percent of edges to be kept (0-1)")
    mergetol: bpy.props.FloatProperty(default=g_mergetol,name="Tolerance to merge nodes (0 to disable)")
    dorepair: bpy.props.BoolProperty(default=g_dorepair,name="Repair mesh (single object only)")
    tetgenopt: bpy.props.StringProperty(default=g_tetgenopt,name="Additional tetgen flags")

    def func(self):
        oc = op.Oct2Py()
        print(os.path.join(os.path.dirname(os.path.abspath(__file__)+'script')))
        oc.addpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'script'))
        
        #remove camera and light
        for ob in bpy.context.scene.objects:
            ob.select_set(False)
            print(ob.type)
            if ob.type == 'CAMERA' or ob.type == 'LIGHT':
                ob.select_set(True)

        bpy.ops.object.delete()

        obj = bpy.context.view_layer.objects.active
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.convert(target='MESH')
        if len(bpy.context.selected_objects)>=2:
            bpy.ops.object.join()

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        try:
            bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE', solver='EXACT')
            print("use exact intersection solver")
        except:
            bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE')
            print("use fast intersection solver")

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

        #output mesh data to Octave
        # this works only in object mode,
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        obj = bpy.context.view_layer.objects.active
        verts = []
        for n in range(len(obj.data.vertices)):
            vert = obj.data.vertices[n].co
            v_global = obj.matrix_world @ vert
            verts.append(v_global)
        edges = [edge.vertices[:] for edge in obj.data.edges]
        faces = [face.vertices[:] for face in obj.data.polygons]

        v = np.array(verts)
        f = np.array(faces)
        
        # Remove previous .stl file
        outputdir = os.path.join(tempfile.gettempdir(),'iso2mesh-'+os.environ.get('USER'),'blenderphotonics');
        if not os.path.isdir(outputdir):
            os.mkdir(outputdir)

        lst_ply = os.listdir(outputdir)
        c=0
        for item in lst_ply:
            fileName, fileExtension = os.path.splitext(lst_ply[c])
            if fileExtension == ".stl":
                os.remove(os.path.join(outputdir,item))
                print ("Delete File: " + os.path.join(outputdir,item))
            c=c+1

        # Save file
        scipy.io.savemat(os.path.join(outputdir,'blendermesh.mat'), mdict={'v':v, 'f':f, 'keepratio':self.keepratio, 'maxvol':self.maxvol, 'mergetol':self.mergetol, 'dorepair':self.dorepair, 'tetgenopt':self.tetgenopt})
        oc.run(os.path.join(os.path.dirname(os.path.abspath(__file__)),'script','blender2mesh.m'))

        # import volum mesh to blender(just for user to check the result)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        bpy.ops.import_mesh.stl(filepath=os.path.join(outputdir,'volumic_mesh.stl'), files=[{'name': os.path.join(outputdir,'volumic_mesh.stl')}], directory=outputdir, filter_glob="*.stl")
	
        bpy.context.space_data.shading.type = 'WIREFRAME'


        ShowMessageBox("Mesh generation is complete. The combined tetrahedral mesh is imported for inspection. To set optical properties for each region, please click 'Load mesh and setup simulation'", "BlenderPhotonics")

    def execute(self, context):
        print("begin to genert volumic mesh")
        self.func()
        return {"FINISHED"}

    def invoke(self, context, event):
        global g_maxvol, g_keepratio, g_mergetol, g_dorepair, g_tetgenopt
        self.maxvol = g_maxvol
        self.keepratio = g_keepratio
        self.mergetol = g_mergetol
        self.dorepair = g_dorepair
        self.tetgenopt = g_tetgenopt
        return context.window_manager.invoke_props_dialog(self)


#
#   Dialog to set meshing properties
#
class setmeshingprop(bpy.types.Panel):
    bl_label = "Mesh generation setting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global g_maxvol, g_keepratio, g_mergetol, g_dorepair, g_tetgenopt
        self.layout.operator("object.dialog_operator")
