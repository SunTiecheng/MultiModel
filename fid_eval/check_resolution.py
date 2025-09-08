import os
from PIL import Image
from collections import defaultdict


def get_image_resolutions(folder_path):
    """获取文件夹中所有图片的分辨率统计"""
    resolutions = defaultdict(list)
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(supported_formats):
            try:
                with Image.open(os.path.join(folder_path, filename)) as img:
                    res = img.size  # (width, height)
                    resolutions[res].append(filename)
            except Exception as e:
                print(f"无法读取 {filename}: {str(e)}")
    return resolutions


def center_crop_image(image, target_size):
    """从中心裁剪图片到目标尺寸"""
    width, height = image.size
    target_width, target_height = target_size

    # 计算裁剪区域
    left = (width - target_width) // 2
    top = (height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    return image.crop((left, top, right, bottom))


def parse_resolution(input_str):
    """解析用户输入的分辨率"""
    # 尝试多种分隔符：x, X, *, 空格, 逗号
    separators = ['x', 'X', '*', ' ', ',']

    for sep in separators:
        if sep in input_str:
            parts = input_str.split(sep)
            if len(parts) == 2:
                try:
                    width = int(parts[0].strip())
                    height = int(parts[1].strip())
                    if width > 0 and height > 0:
                        return (width, height)
                except ValueError:
                    continue

    # 如果常见分隔符都不行，尝试提取所有数字
    numbers = []
    current_num = ""
    for char in input_str:
        if char.isdigit():
            current_num += char
        elif current_num:
            numbers.append(int(current_num))
            current_num = ""
    if current_num:
        numbers.append(int(current_num))

    if len(numbers) >= 2:
        return (numbers[0], numbers[1])

    return None


def main():
    # 输入文件夹路径
    folder_path = input("请输入图片文件夹路径: ").strip()

    # 验证路径是否存在
    if not os.path.exists(folder_path):
        print("错误: 文件夹不存在")
        return

    # 获取分辨率统计
    resolutions = get_image_resolutions(folder_path)

    if not resolutions:
        print("未找到支持的图片文件")
        return

    # 显示所有分辨率
    print("\n发现以下分辨率:")
    for i, (res, files) in enumerate(resolutions.items()):
        print(f"{i + 1}. {res[0]} x {res[1]} - {len(files)}张图片")

    # 获取用户输入的目标分辨率
    while True:
        input_res = input("\n请输入目标分辨率 (例如: 800x600, 800*600 或 800 600): ").strip()
        target_size = parse_resolution(input_res)

        if target_size:
            target_width, target_height = target_size
            print(f"设置目标分辨率: {target_width} x {target_height}")
            break
        else:
            print("错误: 无法识别分辨率格式。请使用类似 '800x600', '800*600' 或 '800 600' 的格式")

    # 创建输出文件夹
    output_folder = os.path.join(folder_path, 'edited_images')
    os.makedirs(output_folder, exist_ok=True)

    # 处理所有图片
    processed = skipped = 0
    for res, files in resolutions.items():
        for filename in files:
            file_path = os.path.join(folder_path, filename)
            try:
                with Image.open(file_path) as img:
                    # 检查原始尺寸是否足够大
                    if img.width < target_width or img.height < target_height:
                        print(f"跳过 {filename}: 原始尺寸({img.width}x{img.height})小于目标尺寸")
                        skipped += 1
                        continue

                    # 中心裁剪
                    cropped = center_crop_image(img, (target_width, target_height))

                    # 保存图片
                    output_path = os.path.join(output_folder, filename)
                    cropped.save(output_path)
                    processed += 1
                    print(f"已处理: {filename} ({img.width}x{img.height} → {target_width}x{target_height})")
            except Exception as e:
                print(f"处理 {filename} 时出错: {str(e)}")

    print(f"\n处理完成! 成功处理: {processed}张, 跳过: {skipped}张")
    print(f"裁剪后的图片已保存到: {output_folder}")


if __name__ == "__main__":
    main()