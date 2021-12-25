import bpy


def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def AddMeshFromNodeFace(node,face,name):

    # Create mesh and related object
    my_mesh=bpy.data.meshes.new(name)
    my_obj=bpy.data.objects.new(name,my_mesh)

    # Set object location in 3D space
    my_obj.location = bpy.context.scene.cursor.location 

    # make collection
    rootcoll=bpy.context.scene.collection.children.get("Collection")

    # Link object to the scene collection
    rootcoll.objects.link(my_obj)

    # Create object using blender function
    my_mesh.from_pydata(node,[],face)
    my_mesh.update(calc_edges=True)