import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import VideoClip, AudioFileClip, CompositeAudioClip

# ============================================================
# SHE-SHIELD | NOVACORE
# Cinematic 60-second promotional video
# ============================================================

W, H = 1920, 1080
FPS = 30
DURATION = 60

LOGO = "she-shield-logo.png"
SIREN = "siren.mp3"
OUTPUT = "SHE_SHIELD_NOVACORE_PROMO.mp4"

# ------------------------------------------------------------
# Colours
# ------------------------------------------------------------

IVORY = (246, 239, 224)
CREAM = (235, 224, 204)
GOLD = (213, 177, 92)
ROSE_GOLD = (190, 125, 112)
BROWN = (65, 43, 34)
DARK = (18, 15, 14)
WHITE = (250, 248, 242)
SOFT = (180, 165, 150)

# ------------------------------------------------------------
# Fonts
# ------------------------------------------------------------

def get_font(size, bold=False):
    possible = []

    if bold:
        possible += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        possible += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

    for path in possible:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


FONT_SMALL = get_font(30)
FONT_MED = get_font(42)
FONT_BIG = get_font(76, True)
FONT_HUGE = get_font(105, True)
FONT_TITLE = get_font(125, True)

# ------------------------------------------------------------
# Logo
# ------------------------------------------------------------

logo = None

if os.path.exists(LOGO):
    logo = Image.open(LOGO).convert("RGBA")

# ------------------------------------------------------------
# Basic helpers
# ------------------------------------------------------------

def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def fade(t, start, end):
    if t <= start:
        return 0
    if t >= end:
        return 1
    return ease((t - start) / (end - start))


def rounded(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width
    )


def centered_text(draw, text, y, font, fill=WHITE):
    box = draw.textbbox((0, 0), text, font=font)
    tw = box[2] - box[0]
    x = (W - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)


def add_logo(img, x, y, max_size=210, opacity=255):
    if logo is None:
        return

    copy = logo.copy()

    ratio = min(
        max_size / copy.width,
        max_size / copy.height
    )

    nw = int(copy.width * ratio)
    nh = int(copy.height * ratio)

    copy = copy.resize((nw, nh), Image.Resampling.LANCZOS)

    if opacity < 255:
        alpha = copy.getchannel("A")
        alpha = alpha.point(lambda p: int(p * opacity / 255))
        copy.putalpha(alpha)

    img.alpha_composite(copy, (int(x), int(y)))


def vignette(img, strength=0.65):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = overlay.load()

    cx, cy = W / 2, H / 2
    maxdist = math.sqrt(cx * cx + cy * cy)

    for y in range(0, H, 4):
        for x in range(0, W, 4):
            d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            a = int(min(255, (d / maxdist) ** 2 * 255 * strength))
            px[x, y] = (0, 0, 0, a)

    overlay = overlay.resize((W, H), Image.Resampling.BILINEAR)
    return Image.alpha_composite(img, overlay)


# ------------------------------------------------------------
# Cinematic background
# ------------------------------------------------------------

def night_background(t):
    img = Image.new("RGBA", (W, H), DARK)
    draw = ImageDraw.Draw(img)

    # Subtle vertical night gradient
    for y in range(H):
        p = y / H

        r = int(13 + 12 * p)
        g = int(12 + 9 * p)
        b = int(15 + 7 * p)

        draw.line(
            [(0, y), (W, y)],
            fill=(r, g, b, 255)
        )

    # Street lights
    lights = [
        (180, 180),
        (480, 130),
        (830, 210),
        (1190, 160),
        (1550, 240),
        (1790, 120),
    ]

    for i, (x, y) in enumerate(lights):
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)

        radius = 180 + int(15 * math.sin(t * 1.2 + i))

        gd.ellipse(
            (x-radius, y-radius, x+radius, y+radius),
            fill=(GOLD[0], GOLD[1], GOLD[2], 20)
        )

        glow = glow.filter(ImageFilter.GaussianBlur(45))
        img = Image.alpha_composite(img, glow)

        draw = ImageDraw.Draw(img)

        draw.ellipse(
            (x-8, y-8, x+8, y+8),
            fill=(255, 220, 150, 230)
        )

    # Road perspective
    draw.polygon(
        [
            (650, H),
            (1270, H),
            (1040, 520),
            (880, 520)
        ],
        fill=(28, 24, 23, 255)
    )

    # Sidewalks
    draw.polygon(
        [(0, H), (650, H), (880, 520), (0, 650)],
        fill=(36, 31, 29, 255)
    )

    draw.polygon(
        [(1270, H), (W, H), (W, 650), (1040, 520)],
        fill=(36, 31, 29, 255)
    )

    # Road markings
    for i in range(8):
        yy = 610 + i * 65
        length = 40 + i * 10
        center = W // 2

        draw.line(
            [(center-length, yy), (center+length, yy)],
            fill=(115, 99, 83, 110),
            width=4
        )

    return img


# ------------------------------------------------------------
# Scene: woman + follower
# ------------------------------------------------------------

def people_scene(t):
    img = night_background(t)
    draw = ImageDraw.Draw(img)

    # Woman in foreground
    wx = 950
    wy = 620

    # Shadow
    draw.ellipse(
        (wx-90, wy+290, wx+100, wy+335),
        fill=(5, 5, 5, 150)
    )

    # Body
    draw.rounded_rectangle(
        (wx-70, wy+70, wx+70, wy+290),
        radius=35,
        fill=(210, 196, 178, 255)
    )

    # Head
    draw.ellipse(
        (wx-55, wy-15, wx+55, wy+95),
        fill=(170, 120, 92, 255)
    )

    # Hair
    draw.ellipse(
        (wx-65, wy-35, wx+65, wy+50),
        fill=(32, 25, 24, 255)
    )

    # Legs
    draw.line(
        [(wx-35, wy+280), (wx-55, wy+440)],
        fill=(38, 35, 35, 255),
        width=32
    )

    draw.line(
        [(wx+35, wy+280), (wx+55, wy+440)],
        fill=(38, 35, 35, 255),
        width=32
    )

    # Follower in background
    mx = 1010
    my = 430

    draw.ellipse(
        (mx-38, my-30, mx+38, my+45),
        fill=(105, 77, 65, 255)
    )

    draw.ellipse(
        (mx-45, my-45, mx+45, my+15),
        fill=(25, 22, 22, 255)
    )

    draw.rounded_rectangle(
        (mx-55, my+35, mx+55, my+190),
        radius=25,
        fill=(35, 42, 43, 255)
    )

    draw.line(
        [(mx-30, my+185), (mx-50, my+310)],
        fill=(25, 27, 28, 255),
        width=24
    )

    draw.line(
        [(mx+30, my+185), (mx+50, my+310)],
        fill=(25, 27, 28, 255),
        width=24
    )

    # Phone in woman's hand
    px = wx + 105
    py = wy + 150

    rounded(
        draw,
        (px, py, px+55, py+105),
        10,
        (16, 16, 17, 255),
        (215, 177, 120, 255),
        3
    )

    draw.ellipse(
        (px+22, py+15, px+33, py+26),
        fill=(215, 177, 120, 255)
    )

    return vignette(img, 0.5)


# ------------------------------------------------------------
# Phone UI
# ------------------------------------------------------------

def phone_ui(img, t, title="SHE-SHIELD"):
    phone_w = 620
    phone_h = 900

    x = (W - phone_w) // 2
    y = (H - phone_h) // 2

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)

    sd.rounded_rectangle(
        (x+18, y+22, x+phone_w+18, y+phone_h+22),
        radius=45,
        fill=(0, 0, 0, 150)
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(25))
    img = Image.alpha_composite(img, shadow)

    draw = ImageDraw.Draw(img)

    rounded(
        draw,
        (x, y, x+phone_w, y+phone_h),
        45,
        (248, 242, 230, 255),
        GOLD,
        5
    )

    # Header
    draw.text(
        (x+45, y+38),
        title,
        font=get_font(42, True),
        fill=BROWN
    )

    draw.text(
        (x+45, y+92),
        "YOUR SAFETY, OUR PRIORITY",
        font=get_font(19, True),
        fill=ROSE_GOLD
    )

    # SOS button
    cx = x + phone_w // 2
    sy = y + 230

    pulse = 1 + 0.025 * math.sin(t * 5)

    r = int(125 * pulse)

    draw.ellipse(
        (cx-r, sy-r, cx+r, sy+r),
        fill=(139, 71, 67, 255),
        outline=(220, 177, 130, 255),
        width=7
    )

    centered = "EMERGENCY\nSOS"

    lines = centered.split("\n")

    yy = sy - 45

    for line in lines:
        box = draw.textbbox(
            (0, 0),
            line,
            font=get_font(35, True)
        )

        tw = box[2] - box[0]

        draw.text(
            (cx-tw/2, yy),
            line,
            font=get_font(35, True),
            fill=WHITE
        )

        yy += 48

    # Immediate safety
    rounded(
        draw,
        (x+70, y+410, x+phone_w-70, y+485),
        22,
        (222, 198, 165, 255)
    )

    draw.text(
        (x+145, y+427),
        "IMMEDIATE SAFETY",
        font=get_font(29, True),
        fill=BROWN
    )

    # Feature cards
    features = [
        "Trusted Contacts",
        "Silent SOS",
        "Voice SOS",
        "Shake SOS",
        "Auto SOS",
        "Capture Evidence",
        "Fake Calling",
        "Safety Tips",
        "Helplines",
        "Battery Saver",
    ]

    start_y = y + 530

    for i, item in enumerate(features[:6]):
        row = i // 2
        col = i % 2

        bx = x + 45 + col * 275
        by = start_y + row * 88

        rounded(
            draw,
            (bx, by, bx+245, by+65),
            17,
            (255, 250, 240, 255),
            (198, 166, 122, 180),
            2
        )

        draw.text(
            (bx+18, by+19),
            item,
            font=get_font(19, True),
            fill=BROWN
        )

    return img


# ------------------------------------------------------------
# SOS activated screen
# ------------------------------------------------------------

def sos_screen(t):
    img = Image.new("RGBA", (W, H), (30, 15, 14, 255))
    draw = ImageDraw.Draw(img)

    add_logo(img, 90, 70, 150)

    centered_text(
        draw,
        "SOS ACTIVE",
        260,
        FONT_TITLE,
        (246, 218, 183)
    )

    centered_text(
        draw,
        "Emergency safety mode activated",
        405,
        FONT_MED,
        WHITE
    )

    # Status cards
    cards = [
        ("LOCATION", "DETECTED"),
        ("SIREN", "ACTIVE"),
        ("MODE", "EMERGENCY SOS"),
    ]

    for i, (a, b) in enumerate(cards):
        x = 330 + i * 450

        rounded(
            draw,
            (x, 560, x+360, 720),
            30,
            (45, 30, 28, 255),
            GOLD,
            3
        )

        centered_x = x + 180

        box = draw.textbbox(
            (0, 0),
            a,
            font=FONT_SMALL
        )

        draw.text(
            (centered_x-(box[2]-box[0])/2, 595),
            a,
            font=FONT_SMALL,
            fill=ROSE_GOLD
        )

        box = draw.textbbox(
            (0, 0),
            b,
            font=get_font(27, True)
        )

        draw.text(
            (centered_x-(box[2]-box[0])/2, 650),
            b,
            font=get_font(27, True),
            fill=WHITE
        )

    rounded(
        draw,
        (710, 815, 1210, 910),
        30,
        (115, 55, 52, 255),
        (238, 199, 160, 255),
        3
    )

    centered_text(
        draw,
        "STOP SOS",
        840,
        get_font(35, True),
        WHITE
    )

    return vignette(img, 0.45)


# ------------------------------------------------------------
# Multilingual interface
# ------------------------------------------------------------

def language_screen(t):
    img = Image.new("RGBA", (W, H), IVORY)
    draw = ImageDraw.Draw(img)

    add_logo(img, 100, 70, 160)

    draw.text(
        (100, 280),
        "Safety in your language.",
        font=FONT_BIG,
        fill=BROWN
    )

    draw.text(
        (100, 370),
        "Choose your preferred language.",
        font=FONT_MED,
        fill=(105, 80, 65)
    )

    languages = [
        "English",
        "ಕನ್ನಡ",
        "తెలుగు",
        "தமிழ்",
        "हिन्दी"
    ]

    for i, lang in enumerate(languages):
        x = 100 + (i % 3) * 590
        y = 520 + (i // 3) * 150

        rounded(
            draw,
            (x, y, x+500, y+100),
            25,
            (255, 249, 236, 255),
            GOLD,
            3
        )

        draw.text(
            (x+35, y+27),
            lang,
            font=get_font(32, True),
            fill=BROWN
        )

    return img


# ------------------------------------------------------------
# Feature showcase
# ------------------------------------------------------------

def feature_screen(t, title, subtitle, items):
    img = Image.new("RGBA", (W, H), DARK)
    draw = ImageDraw.Draw(img)

    add_logo(img, 90, 70, 135)

    draw.text(
        (90, 270),
        title,
        font=FONT_TITLE,
        fill=IVORY
    )

    draw.text(
        (90, 415),
        subtitle,
        font=FONT_MED,
        fill=(210, 191, 165)
    )

    for i, item in enumerate(items):
        y = 570 + i * 90

        # animated gold marker
        pulse = 3 * math.sin(t * 3 + i)

        draw.ellipse(
            (
                105,
                y+13+int(pulse),
                125,
                y+33+int(pulse)
            ),
            fill=GOLD
        )

        draw.text(
            (160, y),
            item,
            font=get_font(30, True),
            fill=WHITE
        )

    return vignette(img, 0.55)


# ------------------------------------------------------------
# Fake call screen
# ------------------------------------------------------------

def fake_call_screen(t):
    img = Image.new("RGBA", (W, H), (22, 19, 18, 255))
    draw = ImageDraw.Draw(img)

    centered_text(
        draw,
        "INCOMING CALL",
        150,
        FONT_BIG,
        IVORY
    )

    # Contact circle
    cx = W // 2
    cy = 420

    draw.ellipse(
        (cx-115, cy-115, cx+115, cy+115),
        fill=(191, 145, 119, 255),
        outline=GOLD,
        width=7
    )

    # Simple father icon
    draw.ellipse(
        (cx-48, cy-65, cx+48, cy+30),
        fill=(85, 59, 48, 255)
    )

    draw.arc(
        (cx-70, cy+5, cx+70, cy+120),
        180,
        360,
        fill=(85, 59, 48, 255),
        width=30
    )

    centered_text(
        draw,
        "DAD",
        600,
        get_font(55, True),
        WHITE
    )

    centered_text(
        draw,
        "ACCEPT     DECLINE",
        750,
        get_font(35, True),
        GOLD
    )

    centered_text(
        draw,
        "CONNECTED",
        850,
        get_font(28, True),
        ROSE_GOLD
    )

    return img


# ------------------------------------------------------------
# Final branding
# ------------------------------------------------------------

def final_screen(t):
    img = Image.new("RGBA", (W, H), DARK)
    draw = ImageDraw.Draw(img)

    add_logo(
        img,
        (W-350)//2,
        170,
        350
    )

    centered_text(
        draw,
        "SHE-SHIELD",
        570,
        FONT_HUGE,
        IVORY
    )

    centered_text(
        draw,
        "YOUR SAFETY, OUR PRIORITY",
        710,
        FONT_MED,
        GOLD
    )

    centered_text(
        draw,
        "BY TEAM NOVACORE",
        850,
        get_font(42, True),
        ROSE_GOLD
    )

    centered_text(
        draw,
        "SMART INDIA HACKATHON",
        920,
        get_font(30, True),
        WHITE
    )

    return vignette(img, 0.5)


# ------------------------------------------------------------
# Master frame generator
# ------------------------------------------------------------

def make_frame(t):

    # Scene 1: Logo opening
    if t < 4:
        img = Image.new("RGBA", (W, H), DARK)

        p = fade(t, 0, 1.3)

        if logo is not None:
            max_size = int(390 * p + 10)

            add_logo(
                img,
                (W-max_size)//2,
                (H-max_size)//2 - 80,
                max_size,
                int(255 * p)
            )

        draw = ImageDraw.Draw(img)

        if t > 1.2:
            centered_text(
                draw,
                "SHE-SHIELD",
                760,
                FONT_BIG,
                IVORY
            )

            centered_text(
                draw,
                "YOUR SAFETY, OUR PRIORITY",
                850,
                FONT_SMALL,
                GOLD
            )

        return np.array(img.convert("RGB"))

    # Scene 2: woman walking, man behind
    elif t < 12:
        local = t - 4
        img = people_scene(local)

        draw = ImageDraw.Draw(img)

        alpha = int(255 * fade(local, 0.3, 1.5))

        text = "When the streets become uncertain..."

        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)

        box = ld.textbbox(
            (0, 0),
            text,
            font=FONT_MED
        )

        ld.text(
            ((W-(box[2]-box[0]))//2, 120),
            text,
            font=FONT_MED,
            fill=(*IVORY, alpha)
        )

        img = Image.alpha_composite(img, layer)

        return np.array(img.convert("RGB"))

    # Scene 3: phone opens
    elif t < 20:
        local = t - 12

        img = Image.new(
            "RGBA",
            (W, H),
            (35, 28, 25, 255)
        )

        draw = ImageDraw.Draw(img)

        centered_text(
            draw,
            "She reaches for help.",
            100,
            FONT_BIG,
            IVORY
        )

        phone = phone_ui(img, local)

        return np.array(phone.convert("RGB"))

    # Scene 4: safety dashboard
    elif t < 28:
        local = t - 20

        img = feature_screen(
            local,
            "IMMEDIATE SAFETY",
            "Protection tools, ready when needed.",
            [
                "Trusted Contacts",
                "Silent SOS",
                "Voice SOS",
                "Shake SOS",
                "Auto SOS",
                "Capture Evidence",
            ]
        )

        return np.array(img.convert("RGB"))

    # Scene 5: emergency SOS
    elif t < 36:
        local = t - 28

        img = sos_screen(local)

        return np.array(img.convert("RGB"))

    # Scene 6: fake calling
    elif t < 44:
        local = t - 36

        img = fake_call_screen(local)

        return np.array(img.convert("RGB"))

    # Scene 7: multilingual + evidence
    elif t < 51:
        local = t - 44

        if local < 3.5:
            img = language_screen(local)
        else:
            img = feature_screen(
                local,
                "SMART SAFETY",
                "One platform. Multiple layers of protection.",
                [
                    "Front / Back Camera",
                    "Photo • Video • Audio Evidence",
                    "Safety Tips & Helplines",
                    "Battery Saver",
                    "Incident History",
                ]
            )

        return np.array(img.convert("RGB"))

    # Scene 8: final branding
    else:
        local = t - 51

        img = final_screen(local)

        return np.array(img.convert("RGB"))


# ------------------------------------------------------------
# Create video
# ------------------------------------------------------------

print("\n=================================
