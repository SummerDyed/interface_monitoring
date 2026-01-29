#!/bin/bash
# 启动脚本
# 启动接口监控服务

echo "=== 启动接口监控服务 ==="

# 检查配置文件
if [ ! -f "config.yaml" ]; then
    echo "错误: 未找到config.yaml配置文件"
    echo "请先运行 ./scripts/install.sh 安装并配置"
    exit 1
fi

# 检查依赖
python -c "import yaml, requests, schedule" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "错误: 依赖库未安装"
    echo "请先运行 ./scripts/install.sh 安装依赖"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 启动服务
echo "启动监控服务..."
PYTHONPATH=src python src/main.py

echo "服务已停止"
