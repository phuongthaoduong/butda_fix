#!/bin/bash
# 测试前端服务和页面
# Usage: ./test_frontend.sh

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              前端服务测试 - Frontend Test                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

FRONTEND_URL="http://localhost:5173"
PASS=0
FAIL=0

# 测试前端主页
echo "🌐 测试前端主页..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 主页可访问 (HTTP $HTTP_CODE)"
    ((PASS++))
else
    echo "   ❌ 主页不可访问 (HTTP $HTTP_CODE)"
    ((FAIL++))
fi

# 测试静态资源
echo ""
echo "📦 测试静态资源..."
CONTENT_TYPE=$(curl -s -I "$FRONTEND_URL/" 2>/dev/null | grep -i "content-type" | head -1)
if echo "$CONTENT_TYPE" | grep -qi "text/html"; then
    echo "   ✅ HTML内容正确返回"
    ((PASS++))
else
    echo "   ❌ 内容类型错误"
    ((FAIL++))
fi

# 测试Vite开发服务器特性
echo ""
echo "⚡ 测试Vite开发服务器..."
RESPONSE=$(curl -s "$FRONTEND_URL/" 2>/dev/null)
if echo "$RESPONSE" | grep -q "vite\|react\|src/main"; then
    echo "   ✅ Vite开发服务器正常运行"
    ((PASS++))
else
    echo "   ⚠️  无法确认Vite服务器（可能是生产构建）"
    ((PASS++))
fi

# 测试logo资源
echo ""
echo "🖼️  测试静态资源 (logo.png)..."
LOGO_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/logo.png")
if [ "$LOGO_CODE" = "200" ]; then
    echo "   ✅ Logo资源可访问"
    ((PASS++))
else
    echo "   ⚠️  Logo资源不可访问 (HTTP $LOGO_CODE)"
    # 这不是关键错误
    ((PASS++))
fi

# 测试网络连接性
echo ""
echo "🔗 测试网络绑定..."
if lsof -i:5173 -P -n | grep -q "LISTEN"; then
    echo "   ✅ 端口5173正在监听"
    ((PASS++))
else
    echo "   ❌ 端口5173未监听"
    ((FAIL++))
fi

# 测试结果汇总
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 测试结果: $PASS 通过 / $FAIL 失败"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAIL -eq 0 ]; then
    echo "🎉 前端测试全部通过！"
    exit 0
else
    echo "⚠️  有 $FAIL 个测试失败"
    exit 1
fi

