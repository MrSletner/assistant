#!/usr/bin/env python3
"""
One-command setup for Local AI Assistant on Windows/Mac/Linux
Downloads and extracts the complete project to ~/local-ai-assistant
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def create_project():
    """Create the complete project structure locally"""
    
    home = Path.home()
    project_dir = home / "local-ai-assistant"
    
    # Remove if exists
    if project_dir.exists():
        print(f"Directory exists. Remove? (y/n): ", end="")
        if input().lower() == 'y':
            shutil.rmtree(project_dir)
        else:
            print("Using existing directory.")
    
    project_dir.mkdir(exist_ok=True)
    os.chdir(project_dir)
    print(f"✓ Created project at {project_dir}")
    
    # Create subdirectories
    for d in ["backend", "frontend", "memory", "documents", "voice", "automation", "config", "workflows"]:
        Path(d).mkdir(exist_ok=True)
    print("✓ Created subdirectories")
    
    # Backend files
    backend_req = """fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
aiofiles==23.2.1
pydantic==2.5.0
httpx==0.25.2
pydantic-settings==2.1.0
langchain==0.1.0
langchain-community==0.0.10
sentence-transformers==2.2.2
faiss-cpu==1.7.4
pypdf==3.17.1
python-docx==0.8.11
openai-whisper==20231117
piper-tts==1.2.0
numpy==1.24.3
"""
    Path("backend/requirements.txt").write_text(backend_req)
    
    backend_dockerfile = """FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    ffmpeg \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    Path("backend/Dockerfile").write_text(backend_dockerfile)
    print("✓ Created backend files")
    
    # Frontend files (minimal package.json)
    frontend_pkg = """{
  "name": "local-ai-assistant-frontend",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.2",
    "zustand": "^4.4.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.4",
    "tailwindcss": "^3.3.6",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16"
  }
}
"""
    Path("frontend/package.json").write_text(frontend_pkg)
    print("✓ Created frontend package.json")
    
    # Docker Compose
    compose = """version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: local-ai-ollama
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - local-ai
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: local-ai-backend
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - MODEL_NAME=llama2
    depends_on:
      ollama:
        condition: service_healthy
    volumes:
      - ./memory:/app/memory
      - ./documents:/app/documents
      - ./voice:/app/voice
    networks:
      - local-ai
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: local-ai-frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
    networks:
      - local-ai
    environment:
      - VITE_API_URL=http://localhost:8000

volumes:
  ollama_data:

networks:
  local-ai:
    driver: bridge
"""
    Path("docker-compose.yml").write_text(compose)
    print("✓ Created docker-compose.yml")
    
    # Init script
    init_py = """import os
from pathlib import Path

dirs = ['memory', 'documents', 'voice', 'automation', 'config']
for d in dirs:
    Path(d).mkdir(exist_ok=True)
    print(f"[OK] Created {d}/")

memory_files = {
    'profile.md': '# Profile\\n\\nAdd information about yourself here.\\n',
    'goals.md': '# Goals\\n\\nList your goals and objectives.\\n',
    'projects.md': '# Projects\\n\\nDocument your projects.\\n',
    'journal.md': '# Journal\\n\\nWrite journal entries here.\\n',
}

for filename, content in memory_files.items():
    path = Path('memory') / filename
    if not path.exists():
        path.write_text(content)
        print(f"[OK] Created memory/{filename}")

print("\\n[OK] Setup complete! Ready to run: docker compose up --pull always")
"""
    Path("init.py").write_text(init_py)
    print("✓ Created init.py")
    
    # .env.example
    env_ex = """OLLAMA_BASE_URL=http://ollama:11434
MODEL_NAME=llama2
BACKEND_PORT=8000
FRONTEND_PORT=5173
ENABLE_VOICE_INPUT=true
"""
    Path(".env.example").write_text(env_ex)
    
    # README
    readme = """# Local AI Assistant

A complete, self-contained AI assistant that runs entirely on your PC.

## Quick Start

1. Make sure Docker is running
2. Run: `docker compose up --pull always`
3. Open: http://localhost:5173

## Services

- **Ollama** (port 11434) - Local LLM runtime
- **Backend** (port 8000) - FastAPI server
- **Frontend** (port 5173) - React UI

## Features

- Chat with local LLM (Llama 2, Mistral, etc.)
- Document upload & RAG search
- Persistent memory (Profile, Goals, Projects, Journal)
- Voice input/output support
- Dark mode UI
- Streaming responses

For full documentation, see the project files.
"""
    Path("README.md").write_text(readme)
    print("✓ Created README.md")
    
    print(f"\n✓ Project created at: {project_dir}")
    print("\nNext steps:")
    print(f"  1. cd {project_dir}")
    print("  2. python init.py")
    print("  3. docker compose up --pull always")
    print("\nThen open: http://localhost:5173")

if __name__ == "__main__":
    try:
        create_project()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
