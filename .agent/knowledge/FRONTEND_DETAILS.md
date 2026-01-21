# GAP Intel: Frontend Deep Dive

The GAP Intel frontend is a modern, high-performance web application built with Next.js 14, located in `gap-intel-website/`.

## Architecture

- **Framework**: Next.js 14 (App Router)
- **Styling**: Vanilla CSS for core design + Tailwind CSS for utility-based adjustments. Features a heavy emphasis on "Glassmorphism" and premium dark aesthetics.
- **State Management**: React Hooks + Context API where needed.
- **Data Fetching**: Server Components for SEO-critical pages, Client Components with standard `fetch` for interactive dashboards.

## Directory Structure (`src/`)

### 1. `app/` (Routes & Pages)
- **`page.tsx`**: The mission-critical landing page. Highly optimized for conversion with interactive demos, feature sections, and pricing.
- **`dashboard/`**: The user's home base. Allows users to start new analyses, view pending tasks, and access their library of reports.
- **`report/[id]/page.tsx`**: The core value-delivery page. Displays the complex JSON output from the backend through interactive charts and organized sections:
    - **Header**: Channel stats and overall opportunity score.
    - **Gap Cards**: High-signal opportunities with viral titles and evidence.
    - **Charts**: Recharts-based visualizations of engagement, sentiment, and growth patterns.
    - **Competitor Section**: Side-by-side benchmarking.
- **`viral-predictor/`**: A standalone tool for users to test their titles and hooks against trained models.

### 2. `components/` (UI Library)
- **`navigation/`**: Responsive navbar and footer.
- **`charts/`**: Custom wrappers for Recharts (Area, Bar, Pie charts).
- **`ui/`**: Specialized components like `OpportunityCard`, `MetricCard`, and `StatusBadge`.
- **`modals/`**: Payment prompts, analysis triggers, and feedback forms.

### 3. `lib/` (Core Utilities)
- `supabase.ts`: Client-side initialization for database interaction.
- `utils.ts`: Formatting helpers (currency, numbers, dates).
- `api.ts`: Centralized logic for talking to the Railway API.

---

## Design System

The application uses a custom design system defined in `src/app/globals.css`. Key tokens include:
- **Primary Color**: `#7c3aed` (Violet)
- **Secondary Color**: `#00d4ff` (Cyan)
- **Background**: Deep black/navy gradient (`#030303` to `#0a0a0f`).
- **Surface**: Translucent glass effect with subtle borders.

## User Flow

1.  **Landing**: User discovers the value prop on the homepage.
2.  **Auth**: User logs in via Google/Email (Supabase).
3.  **Submission**: User submits a YouTube handle or pastes a list of video IDs.
4.  **Wait**: Frontend polls the Railway API for status updates, showing a "Processing" state.
5.  **View**: Once completed, the user is redirected to the `report/` page to explore their data-backed opportunities.
