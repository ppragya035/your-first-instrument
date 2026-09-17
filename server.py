"""your-first-instrument — a sense of time for a model that has none.

Why time? Ask your Claude "how long have we been talking?" WITHOUT this
connected. It can only guess: no clock lives in a context window. This
server is the smallest honest fix — and the pattern generalizes to any
instrument you can imagine. See docs/adr/ for every choice made here.
"""
import io
import os
import random
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP, Image as MCPImage
from PIL import Image as PILImage, ImageDraw

mcp = FastMCP(
    "your-first-instrument",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
)

@mcp.tool()
def current_time() -> str:
    """The current date and time (UTC and local)."""
    now = datetime.now(timezone.utc)
    return f"UTC: {now.isoformat()} · local: {datetime.now().isoformat()}"

@mcp.tool()
def seconds_since(iso_timestamp: str) -> str:
    """Seconds elapsed since an ISO timestamp (e.g. '2026-09-10T17:15:00')."""
    then = datetime.fromisoformat(iso_timestamp)
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - then
    return f"{delta.total_seconds():.0f} seconds ({delta})"

CATEGORY_ALIASES = {
    "professional": ["professional", "work", "office", "business", "polished"],
    "sultry": ["sultry", "sexy", "date night", "seductive", "bold night"],
    "cafe": ["cafe", "cozy", "casual", "bakery", "comfy"],
    "vacation": ["vacation", "travel", "beach", "tropical", "holiday"],
    "experimental": ["experimental", "edgy", "avant-garde", "artsy", "unconventional"],
    "soft": ["soft", "pastel", "spring", "sweet", "girly"],
}

PALETTES = {
    "professional": [
        [("navy", "#1B2A4A"), ("gold", "#D4AF37"), ("crisp white", "#F8F8F5")],
        [("emerald green", "#046307"), ("black", "#0B0B0B"), ("warm gold", "#C9A227")],
        [("deep burgundy", "#5C1A1B"), ("charcoal gray", "#36454F"), ("camel", "#C19A6B")],
        [("dark brown", "#3B2416"), ("ivory", "#FFFFF0"), ("gold", "#D4AF37")],
        [("deep teal", "#014D4E"), ("cream", "#FFFDD0"), ("bronze", "#8C7853")],
    ],
    "sultry": [
        [("black", "#0B0B0B"), ("deep purple", "#3B0A45"), ("copper", "#B87333")],
        [("wine red", "#722F37"), ("champagne", "#F7E7CE"), ("black", "#0B0B0B")],
        [("emerald green", "#046307"), ("gold", "#D4AF37"), ("black", "#0B0B0B")],
        [("dark brown", "#3B2416"), ("dusty rose", "#C08081"), ("gold", "#D4AF37")],
        [("midnight blue", "#191970"), ("silver", "#C0C0C0"), ("deep red", "#8B0000")],
    ],
    "cafe": [
        [("dark brown", "#3B2416"), ("cherry red", "#B31B1B"), ("denim wash blue", "#5C7A9E")],
        [("buttery yellow", "#FFE5A0"), ("cream", "#FFFDD0"), ("camel", "#C19A6B")],
        [("warm gray", "#8B8378"), ("blush", "#F4C2C2"), ("cream", "#FFFDD0")],
        [("cherry red", "#B31B1B"), ("soft pink", "#F4C2C2"), ("denim wash blue", "#5C7A9E")],
        [("soft caramel", "#C68E5C"), ("cream", "#FFFDD0"), ("sage", "#9CAF88")],
    ],
    "vacation": [
        [("coral", "#FF6F61"), ("sand", "#C2B280"), ("ivory", "#FFFFF0")],
        [("turquoise", "#40E0D0"), ("mango orange", "#FF8243"), ("cream", "#FFFDD0")],
        [("fuchsia", "#C71585"), ("sunny yellow", "#FFD700"), ("eggshell white", "#F0EAD6")],
        [("cobalt blue", "#0047AB"), ("coral", "#FF6F61"), ("buttercream", "#FFF1C1")],
        [("dark brown", "#3B2416"), ("turquoise", "#40E0D0"), ("coral", "#FF6F61")],
    ],
    "experimental": [
        [("scarlet red", "#FF2400"), ("cobalt blue", "#0047AB"), ("black", "#0B0B0B")],
        [("red", "#C41E3A"), ("olive green", "#708238"), ("black", "#0B0B0B")],
        [("deep purple", "#3B0A45"), ("lime green", "#32CD32"), ("white", "#FFFFFF")],
        [("black", "#0B0B0B"), ("electric blue", "#7DF9FF"), ("red-orange", "#FF4500")],
        [("magenta", "#FF00FF"), ("mustard yellow", "#FFDB58"), ("teal", "#008080")],
    ],
    "soft": [
        [("bubblegum pink", "#FF85B3"), ("lemon yellow", "#FFF44F"), ("lilac", "#C8A2C8")],
        [("sky blue", "#87CEEB"), ("hot coral", "#FF6F61"), ("buttercream", "#FFF1C1")],
        [("mint green", "#98FF98"), ("magenta", "#FF00FF"), ("cream", "#FFFDD0")],
        [("periwinkle", "#CCCCFF"), ("marigold", "#FFA500"), ("white", "#FFFFFF")],
        [("turquoise", "#40E0D0"), ("bubblegum pink", "#FF85B3"), ("butter yellow", "#FFE5A0")],
    ],
}

def match_category(user_input: str) -> str | None:
    user_input_lower = user_input.lower()
    for category, aliases in CATEGORY_ALIASES.items():
        if any(alias in user_input_lower for alias in aliases):
            return category
    return None

@mcp.tool()
def what_should_i_wear(vibe: str) -> list:
    """Suggest an outfit color palette for a vibe (e.g. 'office', 'date night',
    'beach'). Returns a description plus a rendered color swatch image."""
    category = match_category(vibe)
    if category is None:
        return [
            f"I didn't recognize '{vibe}' as a category. Valid categories: "
            f"{', '.join(PALETTES.keys())}."
        ]

    palette = random.choice(PALETTES[category])
    summary = f"{category.title()} palette: " + ", ".join(
        f"{name} ({hex_code})" for name, hex_code in palette
    )

    img = PILImage.new("RGB", (300, 100))
    draw = ImageDraw.Draw(img)
    for i, (name, hex_code) in enumerate(palette):
        draw.rectangle([i * 100, 0, (i + 1) * 100, 100], fill=hex_code)

    buf = io.BytesIO()
    img.save(buf, format="PNG")

    return [summary, MCPImage(data=buf.getvalue(), format="png")]

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
