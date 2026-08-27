"""
FastAPI backend for local AI assistant with Ollama integration
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# LangChain imports for RAG
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document

# Voice imports
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import piper
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama2")
MEMORY_DIR = Path("memory")
DOCUMENTS_DIR = Path("documents")
VOICE_DIR = Path("voice")

# Ensure directories exist
MEMORY_DIR.mkdir(exist_ok=True)
DOCUMENTS_DIR.mkdir(exist_ok=True)
VOICE_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Local AI Assistant API")

# CORS middleware for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
embedding_model = None
vector_store = None
conversation_history = []

# Pydantic models
class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    use_rag: bool = False
    include_memory: bool = True

class MemoryEntry(BaseModel):
    title: str
    content: str
    memory_type: str  # "profile", "goal", "project", "journal"

class VoiceInput(BaseModel):
    audio_path: str

# ============ RAG Functions ============

async def initialize_embeddings():
    """Initialize embeddings model"""
    global embedding_model
    if embedding_model is None:
        embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return embedding_model

async def load_pdf(file_path: str) -> List[Document]:
    """Load PDF and return documents"""
    loader = PyPDFLoader(file_path)
    return loader.load()

async def load_docx(file_path: str) -> List[Document]:
    """Load DOCX and return documents"""
    loader = Docx2txtLoader(file_path)
    return loader.load()

async def ingest_documents(file_path: str):
    """Ingest document and create vector store"""
    global vector_store, embedding_model
    
    embedding_model = await initialize_embeddings()
    
    # Load based on file type
    if file_path.endswith(".pdf"):
        documents = await load_pdf(file_path)
    elif file_path.endswith(".docx"):
        documents = await load_docx(file_path)
    else:
        raise ValueError("Unsupported file type. Use PDF or DOCX.")
    
    # Split documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(documents)
    
    # Create or update vector store
    if vector_store is None:
        vector_store = FAISS.from_documents(chunks, embedding_model)
    else:
        vector_store.add_documents(chunks)
    
    return len(chunks)

async def retrieve_context(query: str, k: int = 3) -> str:
    """Retrieve relevant documents from vector store"""
    global vector_store, embedding_model
    
    if vector_store is None:
        return ""
    
    embedding_model = await initialize_embeddings()
    docs = vector_store.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in docs])

# ============ Memory Functions ============

def save_memory(title: str, content: str, memory_type: str):
    """Save memory to Markdown file"""
    memory_dir = MEMORY_DIR
    memory_file = memory_dir / f"{memory_type}.md"
    
    timestamp = datetime.now().isoformat()
    entry = f"\n## {title}\n*{timestamp}*\n{content}\n"
    
    if memory_file.exists():
        with open(memory_file, "a") as f:
            f.write(entry)
    else:
        with open(memory_file, "w") as f:
            f.write(f"# {memory_type.title()} Memory\n{entry}")

def load_memory(memory_type: str) -> str:
    """Load memory from Markdown file"""
    memory_file = MEMORY_DIR / f"{memory_type}.md"
    if memory_file.exists():
        with open(memory_file, "r") as f:
            return f.read()
    return ""

def get_memory_context() -> str:
    """Get relevant memory context for the conversation"""
    memory_types = ["profile", "goals", "projects", "journal"]
    context_parts = []
    
    for mtype in memory_types:
        content = load_memory(mtype)
        if content:
            context_parts.append(f"### {mtype.title()}\n{content}")
    
    return "\n\n".join(context_parts) if context_parts else ""

# ============ Ollama Integration ============

async def stream_ollama_response(
    prompt: str,
    use_rag: bool = False,
    include_memory: bool = True,
) -> str:
    """Stream response from Ollama"""
    global conversation_history
    
    # Build context
    context_parts = [prompt]
    
    if include_memory:
        memory_context = get_memory_context()
        if memory_context:
            context_parts.insert(0, f"User Memory Context:\n{memory_context}\n---\n")
    
    if use_rag:
        rag_context = await retrieve_context(prompt)
        if rag_context:
            context_parts.insert(0, f"Document Context:\n{rag_context}\n---\n")
    
    full_prompt = "\n".join(context_parts)
    
    # Add to conversation history
    conversation_history.append({"role": "user", "content": prompt})
    
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": full_prompt,
                    "stream": True,
                },
            ) as response:
                full_response = ""
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")
                        full_response += token
                        yield f"data: {json.dumps({'token': token})}\n\n"
                
                # Add to history
                conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

# ============ API Endpoints ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/models")
async def list_models():
    """List available Ollama models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with streaming response"""
    async def generate():
        async for chunk in stream_ollama_response(
            request.message,
            use_rag=request.use_rag,
            include_memory=request.include_memory,
        ):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/history")
async def get_history():
    """Get conversation history"""
    return {"history": conversation_history}

@app.post("/clear-history")
async def clear_history():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return {"status": "cleared"}

# ============ Document/RAG Endpoints ============

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest document for RAG"""
    try:
        file_path = DOCUMENTS_DIR / file.filename
        
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingest
        chunks = await ingest_documents(str(file_path))
        
        return {
            "status": "success",
            "filename": file.filename,
            "chunks_ingested": chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """List uploaded documents"""
    docs = [f.name for f in DOCUMENTS_DIR.glob("*")]
    return {"documents": docs}

@app.post("/delete-document/{filename}")
async def delete_document(filename: str):
    """Delete document"""
    try:
        file_path = DOCUMENTS_DIR / filename
        if file_path.exists():
            file_path.unlink()
            return {"status": "deleted", "filename": filename}
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ Memory Endpoints ============

@app.post("/memory")
async def save_memory_endpoint(entry: MemoryEntry):
    """Save a memory entry"""
    try:
        save_memory(entry.title, entry.content, entry.memory_type)
        return {"status": "saved", "title": entry.title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{memory_type}")
async def get_memory(memory_type: str):
    """Get memory by type"""
    try:
        content = load_memory(memory_type)
        return {"type": memory_type, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ Voice Endpoints ============

@app.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio using Whisper"""
    if not WHISPER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Whisper not available. Install with: pip install openai-whisper"
        )
    
    try:
        file_path = VOICE_DIR / file.filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        model = whisper.load_model("base")
        result = model.transcribe(str(file_path))
        
        return {
            "text": result["text"],
            "language": result.get("language", "unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/synthesize")
async def synthesize_speech(text: str):
    """Synthesize speech using Piper"""
    if not PIPER_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Piper not available. Install with: pip install piper-tts"
        )
    
    try:
        output_file = VOICE_DIR / f"output_{datetime.now().timestamp()}.wav"
        # Piper synthesis would go here
        return {"audio_file": str(output_file)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
