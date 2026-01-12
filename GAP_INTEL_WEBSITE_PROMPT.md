# GAP Intel Website - Full Stack Development Prompt

## 🎯 Project Overview

Build a modern, premium SaaS website for **GAP Intel** - a YouTube content gap analysis tool. Users pay once via Stripe to receive an AI-powered analysis of their YouTube channel, identifying content opportunities.

---

## 📱 User Flow

```
1. Landing Page → User enters @ChannelName + Email
2. → Redirected to Stripe Payment Link
3. → After payment, Stripe webhook triggers analysis + generates unique access key
4. → User receives email with access key
5. → User enters key on website → Views their personalized GAP Report dashboard
```

---

## 🎨 Design Requirements

### Design Reference
Use the uploaded design template as the primary UI inspiration.

### Brand Identity
- **Logo**: `/Users/yvesromano/.gemini/antigravity/brain/b479d675-1d0a-40b8-a000-e3a2c9c68ed9/gap_intel_logo_1767396308510.png`
- **Primary colors**: 
  - Dark cards: `#1a1a2e` to `#16213e`
  - Mint green accent: `#7cffb2` / `#a8e6cf`
  - Purple secondary: `#b8b8ff` / `#9d94ff`
  - Background: `#e8ebe4` (muted sage)
- **Style**: 
  - Bento-grid card layout
  - Glassmorphism effects on cards
  - Large rounded corners (16-24px)
  - Modern sans-serif typography (Inter or Outfit from Google Fonts)
  - Subtle shadows and hover animations
  - Mobile-first responsive design

### Key UI Elements
- Dark stat cards with charts (like "Sales statistics" card)
- Light cards with green accents for positive metrics
- Timeline/roadmap components
- Progress bars and gauges
- Mini charts and sparklines
- Clean data tables with subtle styling

---

## 🛠 Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS + custom CSS for glassmorphism
- **Charts**: Recharts or Chart.js for data visualization
- **Animations**: Framer Motion for micro-interactions

### Backend
- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Auth (for admin, optional)
- **Storage**: Supabase Storage (for generated reports)
- **Edge Functions**: Supabase Edge Functions (for Stripe webhook handling)

### Payments
- **Stripe Payment Links** (no custom checkout needed)
- **Stripe Webhooks** for payment confirmation

### Hosting (Free during development)
- **Vercel** (free tier) - integrates perfectly with Next.js
- Custom domain DNS ready for later

---

## 📊 Database Schema (Supabase)

```sql
-- Analyses table
CREATE TABLE analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP DEFAULT NOW(),
  
  -- User info
  channel_name TEXT NOT NULL,
  email TEXT NOT NULL,
  
  -- Payment
  stripe_payment_id TEXT UNIQUE,
  stripe_customer_id TEXT,
  amount_paid INTEGER, -- in cents
  payment_status TEXT DEFAULT 'pending', -- pending, completed, failed
  
  -- Access
  access_key TEXT UNIQUE NOT NULL,
  key_used_at TIMESTAMP,
  
  -- Analysis
  analysis_status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
  analysis_result JSONB, -- The full GAP report data
  report_generated_at TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_analyses_access_key ON analyses(access_key);
CREATE INDEX idx_analyses_stripe_payment_id ON analyses(stripe_payment_id);
CREATE INDEX idx_analyses_email ON analyses(email);

-- RLS policies
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

-- Allow reading own analysis with valid access key (handled via API)
```

---

## 📄 Pages to Build

### 1. Landing Page (`/`)
- Hero section with tagline: "Discover Your Channel's Hidden Content Opportunities"
- Simple form: `@ChannelName` input + `Email` input
- CTA button: "Get Your Analysis - $XX" → redirects to Stripe
- Features section (3-4 cards explaining what they get)
- Social proof / testimonials section (can be placeholder)
- Footer with links

### 2. Payment Success Page (`/success`)
- Triggered after Stripe payment (via redirect)
- Shows: "Payment received! Check your email for your access key"
- Also displays the access key directly on this page
- Button to go to analysis page

### 3. Access Analysis Page (`/analysis` or `/report`)
- Input field for access key
- Submit button
- On valid key → renders the full GAP Report dashboard

### 4. Analysis Dashboard (`/analysis/[key]`)
- Beautiful dashboard displaying the GAP Report data
- Sections to display:
  - **Header**: Channel name, date generated, videos analyzed count
  - **Pipeline Stats Card** (dark card): Raw comments, High-signal, Pain points, TRUE GAPS counts
  - **#1 Verified Opportunity** (highlighted green card): Title, engagement potential, reasoning
  - **Content Gaps Grid**: Cards for each gap with status badges (TRUE_GAP / UNDER_EXPLAINED)
  - **Already Covered Topics**: Collapsible list
  - **Videos Analyzed**: List with links
  - **Competitors Analyzed**: List

---

## 🔗 Stripe Integration

### Setup Required (User provides):
- Stripe API keys (publishable + secret)
- Create a Stripe Product + Price
- Create a Stripe Payment Link with the following:
  - Custom fields: `channel_name`, `email` (collect on Stripe checkout)
  - Success URL: `https://[your-domain]/success?session_id={CHECKOUT_SESSION_ID}`
  - Webhook endpoint: `https://[your-domain]/api/webhook/stripe`

### Webhook Handler (`/api/webhook/stripe`)
```typescript
// This endpoint should:
1. Verify Stripe webhook signature
2. Handle `checkout.session.completed` event
3. Extract channel_name, email from custom fields
4. Generate unique access key (e.g., `GAP-${nanoid(12)}`)
5. Create row in Supabase `analyses` table
6. Trigger analysis (call existing Python pipeline or queue job)
7. Send email to user with access key (use Resend, SendGrid, or Supabase Edge Functions)
```

---

## 📧 Email Notification

After successful payment, send an email containing:
- Subject: "Your GAP Intel Analysis is Ready! 🎯"
- Body:
  - Thank you message
  - Their access key prominently displayed
  - Link to the analysis page
  - Expected processing time (if analysis is async)

**Options for email sending:**
- Resend (simple, modern API)
- Supabase Edge Functions with SMTP
- SendGrid

---

## 📋 Analysis Data Format

The analysis is a markdown report that should be parsed and displayed beautifully. Here's the JSON structure to expect:

```typescript
interface GapReport {
  channelName: string;
  generatedAt: string;
  videosAnalyzed: number;
  
  pipeline: {
    rawComments: number;
    highSignal: number;
    painPoints: number;
    trueGaps: number;
    underExplained: number;
    alreadyCovered: number;
  };
  
  topOpportunity: {
    topic: string;
    suggestedTitle: string;
    engagementPotential: number;
    reasoning: string;
  };
  
  contentGaps: Array<{
    rank: number;
    topic: string;
    status: 'TRUE_GAP' | 'UNDER_EXPLAINED';
    userStruggle: string;
    engagement: number;
    verification: string;
    reasoning: string;
    suggestedTitles: string[];
  }>;
  
  alreadyCovered: Array<{
    topic: string;
    explanation: string;
  }>;
  
  videosAnalyzed: Array<{
    title: string;
    comments: number;
    url: string;
  }>;
  
  competitors: string[];
}
```

---

## 🌐 Environment Variables

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PAYMENT_LINK=

# Email (if using Resend)
RESEND_API_KEY=

# App
NEXT_PUBLIC_APP_URL=https://your-domain.vercel.app
```

---

## 🚀 Deployment Steps

### Phase 1: Development
1. Set up Next.js project with Tailwind CSS
2. Create Supabase project and run schema migrations
3. Build all UI components and pages
4. Integrate Stripe Payment Link + webhook
5. Test full flow with Stripe test mode
6. Deploy to Vercel (free tier)

### Phase 2: Custom Domain (Later)
1. User provides custom domain
2. Add domain in Vercel dashboard
3. Update DNS records (CNAME or A record)
4. Update Stripe webhook URL
5. Update success redirect URL

---

## ✅ Acceptance Criteria

- [ ] Landing page matches the design aesthetic (dark cards, green accents, bento grid)
- [ ] Form collects @ChannelName and Email
- [ ] Stripe payment flow works end-to-end (test mode)
- [ ] Webhook creates database entry and generates access key
- [ ] Email is sent with access key (or displayed on success page)
- [ ] Access key unlocks the analysis dashboard
- [ ] Dashboard beautifully displays all GAP report sections
- [ ] Mobile responsive on all pages
- [ ] Deployed on Vercel with working URL
- [ ] Ready for custom domain attachment

---

## 📝 Additional Notes

- The Python analysis pipeline already exists - just need to trigger it (provide details separately)
- For MVP, the analysis can be manually triggered or queued
- Future: Real-time analysis status updates via Supabase Realtime
- Consider rate limiting on the API routes

---

## 🎨 Design Reference Image
![UI Design Template](/Users/yvesromano/.gemini/antigravity/brain/133692aa-7949-4774-ba6a-1da3de3dd82a/uploaded_image_1767396406196.png)

The design should capture this aesthetic: modern bento-grid layout, dark cards with data visualizations, mint green and purple accent colors, clean typography, subtle shadows, and professional SaaS feel.
