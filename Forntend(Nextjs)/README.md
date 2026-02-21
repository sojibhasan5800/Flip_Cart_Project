


```markdown
# FlipCart Frontend – Modern SaaS E-Commerce Dashboard & Storefront

![FlipCart Frontend Banner](https://via.placeholder.com/1200x400/0d1117/58a6ff?text=FlipCart+Frontend)

**Next-generation responsive frontend** for multi-tenant e-commerce SaaS platform — merchant dashboard, admin panel, and public storefront.

Live Demo: [https://flip-cart-project-frontend.onrender.com](https://flip-cart-project-frontend.onrender.com)

## ✨ Core Features & Highlights

- **Multi-tenant aware routing** — automatic subdomain detection & API base URL switching
- **JWT Authentication + Auto Refresh** — seamless login experience with refresh token rotation
- **Real-time Seller Dashboard** — live product analytics & order updates via WebSocket
- **Modern UI/UX** — fully responsive, mobile-first design
- **State Management** — Redux Toolkit for cart, products, auth state
- **Beautiful Components** — Product cards, counters, charts, modals, toast notifications

## 🛠 Tech Stack (2025–2026 Cutting Edge)

- Next.js 14+ (App Router, Server & Client Components)
- React 18 + TypeScript
- Redux Toolkit + React-Redux
- Tailwind CSS + MUI (Material-UI) hybrid styling
- Axios with interceptors (JWT refresh, tenant-aware baseURL)
- react-hot-toast (notifications)
- lucide-react (icons)
- Clerk (optional auth wrapper)

## 🔥 Performance & Developer Experience

- Fast page loads with Next.js App Router & automatic code-splitting
- Smooth JWT token refresh without user interruption
- Tenant subdomain routing logic in Axios → no manual baseURL change
- Responsive breakpoints (mobile → desktop) with Tailwind + MUI
- Loading states, error handling, toast feedback everywhere

## 🚀 Planned / Upcoming Features (Roadmap)

- **AI Product Recommendation Carousel** on homepage
- **Real-time Order & Chat Notifications** (WebSocket integration)
- **Dark Mode** + Theme switcher
- **PWA Support** (offline browsing, installable)
- **Advanced Search with Autocomplete** (powered by backend ES)
- **Seller Analytics Dashboard** with charts (Recharts / ApexCharts)
- **Multi-language Support** (next-intl)
- **Server-side Rendering (SSR)** for SEO-heavy product pages

## 🏁 Quick Start (Local Development)

```bash
# 1. Clone & enter directory
git clone https://github.com/yourusername/gocart-frontend.git
cd gocart-frontend

# 2. Install dependencies
npm install

# 3. Copy & configure .env.local
cp .env.example .env.local
# Edit .env.local → NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/

# 4. Run development server
npm run dev