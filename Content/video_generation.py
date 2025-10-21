import sys
import os

import bpy
import random
import math
import bmesh

import importlib

import numpy as np

from datetime import date

sys.path.append(
    r"C:\Users\reinh\Desktop\Synthetic_Video_of_Real_PPG\Content")  # change for your project directory if running in Blender
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # for running external

import ppg2ppgi_animation as p2p
import config
import image_prep as ip
import render_settings
import images_store

importlib.reload(p2p)
importlib.reload(config)
importlib.reload(ip)
importlib.reload(images_store)
importlib.reload(render_settings)

from render_settings import RenderSettings
from images_store import Images

PPG_DATA_PATH = r"X:\PPGI\KISMED"


# clear scene and remove unused data and reset name
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.context.scene.name = "0"


# add a face and move it
def add_FLAME_head(pos, x_rotation=0, y_rotation=0, z_rotation=0):
    """
    Add FLAME head model to right position in scene and make random shapes
    :param pos: aimed position of head
    :param x_rotation: head x rotation
    :param y_rotation: head y rotation
    :param z_rotation: head z rotation
    :return: -
    """
    # decide gender
    gender_int = random.randint(0, 1)
    gender = "female" if gender_int == 0 else "male"
    bpy.data.window_managers["WinMan"].flame_tool.flame_gender = gender

    # add head model
    bpy.ops.scene.flame_add_gender()

    bpy.ops.transform.translate(value=pos)
    bpy.ops.transform.rotate(value=x_rotation, orient_axis='X')
    bpy.ops.transform.rotate(value=y_rotation, orient_axis='Y')
    bpy.ops.transform.rotate(value=z_rotation, orient_axis='Z')
    # bpy.ops.object.flame_random_shapes()

    # make random shape
    for i in range(1, 301):
        shape_key = "Shape" + str(i)
        # print(shape_key)

        bpy.context.object.active_shape_key_index = i
        bpy.data.shape_keys["Key"].key_blocks[shape_key].value = random.uniform(-1, 1)


# import the experiment room scene
def import_exp_room(path):
    """
    Add scene environment
    :param path: path to blend file with scene
    :return: -
    """
    scene_name = "Exp_Room"

    # select scene
    with bpy.data.libraries.load(path) as (data_from, data_to):

        if scene_name in data_from.scenes:
            data_to.scenes = [scene_name]
        else:
            raise ValueError(f"Scene {scene_name} not available in {path}")

    # remove current scene
    current_scene = bpy.context.scene
    bpy.data.scenes.remove(current_scene)

    # add aimed scene
    bpy.context.window.scene = bpy.data.scenes[scene_name]


# make shader nodes for animation logic
def make_shader_animation(name, max_val):
    """
    Shader Node Group for animation logic
    :param name: Name for the Group Node
    :return: Group Tree that will be represented by a Group Node
    """
    group_tree = bpy.data.node_groups.new(name=name, type='ShaderNodeTree')
    nodes = group_tree.nodes
    links = group_tree.links

    # add inputs and outputs
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='animation_value',
                                    in_out='INPUT')  # animation value that controls the change of colors between two images
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='phase_map',
                                    in_out='INPUT')  # phase map input / 0.5 is no phase map is used
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='mean_radius',
                                    in_out='INPUT')  # mean radius or color for animating mean_radius +-0.1
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='Mag_Value',
                                    in_out='INPUT')  # magnitude value of current cycle
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='Mag_Map',
                                    in_out='INPUT')  # magnitude map for color

    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='range_(0-1)',
                                    in_out='OUTPUT')  # to control Mix Nodes
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='range_(-1-1)',
                                    in_out='OUTPUT')  # if a mask should be used to control Mix Nodes
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='range_(+-0.1)',
                                    in_out='OUTPUT')  # mean_radius +-0.1
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='range_(+-mag_map)',
                                    in_out='OUTPUT')  # mean_radius +-mag_map

    # add nodes
    group_outputs = group_tree.nodes.new('NodeGroupOutput')
    group_outputs.location = (1200, 0)

    add_node_3 = nodes.new(type="ShaderNodeMath")
    add_node_3.location = (1000, -200)

    radius_mul_node = nodes.new(type="ShaderNodeMath")
    radius_mul_node.location = (800, -200)
    radius_mul_node.operation = "MULTIPLY"

    mul_node_2 = nodes.new(type="ShaderNodeMath")
    mul_node_2.operation = "MULTIPLY"
    mul_node_2.location = (600, -200)

    mul_add_node = nodes.new(type="ShaderNodeMath")
    mul_add_node.operation = "MULTIPLY_ADD"
    mul_add_node.location = (800, 0)

    sine_node = nodes.new(type="ShaderNodeMath")
    sine_node.operation = "SINE"
    sine_node.location = (400, 0)

    add_node_2 = nodes.new(type="ShaderNodeMath")
    add_node_2.location = (200, 0)

    mul_node = nodes.new(type="ShaderNodeMath")
    mul_node.operation = "MULTIPLY"
    mul_node.location = (0, -150)

    add_node_1 = nodes.new(type="ShaderNodeMath")
    add_node_1.operation = "ADD"
    add_node_1.location = (-200, -150)

    group_inputs = group_tree.nodes.new('NodeGroupInput')
    group_inputs.location = (-400, 0)

    # nodes for +-mag_map
    map_range = nodes.new(type="ShaderNodeMapRange")
    map_range.location = (0, -350)

    mul_mag_map = nodes.new(type="ShaderNodeMath")
    mul_mag_map.operation = "MULTIPLY"
    mul_mag_map.location = (200, -350)

    mul_mag_map_sine = nodes.new(type="ShaderNodeMath")
    mul_mag_map_sine.operation = "MULTIPLY"
    mul_mag_map_sine.location = (700, -350)

    mul_add_mag_map = nodes.new(type="ShaderNodeMath")
    mul_add_mag_map.operation = "MULTIPLY_ADD"
    mul_add_mag_map.location = (900, -350)

    # link nodes and set values
    links.new(group_inputs.outputs['phase_map'], add_node_1.inputs[0])
    links.new(group_inputs.outputs['animation_value'], add_node_2.inputs[0])

    add_node_1.inputs[1].default_value = -0.5  # shift 0.5 px value to 0s phase
    links.new(add_node_1.outputs["Value"], mul_node.inputs[0])
    mul_node.inputs[1].default_value = 2 * math.pi  # scale the phase

    links.new(mul_node.outputs["Value"], add_node_2.inputs[1])

    links.new(add_node_2.outputs["Value"], sine_node.inputs[0])

    links.new(sine_node.outputs['Value'], mul_node_2.inputs[0])
    mul_node_2.inputs[1].default_value = -0.1 * config.mag_scale  # inverting because max ppg means less radius

    links.new(mul_node_2.outputs['Value'], radius_mul_node.inputs[1])
    links.new(group_inputs.outputs['Mag_Value'], radius_mul_node.inputs[0])

    links.new(group_inputs.outputs['mean_radius'], add_node_3.inputs[0])
    links.new(radius_mul_node.outputs[0], add_node_3.inputs[1])

    links.new(sine_node.outputs['Value'], mul_add_node.inputs[0])
    mul_add_node.inputs[1].default_value = 0.5
    mul_add_node.inputs[2].default_value = 0.5

    links.new(mul_add_node.outputs[0], group_outputs.inputs['range_(0-1)'])

    links.new(sine_node.outputs['Value'], group_outputs.inputs['range_(-1-1)'])
    links.new(add_node_3.outputs[0], group_outputs.inputs['range_(+-0.1)'])

    # links for +-mag_map
    links.new(group_inputs.outputs[4], map_range.inputs[0])
    map_range.inputs[2].default_value = max_val

    links.new(map_range.outputs[0], mul_mag_map.inputs[0])
    mul_mag_map.inputs[1].default_value = -0.1 * config.mag_scale  # inverting because max ppg means less radius

    links.new(mul_mag_map.outputs[0], mul_mag_map_sine.inputs[0])
    links.new(sine_node.outputs['Value'], mul_mag_map_sine.inputs[1])

    links.new(mul_mag_map_sine.outputs[0], mul_add_mag_map.inputs[0])
    links.new(group_inputs.outputs[3], mul_add_mag_map.inputs[1])
    links.new(group_inputs.outputs[2], mul_add_mag_map.inputs[2])

    links.new(mul_add_mag_map.outputs[0], group_outputs.inputs[3])

    return group_tree


# make shader nodes for amplitude images
def make_shader_magnitude(name):
    """

    :param name: name of Group Node
    :return: Group Tree that will be represented by a Group Node
    """
    group_tree = bpy.data.node_groups.new(name=name, type='ShaderNodeTree')
    nodes = group_tree.nodes
    links = group_tree.links

    # add inputs and outputs
    group_tree.interface.new_socket(socket_type='NodeSocketColor', name='Mean_Color', in_out='INPUT')
    group_tree.interface.new_socket(socket_type='NodeSocketColor', name='Mag_Color', in_out='INPUT')
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='Mag_Value', in_out='INPUT')
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='Color_high', in_out='OUTPUT')
    group_tree.interface.new_socket(socket_type='NodeSocketFloat', name='Color_low', in_out='OUTPUT')

    # add nodes
    group_inputs = group_tree.nodes.new('NodeGroupInput')
    group_inputs.location = (-400, 0)

    mul_node = nodes.new('ShaderNodeMath')
    mul_node.location = (-200, 0)
    mul_node.operation = "MULTIPLY"

    sub_node = nodes.new('ShaderNodeMath')
    sub_node.location = (0, -100)
    sub_node.operation = "SUBTRACT"

    add_node = nodes.new('ShaderNodeMath')
    add_node.location = (0, 100)

    group_outputs = nodes.new('NodeGroupOutput')
    group_outputs.location = (200, 0)

    # make links
    links.new(group_inputs.outputs["Mean_Color"], add_node.inputs[0])
    links.new(group_inputs.outputs["Mean_Color"], sub_node.inputs[0])
    links.new(group_inputs.outputs["Mag_Color"], mul_node.inputs[0])
    links.new(group_inputs.outputs["Mag_Value"], mul_node.inputs[1])

    links.new(mul_node.outputs['Value'], add_node.inputs[1])
    links.new(mul_node.outputs['Value'], sub_node.inputs[1])

    links.new(add_node.outputs['Value'], group_outputs.inputs['Color_high'])  # darker color
    links.new(sub_node.outputs['Value'], group_outputs.inputs['Color_low'])  # lighter color

    return group_tree


# adjust shader for BVP animation
def makeShader(images):
    """
    :param images: Images object that contains the needed images for the Shader
    :return: -
    """
    # select material or create new one
    mat = bpy.data.materials.get("Face")
    if not mat:
        mat = bpy.data.materials.new(name="Face")

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # clear all nodes
    nodes.clear()

    ####################
    # Shader Nodes
    ####################

    # Add nodes
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (400, 0)

    mix_final_node = nodes.new(type="ShaderNodeMixShader")
    mix_final_node.location = (200, 0)

    shader_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    shader_node.location = (-200, 900)

    tex_image_node = nodes.new(type="ShaderNodeTexImage")
    tex_image_node.location = (-500, 900)
    tex_image_node.image = images.texture

    subsurface_node = nodes.new(type="ShaderNodeSubsurfaceScattering")
    subsurface_node.location = (0, 0)

    combine_color_node = nodes.new(type="ShaderNodeCombineColor")
    combine_color_node.location = (-200, -100)

    combine_radius_node = nodes.new(type="ShaderNodeCombineXYZ")
    combine_radius_node.location = (-200, 100)

    animation_value_node = nodes.new(type="ShaderNodeValue")
    animation_value_node.location = (-1000, 1000)
    animation_value_node.label = "animation_value"
    animation_value_node.name = config.av_name

    magnitude_value_node = nodes.new(type="ShaderNodeValue")
    magnitude_value_node.location = (-1200, 1000)
    magnitude_value_node.label = "magnitude_value"
    magnitude_value_node.name = config.mag_name

    # RED
    phase_red_node = nodes.new(type="ShaderNodeTexImage")
    phase_red_node.location = (-1000, 800)
    phase_red_node.image = images.phase_red
    phase_red_node.image.colorspace_settings.name = 'Non-Color'

    red_animation = nodes.new('ShaderNodeGroup')
    red_animation.location = (-700, 800)
    red_animation.node_tree = make_shader_animation("Animation_Red", images.max_mag_red)
    red_animation.name = "animation_red"
    red_animation.inputs['mean_radius'].default_value = config.red_radius

    red_magnitude = nodes.new('ShaderNodeGroup')
    red_magnitude.location = (-700, 500)
    red_magnitude.node_tree = make_shader_magnitude("Magnitude_Red")
    red_magnitude.name = "magnitude_red"

    red_mix_node = nodes.new(type="ShaderNodeMix")
    red_mix_node.location = (-500, 600)

    red_mean_node = nodes.new(type="ShaderNodeTexImage")
    red_mean_node.location = (-1000, 600)
    red_mean_node.image = images.mean_red
    red_mean_node.image.colorspace_settings.name = 'Non-Color'

    red_mag_node = nodes.new(type="ShaderNodeTexImage")
    red_mag_node.location = (-1000, 400)
    red_mag_node.image = images.magnitude_red
    red_mag_node.image.colorspace_settings.name = 'Non-Color'

    # GREEN
    phase_green_node = nodes.new(type="ShaderNodeTexImage")
    phase_green_node.location = (-1000, 100)
    phase_green_node.image = images.phase_green
    phase_green_node.image.colorspace_settings.name = 'Non-Color'

    green_animation = nodes.new('ShaderNodeGroup')
    green_animation.location = (-700, 100)
    green_animation.node_tree = make_shader_animation("Animation_Green", images.max_mag_green)
    green_animation.name = "animation_green"
    green_animation.inputs['mean_radius'].default_value = config.green_radius

    green_magnitude = nodes.new('ShaderNodeGroup')
    green_magnitude.location = (-700, -200)
    green_magnitude.node_tree = make_shader_magnitude("Magnitude_Green")
    green_magnitude.name = "magnitude_green"

    green_mix_node = nodes.new(type="ShaderNodeMix")
    green_mix_node.location = (-500, -100)

    green_mean_node = nodes.new(type="ShaderNodeTexImage")
    green_mean_node.location = (-1000, -100)
    green_mean_node.image = images.mean_green
    green_mean_node.image.colorspace_settings.name = 'Non-Color'

    green_mag_node = nodes.new(type="ShaderNodeTexImage")
    green_mag_node.location = (-1000, -300)
    green_mag_node.image = images.magnitude_green
    green_mag_node.image.colorspace_settings.name = 'Non-Color'

    # BLUE
    phase_blue_node = nodes.new(type="ShaderNodeTexImage")
    phase_blue_node.location = (-1000, -600)
    phase_blue_node.image = images.phase_blue
    phase_blue_node.image.colorspace_settings.name = 'Non-Color'

    blue_animation = nodes.new('ShaderNodeGroup')
    blue_animation.location = (-700, -600)
    blue_animation.node_tree = make_shader_animation("Animation_Blue", images.max_mag_blue)
    blue_animation.name = "animation_blue"
    blue_animation.inputs['mean_radius'].default_value = config.blue_radius

    blue_magnitude = nodes.new('ShaderNodeGroup')
    blue_magnitude.location = (-700, -900)
    blue_magnitude.node_tree = make_shader_magnitude("Magnitude_Blue")
    blue_magnitude.name = "magnitude_blue"

    blue_mix_node = nodes.new(type="ShaderNodeMix")
    blue_mix_node.location = (-500, -800)

    blue_mean_node = nodes.new(type="ShaderNodeTexImage")
    blue_mean_node.location = (-1000, -800)
    blue_mean_node.image = images.mean_blue
    blue_mean_node.image.colorspace_settings.name = 'Non-Color'

    blue_mag_node = nodes.new(type="ShaderNodeTexImage")
    blue_mag_node.location = (-1000, -1000)
    blue_mag_node.image = images.magnitude_blue
    blue_mag_node.image.colorspace_settings.name = 'Non-Color'

    # create links
    # RED animation
    links.new(animation_value_node.outputs["Value"], red_animation.inputs[0])
    links.new(phase_red_node.outputs["Color"], red_animation.inputs[1])
    links.new(magnitude_value_node.outputs[0], red_animation.inputs[3])
    links.new(red_mag_node.outputs["Color"], red_animation.inputs[4])

    links.new(magnitude_value_node.outputs[0], red_magnitude.inputs[2])
    links.new(red_mean_node.outputs["Color"], red_magnitude.inputs[0])
    links.new(red_mag_node.outputs["Color"], red_magnitude.inputs[1])

    links.new(red_animation.outputs[0], red_mix_node.inputs[0])
    links.new(red_magnitude.outputs["Color_high"], red_mix_node.inputs[2])  # lighter skin color
    links.new(red_magnitude.outputs["Color_low"], red_mix_node.inputs[3])

    # GREEN animation
    links.new(animation_value_node.outputs["Value"], green_animation.inputs[0])
    links.new(phase_green_node.outputs["Color"], green_animation.inputs[1])
    links.new(magnitude_value_node.outputs[0], green_animation.inputs[3])
    links.new(green_mag_node.outputs["Color"], green_animation.inputs[4])

    links.new(magnitude_value_node.outputs[0], green_magnitude.inputs[2])
    links.new(green_mean_node.outputs["Color"], green_magnitude.inputs[0])
    links.new(green_mag_node.outputs["Color"], green_magnitude.inputs[1])

    links.new(green_animation.outputs[0], green_mix_node.inputs[0])
    links.new(green_magnitude.outputs["Color_high"], green_mix_node.inputs[2])  # lighter skin color
    links.new(green_magnitude.outputs["Color_low"], green_mix_node.inputs[3])

    # BLUE animation
    links.new(animation_value_node.outputs["Value"], blue_animation.inputs[0])
    links.new(phase_blue_node.outputs["Color"], blue_animation.inputs[1])
    links.new(magnitude_value_node.outputs[0], blue_animation.inputs[3])
    links.new(blue_mag_node.outputs["Color"], blue_animation.inputs[4])

    links.new(magnitude_value_node.outputs[0], blue_magnitude.inputs[2])
    links.new(blue_mean_node.outputs["Color"], blue_magnitude.inputs[0])
    links.new(blue_mag_node.outputs["Color"], blue_magnitude.inputs[1])

    links.new(blue_animation.outputs[0], blue_mix_node.inputs[0])
    links.new(blue_magnitude.outputs["Color_high"], blue_mix_node.inputs[2])  # lighter skin color
    links.new(blue_magnitude.outputs["Color_low"], blue_mix_node.inputs[3])

    # mix color and radii channels
    links.new(red_mix_node.outputs["Result"], combine_color_node.inputs[0])
    links.new(green_mix_node.outputs["Result"], combine_color_node.inputs[1])
    links.new(blue_mix_node.outputs["Result"], combine_color_node.inputs[2])

    # RADII animation

    links.new(red_animation.outputs[3], combine_radius_node.inputs[0])
    links.new(green_animation.outputs[3], combine_radius_node.inputs[1])
    links.new(blue_animation.outputs[3], combine_radius_node.inputs[2])

    # output connections
    subsurface_node.inputs[0].default_value = images.getMeanSkinColor()
    # links.new(combine_color_node.outputs["Color"], subsurface_node.inputs[0])
    links.new(combine_radius_node.outputs["Vector"], subsurface_node.inputs[2])
    subsurface_node.inputs[2].default_value[0] = config.red_radius
    subsurface_node.inputs[2].default_value[1] = config.green_radius
    subsurface_node.inputs[2].default_value[2] = config.blue_radius

    links.new(tex_image_node.outputs['Color'], shader_node.inputs[0])

    links.new(shader_node.outputs['BSDF'], mix_final_node.inputs[1])
    links.new(subsurface_node.outputs['BSSRDF'], mix_final_node.inputs[2])
    mix_final_node.inputs[0].default_value = config.SUBSURFACE_FAC

    links.new(mix_final_node.outputs['Shader'], output_node.inputs[0])

    ####################
    # Shader Animation Output Logic
    ####################
    # add nodes
    # forward_animation = nodes.new('ShaderNodeGroup')
    # forward_animation.location = (-400, 300)
    # forward_animation.node_tree = make_shader_animation_forward(2, -0.5, "Animation_Forward")
    # forward_animation.name = "animation_forward"

    # backward_animation = nodes.new('ShaderNodeGroup')
    # backward_animation.location = (-400, -300)
    # backward_animation.node_tree = make_shader_animation_forward(-2, 1.5, "Animation_Backward")
    # backward_animation.name = "animation_backward"


# adjust shader for SCAMPS animation
def makeShaderSCAMPS(images):
    """
    :param images: Images object that contains the needed images for the Shader
    :return: -
    """
    # select material or create new one
    mat = bpy.data.materials.get("Face")
    if not mat:
        mat = bpy.data.materials.new(name="Face")

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # clear all nodes
    nodes.clear()

    # Add nodes
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (600, 0)

    mix_final_node = nodes.new(type="ShaderNodeMixShader")
    mix_final_node.location = (400, 0)

    shader_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    shader_node.location = (-100, 600)

    tex_image_node = nodes.new(type="ShaderNodeTexImage")
    tex_image_node.location = (-400, 600)
    tex_image_node.image = images.texture

    subsurface_node = nodes.new(type="ShaderNodeSubsurfaceScattering")
    subsurface_node.location = (200, 0)
    # subsurface_node.inputs[2].default_value[0] = config.red_radius
    # subsurface_node.inputs[2].default_value[0] = config.green_radius
    # subsurface_node.inputs[2].default_value[0] = config.blue_radius

    add_radius_node = nodes.new(type="ShaderNodeVectorMath")
    add_radius_node.location = (0, -200)

    add_color_node = nodes.new(type="ShaderNodeVectorMath")
    add_color_node.location = (0, 100)

    scale_color_node = nodes.new(type="ShaderNodeVectorMath")
    scale_color_node.operation = "SCALE"
    scale_color_node.location = (-200, 100)

    combine_radius = nodes.new(type="ShaderNodeCombineXYZ")
    combine_radius.location = (-200, -200)

    animation_color_node = nodes.new('ShaderNodeGroup')
    animation_color_node.location = (-400, 100)
    animation_color_node.node_tree = make_shader_animation("Animation", 0)

    define_radius = nodes.new(type="ShaderNodeCombineXYZ")
    define_radius.location = (-400, -400)

    color_node = nodes.new(type="ShaderNodeRGB")
    color_node.location = (-400, 300)
    color_node.outputs[0].default_value = images.getMeanSkinColor()

    radius_mask = nodes.new(type="ShaderNodeTexImage")
    radius_mask.location = (-800, -200)
    radius_mask.image = images.scamps_mask
    radius_mask.image.colorspace_settings.name = 'Non-Color'

    animation_value_node = nodes.new(type="ShaderNodeValue")
    animation_value_node.location = (-800, 100)
    animation_value_node.label = "animation_value"
    animation_value_node.name = config.av_name

    magnitude_value_node = nodes.new(type="ShaderNodeValue")
    magnitude_value_node.location = (-1000, 100)
    magnitude_value_node.label = "magnitude_value"
    magnitude_value_node.name = config.mag_name

    # Add Connections
    links.new(animation_value_node.outputs[0], animation_color_node.inputs[0])
    links.new(magnitude_value_node.outputs[0], animation_color_node.inputs[3])
    animation_color_node.inputs[1].default_value = 0.5
    animation_color_node.inputs[2].default_value = 0
    links.new(radius_mask.outputs[0], animation_color_node.inputs[4])

    define_radius.inputs[0].default_value = config.red_radius
    define_radius.inputs[1].default_value = config.green_radius
    define_radius.inputs[2].default_value = config.blue_radius

    links.new(define_radius.outputs[0], scale_color_node.inputs[0])
    links.new(animation_color_node.outputs[1], scale_color_node.inputs[3])

    links.new(animation_color_node.outputs[2], combine_radius.inputs[0])
    links.new(animation_color_node.outputs[2], combine_radius.inputs[1])
    links.new(animation_color_node.outputs[2], combine_radius.inputs[2])

    links.new(scale_color_node.outputs[0], add_color_node.inputs[0])
    links.new(color_node.outputs[0], add_color_node.inputs[1])

    links.new(combine_radius.outputs[0], add_radius_node.inputs[0])
    links.new(define_radius.outputs[0], add_radius_node.inputs[1])

    links.new(add_color_node.outputs[0], subsurface_node.inputs[0])
    links.new(add_radius_node.outputs[0], subsurface_node.inputs[2])

    links.new(tex_image_node.outputs["Color"], shader_node.inputs[0])

    mix_final_node.inputs[0].default_value = config.SUBSURFACE_FAC
    links.new(shader_node.outputs["BSDF"], mix_final_node.inputs[1])
    links.new(subsurface_node.outputs[0], mix_final_node.inputs[2])

    links.new(mix_final_node.outputs[0], output_node.inputs["Surface"])


# fit uv-map of FLAME head model to common head textures
def adjustUVMap(uv_mesh):
    """
    :param uv_mesh: uv-mesh coordinates
    :return: -
    """
    obj = bpy.context.active_object
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    uv_layer = bm.loops.layers.uv.verify()
    bm.faces.ensure_lookup_table()

    i = 0

    for f, face in enumerate(bm.faces):

        triangle = []
        for loop in face.loops:
            loop[uv_layer].uv = uv_mesh[i]
            triangle.append(uv_mesh[i])

            i += 1

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


# make keyframes for subsurface color and radii changes
def animatePPGI(avs: np.ndarray, mags: np.ndarray, rs):
    """
    :param avs: ndarray of animation values for every frame
    :param mags: ndarray of magnitude values for every frame
    :param rs: RenderSettings object
    :return: -
    """
    avs = np.asarray(avs)
    mags = np.asarray(mags)
    mags = np.abs(mags)

    scene = bpy.context.scene
    obj = bpy.context.active_object
    mat = obj.active_material

    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    av_node = nodes.get(config.av_name)
    mag_node = nodes.get(config.mag_name)

    if avs.size != mags.size:
        raise AttributeError(
            f"Animation value and magnitude array should have same length, but have length {avs.size} and {mags.size}.")

    for i in range(avs.size):
        scene.frame_current = i + 1

        av_node.outputs[0].default_value = avs[i]
        av_node.outputs[0].keyframe_insert(data_path="default_value", frame=i + 1)

        mag_node.outputs[0].default_value = mags[i] / np.max(mags)
        mag_node.outputs[0].keyframe_insert(data_path="default_value", frame=i + 1)

    rs.adjustEndFrame(scene.frame_current)


# set light situations
def setupScenario(scenario, rs):
    """
    :param scenario: light scenario
    :param rs: RenderSettings object
    :return: -
    """

    if scenario not in config.scenario.keys():
        raise AttributeError(f"Input scenario '{scenario}' is unknown ({config.scenario.keys()}).")

    settings = config.scenario[scenario]

    # TOP LIGHT ON
    if settings["top_light"] == 1:
        bpy.data.materials[config.TL_name].node_tree.nodes[config.TL_node].inputs[1].default_value = config.TL_value

    # TOP LIGHT OFF
    elif settings["top_light"] == 0:
        bpy.data.materials[config.TL_name].node_tree.nodes[config.TL_node].inputs[1].default_value = 0

    # CHANGING TOP LIGHT
    elif settings["top_light"] == 0.5:
        pass

    # CHANGING SIDE LIGHT
    if settings["side_light"] == 1:

        sl_node = bpy.data.materials[config.SL_name].node_tree.nodes[config.SL_node]
        sl_node.inputs[1].default_value = config.SL_value

        for i in range(rs.start_frame, rs.end_frame, 20 * 30):
            # make the current frame to keyframe change
            sl_node.inputs[1].keyframe_insert(data_path="default_value", frame=i)

            if sl_node.inputs[1].default_value == config.SL_value:
                sl_node.inputs[1].default_value = 0
            elif sl_node.inputs[1].default_value == 0:
                sl_node.inputs[1].default_value = config.SL_value

            # make sure the light strength won't change before the current frame
            sl_node.inputs[1].keyframe_insert(data_path="default_value", frame=i - 1)

        obj = bpy.data.objects.get("Obj3d66-1558518-14-617")
        obj.rotation_euler[2] = math.pi
        obj.rotation_euler[0] = 0
        obj.location = (-0.23, 2.1, 0)

        bpy.ops.object.select_all(action='DESELECT')

    # SIDE LIGHT OFF
    elif settings["side_light"] == 0:
        bpy.data.materials[config.SL_name].node_tree.nodes[config.SL_node].inputs[1].default_value = 0

    # make environmantal light
    world = bpy.context.scene.world
    world.use_nodes = True

    nodes = world.node_tree.nodes
    bn = next((n for n in nodes if n.type == 'BACKGROUND'), None)

    # bn.inputs["Color"].default_value = config.sunlight
    bn.inputs["Strength"].default_value = config.sunstrength


# method that renders
def render(rs):
    """
    :param rs: RenderSettings object
    :return: all images as files, video file, render information file
    """
    # Output Frame Range
    bpy.context.scene.frame_start = rs.start_frame
    bpy.context.scene.frame_end = rs.end_frame

    # Output Path
    i = 0
    out_dir = ""
    while True:
        out_dir = os.path.join(config.path, "Output", str(date.today()), str(i))
        if os.path.exists(out_dir):
            i += 1
        elif not os.path.exists(out_dir):
            os.makedirs(out_dir)
            break

    # Render Settings
    bpy.context.scene.render.engine = rs.engine  # Render Engine
    bpy.context.scene.cycles.device = rs.device  # Render Device
    bpy.context.scene.cycles.use_denoising = True  # Use Denoising
    bpy.context.scene.cycles.denoiser = rs.denoiser  # Denoiser
    bpy.context.scene.cycles.samples = rs.samples  # Number of Samples
    bpy.context.scene.render.use_persistent_data = False
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = rs.cdt

    # enable rendering devices
    # device_list =  bpy.context.preferences.addons['cycles'].preferences.get_devices()
    # for device in device_list.devices:
    #     if device.type != "CPU":
    #         device.use = True
    #         rs.adjustDeviceName(device.name)
    #         print(f"Use {device.name}")

    # Output Settings
    bpy.context.scene.render.resolution_y = rs.resolution[1]
    bpy.context.scene.render.resolution_x = rs.resolution[0]

    # Output Format
    # bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'

    render.use_file_extension = True
    print("Render:")

    out_path = os.path.join(out_dir, rs.video_file_name)
    bpy.context.scene.render.filepath = out_path

    bpy.context.scene.frame_current = 1
    bpy.ops.render.render(animation=True)

    """for i in range(rs.start_frame, rs.end_frame + 1):
        out_path = os.path.join(out_dir, f"{i}.png")
        bpy.context.scene.render.filepath = out_path

        bpy.context.scene.frame_current = i
        bpy.ops.render.render(write_still=True)

        sys.stdout.write(f"\rFrame {i}/{rs.end_frame}")
        sys.stdout.flush()

        # Test Interrupt
        # if i == 5:
        # break

    # out_path = os.path.join(out_dir, f"S01_PPG001_1a.mp4")
    # bpy.context.scene.render.filepath = out_path
    ip.images2video(out_dir, rs)"""
    print(f"Rendered Video was saved in {out_dir}")

    rs.writeLog(out_dir)

    # bpy.ops.render.render(animation=True)


# main method
def main(exp_room_path, uv_map_path, image_dict, rs):
    """
    :param exp_room_path: path to experiment room template
    :param uv_map_path: map to uv map coordinates
    :param image_dict: Images object
    :param rs: RenderSettings object
    :return: -
    """
    try:
        bpy.ops.wm.save_mainfile()
    except RuntimeError:
        pass

    clear_scene()
    import_exp_room(exp_room_path)
    add_FLAME_head((-0.20746, 1, 1.12), z_rotation=-math.pi / 2)

    if scamps:
        makeShaderSCAMPS(image_dict)
    else:
        makeShader(image_dict)

    uv_map = np.load(uv_map_path)
    adjustUVMap(uv_map)

    ppg_subject_path = os.path.join(PPG_DATA_PATH, f"{rs.ppg_subject}.zip")
    time, bvp = p2p.readPPG(ppg_subject_path, rs.ppg_trial)
    avs, mags, _ = p2p.getKeyframes(time, bvp)

    animatePPGI(avs, mags, rs)

    setupScenario("1a", rs)

    render(rs)


if __name__ == "__main__":

    file = config.path
    print(f"File: {file}")
    exp_room_path = os.path.join(file, r"ExpRoom_template.blend")
    uv_map_path = os.path.join(file, r"assets\uv_coords_template.npy")

    images = Images()

    scamps = False  # Use our own color changes and animation
    # scamps = True  # Use the rebuild of the SCAMPS paper

    rs = RenderSettings('Logitech', "S01", "p001", "v01", scamps, 1, 150)

    tex_image = bpy.data.images.load(os.path.join(file, r"assets\tex_sample_01.png"), check_existing=True)
    tex_image.use_fake_user = True
    images.addTexture(tex_image)

    if scamps:

        scamps_mask = bpy.data.images.load(os.path.join(file, r"assets\original_scamps_mask.png"),
                                           check_existing=True)
        scamps_mask.use_fake_user = True
        images.addSCAMPS(scamps_mask)

    else:

        phase_red = bpy.data.images.load(os.path.join(file, r"assets\S01_moco_phase_r_hd.png"),
                                         check_existing=True)
        phase_red.use_fake_user = True
        mag_blue = bpy.data.images.load(os.path.join(file, r"assets\S01_moco_mag_b_hd.png"),
                                        check_existing=True)
        mag_blue.use_fake_user = True
        mag_green = bpy.data.images.load(os.path.join(file, r"assets\S01_moco_mag_g_hd.png"),
                                         check_existing=True)
        mag_green.use_fake_user = True
        mag_red = bpy.data.images.load(os.path.join(file, r"assets\S01_moco_mag_r_hd.png"),
                                       check_existing=True)
        mag_red.use_fake_user = True
        phase_blue = bpy.data.images.load(os.path.join(file, r"assets\S01_moco_phase_b_hd.png"),
                                          check_existing=True)
        phase_blue.use_fake_user = True
        phase_green = bpy.data.images.load(os.path.join(file, r"assets\S01_moco_phase_g_hd.png"),
                                           check_existing=True)
        phase_green.use_fake_user = True

        images = ip.prepareAmplitudeMaps(tex_image, mag_red, mag_green, mag_blue, images)

        images.addPhases(phase_red, phase_green, phase_blue)

    main(exp_room_path, uv_map_path, images, rs)