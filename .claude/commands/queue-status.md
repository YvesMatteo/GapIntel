# Queue Status

Check the current status of the analysis queue on Railway.

## Steps

1. **Check queue status endpoint**
```bash
curl -s https://thriving-presence-production-ca4a.up.railway.app/queue-status | python3 -m json.tool
```

2. **Check for pending analyses in Supabase**
```bash
curl -s "https://thriving-presence-production-ca4a.up.railway.app/api/analyses?status=pending" | python3 -m json.tool
```

3. **Check for processing analyses**
```bash
curl -s "https://thriving-presence-production-ca4a.up.railway.app/api/analyses?status=processing" | python3 -m json.tool
```

## Queue States
- **pending**: Waiting to be picked up
- **processing**: Currently being analyzed
- **completed**: Successfully finished
- **failed**: Error occurred during analysis

## Notes
- Analyses taking >30 minutes are considered "stuck"
- Use `/reset-analysis` to reset stuck jobs
- Use `/stuck-jobs` for detailed stuck job diagnostics
