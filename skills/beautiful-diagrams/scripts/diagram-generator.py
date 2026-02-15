#!/usr/bin/env python3
"""
Generate beautiful article diagrams using HTML + Playwright screenshots.
Design: Canvas (#F5F1EC) background, gradient service cards, Inter font,
box shadows, emoji icons, brand colors.

Supports three diagram types:
  - pipeline: Horizontal flow of service cards with connectors
  - sequence: Vertical sequence diagram with actors, lifelines, messages
  - grid: Card grid layout with items and connections

Usage:
    python diagram-generator.py --config diagram.json -o diagram.png
    echo '{"type":"pipeline",...}' | python diagram-generator.py --stdin -o diagram.png
"""

import argparse
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

FONT_STACK = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif"
MONO_STACK = "'SF Mono', 'Fira Code', 'Consolas', monospace"
CANVAS_BG = "#F5F1EC"
CHARCOAL = "#36454F"

# Pre-defined service color palettes (name -> [gradient_start, gradient_end])
SERVICE_COLORS = {
    "slack": ["#4A154B", "#3a1040"],
    "cloudflare": ["#F48120", "#d06a10"],
    "github": ["#2d333b", "#1a1e22"],
    "jira": ["#0052CC", "#003d99"],
    "linkedin": ["#0077B5", "#005a8c"],
    "claude": ["#D97706", "#b56305"],
    "aws": ["#FF9900", "#cc7a00"],
    "gcp": ["#4285F4", "#2a6acf"],
    "azure": ["#0078D4", "#005a9e"],
    "vercel": ["#000000", "#1a1a1a"],
    "docker": ["#2496ED", "#1a7ac4"],
    "redis": ["#DC382D", "#b02d24"],
    "postgres": ["#336791", "#264d6e"],
    "mongodb": ["#47A248", "#378a38"],
    "stripe": ["#635BFF", "#4a44cc"],
    "teal": ["#008B8B", "#006d6d"],
    "cobalt": ["#1E4CA1", "#163a7a"],
    "bronze": ["#CD7F32", "#a86628"],
}


def resolve_color(color_input):
    """Resolve a color to [start, end] gradient pair.

    Accepts:
      - A preset name: "slack", "github", etc.
      - A single hex: "#FF0000" -> ["#FF0000", darker shade]
      - A list of two hex codes: ["#FF0000", "#CC0000"]
    """
    if isinstance(color_input, list) and len(color_input) == 2:
        return color_input
    if isinstance(color_input, str):
        lower = color_input.lower().strip("#")
        # Check presets
        if lower in SERVICE_COLORS:
            return SERVICE_COLORS[lower]
        # Single hex -> darken for gradient end
        hex_color = color_input if color_input.startswith("#") else f"#{color_input}"
        return [hex_color, _darken(hex_color, 0.2)]
    return ["#36454F", "#2a363f"]


def _darken(hex_color, factor=0.2):
    """Darken a hex color by a factor."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten(hex_color, factor=0.3):
    """Lighten a hex color by a factor."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# Pipeline diagram
# ---------------------------------------------------------------------------

def generate_pipeline(config):
    """Generate a horizontal pipeline/architecture diagram.

    Config shape:
    {
        "type": "pipeline",
        "width": 900,           (optional, default 900)
        "nodes": [
            {
                "name": "Service Name",
                "desc": "Short description",       (optional)
                "icon": "emoji",                    (optional)
                "color": "preset" | "#hex" | ["#start","#end"],
                "trigger": true,                    (optional, renders as top trigger box)
                "width": 130,                       (optional)
                "components": [                     (optional, sub-items inside the card)
                    {"name": "Sub Name", "desc": "Sub desc", "icon": "emoji", "tag": "LABEL"}
                ]
            }
        ],
        "connectors": [
            {
                "label": "text on arrow",           (optional)
                "bidirectional": false,              (optional)
                "forward_label": "text",            (for bidirectional)
                "reverse_label": "text"             (for bidirectional)
            }
        ]
    }
    """
    nodes = config.get("nodes", [])
    connectors = config.get("connectors", [])
    width = config.get("width", 900)

    # Build node HTML
    node_htmls = []
    for i, node in enumerate(nodes):
        colors = resolve_color(node.get("color", "github"))
        node_w = node.get("width", 130)
        icon = node.get("icon", "")
        name = node.get("name", "")
        desc = node.get("desc", "")
        components = node.get("components", [])
        trigger = node.get("trigger", False)

        icon_html = f'<div class="icon">{icon}</div>' if icon else ""
        desc_html = f'<div class="desc">{desc}</div>' if desc else ""

        # Trigger node: top trigger box + vertical arrow + optional child card below
        if trigger:
            trigger_desc = desc
            trigger_desc_html = f'<div class="cmd">{trigger_desc}</div>' if trigger_desc else ""
            node_html = f"""
  <div class="slack-col">
    <div class="trigger" style="background: linear-gradient(135deg, {colors[0]}, {colors[1]});">
      {f'<div class="icon">{icon}</div>' if icon else ""}
      <div>
        <div class="text">{name}</div>
        {trigger_desc_html}
      </div>
    </div>
    <div class="v-arrow"></div>
    <div style="height: 5px;"></div>"""
            # Render child card below the trigger if specified
            child = node.get("child")
            if child:
                ch_colors = resolve_color(child.get("color", "github"))
                ch_icon = child.get("icon", "")
                ch_name = child.get("name", "")
                ch_desc = child.get("desc", "")
                ch_w = child.get("width", 130)
                ch_icon_html = f'<div class="icon">{ch_icon}</div>' if ch_icon else ""
                ch_desc_html = f'<div class="desc">{ch_desc}</div>' if ch_desc else ""
                node_html += f"""
    <div class="service" style="background: linear-gradient(135deg, {ch_colors[0]}, {ch_colors[1]}); width: {ch_w}px;">
      <div class="service-header">
        {ch_icon_html}
        <div>
          <div class="name">{ch_name}</div>
          {ch_desc_html}
        </div>
      </div>
    </div>"""
            node_html += "\n  </div>"
            node_htmls.append(node_html)
            continue

        # Components card (expanded, like GitHub in the example)
        if components:
            comp_html = '<div class="components">'
            for comp in components:
                comp_icon = comp.get("icon", "")
                comp_name = comp.get("name", "")
                comp_desc = comp.get("desc", "")
                comp_tag = comp.get("tag", "")
                tag_html = f'<div class="cat-tag">{comp_tag}</div>' if comp_tag else ""
                comp_html += f"""
      <div class="comp">
        <div class="comp-icon">{comp_icon}</div>
        <div>
          <div class="comp-name">{comp_name}</div>
          <div class="comp-desc">{comp_desc}</div>
        </div>
        {tag_html}
      </div>"""
            comp_html += "\n    </div>"

            node_html = f"""
  <div class="service" style="background: linear-gradient(135deg, {colors[0]}, {colors[1]}); flex: 1;">
    <div class="service-header">
      {icon_html}
      <div>
        <div class="name">{name}</div>
        {desc_html}
      </div>
    </div>
    {comp_html}
  </div>"""
        else:
            node_html = f"""
  <div class="service service-mid" style="background: linear-gradient(135deg, {colors[0]}, {colors[1]}); width: {node_w}px;">
    <div class="service-header">
      {icon_html}
      <div>
        <div class="name">{name}</div>
        {desc_html}
      </div>
    </div>
  </div>"""

        node_htmls.append(node_html)

    # Build connectors HTML (placed between nodes)
    connector_htmls = []
    for conn in connectors:
        bidi = conn.get("bidirectional", False)
        if bidi:
            fwd = conn.get("forward_label", "")
            rev = conn.get("reverse_label", "")
            connector_htmls.append(f"""
  <div class="bidi">
    <div class="arrow-fwd">
      <div class="label fwd-label">{fwd}</div>
      <div class="line"></div>
    </div>
    <div class="arrow-rev">
      <div class="line"></div>
      <div class="label rev-label">{rev}</div>
    </div>
  </div>""")
        else:
            label = conn.get("label", "")
            label_html = f'<div class="label">{label}</div>' if label else ""
            connector_htmls.append(f"""
  <div class="connector">
    {label_html}
    <div class="line"></div>
  </div>""")

    # Interleave nodes and connectors
    body_parts = []
    for i, node_html in enumerate(node_htmls):
        body_parts.append(node_html)
        if i < len(connector_htmls):
            body_parts.append(connector_htmls[i])

    body_content = "\n".join(body_parts)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: {width}px;
    padding: 20px 24px 20px;
    background: {CANVAS_BG};
    font-family: {FONT_STACK};
  }}
  .pipeline {{
    display: flex;
    align-items: flex-end;
    width: 100%;
  }}
  .slack-col {{
    display: flex;
    flex-direction: column;
    align-items: center;
    flex-shrink: 0;
  }}
  .trigger {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 18px;
    border-radius: 10px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.15), 0 1px 3px rgba(0,0,0,0.08);
  }}
  .trigger .icon {{ font-size: 18px; }}
  .trigger .text {{
    font-size: 13px;
    font-weight: 700;
    color: #fff;
  }}
  .trigger .cmd {{
    font-size: 11px;
    color: rgba(255,255,255,0.75);
    font-family: {MONO_STACK};
  }}
  .v-arrow {{
    width: 2px;
    height: 18px;
    background: {CHARCOAL};
    position: relative;
  }}
  .v-arrow::after {{
    content: '';
    position: absolute;
    bottom: -5px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {CHARCOAL};
  }}
  .service {{
    border-radius: 12px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.12), 0 1px 3px rgba(0,0,0,0.08);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    flex-shrink: 0;
  }}
  .service-header {{
    padding: 12px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .service-header .icon {{
    width: 26px;
    height: 26px;
    border-radius: 6px;
    background: rgba(255,255,255,0.18);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    flex-shrink: 0;
  }}
  .service-header .name {{
    font-size: 13px;
    font-weight: 700;
    color: #fff;
  }}
  .service-header .desc {{
    font-size: 10px;
    color: rgba(255,255,255,0.7);
    margin-top: 1px;
  }}
  .components {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 0 10px 10px;
  }}
  .comp {{
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 7px;
    padding: 7px 10px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .comp .comp-icon {{
    font-size: 12px;
    flex-shrink: 0;
  }}
  .comp .comp-name {{
    font-size: 11px;
    font-weight: 600;
    color: #fff;
  }}
  .comp .comp-desc {{
    font-size: 9px;
    color: rgba(255,255,255,0.55);
  }}
  .cat-tag {{
    font-size: 8px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: rgba(255,255,255,0.45);
    padding: 2px 6px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    margin-left: auto;
  }}
  .connector {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-width: 68px;
    padding: 0 4px;
    flex-shrink: 0;
    margin-bottom: 18px;
  }}
  .connector .label {{
    font-size: 9px;
    color: {CHARCOAL};
    font-weight: 500;
    white-space: nowrap;
    margin-bottom: 3px;
    background: {CANVAS_BG};
    padding: 0 3px;
  }}
  .connector .line {{
    width: 100%;
    height: 2px;
    background: {CHARCOAL};
    position: relative;
  }}
  .connector .line::after {{
    content: '';
    position: absolute;
    right: -1px;
    top: 50%;
    transform: translateY(-50%);
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    border-left: 6px solid {CHARCOAL};
  }}
  .bidi {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-width: 80px;
    padding: 0 4px;
    flex-shrink: 0;
    gap: 6px;
    margin-bottom: 10px;
  }}
  .bidi .arrow-fwd, .bidi .arrow-rev {{
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
  }}
  .bidi .label {{
    font-size: 9px;
    color: {CHARCOAL};
    font-weight: 500;
    white-space: nowrap;
  }}
  .bidi .fwd-label {{ margin-bottom: 2px; }}
  .bidi .rev-label {{ margin-top: 2px; }}
  .bidi .line {{
    width: 100%;
    height: 2px;
    background: {CHARCOAL};
    position: relative;
  }}
  .bidi .arrow-fwd .line::after {{
    content: '';
    position: absolute;
    right: -1px;
    top: 50%;
    transform: translateY(-50%);
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    border-left: 6px solid {CHARCOAL};
  }}
  .bidi .arrow-rev .line::after {{
    content: '';
    position: absolute;
    left: -1px;
    top: 50%;
    transform: translateY(-50%);
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    border-right: 6px solid {CHARCOAL};
  }}
  .service-mid {{
    margin-bottom: 6px;
  }}
</style>
</head>
<body>
<div class="pipeline">
{body_content}
</div>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Sequence diagram
# ---------------------------------------------------------------------------

def generate_sequence(config):
    """Generate a sequence diagram with actors, lifelines, and messages.

    Config shape:
    {
        "type": "sequence",
        "width": 890,           (optional, default 890)
        "actors": [
            {"name": "Developer", "color": "preset" | "#hex" | ["#start","#end"]}
        ],
        "steps": [
            {"type": "message", "from": 0, "to": 1, "label": "text", "style": "solid"|"dashed"},
            {"type": "self", "actor": 2, "label": "Verify signature"},
            {"type": "note", "over": 3, "text": "Note text<br>Line 2"},
            {"type": "phase", "label": "PHASE NAME"},
            {"type": "spacer"}
        ]
    }
    """
    actors = config.get("actors", [])
    steps = config.get("steps", [])
    width = config.get("width", 890)
    n_actors = len(actors)

    # Calculate actor positions (evenly spaced)
    padding = 32
    usable = width - 2 * padding
    actor_w = 110
    if n_actors > 1:
        spacing = usable / (n_actors - 1)
    else:
        spacing = 0
    centers = [padding + i * spacing for i in range(n_actors)]

    # Actor HTML
    actor_html_parts = []
    for i, actor in enumerate(actors):
        colors = resolve_color(actor.get("color", "cobalt"))
        name = actor.get("name", "")
        actor_html_parts.append(
            f'    <div class="actor" style="background: linear-gradient(135deg, {colors[0]}, {colors[1]});">'
            f'<div class="name">{name}</div></div>'
        )
    actors_html = "\n".join(actor_html_parts)

    # Lifeline lines
    lifeline_divs = '<div class="line"></div>' * n_actors
    lifeline_bg = f"""    <div class="lifeline-bg">
      {lifeline_divs}
    </div>"""

    # Position classes
    pos_css = ""
    for i, c in enumerate(centers):
        pos_css += f"  .from-{i} {{ left: {int(c)}px; }}\n"

    # Steps HTML
    step_htmls = []
    for step in steps:
        stype = step.get("type", "message")

        if stype == "message":
            frm = step["from"]
            to = step["to"]
            label = step.get("label", "")
            style = step.get("style", "solid")
            left_idx = min(frm, to)
            right_idx = max(frm, to)
            left_pos = centers[left_idx]
            msg_width = centers[right_idx] - centers[left_idx]
            going_left = to < frm
            arrow_class = "left" if going_left else ""
            arrow_html = (
                f'<div class="arrow-head {arrow_class}"></div>'
            )
            label_style = ""
            if style == "dashed":
                label_style = ' style="color: #008B8B;"'
            step_htmls.append(f"""      <div class="step">
        <div class="msg {style}" style="left: {int(left_pos)}px; width: {int(msg_width)}px;">
          <div class="line"></div>{arrow_html}
          <div class="msg-label"{label_style}>{label}</div>
        </div>
      </div>""")

        elif stype == "self":
            actor_idx = step["actor"]
            label = step.get("label", "")
            pos = centers[actor_idx] - 27
            step_htmls.append(f"""      <div class="step" style="min-height: 24px;">
        <div style="position: absolute; left: {int(pos)}px; top: 0; font-size: 10px; color: {CHARCOAL}; font-style: italic; background: {CANVAS_BG}; padding: 2px 6px; border-radius: 4px; border: 1px solid #c4b8aa;">
          {label}
        </div>
      </div>""")

        elif stype == "note":
            over_idx = step["over"]
            text = step.get("text", "")
            margin_left = int(centers[over_idx]) - 60
            step_htmls.append(f"""      <div class="spacer"></div>
      <div class="note-box" style="margin-left: {margin_left}px;">{text}</div>""")

        elif stype == "phase":
            label = step.get("label", "")
            step_htmls.append(f"""      <div class="phase-label">{label}</div>""")

        elif stype == "spacer":
            step_htmls.append('      <div class="spacer"></div>')

    steps_html = "\n".join(step_htmls)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: {width}px;
    padding: 40px {padding}px 48px;
    background: {CANVAS_BG};
    font-family: {FONT_STACK};
  }}
  .diagram {{ position: relative; }}
  .actors {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 0;
    position: relative;
    z-index: 2;
  }}
  .actor {{
    width: {actor_w}px;
    padding: 12px 6px;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 3px 12px rgba(0,0,0,0.10);
  }}
  .actor .name {{ font-size: 12px; font-weight: 700; color: #fff; line-height: 1.2; }}
  .lifelines {{
    position: relative;
    margin-top: 0;
  }}
  .lifeline-bg {{
    position: absolute;
    top: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: space-between;
    z-index: 0;
    pointer-events: none;
  }}
  .lifeline-bg .line {{
    width: {actor_w}px;
    display: flex;
    justify-content: center;
  }}
  .lifeline-bg .line::after {{
    content: '';
    width: 2px;
    height: 100%;
    background: repeating-linear-gradient(to bottom, #c4b8aa 0px, #c4b8aa 6px, transparent 6px, transparent 12px);
  }}
  .steps {{
    position: relative;
    z-index: 1;
    padding: 16px 0;
  }}
  .step {{
    display: flex;
    align-items: center;
    margin: 10px 0;
    min-height: 32px;
    position: relative;
  }}
  .msg {{
    position: absolute;
    height: 2px;
    z-index: 1;
  }}
  .msg .line {{
    height: 2px;
    width: 100%;
  }}
  .msg.solid .line {{ background: {CHARCOAL}; }}
  .msg.dashed .line {{ background: repeating-linear-gradient(to right, {CHARCOAL} 0px, {CHARCOAL} 6px, transparent 6px, transparent 12px); }}
  .msg .arrow-head {{
    position: absolute;
    right: -1px;
    top: 50%;
    transform: translateY(-50%);
    width: 0; height: 0;
    border-top: 5px solid transparent;
    border-bottom: 5px solid transparent;
    border-left: 8px solid {CHARCOAL};
  }}
  .msg .arrow-head.left {{
    left: -1px;
    right: auto;
    border-left: none;
    border-right: 8px solid {CHARCOAL};
  }}
  .msg-label {{
    font-size: 11px;
    color: {CHARCOAL};
    white-space: nowrap;
    position: absolute;
    top: -16px;
    left: 50%;
    transform: translateX(-50%);
    font-weight: 500;
    background: {CANVAS_BG};
    padding: 0 4px;
  }}
  .note-box {{
    margin: 12px auto;
    padding: 10px 20px;
    border-radius: 8px;
    background: #D7EEFF;
    border: 1.5px solid #0077B5;
    text-align: center;
    font-size: 12px;
    color: {CHARCOAL};
    font-weight: 500;
    width: fit-content;
    position: relative;
    z-index: 1;
    line-height: 1.5;
  }}
  .spacer {{ height: 8px; }}
  .phase-label {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #008B8B;
    margin: 16px 0 4px 55px;
    position: relative;
    z-index: 1;
  }}
{pos_css}
</style>
</head>
<body>
<div class="diagram">
  <div class="actors">
{actors_html}
  </div>
  <div class="lifelines">
{lifeline_bg}
    <div class="steps">
{steps_html}
      <div class="spacer"></div>
    </div>
  </div>
</div>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Grid diagram
# ---------------------------------------------------------------------------

def generate_grid(config):
    """Generate a grid layout of service cards with items and connections.

    Config shape:
    {
        "type": "grid",
        "width": 800,           (optional, default 800)
        "columns": 2,           (optional, default 2)
        "cards": [
            {
                "name": "Service Name",
                "icon": "emoji",
                "color": "preset" | "#hex" | ["#start","#end"],
                "items": [
                    {"name": "TOKEN_NAME", "hint": "Where to find it", "badge": "optional"}
                ]
            }
        ],
        "connections": [            (optional, renders as arrow row between card rows)
            {"from": "Label A", "to": "Label B"},
            {"from": "Label C", "to": "Label D", "dashed": true}
        ]
    }
    """
    cards = config.get("cards", [])
    connections = config.get("connections", [])
    columns = config.get("columns", 2)
    width = config.get("width", 800)

    # Card HTML
    card_htmls = []
    for card in cards:
        colors = resolve_color(card.get("color", "github"))
        icon = card.get("icon", "")
        name = card.get("name", "")
        items = card.get("items", [])

        icon_html = f'<div class="icon">{icon}</div>' if icon else ""

        items_html = ""
        for item in items:
            badge = item.get("badge", "")
            badge_html = f' <span class="badge">{badge}</span>' if badge else ""
            hint = item.get("hint", "")
            hint_html = f'<div class="hint">{hint}</div>' if hint else ""
            items_html += f"""    <div class="token">
      {item.get("name", "")}{badge_html}
      {hint_html}
    </div>
"""

        card_htmls.append(f"""  <div class="service" style="background: linear-gradient(135deg, {colors[0]}, {colors[1]});">
    <div class="service-header">
      {icon_html}
      {name}
    </div>
{items_html}  </div>""")

    # Connection arrows row
    conn_html = ""
    if connections:
        arrow_items = []
        for conn in connections:
            dashed = "dashed" if conn.get("dashed", False) else ""
            arrow_items.append(f"""    <div class="arrow-item">
      <span>{conn.get("from", "")}</span>
      <div class="arrow-line {dashed}"></div>
      <span>{conn.get("to", "")}</span>
    </div>""")
        conn_html = f"""  <div class="arrows">
{chr(10).join(arrow_items)}
  </div>"""

    # Split cards into rows and insert connections between row 0 and row 1
    rows = []
    for i in range(0, len(card_htmls), columns):
        rows.append(card_htmls[i:i + columns])

    body_parts = []
    for i, row in enumerate(rows):
        body_parts.extend(row)
        # Insert connections after first row
        if i == 0 and conn_html:
            body_parts.append(conn_html)

    body_content = "\n".join(body_parts)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: {width}px;
    padding: 40px 32px;
    background: {CANVAS_BG};
    font-family: {FONT_STACK};
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat({columns}, 1fr);
    gap: 24px;
  }}
  .service {{
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.10), 0 1px 4px rgba(0,0,0,0.06);
  }}
  .service-header {{
    font-size: 15px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .service-header .icon {{
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: rgba(255,255,255,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
  }}
  .token {{
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 13px;
    font-weight: 600;
    color: #fff;
    font-family: {MONO_STACK};
    letter-spacing: -0.02em;
  }}
  .token .hint {{
    font-family: {FONT_STACK};
    font-size: 11px;
    font-weight: 400;
    color: rgba(255,255,255,0.7);
    margin-top: 3px;
    letter-spacing: 0;
  }}
  .token:last-child {{ margin-bottom: 0; }}
  .badge {{
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(255,255,255,0.2);
    color: rgba(255,255,255,0.8);
    margin-left: 4px;
    vertical-align: middle;
  }}
  .arrows {{
    grid-column: 1 / -1;
    display: flex;
    justify-content: center;
    gap: 48px;
    padding: 8px 0;
  }}
  .arrow-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: {CHARCOAL};
    font-weight: 500;
  }}
  .arrow-line {{
    width: 40px;
    height: 2px;
    background: {CHARCOAL};
    position: relative;
  }}
  .arrow-line::after {{
    content: '';
    position: absolute;
    right: -1px;
    top: 50%;
    transform: translateY(-50%);
    border-top: 4px solid transparent;
    border-bottom: 4px solid transparent;
    border-left: 6px solid {CHARCOAL};
  }}
  .arrow-line.dashed {{
    background: repeating-linear-gradient(to right, {CHARCOAL} 0px, {CHARCOAL} 4px, transparent 4px, transparent 8px);
  }}
</style>
</head>
<body>
<div class="grid">
{body_content}
</div>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------

def screenshot_html(html, output_path, width):
    """Render HTML and take a full-page screenshot with Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 800})
        page.set_content(html)
        page.wait_for_function("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(200)
        page.screenshot(path=output_path, full_page=True)
        browser.close()
    print(f"Diagram generated: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

GENERATORS = {
    "pipeline": generate_pipeline,
    "sequence": generate_sequence,
    "grid": generate_grid,
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate beautiful article diagrams (pipeline, sequence, grid)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Diagram types:
  pipeline  - Horizontal flow of service cards with connectors
  sequence  - Sequence diagram with actors, lifelines, messages, phases
  grid      - Card grid with items and connection arrows

Examples:
  %(prog)s --config architecture.json -o diagram.png
  %(prog)s --config sequence.json -o sequence.png
  %(prog)s --config tokens.json --save-html tokens.html -o tokens.png
        """
    )
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    parser.add_argument("--output", "-o", required=True, help="Output PNG path")
    parser.add_argument("--save-html", help="Also save the generated HTML to this path")

    args = parser.parse_args()

    if args.stdin:
        config = json.load(sys.stdin)
    elif args.config:
        with open(args.config) as f:
            config = json.load(f)
    else:
        print("Error: provide --config FILE or --stdin", file=sys.stderr)
        sys.exit(1)

    diagram_type = config.get("type", "pipeline")
    generator = GENERATORS.get(diagram_type)
    if not generator:
        print(f"Error: unknown diagram type '{diagram_type}'. Use: {', '.join(GENERATORS.keys())}", file=sys.stderr)
        sys.exit(1)

    html = generator(config)

    if args.save_html:
        Path(args.save_html).write_text(html, encoding="utf-8")
        print(f"HTML saved: {args.save_html}")

    width = config.get("width", 900)
    screenshot_html(html, args.output, width)


if __name__ == "__main__":
    main()
