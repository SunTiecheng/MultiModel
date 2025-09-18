import cv2
import numpy as np
import os
from pathlib import Path
import argparse  # 添加argparse库用于命令行参数解析


def process_images_with_masks(images_folder, masks_folder, output_folder=None):
    """
    使用mask处理图片，只保留mask中的物体部分

    参数:
    images_folder: 原始图片文件夹路径
    masks_folder: mask文件夹路径
    output_folder: 输出文件夹路径，如果为None则保存到'processed_images'文件夹
    """

    # 设置输出文件夹
    if output_folder is None:
        output_folder = "processed_images"

    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)

    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}

    # 获取images文件夹中的所有图片文件
    images_path = Path(images_folder)
    masks_path = Path(masks_folder)

    if not images_path.exists():
        print(f"错误: 图片文件夹 '{images_folder}' 不存在")
        return

    if not masks_path.exists():
        print(f"错误: mask文件夹 '{masks_folder}' 不存在")
        return

    # 处理每个图片文件
    processed_count = 0

    for image_file in images_path.iterdir():
        if image_file.suffix.lower() in image_extensions:
            # 构建对应的mask文件路径
            mask_file = masks_path / image_file.name

            # 如果mask文件不存在，尝试其他可能的扩展名
            if not mask_file.exists():
                # 尝试不同的扩展名
                base_name = image_file.stem
                mask_found = False

                for ext in image_extensions:
                    potential_mask = masks_path / f"{base_name}{ext}"
                    if potential_mask.exists():
                        mask_file = potential_mask
                        mask_found = True
                        break

                if not mask_found:
                    print(f"警告: 找不到对应的mask文件 '{image_file.name}'")
                    continue

            try:
                # 读取原始图片
                image = cv2.imread(str(image_file))
                if image is None:
                    print(f"错误: 无法读取图片 '{image_file.name}'")
                    continue

                # 读取mask图片
                mask = cv2.imread(str(mask_file), cv2.IMREAD_GRAYSCALE)
                if mask is None:
                    print(f"错误: 无法读取mask '{mask_file.name}'")
                    continue

                # 确保mask和图片尺寸一致
                if mask.shape[:2] != image.shape[:2]:
                    print(f"调整mask尺寸以匹配图片: {image_file.name}")
                    mask = cv2.resize(mask, (image.shape[1], image.shape[0]))

                # 将mask转换为三通道
                mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

                # 归一化mask到0-1范围
                mask_normalized = mask_3channel.astype(np.float32) / 255.0

                # 应用mask到图片
                # 方法1: 直接乘法（背景变为黑色）
                masked_image = image.astype(np.float32) * mask_normalized

                # 转换回uint8格式
                masked_image = masked_image.astype(np.uint8)

                # 保存处理后的图片
                output_path = Path(output_folder) / image_file.name
                cv2.imwrite(str(output_path), masked_image)

                processed_count += 1
                print(f"已处理: {image_file.name}")

            except Exception as e:
                print(f"处理 '{image_file.name}' 时出错: {str(e)}")
                continue

    print(f"\n处理完成! 总共处理了 {processed_count} 张图片")
    print(f"结果保存在: {output_folder}")


def process_with_transparent_background(images_folder, masks_folder, output_folder="processed_images_transparent"):
    """
    处理图片并生成透明背景的PNG文件
    """
    os.makedirs(output_folder, exist_ok=True)

    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    images_path = Path(images_folder)
    masks_path = Path(masks_folder)

    processed_count = 0

    for image_file in images_path.iterdir():
        if image_file.suffix.lower() in image_extensions:
            # 寻找对应的mask文件
            mask_file = masks_path / image_file.name

            if not mask_file.exists():
                base_name = image_file.stem
                mask_found = False
                for ext in image_extensions:
                    potential_mask = masks_path / f"{base_name}{ext}"
                    if potential_mask.exists():
                        mask_file = potential_mask
                        mask_found = True
                        break

                if not mask_found:
                    continue

            try:
                image = cv2.imread(str(image_file))
                mask = cv2.imread(str(mask_file), cv2.IMREAD_GRAYSCALE)

                if image is None or mask is None:
                    continue

                if mask.shape[:2] != image.shape[:2]:
                    mask = cv2.resize(mask, (image.shape[1], image.shape[0]))

                # 创建RGBA图片
                rgba_image = np.zeros((image.shape[0], image.shape[1], 4), dtype=np.uint8)
                rgba_image[:, :, :3] = image  # RGB通道
                rgba_image[:, :, 3] = mask  # Alpha通道（透明度）

                # 保存为PNG格式以支持透明度
                output_filename = Path(image_file.stem + '.png')
                output_path = Path(output_folder) / output_filename
                cv2.imwrite(str(output_path), rgba_image)

                processed_count += 1
                print(f"已处理（透明背景）: {image_file.name}")

            except Exception as e:
                print(f"处理 '{image_file.name}' 时出错: {str(e)}")

    print(f"\n透明背景处理完成! 总共处理了 {processed_count} 张图片")


# 使用命令行参数
if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='使用mask处理图片')
    parser.add_argument('-i', '--images', required=True, help='原始图片文件夹路径')
    parser.add_argument('-m', '--masks', required=True, help='mask文件夹路径')
    parser.add_argument('-o', '--output', default='processed_images',
                        help='输出文件夹路径（黑色背景处理），默认: processed_images')
    parser.add_argument('-t', '--transparent_output',
                        help='透明背景处理的输出文件夹路径（可选），指定后将生成透明背景图片')

    # 解析命令行参数
    args = parser.parse_args()

    print("开始处理图片（黑色背景）...")
    process_images_with_masks(args.images, args.masks, args.output)

    # 如果指定了透明背景输出目录，则执行透明背景处理
    if args.transparent_output:
        print("\n开始处理图片（透明背景）...")
        process_with_transparent_background(args.images, args.masks, args.transparent_output)