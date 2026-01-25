# 🚀 GAP Intel - Go Public & Ads Readiness Checklist

A comprehensive guide to prepare the platform for public traffic and paid advertising.

---

## 1. Critical Technical Fixes (Must Do First)
Stop major bugs that will cause refunds or failed reports.
- [x] **Fix Thumbnail Persistence**: Ensure thumbnails appear in reports (Current active task).
- [ ] **Verify API Key Handling**: Ensure backend picks up `.env` changes (Google GenAI key fix verified).
- [ ] **Test Full End-to-End Flow**:
    - [ ] Run a test purchase/analysis with a real channel.
    - [ ] Verify email delivery (Welcome + Report Ready emails).
    - [ ] Verify report link opens correctly for unauthenticated users.
- [ ] **Error Handling**: actively verify that failed YouTube API calls (e.g., private videos, quota limits) fail gracefully with a specific user-friendly error message, not a generic "Internal Server Error".

## 2. Infrastructure & Reliability
Ensure the site doesn't crash when ads start running.
- [ ] **Environment Variables**:
    - [ ] Double-check all production keys in Railway Dashboard (not just local `.env`).
    - [ ] Ensure `NEXT_PUBLIC_APP_URL` and `RAILWAY_API_URL` are correct for production.
- [ ] **Database Maintenance**:
    - [ ] Run `/manage-database` workflow to ensure indices are optimized.
    - [ ] Verify backups are enabled on Supabase.
- [ ] **Cleanup**:
    - [ ] Remove debug scripts (`debug_server.py`, `check_tjr.py`) from production deployment or ensure `process.env.NODE_ENV` blocks them.
    - [ ] Secure or disable `/api/debug/config` endpoint in production.

## 3. Legal & Compliance (Mandatory for Ads)
Ad platforms (Google/Meta) will disapprove ads without these.
- [ ] **Privacy Policy**: Ensure it's reachable from the footer and landing page. Must mention data collection (email, YouTube public data).
- [ ] **Terms of Service**: Reachable from footer. Define "one-time payment" clearly (no hidden subscriptions).
- [ ] **Cookie Banner**: If using analytics/pixel, ensure a basic consent banner exists (especially for EU/UK traffic).
- [ ] **Contact Info**: A valid support email or contact form must be visible (builds trust and required by some ad networks).

## 4. Frontend & User Experience
First impressions matter.
- [ ] **Mobile Responsiveness**: Test the Landing Page and Report View on an actual phone (iPhone + Android).
    - [ ] Check text sizing.
    - [ ] Check chart rendering on small screens.
- [ ] **Social Proof**: Ensure testimonials or "Trusted by" sections look legitimate.
- [ ] **Loading States**: Verify the "Analyzing..." spinner/progress bar works smoothly and doesn't freeze the UI.
- [ ] **Favicon & Metadata**:
    - [ ] Verify correct Favicon shows in browser tab.
    - [ ] Check `og:image` (social share image) - if a user shares their report or the homepage on Twitter/WhatsApp, does it look good?

## 5. Marketing & Tracking (The "Ads" Part)
Don't spend $1 until you can track results.
- [ ] **Google Analytics 4**: Install and verify it is recording visits.
- [ ] **Meta/TikTok Pixel**: Install if you plan to run social ads later.
- [ ] **Conversion Tracking**:
    - [ ] **Purchase Event**: Ensure Stripe purchase triggers a "Purchase" event in GA4/Pixels (or redirect to a `/thank-you` page that fires the event).
    - [ ] **Lead Event**: Track when users hit "Analyze" (even if they don't pay yet).

## 6. Post-Launch Operations
- [ ] **Monitoring**: Set up a way to get notified if the server goes down (Railway has uptime alerts, or use UptimeRobot).
- [ ] **Support Channel**: Decide how you will handle "It didn't work" emails (e.g., a dedicated `support@gapintel.online` inbox).
