import os
import shutil


def copy_output_folder():
    source_folder = './sugar/data/output'
    destination_folder = './sugar/output'

    # 确保目标文件夹存在
    if not os.path.exists(destination_folder):
        shutil.copytree(source_folder, destination_folder)
    else:
        print(f"Folder {destination_folder} already exists.")


def copy_and_rename_cameras_json():
    source_file = './sugar/data/output/cameras.json'
    destination_file = './sugar/data/outputcameras.json'

    # 复制并重命名文件
    if os.path.exists(source_file):
        shutil.copy(source_file, destination_file)
    else:
        print(f"File {source_file} does not exist.")


if __name__ == '__main__':
    copy_output_folder()
    copy_and_rename_cameras_json()
