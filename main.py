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


def load_point_cloud(ply_file_path):
    pcd = PlyData.read(ply_file_path)
    new_file_path = 'test_point_cloud.ply'
    pcd.write(new_file_path)
    return pcd

def save_point_cloud(ply_file_path):
    save = PlyData.read(ply_file_path)
    new_file_path = './output/point_cloud/iteration_60000/point_cloud.ply'
    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
    save.write(new_file_path)
    return save

def process_masks(mask_folder_path):
    masks_dict = {}
    for mask_filename in sorted(os.listdir(mask_folder_path)):
        mask_path = os.path.join(mask_folder_path, mask_filename)
        if os.path.isfile(mask_path):
            image = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                print("Failed to load the image from", mask_folder_path)
                return None
            _, binary_mask = cv2.threshold(image, 30, 1, cv2.THRESH_BINARY)
            if np.any(binary_mask):
                mask_name_without_ext = os.path.splitext(mask_filename)[0]
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


def project_and_filter(cam_infos, binary_masks):
    mask_names = get_mask_names(mask_folder_path)
    print("---------------------------------------------------------------------------------------------")
    for idx, camera in enumerate(cam_infos):
        camera = cam_infos[idx]
        if camera.image_name not in mask_names:
            continue
        pcd = load_point_cloud(ply_file_path)
        if idx > 1 :
            pcd = load_point_cloud(queue_ply_path)
        vertex = pcd['vertex']
        properties = vertex.data.dtype.names
        dtype_desc = [(prop, vertex[prop].dtype) for prop in properties]
        test_points = np.array([vertex[prop] for prop in properties]).T

        print("camera", camera)
        no = camera.image_name
        num_cameras = len(cam_infos)
        print("There are", num_cameras, "items in cam_infos.")
        print("In", idx, "times of iterations")
        filtered_points = np.array([], dtype=dtype_desc)

        mask = binary_masks[no]
        print("The number of using mask：", no)
        CAMERA_INTRINSICS = np.array([[camera.FocalX, 0, camera.width / 2],
                                      [0, camera.FocalY, camera.height / 2],
                                      [0, 0, 1]])
        C2W = getWorld2View(camera.R, camera.T)

        points = np.stack((np.asarray(pcd.elements[0]["x"]),
                           np.asarray(pcd.elements[0]["y"]),
                           np.asarray(pcd.elements[0]["z"])), axis=1)
        points_homogeneous = np.hstack((points, np.ones((points.shape[0], 1))))
        points_camera = (C2W @ points_homogeneous.T).T[:, :3]
        print(f"image_name: {camera.image_name}")

        pixels_homogeneous = CAMERA_INTRINSICS @ points_camera.T
        pixels = np.vstack((pixels_homogeneous[0, :] / pixels_homogeneous[2, :],
                            pixels_homogeneous[1, :] / pixels_homogeneous[2, :])).T

        within_projection = ((pixels[:, 0] >= 0) & (pixels[:, 0] < mask.shape[1]) &
                             (pixels[:, 1] >= 0) & (pixels[:, 1] < mask.shape[0]))

        image_points_within_projection = pixels[within_projection].astype(np.int64)
        mask_values = np.ones(points_camera.shape[0], dtype=bool)
        mask_values[within_projection] = mask[image_points_within_projection[:, 1], image_points_within_projection[:,
                                                                                    0]] == 1
        filtered_points = test_points[mask_values]
        structured_array = np.array([tuple(row) for row in filtered_points], dtype=dtype_desc)

        vertex_element = PlyElement.describe(structured_array, 'vertex')
        queue_ply_path = f"./queue/test_point_cloud{idx}.ply"
        PlyData([vertex_element]).write(queue_ply_path)
        print("---------------------------------------------------------------------------------------------")

    save = save_point_cloud(queue_ply_path)
    new_file_path = f"./output/iteration_60000/point_cloud.ply"
    print(f"point cloud is saved in {new_file_path}")



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

    camera_extrinsics = [
        {'R': camera.R, 't': camera.T},
    ]

print("camera_intrinsics", camera_intrinsics)
print("camera_extrinsics", camera_extrinsics)

ply_file_path = 'point_cloud.ply'
final_ply_file_path = 'gaussian_point_cloud.ply'
mask_folder_path = './masks'

binary_masks = process_masks(mask_folder_path)
print("binary_masks", binary_masks)
# print("pcd:", pcd)

output_folder_path = 'output_mask'

masks = process_masks(mask_folder_path)

filtered_pcd = project_and_filter(cam_infos, binary_masks)