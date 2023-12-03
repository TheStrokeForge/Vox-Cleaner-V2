
#   ██╗░░░██╗░█████╗░██╗░░██╗   ░█████╗░██╗░░░░░███████╗░█████╗░███╗░░██╗███████╗██████╗░    ██╗░░░██╗██████╗░
#   ██║░░░██║██╔══██╗╚██╗██╔╝   ██╔══██╗██║░░░░░██╔════╝██╔══██╗████╗░██║██╔════╝██╔══██╗    ██║░░░██║╚════██╗
#   ╚██╗░██╔╝██║░░██║░╚███╔╝░   ██║░░╚═╝██║░░░░░█████╗░░███████║██╔██╗██║█████╗░░██████╔╝    ╚██╗░██╔╝░░███╔═╝
#   ░╚████╔╝░██║░░██║░██╔██╗░   ██║░░██╗██║░░░░░██╔══╝░░██╔══██║██║╚████║██╔══╝░░██╔══██╗    ░╚████╔╝░██╔══╝░░
#   ░░╚██╔╝░░╚█████╔╝██╔╝╚██╗   ╚█████╔╝███████╗███████╗██║░░██║██║░╚███║███████╗██║░░██║    ░░╚██╔╝░░███████╗
#   ░░░╚═╝░░░░╚════╝░╚═╝░░╚═╝   ░╚════╝░╚══════╝╚══════╝╚═╝░░╚═╝╚═╝░░╚══╝╚══════╝╚═╝░░╚═╝    ░░░╚═╝░░░╚══════╝
#
#                                                    █▄▄ █▄█   █▀▀ ▄▀█ █▀█ █░█ ▄▀█ █▄░█   █▀ █░█ ▄▀█ █ █▄▀ █░█
#                                                    █▄█ ░█░   █▀░ █▀█ █▀▄ █▀█ █▀█ █░▀█   ▄█ █▀█ █▀█ █ █░█ █▀█
#

'''
VoxCleaner © 2021 by Farhan Shaikh is licensed under CC BY 4.0. 

License: CC-BY
Users are free to copy, adapt, remix, and redistribute the content - even commercially. User must give appropriate credit to the creator.
Read more about the license: https://creativecommons.org/licenses/by/4.0/

Thanks so much for your purchase and please feel free to tag me @TheStrokeForge on Instagram/Twitter and I’d love to see your work! Cheers!

'''

bl_info = {
    "name": "Vox Cleaner V2",
    "author": "Farhan Shaikh",
    "version": (2, 0),
    "blender": (3 ,0 , 0),
    "location": "View3D > Sidebar/N-Panel > Vox Cleaner",
    "description": "A Voxel Suite that can handle Voxel Model Cleaning, UV Unwrapping, Texture Baking and Exports",
    "warning": "",
    "doc_url": "https://www.thestrokeforge.xyz/vox-cleaner",
    "category": "Voxel Suite",
    }
    

from distutils.log import warn
from email.policy import default
from logging import error, exception
from types import NoneType
import bpy
import numpy as np
import os, sys, subprocess
import math
import bmesh
import gpu


class FlowData:
    MainObj = 0
    MainObjName = None
    DupeObj = 0
    DupeObjName = None
    ObjArray = None

    VertexCountInitialX = 0
    VertexCountFinalX = 0

    SmallestEdge = None
    SmallestEdgeLength = 10000000.0

    LargestEdge = None
    LargestEdgeLength = 0.0
    LargestEdgeBlocks = 0
    LargestUVEdgeLengthInPixels = 0.0
    ResizeFactor = 0.0

    ApproxLen = 0.0
    AutoRes = 0
    

class MetaData:
    CleanTimes = 0
    BakeTimes = 0
    ProcessRunning = False
    MissingActors = False
    ProperVoxel = True


class StaticData:
    StandardBakeResolutions = [8,16,32,64,128,256,512,1024,2048,4096,8192]
    BakeResolutions = [8,16,24,32,48,64,96,128,192,256,384,512,768,1024,1536,2048,3072,4096,6144,8192]
    TriangulateLoops = 8
    
    ResolutionDefault = "Mini"
    BaseColorDefault = (0.6,0.0,0.2,1.0)
    AlphaDefault = False
    ModelBackupDefault = True
    TriangulateDefault = True
    

    ButtonHeight = 1.5
    ButtonHeightMedium = 1.2
    CleanModePaneHeight = 1
    RowSpacing = 1
    SeperatorSpacing1 = 0.5
    SeperatorSpacing2 = 0.1
    SeperatorSpacing3 = 0.2


class MyProperties(bpy.types.PropertyGroup):
    BaseColor : bpy.props.FloatVectorProperty(name='Base Color',subtype='COLOR_GAMMA',size=4, min=0.0, max=1.0, precision=4, default = StaticData.BaseColorDefault, description="""Base color of the generated image.
Ps, This color won't be visible on the final cleaned model, is just for easier visibility""")
    
    AlphaBool: bpy.props.BoolProperty(name="Base Image has Alpha", description="Should the generated image have alpha?",default = False)

    CreateBackup: bpy.props.BoolProperty(name="Create model backup", description="Enabling this option preserves a version of the original model in the scene", default = StaticData.ModelBackupDefault)

    TriangulatedExport: bpy.props.BoolProperty(name="Export Triangulated model", description="""Enabling triangulates the model before exporting.
(Enabling is Recommended)""",default = StaticData.TriangulateDefault)

    ExportLocation : bpy.props.StringProperty(name="", description="Directory where your objects will be exported.", subtype="DIR_PATH",default = "")
    
    CleanMode : bpy.props.EnumProperty(
        items = [("ez", "Lazy Clean", "Used for fast, one-click cleaning. Cleaned models have automatic Pixel-Perfect UVs", 1),("hard", "2-Step Clean", "Used on a single object for detail oriented cleaning. Allows you to have control over aspects like custom UVs.", 2),],
        description="""Mode of Cleaning.
● Use lazy clean for fast, one-click cleaning.
● Use 2-Step clean for more controlled cleaning like custom UVs.

Mode of cleaning you're hovering on""",default = "ez")

    ResolutionSet : bpy.props.EnumProperty(
        name = "",
        items = [("Stan", "8,16,32,64,128...", "The Set of Standard image sizes like [8,16,32,64,128,256...]"),("Inter", "8,16,24,32,48...", "The set of Intermediate image sizes like [8,16,24,32,48,64,96...]"),("Mini", "Smallest Possible", "The smallest image size possible, not following any set.")],
        description="""Resolution Set Selection.
Select the 1st(Standard) or the 2nd(Intermediate) options for specified resolutions.
Select the 3rd(Mini) option for the smallest possible resolutions. 

Resolution Set you're hovering on""",default = StaticData.ResolutionDefault)

class VoxMethods():        

    def MrChecker(context):
        if bpy.context.mode == 'OBJECT':
            if MetaData.ProcessRunning == False:
                if len(bpy.context.selected_objects) == 1:
                    if bpy.context.active_object == bpy.context.selected_objects[0]:
                        if bpy.context.active_object.type == 'MESH':
                            return 1,1,1
                        else: 
                            return "Select object of type MESH","Select object of type MESH","Select object of type MESH"
                    else:
                        return "Select the object properly","Select the object properly","Select the object properly"
                    
                elif len(bpy.context.selected_objects) >1:    
                    return "Please select a single object","Please select a single object","Please select a single object"
                else:
                    return "Please select an object","Please select an object","Please select an object"
            else:
                return "2 Step Process is running. Finish that first.", 1, "2 Step Process is running. Finish that first."
        else:
            return "Enter object mode to clean","Enter object mode to clean","Enter object mode for exports"

    def NextNamePlease(name):
        if name.rfind("_Backup") != -1:
            trail = name[name.rfind("_Backup")+7:]
            if trail == "":
                name = name[:name.rfind("_Backup")+7]+"2"
                return name
            else:
                if trail.isnumeric():
                    trail = str(int(trail)+1)
                    name = name[:name.rfind("_Backup")+7]+trail
                    return name
                else:
                    name = name + "_Backup"
                    return name
        else:
            name = name + "_Backup"
            return name

    def TriangulateModel(context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.object.editmode_toggle()

    def ModelFixing(context):
        
        MetaData.ProcessRunning = True
        
        #set main object and its name
        FlowData.MainObj = bpy.context.active_object
        FlowData.MainObjName = bpy.context.active_object.name
        FlowData.MainObj.hide_render = False

        
        FlowData.VertexCountInitialX = len(FlowData.MainObj.data.vertices)
        

        #Merge all vertices
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        #Fix Shading
        bpy.context.object.data.use_auto_smooth = False
        bpy.ops.object.shade_flat()
        
        bpy.ops.object.select_all(action='DESELECT')

        #Detect if model is improper
        MetaData.ProperVoxel = True
        
        FlowData.MainObj.select_set(True)
        bpy.context.view_layer.objects.active = FlowData.MainObj
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        bm = bmesh.from_edit_mesh(FlowData.MainObj.data)
        try:
            for e in bm.edges:
                EdgeAngle = round(math.degrees(e.calc_face_angle()),3)
                
                if EdgeAngle == 0.0:
                    continue
                elif EdgeAngle == 90.0:
                    continue
                else:
                    MetaData.ProperVoxel = False
                    break
        except ValueError:
            #print("okay theres 1",e)
            pass

        print(MetaData.ProperVoxel)
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        #duplicate the main obj, set and name dupe
        bpy.ops.object.duplicate()
        FlowData.DupeObj = bpy.context.active_object
        
        #Backup Name calculation
        #name = FlowData.MainObjName

        FlowData.DupeObj.name = VoxMethods.NextNamePlease(FlowData.MainObjName)
        FlowData.DupeObjName = FlowData.DupeObj.name
        #name = None   

        #Hide Dupe obj
        FlowData.DupeObj.hide_set(True)

    def MaterialSetUp(context):
        
        scene = context.scene
        mytool = scene.my_tool

        #remove then add a new material
        FlowData.MainObj.data.materials.clear()

        ImageMaterial = bpy.data.materials.new(name = FlowData.MainObj.name + "_Material")
        FlowData.MainObj.data.materials.append(ImageMaterial)

        #edit the material
        ImageMaterial.use_nodes = True

        nodes = ImageMaterial.node_tree.nodes

        #ImageTex
        ImageTextureNode = nodes.new(type = 'ShaderNodeTexImage')
        ImageTextureNode.interpolation = 'Closest'
        ImageTextureNode.location = (80,115)

        #PrincipledBSDF
        PrincipledBSDF = nodes.get('Principled BSDF')
        PrincipledBSDF.location = (370,195)

        #MaterialOutput
        MO = nodes.get('Material Output')
        MO.location = (680,220)
        
        Links = ImageMaterial.node_tree.links
        l1 = Links.new(ImageTextureNode.outputs[0], PrincipledBSDF.inputs[0])
        l7 = Links.new(PrincipledBSDF.outputs[0], MO.inputs[0])

    def UVProjection(context):

        scene = context.scene
        mytool = scene.my_tool
        
        bpy.ops.object.select_all(action='DESELECT')
        
        FlowData.MainObj.select_set(True)
        bpy.context.view_layer.objects.active = FlowData.MainObj
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        bpy.ops.object.mode_set(mode = 'EDIT')

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.cube_project(cube_size=1)
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(rotate=False, margin=0, shape_method='AABB')


        ob = FlowData.MainObj
        bm = bmesh.from_edit_mesh(ob.data)


        bpy.ops.mesh.select_all(action='DESELECT')

        FlowData.SmallestEdge = None
        FlowData.SmallestEdgeLength = 1000000000000.0

        for e in bm.edges:
            if e.calc_length() < FlowData.SmallestEdgeLength:
                bpy.ops.mesh.select_all(action='DESELECT')
                FlowData.SmallestEdgeLength = e.calc_length()
                e.select = True
                FlowData.SmallestEdge = e

        uv_layer = bm.loops.layers.uv.active

        a = FlowData.SmallestEdge.link_loops[0][uv_layer].uv
        b = FlowData.SmallestEdge.link_loops[0].link_loop_next[uv_layer].uv

        FractionDistance = math.dist(a, b)
        #print("Fractal Dist",FractionDistance)
        FlowData.ApproxLen = 1/FractionDistance

        bpy.ops.object.mode_set(mode = 'OBJECT')

        #Pick an image resolution
        if mytool.ResolutionSet == 'Stan':
            for resolution in StaticData.StandardBakeResolutions:
                if FlowData.ApproxLen <= resolution:
                    FlowData.AutoRes = resolution
                    break
        elif mytool.ResolutionSet == 'Inter':
            for resolution in StaticData.BakeResolutions:
                if FlowData.ApproxLen <= resolution:
                    FlowData.AutoRes = resolution
                    break
        else:
            FlowData.AutoRes = math.ceil(FlowData.ApproxLen)

        GeneratedTex = bpy.data.images.new(FlowData.MainObj.name + "_Tex", int(FlowData.AutoRes), int(FlowData.AutoRes), alpha = mytool.AlphaBool)
        bpy.data.images[FlowData.MainObj.name + "_Tex"].generated_color = (mytool.BaseColor[0],mytool.BaseColor[1],mytool.BaseColor[2],mytool.BaseColor[3])
            
        FlowData.MainObj.data.materials[0].node_tree.nodes["Image Texture"].image = GeneratedTex
        
        #Set that image in the uv editor, if uv editor is available
        for Screen in bpy.data.screens:
            for area in Screen.areas:
                if area.type == 'IMAGE_EDITOR' :
                    area.spaces.active.image = GeneratedTex
                    
    def GeometryCleanUp(context):
        
        #Add and apply modifiers
        FlowData.MainObj.modifiers.new("MrCleaner",'DECIMATE')
        FlowData.MainObj.modifiers["MrCleaner"].decimate_type = 'DISSOLVE'
        FlowData.MainObj.modifiers["MrCleaner"].delimit = {'SHARP'}
        bpy.ops.object.modifier_apply(modifier="MrCleaner", report=True)

        # select main
        FlowData.MainObj.select_set(False)
        FlowData.DupeObj.select_set(False)
        bpy.context.view_layer.objects.active = FlowData.MainObj
        
        # Triangulate Dissolve Loop------
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        i = 0
        while i<StaticData.TriangulateLoops:
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            bpy.ops.mesh.dissolve_limited(angle_limit=0.0872665, delimit={'SHARP'}, use_dissolve_boundaries=False)
            i+=1
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        FlowData.VertexCountFinalX = len(FlowData.MainObj.data.vertices)

    def UVScaling(context):

        #actually scale the UVs according to ScaleFactor n cursor location-------------------------------------can be done with lighter detail

        bpy.ops.object.mode_set(mode = 'EDIT')
        ob = FlowData.MainObj
        bm = bmesh.from_edit_mesh(ob.data)

        bpy.ops.mesh.select_all(action='DESELECT')
        for le in bm.edges:
            if le.calc_length() > FlowData.LargestEdgeLength:
                bpy.ops.mesh.select_all(action='DESELECT')
                FlowData.LargestEdgeLength = le.calc_length()
                le.select = True
                FlowData.LargestEdge = le
        
        FlowData.LargestEdgeBlocks = round(FlowData.LargestEdgeLength/FlowData.SmallestEdgeLength,0)

        uv_layer = bm.loops.layers.uv.active

        p = FlowData.LargestEdge.link_loops[0][uv_layer].uv*FlowData.AutoRes
        q = FlowData.LargestEdge.link_loops[0].link_loop_next[uv_layer].uv*FlowData.AutoRes

        FlowData.LargestUVEdgeLengthInPixels = math.dist(p, q)

        FlowData.ResizeFactor = FlowData.LargestEdgeBlocks/FlowData.LargestUVEdgeLengthInPixels
        bpy.ops.object.mode_set(mode = 'OBJECT')

        ob = FlowData.MainObj

        bpy.ops.object.mode_set(mode = 'EDIT')
        
        bpy.ops.uv.select_all(action='SELECT')
        bm = bmesh.from_edit_mesh(ob.data)
        uv_layer = bm.loops.layers.uv.verify()
        
        for Screen in bpy.data.screens:
            for area in Screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    area.spaces.active.cursor_location[0] = 0
                    area.spaces.active.cursor_location[1] = 0
                    area.spaces.active.pivot_point = 'CURSOR'
        
        for face in bm.faces:
            for loop in face.loops:
                loop_uv = loop[uv_layer]
                
                loop_uv.uv *= FlowData.ResizeFactor
        
        bpy.ops.mesh.select_all(action='SELECT')

        #AreaType = bpy.context.area.type
        #bpy.context.area.type = 'IMAGE_EDITOR'
        #bpy.ops.uv.snap_selected(target='PIXELS')
        #bpy.context.area.type = AreaType
        

        bpy.ops.object.mode_set(mode = 'OBJECT')

        MetaData.CleanTimes = MetaData.CleanTimes+1

    def TextureBake(context):

        scene = context.scene
        mytool = scene.my_tool

        RenderEngine = bpy.context.scene.render.engine

        FlowData.DupeObj.hide_set(False) 

        #Select objects in order
        bpy.ops.object.select_all(action='DESELECT')
        FlowData.MainObj.select_set(True)
        FlowData.DupeObj.select_set(True)
        bpy.context.view_layer.objects.active = FlowData.MainObj

        #set bake settings
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.device = 'GPU'

        bpy.context.scene.cycles.bake_type = 'DIFFUSE'
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False
        if MetaData.BakeTimes >=1:                     #Not the 1st time baking
            bpy.context.scene.render.bake.use_clear = True
        else:
            bpy.context.scene.render.bake.use_clear = False
        bpy.context.scene.render.bake.use_selected_to_active = True
        bpy.context.scene.render.bake.cage_extrusion = 0.01
        bpy.context.scene.render.bake.max_ray_distance = 0.1
        
        bpy.context.scene.render.bake.margin = 0      #margin


        bpy.ops.object.bake(type='DIFFUSE')

        FlowData.DupeObj.hide_set(True)

        bpy.context.scene.render.engine = RenderEngine
        
        MetaData.BakeTimes = MetaData.BakeTimes+1
    
    def EndProcess(context):

        scene = context.scene
        mytool = scene.my_tool
        
        #clear existing VColor Data in the object if it exists
        try:
            if FlowData.MainObj.data.vertex_colors.active != None:
                FlowData.MainObj.data.vertex_colors.remove(FlowData.MainObj.data.vertex_colors.active)
        except Exception: 
            pass
        
        #Print Existing FlowData n MetaData
        if MetaData.ProcessRunning:
            try:
                print('''
    ● METADATA--------------------------------------------------------''')
                print("  Model    (","Target:",FlowData.MainObjName,", Source:",FlowData.DupeObjName,", ProperVoxel:",MetaData.ProperVoxel,")")

                print("  Cleaning (","Initial:",FlowData.VertexCountInitialX,", Final:",FlowData.VertexCountFinalX,", Reduction:",round(100-(FlowData.VertexCountFinalX*100/FlowData.VertexCountInitialX),1),"%",")")

                print("  Geometry (","SmallestEdge:",FlowData.SmallestEdgeLength,", LargestEdge:",FlowData.LargestEdgeLength,", BlocksInLargestEdge:",FlowData.LargestEdgeBlocks,")")

                print("  Image    (","ApproxLen:",round(FlowData.ApproxLen,2),", ResolutionSet:",mytool.ResolutionSet,", AutoRes:",FlowData.AutoRes,")")
                
                print("  UV       (","LargestUVEdgeLength(px):",FlowData.LargestUVEdgeLengthInPixels,", ResizeFactor:",FlowData.ResizeFactor,", RescaledLength(px):",FlowData.LargestUVEdgeLengthInPixels*FlowData.ResizeFactor,")","")

                print("  Meta     (","MissingActors:",MetaData.MissingActors,", Cleaned:",MetaData.CleanTimes,"times, Baked:",MetaData.BakeTimes,"times )")
            except Exception: 
                print(Exception)
                
        #Pack the image for safety
        try:
            ObjectTexture = bpy.context.active_object.active_material.node_tree.nodes["Image Texture"].image
            ObjectTexture.pack()
        except:
            pass
                
        #delete backup if specified
        if not mytool.CreateBackup:
            FlowData.DupeObj.hide_set(False)
            FlowData.MainObj.select_set(False)
            FlowData.DupeObj.select_set(True)
            bpy.context.view_layer.objects.active = FlowData.DupeObj
            bpy.ops.object.delete(use_global=False)

        #Clear Existing FlowData n MetaData
        FlowData.MainObj = None
        FlowData.MainObjName = None
        FlowData.DupeObj = None
        FlowData.DupeObjName = None
        FlowData.ObjArray = None

        FlowData.VertexCountInitialX = FlowData.VertexCountFinalX = 0
        
        FlowData.SmallestEdge = None
        FlowData.SmallestEdgeLength = 10000000.0#

        FlowData.LargestEdge = None
        FlowData.LargestEdgeLength = 0.0#
        FlowData.LargestEdgeBlocks = 0#
        FlowData.LargestUVEdgeLengthInPixels = 0.0#
        FlowData.ResizeFactor = 0.0#
        
        FlowData.ApproxLen = 0.0
        FlowData.AutoRes = 0

        MetaData.CleanTimes = MetaData.BakeTimes = 0
        MetaData.ProperVoxel = True
        MetaData.MissingActors = False
        MetaData.ProcessRunning = False
        

        print('''  ProcessEnded GGs------------------------------------------------
        ''')

    def TextureExport(context,ImgFileName):

        scene = context.scene
        mytool = scene.my_tool

        ObjectTexture = bpy.context.active_object.active_material.node_tree.nodes["Image Texture"].image
        ObjectTexture.alpha_mode = 'STRAIGHT'
        FilePath = os.path.join(mytool.ExportLocation, ImgFileName)
        ObjectTexture.file_format='PNG'
        AreaType = bpy.context.area.type
        bpy.context.area.type = 'IMAGE_EDITOR'
        bpy.context.area.spaces.active.image = ObjectTexture 
        bpy.ops.image.save_as(save_as_render=False, copy=False, filepath=FilePath,show_multiview=False, use_multiview=False)
        bpy.context.area.type = AreaType


class ApplyVColors(bpy.types.Operator):
    """Apply the mesh's vertex colors as the base color.
Specifically made for .PLY meshes, as they have vertex color data present"""
    bl_idname = "voxcleaner.applyvertexcolors"
    bl_label = "Apply Vertex Colors"
    bl_options = {'UNDO'}

    def execute(self, context):
        if bpy.data.materials.get("VColorMaterial") is None:
                VMaterial = bpy.data.materials.new(name = "VColorMaterial")

                #edit the material
                VMaterial.use_nodes = True
                nodes = VMaterial.node_tree.nodes

                PrincipledBSDF = nodes.get('Principled BSDF')
                VertexColorNode = nodes.new(type = 'ShaderNodeVertexColor')
                VertexColorNode.location = (-280,80)

                Links = VMaterial.node_tree.links
                NewLink = Links.new(VertexColorNode.outputs[0], PrincipledBSDF.inputs[0])
        else:
            VMaterial = bpy.data.materials.get("VColorMaterial")

        if len(bpy.context.selected_objects) > 0:
            #remove then add a new material to everyone
            for x in bpy.context.selected_objects:
                if x.type == 'MESH':
                    try:
                        if x.data.vertex_colors.active != None:
                            x.data.materials.clear()
                            x.data.materials.append(VMaterial)
                    except Exception: 
                        pass
            
            if len(bpy.context.selected_objects) == 1:
                self.report({'INFO'}, "Vertex colors applied to selected object")
            else:
                self.report({'INFO'}, "Vertex colors applied to selected objects")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Select an object first")
            return {'CANCELLED'}
    
class PrepareForBake(bpy.types.Operator):
    """Clean the model geometry, set-up a material and generate a new image texture and finally project pixel-perfect UVs"""
    
    bl_idname = "voxcleaner.prepareforbake"
    bl_label = "Prepare For Bake"
    bl_options = {'UNDO'}

    def execute(self, context):

        EZStatus,StepStatus,ExportStatus = VoxMethods.MrChecker(context)
        
        if type(StepStatus) != int:
            self.report({'WARNING'}, StepStatus)
            return {'CANCELLED'}
        
        if MetaData.ProcessRunning == True and MetaData.CleanTimes>=1:
            self.report({'WARNING'}, "A 2 Step Process is running. Finish that first.")
            return {'CANCELLED'}

        VoxMethods.ModelFixing(context)
        VoxMethods.MaterialSetUp(context)
        
        VoxMethods.UVProjection(context)
        VoxMethods.GeometryCleanUp(context)
        VoxMethods.UVScaling(context)
        
        stmnt = "Ready For Texture Bake! "+str(round(100-(FlowData.VertexCountFinalX*100/FlowData.VertexCountInitialX),1))+"% vertex reduction!"
        self.report({'INFO'}, stmnt)
        return {'FINISHED'}

class PostUVBake(bpy.types.Operator):
    """Bake the texture from the Source model to the Target model.
Might take some time depending on the model's voxel density"""
    bl_idname = "voxcleaner.postuvbake"
    bl_label = "Bake Texture"
    bl_options = {'UNDO'}

    def execute(self, context):

        if MetaData.ProcessRunning:
            
            if MetaData.CleanTimes == 0:
                self.report({'WARNING'}, "Prepare a model for bake first!")
                return {'CANCELLED'}

            if MetaData.MissingActors:
                self.report({'WARNING'}, "Missing Objects! Re-do The process!")
                return {'CANCELLED'}

            if MetaData.CleanTimes>=1 and MetaData.MissingActors == False:
                VoxMethods.TextureBake(context)
                self.report({'INFO'}, "Bake Done!")
                return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Prepare a model for bake first!")
            return {'CANCELLED'}           

class LazyClean(bpy.types.Operator):
    """Lazy Clean selected models"""
    bl_idname = "voxcleaner.lazyclean"
    bl_label = "Easy Clean"
    bl_options = {'UNDO'}

    def execute(self, context):

        EZStatus,StepStatus,ExportStatus = VoxMethods.MrChecker(context)
        
        if type(EZStatus) == int:
            pass
        else:
            self.report({'WARNING'}, EZStatus)
            return {'CANCELLED'}
        
        VoxMethods.ModelFixing(context)
        MetaData.ProperVoxel
        VoxMethods.MaterialSetUp(context)
        
        VoxMethods.UVProjection(context)
        VoxMethods.GeometryCleanUp(context)
        VoxMethods.UVScaling(context)
        
        VoxMethods.TextureBake(context)
        
        CleanPercentage = round(100-(FlowData.VertexCountFinalX*100/FlowData.VertexCountInitialX),1)
            
        if MetaData.ProperVoxel:
            stmnt = "Model cleaned! "+str(CleanPercentage)+"% vertex reduction!"
        else:
            stmnt = str(CleanPercentage)+"% vertex reduction! Non Voxel model, results may not be accurate"
        
        VoxMethods.EndProcess(context)

        self.report({'INFO'}, stmnt)
        return {'FINISHED'}

class VoxTerminate(bpy.types.Operator):
    """Finish the ongoing 2-Step process"""
    bl_idname = "voxcleaner.terminate"
    bl_label = "Finish Cleaning"
    bl_options = {'UNDO'}

    def execute(self, context):
        
        if MetaData.ProcessRunning:
            VoxMethods.EndProcess(context)
            self.report({'INFO'}, 'Cleaning Done! Enjoy!')
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "2-Step Process is not running!")
            return {'CANCELLED'}
        
class OpenExportFolder(bpy.types.Operator):
    """Open The specified Export Folder in OS"""
    bl_idname = "voxcleaner.openexportfolder"
    bl_label = "Open Export Folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        mytool = context.scene.my_tool

        if len(mytool.ExportLocation) == 0:
            self.report({'WARNING'}, 'Please add an export location')
            return {'CANCELLED'}

        ExportDirectory = os.path.realpath(bpy.path.abspath(mytool.ExportLocation))

        if not os.path.exists(ExportDirectory):
            self.report({'WARNING'}, 'Export Location does not exist, please add another location')
            return {'CANCELLED'}
        else:
            if sys.platform == "win32":
                os.startfile(ExportDirectory)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.call(["open",ExportDirectory])
            else:   #Linux and others
                try:
                    import subprocess
                    subprocess.Popen(['xdg-open', ExportDirectory])
                except:
                    self.report({'WARNING'}, 'Sorry, Seems like you have an unsupported Operating System')
                    return {'CANCELLED'}
            
        return {'FINISHED'}

class ExportOBJ(bpy.types.Operator):
    """Export OBJ files of the selected meshes, with textures"""
    bl_idname = "voxcleaner.exportobj"
    bl_label = "Export OBJ"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        
        scene = context.scene
        mytool = scene.my_tool
        
        #Directory checks
        if len(mytool.ExportLocation) <= 0:
            self.report({'WARNING'}, 'Please add an export location')
            return {'CANCELLED'}

        ExportDirectory = os.path.realpath(bpy.path.abspath(mytool.ExportLocation))

        if not os.path.exists(ExportDirectory):
            #mytool.ExportLocation = ""
            self.report({'WARNING'}, 'Export Location does not exist, please add another location')
            return {'CANCELLED'}

        #Mr Checker Checks
        EZStatus,StepStatus,ExportStatus = VoxMethods.MrChecker(context)
        
        if type(ExportStatus) == int:
            ExportObjArray = bpy.context.selected_objects[0]
            
            #deselect everything
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = None
            
            #select ith obj
            bpy.context.view_layer.objects.active = ExportObjArray
            ExportObjArray.select_set(True)

            #Generate file names
            FileNameOBJ=ExportObjArray.name+'.obj'
            ImageFileName=ExportObjArray.name+'.png'

            #export Obj texture
            try:
                VoxMethods.TextureExport(context, ImageFileName)
            except Exception as e:
                pass
            
            #export Obj
            TargetFile = os.path.join(ExportDirectory, FileNameOBJ)
            bpy.ops.export_scene.obj(filepath=TargetFile, check_existing=True, axis_forward='-Z', axis_up='Y', filter_glob="*.obj;*.mtl", use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=True, use_smooth_groups=False, use_smooth_groups_bitflags=False, use_normals=True, use_uvs=True, use_materials=True, use_triangles=mytool.TriangulatedExport, use_nurbs=False, use_vertex_groups=False, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=False, global_scale=1, path_mode='AUTO')
            

            ExportObjArray.select_set(True)

            self.report({'INFO'}, "OBJ with textures exported!")
            return {'FINISHED'}
            
        else:
            self.report({'WARNING'}, ExportStatus)
            return {'CANCELLED'}

class ExportFBX(bpy.types.Operator):
    """Export FBX files of the selected meshes, with textures"""
    bl_idname = "voxcleaner.exportfbx"
    bl_label = "Export FBX"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        
        scene = context.scene
        mytool = scene.my_tool
        
        #Directory checks
        if len(mytool.ExportLocation) <= 0:
            self.report({'WARNING'}, 'Please add an export location')
            return {'CANCELLED'}

        ExportDirectory = os.path.realpath(bpy.path.abspath(mytool.ExportLocation))

        if not os.path.exists(ExportDirectory):
            #mytool.ExportLocation = ""
            self.report({'WARNING'}, 'Export Location does not exist, please add another location')
            return {'CANCELLED'}

        #Mr Checker Checks
        EZStatus,StepStatus,ExportStatus = VoxMethods.MrChecker(context)
        
        if type(ExportStatus) == int:
            ExportFbxArray = bpy.context.selected_objects[0]
           
            #deselect everything
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = None
            
            #select ith obj
            bpy.context.view_layer.objects.active = ExportFbxArray
            ExportFbxArray.select_set(True)

            #Generate file names
            FileNameOBJ=ExportFbxArray.name+'.fbx'
            ImageFileName=ExportFbxArray.name+'.png'

            #export fbx texture
            try:
                VoxMethods.TextureExport(context, ImageFileName)
            except Exception as e:
                pass
            
            #Export FBX
            if mytool.TriangulatedExport:
                #Dupe n do that triangulation
                bpy.ops.object.duplicate()
                TriaDommi = bpy.context.active_object
                VoxMethods.TriangulateModel(context)
                TargetFile = os.path.join(ExportDirectory, FileNameOBJ)
                bpy.ops.export_scene.fbx(filepath=str(TargetFile), use_selection=True, apply_scale_options = 'FBX_SCALE_ALL')
                TriaDommi.select_set(True)
                bpy.context.view_layer.objects.active = TriaDommi
                bpy.ops.object.delete(use_global=False)
            else:
                TargetFile = os.path.join(ExportDirectory, FileNameOBJ)
                bpy.ops.export_scene.fbx(filepath=str(TargetFile), use_selection=True, apply_scale_options = 'FBX_SCALE_ALL')


            ExportFbxArray.select_set(True)

            self.report({'INFO'}, "FBX with textures exported!")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, ExportStatus)
            return {'CANCELLED'}
        
class ResetSettings(bpy.types.Operator):
    """Reset all settings in the add-on"""
    bl_idname = "voxcleaner.resetsettings"
    bl_label = "Reset Settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        mytool = context.scene.my_tool
        mytool.ResolutionSet = StaticData.ResolutionDefault
        mytool.BaseColor = StaticData.BaseColorDefault
        mytool.AlphaBool = StaticData.AlphaDefault

        mytool.CreateBackup = StaticData.ModelBackupDefault
        mytool.TriangulatedExport = StaticData.TriangulateDefault

        return {'FINISHED'} 


#UI Panels--------------------------------------------------------------------------------------------------------------UI Panels
class VoxClean(bpy.types.Panel):
    #bl_parent_id = "VoxCleaner_PT_main_panel"
    bl_label = "Cleaner"
    
    bl_idname = "CLEANER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vox Cleaner"
    
    
    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='EXPERIMENTAL')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        
        #Mode Toggle
        box = layout.box()
        EZStatus,StepStatus,ExportStatus = VoxMethods.MrChecker(context)

        row = box.row()
        row.scale_y = StaticData.CleanModePaneHeight
        row.prop(mytool, "CleanMode", expand=True)

        if mytool.CleanMode == 'ez':
            if type(EZStatus) == int:
                row = box.row()
                row.scale_y = StaticData.ButtonHeight
                row.operator("voxcleaner.lazyclean",icon = 'SOLO_ON',text = 'Clean Model')
            else:
                #row = layout.row()
                box.label(icon="ERROR", text = EZStatus)

        if mytool.CleanMode == 'hard':
            if type(StepStatus) == int:
                col = box.column()

                if MetaData.ProcessRunning:
                    try:
                        Trg = str(FlowData.MainObj.name)
                    except:
                        Trg = "- Missing Object -"
                        MetaData.MissingActors = True
                    try:
                        Src = str(FlowData.DupeObj.name)
                    except:
                        Src = "- Missing Object -"
                        MetaData.MissingActors = True
                else:
                    Trg = "None"
                    Src = "None"

                col.label(text = "Target:  " + Trg)
                col.label(text = "Source:  " + Src)
                    
                col = box.column()         #Main Column
                
                row = col.row()
                if MetaData.ProcessRunning == True and MetaData.CleanTimes>=1:
                    row.enabled = False
                row.scale_y = StaticData.ButtonHeight
                row.operator("voxcleaner.prepareforbake", icon = 'TOOL_SETTINGS')
                
                row = col.row()                     #Spacing
                row.scale_y = StaticData.RowSpacing
                
                row = col.row()
                if MetaData.ProcessRunning == True and MetaData.CleanTimes>=1 and MetaData.MissingActors == False:
                    row.enabled = True
                else:
                    row.enabled = False
                    
                row.scale_y = StaticData.ButtonHeight
                row.operator("voxcleaner.postuvbake",icon = 'TEXTURE_DATA')

                
                if MetaData.ProcessRunning:
                    row = col.row()                     #Spacing
                    row.scale_y = StaticData.RowSpacing
                    
                    row = col.row()
                    row.scale_y = StaticData.ButtonHeight
                    
                    col.operator("voxcleaner.terminate",icon = 'CHECKMARK')
            else:
                box.label(icon="ERROR", text = StepStatus)
            
        #Clean
        col = layout.column()
        
        spacing = col.row()
        spacing.scale_y = StaticData.SeperatorSpacing2
        spacing.label(text = " ")
        
        row = col.row()
        row.scale_y = 1.2
        row.operator("voxcleaner.applyvertexcolors", icon = 'MATERIAL')


class VoxExport(bpy.types.Panel):
    #bl_parent_id = "VoxCleaner_PT_main_panel"
    bl_label = "Export"
    bl_idname = "EXPORT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vox Cleaner"
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='FOLDER_REDIRECT')

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        mytool = scene.my_tool

        #Export Panel
        col = layout.column()
        row = col.row(align=True)
        row.label(text="Export Path:")
        #row.prop(mytool, "export_path")
        row.prop(mytool, "ExportLocation")
        
        row = col.row()
        row.scale_y = 1.2
        row.operator("voxcleaner.openexportfolder",icon = 'FILEBROWSER')
        
        spacing = col.row()
        spacing.scale_y = StaticData.SeperatorSpacing2
        spacing.label(text = " ")
        
        box = layout.box()

        EZStatus,StepStatus,ExportStatus = VoxMethods.MrChecker(context)

        if type(ExportStatus) == int:
            #split = box.split()
            col = box.column()
            row = col.row()
            row.scale_y = StaticData.ButtonHeightMedium
            row.operator("voxcleaner.exportobj",icon = 'SNAP_FACE',text = "OBJ")
            row.operator("voxcleaner.exportfbx",icon = 'SNAP_FACE',text = "FBX")    
        else:
            box.label(icon="ERROR", text = ExportStatus)

class VoxSettings(bpy.types.Panel):
    #bl_parent_id = "VoxCleaner_PT_main_panel"
    bl_label = "Settings"
    
    bl_idname = "SETTINGS_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vox Cleaner"
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='PREFERENCES')

    def draw(self, context):
        layout = self.layout
    
        scene = context.scene
        mytool = scene.my_tool
        
        #Settings Panel
        col = layout.column()
        
        col.label(text = "Image Properties",icon = 'FILE_IMAGE')
        row = col.row(align=True)
        row.label(text = "Resolutions (px):")
        row.prop(mytool, "ResolutionSet")
        row = col.row()
        row.prop(mytool, "BaseColor")
        col.prop(mytool, "AlphaBool")
        
        
        spacing = col.row()
        spacing.scale_y = StaticData.SeperatorSpacing1
        spacing.label(text = " ")
        
        col.label(text = "Preferences",icon = 'PROPERTIES')
        col.prop(mytool, "CreateBackup")
        col.prop(mytool, "TriangulatedExport")


        spacing = col.row()
        spacing.scale_y = StaticData.SeperatorSpacing1
        spacing.label(text = " ")

        row = col.row()
        row.scale_y = 1.2
        row.operator("voxcleaner.resetsettings",icon = 'FILE_REFRESH')

        

classes = [ApplyVColors,MyProperties,LazyClean,PrepareForBake,PostUVBake,VoxTerminate,VoxClean,VoxExport,VoxSettings,ExportOBJ,ExportFBX,OpenExportFolder,ResetSettings]
 
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type= MyProperties)

        
def unregister():
    del bpy.types.Scene.my_tool

    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    
 
if __name__ == "__main__":
    register()