---
description: Deploy changes to Railway and verify the deployment
---
# Deploy to Railway

## Steps

1. Commit all changes in the railway-api folder:
```bash
cd /Users/yvesromano/AiRAG && git add railway-api/ && git commit -m "Update railway-api"
```

2. Push to trigger Railway deployment:
```bash
git push origin main
```

3. Wait ~60 seconds for Railway to build

// turbo
4. Verify the deployment is healthy:
```bash
curl -s https://resourceful-passion-production.up.railway.app/health
```

// turbo
5. Check debug info to confirm env vars are set:
```bash
curl -s https://gapintel-api-production.up.railway.app/debug | python3 -m json.tool
```
