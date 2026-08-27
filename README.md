# Local AI Assistant with Docker

Complete, production-ready local AI assistant with FastAPI backend, React frontend, Ollama LLM integration, RAG, voice I/O, and persistent memory.

## Features

✓ **Modern UI** - Dark mode, streaming responses, real-time chat  
✓ **Local LLM** - Ollama integration (Llama 2, Mistral, Neural Chat, etc.)  
✓ **RAG** - Upload & search PDFs, DOCX documents  
✓ **Memory System** - Persistent Markdown files (Profile, Goals, Projects, Journal)  
✓ **Voice** - Whisper transcription + Piper TTS support  
✓ **Streaming** - Real-time AI response streaming  
✓ **CORS-enabled** - Ready for local web access  
✓ **Docker Compose** - Single-command deployment  

## Quick Start

### Prerequisites
- Docker & Docker Compose (Windows, macOS, Linux)
- 8GB RAM minimum
- 20GB disk space for Ollama model

### Run

**Windows:**
```bash
cd local-ai-assistant
start.bat
```

**macOS/Linux:**
```bash
cd local-ai-assistant
bash start.sh
```

Or manually:
```bash
cd local-ai-assistant
python init.py
docker compose up --pull always
```

### Access

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Ollama API:** http://localhost:11434

## Project Structure

```
local-ai-assistant/
├── backend/              # FastAPI server
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # React + Vite
│   ├── src/
│   │   ├── App.jsx
│   │   ├── ChatArea.jsx
│   │   ├── Sidebar.jsx
│   │   ├── api.js
│   │   ├── store.js
│   │   └── index.css
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── docker-compose.yml    # Orchestration
├── memory/               # Persistent memory files
│   ├── profile.md
│   ├── goals.md
│   ├── projects.md
│   └── journal.md
├── documents/            # Uploaded PDFs & DOCX
├── voice/                # Audio files & transcripts
├── automation/           # Workflow configs (future)
├── config/               # Settings (future)
├── init.py               # Setup script
├── start.sh              # Unix start script
└── start.bat             # Windows start script
```

## API Endpoints

### Chat
```
POST /chat
{
  "message": "Tell me about yourself",
  "use_rag": true,
  "include_memory": true
}
```
Returns SSE stream of tokens.

### Documents
```
POST /upload-document                # Upload PDF/DOCX
GET  /documents                      # List uploaded docs
POST /delete-document/{filename}     # Delete doc
```

### Memory
```
POST /memory                         # Save memory entry
GET  /memory/{type}                  # Get memory (profile/goals/projects/journal)
```

### Voice
```
POST /voice/transcribe               # Transcribe audio with Whisper
POST /voice/synthesize               # Synthesize speech with Piper
```

### Utilities
```
GET  /health                         # Health check
GET  /models                         # List Ollama models
GET  /history                        # Conversation history
POST /clear-history                  # Clear history
```

## Services

### Ollama (Port 11434)
Local LLM runtime. Downloads model on first run (500MB+).

**Models available:**
- `llama2` (default, 7B)
- `mistral` (7B, faster)
- `neural-chat` (7B, instruction-tuned)
- `orca-mini` (3B, lightweight)

Pull a model:
```bash
docker exec local-ai-ollama ollama pull mistral
```

### Backend (Port 8000)
FastAPI server with:
- Streaming chat via Ollama
- LangChain RAG (FAISS vector store)
- HuggingFace embeddings
- File upload & document ingestion
- Voice transcription & synthesis
- Markdown-based memory management

### Frontend (Port 5173)
React + Vite + Tailwind:
- Real-time streaming chat UI
- Document upload sidebar
- Memory management interface
- Voice input/output controls
- Dark mode by default
- Mobile-responsive

## Configuration

### Environment Variables

Edit `.env` or pass to `docker compose`:
```bash
OLLAMA_BASE_URL=http://ollama:11434
MODEL_NAME=llama2
BACKEND_PORT=8000
FRONTEND_PORT=5173
ENABLE_VOICE_INPUT=true
ENABLE_VOICE_OUTPUT=true
```

### Customize Model

Change `MODEL_NAME` in docker-compose.yml:
```yaml
backend:
  environment:
    - MODEL_NAME=mistral
```

### Increase Context Window

For longer documents, modify backend `main.py`:
```python
async def stream_ollama_response(...):
    response = await client.stream(
        "POST",
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            ...
            "context_length": 8192,  # Default 2048
        },
    )
```

## Usage Examples

### Chat with Memory
The assistant automatically includes your profile, goals, and journal when responding.

1. Click **Tools** → **Memory** → **Add Profile Note**
2. Save information about yourself
3. Chat naturally—memory context is included

### Document Search (RAG)
1. Click **Tools** → **Documents** → **Upload PDF/DOCX**
2. Ask questions about the document
3. Toggle **Search Documents** to use the document as context

### Voice Input
1. Click **Tools** → **Voice** → **Transcribe Audio**
2. Upload MP3/WAV file
3. Transcribed text appears in chat input

## Performance

- **First run:** 3-5 minutes (Ollama model download + Docker image builds)
- **Chat response:** 2-10 seconds (depends on model & PC specs)
- **Memory overhead:** ~2GB (Ollama + embeddings model)

## Troubleshooting

### "Cannot connect to Ollama"
Ollama still loading. Wait 1-2 min for health check to pass:
```bash
curl http://localhost:11434/api/tags
```

### Out of Memory
Reduce model size:
```bash
# In docker-compose.yml
environment:
  - MODEL_NAME=orca-mini
```

Or increase Docker memory limit in Docker Desktop → Settings → Resources.

### API errors in frontend
Check backend logs:
```bash
docker logs local-ai-backend
```

### Documents not found during search
Ensure document was ingested:
```bash
docker exec local-ai-backend ls /app/documents/
```

### Voice not working
Check Whisper/Piper installed:
```bash
docker exec local-ai-backend pip list | grep whisper
```

## Advanced: Add Custom Models

Edit `backend/main.py` to add local model support:
```python
AVAILABLE_MODELS = {
    "llama2": "llama2",
    "mistral": "mistral",
    "custom-gguf": "/path/to/model.gguf",
}
```

## Development

### Local backend development (skip Docker)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python main.py
```

Visit http://localhost:8000/docs for Swagger API docs.

### Local frontend development
```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173.

## Production Deployment

### Kubernetes manifests
Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: local-ai
spec:
  replicas: 1
  selector:
    matchLabels:
      app: local-ai
  template:
    metadata:
      labels:
        app: local-ai
    spec:
      containers:
      - name: backend
        image: local-ai-backend:latest
        ports:
        - containerPort: 8000
      - name: frontend
        image: local-ai-frontend:latest
        ports:
        - containerPort: 5173
```

Deploy:
```bash
kubectl apply -f k8s/deployment.yaml
```

### Docker Swarm
```bash
docker stack deploy -c docker-compose.yml local-ai
```

## Next Steps

- [ ] Add automation workflow engine
- [ ] Implement WebSocket support for real-time updates
- [ ] Add multiple AI models side-by-side comparison
- [ ] Build plugin system for custom endpoints
- [ ] Add Anthropic Claude integration
- [ ] Implement streaming to frontend with websockets
- [ ] Add conversation export (PDF, JSON)
- [ ] Support for multi-turn function calling

## License

MIT

## Support

- **Issues:** Create a GitHub issue
- **Docs:** Check docker-compose.yml for all environment variables
- **Questions:** Refer to FastAPI & Ollama documentation

---

Built with Docker, FastAPI, React, Ollama, LangChain, and Tailwind CSS.
"# assistant" 
