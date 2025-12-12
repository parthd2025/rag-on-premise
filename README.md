# Local RAG Application

Local RAG system using FastAPI, React, ChromaDB, and vLLM for on-premise document Q&A.

## Features

- 📄 **Document Ingestion**: Upload PDF, TXT, and DOCX files
- 🔍 **Vector Search**: Semantic search using ChromaDB and sentence transformers
- 🤖 **LLM Integration**: Local inference with vLLM (Mistral-7B) or OpenAI API
- 💬 **Streaming Responses**: Real-time streaming answers with source citations
- 🏥 **Health Monitoring**: Comprehensive health checks for all services
- ⚙️ **Configurable**: Environment-based configuration with validation

## Prerequisites

- Python 3.10+ (3.13 for backend, 3.10-3.11 for vLLM)
- Node.js 18+ (for frontend)
- GPU with 16GB+ VRAM (recommended for vLLM) or CPU-only setup
- 16GB+ system RAM

## Quick Start

### 1. Configuration

Copy the example environment file and configure:

```bash
# Copy example config
cp backend/.env.example .env

# Edit .env with your settings (optional - defaults work for local dev)
```

### 2. Backend Setup

```bash
# Create virtual environment (from project root) - only needed once
python -m venv venv

# IMPORTANT: Activate the virtual environment first!
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# Install dependencies (with venv activated)
pip install -r backend/requirements.txt

# Run the backend server (with venv activated)
# Option 1: From backend directory (recommended)
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Option 2: From project root with PYTHONPATH
# Windows PowerShell:
$env:PYTHONPATH="backend"; python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
# Linux/Mac:
PYTHONPATH=backend python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`

### 4. vLLM Server Setup (Optional but Recommended)

vLLM provides local LLM inference. The system will work without it (with fallback messages), but you need it for actual answer generation.

#### Option A: GPU Setup (Recommended)

```bash
# Create separate conda environment for vLLM (Python 3.10-3.11)
conda create -n vllm python=3.10
conda activate vllm

# Install vLLM (requires CUDA)
pip install vllm

# Start vLLM server
vllm serve mistralai/Mistral-7B-Instruct-v0.2 --port 8001

# For other models:
# vllm serve microsoft/Phi-3-mini-4k-instruct --port 8001
# vllm serve meta-llama/Llama-2-7b-chat-hf --port 8001
```

**System Requirements:**
- NVIDIA GPU with 16GB+ VRAM (for 7B models)
- CUDA 11.8+ installed
- ~15GB disk space for model files

#### Option B: CPU Setup (Slower)

```bash
# Install CPU version
pip install vllm --extra-index-url https://download.pytorch.org/whl/cpu

# Start with CPU
vllm serve mistralai/Mistral-7B-Instruct-v0.2 --port 8001 --device cpu
```

**Note:** CPU inference is significantly slower and may require more RAM.

#### Option C: Use OpenAI API (No Local Setup)

Edit `.env`:
```env
USE_OPENAI=true
OPENAI_API_KEY=your-api-key-here
VLLM_ENABLED=false
```

#### Option D: Use Ollama (Easier Alternative)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh  # Linux/Mac
# Or download from https://ollama.ai for Windows

# Pull model
ollama pull mistral:7b

# Ollama runs on port 11434 by default
# You'll need to modify generation_service.py to use Ollama API
```

### 5. Verify Setup

Check system health:
```bash
curl http://localhost:8000/api/health
```

Or visit `http://localhost:8000/docs` and test the `/api/health` endpoint.

## Configuration

All configuration is done via environment variables in `.env` file. See `backend/.env.example` for all available options.

### Key Settings

- **ChromaDB**: Port 8002 (changed from 8000 to avoid conflict)
- **vLLM**: Port 8001, configurable model
- **File Upload**: Max 50MB, supports PDF/TXT/DOCX
- **Chunking**: 300 tokens with 50 token overlap
- **RAG**: Top 5 results, 0.5 similarity threshold

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│  FastAPI     │────▶│  ChromaDB   │
│   (React)   │     │  (Backend)   │     │ (Vector DB) │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ├────▶ Embedding Service
                            │      (Sentence Transformers)
                            │
                            └────▶ vLLM Server
                                   (Mistral-7B)
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /api/health` - Health check for all services
- `POST /api/query` - Query the RAG system (streaming)
- `POST /api/ingest` - Upload and ingest documents
- `GET /api/documents` - List all ingested documents
- `DELETE /api/documents/{id}` - Delete a document

See `http://localhost:8000/docs` for interactive API documentation.

## Troubleshooting

### vLLM Connection Errors

If you see "Unable to connect to vLLM server":
1. Check if vLLM is running: `curl http://localhost:8001/v1/models`
2. Verify port in `.env` matches vLLM port
3. Check firewall settings
4. The system will use fallback messages if vLLM is unavailable

### Port Conflicts

- FastAPI: Port 8000 (configurable via `API_PORT`)
- vLLM: Port 8001 (configurable via `VLLM_PORT`)
- ChromaDB: Port 8002 (configurable via `CHROMA_PORT`)

### File Upload Issues

- Max file size: 50MB (configurable via `MAX_FILE_SIZE_MB`)
- Supported types: PDF, TXT, DOCX (configurable via `ALLOWED_FILE_TYPES`)

### GPU/VRAM Issues

If you get OOM (Out of Memory) errors:
- Use a smaller model (e.g., Phi-3-mini)
- Reduce `max_tokens` in generation
- Use CPU mode (slower but works)
- Use quantization: `vllm serve ... --quantization awq`

## Development

### Project Structure

```
RAG ON PREMISE/
├── backend/
│   ├── api/
│   │   ├── main.py           # FastAPI app
│   │   ├── routes/           # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── models/           # Pydantic schemas
│   │   └── utils/            # Config, logging
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # React + Vite
├── venv/                     # Python virtual environment
└── README.md
```

## License

MIT License - Free for local use

## Support

For issues and questions:
1. Check the health endpoint: `/api/health`
2. Review logs in the console
3. Check configuration in `.env`
4. Verify all services are running
