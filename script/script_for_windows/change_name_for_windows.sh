#!/bin/bash

# 批量重命名脚本：将frame/plane文件夹中的文件重命名
# 用法: ./rename_files.sh <新的文件名前缀>

# 检查参数
if [ $# -eq 0 ]; then
    echo "错误：请提供新的文件名前缀"
    echo "用法: $0 <新的文件名前缀>"
    echo "示例: $0 newname"
    exit 1
fi

# 获取新的文件名前缀
NEW_PREFIX="$1"

# 目标目录路径
TARGET_DIR=".\frame\formulaE"

# 检查目录是否存在
if [ ! -d "$TARGET_DIR" ]; then
    echo "错误：目录 $TARGET_DIR 不存在"
    exit 1
fi

# 进入目标目录
cd "$TARGET_DIR" || {
    echo "错误：无法进入目录 $TARGET_DIR"
    exit 1
}

# 计数器
count=0
success=0
failed=0

echo "开始重命名 $TARGET_DIR 目录下的文件..."
echo "新的文件名前缀: $NEW_PREFIX"
echo "----------------------------------------"

# 遍历所有jpg文件
for file in *.jpg; do
    # 检查文件是否存在（防止没有匹配文件时的问题）
    if [ ! -f "$file" ]; then
        continue
    fi
    
    # 提取文件名中的数字部分
    # 使用正则表达式匹配 _数字.jpg 的模式
    if [[ "$file" =~ _([0-9]+)\.jpg$ ]]; then
        number="${BASH_REMATCH[1]}"
        new_name="${NEW_PREFIX}_${number}.jpg"
        
        # 检查新文件名是否已存在
        if [ -f "$new_name" ] && [ "$file" != "$new_name" ]; then
            echo "警告: $new_name 已存在，跳过 $file"
            ((failed++))
            continue
        fi
        
        # 如果文件名相同，跳过
        if [ "$file" = "$new_name" ]; then
            echo "跳过: $file (文件名已是目标格式)"
            continue
        fi
        
        # 重命名文件
        if mv "$file" "$new_name"; then
            echo "成功: $file -> $new_name"
            ((success++))
        else
            echo "失败: 无法重命名 $file"
            ((failed++))
        fi
    else
        echo "跳过: $file (不符合命名格式 *_数字.jpg)"
        ((failed++))
    fi
    
    ((count++))
done

# 返回原目录
cd - > /dev/null

# 显示统计结果
echo "----------------------------------------"
echo "重命名完成！"
echo "处理文件总数: $count"
echo "成功重命名: $success"
echo "失败/跳过: $failed"

if [ $count -eq 0 ]; then
    echo "注意: 在 $TARGET_DIR 目录中没有找到符合格式的jpg文件"
fi