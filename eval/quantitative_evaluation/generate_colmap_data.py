import re
import numpy as np
from scene.colmap_loader import rotmat2qvec

def parse_camera_poses(file_path):
    frame_pattern = re.compile(r"\[Frame \d+: .*?name:\S+\.png\]", re.DOTALL)

    location_pattern = re.compile(r"Location: \[(.*?)\]")

    rotation_matrix_pattern = re.compile(
        r"Rotation Matrix:\s*\[\[\s*([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s*\]\s*\[\s*([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s*\]\s*\[\s*([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s+([-eE\d\.+-]+)\s*\]\]",
        re.DOTALL
    )

    focalx_pattern = re.compile(r"FocalX: (\d+\.\d+)")
    focaly_pattern = re.compile(r"FocalY: (\d+\.\d+)")
    fovx_pattern = re.compile(r"FovX: ([\d\.]+)")
    fovy_pattern = re.compile(r"FovY: ([\d\.]+)")
    name_pattern = re.compile(r"name:(\S+\.png)")

    with open(file_path, 'r') as file:
        content = file.read()

    frames = frame_pattern.findall(content)

    results = []

    for frame in frames:
        data = {}

        blender2opencv = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]])

        print("Current frame content:", repr(frame))
        rotation_match = rotation_matrix_pattern.search(frame)
        if rotation_match:
            print("Matched Rotation Matrix keyword:", rotation_match.group(0))
        else:
            print("Rotation Matrix keyword not found")


        rotation_match = rotation_matrix_pattern.search(frame)
        print("rotation_match", rotation_match, "-----------")

        if rotation_match:

            R1 = [float(rotation_match.group(i)) for i in range(1, 4)]
            R2 = [float(rotation_match.group(i)) for i in range(4, 7)]
            R3 = [float(rotation_match.group(i)) for i in range(7, 10)]
            R = np.array([R1, R2, R3])

            print("R", R)
            R = R @ blender2opencv
            print("R", R)
            data["R"] = R

            R = np.array(R)
            RX = np.linalg.inv(R)
            qvec = rotmat2qvec(RX)
            data["qvec"] = qvec.tolist()


        location_match = location_pattern.search(frame)

        if location_match:
            T = location_match.group(1).split(", ")
            print("T", T)
            T = np.array(T)
            T =  T.astype(np.float64)
            T = -np.matmul(RX, T)
            data["T"] = [float(val) for val in T]


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

        name_match = name_pattern.search(frame)
        if name_match:
            data["name"] = name_match.group(1)

        results.append(data)

    return results

def save_camera_poses_to_images_txt(camera_poses_data, output_file):
    lines = []

    for idx, data in enumerate(camera_poses_data):
        qvec = data["qvec"]
        T = data["T"]
        name = data["name"]

        index = idx + 1

        qvec_str = " ".join(map(str, qvec))
        T_str = " ".join(map(str, T))

        line = f"{index} {qvec_str} {T_str} {index} {name}"

        lines.append(line)

    result_content = "\n\n".join(lines)

    with open(output_file, 'w') as f:
        f.write(result_content)


file_path = 'camera_poses.txt'
camera_poses_data = parse_camera_poses(file_path)

for data in camera_poses_data:
    print(data)

output_file = 'images.txt'
save_camera_poses_to_images_txt(camera_poses_data, output_file)
