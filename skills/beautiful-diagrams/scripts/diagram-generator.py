#!/usr/bin/env python3
"""
Generate beautiful article diagrams using HTML + Playwright screenshots.

Bold white carousel style:
- White background, no grid
- Thick black borders (3-4px) on cards
- Terracotta accent fills (#E27D5B) on icon tiles and highlight chips
- Inter 900 typography, LARGE font sizes
- Chunky rounded corners (14-18px)
- Designed to be readable in-feed on LinkedIn / Substack

Supports three diagram types:
  - pipeline: Horizontal flow of bold cards with connectors
  - sequence: Sequence diagram with actors, lifelines, messages
  - grid:     Card grid layout with items

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
# Shared design tokens — bold white carousel style
# ---------------------------------------------------------------------------

FONT_STACK = "'Inter', 'Archivo', 'Segoe UI', system-ui, -apple-system, sans-serif"
MONO_STACK = "'JetBrains Mono', 'SF Mono', 'Fira Code', 'Consolas', monospace"

# Core palette
BG_WHITE = "#FFFFFF"
INK = "#0A0A0A"            # Primary text and borders
INK_SOFT = "#2A2A2A"       # Secondary text
INK_MUTED = "#5A5A5A"      # Tertiary / hint text
ACCENT = "#E27D5B"         # Terracotta default accent
ACCENT_SOFT = "#F3D4C6"    # Light terracotta backdrop
HAIRLINE = "#E5E5E5"       # Thin dividers between items

# Google Fonts link for bolder Inter + Archivo Black fallback
GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Inter:wght@400;500;700;800;900&'
    'family=Archivo:wght@700;800;900&'
    'family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">'
)

# IBM Carbon Design System icons (32px viewBox, inline SVG paths)
CARBON_ICONS = {
    "document": '<path d="M25.7,9.3l-7-7A.908.908,0,0,0,18,2H8A2.0058,2.0058,0,0,0,6,4V28a2.0058,2.0058,0,0,0,2,2H24a2.0058,2.0058,0,0,0,2-2V10A.908.908,0,0,0,25.7,9.3ZM18,4.4,23.6,10H18ZM24,28H8V4h8v6a2.0058,2.0058,0,0,0,2,2h6Z"/>',
    "document-tasks": '<path d="M22 27.18 19.41 24.59 18 26 22 30 30 22 28.59 20.59 22 27.18z"/><path d="M15,28H8V4h8v6a2.0058,2.0058,0,0,0,2,2h6v6h2V10a.9092.9092,0,0,0-.3-.7l-7-7A.9087.9087,0,0,0,18,2H8A2.0058,2.0058,0,0,0,6,4V28a2.0058,2.0058,0,0,0,2,2h7ZM18,4.4,23.6,10H18Z"/>',
    "compass": '<path d="M16,4A12,12,0,1,1,4,16,12,12,0,0,1,16,4m0-2A14,14,0,1,0,30,16,14,14,0,0,0,16,2Z"/><path d="M23,10.41,21.59,9l-4.3,4.3a3,3,0,0,0-4,4L9,21.59,10.41,23l4.3-4.3a3,3,0,0,0,4-4ZM17,16a1,1,0,1,1-1-1A1,1,0,0,1,17,16Z"/><circle cx="16" cy="7.5" r="1.5"/>',
    "machine-learning": '<path d="M27,19c1.6543,0,3-1.3457,3-3s-1.3457-3-3-3c-1.302,0-2.4016.8384-2.8157,2h-5.7703l7.3008-7.3008c.3911.1875.8235.3008,1.2852.3008,1.6543,0,3-1.3457,3-3s-1.3457-3-3-3-3,1.3457-3,3c0,.4619.1135.894.3005,1.2852l-8.3005,8.3008v-6.5859c0-1.1025.897-2,2-2h2v-2h-2c-1.2002,0-2.2661.5425-3,1.3823-.7339-.8398-1.7998-1.3823-3-1.3823h-1c-4.9624,0-9,4.0371-9,9v6c0,4.9629,4.0376,9,9,9h1c1.2002,0,2.2661-.5425,3-1.3823.7339.8398,1.7998,1.3823,3,1.3823h2v-2h-2c-1.103,0-2-.8975-2-2v-6.5859l8.3005,8.3008c-.187.3911-.3005.8232-.3005,1.2852,0,1.6543,1.3457,3,3,3s3-1.3457,3-3-1.3457-3-3-3c-.4617,0-.894.1133-1.2852.3008l-7.3008-7.3008h5.7703c.4141,1.1616,1.5137,2,2.8157,2Z"/>',
    "activity": '<path d="M12,29a1,1,0,0,1-.92-.62L6.33,17H2V15H7a1,1,0,0,1,.92.62L12,25.28,20.06,3.65A1,1,0,0,1,21,3a1,1,0,0,1,.93.68L25.72,15H30v2H25a1,1,0,0,1-.95-.68L21,7,12.94,28.35A1,1,0,0,1,12,29Z"/>',
    "branch": '<path d="m20,6c0,1.8587,1.2795,3.4109,3,3.858v4.142c0,1.6543-1.3457,3-3,3h-8c-1.1299,0-2.1617.391-3,1.0256v-8.1676c1.7203-.4471,3-1.9993,3-3.858,0-2.2061-1.7944-4-4-4s-4,1.7939-4,4c0,1.8587,1.2797,3.4108,3,3.858v12.142s0,.142,0,.142c-1.7203.4473-3,1.9997-3,3.858,0,2.2056,1.7944,4,4,4s4-1.7944,4-4c0-1.8583-1.2797-3.4107-3-3.858v-.142c0-1.6543,1.3457-3,3-3h8c2.7568,0,5-2.2432,5-5v-4.142c1.7205-.4471,3-1.9993,3-3.858,0-2.2061-1.7939-4-4-4s-4,1.7939-4,4Zm-14,0c0-1.1025.897-2,2-2s2,.8975,2,2c0,1.1025-.897,2-2,2s-2-.8975-2-2Zm4,20c0,1.103-.897,2-2,2s-2-.897-2-2,.897-2,2-2,2,.897,2,2ZM26,6c0,1.1025-.8975,2-2,2s-2-.8975-2-2c0-1.1025.8975-2,2-2s2,.8975,2,2Z"/>',
    "renew": '<path d="M12,10H6.78A11,11,0,0,1,27,16h2A13,13,0,0,0,6,7.68V4H4v8h8Z"/><path d="M20,22h5.22A11,11,0,0,1,5,16H3a13,13,0,0,0,23,8.32V28h2V20H20Z"/>',
    "flash": '<path d="M11.61,29.92a1,1,0,0,1-.6-1.07L12.83,17H8a1,1,0,0,1-1-1.23l3-13A1,1,0,0,1,11,2H21a1,1,0,0,1,.78.37,1,1,0,0,1,.2.85L20.25,11H25a1,1,0,0,1,.9.56,1,1,0,0,1-.11,1l-13,17A1,1,0,0,1,12,30,1.09,1.09,0,0,1,11.61,29.92ZM17.75,13l2-9H11.8L9.26,15h5.91L13.58,25.28,23,13Z"/>',
    "cognitive": '<path d="M30,13A11,11,0,0,0,19,2H11a9,9,0,0,0-9,9v3a5,5,0,0,0,5,5H8.1A5,5,0,0,0,13,23h1.38l4,7,1.73-1-4-6.89A2,2,0,0,0,14.38,21H13a3,3,0,0,1,0-6h1V13H13a5,5,0,0,0-4.9,4H7a3,3,0,0,1-3-3V12H6A3,3,0,0,0,9,9V8H7V9a1,1,0,0,1-1,1H4.08A7,7,0,0,1,11,4h6V6a1,1,0,0,1-1,1H14V9h2a3,3,0,0,0,3-3V4a9,9,0,0,1,8.05,5H26a3,3,0,0,0-3,3v1h2V12a1,1,0,0,1,1-1h1.77A8.76,8.76,0,0,1,28,13v1a5,5,0,0,1-5,5H20v2h3a7,7,0,0,0,3-.68V21a3,3,0,0,1-3,3H22v2h1a5,5,0,0,0,5-5V18.89A7,7,0,0,0,30,14Z"/>',
    "rule": '<path d="M10 16H22V18H10z"/><path d="M10 10H22V12H10z"/><path d="M16,30,9.8242,26.7071A10.9815,10.9815,0,0,1,4,17V4A2.0022,2.0022,0,0,1,6,2H26a2.0022,2.0022,0,0,1,2,2V17a10.9815,10.9815,0,0,1-5.8242,9.7069ZM6,4V17a8.9852,8.9852,0,0,0,4.7656,7.9423L16,27.7333l5.2344-2.791A8.9852,8.9852,0,0,0,26,17V4Z"/>',
    "code": '<path d="M31 16 24 23 22.59 21.59 28.17 16 22.59 10.41 24 9 31 16z"/><path d="M1 16 8 9 9.41 10.41 3.83 16 9.41 21.59 8 23 1 16z"/><path d="M5.91 15H26.080000000000002V17H5.91z" transform="rotate(-75 15.996 16)"/>',
    "settings": '<path d="M27,16.76c0-.25,0-.5,0-.76s0-.51,0-.77l1.92-1.68A2,2,0,0,0,29.3,11L26.94,7a2,2,0,0,0-1.73-1,2,2,0,0,0-.64.1l-2.43.82a11.35,11.35,0,0,0-1.31-.75l-.51-2.52a2,2,0,0,0-2-1.61H13.64a2,2,0,0,0-2,1.61l-.51,2.52a11.48,11.48,0,0,0-1.32.75L7.43,6.06A2,2,0,0,0,6.79,6,2,2,0,0,0,5.06,7L2.7,11a2,2,0,0,0,.41,2.51L5,15.24c0,.25,0,.5,0,.76s0,.51,0,.77L3.11,18.45A2,2,0,0,0,2.7,21L5.06,25a2,2,0,0,0,1.73,1,2,2,0,0,0,.64-.1l2.43-.82a11.35,11.35,0,0,0,1.31.75l.51,2.52a2,2,0,0,0,2,1.61h4.72a2,2,0,0,0,2-1.61l.51-2.52a11.48,11.48,0,0,0,1.32-.75l2.42.82a2,2,0,0,0,.64.1,2,2,0,0,0,1.73-1L29.3,21a2,2,0,0,0-.41-2.51ZM25.21,24l-3.43-1.16a8.86,8.86,0,0,1-2.71,1.57L18.36,28H13.64l-.71-3.55a9.36,9.36,0,0,1-2.7-1.57L6.79,24,4.43,20l2.72-2.4a8.9,8.9,0,0,1,0-3.13L4.43,12,6.79,8l3.43,1.16a8.86,8.86,0,0,1,2.71-1.57L13.64,4h4.72l.71,3.55a9.36,9.36,0,0,1,2.7,1.57L25.21,8,27.57,12l-2.72,2.4a8.9,8.9,0,0,1,0,3.13L27.57,20Z"/><path d="M16,22a6,6,0,1,1,6-6A5.94,5.94,0,0,1,16,22Zm0-10a3.91,3.91,0,0,0-4,4,3.91,3.91,0,0,0,4,4,3.91,3.91,0,0,0,4-4A3.91,3.91,0,0,0,16,12Z"/>',
    "deploy": '<path d="M16 2L2 14l2 2 4-3.5V28h16V12.5L28 16l2-2L16 2zM22 26H10V10.8l6-5.25 6 5.25z"/><path d="M14 18H18V24H14z"/>',
    "cloud": '<path d="M16,7a7.66,7.66,0,0,1,1.51.15,8,8,0,0,1,6.35,6.34l.26,1.35,1.35.24a5.5,5.5,0,0,1-1,10.92H7.5a5.5,5.5,0,0,1-1-10.92l1.34-.24.26-1.35A8,8,0,0,1,16,7m0-2A10,10,0,0,0,8.36,11.77a7.49,7.49,0,0,0,1.14,14.9h15a7.49,7.49,0,0,0,1.14-14.9A10,10,0,0,0,16,5Z"/>',
    "api": '<path d="M8,14v4H4V14ZM2,12V20h8V12Z"/><path d="M18,12H14a2,2,0,0,0-2,2v6h2V18h4v2h2V14A2,2,0,0,0,18,12Zm0,4H14V14h4Z"/><path d="M28 12L24 12 24 20 26 20 26 18 28 18 28 20 30 20 30 12 28 12 28 16 26 16 26 14 28 14 28 12z"/>',
    "terminal": '<path d="M26,4.01H6c-1.1,0-2,.9-2,2v20c0,1.1.9,2,2,2h20c1.1,0,2-.9,2-2V6.01c0-1.1-.9-2-2-2Zm0,22H6V10.01h20v16Zm0-18H6v-2h20v2Z"/><path d="M10.76,23.01l1.41-1.41,3.59-3.59-3.59-3.59-1.41-1.41-1.41,1.41,1.41,1.41,2.17,2.17-2.17,2.17-1.41,1.41,1.41,1.41Z"/><path d="M18 20.01H24V22.01H18z"/>',
    "data": '<path d="M16,4c5.11,0,10,1.34,10,4s-4.89,4-10,4S6,10.66,6,8,10.89,4,16,4m0-2C9.37,2,4,3.79,4,8s5.37,6,12,6,12-1.79,12-6S22.63,2,16,2Z"/><path d="M4,24c0,3.31,5.37,6,12,6s12-2.69,12-6V20.37c-2.34,2.54-7.09,3.63-12,3.63s-9.66-1.09-12-3.63Z"/><path d="M4,18c0,3.31,5.37,6,12,6s12-2.69,12-6V14.37c-2.34,2.54-7.09,3.63-12,3.63S6.34,16.91,4,14.37Z"/><path d="M4,12c0,3.31,5.37,6,12,6s12-2.69,12-6V8.37C25.66,10.91,20.91,12,16,12S6.34,10.91,4,8.37Z"/>',
    "user": '<path d="M16,4a5,5,0,1,1-5,5,5,5,0,0,1,5-5m0-2a7,7,0,1,0,7,7A7,7,0,0,0,16,2Z"/><path d="M26,30H24V25a5,5,0,0,0-5-5H13a5,5,0,0,0-5,5v5H6V25a7,7,0,0,1,7-7h6a7,7,0,0,1,7,7Z"/>',
    "rocket": '<path d="M24.13,6A21.39,21.39,0,0,0,15,9.77L12.35,14H6.44L2,20l6.78-.41L9,22.35a2,2,0,0,0,.28.65l.33.48-3.06,5L12.25,30l3-5.22.42.28A2,2,0,0,0,16.34,25l2.75.17L20,31.94l6-4.44V21.65L28.23,19A21.39,21.39,0,0,0,32,9.87ZM16.58,23l-.11,0L11,19.53l0-.11L9.16,15.84A19.27,19.27,0,0,1,23.58,8.42,19.27,19.27,0,0,1,16.58,23Z"/><circle cx="20" cy="14" r="2"/>',
    "search": '<path d="M30,28.59,22.45,21A11,11,0,1,0,21,22.45L28.59,30ZM5,14a9,9,0,1,1,9,9A9.01,9.01,0,0,1,5,14Z"/>',
    "warning": '<path d="M16,2A14,14,0,1,0,30,16,14,14,0,0,0,16,2Zm0,26A12,12,0,1,1,28,16,12,12,0,0,1,16,28Z"/><path d="M15 8H17V19H15z"/><path d="M16,22a1.5,1.5,0,1,0,1.5,1.5A1.5,1.5,0,0,0,16,22Z"/>',
    "checkmark": '<path d="M13 24L4 15.09 5.41 13.68 13 21.18 26.59 7.59 28 9z"/>',
    "close": '<path d="M24 9.4L22.6 8 16 14.6 9.4 8 8 9.4 14.6 16 8 22.6 9.4 24 16 17.4 22.6 24 24 22.6 17.4 16 24 9.4z"/>',
    "send": '<path d="M27.45,15.11l-22-11a1,1,0,0,0-1.08.12,1,1,0,0,0-.33,1L7,16,4,26.74A1,1,0,0,0,5,28a1,1,0,0,0,.45-.11l22-11a1,1,0,0,0,0-1.78ZM6.72,25.14,9,17H18V15H9L6.72,6.86,24.55,16Z"/>',
    "notification": '<path d="M28.7,20.3,26,17.6V13A10.07,10.07,0,0,0,17,3.05V1H15V3.05A10.07,10.07,0,0,0,6,13v4.6L3.3,20.3A1,1,0,0,0,3,21v3a1,1,0,0,0,1,1h7a5,5,0,0,0,10,0h7a1,1,0,0,0,1-1V21A1,1,0,0,0,28.7,20.3ZM16,27a3,3,0,0,1-3-3h6A3,3,0,0,1,16,27Zm11-4H5V21.41l2.7-2.71A1,1,0,0,0,8,18V13A8,8,0,0,1,24,13v5a1,1,0,0,0,.3.7L27,21.41Z"/>',
    "network": '<path d="M26,14a2,2,0,0,0,2-2V6a2,2,0,0,0-2-2H20a2,2,0,0,0-2,2v6a2,2,0,0,0,2,2h2v4H10V14h2a2,2,0,0,0,2-2V6a2,2,0,0,0-2-2H6A2,2,0,0,0,4,6v6a2,2,0,0,0,2,2H8v4H4v2H8v4H6a2,2,0,0,0-2,2v6a2,2,0,0,0,2,2h6a2,2,0,0,0,2-2V24a2,2,0,0,0-2-2H10V18H22v4H20a2,2,0,0,0-2,2v6a2,2,0,0,0,2,2h6a2,2,0,0,0,2-2V24a2,2,0,0,0-2-2H24V18h4V16H24V14ZM6,6h6v6H6ZM12,30H6V24h6Zm14,0H20V24h6ZM20,6h6v6H20Z"/>',
}


def render_icon(icon_value, size=28, color=None):
    """Render an icon as either a Carbon SVG or emoji.

    Default size is now 28px (up from 13) to match the bold carousel style.
    """
    if not icon_value:
        return ""
    lookup = icon_value.lower().replace("_", "-").strip()
    fill = color or INK
    if lookup in CARBON_ICONS:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" '
            f'width="{size}" height="{size}" fill="{fill}" '
            f'style="flex-shrink:0;">{CARBON_ICONS[lookup]}</svg>'
        )
    return f'<span style="font-size:{size}px;line-height:1;">{icon_value}</span>'


# Service color presets — used as accent fills on cards and icon tiles.
# Each preset maps to a single hex; the old gradient pair is still supported
# for backward compatibility (only the first value is used as the fill).
SERVICE_COLORS = {
    "slack": "#6B3A6B",
    "cloudflare": "#F48120",
    "github": "#2D333B",
    "jira": "#1E6FDB",
    "linkedin": "#1878B6",
    "claude": "#D97706",
    "aws": "#FF9900",
    "gcp": "#4285F4",
    "azure": "#1A82D4",
    "vercel": "#0A0A0A",
    "docker": "#2496ED",
    "redis": "#DC382D",
    "postgres": "#4269A0",
    "mongodb": "#47A248",
    "stripe": "#6359FF",
    "teal": "#2A8A8A",
    "cobalt": "#2E5BB8",
    "bronze": "#C47434",
    # Aliases matching the carousel palette
    "terracotta": ACCENT,
    "accent": ACCENT,
}


def resolve_color(color_input):
    """Resolve a color input to a single hex fill.

    Accepts:
      - Preset name: "teal", "claude"
      - Single hex: "#E27D5B"
      - Legacy two-item list: ["#E27D5B", "#c46a4a"] (first value used)
    Returns a single hex string.
    """
    if color_input is None:
        return ACCENT
    if isinstance(color_input, list) and color_input:
        return color_input[0]
    if isinstance(color_input, str):
        key = color_input.lower().strip().lstrip("#")
        if key in SERVICE_COLORS:
            return SERVICE_COLORS[key]
        if color_input.startswith("#"):
            return color_input
        return f"#{color_input}" if len(key) in (3, 6) else ACCENT
    return ACCENT


def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgba(hex_color, alpha):
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"


def contrast_ink(hex_color):
    """Return INK or white depending on which contrasts better with the fill."""
    r, g, b = hex_to_rgb(hex_color)
    # Relative luminance (sRGB)
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return INK if lum > 0.55 else "#FFFFFF"


# ---------------------------------------------------------------------------
# Shared base CSS
# ---------------------------------------------------------------------------

def base_css(width, height):
    h_rule = f"height: {height}px;" if height else ""
    center = "display: flex; align-items: center; justify-content: center;" if height else ""
    return f"""
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }}
  body {{
    width: {width}px;
    {h_rule}
    padding: 56px 48px;
    background: {BG_WHITE};
    font-family: {FONT_STACK};
    color: {INK};
    {center}
  }}
"""


# ---------------------------------------------------------------------------
# Pipeline diagram
# ---------------------------------------------------------------------------

def generate_pipeline(config):
    """Generate a horizontal pipeline/architecture diagram.

    Config shape unchanged from previous version — see SKILL.md.
    """
    nodes = config.get("nodes", [])
    connectors = config.get("connectors", [])
    width = config.get("width", 1200)
    height = config.get("height", None)
    animated = config.get("animated", False)

    node_htmls = []
    for i, node in enumerate(nodes):
        fill = resolve_color(node.get("color", "terracotta"))
        ink_on_fill = contrast_ink(fill)
        node_w = node.get("width", 180)
        icon = node.get("icon", "")
        name = node.get("name", "")
        desc = node.get("desc", "")
        components = node.get("components", [])
        trigger = node.get("trigger", False)

        icon_tile = (
            f'<div class="icon-tile" style="background:{fill};">'
            f'{render_icon(icon, size=32, color=ink_on_fill)}'
            f'</div>'
        ) if icon else ""

        desc_html = f'<div class="desc">{desc}</div>' if desc else ""

        if trigger:
            trigger_desc_html = f'<div class="cmd">{desc}</div>' if desc else ""
            node_html = f"""
  <div class="tcol">
    <div class="trigger">
      {icon_tile}
      <div class="trig-text">
        <div class="name">{name}</div>
        {trigger_desc_html}
      </div>
    </div>
    <div class="v-arrow"></div>"""
            child = node.get("child")
            if child:
                ch_fill = resolve_color(child.get("color", "terracotta"))
                ch_ink = contrast_ink(ch_fill)
                ch_icon = child.get("icon", "")
                ch_name = child.get("name", "")
                ch_desc = child.get("desc", "")
                ch_icon_tile = (
                    f'<div class="icon-tile" style="background:{ch_fill};">'
                    f'{render_icon(ch_icon, size=32, color=ch_ink)}'
                    f'</div>'
                ) if ch_icon else ""
                ch_desc_html = f'<div class="desc">{ch_desc}</div>' if ch_desc else ""
                node_html += f"""
    <div class="card">
      {ch_icon_tile}
      <div class="name">{ch_name}</div>
      {ch_desc_html}
    </div>"""
            node_html += "\n  </div>"
            node_htmls.append(node_html)
            continue

        if components:
            comp_items = []
            for comp in components:
                cname = comp.get("name", "")
                cdesc = comp.get("desc", "")
                cicon = comp.get("icon", "")
                ctag = comp.get("tag", "")
                tag_html = f'<div class="tag">{ctag}</div>' if ctag else ""
                icon_mini = (
                    f'<div class="mini-tile" style="background:{fill};">'
                    f'{render_icon(cicon, size=18, color=ink_on_fill)}'
                    f'</div>'
                ) if cicon else ""
                comp_items.append(f"""      <div class="comp">
        {icon_mini}
        <div class="comp-text">
          <div class="comp-name">{cname}</div>
          <div class="comp-desc">{cdesc}</div>
        </div>
        {tag_html}
      </div>""")
            comp_html = '<div class="components">\n' + "\n".join(comp_items) + '\n    </div>'
            node_html = f"""
  <div class="card card-wide">
    <div class="card-head">
      {icon_tile}
      <div class="card-head-text">
        <div class="name">{name}</div>
        {desc_html}
      </div>
    </div>
    {comp_html}
  </div>"""
        else:
            node_html = f"""
  <div class="card" style="width:{node_w}px;">
    {icon_tile}
    <div class="name">{name}</div>
    {desc_html}
  </div>"""

        node_htmls.append(node_html)

    # Connectors
    connector_htmls = []
    for idx, conn in enumerate(connectors):
        bidi = conn.get("bidirectional", False)
        if bidi:
            fwd = conn.get("forward_label", "")
            rev = conn.get("reverse_label", "")
            connector_htmls.append(f"""
  <div class="bidi">
    <div class="bi-row">
      <div class="bi-label">{fwd}</div>
      <div class="bi-line fwd"></div>
    </div>
    <div class="bi-row">
      <div class="bi-line rev"></div>
      <div class="bi-label">{rev}</div>
    </div>
  </div>""")
        else:
            label = conn.get("label", "")
            label_html = f'<div class="conn-label">{label}</div>' if label else ""
            # Animated particles for the flowing dot effect
            particle = '<div class="particle"></div>' if animated else ''
            connector_htmls.append(f"""
  <div class="connector">
    {label_html}
    <div class="line">{particle}</div>
  </div>""")

    body_parts = []
    for i, node_html in enumerate(node_htmls):
        body_parts.append(node_html)
        if i < len(connector_htmls):
            body_parts.append(connector_htmls[i])

    body_content = "\n".join(body_parts)

    # Animation keyframes (only injected when animated=true)
    anim_css = """
  @keyframes particle-flow {
    0%   { left: 0%;   opacity: 0; }
    10%  { opacity: 1; }
    90%  { opacity: 1; }
    100% { left: 100%; opacity: 0; }
  }
  @keyframes card-pulse {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-4px); }
  }
  .particle {
    position: absolute;
    width: 14px; height: 14px;
    border-radius: 50%;
    background: """ + ACCENT + """;
    border: 3px solid """ + INK + """;
    top: 50%;
    transform: translate(-50%, -50%);
    animation: particle-flow 3s linear infinite;
  }
  .card { animation: card-pulse 4s ease-in-out infinite; }
  .card:nth-child(1) { animation-delay: 0s; }
  .card:nth-child(3) { animation-delay: 0.4s; }
  .card:nth-child(5) { animation-delay: 0.8s; }
  .card:nth-child(7) { animation-delay: 1.2s; }
  .card:nth-child(9) { animation-delay: 1.6s; }
""" if animated else ""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{GOOGLE_FONTS}
<style>
{base_css(width, height)}
  .pipeline {{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    gap: 0;
  }}
  .card {{
    background: {BG_WHITE};
    border: 4px solid {INK};
    border-radius: 18px;
    padding: 22px 20px 20px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    flex-shrink: 0;
    box-shadow: 6px 6px 0 {INK};
  }}
  .card-wide {{ flex: 1; max-width: 340px; padding: 24px; }}
  .card-head {{
    display: flex;
    align-items: center;
    gap: 14px;
    width: 100%;
  }}
  .card-head-text {{ display: flex; flex-direction: column; gap: 4px; }}
  .icon-tile {{
    width: 58px; height: 58px;
    border-radius: 13px;
    border: 2.5px solid {INK};
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .mini-tile {{
    width: 36px; height: 36px;
    border-radius: 9px;
    border: 2px solid {INK};
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .name {{
    font-family: {FONT_STACK};
    font-size: 26px;
    font-weight: 900;
    color: {INK};
    letter-spacing: -0.02em;
    line-height: 1.05;
  }}
  .desc {{
    font-size: 15px;
    font-weight: 500;
    color: {INK_SOFT};
    line-height: 1.35;
    margin-top: 2px;
  }}
  .components {{
    display: flex;
    flex-direction: column;
    gap: 10px;
    width: 100%;
    margin-top: 6px;
  }}
  .comp {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    background: {BG_WHITE};
    border: 3px solid {INK};
    border-radius: 12px;
  }}
  .comp-text {{ flex: 1; display: flex; flex-direction: column; gap: 2px; }}
  .comp-name {{ font-size: 17px; font-weight: 800; color: {INK}; letter-spacing: -0.01em; }}
  .comp-desc {{ font-size: 14px; font-weight: 600; color: {INK_SOFT}; line-height: 1.4; }}
  .tag {{
    font-size: 13px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 5px 11px;
    background: {ACCENT};
    color: {INK};
    border: 2px solid {INK};
    border-radius: 7px;
  }}
  .tcol {{
    display: flex; flex-direction: column; align-items: center; gap: 14px;
    flex-shrink: 0;
  }}
  .trigger {{
    display: flex; align-items: center; gap: 14px;
    padding: 18px 22px;
    background: {BG_WHITE};
    border: 4px solid {INK};
    border-radius: 18px;
    box-shadow: 6px 6px 0 {INK};
  }}
  .trig-text {{ display: flex; flex-direction: column; gap: 2px; }}
  .trigger .cmd {{
    font-family: {MONO_STACK};
    font-size: 14px;
    font-weight: 600;
    color: {INK_MUTED};
  }}
  .v-arrow {{
    width: 4px; height: 32px;
    background: {INK};
    position: relative;
  }}
  .v-arrow::after {{
    content: '';
    position: absolute;
    bottom: -12px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 10px solid transparent;
    border-right: 10px solid transparent;
    border-top: 14px solid {INK};
  }}
  .connector {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-width: 140px;
    flex: 0 1 auto;
    padding: 0 8px;
  }}
  .conn-label {{
    font-size: 18px;
    font-weight: 900;
    color: {INK};
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
    white-space: nowrap;
    background: {ACCENT};
    padding: 8px 16px;
    border: 2.5px solid {INK};
    border-radius: 10px;
  }}
  .connector .line {{
    width: 100%;
    height: 4px;
    background: {INK};
    position: relative;
  }}
  .connector .line::after {{
    content: '';
    position: absolute;
    right: -1px;
    top: 50%;
    transform: translateY(-50%);
    border-top: 9px solid transparent;
    border-bottom: 9px solid transparent;
    border-left: 13px solid {INK};
  }}
  .bidi {{
    display: flex; flex-direction: column; justify-content: center;
    align-items: center; min-width: 110px; padding: 0 6px; gap: 14px;
  }}
  .bi-row {{ display: flex; align-items: center; gap: 8px; width: 100%; }}
  .bi-label {{
    font-size: 12px; font-weight: 800; color: {INK};
    text-transform: uppercase; letter-spacing: 0.06em; white-space: nowrap;
  }}
  .bi-line {{
    flex: 1; height: 4px; background: {INK}; position: relative;
  }}
  .bi-line.fwd::after {{
    content: ''; position: absolute; right: -1px; top: 50%;
    transform: translateY(-50%);
    border-top: 8px solid transparent; border-bottom: 8px solid transparent;
    border-left: 12px solid {INK};
  }}
  .bi-line.rev::after {{
    content: ''; position: absolute; left: -1px; top: 50%;
    transform: translateY(-50%);
    border-top: 8px solid transparent; border-bottom: 8px solid transparent;
    border-right: 12px solid {INK};
  }}
{anim_css}
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
    """Generate a sequence diagram with actors, lifelines, and messages."""
    actors = config.get("actors", [])
    steps = config.get("steps", [])
    width = config.get("width", 1200)
    height = config.get("height", None)
    n_actors = len(actors)

    padding = 48
    usable = width - 2 * padding
    actor_w = 160
    if n_actors > 1:
        spacing = usable / (n_actors - 1)
    else:
        spacing = 0
    centers = [padding + i * spacing for i in range(n_actors)]

    actor_html_parts = []
    for i, actor in enumerate(actors):
        fill = resolve_color(actor.get("color", "terracotta"))
        ink_on = contrast_ink(fill)
        name = actor.get("name", "")
        actor_html_parts.append(
            f'    <div class="actor" style="background:{fill};color:{ink_on};">'
            f'<div class="name">{name}</div></div>'
        )
    actors_html = "\n".join(actor_html_parts)

    lifeline_divs = '<div class="ll"></div>' * n_actors
    lifeline_bg = f'    <div class="lifeline-bg">\n      {lifeline_divs}\n    </div>'

    pos_css = ""
    for i, c in enumerate(centers):
        pos_css += f"  .from-{i} {{ left: {int(c)}px; }}\n"

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
            step_htmls.append(f"""      <div class="step">
        <div class="msg {style}" style="left: {int(left_pos)}px; width: {int(msg_width)}px;">
          <div class="msg-line"></div>
          <div class="arrow-head {arrow_class}"></div>
          <div class="msg-label">{label}</div>
        </div>
      </div>""")

        elif stype == "self":
            actor_idx = step["actor"]
            label = step.get("label", "")
            pos = centers[actor_idx] - 60
            step_htmls.append(f"""      <div class="step" style="min-height: 40px;">
        <div class="self-note" style="left: {int(pos)}px;">{label}</div>
      </div>""")

        elif stype == "note":
            over_idx = step["over"]
            text = step.get("text", "")
            margin_left = int(centers[over_idx]) - 120
            step_htmls.append(f'      <div class="spacer"></div>\n      <div class="note-box" style="margin-left: {margin_left}px;">{text}</div>')

        elif stype == "phase":
            label = step.get("label", "")
            step_htmls.append(f'      <div class="phase-label">{label}</div>')

        elif stype == "spacer":
            step_htmls.append('      <div class="spacer"></div>')

    steps_html = "\n".join(step_htmls)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{GOOGLE_FONTS}
<style>
{base_css(width, height)}
  body {{ padding: 56px {padding}px; }}
  .diagram {{ position: relative; width: 100%; }}
  .actors {{
    display: flex;
    justify-content: space-between;
    position: relative;
    z-index: 2;
    margin-bottom: 20px;
  }}
  .actor {{
    width: {actor_w}px;
    padding: 16px 10px;
    border-radius: 14px;
    border: 4px solid {INK};
    text-align: center;
    box-shadow: 5px 5px 0 {INK};
  }}
  .actor .name {{
    font-size: 20px;
    font-weight: 900;
    letter-spacing: -0.01em;
    line-height: 1.1;
  }}
  .lifelines {{ position: relative; margin-top: 0; }}
  .lifeline-bg {{
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: space-between;
    z-index: 0;
    pointer-events: none;
  }}
  .lifeline-bg .ll {{
    width: {actor_w}px;
    display: flex;
    justify-content: center;
  }}
  .lifeline-bg .ll::after {{
    content: '';
    width: 4px;
    height: 100%;
    background: repeating-linear-gradient(
      to bottom,
      {INK} 0px,
      {INK} 8px,
      transparent 8px,
      transparent 16px
    );
  }}
  .steps {{
    position: relative;
    z-index: 1;
    padding: 24px 0;
  }}
  .step {{
    display: flex;
    align-items: center;
    margin: 18px 0;
    min-height: 48px;
    position: relative;
  }}
  .msg {{
    position: absolute;
    height: 4px;
    z-index: 1;
  }}
  .msg-line {{
    height: 4px;
    width: 100%;
    background: {INK};
  }}
  .msg.dashed .msg-line {{
    background: repeating-linear-gradient(
      to right,
      {INK} 0px,
      {INK} 10px,
      transparent 10px,
      transparent 20px
    );
  }}
  .arrow-head {{
    position: absolute;
    right: -1px; top: 50%;
    transform: translateY(-50%);
    width: 0; height: 0;
    border-top: 9px solid transparent;
    border-bottom: 9px solid transparent;
    border-left: 14px solid {INK};
  }}
  .arrow-head.left {{
    left: -1px; right: auto;
    border-left: none;
    border-right: 14px solid {INK};
  }}
  .msg-label {{
    font-size: 15px;
    font-weight: 800;
    color: {INK};
    white-space: nowrap;
    position: absolute;
    top: -28px; left: 50%;
    transform: translateX(-50%);
    background: {ACCENT};
    padding: 4px 10px;
    border: 3px solid {INK};
    border-radius: 6px;
    letter-spacing: 0.02em;
  }}
  .self-note {{
    position: absolute;
    top: 0;
    padding: 8px 14px;
    font-size: 14px;
    font-weight: 700;
    color: {INK};
    background: {BG_WHITE};
    border: 3px solid {INK};
    border-radius: 8px;
  }}
  .note-box {{
    margin: 24px auto;
    padding: 16px 24px;
    border-radius: 12px;
    background: {ACCENT_SOFT};
    border: 4px solid {INK};
    text-align: center;
    font-size: 16px;
    font-weight: 700;
    color: {INK};
    width: fit-content;
    max-width: 80%;
    position: relative;
    z-index: 1;
    line-height: 1.45;
    box-shadow: 4px 4px 0 {INK};
  }}
  .spacer {{ height: 14px; }}
  .phase-label {{
    display: inline-block;
    font-size: 15px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {INK};
    background: {ACCENT};
    padding: 8px 16px;
    border: 3px solid {INK};
    border-radius: 8px;
    margin: 28px 0 16px;
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
    """Generate a grid layout of bold cards with items."""
    cards = config.get("cards", [])
    connections = config.get("connections", [])
    columns = config.get("columns", 2)
    width = config.get("width", 1200)
    height = config.get("height", None)

    card_htmls = []
    for card in cards:
        fill = resolve_color(card.get("color", "terracotta"))
        ink_on = contrast_ink(fill)
        icon = card.get("icon", "")
        name = card.get("name", "")
        items = card.get("items", [])

        icon_tile = (
            f'<div class="icon-tile" style="background:{fill};">'
            f'{render_icon(icon, size=34, color=ink_on)}'
            f'</div>'
        ) if icon else ""

        items_html = ""
        for item in items:
            iname = item.get("name", "")
            badge = item.get("badge", "")
            badge_html = f' <span class="badge">{badge}</span>' if badge else ""
            hint = item.get("hint", "")
            hint_html = f'<div class="hint">{hint}</div>' if hint else ""
            items_html += f"""    <div class="item">
      <div class="item-name">{iname}{badge_html}</div>
      {hint_html}
    </div>
"""

        card_htmls.append(f"""  <div class="card">
    <div class="card-head">
      {icon_tile}
      <div class="card-title">{name}</div>
    </div>
    {items_html}  </div>""")

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

    rows = [card_htmls[i:i + columns] for i in range(0, len(card_htmls), columns)]
    body_parts = []
    for i, row in enumerate(rows):
        body_parts.extend(row)
        if i == 0 and conn_html:
            body_parts.append(conn_html)

    body_content = "\n".join(body_parts)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{GOOGLE_FONTS}
<style>
{base_css(width, height)}
  .grid {{
    display: grid;
    grid-template-columns: repeat({columns}, 1fr);
    gap: 32px;
    width: 100%;
  }}
  .card {{
    background: {BG_WHITE};
    border: 4px solid {INK};
    border-radius: 20px;
    padding: 26px 28px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    box-shadow: 7px 7px 0 {INK};
  }}
  .card-head {{
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 6px;
  }}
  .icon-tile {{
    width: 62px; height: 62px;
    border-radius: 13px;
    border: 2.5px solid {INK};
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .card-title {{
    font-size: 28px;
    font-weight: 900;
    color: {INK};
    letter-spacing: -0.02em;
    line-height: 1.1;
  }}
  .item {{
    padding: 14px 16px;
    background: {BG_WHITE};
    border: 3px solid {INK};
    border-radius: 12px;
  }}
  .item-name {{
    font-family: {FONT_STACK};
    font-size: 18px;
    font-weight: 800;
    color: {INK};
    letter-spacing: -0.01em;
    line-height: 1.2;
  }}
  .hint {{
    font-family: {FONT_STACK};
    font-size: 16px;
    font-weight: 600;
    color: {INK_SOFT};
    margin-top: 6px;
    line-height: 1.4;
  }}
  .badge {{
    display: inline-block;
    font-size: 11px;
    font-weight: 900;
    padding: 3px 9px;
    border-radius: 5px;
    background: {ACCENT};
    color: {INK};
    border: 2px solid {INK};
    margin-left: 6px;
    vertical-align: middle;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }}
  .arrows {{
    grid-column: 1 / -1;
    display: flex;
    justify-content: center;
    gap: 60px;
    padding: 12px 0;
  }}
  .arrow-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 15px;
    font-weight: 800;
    color: {INK};
  }}
  .arrow-line {{
    width: 60px;
    height: 4px;
    background: {INK};
    position: relative;
  }}
  .arrow-line::after {{
    content: '';
    position: absolute;
    right: -1px; top: 50%;
    transform: translateY(-50%);
    border-top: 8px solid transparent;
    border-bottom: 8px solid transparent;
    border-left: 12px solid {INK};
  }}
  .arrow-line.dashed {{
    background: repeating-linear-gradient(
      to right, {INK} 0px, {INK} 8px, transparent 8px, transparent 16px
    );
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
# Stack diagram (vertical numbered cards)
# ---------------------------------------------------------------------------

def generate_stack(config):
    """Generate a vertical stack of numbered hero cards.

    Great for "3 lessons", "5 principles", "N reasons why" articles.

    Config shape:
    {
        "type": "stack",
        "width": 1200,
        "title": "Optional heading shown above the stack",
        "items": [
            {
                "number": "01",                     (optional - auto-numbered if omitted)
                "icon": "search",                   (optional)
                "color": "teal" | "#hex",           (optional, defaults to terracotta)
                "name": "Item title",               (required)
                "desc": "Longer description text"   (optional)
            }
        ]
    }
    """
    title = config.get("title", "")
    items = config.get("items", [])
    width = config.get("width", 1200)
    height = config.get("height", None)

    title_html = f'<div class="stack-title">{title}</div>' if title else ""

    item_htmls = []
    for i, item in enumerate(items):
        fill = resolve_color(item.get("color", "terracotta"))
        ink_on = contrast_ink(fill)
        number = item.get("number", f"{i + 1:02d}")
        icon = item.get("icon", "")
        name = item.get("name", "")
        desc = item.get("desc", "")

        icon_tile = (
            f'<div class="icon-tile" style="background:{fill};">'
            f'{render_icon(icon, size=34, color=ink_on)}'
            f'</div>'
        ) if icon else ""

        desc_html = f'<div class="stack-desc">{desc}</div>' if desc else ""

        item_htmls.append(f"""  <div class="stack-item">
    <div class="stack-number">{number}</div>
    {icon_tile}
    <div class="stack-body">
      <div class="stack-name">{name}</div>
      {desc_html}
    </div>
  </div>""")

    body_content = "\n".join(item_htmls)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{GOOGLE_FONTS}
<style>
{base_css(width, height)}
  body {{ flex-direction: column; align-items: stretch; }}
  .stack-title {{
    font-size: 36px;
    font-weight: 900;
    color: {INK};
    letter-spacing: -0.02em;
    margin-bottom: 28px;
    line-height: 1.1;
  }}
  .stack {{
    display: flex;
    flex-direction: column;
    gap: 20px;
    width: 100%;
  }}
  .stack-item {{
    display: flex;
    align-items: center;
    gap: 24px;
    background: {BG_WHITE};
    border: 4px solid {INK};
    border-radius: 20px;
    padding: 24px 32px;
    box-shadow: 7px 7px 0 {INK};
  }}
  .stack-number {{
    font-size: 72px;
    font-weight: 900;
    color: {INK};
    letter-spacing: -0.04em;
    line-height: 0.9;
    min-width: 110px;
    font-variant-numeric: tabular-nums;
  }}
  .icon-tile {{
    width: 64px; height: 64px;
    border-radius: 14px;
    border: 2.5px solid {INK};
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .stack-body {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .stack-name {{
    font-size: 28px;
    font-weight: 900;
    color: {INK};
    letter-spacing: -0.02em;
    line-height: 1.1;
  }}
  .stack-desc {{
    font-size: 17px;
    font-weight: 600;
    color: {INK_SOFT};
    line-height: 1.4;
  }}
</style>
</head>
<body>
{title_html}
<div class="stack">
{body_content}
</div>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Comparison diagram (two-column head-to-head)
# ---------------------------------------------------------------------------

def generate_comparison(config):
    """Generate a two-column before/after or A-vs-B comparison.

    Config shape:
    {
        "type": "comparison",
        "width": 1200,
        "title": "Optional heading above the comparison",
        "divider": "VS",                            (optional, default "VS")
        "left": {
            "name": "Before",
            "icon": "close",                        (optional)
            "color": "github",                      (optional)
            "items": [                              (list of strings OR {name, hint})
                "Plain string item",
                {"name": "Item with hint", "hint": "Longer explanation"}
            ]
        },
        "right": { ... same shape ... }
    }
    """
    title = config.get("title", "")
    divider = config.get("divider", "VS")
    left = config.get("left", {})
    right = config.get("right", {})
    width = config.get("width", 1200)
    height = config.get("height", None)

    title_html = f'<div class="cmp-title">{title}</div>' if title else ""

    def render_column(col, side_class):
        fill = resolve_color(col.get("color", "terracotta"))
        ink_on = contrast_ink(fill)
        name = col.get("name", "")
        icon = col.get("icon", "")
        items = col.get("items", [])

        icon_tile = (
            f'<div class="icon-tile" style="background:{fill};">'
            f'{render_icon(icon, size=34, color=ink_on)}'
            f'</div>'
        ) if icon else ""

        items_html = ""
        for it in items:
            if isinstance(it, str):
                items_html += f'    <li class="cmp-item"><span class="cmp-item-name">{it}</span></li>\n'
            else:
                iname = it.get("name", "")
                hint = it.get("hint", "")
                hint_html = f'<div class="cmp-item-hint">{hint}</div>' if hint else ""
                items_html += (
                    f'    <li class="cmp-item">'
                    f'<div class="cmp-item-name">{iname}</div>'
                    f'{hint_html}</li>\n'
                )

        return f"""  <div class="cmp-col {side_class}">
    <div class="cmp-head">
      {icon_tile}
      <div class="cmp-col-title">{name}</div>
    </div>
    <ul class="cmp-items">
{items_html}    </ul>
  </div>"""

    left_html = render_column(left, "cmp-left")
    right_html = render_column(right, "cmp-right")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{GOOGLE_FONTS}
<style>
{base_css(width, height)}
  body {{ flex-direction: column; align-items: stretch; }}
  .cmp-title {{
    font-size: 36px;
    font-weight: 900;
    color: {INK};
    letter-spacing: -0.02em;
    margin-bottom: 28px;
    text-align: center;
    line-height: 1.1;
  }}
  .cmp-wrapper {{
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: stretch;
    gap: 20px;
    width: 100%;
  }}
  .cmp-col {{
    background: {BG_WHITE};
    border: 4px solid {INK};
    border-radius: 20px;
    padding: 28px 30px;
    box-shadow: 7px 7px 0 {INK};
    display: flex;
    flex-direction: column;
    gap: 18px;
  }}
  .cmp-head {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding-bottom: 16px;
    border-bottom: 3px solid {INK};
  }}
  .icon-tile {{
    width: 62px; height: 62px;
    border-radius: 13px;
    border: 2.5px solid {INK};
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .cmp-col-title {{
    font-size: 30px;
    font-weight: 900;
    color: {INK};
    letter-spacing: -0.02em;
    line-height: 1.1;
  }}
  .cmp-items {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 14px;
    padding: 0;
    margin: 0;
  }}
  .cmp-item {{
    padding: 14px 18px;
    border: 3px solid {INK};
    border-radius: 12px;
    background: {BG_WHITE};
    position: relative;
  }}
  .cmp-item-name {{
    font-size: 18px;
    font-weight: 800;
    color: {INK};
    letter-spacing: -0.01em;
    line-height: 1.3;
    display: block;
  }}
  .cmp-item-hint {{
    font-size: 15px;
    font-weight: 600;
    color: {INK_SOFT};
    margin-top: 5px;
    line-height: 1.4;
  }}
  .cmp-divider {{
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .cmp-divider-pill {{
    font-size: 26px;
    font-weight: 900;
    color: {INK};
    background: {ACCENT};
    padding: 14px 22px;
    border: 3px solid {INK};
    border-radius: 14px;
    letter-spacing: 0.02em;
    box-shadow: 5px 5px 0 {INK};
  }}
</style>
</head>
<body>
{title_html}
<div class="cmp-wrapper">
{left_html}
  <div class="cmp-divider">
    <div class="cmp-divider-pill">{divider}</div>
  </div>
{right_html}
</div>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Screenshot helpers
# ---------------------------------------------------------------------------

def screenshot_html(html, output_path, width, height=None):
    """Render HTML and capture as PNG.

    If height is provided, clips to exact dimensions (fixed aspect ratio).
    If height is None, measures the content height after render and clips
    to fit tightly — no dead space, no extra viewport padding.
    """
    vp_height = height if height else 1400  # roomy viewport for auto-sized content
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": vp_height})
        page.set_content(html)
        page.wait_for_function("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(300)

        if height:
            page.screenshot(
                path=output_path,
                clip={"x": 0, "y": 0, "width": width, "height": height},
            )
        else:
            # Measure the actual bottom of the rendered content by walking
            # body's direct children. scrollHeight and the body's bounding
            # box can both include viewport-stretched whitespace, so we
            # compute maxBottom of real children + body's bottom padding.
            measured = page.evaluate("""
                () => {
                    const children = Array.from(document.body.children);
                    if (!children.length) return document.body.offsetHeight;
                    let maxBottom = 0;
                    for (const c of children) {
                        const r = c.getBoundingClientRect();
                        if (r.bottom > maxBottom) maxBottom = r.bottom;
                    }
                    const bs = getComputedStyle(document.body);
                    const pb = parseFloat(bs.paddingBottom) || 0;
                    return Math.ceil(maxBottom + pb);
                }
            """)
            measured = int(measured)
            if measured > vp_height:
                page.set_viewport_size({"width": width, "height": measured})
                page.wait_for_timeout(150)
            page.screenshot(
                path=output_path,
                clip={"x": 0, "y": 0, "width": width, "height": measured},
            )
        browser.close()
    print(f"Diagram generated: {output_path}")


def screenshot_html_gif(html, output_path, width, height, duration=5500, fps=10):
    """Render animated HTML and capture as GIF via ffmpeg."""
    import subprocess
    import tempfile
    import os

    if not height:
        height = 627

    frame_interval = 1000 // fps
    total_frames = duration // frame_interval

    with tempfile.TemporaryDirectory() as tmpdir:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.set_content(html)
            page.wait_for_function("document.fonts.ready.then(() => true)")
            page.wait_for_timeout(500)

            print(f"Capturing {total_frames} frames at {fps}fps...")
            for i in range(total_frames):
                frame_path = os.path.join(tmpdir, f"frame_{i:04d}.png")
                page.screenshot(
                    path=frame_path,
                    clip={"x": 0, "y": 0, "width": width, "height": height},
                )
                page.wait_for_timeout(frame_interval)

            static_path = output_path.rsplit(".", 1)[0] + "_static.png"
            page.wait_for_timeout(300)
            page.screenshot(
                path=static_path,
                clip={"x": 0, "y": 0, "width": width, "height": height},
            )
            print(f"Static frame: {static_path}")
            browser.close()

        frame_pattern = os.path.join(tmpdir, "frame_%04d.png")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", frame_pattern,
            "-vf", f"fps={fps},scale={width}:-1:flags=lanczos,"
                   f"split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer",
            output_path,
        ]

        try:
            subprocess.run(ffmpeg_cmd, capture_output=True, check=True, timeout=60)
        except FileNotFoundError:
            print("Error: ffmpeg not found. Install it: brew install ffmpeg", file=sys.stderr)
            sys.exit(1)
        except subprocess.CalledProcessError:
            ffmpeg_cmd_simple = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", frame_pattern,
                "-vf", f"fps={fps},scale={width}:-1",
                output_path,
            ]
            subprocess.run(ffmpeg_cmd_simple, capture_output=True, check=True, timeout=60)

    print(f"GIF generated: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

GENERATORS = {
    "pipeline": generate_pipeline,
    "sequence": generate_sequence,
    "grid": generate_grid,
    "stack": generate_stack,
    "comparison": generate_comparison,
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate beautiful article diagrams (pipeline, sequence, grid, stack, comparison)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Diagram types:
  pipeline    - Horizontal flow of bold cards with connectors
  sequence    - Sequence diagram with actors, lifelines, messages, phases
  grid        - Card grid with items and connection arrows
  stack       - Vertical numbered hero cards (3 lessons, 5 principles, N reasons)
  comparison  - Two-column head-to-head (before/after, A vs B)

Examples:
  %(prog)s --config architecture.json -o diagram.png
  %(prog)s --config sequence.json -o sequence.png
  %(prog)s --config tokens.json --save-html tokens.html -o tokens.png
        """
    )
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    parser.add_argument("--output", "-o", required=True, help="Output PNG or GIF path")
    parser.add_argument("--save-html", help="Also save the generated HTML to this path")
    parser.add_argument("--gif", action="store_true", help="Capture as animated GIF (requires ffmpeg). Also saves a static PNG.")
    parser.add_argument("--gif-duration", type=int, default=5500, help="GIF animation duration in ms (default 5500)")
    parser.add_argument("--gif-fps", type=int, default=10, help="GIF frames per second (default 10)")

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

    width = config.get("width", 1200)
    height = config.get("height", None)

    use_gif = args.gif or config.get("animated", False)
    duration = config.get("gif_duration", args.gif_duration)
    fps = config.get("gif_fps", args.gif_fps)

    if use_gif:
        output = args.output
        if not output.endswith(".gif"):
            output = output.rsplit(".", 1)[0] + ".gif"
        screenshot_html_gif(html, output, width, height, duration=duration, fps=fps)
    else:
        screenshot_html(html, args.output, width, height)


if __name__ == "__main__":
    main()
