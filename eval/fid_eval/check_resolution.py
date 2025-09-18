import os
from PIL import Image
from collections import defaultdict


def get_image_resolutions(folder_path):
    resolutions = defaultdict(list)
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(supported_formats):
            try:
                with Image.open(os.path.join(folder_path, filename)) as img:
                    res = img.size  # (width, height)
                    resolutions[res].append(filename)
            except Exception as e:
                print(f"Unable load {filename}: {str(e)}")
    return resolutions


def center_crop_image(image, target_size):
    width, height = image.size
    target_width, target_height = target_size

    left = (width - target_width) // 2
    top = (height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    return image.crop((left, top, right, bottom))


def parse_resolution(input_str):
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
    folder_path = input("Input path: ").strip()

    if not os.path.exists(folder_path):
        print("Error: No such folder")
        return

    resolutions = get_image_resolutions(folder_path)

    if not resolutions:
        print("Pictures not find")
        return

    print("\nResolution:")
    for i, (res, files) in enumerate(resolutions.items()):
        print(f"{i + 1}. {res[0]} x {res[1]} - {len(files)} pictures")

    while True:
        input_res = input("\nPlease set the target resolution(e.g. 800x600, 800*600 或 800 600): ").strip()
        target_size = parse_resolution(input_res)

        if target_size:
            target_width, target_height = target_size
            print(f"Target resolution: {target_width} x {target_height}")
            break
        else:
            print("Error: un-recognized resolution!")

    output_folder = os.path.join(folder_path, 'edited_images')
    os.makedirs(output_folder, exist_ok=True)

    processed = skipped = 0
    for res, files in resolutions.items():
        for filename in files:
            file_path = os.path.join(folder_path, filename)
            try:
                with Image.open(file_path) as img:
                    if img.width < target_width or img.height < target_height:
                        print(f"Skip {filename}: Original size({img.width}x{img.height})is smaller than target size")
                        skipped += 1
                        continue

                    cropped = center_crop_image(img, (target_width, target_height))

                    output_path = os.path.join(output_folder, filename)
                    cropped.save(output_path)
                    processed += 1
                    print(f"Processed: {filename} ({img.width}x{img.height} → {target_width}x{target_height})")
            except Exception as e:
                print(f"{str(e)} Error when processing {filename} ")

    print(f"\nProcess Done! Processed in successfully {processed} pictures, skip: {skipped} pictures")
    print(f"The pictures have been saved in: {output_folder}")


if __name__ == "__main__":
    main()