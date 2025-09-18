set -e

# 检查并终止已有的 tmux 会话
if tmux has-session -t progress 2>/dev/null; then
    tmux kill-session -t progress
fi

# 启动新的 tmux 会话
tmux new-session -d -s progress
tmux send-keys -t progress "watch -n 1 tail -n 10 progress.log" C-m



for work_dir in 2dgs_gen/*/; do
    # 获取当前文件夹名
    dir_name=$(basename "$work_dir")
    echo "Processing directory: $dir_name" | tee -a progress.log


    python file.py copy -n ${dir_name}
    
    python dilate.py -s 50
    
    python run.py -i ${dir_name}.ply
    
    python file.py delete
    

    
    
    
    
done


