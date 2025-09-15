#!/bin/bash

# 设置脚本在出错时退出
set -e

# 获取项目根目录（脚本所在目录）
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "项目目录: $PROJECT_DIR"

# 检查必要的目录是否存在
if [ ! -d "$PROJECT_DIR/2dgs_gen" ]; then
    echo "错误: 找不到2dgs_gen文件夹"
    exit 1
fi

# 遍历2dgs_gen下的所有文件夹
for folder in "$PROJECT_DIR/2dgs_gen"/*; do
    if [ -d "$folder" ]; then
        # 获取文件夹名称
        folder_name=$(basename "$folder")
        echo "正在处理文件夹: $folder_name"
        
        # 检查multi-modal_data中是否已存在同名文件夹
        if [ -d "$PROJECT_DIR/multi-modal_data/$folder_name" ]; then
            echo "发现已存在的文件夹: multi-modal_data/$folder_name，进行检查..."
            
            # 检查是否存在3D_Model、caption、images三个文件夹
            has_3d_model=false
            has_caption=false
            has_images=false
            
            if [ -d "$PROJECT_DIR/multi-modal_data/$folder_name/3D_Model" ] && [ "$(ls -A "$PROJECT_DIR/multi-modal_data/$folder_name/3D_Model" 2>/dev/null)" ]; then
                has_3d_model=true
                echo "  ✓ 3D_Model文件夹存在且有文件"
            else
                echo "  ✗ 3D_Model文件夹不存在或为空"
            fi
            
            if [ -d "$PROJECT_DIR/multi-modal_data/$folder_name/caption" ] && [ "$(ls -A "$PROJECT_DIR/multi-modal_data/$folder_name/caption" 2>/dev/null)" ]; then
                has_caption=true
                echo "  ✓ caption文件夹存在且有文件"
            else
                echo "  ✗ caption文件夹不存在或为空"
            fi
            
            if [ -d "$PROJECT_DIR/multi-modal_data/$folder_name/images" ] && [ "$(ls -A "$PROJECT_DIR/multi-modal_data/$folder_name/images" 2>/dev/null)" ]; then
                has_images=true
                echo "  ✓ images文件夹存在且有文件"
            else
                echo "  ✗ images文件夹不存在或为空"
            fi
            
            # 如果三个文件夹都存在且都有文件，则跳过本次循环
            if [ "$has_3d_model" = true ] && [ "$has_caption" = true ] && [ "$has_images" = true ]; then
                echo "  >> 所有必需文件夹都存在且有文件，跳过处理: $folder_name"
                echo "----------------------------------------"
                continue
            else
                echo "  >> 部分文件夹缺失或为空，继续处理: $folder_name"
            fi
        else
            echo "文件夹不存在，开始新建处理: $folder_name"
        fi
        
        # 1. 在multi-modal_data下创建同名文件夹
        mkdir -p "$PROJECT_DIR/multi-modal_data/$folder_name"
        echo "创建文件夹: multi-modal_data/$folder_name"
        
        # 2. 复制input文件夹到multi-modal_data下并重命名为images
        if [ -d "$PROJECT_DIR/2dgs_gen/$folder_name/data/input" ]; then
            cp -r "$PROJECT_DIR/2dgs_gen/$folder_name/data/input" "$PROJECT_DIR/multi-modal_data/$folder_name/images"
            echo "复制并重命名input文件夹为images"
        else
            echo "警告: 找不到 2dgs_gen/$folder_name/data/input 文件夹"
        fi
        
        # 3. 创建3D_Model和caption文件夹
        mkdir -p "$PROJECT_DIR/multi-modal_data/$folder_name/3D_Model"
        mkdir -p "$PROJECT_DIR/multi-modal_data/$folder_name/caption"
        echo "创建3D_Model和caption文件夹"
        
        # 4. 复制point_cloud.ply到3D_Model
        if [ -f "$PROJECT_DIR/2dgs_gen/$folder_name/output/point_cloud/iteration_30000/point_cloud.ply" ]; then
            cp "$PROJECT_DIR/2dgs_gen/$folder_name/output/point_cloud/iteration_30000/point_cloud.ply" "$PROJECT_DIR/multi-modal_data/$folder_name/3D_Model/"
            echo "复制point_cloud.ply到3D_Model"
        else
            echo "警告: 找不到 point_cloud.ply 文件"
        fi
        
        # 5. 运行rgb_process.py
        echo "运行rgb_process.py..."
        cd "$PROJECT_DIR"
        if [ -f "rgb_process.py" ]; then
            python rgb_process.py -i "./multi-modal_data/$folder_name/3D_Model" -o "./multi-modal_data/$folder_name/3D_model"
        else
            echo "警告: 找不到rgb_process.py文件"
        fi
        
        # 6. 重命名point_cloud.ply为gaussian_point_cloud.ply
        if [ -f "$PROJECT_DIR/multi-modal_data/$folder_name/3D_Model/point_cloud.ply" ]; then
            mv "$PROJECT_DIR/multi-modal_data/$folder_name/3D_Model/point_cloud.ply" "$PROJECT_DIR/multi-modal_data/$folder_name/3D_Model/gaussian_point_cloud.ply"
            echo "重命名point_cloud.ply为gaussian_point_cloud.ply"
        fi
        
        # 7. 复制fuse_post.ply到3D_Model并重命名为mesh.ply
        if [ -f "$PROJECT_DIR/2dgs_gen/$folder_name/output/train/ours_30000/fuse_post.ply" ]; then
            cp "$PROJECT_DIR/2dgs_gen/$folder_name/output/train/ours_30000/fuse_post.ply" "$PROJECT_DIR/multi-modal_data/$folder_name/3D_Model/mesh.ply"
            echo "复制并重命名fuse_post.ply为mesh.ply"
        else
            echo "警告: 找不到fuse_post.ply文件"
        fi
        
        # 8. 复制mesh_ply中的文件到3D_Model并重命名为mesh_no_bg.ply
        if [ -f "$PROJECT_DIR/mesh_ply/${folder_name}_ps.ply" ]; then
            cp "$PROJECT_DIR/mesh_ply/${folder_name}_ps.ply" "$PROJECT_DIR/multi-modal_data/$folder_name/3D_Model/mesh_no_bg.ply"
            echo "复制并重命名${folder_name}_ps.ply为mesh_no_bg.ply"
        else
            echo "警告: 找不到mesh_ply/${folder_name}_ps.ply文件"
        fi
        
        # 9. 创建frame_exchange必要的文件夹
        mkdir -p "$PROJECT_DIR/frame_exchange/images"
        mkdir -p "$PROJECT_DIR/frame_exchange/masks"
        
        # 10. 复制图片和mask文件到frame_exchange
        if [ -f "$PROJECT_DIR/multi-modal_data/$folder_name/images/${folder_name}_0.jpg" ]; then
            cp "$PROJECT_DIR/multi-modal_data/$folder_name/images/${folder_name}_0.jpg" "$PROJECT_DIR/frame_exchange/images/"
            echo "复制${folder_name}_0.jpg到frame_exchange/images"
        else
            echo "警告: 找不到${folder_name}_0.jpg文件"
        fi
        
        if [ -f "$PROJECT_DIR/2dgs_gen/$folder_name/masks/${folder_name}_0.png" ]; then
            cp "$PROJECT_DIR/2dgs_gen/$folder_name/masks/${folder_name}_0.png" "$PROJECT_DIR/frame_exchange/masks/"
            echo "复制${folder_name}_0.png到frame_exchange/masks"
        else
            echo "警告: 找不到${folder_name}_0.png文件"
        fi
        
        # 11. 运行touming.py
        echo "运行touming.py..."
        cd "$PROJECT_DIR"
        if [ -f "touming.py" ]; then
            python touming.py
        else
            echo "警告: 找不到touming.py文件"
        fi
        
        # 12. 创建MeaCap/images_example文件夹并复制save文件夹内容
        mkdir -p "$PROJECT_DIR/MeaCap/images_example"
        if [ -d "$PROJECT_DIR/frame_exchange/save" ]; then
            cp -r "$PROJECT_DIR/frame_exchange/save/"* "$PROJECT_DIR/MeaCap/images_example/"
            echo "复制save文件夹内容到MeaCap/images_example"
        else
            echo "警告: 找不到frame_exchange/save文件夹"
        fi
        
        # 13. 切换到MeaCap目录并运行inference.py
        echo "运行MeaCap inference..."
        cd "$PROJECT_DIR/MeaCap"
        if [ -f "inference.py" ]; then
            python inference.py --memory_id coco --img_path ./images_example --lm_model_path ./checkpoints/CBART_coco
        else
            echo "警告: 找不到MeaCap/inference.py文件"
        fi
        
        # 14. 复制outputs中的json文件到caption文件夹并重命名
        cd "$PROJECT_DIR"
        if [ -d "$PROJECT_DIR/MeaCap/outputs" ]; then
            # 查找json文件并复制第一个找到的
            json_file=$(find "$PROJECT_DIR/MeaCap/outputs" -name "*.json" -type f | head -1)
            if [ -n "$json_file" ]; then
                cp "$json_file" "$PROJECT_DIR/multi-modal_data/$folder_name/caption/caption.json"
                echo "复制json文件并重命名为caption.json"
            else
                echo "警告: 在MeaCap/outputs中找不到json文件"
            fi
        else
            echo "警告: 找不到MeaCap/outputs文件夹"
        fi
        
        echo "完成处理文件夹: $folder_name"
        echo "----------------------------------------"
        
        # 清理frame_exchange文件夹为下一次处理做准备
        rm -rf "$PROJECT_DIR/frame_exchange/images/"*
        rm -rf "$PROJECT_DIR/frame_exchange/masks/"*
        rm -rf "$PROJECT_DIR/frame_exchange/save/"*
        rm -rf "$PROJECT_DIR/MeaCap/images_example/"*
        rm -rf "$PROJECT_DIR/MeaCap/outputs/"*
    fi
done

echo "所有文件夹处理完成！"