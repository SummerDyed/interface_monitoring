#!/bin/bash
# 安装脚本
# 安装项目依赖和配置环境

echo "=== 接口监控脚本安装程序 ==="
echo ""

# 检查Python版本
python_version=$(python --version 2>&1)
if [ $? -ne 0 ]; then
    echo "错误: 未找到Python，请先安装Python 3.7+"
    exit 1
fi
echo "✓ Python版本: $python_version"

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境? (y/n): " create_venv
if [ "$create_venv" = "y" ] || [ "$create_venv" = "Y" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
    source venv/bin/activate
    echo "✓ 虚拟环境已创建并激活"
fi

# 升级pip
echo "升级pip..."
python -m pip install --upgrade pip

# 安装依赖
echo "安装项目依赖..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ 依赖安装成功"
else
    echo "✗ 依赖安装失败"
    exit 1
fi

# 创建日志目录
mkdir -p logs
echo "✓ 日志目录已创建"

# 设置脚本权限
chmod +x scripts/*.sh
echo "✓ 脚本权限已设置"

echo ""
echo "=== 安装完成 ==="
echo "下一步: 配置config.yaml文件中的参数"
echo "运行: ./scripts/start.sh 启动监控"
