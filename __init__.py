bl_info = {
    "name": "Color Matching Analyzer",
    "author": "Spencer Magnusson",
    "version": (0, 1),
    "blender": (2, 79, 0),
    "description": "Analyzes colors of an image and applies it to the compositing tree.",
    "support": "COMMUNITY",
    "category": "Node"
}

import bpy
from statistics import median        
        
class CMR_OT_color_reset(bpy.types.Operator):
    bl_idname = "image.cmr_ot_min_max_reset"
    bl_label = "Reset Min and Max Colors"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        context.scene.max_color = (0.0, 0.0, 0.0)
        context.scene.midtone_color = (0.5, 0.5, 0.5)
        context.scene.min_color = (1.0, 1.0, 1.0)
        return {'FINISHED'}
        
class CMC_OT_image_calculator(bpy.types.Operator):
    bl_idname = "image.cmc_ot_image_calculator"
    bl_label = "Image Calculator"
    bl_options = {'REGISTER'}
    
    def execute(self, context):   
        current_img = bpy.context.edit_image 
        pixels = current_img.pixels[:] # create a copy (tuple) for read-only access
        
        #slice the pixels into the RGB channels
        ch_r = pixels[0::4]
        #ch_r = sorted(ch_r)
        
        ch_g = pixels[1::4]
        #ch_g = sorted(ch_g)
        
        ch_b = pixels[2::4]
        #ch_b = sorted(ch_b)
        
        max_r = max(ch_r)
        max_g = max(ch_g)
        max_b = max(ch_b)
        min_r = min(ch_r)
        min_g = min(ch_g)
        min_b = min(ch_b)
        
        midtone_r = median(ch_r)
        midtone_g = median(ch_g)
        midtone_b = median(ch_b)
        
        context.scene.midtone_color = (midtone_r, midtone_g, midtone_b)
        context.scene.max_color = (max_r, max_g, max_b)
        context.scene.min_color = (min_r, min_g, min_b)
        
        
        return {'FINISHED'}
    
class CMN_OT_add_color_matching_node(bpy.types.Operator):
    bl_idname = "node.cmn_ot_add_color_matching_node"
    bl_label = "Add Min/Max Color Balance to Compositor"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
        
        node_label = "Color-Matched Color Balance"
        color_node = None

        if not node_label in [node.label for node in tree.nodes]:
            color_node = tree.nodes.new(type='CompositorNodeColorBalance')
            color_node.label = node_label
            color_node.name = node_label
        else:
            color_node = tree.nodes.get(node_label)
            
        color_node.correction_method = 'OFFSET_POWER_SLOPE'
        color_node.offset = context.scene.min_color
        color_node.slope = context.scene.max_color - context.scene.min_color
        
        return {'FINISHED'}
    
class CMP_OT_color_picker(bpy.types.Operator):
    bl_idname = "image.cmp_ot_color_picker"
    bl_label = "Min Max Color Picker"

    def modal(self, context, event):
        context.area.tag_redraw()
        
        min_rgb = context.scene.min_color
        max_rgb = context.scene.max_color
        
        context.area.header_text_set("LMB: pick max/min colors, RMB: finish and apply, ESC: cancel")
        
        if event.type == 'MOUSEMOVE':
            if self.lmb:
                mouse_x = event.mouse_x - context.region.x
                mouse_y = event.mouse_y - context.region.y


                uv = context.area.regions[-1].view2d.region_to_view(mouse_x, mouse_y)
                img = bpy.context.edit_image
                size_x, size_y = img.size[:]


                x = int(size_x * uv[0]) % size_x
                y = int(size_y * uv[1]) % size_y


                offset = (y * size_x + x) * 4
                pixels = img.pixels[offset:offset+3]

                #check max for each channel
                if pixels[0] > max_rgb[0]:
                    max_rgb[0] = pixels[0]
                if pixels[1] > max_rgb[1]:
                    max_rgb[1] = pixels[1]
                if pixels[2] > max_rgb[2]:
                    max_rgb[2] = pixels[2]
                
                #check min for each channel
                if pixels[0] < min_rgb[0]:
                    min_rgb[0] = pixels[0]
                if pixels[1] < min_rgb[1]:
                    min_rgb[1] = pixels[1]
                if pixels[2] < min_rgb[2]:
                    min_rgb[2] = pixels[2]
            
        elif event.type == 'LEFTMOUSE':
            self.lmb = (event.value == 'PRESS')
            
        elif event.type in {'RIGHTMOUSE'}:
            context.scene.min_color = min_rgb
            context.scene.max_color = max_rgb
            context.area.header_text_set()
            return {'FINISHED'}
        
        elif event.type in {'ESC'}:
            context.area.header_text_set()
            return {'FINISHED'}
            
        #allows other input events to pass
        #otherwise, "YOOUU SHALL NOT - PASSSSS!"   
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        self.lmb = False
        
        if context.area.type == 'IMAGE_EDITOR':
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        
        else:
            self.report({'WARNING'}, "UV/Image Editor not found, cannot run operator")
            return {'CANCELLED'}
        
class CMP_PT_color_matching(bpy.types.Panel):
    bl_idname = "image.cmp_pt_color_matching"
    bl_space_type = 'IMAGE_EDITOR'
    bl_label = "Color-Matching Analysis"
    bl_category = "B-VFX"
    bl_region_type = 'UI'
    
    def draw(self, context):
        
        layout = self.layout
        layout.prop(context.scene, "max_color", text='Max Color')
        layout.prop(context.scene, "midtone_color", text='Midtone Color')
        layout.prop(context.scene, "min_color", text='Min Color')
        
        row = layout.row()
        row.operator(CMC_OT_image_calculator.bl_idname, text = 'Calculate Picture', icon='SEQ_HISTOGRAM')
        row = layout.row()
        row.operator(CMP_OT_color_picker.bl_idname, text = 'Max/Min Color Picker', icon='EYEDROPPER')
        row.operator(CMR_OT_color_reset.bl_idname, text = 'Reset Color Picker', icon='IMAGE_ALPHA')
        layout.operator(CMN_OT_add_color_matching_node.bl_idname, text = 'Add to Compositor', icon='NODETREE')
        
        
classes = (CMR_OT_color_reset, CMC_OT_image_calculator, CMN_OT_add_color_matching_node, CMP_OT_color_picker, CMP_PT_color_matching)

def register():
    # To show the input in the left tool shelf, store 'bpy.props.~'.
    #   In draw() in the subclass of Panel, access the input value by 'context.scene'.
    #   In execute() in the class, access the input value by 'context.scene.float_input'.
    bpy.types.Scene.min_color = bpy.props.FloatVectorProperty(
        default=(0.0, 0.0, 0.0),
        min=0.0,
        precision=4,
        subtype='COLOR')
    bpy.types.Scene.midtone_color = bpy.props.FloatVectorProperty(
        default=(0.5, 0.5, 0.5),
        min=0.0,
        precision=4,
        subtype='COLOR')
    bpy.types.Scene.max_color = bpy.props.FloatVectorProperty(
        default=(1.0, 1.0, 1.0),
        min=0.0,
        precision=4,
        subtype='COLOR')
        
    for cls in classes:
        bpy.utils.register_class(cls)
    
 
def unregister():
    del bpy.types.Scene.min_color, bpy.types.Scene.max_color
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()
