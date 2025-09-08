import cv2 as cv
import numpy as np
import os
import argparse

# 定义输入和输出文件夹路径
input_folder = 'masks'
output_folder = 'dilate_mask'


def dilate_mask(input_folder, output_folder, size):
    # 创建输出文件夹，如果它不存在
    os.makedirs(output_folder, exist_ok=True)

    # 获取输入文件夹中的所有文件名
    file_names = os.listdir(input_folder)

    # 定义膨胀内核
    k = np.ones((size, size), np.uint8)

    # 遍历所有文件并处理
    for file_name in file_names:
        # 构建完整的文件路径
        input_path = os.path.join(input_folder, file_name)
        output_path = os.path.join(output_folder, file_name)

        # 读取图像
        image = cv.imread(input_path)

        # 如果图像读取成功，进行膨胀操作
        if image is not None:
            dilated_image = cv.dilate(image, k, iterations=2)

            # 保存处理后的图像到输出文件夹
            cv.imwrite(output_path, dilated_image)
        else:
            print(f"无法读取文件 {input_path}")

    print("所有mask已膨胀并保存到dilate_mask文件夹。")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="rgb process.")
    parser.add_argument('-s', '--size', type=int, default= 10, help="Size of dilate kernel.")
    args = parser.parse_args()

    dilate_mask(input_folder, output_folder, args.size)
