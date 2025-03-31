# AI Chatbot Application

A full-stack AI chatbot application with support for multiple LLM providers and real-time streaming responses.

## Features

- Multiple LLM provider support (Anthropic, Groq, OpenRouter, Perplexity)
- Real-time response streaming
- Automatic mock mode when API keys are missing
- Docker-based deployment
- Comprehensive logging and monitoring
- Rate limiting and security features

## Tech Stack

- Backend: FastAPI (Python 3.9+)
- Frontend: React 18+ with Vite
- Deployment: Docker & Docker Compose

## Getting Started

1. Clone the repository
2. Copy `.env.example` to `.env` in the backend directory and configure your API keys
3. Development:
   ```bash
   docker-compose up --build
   ```
4. Access the application at http://localhost:8000

## Development Setup

### Backend

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate   # Windows
   ```
2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start development server:
   ```bash
   npm run dev
   ```

## Configuration

See `backend/.env.example` for available configuration options.

## API Documentation

Once running, visit:
- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT 