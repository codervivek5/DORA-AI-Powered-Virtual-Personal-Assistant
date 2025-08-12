# DORA AI Backend

This is the backend API server for the DORA AI Virtual Personal Assistant, built with FastAPI.

## Features

- **Chat API**: Process user messages and generate AI responses
- **Voice API**: Speech-to-text and text-to-speech capabilities
- **Task Management**: Create, read, update, and delete tasks
- **CORS Support**: Configured for frontend communication
- **Health Check**: API health monitoring endpoint

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

### Development Mode
```bash
python main.py
```

### Using Uvicorn Directly
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## API Endpoints

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: Configure as needed

### Available Endpoints

#### Root
- `GET /` - API information and available endpoints

#### Health Check
- `GET /health` - Server health status

#### Chat
- `POST /chat` - Send a message and get AI response
- `GET /chat/history` - Get chat history

#### Voice
- `POST /voice` - Process voice input

#### Tasks
- `GET /tasks` - Get all tasks
- `POST /tasks` - Create a new task
- `PUT /tasks/{task_id}` - Update a task
- `DELETE /tasks/{task_id}` - Delete a task

## API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## Example Usage

### Chat API
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"content": "Hello, how can you help me?"}'
```

### Create Task
```bash
curl -X POST "http://localhost:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{"title": "Buy groceries", "description": "Milk, bread, eggs", "priority": "high"}'
```

## Development

### Project Structure
```
backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .env                # Environment variables (create as needed)
```

### Environment Variables

Create a `.env` file for configuration:
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# AI Services (for future integration)
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key

# Voice Services
GOOGLE_SPEECH_API_KEY=your_google_speech_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Database (for future integration)
DATABASE_URL=your_database_url
```

## Integration with Frontend

The backend is configured with CORS to allow communication with the frontend running on:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

## Future Enhancements

1. **AI Integration**: Connect to OpenAI, LangChain, and other AI services
2. **Database**: Add persistent storage for chat history and tasks
3. **Authentication**: Implement user authentication and authorization
4. **Voice Processing**: Integrate with Google Speech and ElevenLabs
5. **Task Automation**: Add CrewAI and LangGraph integration
6. **Real-time Communication**: Add WebSocket support for real-time chat

## Contributing

1. Follow the existing code style
2. Add proper error handling
3. Include API documentation
4. Test your changes thoroughly

## License

This project is licensed under the MIT License.
