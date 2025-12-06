#!/usr/bin/env python3
"""Generate a 220x220 logo for MemoryGraph in green screen ASCII style."""

from PIL import Image, ImageDraw, ImageFont
import os

# Colors - Green screen terminal style
BG_COLOR = (10, 10, 10)  # Near black background
GREEN = (0, 255, 65)  # Classic terminal green
GLOW_GREEN = (0, 180, 45)  # Darker green for glow effect

# Create image
size = 220
img = Image.new('RGB', (size, size), BG_COLOR)
draw = ImageDraw.Draw(img)

# Try to use a monospace font
font_paths = [
    "/System/Library/Fonts/Monaco.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Courier.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

font_large = None
font_small = None

for path in font_paths:
    if os.path.exists(path):
        try:
            font_large = ImageFont.truetype(path, 28)
            font_small = ImageFont.truetype(path, 14)
            break
        except:
            continue

if font_large is None:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Add subtle scanline effect
for y in range(0, size, 3):
    draw.line([(0, y), (size, y)], fill=(20, 20, 20), width=1)

# Draw the text - stacked layout for square format
lines = [
    "memory",
    "graph",
]

# Calculate positioning
y_start = 70
line_height = 35

for i, line in enumerate(lines):
    y = y_start + (i * line_height)
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), line, font=font_large)
    text_width = bbox[2] - bbox[0]
    x = (size - text_width) // 2

    # Draw glow effect (multiple passes with offset)
    for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1), (0, 1), (0, -1), (1, 0), (-1, 0)]:
        draw.text((x + offset[0], y + offset[1]), line, font=font_large, fill=(0, 60, 20))

    # Draw main text
    draw.text((x, y), line, font=font_large, fill=GREEN)

# Add blinking cursor
cursor_x = (size // 2) + 45
cursor_y = y_start + line_height + 5
draw.rectangle([cursor_x, cursor_y, cursor_x + 12, cursor_y + 22], fill=GREEN)

# Add decorative border
border_color = GLOW_GREEN
# Top border
draw.line([(10, 10), (size-10, 10)], fill=border_color, width=2)
# Bottom border
draw.line([(10, size-10), (size-10, size-10)], fill=border_color, width=2)
# Left border
draw.line([(10, 10), (10, size-10)], fill=border_color, width=2)
# Right border
draw.line([(size-10, 10), (size-10, size-10)], fill=border_color, width=2)

# Corner decorations
corner_len = 15
# Top-left
draw.line([(10, 25), (10+corner_len, 25)], fill=GREEN, width=1)
draw.line([(25, 10), (25, 10+corner_len)], fill=GREEN, width=1)
# Top-right
draw.line([(size-10-corner_len, 25), (size-10, 25)], fill=GREEN, width=1)
draw.line([(size-25, 10), (size-25, 10+corner_len)], fill=GREEN, width=1)
# Bottom-left
draw.line([(10, size-25), (10+corner_len, size-25)], fill=GREEN, width=1)
draw.line([(25, size-10-corner_len), (25, size-10)], fill=GREEN, width=1)
# Bottom-right
draw.line([(size-10-corner_len, size-25), (size-10, size-25)], fill=GREEN, width=1)
draw.line([(size-25, size-10-corner_len), (size-25, size-10)], fill=GREEN, width=1)

# Add subtle version/tagline at bottom
tagline = "> MCP MEMORY"
bbox = draw.textbbox((0, 0), tagline, font=font_small)
text_width = bbox[2] - bbox[0]
x = (size - text_width) // 2
draw.text((x, size - 45), tagline, font=font_small, fill=GLOW_GREEN)

# Save
output_path = os.path.join(os.path.dirname(__file__), "logo-220.png")
img.save(output_path, "PNG")
print(f"Logo saved to: {output_path}")
