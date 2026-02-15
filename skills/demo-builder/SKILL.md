---
name: demo-builder
description: "Build complete demo projects from scratch. Takes a project description (presentation website, shop, dashboard, SaaS, portfolio, etc.) and scaffolds a full working Next.js + Tailwind CSS 3.4 app ready for Vercel deployment. Supports optional database integration when a DATABASE_URL is provided. Use when the user wants to build a demo, create a project, scaffold an app, prototype something, or spin up a quick site."
---

# Demo Builder

Build complete, production-ready demo projects from scratch using **Next.js 14 (App Router) + Tailwind CSS 3.4.1**, optimized for **Vercel** deployment. Takes a project concept and delivers a fully functional, styled application.

## Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 14.x |
| Styling | Tailwind CSS | 3.4.19 |
| Language | TypeScript | 5.x |
| Deployment | Vercel | latest |
| Database ORM | Prisma | latest (when DB provided) |
| Auth (optional) | NextAuth.js | 4.x |
| Icons | Lucide React | latest |

## Workflow

When the user describes what they want to build, follow this exact sequence:

### Step 1: Clarify the Project

Ask the user (if not already clear):
1. **What is the project?** — e.g., "a portfolio site", "an e-commerce shop", "a SaaS dashboard"
2. **Database URL?** — If they provide one, enable full database integration with Prisma
3. **Any specific pages or features?** — e.g., "landing page, pricing, blog", "product listings, cart, checkout"

### Step 2: Scaffold the Project

```bash
npx create-next-app@14 <project-name> \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --no-turbo
```

Then pin Tailwind CSS to 3.4.1:

```bash
cd <project-name>
npm install tailwindcss@3.4.1 postcss autoprefixer
```

### Step 3: Configure Tailwind

Use this `tailwind.config.ts` as the base, customizing colors/fonts per project type:

```ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
          950: "#082f49",
        },
        accent: {
          50: "#fdf4ff",
          100: "#fae8ff",
          200: "#f5d0fe",
          300: "#f0abfc",
          400: "#e879f9",
          500: "#d946ef",
          600: "#c026d3",
          700: "#a21caf",
          800: "#86198f",
          900: "#701a75",
          950: "#4a044e",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

### Step 4: Set Up Project Structure

Create the base file structure:

```
src/
  app/
    layout.tsx          # Root layout with fonts, metadata
    page.tsx            # Home/landing page
    globals.css         # Tailwind directives + custom styles
    favicon.ico
  components/
    ui/                 # Reusable UI primitives
      button.tsx
      card.tsx
      input.tsx
      badge.tsx
      container.tsx
    layout/             # Layout components
      navbar.tsx
      footer.tsx
      sidebar.tsx       # (if dashboard-style)
  lib/
    utils.ts            # cn() helper, formatters
    constants.ts        # Site config, nav links
  types/
    index.ts            # Shared TypeScript types
```

### Step 5: Build Core Components

#### cn() Utility

```ts
// src/lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

Install dependencies:

```bash
npm install clsx tailwind-merge lucide-react
```

#### Root Layout

```tsx
// src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";

const inter = Inter({ subsets: ["latin"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  title: "Project Name",
  description: "Project description",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <Navbar />
        <main className="min-h-screen">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
```

#### Globals CSS

```css
/* src/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-gray-200;
  }
  body {
    @apply bg-white text-gray-900;
  }
}

@layer components {
  .container-default {
    @apply mx-auto max-w-7xl px-4 sm:px-6 lg:px-8;
  }
  .section-padding {
    @apply py-16 sm:py-20 lg:py-24;
  }
}
```

### Step 6: Database Integration (When DATABASE_URL Provided)

If the user provides a database URL, set up Prisma:

```bash
npm install prisma @prisma/client
npx prisma init
```

Create the Prisma client singleton:

```ts
// src/lib/db.ts
import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const db = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = db;
```

Add `DATABASE_URL` to `.env`:

```env
DATABASE_URL="<user-provided-url>"
```

Then design the Prisma schema based on the project type:

**E-commerce example:**
```prisma
model Product {
  id          String   @id @default(cuid())
  name        String
  description String?
  price       Float
  image       String?
  category    String?
  inStock     Boolean  @default(true)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}

model Order {
  id        String      @id @default(cuid())
  total     Float
  status    String      @default("pending")
  items     OrderItem[]
  createdAt DateTime    @default(now())
}

model OrderItem {
  id        String  @id @default(cuid())
  quantity  Int
  price     Float
  productId String
  orderId   String
  order     Order   @relation(fields: [orderId], references: [id])
}
```

**Dashboard example:**
```prisma
model User {
  id        String   @id @default(cuid())
  name      String
  email     String   @unique
  role      String   @default("user")
  createdAt DateTime @default(now())
}

model Metric {
  id        String   @id @default(cuid())
  name      String
  value     Float
  category  String
  date      DateTime @default(now())
}
```

After defining the schema:

```bash
npx prisma db push
npx prisma generate
```

Create API routes for CRUD operations:

```ts
// src/app/api/<resource>/route.ts
import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export async function GET() {
  const items = await db.<model>.findMany({
    orderBy: { createdAt: "desc" },
  });
  return NextResponse.json(items);
}

export async function POST(request: Request) {
  const body = await request.json();
  const item = await db.<model>.create({ data: body });
  return NextResponse.json(item, { status: 201 });
}
```

## Project Templates

Adapt the build based on what the user asks for:

### Landing Page / Presentation Website
- Hero section with CTA
- Features grid (3-4 cards)
- Testimonials section
- Pricing table (if relevant)
- FAQ accordion
- Contact / CTA footer section
- Responsive navbar with mobile menu

### E-Commerce / Shop
- Product listing grid with filters
- Product detail page
- Shopping cart (client-side state or DB-backed)
- Checkout flow
- Category navigation
- Search functionality
- If DATABASE_URL: full Prisma product/order models + API routes

### Dashboard / Admin Panel
- Sidebar navigation
- Stats/metrics cards at top
- Data tables with sorting/filtering
- Charts placeholder (recommend recharts)
- User management section
- If DATABASE_URL: real data from Prisma queries via server components

### SaaS Application
- Marketing landing page
- Feature comparison
- Pricing tiers
- Auth pages (login/signup layouts)
- Dashboard shell
- Settings page
- If DATABASE_URL: user + subscription models

### Portfolio
- Hero with name/title/avatar
- Project showcase grid
- About section
- Skills/tech stack display
- Contact form
- Blog section (optional)

### Blog
- Post listing with thumbnails
- Post detail with MDX-like layout
- Category/tag filtering
- Author info
- If DATABASE_URL: posts + categories models

## Vercel Deployment Readiness

Every project must include:

1. **`vercel.json`** (only if custom config needed):
```json
{
  "framework": "nextjs"
}
```

2. **Environment variables documentation** in README:
```markdown
## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | No | Database connection string |
```

3. **Proper `next.config.mjs`**:
```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
};

export default nextConfig;
```

4. **Generated README.md** with:
   - Project description
   - Tech stack
   - Setup instructions (`npm install`, `npm run dev`)
   - Environment variables table
   - Deployment instructions

## Quality Standards

### Every demo project MUST have:
- [ ] Fully responsive design (mobile-first)
- [ ] Semantic HTML with proper heading hierarchy
- [ ] Consistent spacing using Tailwind's spacing scale
- [ ] Hover/focus states on all interactive elements
- [ ] Loading states where appropriate
- [ ] Proper TypeScript types (no `any`)
- [ ] Clean component structure (one component per file)
- [ ] Accessible markup (alt text, aria labels, focus management)
- [ ] Working navigation between all pages
- [ ] Placeholder content that looks realistic (not lorem ipsum where avoidable)

### Code quality:
- [ ] No unused imports or variables
- [ ] Consistent naming conventions (PascalCase components, camelCase functions)
- [ ] Server Components by default, `"use client"` only when needed
- [ ] Proper error boundaries for data-fetching pages
- [ ] SEO metadata on every page

## Build Verification

After building the project, always run:

```bash
npm run build
```

Fix any TypeScript or build errors before presenting the project to the user. The project must compile cleanly.

Then start the dev server to verify:

```bash
npm run dev
```

Confirm the app loads correctly at `http://localhost:3000`.
