# Build Frontend

Build the Next.js frontend for production deployment.

## Steps

1. **Install dependencies**
```bash
cd /Users/yvesromano/AiRAG/gap-intel-website && npm install
```

2. **Run type checking**
```bash
cd /Users/yvesromano/AiRAG/gap-intel-website && npx tsc --noEmit
```

3. **Build for production**
```bash
cd /Users/yvesromano/AiRAG/gap-intel-website && npm run build
```

4. **Test the production build locally** (optional)
```bash
cd /Users/yvesromano/AiRAG/gap-intel-website && npm run start
```

## Build Output
- Output directory: `.next/`
- Static assets: `.next/static/`

## Common Build Errors
- **Type errors**: Fix TypeScript issues shown in step 2
- **Missing env vars**: Ensure `.env.local` has required variables
- **Import errors**: Check for circular dependencies

## Notes
- Build must succeed before deploying to Vercel/production
- The build process validates all pages and API routes
- Check `next.config.js` for build configuration
