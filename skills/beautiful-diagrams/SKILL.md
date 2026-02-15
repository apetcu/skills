---
name: beautiful-diagrams
description: "Generate beautiful article diagrams (pipeline, sequence, grid) using HTML + Playwright. Canvas background, gradient service cards, clean professional style. Use when creating architecture diagrams, sequence diagrams, token/secret maps, or any visual diagram for articles. Triggers: 'create diagram', 'generate diagram', 'make architecture diagram', 'build sequence diagram', 'create a visual', 'diagram for article'."
---

# Beautiful Diagrams

Generate professional article diagrams using HTML + Playwright screenshots. Clean design: Canvas (#F5F1EC) background, gradient service cards, Inter font, box shadows, emoji icons.

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

### 1. Pipeline (Architecture / Flow)

Horizontal flow of service cards connected by arrows. Great for system architecture, CI/CD pipelines, data flows.

```json
{
  "type": "pipeline",
  "width": 900,
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

## CLI Options

```bash
python scripts/diagram-generator.py [options]
```

| Option | Description |
|--------|-------------|
| `--config FILE` | Path to JSON config file |
| `--stdin` | Read JSON config from stdin |
| `--output, -o FILE` | Output PNG path (required) |
| `--save-html FILE` | Also save the generated HTML |

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

## Tips

- Keep node/actor names short (1-2 words) for best readability
- Use `components` in pipeline nodes to show sub-services within a larger service
- Use `phase` steps in sequence diagrams to label sections
- Grid diagrams with `connections` work best with 2 columns
- The `--save-html` option is useful for manual tweaks in a browser before screenshotting
- Use `trigger: true` on the first pipeline node for user-initiated flows

## Cost

**Free!** No API costs. Runs locally with Playwright.
