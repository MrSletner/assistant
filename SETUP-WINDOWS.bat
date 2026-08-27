@echo off
REM Download and extract the Local AI Assistant to your user directory
REM Run this from PowerShell or Command Prompt

setlocal enabledelayedexpansion

echo Local AI Assistant Setup
echo =======================
echo.

REM Define target directory
set "TARGET_DIR=%USERPROFILE%\local-ai-assistant"

echo Creating project directory at: %TARGET_DIR%
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
cd /d "%TARGET_DIR%"

echo.
echo Creating subdirectories...
mkdir backend frontend memory documents voice automation config workflows >nul 2>&1

echo.
echo Creating files...

REM Create backend/requirements.txt
(
echo fastapi==0.104.1
echo uvicorn==0.24.0
echo python-multipart==0.0.6
echo aiofiles==23.2.1
echo pydantic==2.5.0
echo httpx==0.25.2
echo pydantic-settings==2.1.0
echo langchain==0.1.0
echo langchain-community==0.0.10
echo sentence-transformers==2.2.2
echo faiss-cpu==1.7.4
echo pypdf==3.17.1
echo python-docx==0.8.11
echo openai-whisper==20231117
echo piper-tts==1.2.0
echo numpy==1.24.3
) > "backend\requirements.txt"

echo [OK] backend/requirements.txt

REM Create backend/Dockerfile
(
echo FROM python:3.11-slim
echo.
echo WORKDIR /app
echo.
echo RUN apt-get update ^&^& apt-get install -y \
echo     ffmpeg \
echo     ^&^& rm -rf /var/lib/apt/lists/*
echo.
echo COPY requirements.txt .
echo RUN pip install --no-cache-dir -r requirements.txt
echo.
echo COPY . .
echo.
echo EXPOSE 8000
echo.
echo CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
) > "backend\Dockerfile"

echo [OK] backend/Dockerfile

REM Create frontend package.json
(
echo {
echo   "name": "local-ai-assistant-frontend",
echo   "private": true,
echo   "version": "0.0.1",
echo   "type": "module",
echo   "scripts": {
echo     "dev": "vite",
echo     "build": "vite build",
echo     "preview": "vite preview"
echo   },
echo   "dependencies": {
echo     "react": "^18.2.0",
echo     "react-dom": "^18.2.0",
echo     "axios": "^1.6.2",
echo     "zustand": "^4.4.1"
echo   },
echo   "devDependencies": {
echo     "@vitejs/plugin-react": "^4.2.0",
echo     "vite": "^5.0.4",
echo     "tailwindcss": "^3.3.6",
echo     "postcss": "^8.4.32",
echo     "autoprefixer": "^10.4.16"
echo   }
echo }
) > "frontend\package.json"

echo [OK] frontend/package.json

REM Create docker-compose.yml (already have full copy above)

REM Create .env.example
(
echo OLLAMA_BASE_URL=http://ollama:11434
echo OLLAMA_HOST=0.0.0.0:11434
echo MODEL_NAME=llama2
echo BACKEND_PORT=8000
echo FRONTEND_PORT=5173
echo ENABLE_VOICE_INPUT=true
echo ENABLE_VOICE_OUTPUT=true
echo ENABLE_RAG=true
echo ENABLE_MEMORY=true
) > ".env.example"

echo [OK] .env.example

REM Create init.py
(
echo import os
echo from pathlib import Path
echo.
echo dirs = [
echo     'memory',
echo     'documents',
echo     'voice',
echo     'automation',
echo     'config'
echo ]
echo.
echo for d in dirs:
echo     Path(d^).mkdir(exist_ok=True^)
echo     print(f"[OK] Created {d}/"^)
echo.
echo memory_files = {
echo     'profile.md': '# Profile\n\nAdd information about yourself here.\n',
echo     'goals.md': '# Goals\n\nList your goals and objectives.\n',
echo     'projects.md': '# Projects\n\nDocument your projects.\n',
echo     'journal.md': '# Journal\n\nWrite journal entries here.\n',
echo }
echo.
echo for filename, content in memory_files.items(^):
echo     path = Path('memory'^) / filename
echo     if not path.exists(^):
echo         path.write_text(content^)
echo         print(f"[OK] Created memory/{filename}"^)
echo.
echo print("\n[OK] Setup complete! Ready to run: docker compose up --pull always"^)
) > "init.py"

echo [OK] init.py

REM Create start.bat
(
echo @echo off
echo echo Local AI Assistant
echo echo ====================
echo echo.
echo echo Setting up directories...
echo python init.py
echo echo.
echo echo Starting Docker services...
echo docker compose up --pull always
) > "start.bat"

echo [OK] start.bat

REM Create docker-compose.yml
(
echo version: '3.8'
echo.
echo services:
echo   ollama:
echo     image: ollama/ollama:latest
echo     container_name: local-ai-ollama
echo     ports:
echo       - "11434:11434"
echo     environment:
echo       - OLLAMA_HOST=0.0.0.0:11434
echo     volumes:
echo       - ollama_data:/root/.ollama
echo     networks:
echo       - local-ai
echo     healthcheck:
echo       test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
echo       interval: 10s
echo       timeout: 5s
echo       retries: 5
echo.
echo   backend:
echo     build:
echo       context: ./backend
echo       dockerfile: Dockerfile
echo     container_name: local-ai-backend
echo     ports:
echo       - "8000:8000"
echo     environment:
echo       - OLLAMA_BASE_URL=http://ollama:11434
echo       - MODEL_NAME=llama2
echo     depends_on:
echo       ollama:
echo         condition: service_healthy
echo     volumes:
echo       - ./memory:/app/memory
echo       - ./documents:/app/documents
echo       - ./voice:/app/voice
echo       - ./automation:/app/automation
echo     networks:
echo       - local-ai
echo     healthcheck:
echo       test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
echo       interval: 10s
echo       timeout: 5s
echo       retries: 5
echo.
echo   frontend:
echo     build:
echo       context: ./frontend
echo       dockerfile: Dockerfile
echo     container_name: local-ai-frontend
echo     ports:
echo       - "5173:5173"
echo     depends_on:
echo       - backend
echo     networks:
echo       - local-ai
echo     environment:
echo       - VITE_API_URL=http://localhost:8000
echo.
echo volumes:
echo   ollama_data:
echo.
echo networks:
echo   local-ai:
echo     driver: bridge
) > "docker-compose.yml"

echo [OK] docker-compose.yml

echo.
echo =======================
echo Setup complete!
echo Project location: %TARGET_DIR%
echo.
echo Next: Run "start.bat" or use: docker compose up --pull always
echo.
pause
