set -e

# 检查并终止已有的 tmux 会话
if tmux has-session -t progress 2>/dev/null; then
    tmux kill-session -t progress
fi

# 启动新的 tmux 会话
tmux new-session -d -s progress
tmux send-keys -t progress "watch -n 1 tail -n 10 progress.log" C-m



for work_dir in frame/*/; do
    # 获取当前文件夹名
    dir_name=$(basename "$work_dir")
    echo "Processing directory: $dir_name" | tee -a progress.log

    # 复制并重命名文件夹
    echo "Copying and renaming $dir_name to 2d-gaussian-splatting/data/input" | tee -a progress.log
    cp -r "$work_dir"/* 2d-gaussian-splatting/data/input
    
    cd 2d-gaussian-splatting

    python convert.py -s data

    python train.py -s data

    # 获取output文件夹中的文件夹名
    output_dir=$(ls output | head -n 1)


    # 运行Python脚本
    echo "Running Python script 'render.py' with output directory: $output_dir" | tee -a progress.log
    python render.py -m "output/$output_dir" -s data
    
    cd ..

    # 创建新的文件夹
    new_gen_dir="2dgs_gen/$dir_name"
    echo "Creating directory $new_gen_dir" | tee -a progress.log
    mkdir -p "$new_gen_dir"

    # 复制data文件夹到新文件夹并重命名
    echo "Copying data to $new_gen_dir/data" | tee -a progress.log
    cp -r 2d-gaussian-splatting/data "$new_gen_dir/data"

    # 复制output文件夹并重命名
    echo "Copying and renaming the output directory to $new_gen_dir/output" | tee -a progress.log
    cp -r "2d-gaussian-splatting/output/$output_dir" "$new_gen_dir/output"

    # 清除2d-gaussian-splatting文件夹中的data和output文件夹
    echo "Cleaning up data and output folders in 2d-gaussian-splatting..." | tee -a progress.log
    rm -rf 2d-gaussian-splatting/data/*
    rm -rf 2d-gaussian-splatting/output/*
    
    cp "frame/$dir_name/${dir_name}_0.jpg" rembg_process/in
    
    # 清除rembg和XMem文件夹内的图片
    rm -rf rembg_process/in/*
    rm -rf rembg_process/out/*
    rm -rf pic/JPEGImages/video1/*
    rm -rf pic/Annotations/video1/*
    rm -rf pic/video1
    
    rm -rf masks/*
    
    
    # 使用rembg或第一帧mask
    python rembg_process.py -i "$dir_name" -o ./rembg_process/out -m u2net

    # 使用XMem获取完整mask
    python ./xmem/eval.py --model ./xmem/saves/XMem-s012.pth --generic_path ./pic --dataset G --output ./pic
    
    #复制mask
    cp -r pic/video1/* masks
    cp -r pic/video1/ "$new_gen_dir/masks"
    
    # 清除rembg和XMem文件夹内的图片
    rm -rf rembg_process/in/*
    rm -rf rembg_process/out/*
    rm -rf pic/JPEGImages/video1/*
    rm -rf pic/Annotations/video1/*
    rm -rf pic/video1
    
    rm -rf masks/*
    
    
    
    
    
done


