# Environment Check

Verify all environment variables and configurations are properly set.

## Steps

1. **Check Railway debug config**
```bash
curl -s https://thriving-presence-production-ca4a.up.railway.app/api/debug/config | python3 -m json.tool
```

2. **Check local backend .env file exists**
```bash
ls -la /Users/yvesromano/AiRAG/railway-api/.env 2>/dev/null || echo "No .env file found in railway-api/"
```

3. **Check local frontend .env.local exists**
```bash
ls -la /Users/yvesromano/AiRAG/gap-intel-website/.env.local 2>/dev/null || echo "No .env.local file found in frontend/"
```

4. **Verify Railway environment**
```bash
curl -s https://thriving-presence-production-ca4a.up.railway.app/check-env | python3 -c "import sys,json; d=json.load(sys.stdin); print('Python:', d.get('python_version','')); print('Packages:', len(d.get('installed_packages',[])))"
```

## Required Environment Variables

### Backend (Railway)
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `YOUTUBE_API_KEY` - YouTube Data API key
- `OPENAI_API_KEY` - OpenAI API key for analysis
- `RESEND_API_KEY` - Resend email service key

### Frontend (Vercel/Local)
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key

## Notes
- Never commit `.env` files to git
- Check `.gitignore` includes all env files
- Railway env vars are set in the dashboard
- Vercel env vars are set in project settings
