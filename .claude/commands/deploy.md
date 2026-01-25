# Smart Deploy

Deploy changes to Railway. This commits all current changes (respecting .gitignore) and pushes to main to trigger a Railway deployment.

## Steps

1. **Stage all changes**
```bash
git add .
```

2. **Commit changes**
```bash
git commit -m "Deploy: Update codebase" || echo "No changes to commit"
```

3. **Push to trigger Railway deployment**
```bash
git push origin main
```

4. **Wait for build to start** (approx 10s)
```bash
sleep 10
```

5. **Verify deployment health**
```bash
curl -s https://thriving-presence-production-ca4a.up.railway.app/health
```

## Notes
- Railway automatically deploys on push to main
- Check Railway dashboard for build logs if deployment fails
