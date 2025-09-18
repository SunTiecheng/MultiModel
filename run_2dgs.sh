set -e

if tmux has-session -t progress 2>/dev/null; then
    tmux kill-session -t progress
fi

tmux new-session -d -s progress
tmux send-keys -t progress "watch -n 1 tail -n 10 progress.log" C-m



for work_dir in frame/*/; do
    dir_name=$(basename "$work_dir")
    echo "Processing directory: $dir_name" | tee -a progress.log

    echo "Copying and renaming $dir_name to 2d-gaussian-splatting/data/input" | tee -a progress.log
    cp -r "$work_dir"/* 2d-gaussian-splatting/data/input
    
    cd 2d-gaussian-splatting

    python convert.py -s data

    python train.py -s data

    output_dir=$(ls output | head -n 1)


    echo "Running Python script 'render.py' with output directory: $output_dir" | tee -a progress.log
    python render.py -m "output/$output_dir" -s data
    
    cd ..

    new_gen_dir="2dgs_gen/$dir_name"
    echo "Creating directory $new_gen_dir" | tee -a progress.log
    mkdir -p "$new_gen_dir"

    echo "Copying data to $new_gen_dir/data" | tee -a progress.log
    cp -r 2d-gaussian-splatting/data "$new_gen_dir/data"

    echo "Copying and renaming the output directory to $new_gen_dir/output" | tee -a progress.log
    cp -r "2d-gaussian-splatting/output/$output_dir" "$new_gen_dir/output"

    echo "Cleaning up data and output folders in 2d-gaussian-splatting..." | tee -a progress.log
    rm -rf 2d-gaussian-splatting/data/*
    rm -rf 2d-gaussian-splatting/output/*
    
    cp "frame/$dir_name/${dir_name}_0.jpg" rembg_process/in
    
    rm -rf rembg_process/in/*
    rm -rf rembg_process/out/*
    rm -rf pic/JPEGImages/video1/*
    rm -rf pic/Annotations/video1/*
    rm -rf pic/video1
    
    rm -rf masks/*
    
    
    python rembg_process.py -i "$dir_name" -o ./rembg_process/out -m u2net

    python ./xmem/eval.py --model ./xmem/saves/XMem-s012.pth --generic_path ./pic --dataset G --output ./pic
    
    cp -r pic/video1/* masks
    cp -r pic/video1/ "$new_gen_dir/masks"
    
    rm -rf rembg_process/in/*
    rm -rf rembg_process/out/*
    rm -rf pic/JPEGImages/video1/*
    rm -rf pic/Annotations/video1/*
    rm -rf pic/video1
    
    rm -rf masks/*
done


