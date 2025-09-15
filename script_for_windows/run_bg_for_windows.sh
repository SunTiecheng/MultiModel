#!/bin/bash

# 移除 set -e，改为手动处理错误
# set -e

#need_to_process=("shoes3") # 在这里替换为你的目标文件夹名称
need_to_jump=("chika2_720p") # 在这里替换为你的目标文件夹名称

# 创建数组来记录失败的文件夹名
failed_dirs=()

# 检查并终止已有的 tmux 会话
if tmux has-session -t progress 2>/dev/null; then
    tmux kill-session -t progress
fi

for work_dir in 2dgs_gen/*/; do

    # 获取当前文件夹名
    dir_name=$(basename "$work_dir")
    
    # ====== 新增检查：如果存在同名_ps.ply文件则跳过 ======
    if [ -f "mesh_ply/${dir_name}_ps.ply" ]; then
        echo "Skipping ${dir_name}: _ps.ply file already exists" | tee -a progress.log
        continue
    fi
    # =================================================

    # 检查 dir_name 是否在 need_to_process 列表中
    #if [[ ! " ${need_to_process[@]} " =~ " ${dir_name} " ]]; then
        #echo "Skipping directory: $dir_name (not in need_to_process)"
        #continue  # 如果不在列表中，跳过当前目录，进入下一个
    #fi

    if [[ ! " ${need_to_jump[@]} " =~ " ${dir_name} " ]]; then
        echo "$dir_name (in need_to_process)"
    else
        echo "Skipping directory: $dir_name (in need_to_jump)"
        continue  # 如果不在列表中，跳过当前目录，进入下一个
    fi

    echo "Processing directory: $dir_name" | tee -a progress.log
    
    # 开始错误处理：禁用自动退出
    set +e
    
    # 执行第一个python命令
    python file.py delete
    if [ $? -ne 0 ]; then
        echo "Error: Failed to execute 'python file.py delete' for $dir_name" | tee -a progress.log
        failed_dirs+=("$dir_name")
        set -e  # 重新启用错误退出以保持脚本其他部分的行为
        continue
    fi
    
    # 删除images目录
    rm -rf images
    if [ $? -ne 0 ]; then
        echo "Error: Failed to remove images directory for $dir_name" | tee -a progress.log
        failed_dirs+=("$dir_name")
        set -e
        continue
    fi

    # 执行copy命令
    python file.py copy -n ${dir_name}
    if [ $? -ne 0 ]; then
        echo "Error: Failed to execute 'python file.py copy -n ${dir_name}' for $dir_name" | tee -a progress.log
        failed_dirs+=("$dir_name")
        set -e
        continue
    fi
    
    # 执行dilate.py
    python dilate.py -s 50
    if [ $? -ne 0 ]; then
        echo "Error: Failed to execute 'python dilate.py -s 50' for $dir_name" | tee -a progress.log
        failed_dirs+=("$dir_name")
        set -e
        continue
    fi
    
    # 执行run.py
    python run.py -i ${dir_name}.ply
    if [ $? -ne 0 ]; then
        echo "Error: Failed to execute 'python run.py -i ${dir_name}.ply' for $dir_name" | tee -a progress.log
        failed_dirs+=("$dir_name")
        set -e
        continue
    fi
    
    # 执行最后的delete命令
    python file.py delete
    if [ $? -ne 0 ]; then
        echo "Error: Failed to execute final 'python file.py delete' for $dir_name" | tee -a progress.log
        failed_dirs+=("$dir_name")
        set -e
        continue
    fi
    
    # 如果到达这里，说明当前目录处理成功
    echo "Successfully processed: $dir_name" | tee -a progress.log
    
    # 重新启用错误退出
    set -e
    
done

# 输出处理结果
echo "==================== PROCESSING SUMMARY ====================" | tee -a progress.log
if [ ${#failed_dirs[@]} -eq 0 ]; then
    echo "✅ All directories processed successfully!" | tee -a progress.log
else
    echo "❌ The following directories failed during processing:" | tee -a progress.log
    for failed_dir in "${failed_dirs[@]}"; do
        echo "  - $failed_dir" | tee -a progress.log
    done
    echo "Total failed directories: ${#failed_dirs[@]}" | tee -a progress.log
fi
echo "=============================================================" | tee -a progress.log