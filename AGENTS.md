# Base44 Dev Notes

## Stack
- **Backend**: FastAPI (`backend/main.py`) — Ollama chat (SSE streaming), RAG (LangChain + FAISS + sentence-transformers), persistent Markdown memory, optional Whisper/Piper voice.
- **Frontend**: React + Vite (`frontend/`), Tailwind, Zustand store.
- **LLM**: Ollama runs as a compose service; model `tinyllama` is pulled automatically by the `ollama-pull` one-shot service.

## Dev environment (`docker-compose.base44.yml`)
- Runs from bind-mounted source with live reload (backend: `uvicorn --reload`, frontend: `vite`).
- Backend dev image (`backend/Dockerfile.dev`) installs a subset of deps (`backend/requirements.dev.txt`) — excludes `openai-whisper` and `piper-tts` (optional, try/except guarded) to keep builds fast. Voice endpoints return 501 in dev.
- Frontend reaches the backend via `VITE_API_URL` (the backend's public URL). `api.js` falls back to `http://localhost:8000` when unset.
- `vite.config.js` sets `allowedHosts: true` so the preview proxy hostname is accepted.

## Verify
- Frontend: `curl -sf -H "Host: external.example" http://localhost:3000/`
- Backend health: `curl -sf http://localhost:8000/health` → `{"status":"ok"}`
- Chat works once `ollama-pull` finishes pulling `tinyllama`.

## Notes
- No external secrets required; Ollama is local.
- To use a different/larger model, change `MODEL_NAME` and the `ollama-pull` command.
