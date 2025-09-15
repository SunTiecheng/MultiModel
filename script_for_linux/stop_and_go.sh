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
    
    cp "frame/$dir_name/${dir_name}_0.jpg" rembg_process/in
    
    # 使用rembg或第一帧mask
    python rembg_process.py -i "$dir_name" -o ./rembg_process/out -m u2net
    


    # 使用XMem获取完整mask
    python ./xmem/eval.py --model ./xmem/saves/XMem-s012.pth --generic_path ./pic --dataset G --output ./pic
    
    #复制mask
    cp -r pic/video1/* masks
    
    # 清除rembg和XMem文件夹内的图片
    rm -rf rembg_process/in/*
    rm -rf rembg_process/out/*
    rm -rf pic/JPEGImages/video1/*
    rm -rf pic/Annotations/video1/*
    rm -rf pic/video1
    
    
    
    
    
done
