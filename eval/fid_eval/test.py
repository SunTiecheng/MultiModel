import bpy
import numpy as np
import os
import sys
from mathutils import Vector, Matrix
import math
import random
import bmesh


class PLYRenderer:
    def __init__(self, ply_path, output_dir, num_renders=20):
        """
        初始化PLY渲染器

        Args:
            ply_path: PLY文件路径
            output_dir: 输出图片目录
            num_renders: 渲染图片数量
        """
        self.ply_path = ply_path
        self.output_dir = output_dir
        self.num_renders = num_renders
        self.texture_files = []
        self.vertices = []
        self.faces = []
        self.face_texcoords = []
        self.face_texnumbers = []
        self.face_colors = []
        self.has_texnumber = False

        # 默认渲染参数
        self.render_resolution = (1920, 1080)
        self.render_samples = 128
        self.render_engine = 'CYCLES'
        self.camera_distance_factor = 1.5

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

    def clear_scene(self):
        """清空场景中的所有对象"""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # 清空所有mesh数据
        for mesh in bpy.data.meshes:
            bpy.data.meshes.remove(mesh)

    def parse_ply_header(self):
        """解析PLY文件头部信息"""
        self.has_texnumber = False
        face_properties = []

        with open(self.ply_path, 'r') as f:
            line = f.readline().strip()
            if line != 'ply':
                raise ValueError("不是有效的PLY文件")

            in_header = True
            vertex_count = 0
            face_count = 0
            current_element = None

            while in_header:
                line = f.readline().strip()
                if line == 'end_header':
                    in_header = False
                elif line.startswith('comment TextureFile'):
                    # 提取纹理文件名
                    texture_file = line.split()[-1]
                    self.texture_files.append(texture_file)
                elif line.startswith('element vertex'):
                    vertex_count = int(line.split()[-1])
                    current_element = 'vertex'
                elif line.startswith('element face'):
                    face_count = int(line.split()[-1])
                    current_element = 'face'
                elif line.startswith('property') and current_element == 'face':
                    face_properties.append(line)
                    if 'texnumber' in line:
                        self.has_texnumber = True

        print(f"面属性: {face_properties}")
        print(f"是否有texnumber: {self.has_texnumber}")
        return vertex_count, face_count

    def read_ply_data(self):
        """读取PLY文件的完整数据"""
        vertex_count, face_count = self.parse_ply_header()

        with open(self.ply_path, 'r') as f:
            # 跳过头部
            line = f.readline()
            while line.strip() != 'end_header':
                line = f.readline()

            # 读取顶点
            for i in range(vertex_count):
                line = f.readline().strip().split()
                x, y, z = float(line[0]), float(line[1]), float(line[2])
                self.vertices.append((x, y, z))

            # 读取前几个面来分析格式
            print("\n分析面数据格式...")
            for i in range(min(3, face_count)):
                line = f.readline().strip()
                print(f"面 {i}: {line}")

            # 重新打开文件并跳到面数据开始位置
            f.seek(0)
            line = f.readline()
            while line.strip() != 'end_header':
                line = f.readline()
            # 跳过顶点
            for i in range(vertex_count):
                f.readline()

            # 读取面
            for i in range(face_count):
                line = f.readline().strip().split()
                idx = 0

                try:
                    # 顶点索引
                    num_verts = int(line[idx])
                    idx += 1
                    vert_indices = []
                    for j in range(num_verts):
                        vert_indices.append(int(line[idx]))
                        idx += 1
                    self.faces.append(vert_indices)

                    # 纹理坐标
                    num_texcoords = int(line[idx])
                    idx += 1
                    texcoords = []
                    for j in range(num_texcoords):
                        texcoords.append(float(line[idx]))
                        idx += 1
                    self.face_texcoords.append(texcoords)

                    # 纹理编号 (如果存在)
                    if self.has_texnumber:
                        texnumber = int(line[idx])
                        self.face_texnumbers.append(texnumber)
                        idx += 1
                    else:
                        # 没有texnumber，所有面使用纹理0
                        self.face_texnumbers.append(0)

                    # 颜色 (红、绿、蓝、透明度)
                    if idx + 3 < len(line):
                        r, g, b, a = int(line[idx]), int(line[idx + 1]), int(line[idx + 2]), int(line[idx + 3])
                        self.face_colors.append((r / 255.0, g / 255.0, b / 255.0, a / 255.0))
                    elif idx + 2 < len(line):
                        # 只有RGB，没有alpha
                        r, g, b = int(line[idx]), int(line[idx + 1]), int(line[idx + 2])
                        self.face_colors.append((r / 255.0, g / 255.0, b / 255.0, 1.0))
                    else:
                        # 默认白色
                        self.face_colors.append((1.0, 1.0, 1.0, 1.0))

                except (ValueError, IndexError) as e:
                    if i < 3:  # 只打印前几个错误
                        print(f"警告: 读取第 {i} 个面时出错: {e}")
                        print(f"当前行内容: {' '.join(line)}")
                        print(f"当前索引: {idx}, 行长度: {len(line)}")
                    # 使用默认值
                    if len(self.faces) > len(self.face_texcoords):
                        self.face_texcoords.append([])
                    if len(self.faces) > len(self.face_texnumbers):
                        self.face_texnumbers.append(0)
                    if len(self.faces) > len(self.face_colors):
                        self.face_colors.append((1.0, 1.0, 1.0, 1.0))

    def create_mesh_with_multiple_textures(self):
        """创建带有多个纹理的网格"""
        # 创建网格
        mesh = bpy.data.meshes.new(name="PLY_Mesh")
        obj = bpy.data.objects.new("PLY_Object", mesh)
        bpy.context.collection.objects.link(obj)

        # 使用bmesh创建几何体
        bm = bmesh.new()

        # 添加顶点
        for v in self.vertices:
            bm.verts.new(v)
        bm.verts.ensure_lookup_table()

        # 创建UV层
        uv_layer = bm.loops.layers.uv.new()

        # 按纹理编号分组面
        faces_by_texture = {}
        for i, (face_verts, texcoords, texnum) in enumerate(zip(self.faces, self.face_texcoords, self.face_texnumbers)):
            if texnum not in faces_by_texture:
                faces_by_texture[texnum] = []
            faces_by_texture[texnum].append((i, face_verts, texcoords))

        # 创建面并分配材质索引
        material_indices = {}
        current_mat_index = 0

        for texnum in sorted(faces_by_texture.keys()):
            material_indices[texnum] = current_mat_index
            current_mat_index += 1

            for face_idx, face_verts, texcoords in faces_by_texture[texnum]:
                # 创建面
                try:
                    bmface = bm.faces.new([bm.verts[v] for v in face_verts])
                    bmface.material_index = material_indices[texnum]

                    # 设置UV坐标
                    for j, loop in enumerate(bmface.loops):
                        uv_idx = j * 2
                        if uv_idx + 1 < len(texcoords):
                            loop[uv_layer].uv = (texcoords[uv_idx], texcoords[uv_idx + 1])

                except ValueError:
                    # 面已存在，跳过
                    pass

        # 更新mesh
        bm.to_mesh(mesh)
        bm.free()

        self.obj = obj

        # 创建材质
        self.create_materials_for_textures(material_indices)

        return obj

    def create_materials_for_textures(self, material_indices):
        """为每个纹理创建材质"""
        ply_dir = os.path.dirname(self.ply_path)

        for texnum, mat_index in material_indices.items():
            # 确保纹理编号在范围内
            if texnum < len(self.texture_files):
                texture_file = self.texture_files[texnum]
                texture_path = os.path.join(ply_dir, texture_file)

                # 创建材质
                mat_name = f"Material_Texture_{texnum}"
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True

                # 获取节点
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                # 清除默认节点
                nodes.clear()

                # 创建节点
                output_node = nodes.new(type='ShaderNodeOutputMaterial')
                bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')

                if os.path.exists(texture_path):
                    # 创建纹理节点
                    texture_node = nodes.new(type='ShaderNodeTexImage')
                    texture_node.image = bpy.data.images.load(texture_path)

                    # 创建UV映射节点
                    uv_node = nodes.new(type='ShaderNodeUVMap')

                    # 连接节点
                    links.new(uv_node.outputs['UV'], texture_node.inputs['Vector'])
                    links.new(texture_node.outputs['Color'], bsdf_node.inputs['Base Color'])
                    links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
                else:
                    print(f"警告: 纹理文件 {texture_path} 不存在")
                    # 使用默认颜色
                    links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])

                # 添加材质到对象
                self.obj.data.materials.append(mat)

    def center_object_to_centroid(self):
        """将对象的重心移动到原点"""
        # 计算重心
        centroid = Vector((0, 0, 0))
        for v in self.vertices:
            centroid += Vector(v)
        centroid /= len(self.vertices)

        # 移动对象使重心位于原点
        self.obj.location = -centroid

        # 应用变换
        bpy.context.view_layer.update()

        return centroid

    def calculate_bounding_box(self):
        """计算对象的包围盒"""
        # 获取世界坐标下的包围盒
        bbox_corners = [self.obj.matrix_world @ Vector(corner) for corner in self.obj.bound_box]

        # 计算包围盒的最小和最大点
        min_point = Vector((min(v.x for v in bbox_corners),
                            min(v.y for v in bbox_corners),
                            min(v.z for v in bbox_corners)))
        max_point = Vector((max(v.x for v in bbox_corners),
                            max(v.y for v in bbox_corners),
                            max(v.z for v in bbox_corners)))

        # 计算包围盒的对角线长度
        diagonal = (max_point - min_point).length

        # 相机距离设置为对角线长度的倍数（可配置）
        self.camera_distance = diagonal * self.camera_distance_factor

        return min_point, max_point, diagonal

    def setup_camera(self):
        """设置相机"""
        # 创建相机
        camera_data = bpy.data.cameras.new(name="Camera")
        camera_obj = bpy.data.objects.new("Camera", camera_data)
        bpy.context.collection.objects.link(camera_obj)

        # 设置为活动相机
        bpy.context.scene.camera = camera_obj

        self.camera = camera_obj
        return camera_obj

    def setup_lighting(self):
        """设置照明"""
        # 添加环境光
        world = bpy.context.scene.world
        world.use_nodes = True
        bg_node = world.node_tree.nodes['Background']
        bg_node.inputs[0].default_value = (1, 1, 1, 1)  # 白色背景
        bg_node.inputs[1].default_value = 0.5  # 强度

        # 添加主光源
        light_data = bpy.data.lights.new(name="Key_Light", type='SUN')
        light_data.energy = 1.5
        light_obj = bpy.data.objects.new(name="Key_Light", object_data=light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.rotation_euler = (math.radians(45), math.radians(45), 0)

        # 添加补光
        fill_light_data = bpy.data.lights.new(name="Fill_Light", type='SUN')
        fill_light_data.energy = 0.5
        fill_light_obj = bpy.data.objects.new(name="Fill_Light", object_data=fill_light_data)
        bpy.context.collection.objects.link(fill_light_obj)
        fill_light_obj.rotation_euler = (math.radians(-45), math.radians(-45), 0)

    def generate_camera_positions(self):
        """在球面上生成随机相机位置"""
        positions = []

        for i in range(self.num_renders):
            # 生成随机球面坐标
            # theta: 方位角 (0 到 2π)
            # phi: 极角 (0 到 π)
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(math.pi * 0.1, math.pi * 0.9)  # 避免极点

            # 转换为笛卡尔坐标
            x = self.camera_distance * math.sin(phi) * math.cos(theta)
            y = self.camera_distance * math.sin(phi) * math.sin(theta)
            z = self.camera_distance * math.cos(phi)

            positions.append(Vector((x, y, z)))

        return positions

    def point_camera_to_origin(self, camera_pos):
        """将相机对准原点"""
        # 设置相机位置
        self.camera.location = camera_pos

        # 计算相机朝向
        direction = -camera_pos.normalized()

        # 计算旋转四元数
        rot_quat = direction.to_track_quat('-Z', 'Y')
        self.camera.rotation_euler = rot_quat.to_euler()

    def setup_render_settings(self):
        """设置渲染参数"""
        scene = bpy.context.scene

        # 设置渲染引擎
        scene.render.engine = self.render_engine
        if self.render_engine == 'CYCLES':
            scene.cycles.samples = self.render_samples

        # 设置输出分辨率
        scene.render.resolution_x = self.render_resolution[0]
        scene.render.resolution_y = self.render_resolution[1]
        scene.render.resolution_percentage = 100

        # 设置输出格式
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'

    def render_views(self):
        """渲染多个视角"""
        camera_positions = self.generate_camera_positions()

        for i, pos in enumerate(camera_positions):
            # 设置相机位置并对准原点
            self.point_camera_to_origin(pos)

            # 设置输出路径
            output_path = os.path.join(self.output_dir, f"render_{i:04d}.png")
            bpy.context.scene.render.filepath = output_path

            # 渲染
            print(f"渲染视角 {i + 1}/{self.num_renders}...")
            bpy.ops.render.render(write_still=True)

        print("渲染完成！")

    def run(self):
        """执行完整的渲染流程"""
        # 清空场景
        self.clear_scene()

        # 读取PLY文件数据
        print(f"读取PLY文件: {self.ply_path}")
        self.read_ply_data()
        print(f"找到 {len(self.texture_files)} 个纹理文件: {self.texture_files}")

        # 创建带纹理的网格
        print("创建网格和材质...")
        self.create_mesh_with_multiple_textures()

        # 将重心移到原点
        print("调整模型位置...")
        self.center_object_to_centroid()

        # 计算包围盒
        print("计算包围盒...")
        self.calculate_bounding_box()

        # 设置相机
        print("设置相机...")
        self.setup_camera()

        # 设置照明
        print("设置照明...")
        self.setup_lighting()

        # 设置渲染参数
        print("设置渲染参数...")
        self.setup_render_settings()

        # 渲染多个视角
        print(f"开始渲染 {self.num_renders} 个视角...")
        self.render_views()


# 使用示例
if __name__ == "__main__":
    import argparse

    # 备选配置（当无法使用命令行参数时）
    # 可以直接修改这些值
    DIRECT_CONFIG = {
        'PLY_FILE': None,  # 例如: "/path/to/model.ply"
        'OUTPUT_DIR': None,  # 例如: "./output"
        'NUM_RENDERS': 20,
        'RESOLUTION': (1000, 1000),
        'SAMPLES': 128,
        'ENGINE': 'CYCLES',
        'DISTANCE': 1.5
    }

    # 尝试使用命令行参数
    use_direct_config = False

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='使用Blender渲染PLY格式的3D模型')
    parser.add_argument('input', type=str, help='PLY文件路径')
    parser.add_argument('output', type=str, help='输出图片目录')
    parser.add_argument('-n', '--num-renders', type=int, default=20,
                        help='渲染图片数量 (默认: 20)')
    parser.add_argument('-r', '--resolution', type=str, default='1920x1080',
                        help='输出分辨率，格式: WIDTHxHEIGHT (默认: 1920x1080)')
    parser.add_argument('-s', '--samples', type=int, default=128,
                        help='Cycles渲染采样数 (默认: 128)')
    parser.add_argument('-e', '--engine', type=str, default='CYCLES',
                        choices=['CYCLES', 'BLENDER_EEVEE'],
                        help='渲染引擎 (默认: CYCLES)')
    parser.add_argument('-d', '--distance', type=float, default=1.5,
                        help='相机距离系数，相对于包围盒对角线 (默认: 1.5)')

    # 处理Blender传递的参数
    # 当使用 blender --background --python script.py -- args 时
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]

    # 如果没有参数且没有配置直接参数，显示帮助
    if len(argv) == 0 and DIRECT_CONFIG['PLY_FILE'] is None:
        print("\n错误: 没有提供输入参数")
        print("\n使用方法:")
        print("1. 通过Blender命令行（注意双横线）:")
        print("   blender --background --python render_ply.py -- input.ply output_dir [选项]")
        print("\n2. 或者修改脚本中的 DIRECT_CONFIG 配置")
        print("\n示例:")
        print("   blender --background --python render_ply.py -- model.ply ./output -n 30")
        print("   blender --background --python render_ply.py -- model.ply ./output -n 50 -r 4096x2160")
        parser.print_help()
        sys.exit(1)

    # 尝试解析命令行参数
    if len(argv) > 0:
        try:
            args = parser.parse_args(argv)

            # 解析分辨率
            try:
                width, height = map(int, args.resolution.split('x'))
                resolution = (width, height)
            except ValueError:
                print(f"错误: 无效的分辨率格式 '{args.resolution}'，应该是 'WIDTHxHEIGHT'")
                sys.exit(1)

            # 设置参数
            ply_file = args.input
            output_dir = args.output
            num_renders = args.num_renders
            samples = args.samples
            engine = args.engine
            distance = args.distance

        except SystemExit:
            if DIRECT_CONFIG['PLY_FILE'] is not None:
                use_direct_config = True
            else:
                raise
    else:
        use_direct_config = True

    # 使用直接配置
    if use_direct_config:
        if DIRECT_CONFIG['PLY_FILE'] is None:
            print("错误: 请在脚本中设置 DIRECT_CONFIG['PLY_FILE'] 和 DIRECT_CONFIG['OUTPUT_DIR']")
            sys.exit(1)
        ply_file = DIRECT_CONFIG['PLY_FILE']
        output_dir = DIRECT_CONFIG['OUTPUT_DIR']
        num_renders = DIRECT_CONFIG['NUM_RENDERS']
        resolution = DIRECT_CONFIG['RESOLUTION']
        samples = DIRECT_CONFIG['SAMPLES']
        engine = DIRECT_CONFIG['ENGINE']
        distance = DIRECT_CONFIG['DISTANCE']

    # 检查输入文件
    if not os.path.exists(ply_file):
        print(f"错误: 输入文件 '{ply_file}' 不存在")
        sys.exit(1)

    # 创建渲染器
    renderer = PLYRenderer(ply_file, output_dir, num_renders)

    # 设置额外的参数
    renderer.render_resolution = resolution
    renderer.render_samples = samples
    renderer.render_engine = engine
    renderer.camera_distance_factor = distance

    # 显示配置信息
    print("=" * 50)
    print("PLY渲染器配置:")
    print(f"输入文件: {ply_file}")
    print(f"输出目录: {output_dir}")
    print(f"渲染数量: {num_renders}")
    print(f"分辨率: {resolution[0]}x{resolution[1]}")
    print(f"采样数: {samples}")
    print(f"渲染引擎: {engine}")
    print(f"相机距离系数: {distance}")
    print("=" * 50)

    # 执行渲染
    renderer.run()