#!/bin/bash

# 定义根目录
ROOT_DIR="2dgs_gen"
REMBG_INPUT_DIR="rembg_process/in"
REMBG_OUTPUT_DIR="rembg_process/out"
XMEM_OUTPUT_DIR="pic"
MISSING_OUTPUT=()

# 确保必要的目录存在
mkdir -p "$REMBG_INPUT_DIR" "$REMBG_OUTPUT_DIR" "$XMEM_OUTPUT_DIR"

# 遍历所有项目文件夹
for PROJECT_DIR in "$ROOT_DIR"/*/; do
    PROJECT_NAME=$(basename "$PROJECT_DIR")
    echo "检查项目: $PROJECT_NAME"
    
    # 检查必需目录
    DATA_DIR="$PROJECT_DIR/data"
    MASKS_DIR="$PROJECT_DIR/masks"
    OUTPUT_DIR="$PROJECT_DIR/output"
    
    # 1. 检查基础目录结构
    if [[ ! -d "$DATA_DIR" || ! -d "$OUTPUT_DIR" ]]; then
        echo "  [错误] 缺失基础目录 (data 或 output)"
        continue
    fi
    
    # 2. 检查masks目录和文件
    # 如果masks目录不存在，或者存在但为空，则进行处理
    if [[ ! -d "$MASKS_DIR" ]] || [[ -z "$(ls -A "$MASKS_DIR" 2>/dev/null)" ]]; then
        if [[ ! -d "$MASKS_DIR" ]]; then
            echo "  [处理] 创建masks目录并生成内容"
            mkdir -p "$MASKS_DIR"
        else
            echo "  [处理] masks目录为空，重新生成内容"
        fi
        
        # 检查输入目录是否存在
        INPUT_DIR="$DATA_DIR/input"
        if [[ ! -d "$INPUT_DIR" ]]; then
            echo "  [错误] 输入目录不存在: $INPUT_DIR"
            continue
        fi
        
        # 查找所有input图像
        INPUT_IMAGES=("$INPUT_DIR"/*_0.jpg)
        if [[ ${#INPUT_IMAGES[@]} -eq 0 ]]; then
            echo "  [错误] 未找到input图像 (*_0.jpg)"
            continue
        fi
        
        # 处理每张输入图像
        for IMG_PATH in "${INPUT_IMAGES[@]}"; do
            # 清除rembg和XMem文件夹内的图片
            rm -rf rembg_process/in/*
            rm -rf rembg_process/out/*
            rm -rf pic/JPEGImages/video1/*
            rm -rf pic/Annotations/video1/*
            rm -rf pic/video1

            IMG_NAME=$(basename "$IMG_PATH")
            BASE_NAME=${IMG_NAME%_0.jpg}
            
            # 复制到rembg输入目录
            echo "  [处理] 复制图像到rembg输入: $IMG_NAME"
            cp "$IMG_PATH" "$REMBG_INPUT_DIR/"
            
            # 运行rembg处理
            echo "  [处理] 执行rembg处理: $BASE_NAME"
            python rembg_process.py -i "$BASE_NAME" -o "$REMBG_OUTPUT_DIR" -m u2net
            
            # 确保XMem输出目录存在
            mkdir -p "$XMEM_OUTPUT_DIR/video1"
            
            # 运行XMem处理
            echo "  [处理] 执行XMem分割"
            python ./xmem/eval_test.py \
                --model ./xmem/saves/XMem-s012.pth \
                --generic_path ./pic \
                --dataset G \
                --output ./pic
            
            # 复制生成的masks
            echo "  [处理] 复制生成的masks"
            cp "$XMEM_OUTPUT_DIR/video1/"* "$MASKS_DIR/"
            
            # 清理临时文件
            rm -f "$REMBG_INPUT_DIR/$IMG_NAME"
            rm -f "$REMBG_OUTPUT_DIR/${BASE_NAME}.png"
            rm -rf "$XMEM_OUTPUT_DIR/video1"

            # 清除rembg和XMem文件夹内的图片
            rm -rf rembg_process/in/*
            rm -rf rembg_process/out/*
            rm -rf pic/JPEGImages/video1/*
            rm -rf pic/Annotations/video1/*
            rm -rf pic/video1
        done
        echo "  [完成] masks生成完成"
    else
        echo "  [通过] masks目录已存在且包含文件"
    fi
    
    # 3. 检查输出文件
    TRAIN_DIR="$OUTPUT_DIR/train/ours_30000"
    if [[ -d "$TRAIN_DIR" ]]; then
        if [[ ! -f "$TRAIN_DIR/fuse.ply" || ! -f "$TRAIN_DIR/fuse_post.ply" ]]; then
            echo "  [警告] 缺失输出文件"
            MISSING_OUTPUT+=("$PROJECT_NAME")
        else
            echo "  [通过] 所有输出文件存在"
        fi
    else
        echo "  [错误] 训练输出目录不存在"
        MISSING_OUTPUT+=("$PROJECT_NAME")
    fi
    
    echo "----------------------------------------"
done

# 报告缺失输出的项目
if [[ ${#MISSING_OUTPUT[@]} -gt 0 ]]; then
    echo "以下项目缺失输出文件:"
    printf ' - %s\n' "${MISSING_OUTPUT[@]}"
else
    echo "所有项目输出完整"
fi