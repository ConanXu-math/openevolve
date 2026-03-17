#!/bin/bash
# OpenEvolve 自动化运行脚本
# 用法: ./run_evolution.sh [迭代次数] [输出目录]

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 默认参数
ITERATIONS=${1:-10}
OUTPUT_DIR=${2:-"openevolve_output"}

# 检查必要文件
if [ ! -f "initial_program.py" ]; then
    echo "错误: 找不到 initial_program.py"
    exit 1
fi

if [ ! -f "evaluator.py" ]; then
    echo "错误: 找不到 evaluator.py"
    exit 1
fi

# 检查配置文件，如果不存在则使用默认配置
CONFIG_FILE="config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "警告: 找不到 config.yaml，将使用默认配置"
    CONFIG_FILE="config_default.yaml"
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "错误: 找不到任何配置文件"
        exit 1
    fi
fi

# 检查API密钥
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "错误: 请设置 DEEPSEEK_API_KEY 环境变量"
    echo "例如: export DEEPSEEK_API_KEY=\"your-api-key\""
    exit 1
fi

echo "========================================"
echo "OpenEvolve 函数最小化演化"
echo "========================================"
echo "输入文件夹: $SCRIPT_DIR"
echo "初始程序: initial_program.py"
echo "评估器: evaluator.py"
echo "配置文件: $CONFIG_FILE"
echo "迭代次数: $ITERATIONS"
echo "输出目录: $OUTPUT_DIR"
echo "========================================"

# 运行OpenEvolve
echo "开始演化过程..."
python ../../openevolve-run.py \
    initial_program.py \
    evaluator.py \
    --config "$CONFIG_FILE" \
    --iterations "$ITERATIONS" \
    --output "$OUTPUT_DIR"

echo "========================================"
echo "演化完成!"
echo "结果保存在: $OUTPUT_DIR/"
echo ""
echo "查看最佳程序:"
echo "  cat $OUTPUT_DIR/best/best_program_info.json"
echo ""
echo "运行最佳程序:"
echo "  python $OUTPUT_DIR/best/best_program.py"
echo "========================================"