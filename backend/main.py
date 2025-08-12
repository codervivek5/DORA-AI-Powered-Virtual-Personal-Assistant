from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import json

# Initialize FastAPI app
app = FastAPI(
    title="DORA AI - Virtual Personal Assistant API",
    description="AI-powered virtual personal assistant with chat, voice, and task management capabilities",
    version="1.0.0"
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "DORA AI - Virtual Personal Assistant API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/chat",
            "voice": "/voice",
            "tasks": "/tasks",
            "health": "/health"
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
    """
    try:
        # Add user message to history
        user_msg = {
            "content": message.content,
            "type": "user",
            "timestamp": datetime.now()
        }
        chat_history.append(user_msg)
        
        # Simulate AI processing (replace with actual AI integration)
        ai_response = generate_ai_response(message.content)
        
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
    """
    try:
        # Simulate voice processing (replace with actual voice API integration)
        # For now, return a mock response
        return {
            "transcript": "Voice input received",
            "response": "I heard your voice message. This is a simulated response.",
            "audio_url": None,  # Would contain TTS audio URL
            "timestamp": datetime.now()
        }
        
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

def generate_ai_response(user_message: str) -> str:
    """
    Generate AI response based on user message
    This is a simple simulation - replace with actual AI integration
    """
    user_message_lower = user_message.lower()
    
    # Simple response logic for demo
    if "hello" in user_message_lower or "hi" in user_message_lower:
        return "Hello! I'm DORA, your AI-powered virtual personal assistant. How can I help you today?"
    
    elif "help" in user_message_lower:
        return "I can help you with:\n• Chat and voice interactions\n• Task management\n• Reminders and calendar\n• Email handling\n• Information search\n• Smart home integration\n\nWhat would you like to do?"
    
    elif "task" in user_message_lower or "todo" in user_message_lower:
        return "I can help you manage tasks! You can create, update, and delete tasks through the API. Would you like me to show you your current tasks?"
    
    elif "weather" in user_message_lower:
        return "I can provide weather information! However, this is currently a demo. In the full implementation, I would connect to a weather API to give you real-time weather data."
    
    elif "reminder" in user_message_lower:
        return "I can set reminders for you! Just let me know what you'd like to be reminded about and when."
    
    elif "email" in user_message_lower:
        return "I can help you with emails! I can read, draft, and summarize emails. What would you like to do with your emails?"
    
    elif "thank" in user_message_lower:
        return "You're welcome! I'm here to help make your life easier. Is there anything else you'd like assistance with?"
    
    else:
        return f"I received your message: '{user_message}'. This is a simulated response from the DORA AI backend. In the full implementation, this would be processed by advanced AI models including LLMs, RAG systems, and agentic AI for more intelligent responses."

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
