#!/usr/bin/env python3
"""
ascii_knight.py
Renders your custom braille-dot art as an animated SVG HUD panel, matching
the phosphor-green terminal aesthetic used across the profile card.
No API calls needed - purely decorative.

Usage: python3 ascii_knight.py
Output: ascii-knight.svg
"""

from braille_rows import ROWS

BG = "#070c0b"
LINE = "#4a6b60"
TEXT_DIM = "#5f8a7d"
ACCENT = "#8ffcd0"

MAX_LEN = max(len(r) for r in ROWS)
FONT_SIZE = 11
CHAR_W = FONT_SIZE * 0.62
LINE_HEIGHT = FONT_SIZE + 3

MARGIN = 30
WIDTH = int(MAX_LEN * CHAR_W) + MARGIN * 2
HEIGHT = 70 + len(ROWS) * LINE_HEIGHT + 50


def bracket_corner(x, y, size, flip_x=1, flip_y=1):
    dx = size * flip_x
    dy = size * flip_y
    return f'<path d="M{x} {y+dy} L{x} {y} L{x+dx} {y}" stroke="{ACCENT}" stroke-width="2" fill="none"/>'


def render():
    corners = "".join([
        bracket_corner(12, 12, 18, 1, 1),
        bracket_corner(WIDTH - 12, 12, 18, -1, 1),
        bracket_corner(12, HEIGHT - 12, 18, 1, -1),
        bracket_corner(WIDTH - 12, HEIGHT - 12, 18, -1, -1),
    ])

    art_start_y = 66
    art_lines = ""
    for i, line in enumerate(ROWS):
        y = art_start_y + i * LINE_HEIGHT
        begin = round((i * 0.06) % 2.2, 2)
        escaped = (
            line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        art_lines += f'''
        <text x="{WIDTH/2}" y="{y}" text-anchor="middle"
              font-family="Consolas, monospace" font-size="{FONT_SIZE}"
              fill="{ACCENT}" filter="url(#glow)" xml:space="preserve">{escaped}
          <animate attributeName="opacity"
                   values="1;1;0.6;1;0.9;1"
                   dur="2.8s"
                   begin="{begin}s"
                   repeatCount="indefinite"/>
        </text>'''

    svg = f'''<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="1.1" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>
  <rect x="1" y="1" width="{WIDTH-2}" height="{HEIGHT-2}" fill="none" stroke="{LINE}" stroke-width="1" opacity="0.6"/>
  {corners}

  <text x="30" y="36" font-family="Consolas, monospace" font-size="12" fill="{ACCENT}">&gt; SIGNAL TRACE</text>
  <line x1="30" y1="46" x2="{WIDTH-30}" y2="46" stroke="{LINE}" stroke-width="1"/>

  {art_lines}

  <line x1="30" y1="{HEIGHT-30}" x2="{WIDTH-30}" y2="{HEIGHT-30}" stroke="{LINE}" stroke-width="1"/>
  <text x="30" y="{HEIGHT-12}" font-family="Consolas, monospace" font-size="9" fill="{TEXT_DIM}">PATTERN: RECOGNIZED // STATUS: STABLE</text>
</svg>'''
    return svg


if __name__ == "__main__":
    with open("ascii-knight.svg", "w") as f:
        f.write(render())
    print("ascii-knight.svg generated,", WIDTH, "x", HEIGHT)
