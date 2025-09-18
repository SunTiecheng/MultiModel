import os
import shutil
import argparse


def copy_files_and_folders():
    current_directory = os.getcwd()
    for item in file_to_copy:
        if os.path.exists(item):
            if os.path.isfile(item):
                shutil.copy2(item, current_directory)
            elif os.path.isdir(item):
                destination = os.path.join(current_directory, os.path.basename(item))
                shutil.copytree(item, destination)
    if os.path.exists(frame_folder):
       destination = "./images"
       shutil.copytree(frame_folder, destination)
    if os.path.exists(mask_folder):
       destination = "./masks"
       shutil.copytree(mask_folder, destination)
    if os.path.exists(ply_files_folder):
       destination_ply = os.path.join('./mesh_ply', f"{new_ply_name}.ply")
       shutil.copy2(ply_files_folder, destination_ply)

def delete_files_and_folders():
    files_to_delete = [
        'cameras.bin',
        'images.bin',
    ]
    folders_to_delete = ['./images', './masks', './dilate_mask']
    folders_to_clear = []

    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)

    for folder in folders_to_clear:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')

    for folder in folders_to_delete:
        if os.path.exists(folder):
            shutil.rmtree(folder)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Copy or delete specified files and folders.")
    parser.add_argument('action', choices=['copy', 'delete'],
                        help="Action to perform: 'copy' to copy files/folders, 'delete' to delete files/folders.")
    parser.add_argument('-n', '--name', type=str, help="Path to the input ply file.")
    args = parser.parse_args()
    


    if args.action == 'copy':
        cameras_file_path = os.path.join('./2dgs_gen', args.name, 'data/sparse/0/cameras.bin')
        images_file_path = os.path.join('./2dgs_gen', args.name, 'data/sparse/0/images.bin')
        frame_folder = os.path.join('./frame', args.name)
        mask_folder = os.path.join('./2dgs_gen', args.name, 'masks')
        ply_files_folder = os.path.join('./2dgs_gen', args.name, 'output/train/ours_30000/fuse_post.ply')
        file_to_copy = [cameras_file_path, images_file_path]
        new_ply_name = args.name
        copy_files_and_folders()
        print(new_ply_name)
    elif args.action == 'delete':
        delete_files_and_folders()
