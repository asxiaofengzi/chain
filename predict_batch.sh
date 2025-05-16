#!/bin/bash

echo "铁链缺陷检测批处理工具"
echo "========================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请安装Python 3.8或更高版本。"
    exit 1
fi

# 检查输入参数
if [ $# -eq 0 ]; then
    echo "用法: ./predict_batch.sh [图片目录] [可选:输出目录] [可选:模型路径]"
    echo "例如: ./predict_batch.sh /home/user/images /home/user/results best.pt"
    exit 1
fi

# 设置参数
INPUT_DIR="$1"
OUTPUT_DIR="${2:-results}"
MODEL_PATH="${3:-best.pt}"

echo "输入目录: $INPUT_DIR"
echo "输出目录: $OUTPUT_DIR"
echo "模型路径: $MODEL_PATH"
echo ""

# 运行预测脚本
python3 predict_images.py --input "$INPUT_DIR" --output "$OUTPUT_DIR" --model "$MODEL_PATH" --crops

echo ""
echo "处理完成！" 