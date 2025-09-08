#!/bin/bash

# 定义基础路径
base_dir="./objaverse_xl"
model_dir="${base_dir}/3d_model"
output_dir="${base_dir}/tmp"
real_image_dir="${base_dir}/real_image"
render_image_dir="${base_dir}/render_image"

# 创建必要的目录
mkdir -p "${output_dir}"
mkdir -p "${real_image_dir}"
mkdir -p "${render_image_dir}"

# 获取Blender路径
blender_path="/opt/blender-2.90.0-linux64/blender"

# 遍历3d_model目录中的所有文件夹
for folder in "${model_dir}"/*/; do
    # 获取文件夹名称（移除路径和末尾斜杠）
    folder_name=$(basename "${folder}")
    
    # 检查文件夹是否为空
    if [ -z "$folder_name" ]; then
        echo "跳过空文件夹"
        continue
    fi
    
    # 构建PLY文件路径
    ply_path="${folder}${folder_name}.ply"
    
    # 检查PLY文件是否存在
    if [ ! -f "$ply_path" ]; then
        echo "PLY文件不存在: $ply_path"
        continue
    fi
    
    echo "处理模型: $folder_name"
    echo "PLY路径: $ply_path"
    
    # 清空临时输出目录
    rm -rf "${output_dir}"/*
    
    # 执行Blender渲染
    echo "开始渲染..."
    "$blender_path" --background --python test.py -- "$ply_path" "$output_dir" -n 194
    
    # 检查渲染是否成功
    if [ $? -ne 0 ]; then
        echo "渲染失败: $folder_name"
        continue
    fi
    
    # 获取所有渲染图片
    images=("${output_dir}"/*.png)
    total_images=${#images[@]}
    
    # 检查是否有足够的图片
    if [ $total_images -lt 194 ]; then
        echo "渲染图片不足: $total_images/194"
        continue
    fi
    
    # 随机打乱图片顺序
    shuffled_images=($(shuf -e "${images[@]}"))
    
    # 计算分割点（平分图片）
    split_point=$((total_images / 2))
    
    # 移动前一半到real_image
    echo "移动图片到real_image目录..."
    for ((i=0; i<split_point; i++)); do
        # 添加前缀避免文件名冲突
        filename=$(basename "${shuffled_images[$i]}")
        new_filename="${folder_name}_${filename}"
        mv "${shuffled_images[$i]}" "${real_image_dir}/${new_filename}"
    done
    
    # 移动后一半到render_image
    echo "移动图片到render_image目录..."
    for ((i=split_point; i<total_images; i++)); do
        # 添加前缀避免文件名冲突
        filename=$(basename "${shuffled_images[$i]}")
        new_filename="${folder_name}_${filename}"
        mv "${shuffled_images[$i]}" "${render_image_dir}/${new_filename}"
    done
    
    echo "完成处理: $folder_name"
    echo "----------------------------------------"
done

echo "所有模型处理完成！"
