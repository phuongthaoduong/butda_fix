#!/bin/bash
# 测试所有服务的运行状态
# Usage: ./test_services.sh

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              服务状态测试 - Service Status Test              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0

# 测试工具服务器 (8000端口)
echo "🔧 测试工具服务器 (Port 8000)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "404\|200"; then
    echo "   ✅ 工具服务器运行中"
    ((PASS++))
else
    echo "   ❌ 工具服务器未运行"
    ((FAIL++))
fi

# 测试后端API (8001端口)
echo ""
echo "🚀 测试后端API (Port 8001)..."
HEALTH_RESPONSE=$(curl -s http://localhost:8001/api/health 2>/dev/null)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    echo "   ✅ 后端API运行中且健康"
    ((PASS++))
else
    echo "   ❌ 后端API未运行或不健康"
    ((FAIL++))
fi

# 测试前端服务 (5173端口)
echo ""
echo "💻 测试前端服务 (Port 5173)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/ | grep -q "200"; then
    echo "   ✅ 前端服务运行中"
    ((PASS++))
else
    echo "   ❌ 前端服务未运行"
    ((FAIL++))
fi

# 测试API文档
echo ""
echo "📚 测试API文档 (Swagger UI)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/docs | grep -q "200"; then
    echo "   ✅ API文档可访问"
    ((PASS++))
else
    echo "   ❌ API文档不可访问"
    ((FAIL++))
fi

# 测试结果汇总
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 测试结果: $PASS 通过 / $FAIL 失败"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAIL -eq 0 ]; then
    echo "🎉 所有服务测试通过！"
    exit 0
else
    echo "⚠️  有 $FAIL 个服务测试失败"
    exit 1
fi

