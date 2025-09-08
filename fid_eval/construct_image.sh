#!/bin/bash

# 批量处理多模态数据脚本
# 脚本位置: project/fid_eval/

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示使用说明
show_usage() {
    echo "使用方法:"
    echo "  $0                    - 根据脚本中的MODE配置运行"
    echo "  $0 -h|--help         - 显示此帮助信息"
    echo ""
    echo "配置说明:"
    echo "  在脚本顶部修改以下配置:"
    echo "    MODE=\"all\"         - 处理所有文件夹"
    echo "    MODE=\"specific\"    - 处理SPECIFIC_FOLDERS数组中指定的文件夹"
    echo ""
    echo "示例配置:"
    echo "  MODE=\"specific\""
    echo "  SPECIFIC_FOLDERS=("
    echo "      \"apple\""
    echo "      \"banana\""
    echo "      \"car\""
    echo "  )"
}

# 处理单个文件夹的函数
process_folder() {
    local folder_name="$1"
    local source_path="../multi-modal_data/$folder_name"
    local mesh_source="$source_path/3D_Model/mesh_no_bg.ply"
    local mesh_dest="./ours/3d_model/$folder_name.ply"
    
    print_info "开始处理文件夹: $folder_name"
    
    # 检查源文件夹是否存在
    if [ ! -d "$source_path" ]; then
        print_error "源文件夹不存在: $source_path"
        return 1
    fi
    
    # 检查mesh文件是否存在
    if [ ! -f "$mesh_source" ]; then
        print_error "mesh文件不存在: $mesh_source"
        return 1
    fi
    
    # 确保目标目录存在
    mkdir -p "./ours/3d_model"
    mkdir -p "./ours/render_image"
    mkdir -p "./ours/tmp"
    mkdir -p "./ours/real_image"
    
    # 复制并重命名mesh文件
    print_info "复制mesh文件: $mesh_source -> $mesh_dest"
    if cp "$mesh_source" "$mesh_dest"; then
        print_success "mesh文件复制成功"
    else
        print_error "mesh文件复制失败"
        return 1
    fi
    
    # 检查cameras.json文件是否存在
    local camera_json="../2dgs_gen/$folder_name/output/cameras.json"
    if [ ! -f "$camera_json" ]; then
        print_error "相机配置文件不存在: $camera_json"
        return 1
    fi
    
    # 执行Blender渲染命令
    print_info "执行Blender渲染..."
    local blender_cmd="/opt/blender-2.90.0-linux64/blender --background --python load_colmap_to_render.py -- --camera_json $camera_json --output_folder ./ours/render_image $mesh_dest"
    
    print_info "执行命令: $blender_cmd"
    if eval "$blender_cmd"; then
        print_success "Blender渲染完成"
    else
        print_error "Blender渲染失败"
        return 1
    fi
    
    # 检查图像处理所需的目录
    local images_dir="../2dgs_gen/$folder_name/data/images"
    local masks_dir="../2dgs_gen/$folder_name/masks"
    
    if [ ! -d "$images_dir" ]; then
        print_error "图像目录不存在: $images_dir"
        return 1
    fi
    
    if [ ! -d "$masks_dir" ]; then
        print_error "遮罩目录不存在: $masks_dir"
        return 1
    fi
    
    # 执行图像处理命令
    print_info "执行图像处理..."
    local process_cmd="python process_image.py -i $images_dir -m $masks_dir -o ./ours/tmp -t ./ours/real_image"
    
    print_info "执行命令: $process_cmd"
    if eval "$process_cmd"; then
        print_success "图像处理完成"
    else
        print_error "图像处理失败"
        return 1
    fi
    
    print_success "文件夹 '$folder_name' 处理完成！"
    echo "----------------------------------------"
    return 0
}

# ================== 配置区域 ==================
# 处理模式设置：
# MODE="all"           - 处理所有文件夹
# MODE="specific"      - 处理指定的文件夹列表

MODE="specific"  # 修改这里来切换处理模式

# 当MODE="specific"时，在下面的数组中指定要处理的文件夹名字
SPECIFIC_FOLDERS=(
"plant"
"chika_exp"
"duck"
"kotori_exp"
"p1"
"plant8"
"fighter_exp"
"formulaE"
    # "apple"
    # "banana" 
    # "car"
    # "chair"
    # 在这里添加需要处理的文件夹名字，每行一个，取消前面的#号
)

# =============================================

# 主函数
main() {
    # 检查是否在正确的目录
    if [ ! -d "../multi-modal_data" ]; then
        print_error "未找到 ../multi-modal_data 目录，请确保脚本在 project/fid_eval/ 目录下运行"
        exit 1
    fi
    
    # 检查必要的Python脚本是否存在
    if [ ! -f "load_colmap_to_render.py" ]; then
        print_error "未找到 load_colmap_to_render.py 脚本"
        exit 1
    fi
    
    if [ ! -f "process_image.py" ]; then
        print_error "未找到 process_image.py 脚本"
        exit 1
    fi
    
    # 检查Blender是否存在
    if [ ! -f "/opt/blender-2.90.0-linux64/blender" ]; then
        print_error "未找到Blender: /opt/blender-2.90.0-linux64/blender"
        exit 1
    fi
    
    local success_count=0
    local fail_count=0
    
    # 解析命令行参数
    case "$1" in
        -h|--help)
            show_usage
            exit 0
            ;;
    esac
    
    # 根据配置的MODE决定处理方式
    if [ "$MODE" = "specific" ]; then
        # 处理指定的文件夹列表
        if [ ${#SPECIFIC_FOLDERS[@]} -eq 0 ]; then
            print_error "MODE设置为specific，但SPECIFIC_FOLDERS数组为空！"
            print_info "请在脚本顶部的SPECIFIC_FOLDERS数组中添加要处理的文件夹名字"
            exit 1
        fi
        
        print_info "处理模式: 指定文件夹"
        print_info "要处理的文件夹: ${SPECIFIC_FOLDERS[*]}"
        
        for folder_name in "${SPECIFIC_FOLDERS[@]}"; do
            if process_folder "$folder_name"; then
                ((success_count++))
            else
                ((fail_count++))
            fi
        done
    else
        # 处理所有文件夹
        print_info "处理模式: 所有文件夹"
        
        for folder in ../multi-modal_data/*/; do
            if [ -d "$folder" ]; then
                folder_name=$(basename "$folder")
                if process_folder "$folder_name"; then
                    ((success_count++))
                else
                    ((fail_count++))
                fi
            fi
        done
    fi
    
    # 输出总结
    echo "========================================"
    print_info "处理完成！"
    print_success "成功处理: $success_count 个文件夹"
    if [ $fail_count -gt 0 ]; then
        print_error "失败处理: $fail_count 个文件夹"
    fi
    echo "========================================"
    
    # 返回适当的退出码
    if [ $fail_count -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# 脚本入口点
main "$@"
