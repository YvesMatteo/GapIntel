---
description: Check Railway API health and configuration
---
# Check Railway Health

// turbo-all

## Steps

1. Check if the API is responding:
```bash
curl -s https://resourceful-passion-production.up.railway.app/health
```

2. Check debug info (env vars, ffmpeg, dependencies):
```bash
curl -s https://resourceful-passion-production.up.railway.app/debug | python3 -m json.tool
```

3. Check installed packages and Python environment:
```bash
curl -s https://resourceful-passion-production.up.railway.app/check-env | python3 -c "import sys,json; d=json.load(sys.stdin); print('Python:', d.get('python_version','')); print('Packages:', len(d.get('installed_packages',[])))"
```

4. Test yt-dlp and ffmpeg availability:
```bash
curl -s https://gapintel-api-production.up.railway.app/test | python3 -m json.tool
```
