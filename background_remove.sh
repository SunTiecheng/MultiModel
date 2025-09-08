#!/bin/bash

# 定义需要处理的文件夹名称列表
#need_to_process=("truck3" "volvo") # 在这里替换为你的目标文件夹名称
need_to_process=("flower_exp") # 在这里替换为你的目标文件夹名称

# 遍历每个文件夹
for work_dir in 2dgs_gen/*/; do
    # 获取当前文件夹名
    dir_name=$(basename "$work_dir")

    # 检查 dir_name 是否在 need_to_process 列表中
    if [[ ! " ${need_to_process[@]} " =~ " ${dir_name} " ]]; then
        echo "Skipping directory: $dir_name (not in need_to_process)"
        continue  # 如果不在列表中，跳过当前目录，进入下一个
    fi

    echo "Processing directory: $dir_name"

    # 清除 2d-gaussian-splatting 文件夹中的数据和输出文件夹
    echo "Cleaning up data and output folders in 2d-gaussian-splatting..."
    rm -rf images
    rm -rf masks
    rm -rf dilate_mask/*
    rm -rf images.bin
    rm -rf cameras.bin

    # 运行文件检查
    python file.py copy -n "$dir_name"
    echo "Already run python file.py copy -n $dir_name"

    # 运行膨胀 mask
    python dilate.py -s 50

    # 运行去除背景
    python run.py -i "$dir_name".ply

    # 清除 dilate_mask 文件夹内容
    rm -rf dilate_mask/*
done

