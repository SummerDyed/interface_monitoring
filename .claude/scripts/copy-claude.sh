#!/bin/bash

# Copy Claude Configuration Script
# 将 claude 目录内容复制到目标项目的 .claude 目录
# 用法: ./copy-claude.sh <目标项目路径>

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示使用说明
show_usage() {
    echo -e "${BLUE}用法:${NC}"
    echo -e "  $0 <目标项目路径>"
    echo -e ""
    echo -e "${BLUE}示例:${NC}"
    echo -e "  $0 /path/to/your/project"
    echo -e ""
    echo -e "${BLUE}说明:${NC}"
    echo -e "  此脚本会将 claude 目录的所有内容复制到目标项目的 .claude 目录"
    echo -e "  排除的目录: prds/, epics/"
    echo -e "  已存在的文件将被覆盖"
    exit 1
}

# 检查参数
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ 错误: 缺少目标项目路径参数${NC}"
    echo -e ""
    show_usage
fi

TARGET_PROJECT="$1"

# 验证目标路径
if [ ! -d "$TARGET_PROJECT" ]; then
    echo -e "${RED}❌ 错误: 目标路径不存在: $TARGET_PROJECT${NC}"
    exit 1
fi

if [ ! -w "$TARGET_PROJECT" ]; then
    echo -e "${RED}❌ 错误: 目标路径没有写入权限: $TARGET_PROJECT${NC}"
    exit 1
fi

# 定位源 claude 目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_CLAUDE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)/claude"

if [ ! -d "$SOURCE_CLAUDE_DIR" ]; then
    echo -e "${RED}❌ 错误: 找不到源 claude 目录: $SOURCE_CLAUDE_DIR${NC}"
    exit 1
fi

# 目标 .claude 目录
TARGET_CLAUDE_DIR="$TARGET_PROJECT/.claude"

echo -e "${BLUE}🚀 开始复制 Claude 配置${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}源目录:${NC} $SOURCE_CLAUDE_DIR"
echo -e "${BLUE}目标目录:${NC} $TARGET_CLAUDE_DIR"
echo -e "${YELLOW}排除目录:${NC} prds/, epics/"
echo -e "${RED}覆盖模式:${NC} 强制覆盖所有已存在的文件"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 创建目标 .claude 目录（如果不存在）
if [ ! -d "$TARGET_CLAUDE_DIR" ]; then
    echo -e "${BLUE}📁 创建目标目录: $TARGET_CLAUDE_DIR${NC}"
    mkdir -p "$TARGET_CLAUDE_DIR"
fi

# 检查 rsync 是否可用
if ! command -v rsync &> /dev/null; then
    echo -e "${RED}❌ 错误: rsync 未安装${NC}"
    echo -e "${YELLOW}请先安装 rsync:${NC}"
    echo -e "  macOS: brew install rsync"
    echo -e "  Linux: sudo apt-get install rsync"
    exit 1
fi

# 创建目标目录中的 prds 和 epics 目录（如果不存在）
# 这样确保这些目录存在但不会被覆盖
mkdir -p "$TARGET_CLAUDE_DIR/prds"
mkdir -p "$TARGET_CLAUDE_DIR/epics"

echo -e "${BLUE}📋 开始复制文件...${NC}"
echo ""

# 使用 rsync 复制文件
# --archive: 保留权限、时间戳等
# --verbose: 显示详细信息
# --human-readable: 人类可读的文件大小
# --ignore-times: 强制覆盖所有文件（不比较时间戳）
# --exclude: 排除指定目录
if rsync --archive \
         --verbose \
         --human-readable \
         --ignore-times \
         --exclude='prds/' \
         --exclude='epics/' \
         "$SOURCE_CLAUDE_DIR/" \
         "$TARGET_CLAUDE_DIR/"; then
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ 复制完成!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # 统计复制的内容
    echo -e "${BLUE}📊 复制统计:${NC}"
    
    # 统计文件数量（排除 prds 和 epics）
    FILE_COUNT=$(find "$TARGET_CLAUDE_DIR" -type f \
                 ! -path "*/prds/*" \
                 ! -path "*/epics/*" \
                 2>/dev/null | wc -l | tr -d ' ')
    
    # 统计目录数量（排除 prds 和 epics）
    DIR_COUNT=$(find "$TARGET_CLAUDE_DIR" -type d \
                ! -path "*/prds*" \
                ! -path "*/epics*" \
                2>/dev/null | wc -l | tr -d ' ')
    
    echo -e "  文件数: ${GREEN}$FILE_COUNT${NC}"
    echo -e "  目录数: ${GREEN}$DIR_COUNT${NC}"
    echo ""
    
    echo -e "${YELLOW}📝 提醒:${NC}"
    echo -e "  • prds/ 和 epics/ 目录已保留在目标项目中"
    echo -e "  • 所有其他文件已被强制覆盖（无论是否已存在）"
    echo -e "  • 脚本文件已复制，可能需要设置执行权限:"
    echo -e "    ${BLUE}chmod +x $TARGET_CLAUDE_DIR/scripts/**/*.sh${NC}"
    echo ""
    
    exit 0
else
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ 复制失败!${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi

