---
name: beautiful-diagrams
description: "Generate beautiful article diagrams (pipeline, sequence, grid) using HTML + Playwright. Dark minimal design, wireframe service cards, structural grid, near-monochrome palette. Use when creating architecture diagrams, sequence diagrams, token/secret maps, or any visual diagram for articles. Triggers: 'create diagram', 'generate diagram', 'make architecture diagram', 'build sequence diagram', 'create a visual', 'diagram for article'."
---

# Beautiful Diagrams

Generate professional article diagrams using HTML + Playwright screenshots. Dark minimal design: flat dark background (#0F0F0F), structural grid, wireframe service cards with accent-color borders, Inter bold typography, near-monochrome palette.

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

You can also use raw hex colors: `"#FF5733"` or gradient pairs: `["#FF5733", "#C70039"]`

**Note:** Color presets now control the card's border accent color (at 20% opacity), not gradient fill.

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

## Fixed-Size Diagrams (IMPORTANT)

**Always set `height` in the JSON config for article images.** Without it, the generator uses `full_page: true` which captures the content height and often results in diagrams with dead space or content crammed at the top.

For LinkedIn article images, always use:
- `"width": 1200, "height": 627` (landscape 16:9)
- `"width": 1080, "height": 1080` (square)
- `"width": 1080, "height": 1350` (carousel 4:5)

When `height` is set, the body gets flexbox centering and the screenshot clips to the exact dimensions. Content fills the canvas properly with no dead space.

## Tips

- **Always set `height`** in configs for article images to avoid dead space
- Keep node/actor names short (1-2 words) for best readability
- Use `components` in pipeline nodes to show sub-services within a larger service
- Use `phase` steps in sequence diagrams to label sections
- Grid diagrams with `connections` work best with 2 columns
- The `--save-html` option is useful for manual tweaks in a browser before screenshotting
- Use `trigger: true` on the first pipeline node for user-initiated flows

## Cost

**Free!** No API costs. Runs locally with Playwright.
