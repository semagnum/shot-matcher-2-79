bl_info = {
    "name": "Color Matching Analyzer",
    "author": "Spencer Magnusson",
    "version": (0, 5),
    "blender": (2, 79, 0),
    "description": "Analyzes colors of an image and applies it to the compositing tree.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
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
        #context.scene.midtone_color = (0.5, 0.5, 0.5)
        context.scene.min_color = (1.0, 1.0, 1.0)
        return {'FINISHED'}
        
class CMC_OT_image_calculator(bpy.types.Operator):
    bl_idname = "image.cmc_ot_image_calculator"
    bl_label = "Image Calculator"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        return context.edit_image is not None
    
    def execute(self, context):
        
        context.window.cursor_set("WAIT")
          
        current_img = context.edit_image 
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
        
        #disable midtone since not usable at the moment
        '''midtone_r = median(ch_r)
        midtone_g = median(ch_g)
        midtone_b = median(ch_b)
        context.scene.midtone_color = (midtone_r, midtone_g, midtone_b)'''
        
        context.scene.max_color = (max_r, max_g, max_b)
        context.scene.min_color = (min_r, min_g, min_b)
        
        context.window.cursor_set("DEFAULT")
        
        return {'FINISHED'}
    
class CMN_OT_add_color_matching_node(bpy.types.Operator):
    bl_idname = "node.cmn_ot_add_color_matching_node"
    bl_label = "Add Min/Max Color Balance to Compositor"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        return context.edit_image is not None
    
    def execute(self, context):
        context.scene.use_nodes = True
        tree = context.scene.node_tree
        
        #create color balance node
        node_label = "Color-Matched Color Balance"
        color_node = tree.nodes.get(node_label)

        if color_node is None:
            color_node = tree.nodes.new(type='CompositorNodeColorBalance')
            color_node.label = node_label
            color_node.name = node_label
            
        color_node.correction_method = 'OFFSET_POWER_SLOPE'
        color_node.offset = context.scene.min_color
        color_node.slope = context.scene.max_color - context.scene.min_color
        
        image_node_label = "Selected Background Image" 
        image_node = tree.nodes.get(image_node_label)
        
        #create image texture node
        if image_node is None:
            image_node = tree.nodes.new(type="CompositorNodeImage")
            image_node.name = image_node_label
            image_node.label = image_node_label
            image_node.location = 100, 400
        
        image_node.image = bpy.data.images[context.edit_image.name]
        
        #create alpha over node
        alpha_over_node_label = "BG/Render Alpha Over" 
        alpha_over_node = tree.nodes.get(alpha_over_node_label)
        
        if alpha_over_node is None:
            alpha_over_node = tree.nodes.new(type="CompositorNodeAlphaOver")
            alpha_over_node.name = alpha_over_node_label
            alpha_over_node.label = alpha_over_node_label
            alpha_over_node.location = 600, 200
            alpha_over_node.use_premultiply = True
            
        #create/get composite node
        comp_node = tree.nodes.get("Composite")
        
        if comp_node is None:
            comp_node = tree.nodes.new(type="CompositorNodeComposite")
            comp_node.location = 1000, 150
            
        #bring it all together
        tree.links.new(image_node.outputs[0], alpha_over_node.inputs[1])
        tree.links.new(color_node.outputs[0], alpha_over_node.inputs[2])
        tree.links.new(alpha_over_node.outputs[0], comp_node.inputs[0])
        
        #switch views
        context.area.type = 'NODE_EDITOR'
        context.space_data.tree_type = 'CompositorNodeTree'

        
        return {'FINISHED'}
    
class CMP_OT_color_picker(bpy.types.Operator):
    bl_idname = "image.cmp_ot_color_picker"
    bl_label = "Min Max Color Picker"

    
    @classmethod
    def poll(cls, context):
        return context.edit_image is not None

    def modal(self, context, event):
        
        context.window.cursor_set("EYEDROPPER")

        context.area.header_text_set("Ctrl + Mouse: pick max/min colors, LMB/RMB: finish and apply, ESC: cancel")
        
        if event.type == 'MOUSEMOVE':
            if event.ctrl:
                print("pick")
                mouse_x = event.mouse_x - context.region.x
                mouse_y = event.mouse_y - context.region.y
                uv = context.area.regions[-1].view2d.region_to_view(mouse_x, mouse_y)
                img = context.edit_image
                size_x, size_y = img.size[:]
                x = int(size_x * uv[0]) % size_x
                y = int(size_y * uv[1]) % size_y
                offset = (y * size_x + x) * 4
                pixels = img.pixels[offset:offset+3]
                #check max for each channel
                if pixels[0] > self.max_r:
                    self.max_r = pixels[0]
                if pixels[1] > self.max_g:
                    self.max_g = pixels[1]
                if pixels[2] > self.max_b:
                    self.max_b = pixels[2]                
                #check min for each channel
                if pixels[0] < self.min_r:
                    self.min_r = pixels[0]
                if pixels[1] < self.min_g:
                    self.min_g = pixels[1]
                if pixels[2] < self.min_b:
                    self.min_b = pixels[2]        
        elif event.type in {'RIGHTMOUSE', 'LEFTMOUSE'}:
            context.scene.min_color = (self.min_r, self.min_g, self.min_b)
            context.scene.max_color = (self.max_r, self.max_g, self.max_b)
            context.area.header_text_set()
            context.window.cursor_set("DEFAULT")
            return {'FINISHED'}
        elif event.type == 'ESC':
            context.window.cursor_set("DEFAULT")
            context.area.header_text_set()
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        self.min_r = context.scene.min_color[0]
        self.min_g = context.scene.min_color[1]
        self.min_b = context.scene.min_color[2]
        self.max_r = context.scene.max_color[0]
        self.max_g = context.scene.max_color[1]
        self.max_b = context.scene.max_color[2]
        
        if context.area.type == 'IMAGE_EDITOR' and context.edit_image is not None:
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "UV/Image Editor not found, cannot run operator")
            return {'CANCELLED'}
        
class CMP_PT_color_matching(bpy.types.Panel):
    bl_idname = "image.cmp_pt_color_matching"
    bl_space_type = 'IMAGE_EDITOR'
    bl_label = "Color-Matching Analysis"
    bl_category = "Color-Matching"
    bl_region_type = 'UI'
    
    def draw(self, context):
        
        layout = self.layout
        layout.prop(context.scene, "max_color", text='Max Color')
        #layout.prop(context.scene, "midtone_color", text='Midtone Color')
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
    #midtone not usable at the moment
    '''bpy.types.Scene.midtone_color = bpy.props.FloatVectorProperty(
        default=(0.5, 0.5, 0.5),
        min=0.0,
        precision=4,
        subtype='COLOR')'''
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
        utils.unregister_class(cls)

if __name__ == "__main__":
    register()
