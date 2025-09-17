import os
from PIL import Image

def process_images_in_folder(input_folder, mask_folder, output_folder):
    # 确保输出文件夹存在，如果不存在则创建
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 获取输入文件夹中的所有图片文件
    input_images = sorted(os.listdir(input_folder))
    mask_images = sorted(os.listdir(mask_folder))

    for input_image, mask_image in zip(input_images, mask_images):
        input_image_path = os.path.join(input_folder, input_image)
        mask_image_path = os.path.join(mask_folder, mask_image)
        output_image_path = os.path.join(output_folder, input_image)

        # 检查文件扩展名是否为图片格式
        if input_image.endswith(('png', 'jpg', 'jpeg')) and mask_image.endswith(('png', 'jpg', 'jpeg')):
            process_image(input_image_path, mask_image_path, output_image_path)
            print(f"Processed: {input_image}")

def process_image(image_path, mask_path, output_path):
    # 打开原始图像和mask图像
    image = Image.open(image_path).convert("RGBA")
    mask = Image.open(mask_path).convert("L")  # 只需要mask的灰度信息

    # 创建一个与原图像尺寸相同的空白RGBA图像，背景设置为透明
    new_image = Image.new("RGBA", image.size, (0, 0, 0, 0))

    # 将mask的白色区域（255）设置为0，黑色区域（0）设置为1
    mask = mask.point(lambda p: 255 if p == 0 else 0)

    # 遍历mask，将物体区域设置为透明
    for y in range(mask.size[1]):
        for x in range(mask.size[0]):
            if mask.getpixel((x, y)) == 0:  # mask的物体区域
                new_image.putpixel((x, y), image.getpixel((x, y)))
            else:
                # 背景区域保持透明
                new_image.putpixel((x, y), (0, 0, 0, 0))

    # 保存处理后的图像
    new_image.save(output_path, "PNG")

# 文件夹路径
input_folder = "./frame_exchange/images"  # 原始图片文件夹
mask_folder = "./frame_exchange/masks"  # mask图片文件夹
output_folder = "./frame_exchange/save1"  # 输出图片文件夹

# 批量处理整个文件夹中的图片
process_images_in_folder(input_folder, mask_folder, output_folder)
