# 🚀 Quick Start - Ask Rumi Backend

## How to Start the Server

### 1. **Kill All Running Instances** (if any)
```bash
pkill -9 uvicorn
```

### 2. **Navigate to Project Directory**
```bash
cd /Users/abdulbasit/Documents/AppsAI/askrumi/RumiBackend
```

### 3. **Activate Virtual Environment**
```bash
source venv/bin/activate
```

### 4. **Start the Server**
```bash
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

## 📍 Server URLs

- **API Base**: http://127.0.0.1:8001
- **Frontend**: http://127.0.0.1:8001/frontend
- **API Docs**: http://127.0.0.1:8001/docs

## ✅ What Was Implemented

### 🎯 Fully Configurable System
- **No hardcoded values** - Everything in JSON
- **Frontend JSON editor** - Edit all prompts, settings, behaviors
- **Dynamic loading** - All settings loaded at runtime

### 📝 Conversation History
- **Load conversations** - Click any conversation in History tab
- **Delete conversations** - Click 🗑️ button
- **Preview messages** - See first user message as preview
- **Full conversation restore** - All messages load correctly

### 🧠 LLM Behavior Settings (Frontend Editable)
- Token limits per mode (Wisdom/Empathetic/Casual)
- Temperature control
- Conversation history depth
- Max quotes retrieved
- **Prompt templates** (casual, empathetic, wisdom)
- **Quote formatting** options
- **Post-processing** markers and filters

### 🎨 UI Improvements
- Clean conversation history sidebar
- Delete buttons on conversations
- Message previews
- Better meta information display

## 🔧 Configuration Files

All settings editable via frontend at ⚙️ Settings → Prompt Templates:
- `data/llm_behavior_config.json` - All LLM behaviors
- Loaded dynamically by `services/behavior_config.py`
- Applied by `services/rumi_responder.py`

## 🎮 Quick Commands

### Using rumi.sh (Easiest)
```bash
# Start server
./rumi.sh start

# Stop server
./rumi.sh stop

# Restart server
./rumi.sh restart

# Check status
./rumi.sh status

# Kill all processes
./rumi.sh kill
```

### Or use traditional methods
```bash
# Kill server
pkill -9 uvicorn

# Start server
cd /Users/abdulbasit/Documents/AppsAI/askrumi/RumiBackend
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

## 📊 Verify Everything Works

```bash
# Check API
curl http://127.0.0.1:8001/api/chat/behavior-settings | python3 -m json.tool

# Test chat
curl -X POST http://127.0.0.1:8001/api/chat/ask-rumi \
  -H "Content-Type: application/json" \
  -d '{"message": "hi", "model": "gemma3:270m"}' | python3 -m json.tool
```

