'''

Created by Spencer Magnusson
semagnum+blendermarket@gmail.com

'''

bl_info = {
    "name": 'Shot Matcher',
    "author": 'Spencer Magnusson',
    "version": (3, 0, 0),
    "blender": (2, 79, 0),
    "description": 'Analyzes colors of an image or movie clip and applies it to the compositing tree.',
    "location": 'Image Editor > UI > Shot Matcher & Movie Clip Editor > Tools > Shot Matcher',
    "support": 'COMMUNITY',
    "category": 'Compositing'
}

import bpy

from .LayerSettings import LayerSettings


# load and reload submodules
##################################

import importlib
from . import developer_utils
importlib.reload(developer_utils)
modules = developer_utils.setup_addon_modules(__path__, __name__, "bpy" in locals())


# register
##################################

import traceback

def register():
    try: bpy.utils.register_module(__name__)
    except: traceback.print_exc()
    scene = bpy.types.Scene
    scene.layer_context = bpy.props.EnumProperty(
        name='Layer',
        description='The current layer being analyzed',
        items=[ ('bg', 'Background', ''),
                ('fg', 'Foreground', ''),
               ]
        )
    scene.sm_background = bpy.props.PointerProperty(type=LayerSettings)
    scene.sm_foreground = bpy.props.PointerProperty(type=LayerSettings)

def unregister():
    try: bpy.utils.unregister_module(__name__)
    except: traceback.print_exc()

    print("Unregistered {}".format(bl_info["name"]))
    scene = bpy.types.Scene
    del scene.sm_background, scene.sm_foreground, scene.layer_context
