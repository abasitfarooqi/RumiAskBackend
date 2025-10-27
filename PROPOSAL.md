# Rumi-Based Conversational App - Implementation Proposal

## Executive Summary
Transform the current generic LLM chat into an intelligent Rumi conversational system that understands queries semantically, matches them to appropriate quotes from the knowledge base, and responds poetically in Rumi's style.

---

## Phase 1: Knowledge Base Conversion

### 1.1 Convert Markdown to Structured JSON
**Target Structure:**
```json
{
  "id": "DLV001",
  "core_pillar": "I. The Heart's Desire (Love & Union)",
  "primary_theme": "Divine Love",
  "quote": "The moment you give up the search, you are found...",
  "micro_tags": ["Ecstasy", "Worship", "Presence", "Inwardness"],
  "emotion_tags": ["realization", "surrender", "enlightenment", "recognition"],
  "source_ref": "Masnavi I: 3052-3067",
  "quote_type": "Short-Quote",
  "query_intent": [
    "Where can I find myself?",
    "I've been searching for meaning",
    "I feel lost in my spiritual journey"
  ]
}
```

### 1.2 Conversion Script
- Parse both `Knowledge Data.md` and `Knowledge DATAset2.md`
- Extract all 9 themes with ~40 quotes each (~360 total quotes)
- Map to JSON structure with intelligent emotion tagging
- Store in `data/rumi_knowledge_base.json`

---

## Phase 2: Intelligent Query Processing

### 2.1 Components to Build
1. **Query Analyzer** (`services/query_analyzer.py`)
   - Semantic search across quote text
   - Tag-based matching (micro_tags, emotion_tags, themes)
   - Intent detection (question type, emotional state)

2. **Quote Retriever** (`services/quote_retriever.py`)
   - Fetch 3-5 most relevant quotes based on query
   - Score by theme relevance + emotion match
   - Extract context from conversation history

3. **Response Generator** (`services/rumi_responder.py`)
   - Craft poetic responses using retrieved quotes
   - Blend multiple quotes when relevant
   - Maintain Rumi's voice (concise, metaphorical, profound)

### 2.2 Flow Diagram
```
User Query → Query Analyzer → Intent + Emotions + Themes
                ↓
            Quote Retriever → Top 3-5 Quotes + Context
                ↓
         Response Generator → Rumi-Style Response
```

---

## Phase 3: Enhanced Prompt Engineering

### 3.1 System Prompt Template
```python
RUMI_SYSTEM_PROMPT = """You are Jalaluddin Rumi, the 13th-century Persian mystic and poet. 
Your responses are:
- Concise and profound (50-150 words)
- Poetic and metaphorical
- Thematically aligned with the attached quotes
- Compassionate yet direct
- Reflective of mystical wisdom

Context Quotes:
{retrieved_quotes}

User's Current State:
{emotion_detected}

Respond as Rumi would:"""
```

### 3.2 Prompt Enhancement
- Inject retrieved quotes into context
- Add emotional context from user query
- Include conversation history themes

---

## Phase 4: API Integration

### 4.1 Modified Endpoints
- **Keep**: Existing `/api/chat/send` and `/api/chat/stream`
- **Enhance**: `/api/chat/ask-rumi` with intelligent retrieval
- **Add**: `/api/rumi/query-analyze` for testing query understanding

### 4.2 New Route Structure
```python
@router.post("/ask-rumi")
async def ask_rumi(request: ChatRequest):
    # 1. Analyze query
    intent = analyze_query(request.message)
    
    # 2. Retrieve relevant quotes
    quotes = retrieve_quotes(intent)
    
    # 3. Generate Rumi response
    response = generate_rumi_response(quotes, request.message)
    
    return response
```

---

## Technical Stack Needed

### Dependencies to Add
```bash
# Semantic search (simple approach first)
pip install sentence-transformers  # or use TF-IDF with sklearn

# Text processing
pip install nltk
pip install spacy

# JSON handling (already have)
```

### File Structure
```
/services
  ├── query_analyzer.py      # Intent + emotion detection
  ├── quote_retriever.py     # Semantic search
  ├── rumi_responder.py      # Response generation
  └── rumi_knowledge.py      # Knowledge base loader

/data
  ├── rumi_knowledge_base.json  # All quotes (NEW)
  └── rumi_quotes.json          # Keep for backwards compat

/utils
  ├── text_processor.py      # NLP utilities
  └── embedding_generator.py  # Semantic embeddings
```

---

## Example Interaction

### Before (Current):
**User:** "What is the meaning of life?"
**App:** *[Generic philosophical response like any LLM]*

### After (Proposed):
**User:** "What is the meaning of life?"
**App (As Rumi):** 
*"Ah, seeker—the purpose of your life is not to seek the answer in books or distant shores, but to come to the point where nothing remains in you except the Beloved. Cleanse everything else away. The meaning is not found, but felt: in the way you love, how you serve, and the breath that moves within you. Your task is simply to become what you already are."*

---

## Success Criteria

1. **Semantic Understanding**: Correctly identifies theme even with diverse phrasings
2. **Emotional Resonance**: Detects user emotion and responds appropriately
3. **Poetic Style**: Responses feel authentically Rumi-like
4. **Thematic Consistency**: Matches quotes to query intent
5. **Performance**: Response time < 3 seconds (local inference)

---

## Implementation Approach

### Option A: Lightweight (Recommended for MVP)
- Use simple keyword/TF-IDF matching for quote retrieval
- Pattern-based emotion detection
- Template-based response generation
- **Pros**: Fast, no external dependencies, works offline
- **Cons**: Less sophisticated matching

### Option B: Advanced (Future Enhancement)
- Sentence transformers for semantic embeddings
- Fine-tuned emotion classification
- Retrieval-Augmented Generation with proper vector DB
- **Pros**: More accurate, scalable
- **Cons**: Larger dependencies, requires fine-tuning

---

## Questions for You

1. **Which approach** (A or B) for Phase 2?
2. **Response Style**: 
   - A) Quote verbatim and then expand
   - B) Weave quotes into new poetic prose
   - C) Hybrid
3. **Quote Selection**: Top 1, 3, or 5 quotes per response?
4. **Priority**: Which theme should we perfect first? (Love, Wisdom, Self-Discovery?)

---

## Next Steps

**ON HOLD until your approval:**
1. Convert knowledge base to JSON
2. Build query analyzer
3. Implement quote retriever
4. Enhance `/ask-rumi` endpoint
5. Test with various query types

**Awaiting your GO signal to proceed.**

