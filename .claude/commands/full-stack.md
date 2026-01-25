# Full Stack Development

Run both frontend and backend development servers simultaneously.

## Steps

1. **Start the backend server in background**
```bash
cd /Users/yvesromano/AiRAG/railway-api && uvicorn server:app --reload --host 0.0.0.0 --port 8000 &
```

2. **Start the frontend server**
```bash
cd /Users/yvesromano/AiRAG/gap-intel-website && npm run dev
```

## Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Configuration
Ensure frontend is configured to hit local backend:
- Check `gap-intel-website/.env.local` for `NEXT_PUBLIC_API_URL`
- Set to `http://localhost:8000` for local development

## Stopping Services
```bash
# Find and kill the backend process
pkill -f "uvicorn server:app"

# Frontend stops with Ctrl+C
```

## Notes
- Backend requires Python environment with dependencies
- Frontend requires Node.js and npm
- Both servers have hot reload enabled
- Check terminal output for any startup errors
