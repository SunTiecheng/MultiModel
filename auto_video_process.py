import os
import subprocess
from tqdm import tqdm


def process_videos():
    video_dir = os.path.join('.', 'video')
    output_dir = os.path.join('.', 'frame')

    os.makedirs(output_dir, exist_ok=True)

    video_files = [f for f in os.listdir(video_dir) if f.lower().endswith('.mp4')]

    if not video_files:
        print("MP4 Video File Not Found")
        return

    with tqdm(total=len(video_files), desc="Processing:", unit="video") as pbar:
        for video_file in video_files:
            input_path = os.path.join(video_dir, video_file)

            command = [
                'python',
                'video_process.py',
                '-i', input_path,
                '-o', output_dir,
                '-t', '150'
            ]

            try:
                subprocess.run(command, check=True)
                pbar.set_postfix_str(f"Current：{video_file}", refresh=False)

            except subprocess.CalledProcessError as e:
                pbar.write(f"× Failed：{video_file} (Error Code: {e.returncode})")
            except Exception as e:
                pbar.write(f"× Error：{video_file} ({str(e)})")
            finally:
                pbar.update(1)


if __name__ == "__main__":
    process_videos()