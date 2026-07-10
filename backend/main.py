from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Set
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime
import  os
import  sys
import json
import time

# Import Jenny core modules
from core.brain import brain
from core.stt import stt_provider
from core.tts import tts_provider
from config.settings import settings
import subprocess
import threading
from loguru import logger

# Initialize FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    threading.Thread(target=start_assistant, daemon=True).start()
    yield
    # Shutdown logic (optional)
    logger.info("Shutting down Jenny AI...")

app = FastAPI(
    title="Jenny AI - Virtual Personal Assistant API",
    description="Jenny AI-powered virtual personal assistant with chat, voice, and task management capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ChatMessage(BaseModel):
    content: str
    type: str = "user"  # "user" or "assistant"
    timestamp: Optional[datetime] = None

class ChatResponse(BaseModel):
    message: str
    timestamp: datetime
    type: str = "assistant"

class VoiceRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    language: str = "en-US"

class TaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None

# In-memory storage for demo purposes
chat_history = []
tasks = []

# Avatar WebSocket Connection Manager
class AvatarConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_state(self, state: str):
        message = json.dumps({"state": state})
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

avatar_manager = AvatarConnectionManager()

class AvatarStateEvent(BaseModel):
    state: str  # "idle", "listening", "thinking", "speaking"

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Jenny AI - Virtual Personal Assistant API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/chat",
            "voice": "/voice",
            "tasks": "/tasks",
            "health": "/health",
            "avatar_ws": "/ws/avatar",
            "avatar_event": "/api/avatar/event"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """
    Chat endpoint for processing user messages and generating AI responses
    Uses Jenny Brain (Ollama) for intelligent responses
    """
    try:
        # Add user message to history
        user_msg = {
            "content": message.content,
            "type": "user",
            "timestamp": datetime.now()
        }
        chat_history.append(user_msg)
        
        # Use Lajvanti Brain for AI processing
        ai_response = brain.chat(message.content)
        
        # Create response
        response = ChatResponse(
            message=ai_response,
            timestamp=datetime.now(),
            type="assistant"
        )
        
        # Add AI response to history
        ai_msg = {
            "content": ai_response,
            "type": "assistant",
            "timestamp": datetime.now()
        }
        chat_history.append(ai_msg)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/chat/history")
async def get_chat_history():
    """Get chat history"""
    return {"messages": chat_history}

@app.post("/voice")
async def voice_endpoint(request: VoiceRequest):
    """
    Voice processing endpoint for speech-to-text and text-to-speech
    Uses Whisper for STT and Piper for TTS
    """
    try:
        import base64
        import tempfile
        import os
        
        # Decode base64 audio data
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe audio using STT provider
            transcript = stt_provider.transcribe(temp_file_path, language=request.language)
            
            if not transcript:
                return {
                    "transcript": "",
                    "response": "I couldn't understand the audio. Please try again.",
                    "audio_url": None,
                    "timestamp": datetime.now()
                }
            
            # Get AI response from brain
            ai_response = brain.chat(transcript)
            
            # Generate TTS audio (optional - can be done client-side)
            # For now, return text response
            
            return {
                "transcript": transcript,
                "response": ai_response,
                "audio_url": None,  # TTS can be handled client-side or via separate endpoint
                "timestamp": datetime.now()
            }
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice: {str(e)}")

@app.get("/tasks")
async def get_tasks():
    """Get all tasks"""
    return {"tasks": tasks}

@app.post("/tasks")
async def create_task(task: TaskRequest):
    """Create a new task"""
    try:
        new_task = {
            "id": len(tasks) + 1,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "due_date": task.due_date,
            "status": "pending",
            "created_at": datetime.now()
        }
        tasks.append(new_task)
        return {"task": new_task, "message": "Task created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: TaskRequest):
    """Update an existing task"""
    try:
        for t in tasks:
            if t["id"] == task_id:
                t.update({
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority,
                    "due_date": task.due_date,
                    "updated_at": datetime.now()
                })
                return {"task": t, "message": "Task updated successfully"}
        
        raise HTTPException(status_code=404, detail="Task not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task"""
    try:
        for i, task in enumerate(tasks):
            if task["id"] == task_id:
                deleted_task = tasks.pop(i)
                return {"message": "Task deleted successfully", "deleted_task": deleted_task}
        
        raise HTTPException(status_code=404, detail="Task not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")

@app.get("/health/brain")
async def brain_health():
    """Check if Jenny Brain (Ollama) is available"""
    is_connected = brain.check_ollama_connection()
    models = brain.get_available_models() if is_connected else []
    
    return {
        "brain_available": is_connected,
        "provider": settings.LLM_PROVIDER,
        "model": settings.OLLAMA_MODEL,
        "available_models": models,
        "status": "healthy" if is_connected else "unavailable"
    }

# --- Avatar Endpoints ---

@app.websocket("/ws/avatar")
async def websocket_avatar_endpoint(websocket: WebSocket):
    """WebSocket endpoint for the Electron/React 3D Avatar to listen to state changes."""
    await avatar_manager.connect(websocket)
    try:
        while True:
            # We just keep the connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        avatar_manager.disconnect(websocket)

@app.post("/api/avatar/event")
async def avatar_event_webhook(event: AvatarStateEvent):
    """
    Webhook for the existing orchestration loop (e.g. desktop.py) 
    to blindly notify the backend of state changes.
    """
    await avatar_manager.broadcast_state(event.state)
    return {"status": "broadcasted", "state": event.state}

def start_assistant():
    """Start the Jenny assistant background process safely with hardware reset"""
    try:
        # 1. Surgical kill: Terminate any lingering assistant processes
        logger.info("🧹 Cleaning up hardware handles...")
        try:
            # -9 forces immediate release of system resources on Mac
            subprocess.run(["pkill", "-9", "-f", "assistant.py"], check=False)
            time.sleep(1.5) # Time for CoreAudio/PortAudio to fully release
        except:
            pass

        # 2. Give the API a moment to fully initialize
        time.sleep(2) 
        python_executable = sys.executable
        current_dir = os.path.dirname(os.path.abspath(__file__))
        assistant_path = os.path.join(current_dir, "core", "assistant.py")
        
        logger.info(f"🚀 Launching Jenny Assistant: {assistant_path}")
        
        # Explicitly set PYTHONPATH to current directory
        env = os.environ.copy()
        env["PYTHONPATH"] = current_dir
        
        # Launch fresh subprocess
        subprocess.Popen([python_executable, assistant_path], cwd=current_dir, env=env)
    except Exception as e:
        logger.error(f"❌ Failed to launch Jenny Assistant: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
