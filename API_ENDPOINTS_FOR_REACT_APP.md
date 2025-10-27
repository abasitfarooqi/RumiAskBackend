# Ask Rumi API Endpoints for React Native App

## 📋 Complete Endpoint List

### Base URL
```
Local: http://127.0.0.1:8001
Tunnel: https://your-tunnel-url.ngrok.io (auto-detected)
```

---

## 🔗 Chat Endpoints

### 1. Send Message to Rumi
```
POST /api/chat/ask-rumi
Content-Type: application/json

Request Body:
{
  "message": "your message here",
  "model": "qwen3:0.6b",
  "temperature": 0.8,
  "conversation_id": "optional_conversation_id"
}

Response:
{
  "response": "Rumi's response text with tech specs",
  "model": "qwen3:0.6b",
  "conversation_id": "conv_123",
  "timestamp": "2025-10-27T19:01:37.051224",
  "tokens_used": 150,
  "inference_time": 2.33
}
```

### 2. Get All Conversations
```
GET /api/chat/conversations

Response:
{
  "conversations": [
    {
      "id": "conv_1",
      "created_at": "2025-10-27T10:00:00",
      "updated_at": "2025-10-27T11:00:00",
      "message_count": 15,
      "model": "qwen3:0.6b",
      "messages": [
        {
          "role": "user",
          "content": "message text",
          "timestamp": "..."
        },
        {
          "role": "assistant",
          "content": "response text",
          "timestamp": "..."
        }
      ]
    }
  ]
}
```

### 3. Delete Conversation
```
DELETE /api/chat/conversations/{conversation_id}

Response: 200 OK
```

### 4. Get Conversation by ID
```
GET /api/chat/conversations/{conversation_id}

Response: Same as conversation object above
```

---

## 🤖 Models Endpoints

### 5. Get All Models
```
GET /api/models/

Response:
{
  "models": [
    {
      "name": "qwen3:0.6b",
      "display_name": "Qwen 3 0.6B",
      "description": "Alibaba's Qwen 3 tiny model",
      "size_gb": 0.52,
      "provider": "ollama",
      "status": "available",
      "tags": ["chat", "tiny", "fast"],
      "capabilities": ["chat"],
      "last_updated": "2024-01-01T00:00:00Z"
    },
    {
      "name": "gemma3:270m",
      "display_name": "Gemma 3 270M",
      "description": "Google's ultra-lightweight model",
      "size_gb": 0.29,
      "provider": "ollama",
      "status": "available",
      "tags": ["chat", "tiny", "ultra-fast"],
      "capabilities": ["chat"],
      "last_updated": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 6. Download Model
```
POST /api/models/download
Content-Type: application/json

Request Body:
{
  "model": "llama3.2:3b",
  "priority": "normal"
}

Response: 200 OK
```

### 7. Test Model
```
POST /api/models/{model_name}/test

Response:
{
  "test_passed": true,
  "message": "Test successful"
}
```

---

## ⚙️ Settings Endpoints

### 8. Get Behavior Settings
```
GET /api/chat/behavior-settings

Response:
{
  "status": "success",
  "config": {
    "conversation_history_depth": 2,
    "max_tokens_wisdom": 350,
    "max_tokens_empathetic": 280,
    "max_tokens_casual": 220,
    "temperature": 0.8,
    "max_quotes_retrieved": 3,
    "max_quotes_for_empathetic": 2,
    "prompt_templates": {
      "casual": {...},
      "empathetic": {...},
      "wisdom": {...}
    },
    "quote_formatting": {...},
    "response_guidelines": {...},
    "post_processing": {...}
  }
}
```

### 9. Save Behavior Settings
```
POST /api/chat/behavior-settings
Content-Type: application/json

Request Body:
{
  "conversation_history_depth": 2,
  "max_tokens_wisdom": 350,
  "max_tokens_empathetic": 280,
  "max_tokens_casual": 220,
  "temperature": 0.8,
  "max_quotes_retrieved": 3
}

Response:
{
  "status": "success",
  "message": "Settings updated"
}
```

### 10. Get Settings
```
GET /api/chat/settings

Response:
{
  "historyDepth": 2,
  "maxTokensWisdom": 350,
  "maxTokensEmpathy": 280,
  "maxTokensCasual": 220,
  "temperature": 0.8,
  "maxQuotes": 3
}
```

### 11. Save Settings
```
POST /api/chat/settings
Content-Type: application/json

Request Body: Same as above

Response: 200 OK
```

---

## 📊 System Endpoints

### 12. Get System Info
```
GET /api/system/info

Response:
{
  "platform": "Darwin",
  "python_version": "3.11.0",
  "torch_version": "2.1.0",
  "cpu_count": 8,
  "memory_total": 16.0,
  "memory_available": 8.5
}
```

### 13. Health Check
```
GET /api/chat/health

Response:
{
  "status": "healthy",
  "active_conversations": 1,
  "available_models": 3
}
```

---

## 🎨 Frontend Static Files

### 14. Get Frontend HTML
```
GET /frontend/index.html

Returns: Complete HTML page
```

### 15. Get Frontend JavaScript
```
GET /frontend/app.js

Returns: All JavaScript functionality
```

### 16. Get Frontend CSS
```
GET /frontend/styles.css

Returns: All styling
```

---

## 📱 React Native Implementation

### API Base URL Setup
```javascript
const API_BASE = Platform.select({
  ios: 'http://localhost:8001',
  android: 'http://10.0.2.2:8001',
  // For tunnel, detect from environment or config
  default: 'http://127.0.0.1:8001'
});
```

### Example API Calls

```javascript
// 1. Send message
const response = await fetch(`${API_BASE}/api/chat/ask-rumi`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: userMessage,
    model: selectedModel,
    conversation_id: currentConvId
  })
});

// 2. Get all models
const models = await fetch(`${API_BASE}/api/models/`);

// 3. Get conversations
const conversations = await fetch(`${API_BASE}/api/chat/conversations`);

// 4. Delete conversation
await fetch(`${API_BASE}/api/chat/conversations/${convId}`, {
  method: 'DELETE'
});

// 5. Get behavior settings
const settings = await fetch(`${API_BASE}/api/chat/behavior-settings`);

// 6. Save behavior settings
await fetch(`${API_BASE}/api/chat/behavior-settings`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(newSettings)
});

// 7. Get system info
const systemInfo = await fetch(`${API_BASE}/api/system/info`);

// 8. Health check
const health = await fetch(`${API_BASE}/api/chat/health`);
```

---

## 🔑 Authentication

Currently: **No authentication required**

For production, you may want to add:
- API keys
- JWT tokens
- OAuth

---

## 📊 Response Format Standards

### Success Response
```json
{
  "response": "data",
  "status": "success"
}
```

### Error Response
```json
{
  "error": "Error message",
  "detail": "Detailed error description"
}
```

### Tech Specs in Chat Response
Every chat response includes:
```
--- TECH SPECS ---
Mode: 💬 Casual Chat / 🔮 Rumi Wisdom / ❤️ Empathetic Support
Model: qwen3:0.6b
Quotes used: 3
Inference time: 2.33s
Tokens generated: 150
Prompt length: 2450 chars (includes 2 previous messages)
Max tokens: 350
Temperature: 0.8
Estimated GPU usage: 300 MB
Estimated cost: $0.000015
📜 Sources: SPH011, DLV003, DLV010
```

---

## ✅ Complete Endpoint Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/chat/ask-rumi` | Send message, get response |
| GET | `/api/chat/conversations` | Get all conversations |
| GET | `/api/chat/conversations/{id}` | Get specific conversation |
| DELETE | `/api/chat/conversations/{id}` | Delete conversation |
| GET | `/api/chat/behavior-settings` | Get LLM settings |
| POST | `/api/chat/behavior-settings` | Save LLM settings |
| GET | `/api/chat/settings` | Get app settings |
| POST | `/api/chat/settings` | Save app settings |
| GET | `/api/chat/health` | Health check |
| GET | `/api/models/` | Get all models |
| POST | `/api/models/download` | Download model |
| POST | `/api/models/{name}/test` | Test model |
| GET | `/api/system/info` | Get system info |

---

## 🎯 Priority Endpoints for React Native

### Critical (Must Implement)
1. `POST /api/chat/ask-rumi` - Chat functionality
2. `GET /api/models/` - Model selection
3. `GET /api/chat/conversations` - History
4. `DELETE /api/chat/conversations/{id}` - Delete

### Important (Should Implement)
5. `GET /api/chat/behavior-settings` - Load config
6. `POST /api/chat/behavior-settings` - Save config
7. `GET /api/chat/health` - Connection check
8. `GET /api/system/info` - System display

### Nice to Have
9. `POST /api/models/download` - Download models
10. `POST /api/models/{name}/test` - Test models
11. `GET /api/chat/conversations/{id}` - Load specific conversation

---

## 📝 Notes for React Native

1. **Auto-detect base URL:**
   - Check if running on tunnel
   - Adjust API calls accordingly

2. **Store conversation_id:**
   - Keep track of current conversation
   - Pass it with each message

3. **Handle long responses:**
   - Responses include tech specs
   - Parse and display separately if needed

4. **Model filtering:**
   - Filter to `status: "available"`
   - Exclude models with "whisper" in name
   - Only show models with "chat" capability

5. **Error handling:**
   - Always check for errors
   - Show user-friendly messages
   - Retry failed requests

6. **Settings persistence:**
   - Use AsyncStorage
   - Load on app start
   - Auto-save on changes

---

All endpoints are CORS-enabled and ready for cross-origin requests from your React Native app!

