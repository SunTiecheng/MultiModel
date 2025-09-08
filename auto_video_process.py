import os
import subprocess
from tqdm import tqdm


def process_videos():
    # 定义路径
    video_dir = os.path.join('.', 'video')
    output_dir = os.path.join('.', 'frame')

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有.mp4视频文件
    video_files = [f for f in os.listdir(video_dir) if f.lower().endswith('.mp4')]

    if not video_files:
        print("未找到MP4视频文件")
        return

    # 初始化总进度条
    with tqdm(total=len(video_files), desc="处理进度", unit="video") as pbar:
        # 处理每个视频文件py
        for video_file in video_files:
            input_path = os.path.join(video_dir, video_file)

            # 构建命令
            command = [
                'python',
                'video_process.py',
                '-i', input_path,
                '-o', output_dir,
                '-t', '150'
            ]

            try:
                # 执行命令（不再捕获输出）
                subprocess.run(command, check=True)
                pbar.set_postfix_str(f"当前：{video_file}", refresh=False)

            except subprocess.CalledProcessError as e:
                pbar.write(f"× 失败：{video_file} (错误码 {e.returncode})")
            except Exception as e:
                pbar.write(f"× 异常：{video_file} ({str(e)})")
            finally:
                pbar.update(1)  # 确保无论如何都更新进度


if __name__ == "__main__":
    process_videos()