import numpy as np
import os


def center_mesh(input_path, output_path):
    """将网格的重心移动到坐标系原点，支持 PLY 和 OBJ 格式"""

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    ext = os.path.splitext(input_path)[1].lower()

    if ext == '.ply':
        center_ply(input_path, output_path)
    elif ext == '.obj':
        center_obj(input_path, output_path)
    else:
        raise ValueError(f"不支持的格式: {ext}。仅支持 .ply 和 .obj 文件")


def center_ply(input_path, output_path):
    """处理 PLY 格式文件"""
    try:
        from plyfile import PlyData, PlyElement
    except ImportError:
        raise ImportError("处理 PLY 需要 plyfile 库。请运行: pip install plyfile")

    ply_data = PlyData.read(input_path)

    # 检查是否有顶点数据
    if 'vertex' not in ply_data:
        raise ValueError("PLY 文件中未找到顶点数据")

    vertices = ply_data['vertex']

    # 提取顶点坐标
    vert_coords = np.vstack([vertices['x'], vertices['y'], vertices['z']]).T

    # 计算重心
    centroid = np.mean(vert_coords, axis=0)
    print(f"PLY 文件原始重心: {centroid}")

    # 平移顶点到原点
    vert_coords -= centroid

    # 更新顶点数据
    vertices['x'] = vert_coords[:, 0]
    vertices['y'] = vert_coords[:, 1]
    vertices['z'] = vert_coords[:, 2]

    # 保存新文件
    PlyData(ply_data.elements).write(output_path)
    print(f"中心化 PLY 已保存至: {output_path}")

    # 验证新重心
    new_centroid = np.mean(vert_coords, axis=0)
    print(f"新重心验证: {new_centroid} (应接近零)")


def center_obj(input_path, output_path):
    """处理 OBJ 格式文件 - 修复版本"""
    vertices = []
    vertex_lines = []  # 存储原始顶点行信息
    other_lines = []  # 存储其他行

    # 第一次读取：收集顶点数据
    with open(input_path, 'r') as f:
        for line in f:
            stripped = line.strip()

            # 处理顶点行 (v x y z)
            if stripped.startswith('v ') and len(stripped.split()) >= 4:
                parts = stripped.split()
                try:
                    # 提取前三个坐标值
                    x, y, z = map(float, parts[1:4])
                    vertices.append([x, y, z])
                    vertex_lines.append(line)  # 保留原始行信息
                except ValueError:
                    other_lines.append(line)  # 格式错误，保留原样
            else:
                other_lines.append(line)  # 非顶点行

    if not vertices:
        raise ValueError("OBJ 文件中未找到有效顶点")

    # 计算重心
    vert_array = np.array(vertices)
    centroid = np.mean(vert_array, axis=0)
    print(f"OBJ 文件原始重心: {centroid}")

    # 计算平移后的顶点
    centered_verts = vert_array - centroid

    # 第二次处理：写入修改后的文件
    with open(output_path, 'w') as f_out:
        vertex_index = 0

        # 先处理非顶点行
        for line in other_lines:
            f_out.write(line)

        # 再写入修改后的顶点
        for orig_line in vertex_lines:
            stripped = orig_line.strip()
            parts = stripped.split()

            # 创建新的顶点行
            new_vert = centered_verts[vertex_index]
            new_line = f"v {new_vert[0]:.6f} {new_vert[1]:.6f} {new_vert[2]:.6f}"

            # 保留原始行的额外数据（纹理坐标、法线等）
            if len(parts) > 4:
                extra = " " + " ".join(parts[4:])
                new_line += extra

            f_out.write(new_line + "\n")
            vertex_index += 1

    print(f"中心化 OBJ 已保存至: {output_path}")

    # 验证新重心
    new_centroid = np.mean(centered_verts, axis=0)
    print(f"新重心验证: {new_centroid} (应接近零)")


if __name__ == "__main__":
    input_file = "mesh_no_bg.obj"  # 或 .ply 文件
    output_file = "centered_model.obj"  # 或 .ply

    center_mesh(input_file, output_file)