import numpy as np
import os
from PIL import Image

def process_masks(mask_folder_path, target_color=(128, 0, 0), background_color=(0, 0, 0)):
    binary_masks = []
    for file_name in sorted(os.listdir(mask_folder_path)):
        if file_name.endswith('.png') or file_name.endswith('.jpg'):
            file_path = os.path.join(mask_folder_path, file_name)
            mask_img = np.array(Image.open(file_path))  # 默认读取模式即RGB
            binary_mask = np.all(mask_img == background_color, axis=-1).astype(np.uint8)  # 背景设置为0
            binary_mask[np.all(mask_img == target_color, axis=-1)] = 1  # 目标设置为1
            binary_masks.append(binary_mask)
    return binary_masks

mask_folder_path = './masks/'
print = process_masks(mask_folder_path)
print("text", print)