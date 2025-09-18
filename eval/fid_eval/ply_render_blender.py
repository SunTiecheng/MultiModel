# A simple script that uses blender to render views of a single object by rotation the camera around it.
# Also produces depth map at the same time.
#
# Modified to support PLY format with vertex colors, output type control and custom resolution
#
# Tested with Blender 2.9
#
# Example for 1920x1080 resolution:
# blender --background --python render_ply.py -- --width 1920 --height 1080 --views 10 /path/to/mesh.ply
#

import argparse, sys, os, math
import bpy
from mathutils import Vector

parser = argparse.ArgumentParser(description='Renders given PLY file by rotation a camera around it.')
parser.add_argument('--views', type=int, default=30,
                    help='number of views to be rendered')
parser.add_argument('obj', type=str,
                    help='Path to the PLY file to be rendered.')
parser.add_argument('--output_folder', type=str, default='/tmp',
                    help='The path the output will be dumped to.')
parser.add_argument('--output_types', nargs='+', default=['render', 'depth', 'normal', 'albedo', 'id'],
                    choices=['render', 'depth', 'normal', 'albedo', 'id'],
                    help='Types of outputs to produce. Options: render, depth, normal, albedo, id. Default: all')
# 添加宽度和高度参数
parser.add_argument('--width', type=int, default=1920,
                    help='Width of the images.')
parser.add_argument('--height', type=int, default=1080,
                    help='Height of the images.')
parser.add_argument('--scale', type=float, default=1,
                    help='Scaling factor applied to model. Depends on size of mesh.')
parser.add_argument('--remove_doubles', type=bool, default=True,
                    help='Remove double vertices to improve mesh quality.')
parser.add_argument('--edge_split', type=bool, default=True,
                    help='Adds edge split filter.')
parser.add_argument('--depth_scale', type=float, default=1.4,
                    help='Scaling that is applied to depth. Depends on size of mesh. Try out various values until you get a good result. Ignored if format is OPEN_EXR.')
parser.add_argument('--color_depth', type=str, default='8',
                    help='Number of bit per channel used for output. Either 8 or 16.')
parser.add_argument('--format', type=str, default='PNG',
                    help='Format of files generated. Either PNG or OPEN_EXR')
parser.add_argument('--engine', type=str, default='BLENDER_EEVEE',
                    help='Blender internal engine for rendering. E.g. CYCLES, BLENDER_EEVEE, ...')

argv = sys.argv[sys.argv.index("--") + 1:]
args = parser.parse_args(argv)

# Convert output types to set for faster lookup
output_types = set(args.output_types)

# Set up rendering
context = bpy.context
scene = bpy.context.scene
render = bpy.context.scene.render

render.engine = args.engine
render.image_settings.color_mode = 'RGBA'  # ('RGB', 'RGBA', ...)
render.image_settings.color_depth = args.color_depth  # ('8', '16')
render.image_settings.file_format = args.format  # ('PNG', 'OPEN_EXR', 'JPEG, ...)
# 设置宽度和高度
render.resolution_x = args.width
render.resolution_y = args.height
render.resolution_percentage = 100
render.film_transparent = True

scene.use_nodes = True
scene.view_layers["View Layer"].use_pass_normal = 'normal' in output_types
scene.view_layers["View Layer"].use_pass_diffuse_color = 'albedo' in output_types
scene.view_layers["View Layer"].use_pass_object_index = 'id' in output_types

nodes = bpy.context.scene.node_tree.nodes
links = bpy.context.scene.node_tree.links

# Clear default nodes
for n in nodes:
    nodes.remove(n)

# Create input render layer node
render_layers = nodes.new('CompositorNodeRLayers')

# Create output nodes only for requested types
depth_file_output = None
normal_file_output = None
albedo_file_output = None
id_file_output = None

# Create depth output nodes if requested
if 'depth' in output_types:
    depth_file_output = nodes.new(type="CompositorNodeOutputFile")
    depth_file_output.label = 'Depth Output'
    depth_file_output.base_path = ''
    depth_file_output.file_slots[0].use_node_format = True
    depth_file_output.format.file_format = args.format
    depth_file_output.format.color_depth = args.color_depth

    if args.format == 'OPEN_EXR':
        links.new(render_layers.outputs['Depth'], depth_file_output.inputs[0])
    else:
        depth_file_output.format.color_mode = "BW"
        map = nodes.new(type="CompositorNodeMapValue")
        map.offset = [-0.7]
        map.size = [args.depth_scale]
        map.use_min = True
        map.min = [0]
        links.new(render_layers.outputs['Depth'], map.inputs[0])
        links.new(map.outputs[0], depth_file_output.inputs[0])

# Create normal output nodes if requested
if 'normal' in output_types:
    scale_node = nodes.new(type="CompositorNodeMixRGB")
    scale_node.blend_type = 'MULTIPLY'
    scale_node.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
    links.new(render_layers.outputs['Normal'], scale_node.inputs[1])

    bias_node = nodes.new(type="CompositorNodeMixRGB")
    bias_node.blend_type = 'ADD'
    bias_node.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
    links.new(scale_node.outputs[0], bias_node.inputs[1])

    normal_file_output = nodes.new(type="CompositorNodeOutputFile")
    normal_file_output.label = 'Normal Output'
    normal_file_output.base_path = ''
    normal_file_output.file_slots[0].use_node_format = True
    normal_file_output.format.file_format = args.format
    links.new(bias_node.outputs[0], normal_file_output.inputs[0])

# Create albedo output nodes if requested
if 'albedo' in output_types:
    alpha_albedo = nodes.new(type="CompositorNodeSetAlpha")
    links.new(render_layers.outputs['DiffCol'], alpha_albedo.inputs['Image'])
    links.new(render_layers.outputs['Alpha'], alpha_albedo.inputs['Alpha'])

    albedo_file_output = nodes.new(type="CompositorNodeOutputFile")
    albedo_file_output.label = 'Albedo Output'
    albedo_file_output.base_path = ''
    albedo_file_output.file_slots[0].use_node_format = True
    albedo_file_output.format.file_format = args.format
    albedo_file_output.format.color_mode = 'RGBA'
    albedo_file_output.format.color_depth = args.color_depth
    links.new(alpha_albedo.outputs['Image'], albedo_file_output.inputs[0])

# Create id map output nodes if requested
if 'id' in output_types:
    id_file_output = nodes.new(type="CompositorNodeOutputFile")
    id_file_output.label = 'ID Output'
    id_file_output.base_path = ''
    id_file_output.file_slots[0].use_node_format = True
    id_file_output.format.file_format = args.format
    id_file_output.format.color_depth = args.color_depth

    if args.format == 'OPEN_EXR':
        links.new(render_layers.outputs['IndexOB'], id_file_output.inputs[0])
    else:
        id_file_output.format.color_mode = 'BW'
        divide_node = nodes.new(type='CompositorNodeMath')
        divide_node.operation = 'DIVIDE'
        divide_node.use_clamp = False
        divide_node.inputs[1].default_value = 2 ** int(args.color_depth)
        links.new(render_layers.outputs['IndexOB'], divide_node.inputs[0])
        links.new(divide_node.outputs[0], id_file_output.inputs[0])

# Delete default cube
context.active_object.select_set(True)
bpy.ops.object.delete()

# Import PLY mesh
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.import_mesh.ply(filepath=args.obj)

obj = bpy.context.selected_objects[0]
context.view_layer.objects.active = obj

# ================== 处理顶点颜色 ==================
# 确保顶点颜色层存在
if not obj.data.vertex_colors:
    # 创建新的顶点颜色层
    color_layer = obj.data.vertex_colors.new(name="Col")
else:
    # 使用现有的第一个顶点颜色层
    color_layer = obj.data.vertex_colors[0]

# 创建材质并应用顶点颜色
if not obj.data.materials:
    # 创建新材质
    mat = bpy.data.materials.new(name="VertexColorMaterial")
    mat.use_nodes = True
    obj.data.materials.append(mat)
else:
    # 使用第一个现有材质
    mat = obj.data.materials[0]
    mat.use_nodes = True

# 清除现有节点
nodes = mat.node_tree.nodes
for node in nodes:
    nodes.remove(node)

# 创建新节点
output_node = nodes.new(type='ShaderNodeOutputMaterial')
principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
attribute_node = nodes.new(type='ShaderNodeAttribute')

# 设置属性节点使用顶点颜色
attribute_node.attribute_name = color_layer.name

# 设置节点位置
output_node.location = (300, 0)
principled_node.location = (0, 0)
attribute_node.location = (-300, 0)

# 连接节点
links = mat.node_tree.links
links.new(attribute_node.outputs['Color'], principled_node.inputs['Base Color'])
links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

# 降低高光
principled_node.inputs['Specular'].default_value = 0.05
# ================== 顶点颜色处理结束 ==================

# 获取模型在世界坐标系中的边界框
bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

# 计算边界框的最小和最大坐标
min_coord = Vector(bbox_corners[0])
max_coord = Vector(bbox_corners[0])
for corner in bbox_corners:
    min_coord.x = min(min_coord.x, corner.x)
    min_coord.y = min(min_coord.y, corner.y)
    min_coord.z = min(min_coord.z, corner.z)
    max_coord.x = max(max_coord.x, corner.x)
    max_coord.y = max(max_coord.y, corner.y)
    max_coord.z = max(max_coord.z, corner.z)

# 计算边界框中心和对角线长度
bbox_center = (min_coord + max_coord) * 0.5
diagonal = (max_coord - min_coord).length

# 将模型移动到世界原点
obj.location -= bbox_center

if args.scale != 1:
    bpy.ops.transform.resize(value=(args.scale, args.scale, args.scale))
    bpy.ops.object.transform_apply(scale=True)
if args.remove_doubles:
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.object.mode_set(mode='OBJECT')
if args.edge_split:
    bpy.ops.object.modifier_add(type='EDGE_SPLIT')
    context.object.modifiers["EdgeSplit"].split_angle = 1.32645
    bpy.ops.object.modifier_apply(modifier="EdgeSplit")

# Set object ID if ID output is requested
if 'id' in output_types:
    obj.pass_index = 1

# Make light just directional, disable shadows.
light = bpy.data.lights['Light']
light.type = 'SUN'
light.use_shadow = False
light.specular_factor = 1.0
light.energy = 10.0

# Add another light source so stuff facing away from light is not completely dark
bpy.ops.object.light_add(type='SUN')
light2 = bpy.data.lights['Sun']
light2.use_shadow = False
light2.specular_factor = 1.0
light2.energy = 0.015
bpy.data.objects['Sun'].rotation_euler = bpy.data.objects['Light'].rotation_euler
bpy.data.objects['Sun'].rotation_euler[0] += 180

# Place camera
cam = scene.objects['Camera']

# 设置相机位置
camera_distance = diagonal * 1.5  # 距离为对角线长度的1.5倍
cam.location = (0, -camera_distance, diagonal * 0.3)  # 调整位置使模型在视野中心
cam.data.lens = 35
cam.data.sensor_width = 32

# 调整相机传感器尺寸以适应宽高比
aspect_ratio = args.width / args.height
if aspect_ratio > 1:  # 宽屏
    cam.data.sensor_width = 36
    cam.data.sensor_height = 36 / aspect_ratio
else:  # 竖屏或方形
    cam.data.sensor_width = 36 * aspect_ratio
    cam.data.sensor_height = 36

cam_constraint = cam.constraints.new(type='TRACK_TO')
cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
cam_constraint.up_axis = 'UP_Y'

cam_empty = bpy.data.objects.new("Empty", None)
cam_empty.location = (0, 0, 0)
cam.parent = cam_empty

scene.collection.objects.link(cam_empty)
context.view_layer.objects.active = cam_empty
cam_constraint.target = cam_empty

stepsize = 360.0 / args.views
rotation_mode = 'XYZ'

model_identifier = os.path.splitext(os.path.basename(args.obj))[0]
fp = os.path.join(os.path.abspath(args.output_folder), model_identifier, model_identifier)

# 确保输出目录存在
os.makedirs(os.path.dirname(fp), exist_ok=True)

for i in range(0, args.views):
    print("Rotation {}, {}".format((stepsize * i), math.radians(stepsize * i)))

    render_file_path = fp + '_r_{0:03d}'.format(int(i * stepsize))

    # 设置主渲染路径
    if 'render' in output_types:
        scene.render.filepath = render_file_path
    else:
        scene.render.filepath = ''  # 不保存主渲染图像

    # 设置其他输出路径
    if depth_file_output:
        depth_file_output.file_slots[0].path = render_file_path + "_depth"
    if normal_file_output:
        normal_file_output.file_slots[0].path = render_file_path + "_normal"
    if albedo_file_output:
        albedo_file_output.file_slots[0].path = render_file_path + "_albedo"
    if id_file_output:
        id_file_output.file_slots[0].path = render_file_path + "_id"

    bpy.ops.render.render(write_still=True)  # render still

    cam_empty.rotation_euler[2] += math.radians(stepsize)

# For debugging the workflow
# bpy.ops.wm.save_as_mainfile(filepath='debug.blend')