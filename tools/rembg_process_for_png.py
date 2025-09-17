import os
import argparse
from PIL import Image
from rembg import new_session, remove
import shutil


def copy_image_to_rembg_process_in(source_folder):
    # 构建源文件名和目标文件夹路径
    source_file = os.path.join('./frame', source_folder, f"{source_folder}_000.png")
    destination_folder = './rembg_process/in'

    # 确保目标文件夹存在
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # 复制文件到目标文件夹
    if os.path.exists(source_file):
        shutil.copy(source_file, destination_folder)
        print(f"Copied {source_file} to {destination_folder}")
    else:
        print(f"File {source_file} does not exist.")


def rembg_process(output_folder_path, model):
    input_folder_path = './rembg_process/in'
    # 获取文件夹中所有的图片
    images = [f for f in os.listdir(input_folder_path) if f.endswith('.png')]
    # 按照你的命名规则对图片进行排序
    images.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))

    for i, img_name in enumerate(images, start=1):
        image_path = os.path.join(input_folder_path, img_name)
        image = Image.open(image_path)
        extracted_count = 0
        image_name, _ = os.path.splitext(img_name)
        # print("image name: ", image_name)

        output = remove(image, session=new_session(model), only_mask=True, post_process_mask=True)
        new_name = f"{image_name}.png"
        output.save(os.path.join(output_folder_path, new_name))
        extracted_count += 1


def clear_and_copy_files(output_folder, input_folder):
    annotations_folder = './pic/Annotations/video1'
    jpegimages_folder = './pic/JPEGImages/video1'
    frame_input_folder = os.path.join('./frame', input_folder)

    # 确保目标文件夹存在
    if not os.path.exists(annotations_folder):
        os.makedirs(annotations_folder)

    if not os.path.exists(jpegimages_folder):
        os.makedirs(jpegimages_folder)

    # 清空目标文件夹
    for folder in [annotations_folder, jpegimages_folder]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

    # 复制文件到 ./pic/Annotations/video1 文件夹
    for item in os.listdir(output_folder):
        s = os.path.join(output_folder, item)
        d = os.path.join(annotations_folder, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    # 复制文件到 ./pic/JPEGImages/video1 文件夹
    for item in os.listdir(frame_input_folder):
        s = os.path.join(frame_input_folder, item)
        d = os.path.join(jpegimages_folder, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)



# if __name__ == '__main__':
#     input_folder_path = './test_rembg/in/'
#     output_folder_path = './test_rembg/out/'
#     model = 'u2net'
#     rembg_process(input_folder_path, output_folder_path, model)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="rembg process.")
    parser.add_argument('-i', '--input_folder', type=str, help="Path to the input video file.")
    parser.add_argument('-o', '--output_folder', type=str, default= './rembg_process/out', help="Folder to save the extracted frames.")
    parser.add_argument('-m', '--model', type=str, default= 'u2net', help="Target number of frames to extract.")

    args = parser.parse_args()

    copy_image_to_rembg_process_in(args.input_folder)
    rembg_process(args.output_folder, args.model)
    clear_and_copy_files(args.output_folder, args.input_folder)
