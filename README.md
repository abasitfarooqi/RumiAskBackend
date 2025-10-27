# Ask Rumi Backend

A local, offline-first AI mentor app backend inspired by Rumi's wisdom. Built with FastAPI and designed to run local LLMs with optional GPU acceleration.

## Features

- **Local Model Management**: Download and manage Ollama models (phi3-mini, mistral, llama3)
- **GPU Acceleration**: Automatic detection and switching between CPU, Apple Metal (MPS), and CUDA
- **Async Task Queue**: Handle concurrent requests efficiently
- **Rumi Wisdom Database**: Local JSON database with Rumi quotes and teachings
- **RESTful API**: Complete API for chat, models, providers, and system management
- **Streaming Support**: Real-time streaming responses
- **Health Monitoring**: System health checks and device status

## Quick Start

### 1. Setup Environment

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Server

```bash
# Run the development server
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

The server will be available at `http://127.0.0.1:8001`

### 3. API Documentation

Visit `http://127.0.0.1:8001/docs` for interactive API documentation.

## API Endpoints

### System
- `GET /` - Root endpoint with basic info
- `GET /api/system/info` - System information
- `GET /api/system/device` - Device status
- `POST /api/system/device` - Switch device
- `GET /api/system/health` - Health check

### Models
- `GET /api/models/` - List all models
- `GET /api/models/available` - List available models
- `POST /api/models/download` - Download a model
- `POST /api/models/run` - Run model inference
- `POST /api/models/run/stream` - Stream model inference

### Chat
- `POST /api/chat/send` - Send chat message
- `POST /api/chat/stream` - Stream chat response
- `POST /api/chat/ask-rumi` - Ask Rumi-style questions
- `GET /api/chat/conversations` - List conversations

### Providers
- `GET /api/providers/` - List providers
- `GET /api/providers/{name}` - Get provider info
- `POST /api/providers/{name}/test` - Test provider

## Model Management

### Download Models

```bash
# Download phi3-mini via API
curl -X POST "http://127.0.0.1:8001/api/models/download" \
  -H "Content-Type: application/json" \
  -d '{"model": "phi3-mini"}'
```

### Run Inference

```bash
# Run model inference
curl -X POST "http://127.0.0.1:8001/api/models/run" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3-mini",
    "prompt": "What is the meaning of life?",
    "temperature": 0.7,
    "max_tokens": 200
  }'
```

## Device Management

The backend automatically detects and manages devices:

- **CPU**: Fallback for all systems
- **Apple Metal (MPS)**: Preferred on Apple Silicon Macs
- **CUDA**: Preferred on NVIDIA GPUs

Switch devices via API:

```bash
# Switch to Apple Metal
curl -X POST "http://127.0.0.1:8001/api/system/device?device=mps"

# Switch to CPU
curl -X POST "http://127.0.0.1:8001/api/system/device?device=cpu"
```

## Data Structure

### Rumi Quotes Database
Located at `data/rumi_quotes.json` with 15+ curated Rumi quotes including:
- Categories: healing, wisdom, love, guidance, spirituality
- Themes: transformation, self-improvement, divine-love
- Tags for semantic search

### Model Registry
Located at `data/model_registry.json` tracking:
- Model metadata (size, provider, capabilities)
- Download status and progress
- Availability checks

## Architecture

```
RumiBackend/
├── main.py                 # FastAPI application entry point
├── core/                   # Core modules
│   ├── config.py          # Configuration management
│   ├── gpu_manager.py     # GPU detection and switching
│   ├── model_manager.py   # Model registry and downloads
│   ├── local_runner.py    # Local model inference
│   └── queue_manager.py   # Async task queue
├── routes/                 # API routes
│   ├── chat.py            # Chat endpoints
│   ├── models.py          # Model management
│   ├── providers.py        # Provider configuration
│   └── system.py          # System information
├── data/                   # Data files
│   ├── rumi_quotes.json   # Rumi wisdom database
│   ├── model_registry.json # Model metadata
│   └── providers.config.json # Provider settings
└── requirements.txt        # Python dependencies
```

## Development

### Adding New Models

1. Update `data/model_registry.json` with model metadata
2. Implement provider-specific download logic in `core/model_manager.py`
3. Add inference support in `core/local_runner.py`

### Adding New Providers

1. Add provider configuration to `data/providers.config.json`
2. Implement provider logic in `routes/providers.py`
3. Add model support in `core/model_manager.py`

## Next Steps

- [ ] Add Whisper integration for voice input
- [ ] Implement semantic search with embeddings
- [ ] Add RAG (Retrieval-Augmented Generation) with Rumi database
- [ ] Create MicroRumiLLM fine-tuning pipeline
- [ ] Add React Native frontend integration
- [ ] Implement user session management
- [ ] Add conversation persistence

## Requirements

- Python 3.11+
- Ollama (for local model inference)
- PyTorch with MPS/CUDA support
- 4GB+ RAM (8GB+ recommended)
- macOS M1/M2/M3 or NVIDIA GPU (optional)

## License

This project is part of the Ask Rumi (RumiTalks) open-source initiative.
