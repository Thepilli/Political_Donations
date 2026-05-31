"""
Render KPI icons to PNG using Pillow directly (no SVG renderer).
Geometry mirrors the matching SVG files. Renders at 4x then downsamples for crisp edges.

Outputs:
  total_donation_64.png   no_of_donors_64.png   no_of_donations_64.png
  total_donation_256.png  no_of_donors_256.png  no_of_donations_256.png
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(__file__).parent
COLOR = (37, 99, 235, 255)        # primary (blue) -- change here to retheme all 3
WHITE = (255, 255, 255, 255)
SCALE = 8                          # supersample factor; final image is downsampled


def _font(size):
    for name in ("segoeui.ttf", "Segoe UI.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


UNIT = 64                          # logical viewBox is 0..64
CANVAS = UNIT * SCALE              # always render at 512x512 then downsample


def _new(size):
    """Returns an oversampled RGBA canvas. Geometry uses logical coords
    multiplied by SCALE -> pixel coords in a CANVAS-sized image."""
    return Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0)), CANVAS


def _finish(img, size, name):
    out = img.resize((size, size), Image.Resampling.LANCZOS)
    out.save(OUT / f"{name}_{size}.png", "PNG")


def _centered_text(draw, cx, cy, text, font, fill):
    # Pillow 10: textbbox returns (l, t, r, b)
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((cx - w / 2 - bbox[0], cy - h / 2 - bbox[1]), text, font=font, fill=fill)


# ---------------- TOTAL DONATION : money bag with Kč ----------------
def total_donation(size):
    img, s = _new(size)
    d = ImageDraw.Draw(img)
    # bag body — built from a smooth polygon approximating the SVG path
    # SVG path: M18 30 C14 38 13 48 18 54 C22 59 28 60 32 60 C36 60 42 59 46 54 C51 48 50 38 46 30 Z
    bag_pts = []
    # left side curve (top to bottom): from (18,30) down to (18,54) bulging out left
    for t in [i / 20 for i in range(21)]:
        # quadratic-ish: x goes 18 -> ~13 -> 18, y goes 30 -> 54
        x = 18 - 5 * (4 * t * (1 - t))    # parabola peaking at t=0.5
        y = 30 + 24 * t
        bag_pts.append((x, y))
    # bottom curve (left to right at y=60), from (18,54) -> (32,60) -> (46,54)
    for t in [i / 20 for i in range(1, 21)]:
        x = 18 + 28 * t
        y = 54 + 6 * (4 * t * (1 - t))    # bulge down
        bag_pts.append((x, y))
    # right side curve (bottom to top): from (46,54) -> (46,30) bulging out right
    for t in [i / 20 for i in range(1, 21)]:
        x = 46 + 5 * (4 * t * (1 - t))
        y = 54 - 24 * t
        bag_pts.append((x, y))
    bag_pts = [(x * SCALE, y * SCALE) for x, y in bag_pts]
    d.polygon(bag_pts, fill=COLOR)

    # bag tie / cinched neck — polyline at the top
    tie = [(22, 30), (20, 24), (26, 22), (32, 24), (38, 22), (44, 24), (42, 30)]
    tie = [(x * SCALE, y * SCALE) for x, y in tie]
    d.line(tie, fill=COLOR, width=int(2.5 * SCALE), joint="curve")

    # Kč mark
    font = _font(int(16 * SCALE * 0.95))
    _centered_text(d, 32 * SCALE, 50 * SCALE, "Kč", font, WHITE)

    _finish(img, size, "total_donation")


# ---------------- NO OF DONORS : three person silhouettes ----------------
def no_of_donors(size):
    img, s = _new(size)
    d = ImageDraw.Draw(img)

    def person(cx_head, cy_head, r_head, body_top_y, body_w, body_h):
        # head
        d.ellipse([
            (cx_head - r_head) * SCALE, (cy_head - r_head) * SCALE,
            (cx_head + r_head) * SCALE, (cy_head + r_head) * SCALE,
        ], fill=COLOR)
        # body — rounded shoulders
        left = (cx_head - body_w / 2) * SCALE
        top = body_top_y * SCALE
        right = (cx_head + body_w / 2) * SCALE
        bottom = (body_top_y + body_h) * SCALE
        radius = int(body_w / 2 * SCALE)
        d.rounded_rectangle([left, top, right, bottom], radius=radius, fill=COLOR)
        # square off the bottom (cover the lower roundness)
        d.rectangle([left, bottom - radius, right, bottom], fill=COLOR)

    # background pair (left + right)
    person(16, 22, 6, 36, 18, 18)
    person(48, 22, 6, 36, 18, 18)
    # foreground center person (slightly larger)
    person(32, 20, 8, 34, 24, 20)

    _finish(img, size, "no_of_donors")


# ---------------- NO OF DONATIONS : stack of 3 coins (side view) ----------------
def no_of_donations(size):
    img, _ = _new(size)
    d = ImageDraw.Draw(img)

    # Three coins, side view. Each coin = an ellipse on top + a rectangle body
    # + an ellipse on the bottom front arc, giving a 3D look.
    coin_w = 44                            # coin width (x extent)
    coin_h = 6                             # coin thickness (visible body height)
    cx = 32
    x1 = cx - coin_w / 2
    x2 = cx + coin_w / 2
    ellipse_ry = 4                         # half-height of top/bottom ellipse

    # Centers from bottom to top so upper coins overlap lower ones cleanly
    centers_y = [50, 36, 22]               # y positions of each coin's mid-line

    for i, cy in enumerate(centers_y):
        top_y = cy - coin_h / 2
        bot_y = cy + coin_h / 2

        # body (cylinder side) = rectangle
        d.rectangle(
            [x1 * SCALE, top_y * SCALE, x2 * SCALE, bot_y * SCALE],
            fill=COLOR,
        )
        # bottom front arc (the rounded underside of the cylinder)
        d.chord(
            [x1 * SCALE, (bot_y - ellipse_ry) * SCALE,
             x2 * SCALE, (bot_y + ellipse_ry) * SCALE],
            start=0, end=180, fill=COLOR,
        )
        # top ellipse (the visible top face of the cylinder)
        d.ellipse(
            [x1 * SCALE, (top_y - ellipse_ry) * SCALE,
             x2 * SCALE, (top_y + ellipse_ry) * SCALE],
            fill=COLOR,
        )
        # subtle highlight ring on the top face (thin lighter ellipse)
        rim = int(0.6 * SCALE)
        d.ellipse(
            [(x1 + 2) * SCALE, (top_y - ellipse_ry + 1.2) * SCALE,
             (x2 - 2) * SCALE, (top_y + ellipse_ry - 1.2) * SCALE],
            outline=WHITE, width=rim,
        )

    _finish(img, size, "no_of_donations")


for size in (64, 256):
    total_donation(size)
    no_of_donors(size)
    no_of_donations(size)

print("Wrote 6 PNGs to", OUT)
