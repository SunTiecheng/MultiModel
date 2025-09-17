import numpy as np
import argparse
import open3d as o3d
from plyfile import PlyData, PlyElement, PlyProperty
from PIL import Image
import os
import cv2
import re
from scene.colmap_loader import read_extrinsics_binary, read_intrinsics_binary
from scene.dataset_readers import readColmapCameras
from utils.graphics_utils import getWorld2View2, focal2fov, fov2focal, getWorld2View


# 读取点云
def load_point_cloud(ply_file_path):
    pcd = PlyData.read(ply_file_path)
    return pcd

def save_point_cloud(vertices, faces, output_file_path):
    vertex_element = PlyElement.describe(vertices, 'vertex')
    # face_element = PlyElement.describe(faces, 'face')
    face_element = PlyElement.describe(
        np.array([([f[0], f[1], f[2]],) for f in faces], dtype=[('vertex_indices', 'i4', (3,))]),
        'face'
    )
    PlyData([vertex_element, face_element], text=True).write(output_file_path)

def process_masks(mask_folder_path):
    masks_dict = {}  # 初始化一个空字典来存储文件名和对应的二值化掩码
    for mask_filename in sorted(os.listdir(mask_folder_path)):
        mask_path = os.path.join(mask_folder_path, mask_filename)
        if os.path.isfile(mask_path):  # 确保是文件
            image = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                print("Failed to load the image from", mask_folder_path)
                return None
            _, binary_mask = cv2.threshold(image, 30, 1, cv2.THRESH_BINARY)
            if np.any(binary_mask):  # 如果掩码中至少有一个非零元素
                # 获取去除文件扩展名的文件名
                mask_name_without_ext = os.path.splitext(mask_filename)[0]
                # 添加二值化掩码到字典，键是去除后缀的文件名
                masks_dict[mask_name_without_ext] = binary_mask
            else:
                print("Binary mask is fully zero. Skipping:", mask_filename)
    return masks_dict


def get_mask_names(mask_folder_path):
    mask_names = set()
    for mask_filename in os.listdir(mask_folder_path):
        if os.path.isfile(os.path.join(mask_folder_path, mask_filename)):
            mask_name_without_ext = os.path.splitext(mask_filename)[0]
            mask_names.add(mask_name_without_ext)
    return mask_names


def get_mask_files_number(mask_folder_path):
    mask_files = [f for f in os.listdir(mask_folder_path) if os.path.isfile(os.path.join(mask_folder_path, f))]
    return len(mask_files)


def project_and_filter(cam_infos, binary_masks, new_file_path):
    mask_names = get_mask_names(mask_folder_path)
    print("---------------------------------------------------------------------------------------------")
    times = 0
    for idx, camera, in enumerate(cam_infos):
        camera = cam_infos[idx]
        if camera.image_name not in mask_names:
            continue  # 跳过不在mask_names中的项

        print("idx", idx)

        if times < 1 :
            pcd = load_point_cloud(ply_file_path)
            vertices = np.array(pcd.elements[0].data)
            faces = np.array(pcd.elements[1].data)
            faces = np.stack((faces["vertex_indices"]))
            print("vertices1", vertices)
            print("faces1", faces)
        else:
            vertices = filtered_points
            faces = filtered_faces
            print("vertices2", vertices)
            print("faces2", faces)

        properties = vertices.dtype.names
        dtype_desc = [(prop, vertices[prop].dtype) for prop in properties]
        test_points = np.array([vertices[prop] for prop in properties]).T




        print("camera", camera)
        no = camera.image_name
        num_cameras = len(cam_infos)
        print("There are", num_cameras, "items in cam_infos.")
        print("第", idx, "次循环")
        filtered_points = np.array([], dtype=dtype_desc)

        mask = binary_masks[no]
        print("调用的mask编号为：", no)
        CAMERA_INTRINSICS = np.array([[camera.FocalX, 0, camera.width / 2],
                                      [0, camera.FocalY, camera.height / 2],
                                      [0, 0, 1]])
        # 计算世界坐标系到相机坐标系的变换
        C2W = getWorld2View(camera.R, camera.T)

        # 世界坐标系转相机坐标系
        points = np.stack((vertices["x"], vertices["y"], vertices["z"]), axis=1)
        points_homogeneous = np.hstack((points, np.ones((points.shape[0], 1))))
        points_camera = (C2W @ points_homogeneous.T).T[:, :3]
        print(f"image_name: {camera.image_name}")

        # 投影到平面
        pixels_homogeneous = CAMERA_INTRINSICS @ points_camera.T
        pixels = np.vstack((pixels_homogeneous[0, :] / pixels_homogeneous[2, :],
                            pixels_homogeneous[1, :] / pixels_homogeneous[2, :])).T

        # 计算在投影范围内的点
        within_projection = ((pixels[:, 0] >= 0) & (pixels[:, 0] < mask.shape[1]) &
                             (pixels[:, 1] >= 0) & (pixels[:, 1] < mask.shape[0]))

        # 计算投影范围内的点的像素坐标
        image_points_within_projection = pixels[within_projection].astype(np.int64)
        # 初始化 mask_values 全部为 True
        mask_values = np.ones(points_camera.shape[0], dtype=bool)
        # 仅对于投影范围内的点，更新 mask_values
        mask_values[within_projection] = mask[image_points_within_projection[:, 1], image_points_within_projection[:,
                                                                                    0]] == 1

        # 保留所有原始点，但将投影范围内的0值点删除
        filtered_points = test_points[mask_values]
        filtered_points = np.array([tuple(row) for row in filtered_points], dtype=dtype_desc)


        deleted_indices = np.where(~mask_values)[0]
        print("deleted_indices", deleted_indices)
        print("len(deleted_indices)", len(deleted_indices))
        deleted_indices = np.array(deleted_indices)
        mask = np.any(np.isin(faces, deleted_indices), axis=1)
        print("mask", mask)
        faces = faces[~mask]


        new_vertex_indices = np.arange(vertices.shape[0])
        new_vertex_indices = np.delete(new_vertex_indices, deleted_indices)
        print("new_vertex_indices:", new_vertex_indices)
        index_mapping = {old_idx: new_idx for new_idx, old_idx in enumerate(new_vertex_indices)}
        print("index_mapping:", index_mapping)
        filtered_faces = np.vectorize(index_mapping.get)(faces)
        print("filtered_faces:", filtered_faces)
        print("----------------------------------------------------------------------")
        times += 1


    save_point_cloud(filtered_points, filtered_faces, new_file_path)
    print(f"点云已保存为{new_file_path}")



path_to_images_bin = 'images.bin'
path_to_cameras_bin = 'cameras.bin'
path_to_cameras_extrinsic_file = "images.bin"
path_to_cameras_intrinsic_file = "cameras.bin"
images_folder = "images"
ex_images_data = read_extrinsics_binary(path_to_images_bin)
in_images_data = read_intrinsics_binary(path_to_cameras_bin)
cam_extrinsics = read_extrinsics_binary(path_to_cameras_extrinsic_file)
cam_intrinsics = read_intrinsics_binary(path_to_cameras_intrinsic_file)
cam_infos = readColmapCameras(cam_extrinsics=cam_extrinsics, cam_intrinsics=cam_intrinsics, images_folder=images_folder)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="run clean background")
    parser.add_argument('-i', '--input_file', type=str, help="Path to the input fply file.")

    args = parser.parse_args()



    camera_intrinsics = []
    camera_extrinsics = []
    for camera in cam_infos:
        # 设置相机内参
        camera_intrinsics = {
            'fx': camera.FocalX,
            'fy': camera.FocalY,
            'cx': camera.width / 2,
            'cy': camera.height / 2
        }

        # 设置相机外参
        camera_extrinsics = [
            {'R': camera.R, 't': camera.T},
        ]

    print("camera_intrinsics", camera_intrinsics)
    print("camera_extrinsics", camera_extrinsics)


    ply_file_path = os.path.join('./mesh_ply', args.input_file)

    print("ply_file_path", ply_file_path)
    file_name, file_ext = os.path.splitext(args.input_file)
    new_file_path = os.path.join('./mesh_ply', file_name + '_ps' + file_ext)

    print("new_file_path:", new_file_path)

    mask_folder_path = './dilate_mask'

    # 执行函数
    binary_masks = process_masks(mask_folder_path)

    filtered_pcd = project_and_filter(cam_infos, binary_masks, new_file_path)