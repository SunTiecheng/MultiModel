import re
import numpy as np
from scene.colmap_loader import rotmat2qvec

# 将旋转矩阵转换为四元数的函数
# def rotmat2qvec(R):
#     R = np.array(R)  # 确保R是一个numpy数组
#     Rxx, Ryx, Rzx, Rxy, Ryy, Rzy, Rxz, Ryz, Rzz = R.flat
#     K = np.array([
#         [Rxx - Ryy - Rzz, 0, 0, 0],
#         [Ryx + Rxy, Ryy - Rxx - Rzz, 0, 0],
#         [Rzx + Rxz, Rzy + Ryz, Rzz - Rxx - Ryy, 0],
#         [Ryz - Rzy, Rzx - Rxz, Rxy - Ryx, Rxx + Ryy + Rzz]]) / 3.0
#     eigvals, eigvecs = np.linalg.eigh(K)
#     qvec = eigvecs[[3, 0, 1, 2], np.argmax(eigvals)]
#     if qvec[0] < 0:
#         qvec *= -1
#     return qvec


# 解析camera_poses.txt文件的函数
def parse_camera_poses(file_path):
    # 定义正则表达式模式
    # frame_pattern = re.compile(r"\[Frame \d+: .*?\]", re.DOTALL)
    frame_pattern = re.compile(r"\[Frame \d+: .*?name:\S+\.png\]", re.DOTALL)

    # location_pattern = re.compile(r"Location: <Vector \((.*?)\)>")
    location_pattern = re.compile(r"Location: \[(.*?)\]")
    # rotation_matrix_pattern = re.compile(r"Rotation Matrix: <Matrix 3x3 \((.*?)\)\s+\((.*?)\)\s+\((.*?)\)>")
    # rotation_matrix_pattern = re.compile(
    #     r"Rotation Matrix:\s*<Matrix 3x3\s*\((.*?)\)\s*\((.*?)\)\s*\((.*?)\)>", re.DOTALL
    # )
    rotation_matrix_pattern = re.compile(
        r"Rotation Matrix:\s*\[\[\s*([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s*\]\s*\[\s*([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s*\]\s*\[\s*([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s*\]\]",
        re.DOTALL
    )

    focalx_pattern = re.compile(r"FocalX: (\d+\.\d+)")
    focaly_pattern = re.compile(r"FocalY: (\d+\.\d+)")
    fovx_pattern = re.compile(r"FovX: ([\d\.]+)")
    fovy_pattern = re.compile(r"FovY: ([\d\.]+)")
    name_pattern = re.compile(r"name:(\S+\.png)")

    # 读取文件内容
    with open(file_path, 'r') as file:
        content = file.read()

    # 匹配所有Frame块
    frames = frame_pattern.findall(content)

    # 存储解析结果的字典列表
    results = []

    # 解析每一个Frame块
    for frame in frames:
        data = {}

        # # 提取Location (T)
        # location_match = location_pattern.search(frame)
        # if location_match:
        #     T = location_match.group(1).split(", ")
        #     data["T"] = [float(val) for val in T]

        blender2opencv = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])

        print("Current frame content:", repr(frame))  # 打印原始frame内容
        rotation_match = rotation_matrix_pattern.search(frame)
        if rotation_match:
            print("Matched Rotation Matrix keyword:", rotation_match.group(0))
        else:
            print("Rotation Matrix keyword not found")



        # 提取Rotation Matrix (R)
        rotation_match = rotation_matrix_pattern.search(frame)
        print("rotation_match", rotation_match, "-----------")

        if rotation_match:
            # R1 = rotation_match.group(1).split(", ")
            # R2 = rotation_match.group(2).split(", ")
            # R3 = rotation_match.group(3).split(", ")
            # R = [[float(val) for val in R1], [float(val) for val in R2], [float(val) for val in R3]]

            # 提取每行并转换为浮点数
            R1 = [float(rotation_match.group(i)) for i in range(1, 4)]
            R2 = [float(rotation_match.group(i)) for i in range(4, 7)]
            R3 = [float(rotation_match.group(i)) for i in range(7, 10)]
            # 创建3x3矩阵R
            R = np.array([R1, R2, R3])

            print("R", R)
            R = R @ blender2opencv
            print("R", R)
            # A = np.array([[0.6,0.8,0.9],[0.4,0.5,0.7],[0.3,0.2,0.1]])
            # A = A @ blender2opencv
            # print("A", A)
            data["R"] = R

            # 计算四元数qvec
            R = np.array(R)
            RX = np.linalg.inv(R)
            # R = -R
            # R = R.T
            qvec = rotmat2qvec(RX)  # 传递R，R现在是numpy数组
            # print("qvec", qvec)
            # qvec[1:] = -qvec[1:]
            # print("fix_qvec", qvec)
            data["qvec"] = qvec.tolist()


    # 提取Location (T)
        location_match = location_pattern.search(frame)

        if location_match:
            T = location_match.group(1).split(", ")
            print("T", T)
            T = np.array(T)
            T =  T.astype(np.float64)
            # T[1:] = -np.abs(T[1:])
            # T = -np.matmul(R, T)
            T = -np.matmul(RX, T)
            # print("T:", T)
            # T = -T
            # T = -R @ T
            data["T"] = [float(val) for val in T]


        # 提取FocalX, FocalY, FovX, FovY
        focalx_match = focalx_pattern.search(frame)
        focaly_match = focaly_pattern.search(frame)
        fovx_match = fovx_pattern.search(frame)
        fovy_match = fovy_pattern.search(frame)

        if focalx_match:
            data["FocalX"] = float(focalx_match.group(1))
        if focaly_match:
            data["FocalY"] = float(focaly_match.group(1))
        if fovx_match:
            data["FovX"] = float(fovx_match.group(1))
        if fovy_match:
            data["FovY"] = float(fovy_match.group(1))

        # 提取name
        name_match = name_pattern.search(frame)
        if name_match:
            data["name"] = name_match.group(1)

        # 将数据加入到结果列表
        results.append(data)

    return results

def save_camera_poses_to_images_txt(camera_poses_data, output_file):
    lines = []

    # 遍历camera_poses_data，提取qvec, T和name，并生成格式化字符串
    for idx, data in enumerate(camera_poses_data):
        qvec = data["qvec"]
        T = data["T"]
        name = data["name"]

        # 序号从1开始
        index = idx + 1
        # index = 1

        # 将qvec和T的值拼接成字符串，空格分隔
        qvec_str = " ".join(map(str, qvec))
        T_str = " ".join(map(str, T))

        # 组成一行的格式：序号 qvec T 1 name

        line = f"{index} {qvec_str} {T_str} {index} {name}"

        # 将行添加到lines列表
        lines.append(line)

    # 将所有行以空行分隔，拼接成完整内容
    result_content = "\n\n".join(lines)

    # 将内容写入到文件
    with open(output_file, 'w') as f:
        f.write(result_content)


# 使用示例
file_path = 'camera_poses.txt'
camera_poses_data = parse_camera_poses(file_path)

# 打印每个frame的解析数据
for data in camera_poses_data:
    print(data)

# 使用示例
output_file = 'images.txt'
save_camera_poses_to_images_txt(camera_poses_data, output_file)
