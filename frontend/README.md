# BOTUVIC Dashboard

Next.js 14 dashboard with clean animations and modern UI.

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Create `.env.local`:**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your API URL and Supabase keys
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   ```
   http://localhost:3000
   ```

## Features

✅ **Clean Design** - Purple/Cyan theme with smooth animations
✅ **Metrics Cards** - Projects, tasks, AI calls, errors
✅ **Project List** - Status indicators, progress bars
✅ **Activity Graph** - Weekly/monthly charts
✅ **Responsive** - Mobile-friendly
✅ **Animations** - Fade-in, slide-up, hover effects
✅ **API Integration** - Connected to FastAPI backend

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- Recharts
- Lucide Icons

## Project Structure

```
app/
├── layout.tsx          # Root layout
├── page.tsx              # Dashboard home
├── login/
│   └── page.tsx         # Login page
└── settings/
    └── page.tsx         # Settings page

components/
├── Header.tsx           # Top bar
├── ProfileDropdown.tsx  # Profile menu
├── MetricsCards.tsx    # Metric cards
├── ProjectList.tsx     # Project list
└── ActivityGraph.tsx   # Activity chart

lib/
└── api.ts              # API client
```
