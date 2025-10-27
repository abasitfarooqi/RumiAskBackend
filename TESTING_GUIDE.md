# Testing Guide: Rumi Conversational System

## ✅ System Status

**Backend**: Running on `http://127.0.0.1:8001`  
**Frontend**: Available at `/frontend/index.html`  
**API Endpoint**: `/api/chat/ask-rumi`

---

## Recent Improvements

### 1. **Conciseness Enhancement** ✓
- ✅ Reduced max tokens from 200 → 120
- ✅ Added explicit word limit in prompt (2-3 sentences, max 60 words)
- ✅ Added post-processing to trim responses > 80 words
- ✅ Cleaner prompt with strict rules

### 2. **Better Quote Integration** ✓
- ✅ Clearer format for retrieved quotes
- ✅ Emotion context included
- ✅ Explicit instructions to use ONE quote naturally

---

## Testing Instructions

### 1. Open Frontend
```bash
# The server is already running, just open:
# http://127.0.0.1:8001/frontend/index.html
```

### 2. Test Queries

#### Test 1: Emotion Detection
**Query**: "I'm feeling sad"  
**Expected**: Short, empathetic response about sadness/transformation

#### Test 2: Love Query
**Query**: "I'm afraid to love deeply"  
**Expected**: Concise (60-80 words), about courage and surrender

#### Test 3: Self-Discovery
**Query**: "How do I find myself?"  
**Expected**: Poetic guidance about inner journey

#### Test 4: Purpose
**Query**: "What's the meaning of life?"  
**Expected**: Profound but brief answer

#### Test 5: Simple Greeting
**Query**: "hi"  
**Expected**: Short, warm greeting (2-3 sentences max)

---

## Response Quality Checks

### ✅ Good Response Should:
- Be 2-4 sentences (40-80 words)
- Start with Rumi-like address ("Ah, seeker," or "Beloved,")
- Include thematic quote naturally
- Be poetic and profound
- Address the emotion/query directly

### ❌ Bad Response Has:
- More than 100 words
- Repetitive content
- Generic advice (not Rumi-like)
- No emotional connection
- Rambling structure

---

## What to Watch For

### 1. **Length**
Response should be **concise** (2-3 sentences). If too long, the post-processor will trim it.

### 2. **Thematic Relevance**
Check if the response matches the theme of your query:
- Love queries → Love quotes
- Sadness queries → Transformation quotes
- Purpose queries → Destiny quotes

### 3. **Emotional Resonance**
Responses should acknowledge your emotional state:
- If you're sad → talks about transformation/meaning
- If you're afraid → talks about courage/surrender
- If you're seeking → talks about the journey

### 4. **Poetic Style**
Should sound like Rumi:
- Metaphorical
- Mystical
- Profound but accessible
- Uses natural language

---

## Example Test Flow

1. **Open frontend** → See Rumi interface
2. **Type**: "I'm feeling lost in life"
3. **Expected Response** (60-80 words):
   *"Ah, seeker—the path you tread is not lost, but finding you. The moment you give up the search, you are found. The map was written on the sole of your foot all along. Feel this longing as your prayer, for only a soul that remembers its home can weep."*

4. **Check quality**:
   - ✓ Length: ~40 words ✓
   - ✓ Theme: Self-discovery ✓
   - ✓ Emotion: addresses "lost" feeling ✓
   - ✓ Poetic: metaphorical and profound ✓

---

## Troubleshooting

### Problem: Responses too long
**Solution**: Already fixed with max_tokens=120 and post-processing

### Problem: Generic responses
**Cause**: Quotes not being retrieved properly  
**Solution**: Check logs for "Retrieved X quotes" message

### Problem: Not Rumi-like
**Cause**: Wrong model or prompt issues  
**Solution**: Check temperature=0.7 and prompt format

### Problem: No response
**Cause**: Model not loaded or API error  
**Solution**: Check server logs and model status

---

## Server Commands

```bash
# Start server
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8001 --reload

# Check server health
curl http://127.0.0.1:8001/health

# Test API directly
curl -X POST http://127.0.0.1:8001/api/chat/ask-rumi \
     -H "Content-Type: application/json" \
     -d '{"message": "What is love?"}'
```

---

## Success Criteria

✅ **Concise**: 2-4 sentences (40-80 words)  
✅ **Thematic**: Matches query theme  
✅ **Emotional**: Acknowledges user's emotion  
✅ **Poetic**: Rumi-like, metaphorical, profound  
✅ **Natural**: Flows well, not repetitive  

---

## Current Status

🟢 **Server**: Running  
🟢 **Knowledge Base**: 356 quotes loaded  
🟢 **Services**: All operational  
🟢 **API**: Responding  
🔧 **Conciseness**: Improved  

**Ready for testing! Try it in the frontend now.**

