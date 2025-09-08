#need_to_process=("human3" "motor") # 在这里替换为你的目标文件夹名称
need_to_process=("shoes2") # 在这里替换为你的目标文件夹名称

for work_dir in colmap_done/*/; do

    # 获取当前文件夹名
    dir_name=$(basename "$work_dir")

    # 检查 dir_name 是否在 need_to_process 列表中
    if [[ ! " ${need_to_process[@]} " =~ " ${dir_name} " ]]; then
        echo "Skipping directory: $dir_name (not in need_to_process)"
        continue  # 如果不在列表中，跳过当前目录，进入下一个
    fi

    echo "Processing directory: $dir_name"

    # 清除2d-gaussian-splatting文件夹中的data和output文件夹
    echo "Cleaning up data and output folders in 2d-gaussian-splatting..."
    rm -rf 2d-gaussian-splatting/data
    rm -rf 2d-gaussian-splatting/output/*
    
    # 获取当前文件夹名
    #dir_name=$(basename "$work_dir")
    #echo "Processing directory: $dir_name"

    # 复制并重命名文件夹
    echo "Copying and renaming $dir_name to 2d-gaussian-splatting/data/input"

    cp -r "$work_dir"/* 2d-gaussian-splatting/
    
    cd 2d-gaussian-splatting

    python train.py -s data

    # 获取output文件夹中的文件夹名
    output_dir=$(ls output | head -n 1)


    # 运行Python脚本
    echo "Running Python script 'render.py' with output directory: $output_dir"
    python render.py -m "output/$output_dir" -s data
    
    cd ..

    # 创建新的文件夹
    new_gen_dir="2dgs_gen/$dir_name"
    echo "Creating directory $new_gen_dir"
    mkdir -p "$new_gen_dir"

    # 复制data文件夹到新文件夹并重命名
    echo "Copying data to $new_gen_dir/data"
    cp -r 2d-gaussian-splatting/data "$new_gen_dir/data"

    # 复制output文件夹并重命名
    echo "Copying and renaming the output directory to $new_gen_dir/output"
    cp -r "2d-gaussian-splatting/output/$output_dir" "$new_gen_dir/output"

    # 清除2d-gaussian-splatting文件夹中的data和output文件夹
    echo "Cleaning up data and output folders in 2d-gaussian-splatting..."
    rm -rf 2d-gaussian-splatting/data
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


