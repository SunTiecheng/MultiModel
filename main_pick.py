import numpy as np
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
    new_file_path = 'test_point_cloud.ply'
    pcd.write(new_file_path)
    return pcd

def save_point_cloud(ply_file_path):
    save = PlyData.read(ply_file_path)
    #new_file_path = f"./output/iteration_60000/point_cloud.ply"
    new_file_path = f"./output/point_cloud.ply"
    save.write(new_file_path)
    return save

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


def project_and_filter(cam_infos, binary_masks):
    mask_names = get_mask_names(mask_folder_path)
    print("---------------------------------------------------------------------------------------------")
    for idx, camera in enumerate(cam_infos):
        camera = cam_infos[idx]
        if camera.image_name not in mask_names:
            continue  # 跳过不在mask_names中的项
        pcd = load_point_cloud(ply_file_path)
        if idx > 1 :
            pcd = load_point_cloud(queue_ply_path)
        vertex = pcd['vertex']
        properties = vertex.data.dtype.names
        dtype_desc = [(prop, vertex[prop].dtype) for prop in properties]  # 更新dtype描述以包含所有属性
        test_points = np.array([vertex[prop] for prop in properties]).T

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
        points = np.stack((np.asarray(pcd.elements[0]["x"]),
                           np.asarray(pcd.elements[0]["y"]),
                           np.asarray(pcd.elements[0]["z"])), axis=1)
        points_homogeneous = np.hstack((points, np.ones((points.shape[0], 1))))
        points_camera = (C2W @ points_homogeneous.T).T[:, :3]
        print(f"image_name: {camera.image_name}")

        # 投影到平面
        pixels_homogeneous = CAMERA_INTRINSICS @ points_camera.T
        pixels = np.vstack((pixels_homogeneous[0, :] / pixels_homogeneous[2, :],
                            pixels_homogeneous[1, :] / pixels_homogeneous[2, :])).T

        # 应用二值掩码
        valid_mask = ((pixels[:, 0] >= 0) & (pixels[:, 0] < mask.shape[1]) &
                      (pixels[:, 1] >= 0) & (pixels[:, 1] < mask.shape[0]))
        image_points = pixels[valid_mask].astype(np.int64)
        mask_values = mask[image_points[:, 1], image_points[:, 0]] == 1

        # 只保留当前相机视角下通过掩码测试的点
        # 应用mask过滤
        valid_points = test_points[valid_mask]
        filtered_points = valid_points[mask_values]

        # 根据过滤后的值，创造新的结构化数组
        structured_array = np.array([tuple(row) for row in filtered_points], dtype=dtype_desc)

        # 保存过滤后的点云到新的 PLY 文件
        vertex_element = PlyElement.describe(structured_array, 'vertex')
        queue_ply_path = f"./queue/test_point_cloud{idx}.ply"
        PlyData([vertex_element]).write(queue_ply_path)
        print("---------------------------------------------------------------------------------------------")
    save = save_point_cloud(queue_ply_path)
    new_file_path = f"./output/iteration_60000/point_cloud.ply"
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
cam_infos = readColmapCameras(cam_extrinsics=cam_extrinsics, cam_intrinsics=cam_intrinsics,
                              images_folder=images_folder)
camera_intrinsics = []
camera_extrinsics = []
for camera in cam_infos:
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

#ply_file_path = 'point_cloud_test.ply'
ply_file_path = 'points3D.ply'
final_ply_file_path = 'gaussian_point_cloud.ply'
mask_folder_path = './masks'

# 执行函数

binary_masks = process_masks(mask_folder_path)
print("binary_masks", binary_masks)
# print("pcd:", pcd)

output_folder_path = 'output_mask'
# 首先处理掩码
masks = process_masks(mask_folder_path)

filtered_pcd = project_and_filter(cam_infos, binary_masks)
