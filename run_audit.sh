#!/bin/bash
###############################################################################
# Linux系统进程与端口自动分析 - 一键运行脚本
# 功能：自动执行数据收集和PDF报告生成
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$1" = "edit-whitelist" ]; then
    python3 "${SCRIPT_DIR}/whitelist_editor.py"
    exit 0
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}   Linux系统进程与端口自动分析工具${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}警告: 未使用root权限运行，部分信息可能无法获取${NC}"
    echo "建议运行方式: sudo bash run_audit.sh"
    echo ""
fi

# 检查依赖
echo -e "${GREEN}[检查依赖]${NC}"

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3，请先安装${NC}"
    exit 1
fi
echo "  ✓ Python3 已安装"

# 检查reportlab (用于PDF生成)
if ! python3 -c "import reportlab" 2>/dev/null; then
    echo -e "${YELLOW}警告: 未找到reportlab库，PDF生成可能失败${NC}"
    echo "  建议安装: pip3 install reportlab"
fi

# 检查必要的命令
for cmd in ps ss netstat; do
    if command -v $cmd &> /dev/null; then
        echo "  ✓ $cmd 已安装"
    else
        echo "  ⚠ $cmd 未安装"
    fi
done

echo ""

# 步骤1: 运行数据收集脚本
echo -e "${GREEN}[步骤1/2] 正在收集系统数据...${NC}"
JSON_PATH=$(bash "${SCRIPT_DIR}/linux_process_audit.sh" 2>/dev/null | tail -1)

if [ -z "$JSON_PATH" ] || [ ! -f "$JSON_PATH" ]; then
    echo -e "${RED}错误: 数据收集失败${NC}"
    exit 1
fi

echo -e "  数据文件: ${JSON_PATH}"
echo ""

# 步骤2: 生成PDF报告
echo -e "${GREEN}[步骤2/2] 正在生成PDF报告...${NC}"

python3 "${SCRIPT_DIR}/generate_pdf_report.py" "$JSON_PATH"

# 查找生成的PDF文件
OUTPUT_DIR=$(dirname "$JSON_PATH")
PDF_FILE=$(ls -t "${OUTPUT_DIR}"/linux_process_audit_report_*.pdf 2>/dev/null | head -1)

echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}   巡检完成!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""

if [ -n "$PDF_FILE" ] && [ -f "$PDF_FILE" ]; then
    echo -e "${GREEN}PDF报告已生成:${NC}"
    echo "  $PDF_FILE"
    echo ""
    echo "报告大小: $(du -h "$PDF_FILE" | cut -f1)"
    
    # 尝试复制到脚本目录
    REPORT_NAME=$(basename "$PDF_FILE")
    if [ "$OUTPUT_DIR" != "$SCRIPT_DIR" ]; then
        cp "$PDF_FILE" "${SCRIPT_DIR}/${REPORT_NAME}" 2>/dev/null || true
        echo "报告已复制到: ${SCRIPT_DIR}/${REPORT_NAME}"
    fi
else
    echo -e "${YELLOW}PDF生成可能失败，请检查HTML文件:${NC}"
    ls -la "${OUTPUT_DIR}"/*.html 2>/dev/null || echo "未找到HTML文件"
fi

echo ""
echo "原始数据位置: $OUTPUT_DIR"
echo ""
