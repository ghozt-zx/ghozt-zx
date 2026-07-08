#!/usr/bin/env python3
"""
ascii_knight.py
Generates a static SVG containing animated ASCII-art knight, styled to match
the phosphor-green HUD terminal aesthetic. No API calls needed - purely
decorative, so you can regenerate/tweak it anytime without a GitHub token.

Usage: python3 ascii_knight.py
Output: ascii-knight.svg
"""

BG = "#070c0b"
LINE = "#4a6b60"
TEXT_DIM = "#5f8a7d"
ACCENT = "#8ffcd0"

# Stylized ASCII knight: helm, cross-guard sword shape, armored torso, legs.
ASCII_ART = [
    "        _____        ",
    "       /     \\       ",
    "      |  o o  |      ",
    "       \\  ^  /       ",
    "     ---**|**---     ",
    "    /     |     \\    ",
    "   |    [=====]  |   ",
    "    \\      |    /    ",
    "     |     |     |   ",
    "    /|     |     |\\  ",
    "   / |     |     | \\ ",
    "     |_____|_____|   ",
    "      |         |    ",
    "      |         |    ",
    "     /           \\   ",
    "    /_____________\\  ",
]

WIDTH = 300
HEIGHT = 60 + len(ASCII_ART) * 16 + 60
FONT_SIZE = 13
LINE_HEIGHT = 16


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

    art_start_y = 70
    art_lines = ""
    for i, line in enumerate(ASCII_ART):
        y = art_start_y + i * LINE_HEIGHT
        # stagger each line's flicker so it reads as a scanline glitch,
        # not a uniform blink
        begin = round((i * 0.08) % 2.4, 2)
        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        art_lines += f'''
        <text x="{WIDTH/2}" y="{y}" text-anchor="middle"
              font-family="Consolas, monospace" font-size="{FONT_SIZE}"
              fill="{ACCENT}" filter="url(#glow)" xml:space="preserve">{escaped}
          <animate attributeName="opacity"
                   values="1;1;0.55;1;0.85;1"
                   dur="2.6s"
                   begin="{begin}s"
                   repeatCount="indefinite"/>
        </text>'''

    svg = f'''<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="1.2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>
  <rect x="1" y="1" width="{WIDTH-2}" height="{HEIGHT-2}" fill="none" stroke="{LINE}" stroke-width="1" opacity="0.6"/>
  {corners}

  <text x="30" y="38" font-family="Consolas, monospace" font-size="12" fill="{ACCENT}">&gt; ENTITY SCAN</text>
  <line x1="30" y1="46" x2="{WIDTH-30}" y2="46" stroke="{LINE}" stroke-width="1"/>

  {art_lines}

  <line x1="30" y1="{HEIGHT-32}" x2="{WIDTH-30}" y2="{HEIGHT-32}" stroke="{LINE}" stroke-width="1"/>
  <text x="30" y="{HEIGHT-14}" font-family="Consolas, monospace" font-size="9" fill="{TEXT_DIM}">CLASS: UNKNOWN // STATUS: ACTIVE</text>
</svg>'''
    return svg


if __name__ == "__main__":
    with open("ascii-knight.svg", "w") as f:
        f.write(render())
    print("ascii-knight.svg generated")
