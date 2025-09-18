import os
import cv2
import math
import argparse
import shutil


def extract_images(video_path, output_folder, target_frame_count=150):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_folder, video_name)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= target_frame_count:
        frame_interval = 1
        target_frame_count = total_frames
    else:
        frame_interval = math.ceil(total_frames / target_frame_count)

    count = 0
    extracted_count = 0

    while cap.isOpened() and extracted_count < target_frame_count:
        ret, frame = cap.read()
        if ret:
            if count % frame_interval == 0:
                image_name = os.path.join(output_path, f"{video_name}_{extracted_count}.jpg")
                cv2.imwrite(image_name, frame)
                extracted_count += 1
            count += 1
        else:
            break

    cap.release()


def copy_to_input_folder(output_folder):
    destination_folder = './sugar/data/input'

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    for item in os.listdir(output_folder):
        s = os.path.join(output_folder, item)
        d = os.path.join(destination_folder, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract frames from a video.")
    parser.add_argument('-i', '--video_path', type=str, default= './video/flower2.mp4', help="Path to the input video file.")
    parser.add_argument('-o', '--output_folder', type=str, default= './frame', help="Folder to save the extracted frames.")
    parser.add_argument('-t', '--target_frame_count', type=int, default=150, help="Target number of frames to extract.")

    args = parser.parse_args()

    extract_images(args.video_path, args.output_folder, args.target_frame_count)

    copy_to_input_folder(args.output_folder)

# if __name__ == '__main__':
#     video_path = './video/flower2.mp4'
#     output_folder = './frame'
#     extract_images(video_path, output_folder)
