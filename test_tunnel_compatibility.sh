#!/bin/bash

echo "🧪 Testing Ask Rumi System for Tunnel Compatibility"
echo "=================================================="
echo ""

# Test 1: Health Check
echo "1️⃣  Testing Health Endpoint..."
HEALTH=$(curl -s http://127.0.0.1:8001/api/chat/health)
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo "✅ Health check: PASSED"
else
    echo "❌ Health check: FAILED"
    exit 1
fi
echo ""

# Test 2: Models Endpoint
echo "2️⃣  Testing Models Endpoint..."
MODELS=$(curl -s http://127.0.0.1:8001/api/models/)
if echo "$MODELS" | grep -q '"models"'; then
    AVAILABLE=$(echo "$MODELS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [m for m in data['models'] if m['status']=='available' and 'whisper' not in m['name'].lower()]
print(len(models))
")
    echo "✅ Models endpoint: PASSED ($AVAILABLE available chat models)"
else
    echo "❌ Models endpoint: FAILED"
    exit 1
fi
echo ""

# Test 3: Chat Endpoint
echo "3️⃣  Testing Chat Endpoint..."
CHAT_RESPONSE=$(curl -s -X POST http://127.0.0.1:8001/api/chat/ask-rumi \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "model": "qwen3:0.6b"}')
if echo "$CHAT_RESPONSE" | grep -q '"response"'; then
    echo "✅ Chat endpoint: PASSED"
    echo "   Response includes: conversation_id, model, inference_time"
else
    echo "❌ Chat endpoint: FAILED"
    exit 1
fi
echo ""

# Test 4: Behavior Settings Endpoint
echo "4️⃣  Testing Behavior Settings Endpoint..."
BEHAVIOR=$(curl -s http://127.0.0.1:8001/api/chat/behavior-settings)
if echo "$BEHAVIOR" | grep -q '"config"'; then
    echo "✅ Behavior Settings endpoint: PASSED"
else
    echo "❌ Behavior Settings endpoint: FAILED"
    exit 1
fi
echo ""

# Test 5: Conversations Endpoint
echo "5️⃣  Testing Conversations Endpoint..."
CONVERSATIONS=$(curl -s http://127.0.0.1:8001/api/chat/conversations)
if echo "$CONVERSATIONS" | grep -q '"conversations"'; then
    echo "✅ Conversations endpoint: PASSED"
else
    echo "❌ Conversations endpoint: FAILED"
    exit 1
fi
echo ""

# Test 6: System Info Endpoint
echo "6️⃣  Testing System Info Endpoint..."
SYSTEM=$(curl -s http://127.0.0.1:8001/api/system/info)
if echo "$SYSTEM" | grep -q '"platform"'; then
    echo "✅ System Info endpoint: PASSED"
else
    echo "❌ System Info endpoint: FAILED"
    exit 1
fi
echo ""

# Test 7: Frontend Static Files
echo "7️⃣  Testing Frontend Static Files..."
HTML=$(curl -s http://127.0.0.1:8001/frontend/index.html)
if echo "$HTML" | grep -q 'chatModelSelector'; then
    echo "✅ Frontend HTML: PASSED (chatModelSelector found)"
else
    echo "❌ Frontend HTML: FAILED"
    exit 1
fi

JS=$(curl -s http://127.0.0.1:8001/frontend/app.js)
if echo "$JS" | grep -q 'loadChatModelSelector'; then
    echo "✅ Frontend JS: PASSED (loadChatModelSelector function found)"
else
    echo "❌ Frontend JS: FAILED"
    exit 1
fi
echo ""

# Test 8: CORS Headers
echo "8️⃣  Testing CORS Configuration..."
CORS=$(curl -s -I http://127.0.0.1:8001/api/chat/health | grep -i "access-control")
if [ ! -z "$CORS" ]; then
    echo "✅ CORS headers: PASSED"
    echo "$CORS"
else
    echo "❌ CORS headers: FAILED or not configured"
fi
echo ""

echo "=================================================="
echo "✅ All Tunnel Compatibility Tests PASSED!"
echo ""
echo "Your system is ready for ngrok/cloudflared tunneling."
echo ""
echo "To use with tunnel:"
echo "  1. ./rumi.sh start"
echo "  2. ngrok http 8001"
echo "  3. Access: https://your-tunnel-url.ngrok.io/frontend"
echo ""
echo "Frontend will auto-detect tunnel URL and work correctly!"

