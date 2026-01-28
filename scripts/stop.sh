#!/bin/bash
# 停止脚本
# 停止接口监控服务

echo "=== 停止接口监控服务 ==="

# 查找并停止所有Python进程
pids=$(pgrep -f "src.main")
if [ -n "$pids" ]; then
    echo "正在停止监控服务..."
    for pid in $pids; do
        kill $pid
        echo "已停止进程: $pid"
    done
    echo "✓ 服务已停止"
else
    echo "未找到运行中的监控服务"
fi
