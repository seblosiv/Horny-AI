#!/bin/bash

# Test script for B2B Chat API
# Make sure to set your API_KEY and BOT_ID

set -e

API_URL="http://localhost:8000"
API_KEY="${API_KEY:-YOUR_API_KEY_HERE}"
BOT_ID="${BOT_ID:-YOUR_BOT_ID_HERE}"

echo "🧪 B2B Chat API Test Script"
echo "============================"
echo ""

if [ "$API_KEY" = "YOUR_API_KEY_HERE" ] || [ "$BOT_ID" = "YOUR_BOT_ID_HERE" ]; then
    echo "❌ Please set API_KEY and BOT_ID environment variables"
    echo ""
    echo "Example:"
    echo "  export API_KEY='sk_live_...'"
    echo "  export BOT_ID='uuid-here'"
    echo "  ./examples/test_api.sh"
    exit 1
fi

echo "📡 Testing API at: $API_URL"
echo ""

# Test 1: Health check
echo "1️⃣  Health check..."
curl -s "$API_URL/health" | python3 -m json.tool
echo ""
echo ""

# Test 2: Non-streaming chat
echo "2️⃣  Non-streaming chat..."
curl -s -X POST "$API_URL/v1/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"bot_id\": \"$BOT_ID\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"Say hello in one sentence.\"}
    ],
    \"stream\": false
  }" | python3 -m json.tool
echo ""
echo ""

# Test 3: Streaming chat (first 20 lines)
echo "3️⃣  Streaming chat (first few lines)..."
curl -s -N -X POST "$API_URL/v1/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"bot_id\": \"$BOT_ID\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"Count from 1 to 5.\"}
    ],
    \"stream\": true
  }" | head -n 20
echo ""
echo ""

echo "✅ Tests complete!"
