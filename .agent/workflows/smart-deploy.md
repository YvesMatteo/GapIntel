---
description: Intelligent deployment to Railway that only pushes relevant changes
---

# Smart Deploy

This workflow commits all current changes (respecting .gitignore to avoid large files) and pushes to main to trigger a Railway deployment.

## Steps

1. Add all tracked and new files (respecting gitignore)
```bash
git add .
```

2. Commit changes
```bash
git commit -m "Smart deploy: Update codebase" || echo "No changes to commit"
```

3. Push to trigger Railway deployment
```bash
git push origin main
```

4. Wait for build to start (approx 10s)
```bash
sleep 10
```

// turbo
5. Verify deployment health (Backend)
```bash
curl -s https://resourceful-passion-production.up.railway.app/health
```
