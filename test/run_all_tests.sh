#!/bin/bash
# 运行所有测试
# Usage: ./run_all_tests.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Being-Up-To-Date Assistant - 完整测试套件            ║"
echo "║                Full Test Suite                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

TOTAL_PASS=0
TOTAL_FAIL=0

# 运行服务状态测试
echo ""
echo "▶️  运行服务状态测试..."
echo "────────────────────────────────────────────────────────────────"
bash ./test_services.sh
if [ $? -eq 0 ]; then
    ((TOTAL_PASS++))
else
    ((TOTAL_FAIL++))
fi

# 运行前端测试
echo ""
echo "▶️  运行前端测试..."
echo "────────────────────────────────────────────────────────────────"
bash ./test_frontend.sh
if [ $? -eq 0 ]; then
    ((TOTAL_PASS++))
else
    ((TOTAL_FAIL++))
fi

# 运行API测试
echo ""
echo "▶️  运行API测试..."
echo "────────────────────────────────────────────────────────────────"
python3 ./test_api.py
if [ $? -eq 0 ]; then
    ((TOTAL_PASS++))
else
    ((TOTAL_FAIL++))
fi

# 最终汇总
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                      测试汇总报告                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 测试套件结果: $TOTAL_PASS 通过 / $TOTAL_FAIL 失败"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

if [ $TOTAL_FAIL -eq 0 ]; then
    echo "═══════════════════════════════════════════════════════════════"
    echo "  🎉 所有测试套件通过！系统运行正常。"
    echo "═══════════════════════════════════════════════════════════════"
    exit 0
else
    echo "═══════════════════════════════════════════════════════════════"
    echo "  ⚠️  有 $TOTAL_FAIL 个测试套件失败，请检查相关服务"
    echo "═══════════════════════════════════════════════════════════════"
    exit 1
fi

