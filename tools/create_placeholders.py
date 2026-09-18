"""Reproducible original geometric placeholders. Requires Pillow only for regeneration."""
from pathlib import Path
import math
import struct
import wave
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1] / "game"

def generate():
    target = ROOT / "assets/backgrounds/observatory.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (1920, 1080))
    d = ImageDraw.Draw(im)
    for y in range(1080):
        t = y / 1080
        d.line((0, y, 1920, y), fill=(int(13+25*t), int(25+29*t), int(48+33*t)))
    # Architectural study: original observatory, open arch, layered ridgelines.
    d.ellipse((1190, 135, 1310, 255), fill="#d7d1b4")
    for x in range(140, 1800, 137):
        y = 100 + ((x * 17) % 260)
        d.ellipse((x, y, x+2, y+2), fill="#8d9aa9")
    for j, color in enumerate(("#32465b", "#253b4d", "#1a3040")):
        points = [(0, 1080), (0, 600+j*65)]
        points += [(x, 480+j*95+int(55*math.sin(x/170+j))) for x in range(0, 1921, 60)]
        points += [(1920, 1080)]
        d.polygon(points, fill=color)
    d.rectangle((0, 0, 360, 1080), fill="#111b29")
    d.rectangle((1590, 0, 1920, 1080), fill="#111b29")
    d.arc((255, -350, 1695, 820), 180, 360, fill="#1a2635", width=130)
    for x in (280, 340, 1600, 1660):
        d.line((x, 0, x, 920), fill="#354052", width=3)
    d.polygon([(0, 915), (780, 685), (1150, 685), (1920, 915), (1920, 1080), (0, 1080)], fill="#182332")
    for y in (835, 910, 1005):
        d.line((0, y, 1920, y), fill="#354051", width=2)
    d.rectangle((1370, 485, 1390, 760), fill="#17202c")
    glow = Image.new("RGBA", im.size)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((1250, 340, 1510, 620), fill="#eab36c66")
    im = Image.alpha_composite(im.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(65)))
    d = ImageDraw.Draw(im)
    d.rectangle((1344, 442, 1416, 535), fill="#25303c", outline="#8c704e", width=4)
    d.rectangle((1354, 455, 1406, 520), fill="#e4bc76")
    im.convert("RGB").save(target)
    for name, color in (("eye", "#cbd5df"), ("eye_hover", "#e5c38b")):
        eye = Image.new("RGBA", (56, 48))
        ed = ImageDraw.Draw(eye)
        ed.rounded_rectangle((0, 0, 55, 47), radius=12, fill="#0b1429a0")
        ed.ellipse((12, 16, 44, 32), outline=color, width=2)
        ed.ellipse((24, 20, 32, 28), fill=color)
        path = ROOT / ("assets/overlays/" + name + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        eye.save(path)
    path = ROOT / "audio/music/quiet.wav"
    path.parent.mkdir(parents=True, exist_ok=True)
    rate, duration = 22050, 8
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        samples = []
        for n in range(rate * duration):
            t = n/rate
            envelope = math.sin(math.pi*t/duration)**2
            v = sum(math.sin(2*math.pi*f*t) for f in (110, 165, 220)) / 3
            samples.append(struct.pack("<h", int(1900*v*envelope)))
        output.writeframes(b"".join(samples))

if __name__ == "__main__":
    generate()
