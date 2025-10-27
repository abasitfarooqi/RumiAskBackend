# Rumi Conversational App - Architecture & Flow

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                           │
│  (Frontend: React/Web or Mobile App)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 API LAYER (FastAPI)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  /api/chat/ask-rumi                                     │ │
│  │  - Receives user query                                  │ │
│  │  - Manages conversation context                         │ │
│  │  - Returns Rumi-style response                          │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌───────────────────────────────┐
        │   QUERY PROCESSING PIPELINE    │
        └───────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                  │
        ▼                                  ▼
┌───────────────┐              ┌──────────────────────┐
│ QUERY ANALYZER│              │   QUOTE RETRIEVER     │
│               │              │                       │
│ - Intent      │────matches──▶│ - Semantic Search     │
│ - Emotion     │              │ - Tag Matching        │
│ - Theme       │              │ - Score Quotes        │
│ - Keywords    │              │ - Context Awareness   │
└───────────────┘              └───────────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────┐
                         │   RESPONSE GENERATOR        │
                         │                             │
                         │ - Rumi System Prompt        │
                         │ - Inject Retrieved Quotes   │
                         │ - Poetic Blending           │
                         │ - Maintain Voice            │
                         └─────────────────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────┐
                         │   LOCAL LLM (phi3-mini)   │
                         │                             │
                         │ - Generates Final Response  │
                         │ - Maintains Rumi Style     │
                         │ - Returns to User           │
                         └─────────────────────────────┘
```

## Data Flow Example

### Example 1: User asks about love
```
User Query: "I'm afraid to love deeply, should I open my heart?"

STEP 1: Query Analyzer
├─ Intent: Seeking guidance on vulnerability in love
├─ Emotion: "fear", "caution", "hesitance"
├─ Theme: Human Love / Divine Love
└─ Keywords: [love, afraid, heart, open]

STEP 2: Quote Retriever
├─ Searches knowledge base for quotes matching:
│  ├─ Love theme
│  ├─ Courage/fear tags
│  ├─ Heart/vulnerability tags
│  └─ Risk/devotion tags
├─ Returns top matches:
│  ├─ DLV002: "Do not seek to be safe... be a moth..."
│  ├─ HLV014: "Love rests on no foundation..."
│  └─ SDI005: "Sell your cleverness for bewilderment..."
└─ Scores: 0.92, 0.88, 0.76

STEP 3: Response Generator
├─ Creates prompt with retrieved quotes
├─ Adds emotional context: "user feels fear about love"
├─ Generates Rumi response weaving quotes
└─ Returns poetic, encouraging answer

RESPONSE:
"Ah, beloved—your fear itself is the doorway. Do not seek 
to be safe. Seek only to be the moth who has surrendered 
to the fire. The heart that hesitates lives in a shadow 
of the truth. Love rests on no foundation; it is an 
endless ocean. Dive in, for the cage of caution is the 
only prison keeping you from the vastness of what is 
already within you."
```

### Example 2: User asks about purpose
```
User Query: "What's my purpose? I feel lost."

STEP 1: Query Analyzer
├─ Intent: Seeking meaning and direction
├─ Emotion: "lost", "uncertainty", "seeking"
├─ Theme: Purpose & Destiny / Self-Discovery
└─ Keywords: [purpose, lost, meaning, direction]

STEP 2: Quote Retriever
├─ Searches for:
│  ├─ Purpose/meaning themes
│  ├─ Calling/destiny tags
│  ├─ Lost/searching tags
│  └─ Inner journey tags
├─ Returns:
│  ├─ PDS001: "Do not worry about the purpose..."
│  ├─ SDI001: "Your task is not to seek the Path..."
│  └─ SDI004: "Do not travel from shore to shore..."
└─ Scores: 0.95, 0.91, 0.85

STEP 3: Response Generator
RESPONSE:
"The purpose you seek is already planted in your heart like 
a seed, waiting for you to stop searching and simply tend 
to what grows. Do not travel from shore to shore in search 
of water—the answer to all your questions is the ocean of 
your own being. Your task is not to seek the Path, but to 
find the thousands of walls you have built against it 
inside your own heart. Tear them down."
```

## Component Details

### 1. Query Analyzer (`services/query_analyzer.py`)
```python
class QueryAnalyzer:
    def analyze(self, query: str) -> QueryIntent:
        """
        Extract:
        - Primary intent (question, seeking, sharing)
        - Emotions (detected keywords + sentiment)
        - Themes (from keywords matching pillar themes)
        - Keywords (for semantic search)
        """
        pass
```

**Detection Methods:**
- Keyword matching for themes
- Pattern matching for emotions
- Simple NLP for intent
- Conversation history for context

### 2. Quote Retriever (`services/quote_retriever.py`)
```python
class QuoteRetriever:
    def retrieve(self, intent: QueryIntent) -> List[Quote]:
        """
        Retrieve quotes by:
        1. Tag overlap (micro_tags, emotion_tags)
        2. Semantic similarity (simple embedding or TF-IDF)
        3. Theme match (primary_theme)
        4. Context (conversation history)
        
        Returns top 3-5 quotes with scores
        """
        pass
```

**Retrieval Strategy:**
- Primary: Tag matching (fast, reliable)
- Secondary: Semantic similarity (fallback)
- Tertiary: Theme browsing (if no direct match)
- Context: Conversation history themes

### 3. Response Generator (`services/rumi_responder.py`)
```python
class RumiResponder:
    def generate_response(
        self, 
        query: str,
        quotes: List[Quote],
        intent: QueryIntent
    ) -> str:
        """
        Craft Rumi response:
        1. Select best quote(s) from retrieved
        2. Create system prompt with quote context
        3. Generate poetic response
        4. Ensure conciseness and authenticity
        """
        pass
```

**Prompt Template:**
```
You are Rumi. Respond to: "{query}"

Context quotes:
- "{quote1}"
- "{quote2}"

User's emotion: {emotion}

Keep it:
- Concise (50-150 words)
- Poetic and metaphorical
- Thematically aligned
- Compassionate and direct
```

## Storage Structure

```
data/
├── rumi_knowledge_base.json    # Main KB (360 quotes)
├── rumi_quotes.json            # Backwards compat (15 quotes)
└── embeddings_cache.json       # Optional: pre-computed embeddings

services/
├── query_analyzer.py
├── quote_retriever.py
├── rumi_responder.py
└── knowledge_loader.py

routes/
└── chat.py                      # Enhanced with Rumi logic
```

## API Endpoints

### Enhanced `/api/chat/ask-rumi`
```python
POST /api/chat/ask-rumi
{
  "message": "How do I find myself?",
  "model": "phi3-mini",
  "conversation_id": "conv_123"
}

Response:
{
  "response": "...Rumi quote and elaboration...",
  "theme": "Self-Discovery",
  "emotion_detected": "seeking",
  "quotes_used": ["SDI001", "SDI004"],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### New `/api/rumi/analyze`
```python
POST /api/rumi/analyze
{
  "query": "I'm afraid to love"
}

Response:
{
  "intent": "seeking_guidance",
  "emotion": "fear",
  "theme": "Human Love",
  "keywords": ["afraid", "love", "heart"],
  "suggested_quotes": ["HLV014", "DLV002"]
}
```

## Performance Considerations

### Current:
- Simple keyword search: ~50ms
- LLM inference (phi3-mini): ~2-3s
- **Total: ~3s**

### Future (with embeddings):
- Semantic search: ~100ms
- LLM inference: ~2-3s
- **Total: ~3.1s**

Both approaches are acceptable for conversational speed.

