# Backend Development Server

Start the FastAPI backend server locally for development and testing.

## Steps

1. **Ensure virtual environment is activated and dependencies installed**
```bash
cd /Users/yvesromano/AiRAG/railway-api && pip install -r requirements.txt
```

2. **Start the FastAPI server with hot reload**
```bash
cd /Users/yvesromano/AiRAG/railway-api && uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

3. **Access the API**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Environment Variables
Ensure these are set in your `.env` file:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `YOUTUBE_API_KEY`
- `OPENAI_API_KEY`
- `RESEND_API_KEY`

## Notes
- The main entry point is `server.py`
- Core analysis logic is in `GAP_ULTIMATE.py`
- Press Ctrl+C to stop the server
