---
name: beautiful-diagrams
description: "Generate beautiful article diagrams using HTML + Playwright. Five layouts: pipeline (horizontal flow), sequence (actors + messages), grid (2-col cards), stack (numbered hero cards), comparison (before/after). Bold white carousel style with thick black borders, terracotta accents, chunky rounded cards, and LARGE Inter 900 typography. Use when creating architecture diagrams, sequence diagrams, numbered lists, before/after comparisons, or any visual for articles. Triggers: 'create diagram', 'generate diagram', 'make architecture diagram', 'build sequence diagram', 'numbered list diagram', 'comparison diagram', 'create a visual', 'diagram for article'."
---

# Beautiful Diagrams

Generate professional article diagrams using HTML + Playwright screenshots.

**Style: bold white carousel.** White background, thick black borders (3-4px), chunky rounded cards with 6px drop shadows, terracotta (`#E27D5B`) icon tiles, Inter 900 typography at large sizes. Designed to be readable in-feed on LinkedIn / Substack, not a reader-hostile monitoring UI.

**Design tokens:**

| Token | Value | Use |
|-------|-------|-----|
| `BG_WHITE` | `#FFFFFF` | Canvas + card fill |
| `INK` | `#0A0A0A` | Text, borders, arrows |
| `INK_SOFT` | `#2A2A2A` | Secondary text |
| `INK_MUTED` | `#5A5A5A` | Hints, tertiary text |
| `ACCENT` | `#E27D5B` | Icon tiles, connector chips, badges |
| `ACCENT_SOFT` | `#F3D4C6` | Note boxes |

**Typography:** Inter (400–900 weights), loaded from Google Fonts. Headings use weight 900 at 24-28px. Body text is 14-18px. Connector labels and badges are uppercase bold at 11-14px on accent pills. Nothing smaller than 13px.

**Rules:**
1. NEVER use small fonts. If content doesn't fit, increase the canvas width or drop the fixed height — don't shrink the text.
2. Thick borders (3-4px) on everything. No hairlines.
3. Cards have a 6-7px solid black offset shadow (no blur, no gradients).
4. Icon tiles are rounded squares (14px radius) with 4px black borders and terracotta fill.
5. Connector labels are small uppercase pills on terracotta with black borders.
6. Use the `color` field to override an individual card/node's accent. Default is terracotta.

## Requirements

```bash
pip install playwright
python -m playwright install chromium
```

## Quick Start

```bash
python scripts/diagram-generator.py --config diagram.json -o diagram.png
```

## Diagram Types

### Icons (IBM Carbon Design System)

The `icon` field in JSON configs supports **IBM Carbon icon names** (preferred) or emoji fallback. Use Carbon icon names for a professional, monoline look.

**Available Carbon icons:**

| Name | Description | Name | Description |
|------|-------------|------|-------------|
| `document` | Generic document | `document-tasks` | Document with checkmark |
| `compass` | Navigation/architecture | `machine-learning` | ML/AI model |
| `activity` | Activity/heartbeat | `branch` | Git branch/merge |
| `renew` | Refresh/loop | `flash` | Lightning/fast |
| `cognitive` | Brain/AI | `rule` | Shield/rules |
| `code` | Code brackets | `settings` | Gear/config |
| `deploy` | Deploy/house | `cloud` | Cloud service |
| `api` | API endpoint | `terminal` | Terminal/CLI |
| `data` | Database/storage | `user` | User/person |
| `rocket` | Launch/deploy | `search` | Search/find |
| `warning` | Alert/warning | `checkmark` | Success/done |
| `close` | Close/error | `send` | Send/message |
| `notification` | Bell/alert | `network` | Network/nodes |

**Usage:** Set `"icon": "branch"` instead of `"icon": "🔀"`. Emoji still works as fallback.

### 1. Pipeline (Architecture / Flow)

Horizontal flow of service cards connected by arrows. Great for system architecture, CI/CD pipelines, data flows.

```json
{
  "type": "pipeline",
  "width": 900,
  "height": 627,
  "nodes": [
    {
      "name": "Developer",
      "desc": "/deploy prod",
      "icon": "👨‍💻",
      "color": "linkedin",
      "trigger": true,
      "child": {
        "name": "Slack",
        "desc": "Slash Command",
        "icon": "💬",
        "color": "slack",
        "width": 130
      }
    },
    {
      "name": "GitHub",
      "desc": "CI/CD",
      "icon": "⚙️",
      "color": "github",
      "components": [
        {"name": "Actions", "desc": "Run tests & build", "icon": "🔄", "tag": "CI"},
        {"name": "Deploy", "desc": "Push to production", "icon": "🚀", "tag": "CD"}
      ]
    },
    {
      "name": "AWS",
      "desc": "Hosting",
      "icon": "☁️",
      "color": "aws"
    }
  ],
  "connectors": [
    {"label": "git push"},
    {"label": "deploy"}
  ]
}
```

**Node options:**
- `name` - Service name (required)
- `desc` - Short description (optional)
- `icon` - Emoji icon (optional)
- `color` - Color preset or hex (see Colors below)
- `trigger` - If true, renders as a top trigger box with vertical arrow down
- `child` - When `trigger` is true, a service card rendered below the trigger (has name, desc, icon, color, width)
- `width` - Override card width in px (default 130)
- `components` - Sub-items inside the card (each has name, desc, icon, tag)

**Connector options:**
- `label` - Text on the arrow (optional)
- `bidirectional` - Two-way arrow (default false)
- `forward_label` / `reverse_label` - Labels for bidirectional arrows

### 2. Sequence

Sequence diagram with actors, lifelines, phase labels, messages, and notes. Great for API flows, request/response chains, workflow steps.

```json
{
  "type": "sequence",
  "width": 890,
  "actors": [
    {"name": "Client", "color": "linkedin"},
    {"name": "API Gateway", "color": "cloudflare"},
    {"name": "Auth Service", "color": "teal"},
    {"name": "Database", "color": "postgres"}
  ],
  "steps": [
    {"type": "phase", "label": "Authentication"},
    {"type": "message", "from": 0, "to": 1, "label": "POST /login", "style": "solid"},
    {"type": "message", "from": 1, "to": 2, "label": "validate token", "style": "solid"},
    {"type": "message", "from": 2, "to": 1, "label": "200 OK", "style": "dashed"},
    {"type": "spacer"},
    {"type": "phase", "label": "Data Fetch"},
    {"type": "message", "from": 1, "to": 3, "label": "SELECT * FROM users", "style": "solid"},
    {"type": "note", "over": 3, "text": "Query executes<br>Index scan on email"}
  ]
}
```

**Step types:**
- `message` - Arrow between two actors: `from` (index), `to` (index), `label`, `style` ("solid" | "dashed")
- `self` - Self-referencing note on an actor: `actor` (index), `label`
- `note` - Highlighted note box: `over` (actor index), `text` (supports `<br>`)
- `phase` - Section label in teal: `label`
- `spacer` - Vertical spacing

### 3. Grid (Tokens / Secrets / Config Map)

Card grid with items inside each card, plus optional connection arrows. Great for secrets/tokens maps, config overviews, feature comparisons.

```json
{
  "type": "grid",
  "width": 800,
  "columns": 2,
  "cards": [
    {
      "name": "Environment Variables",
      "icon": "🔧",
      "color": "github",
      "items": [
        {"name": "DATABASE_URL", "hint": "PostgreSQL connection string"},
        {"name": "REDIS_URL", "hint": "Redis cache endpoint"},
        {"name": "DEBUG", "hint": "Set to false in production", "badge": "optional"}
      ]
    },
    {
      "name": "API Keys",
      "icon": "🔑",
      "color": "cobalt",
      "items": [
        {"name": "OPENAI_API_KEY", "hint": "From platform.openai.com"},
        {"name": "STRIPE_SECRET", "hint": "Dashboard → Developers → API keys"}
      ]
    }
  ],
  "connections": [
    {"from": "DATABASE_URL", "to": "PostgreSQL"},
    {"from": "REDIS_URL", "to": "Redis", "dashed": true}
  ]
}
```

**Card options:**
- `name` - Card title (required)
- `icon` - Emoji icon (optional)
- `color` - Color preset or hex
- `items` - List of items, each with `name`, `hint` (optional), `badge` (optional)

**Connection options:**
- `from` / `to` - Label text on each side of the arrow
- `dashed` - Dashed line style (default false)

### 4. Stack (Numbered Hero Cards)

Vertical stack of big numbered cards. Perfect for "3 lessons", "5 principles", "N reasons why" articles — each item gets full-width treatment with a large 72px number, icon tile, bold title, and descriptive subtitle.

```json
{
  "type": "stack",
  "width": 1200,
  "title": "Optional heading above the stack",
  "items": [
    {
      "number": "01",
      "icon": "close",
      "color": "terracotta",
      "name": "Item title",
      "desc": "Longer explanation that wraps to multiple lines if needed."
    },
    {
      "icon": "activity",
      "color": "teal",
      "name": "Second item",
      "desc": "number is auto-generated when omitted"
    }
  ]
}
```

**Item options:**
- `number` - Display number (optional, auto-generated as "01", "02", ... if omitted)
- `icon` - Carbon icon name or emoji (optional)
- `color` - Accent color for the icon tile (optional, default terracotta)
- `name` - Item title, required
- `desc` - Longer description (optional)

**Sizing tip:** use `width: 1200` and omit `height` — stack auto-sizes to content. For 3-item stacks expect ~700px height, for 5-item ~1100px.

### 5. Comparison (Before / After, A vs B)

Two-column head-to-head comparison with a divider pill in the middle. Use for before/after migrations, naive vs optimized approaches, old vs new workflows.

```json
{
  "type": "comparison",
  "width": 1200,
  "title": "Optional heading",
  "divider": "VS",
  "left": {
    "name": "Before",
    "icon": "close",
    "color": "github",
    "items": [
      "Simple string item",
      {"name": "Item with hint", "hint": "Longer explanation under the name"}
    ]
  },
  "right": {
    "name": "After",
    "icon": "checkmark",
    "color": "teal",
    "items": [
      "Better approach",
      {"name": "With context", "hint": "why it's better"}
    ]
  }
}
```

**Column options:**
- `name` - Column header title, required
- `icon` - Carbon icon name or emoji (optional)
- `color` - Accent color for the icon tile (optional, default terracotta)
- `items` - List of strings OR `{name, hint}` objects

**Top-level options:**
- `title` - Heading above the comparison (optional)
- `divider` - Text shown in the center pill (default `"VS"`). Use `"→"`, `"THEN"`, `"NOW"`, etc.

## Color Presets

Use these preset names in the `color` field:

| Preset | Colors | Best for |
|--------|--------|----------|
| `slack` | Purple | Slack, messaging |
| `cloudflare` | Orange | Cloudflare, CDN |
| `github` | Dark gray | GitHub, Git, SCM |
| `jira` | Blue | Jira, Atlassian |
| `linkedin` | LinkedIn Blue | LinkedIn, social |
| `claude` | Amber | Claude, AI tools |
| `aws` | Orange | AWS services |
| `gcp` | Blue | Google Cloud |
| `azure` | Blue | Microsoft Azure |
| `vercel` | Black | Vercel, hosting |
| `docker` | Blue | Docker, containers |
| `redis` | Red | Redis, caching |
| `postgres` | Blue-gray | PostgreSQL |
| `mongodb` | Green | MongoDB |
| `stripe` | Purple | Stripe, payments |
| `teal` | Teal | Innovation, AI themes |
| `cobalt` | Deep blue | Authority, headers |
| `bronze` | Bronze | Achievements |

You can also use raw hex colors: `"#FF5733"`. Legacy two-item lists `["#FF5733", "#C70039"]` are still accepted (first value wins).

**Default:** If `color` is omitted, the card uses `terracotta` (`#E27D5B`). The color fills the icon tile; card borders and text are always solid black.

## CLI Options

```bash
python scripts/diagram-generator.py [options]
```

| Option | Description |
|--------|-------------|
| `--config FILE` | Path to JSON config file |
| `--stdin` | Read JSON config from stdin |
| `--output, -o FILE` | Output PNG or GIF path (required) |
| `--save-html FILE` | Also save the generated HTML |
| `--gif` | Capture as animated GIF (requires ffmpeg). Also saves a `_static.png` |
| `--gif-duration MS` | Animation duration in ms (default 5500) |
| `--gif-fps N` | Frames per second (default 10) |

## Animated GIF Output

For diagrams with CSS animations (flowing particles, pulse effects, fade-ins), use `--gif` to capture as an animated GIF. Also saves a static PNG of the final frame automatically.

**Requirements:** `ffmpeg` (`brew install ffmpeg`)

**CLI usage:**
```bash
python scripts/diagram-generator.py --config diagram.json --gif -o diagram.gif
python scripts/diagram-generator.py --config diagram.json --gif --gif-duration 6000 --gif-fps 12 -o diagram.gif
```

**JSON config:**
```json
{
  "type": "pipeline",
  "animated": true,
  "gif_duration": 5500,
  "gif_fps": 10,
  "width": 1200,
  "height": 627,
  "nodes": [...]
}
```

Setting `"animated": true` in the config has the same effect as `--gif`. The generator captures frames at the specified FPS for the duration, then assembles them into a GIF with ffmpeg.

**Output files:**
- `diagram.gif` - Animated GIF
- `diagram_static.png` - Static final frame (useful for Substack covers which don't support GIF)

**Tips:**
- Add CSS `@keyframes` animations to your HTML for flowing particles, pulse rings, fade-ins
- 10fps at 5.5 seconds (55 frames) keeps GIF size under 200KB
- Use `height` in config (required for GIF mode)

## Workflow

1. **Determine diagram type** from user's description: pipeline (flow/architecture), sequence (interactions/steps), or grid (config/tokens/comparison)
2. **Build the JSON config** with nodes, actors, or cards as appropriate
3. **Save the JSON** to the article's `files/` folder (e.g., `diagram_architecture.json`)
4. **Run the generator** to create the PNG
5. **Optionally save HTML** with `--save-html` for future editing

## Examples

**Architecture diagram for an article:**
```bash
python scripts/diagram-generator.py \
  --config posts/daily-thoughts/09-fix-my-bug/files/diagram_architecture.json \
  --save-html posts/daily-thoughts/09-fix-my-bug/files/diagram_architecture.html \
  -o posts/daily-thoughts/09-fix-my-bug/files/diagram_architecture.png
```

**Quick diagram from inline JSON:**
```bash
echo '{"type":"pipeline","nodes":[{"name":"A","icon":"📦","color":"github"},{"name":"B","icon":"🚀","color":"teal"}],"connectors":[{"label":"deploy"}]}' | \
  python scripts/diagram-generator.py --stdin -o quick-diagram.png
```

## Sizing (IMPORTANT)

The bold style uses large typography and chunky cards, so the default canvas should be WIDER than the old dark-minimal style. Recommended starting points:

- **Pipeline (horizontal flow)**: `"width": 1400-1600`, `"height": 520-600`. For 4+ nodes prefer 1500+.
- **Grid (2 columns × 2 rows)**: `"width": 1200`, OMIT `height` (let it auto-size to content).
- **Grid (2 × 3+ rows)**: `"width": 1200`, omit height.
- **Sequence**: `"width": 1200-1400`, omit height for short flows, set 800-1000 for long ones.
- **Stack (numbered cards)**: `"width": 1200`, omit height. 3-item stacks land ~700px, 5-item ~1100px.
- **Comparison (two columns)**: `"width": 1200-1400`, omit height. Each column should hold 3-5 items for best balance.

**Rule of thumb:** if content looks cramped, INCREASE the width. Do NOT shrink the font sizes — they are deliberately large so the diagrams are readable in-feed on LinkedIn and Substack.

**When to set `height`:**
- Fixed aspect ratio for a cover image (e.g., 1200×627 for LinkedIn landscape).
- GIF mode — height is required.
- Otherwise omit it and let the content define the height.

## Tips

- Increase canvas width before shrinking content. Small fonts are a regression.
- Keep node/actor names short (1-3 words) — the bold weight eats horizontal space fast.
- Use `components` in pipeline nodes to show sub-services within a larger card.
- Use `phase` steps in sequence diagrams to label sections (renders as an accent pill).
- Grid diagrams with `connections` work best with 2 columns.
- `--save-html` saves the generated HTML for manual tweaks in a browser.
- Use `trigger: true` on the first pipeline node for user-initiated flows.

## Cost

**Free!** No API costs. Runs locally with Playwright.
