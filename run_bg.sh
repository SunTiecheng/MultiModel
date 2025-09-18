set -e

if tmux has-session -t progress 2>/dev/null; then
    tmux kill-session -t progress
fi

tmux new-session -d -s progress
tmux send-keys -t progress "watch -n 1 tail -n 10 progress.log" C-m



for work_dir in 2dgs_gen/*/; do
    dir_name=$(basename "$work_dir")
    echo "Processing directory: $dir_name" | tee -a progress.log


    python file.py copy -n ${dir_name}
    
    python dilate.py -s 50
    
    python run.py -i ${dir_name}.ply
    
    python file.py delete
    
done


