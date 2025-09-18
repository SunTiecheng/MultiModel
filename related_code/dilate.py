import cv2 as cv
import numpy as np
import os
import argparse

input_folder = 'masks'
output_folder = 'dilate_mask'


def dilate_mask(input_folder, output_folder, size):
    os.makedirs(output_folder, exist_ok=True)

    file_names = os.listdir(input_folder)

    k = np.ones((size, size), np.uint8)

    for file_name in file_names:
        input_path = os.path.join(input_folder, file_name)
        output_path = os.path.join(output_folder, file_name)

        image = cv.imread(input_path)

        if image is not None:
            dilated_image = cv.dilate(image, k, iterations=2)

            cv.imwrite(output_path, dilated_image)
        else:
            print(f"Unable load file in path: {input_path}")

    print("All masks have been dilated.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="rgb process.")
    parser.add_argument('-s', '--size', type=int, default= 10, help="Size of dilate kernel.")
    args = parser.parse_args()

    dilate_mask(input_folder, output_folder, args.size)
