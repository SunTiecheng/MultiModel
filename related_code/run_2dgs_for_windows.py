import os
import shutil
import glob
import subprocess
from datetime import datetime

def log_message(message, log_file="progress.log"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(log_file, "a") as f:
        f.write(full_message + "\n")

def clear_directory(dir_path):
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            log_message(f"Failed to delete {file_path}. Reason: {e}")

def main():
    need_to_process = ["shoes3"]
    base_dir = os.getcwd()

    os.makedirs("2dgs_gen", exist_ok=True)
    os.makedirs("rembg_process/in", exist_ok=True)
    os.makedirs("masks", exist_ok=True)

    for work_dir in glob.glob("frame/*/"):
        dir_name = os.path.basename(work_dir.rstrip('/'))
        
        # if dir_name not in need_to_process:
        #     log_message(f"Skipping directory: {dir_name} (not in need_to_process)")
        #     continue

        log_message(f"Processing directory: {dir_name}")

        try:
            target_dir = "2d-gaussian-splatting/data/input"
            log_message(f"Copying and renaming {dir_name} to {target_dir}")
            
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            os.makedirs(target_dir, exist_ok=True)
            
            for item in glob.glob(f"{work_dir}/*"):
                if os.path.isdir(item):
                    shutil.copytree(item, os.path.join(target_dir, os.path.basename(item)))
                else:
                    shutil.copy2(item, target_dir)

            gs_dir = "2d-gaussian-splatting"
            subprocess.run(["python", "convert.py", "-s", "data"], cwd=gs_dir, check=True)
            subprocess.run(["python", "train.py", "-s", "data"], cwd=gs_dir, check=True)

            output_path = os.path.join(gs_dir, "output")
            output_dirs = [d for d in os.listdir(output_path) if os.path.isdir(os.path.join(output_path, d))]
            if not output_dirs:
                raise Exception("No output directory found")
            output_dir = output_dirs[0]

            log_message(f"Running Python script 'render.py' with output directory: {output_dir}")
            subprocess.run(["python", "render.py", "-m", f"output/{output_dir}", "-s", "data"], cwd=gs_dir, check=True)

            new_gen_dir = f"2dgs_gen/{dir_name}"
            log_message(f"Creating directory {new_gen_dir}")
            os.makedirs(new_gen_dir, exist_ok=True)

            shutil.copytree(os.path.join(gs_dir, "data"), os.path.join(new_gen_dir, "data"), dirs_exist_ok=True)
            shutil.copytree(os.path.join(gs_dir, "output", output_dir), os.path.join(new_gen_dir, "output"), dirs_exist_ok=True)

            log_message("Cleaning up data and output folders in 2d-gaussian-splatting...")
            clear_directory(os.path.join(gs_dir, "data"))
            clear_directory(os.path.join(gs_dir, "output"))

            first_frame = f"frame/{dir_name}/{dir_name}_0.jpg"
            rembg_in = "rembg_process/in"
            shutil.copy(first_frame, rembg_in)

            clear_directory("rembg_process/out")
            clear_directory("pic/JPEGImages/video1")
            clear_directory("pic/Annotations/video1")
            if os.path.exists("pic/video1"):
                shutil.rmtree("pic/video1")
            clear_directory("masks")

            subprocess.run(["python", "rembg_process.py", "-i", dir_name, "-o", "./rembg_process/out", "-m", "u2net"], check=True)
            
            subprocess.run(["python", "./xmem/eval_test.py", "--model", "./xmem/saves/XMem-s012.pth",
                          "--generic_path", "./pic", "--dataset", "G", "--output", "./pic"], check=True)

            if os.path.exists("pic/video1"):
                shutil.copytree("pic/video1", "masks", dirs_exist_ok=True)
                shutil.copytree("pic/video1", os.path.join(new_gen_dir, "masks"), dirs_exist_ok=True)

            clear_directory("rembg_process/in")
            clear_directory("rembg_process/out")
            clear_directory("pic/JPEGImages/video1")
            clear_directory("pic/Annotations/video1")
            if os.path.exists("pic/video1"):
                shutil.rmtree("pic/video1")
            clear_directory("masks")

        except Exception as e:
            log_message(f"Error processing {dir_name}: {str(e)}")
            continue

if __name__ == "__main__":
    main()