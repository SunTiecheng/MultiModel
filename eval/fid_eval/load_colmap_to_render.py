import argparse, sys, os, math, json
import bpy
import numpy as np
from mathutils import Vector, Matrix

parser = argparse.ArgumentParser(description='Renders given PLY file using camera parameters from Colmap JSON.')
parser.add_argument('--camera_json', type=str, required=True,
                    help='Path to Colmap cameras.json file')
parser.add_argument('obj', type=str,
                    help='Path to the PLY file to be rendered.')
parser.add_argument('--output_folder', type=str, default='/tmp',
                    help='The path the output will be dumped to.')
parser.add_argument('--output_types', nargs='+', default=['albedo'],
                    choices=['render', 'depth', 'normal', 'albedo', 'id'],
                    help='Types of outputs to produce. Options: render, depth, normal, albedo, id. Default: all')
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
render.resolution_percentage = 100
render.film_transparent = True

# 重要：禁用文件名中的帧号后缀
render.use_file_extension = True  # 使用正确的文件扩展名
render.use_render_cache = False  # 禁用渲染缓存
scene.frame_set(1)  # 设置为第1帧
render.filepath = ""  # 清空默认路径

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

# 获取模型的边界框信息（仅用于信息输出，不移动模型）
bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

# 计算边界框的最小和最大坐标
min_coord = Vector(bbox_corners[0])
max_coord = Vector(bbox_corners[0])
for corner in bbox_corners:
    min_coord.x = min(min_coord.x, corner.x)
    min_coord.y = min(min_coord.y, corner.y)
    min_coord.z = min(min_coord.z, corner.z)
    max_coord.x = max(max_coord.x, corner.x)
    max_coord.y = max(max_coord.y, corner.z)
    max_coord.z = max(max_coord.z, corner.z)

# 计算边界框中心和对角线长度（仅用于信息输出）
bbox_center = (min_coord + max_coord) * 0.5
diagonal = (max_coord - min_coord).length

print(f"Model bounding box: min={min_coord}, max={max_coord}")
print(f"Model center: {bbox_center}, diagonal: {diagonal:.3f}")
print("Model position: KEEPING ORIGINAL POSITION (not moved to origin)")

# ⚠️ 重要：不移动模型，保持原始位置
# obj.location -= bbox_center  # ❌ 注释掉这行，不移动模型

# 应用缩放和其他修改器（如果需要）
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

# 移除之前的相机约束
if cam.constraints:
    for constraint in list(cam.constraints):
        cam.constraints.remove(constraint)

# 删除空物体（如果存在）
if "Empty" in bpy.data.objects:
    empty_obj = bpy.data.objects["Empty"]
    bpy.data.objects.remove(empty_obj, do_unlink=True)

# 解除相机与空物体的父子关系
if cam.parent:
    cam.parent = None

# ================== 读取Colmap相机参数 ==================
# 加载相机JSON文件
with open(args.camera_json, 'r') as f:
    cameras = json.load(f)

print(f"Loaded {len(cameras)} camera poses from {args.camera_json}")

# 修改点：直接使用输出目录，不创建模型名称的子文件夹
output_folder = os.path.abspath(args.output_folder)
os.makedirs(output_folder, exist_ok=True)

print(f"Output directory: {output_folder}")
print(f"Output types: {list(output_types)}")

for camera_idx, camera_data in enumerate(cameras):
    print(f"\nProcessing camera {camera_idx + 1}/{len(cameras)}: {camera_data['img_name']}")

    # 重要：设置当前帧为固定值，避免帧号添加到文件名
    scene.frame_current = 1
    scene.frame_start = 1
    scene.frame_end = 1

    # 设置渲染分辨率
    render.resolution_x = camera_data['width']
    render.resolution_y = camera_data['height']

    # 读取COLMAP相机参数
    R_colmap_array = np.array(camera_data['rotation'], dtype=np.float64)  # COLMAP旋转矩阵
    T_colmap_array = np.array(camera_data['position'], dtype=np.float64)  # COLMAP位置向量

    # 应用我们发现的转换关系：第0列保持不变，第1列和第2列取反
    R_blender_array = R_colmap_array.copy()
    R_blender_array[:, 1] = -R_blender_array[:, 1]  # 第1列取反
    R_blender_array[:, 2] = -R_blender_array[:, 2]  # 第2列取反

    # 转换为Blender Matrix格式
    R_blender = Matrix(R_blender_array.tolist())
    T_blender = Vector(T_colmap_array.tolist())

    # 设置相机位置（直接使用COLMAP位置，不调整）
    cam.location = T_blender
    print(f"  Camera position: [{T_blender.x:.3f}, {T_blender.y:.3f}, {T_blender.z:.3f}]")

    # 设置相机旋转 (使用四元数)
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = R_blender.to_quaternion()

    # 设置相机FOV（推荐方法：直接使用FOV，避免焦距单位转换问题）
    fx = camera_data['fx']
    fy = camera_data['fy']
    width = camera_data['width']
    height = camera_data['height']

    # 计算FOV（弧度）
    fov_x_rad = 2 * math.atan(width / (2 * fx))
    fov_y_rad = 2 * math.atan(height / (2 * fy))

    # 设置Blender相机FOV
    cam.data.type = 'PERSP'
    cam.data.angle = fov_x_rad  # 使用水平FOV
    cam.data.sensor_fit = 'HORIZONTAL'

    print(f"  Resolution: {width}x{height}")
    print(f"  Focal length: fx={fx:.1f}px, fy={fy:.1f}px")
    print(f"  FOV: {math.degrees(fov_x_rad):.2f}° x {math.degrees(fov_y_rad):.2f}°")

    # 设置输出文件名（避免Blender重复添加扩展名和帧号）
    img_name = camera_data['img_name']

    # 如果img_name已经包含扩展名，去掉扩展名作为基础名
    if '.' in img_name:
        base_name = os.path.splitext(img_name)[0]
    else:
        base_name = img_name

    # 修改点：直接使用输出目录，不创建子文件夹
    output_path = os.path.join(output_folder, base_name)

    # 设置主渲染路径
    if 'render' in output_types:
        scene.render.filepath = output_path
        print(f"  Main render output: {base_name}.{args.format.lower()}")
    else:
        scene.render.filepath = ''  # 不保存主渲染图像

    # 设置其他输出路径
    if depth_file_output:
        depth_file_output.file_slots[0].path = output_path
        print(f"  Depth output: {base_name}_Depth.{args.format.lower()}")
    if normal_file_output:
        normal_file_output.file_slots[0].path = output_path
        print(f"  Normal output: {base_name}_Normal.{args.format.lower()}")
    if albedo_file_output:
        albedo_file_output.file_slots[0].path = output_path
        print(f"  Albedo output: {base_name}_Albedo.{args.format.lower()}")
    if id_file_output:
        id_file_output.file_slots[0].path = output_path
        print(f"  ID output: {base_name}_ID.{args.format.lower()}")

    # 渲染当前视图
    print(f"  🎬 Rendering...")
    bpy.ops.render.render(write_still=True)
    print(f"  ✅ Rendered {base_name}")

print(f"\n🎉 All {len(cameras)} cameras rendered successfully!")
print(f"📁 Output directory: {output_folder}")

# For debugging the workflow
# bpy.ops.wm.save_as_mainfile(filepath='debug.blend')