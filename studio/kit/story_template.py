# यह किट का साँचा (template) है: इसमें तुलसी विवाह का उदाहरण भरा है। नई कथा के लिए इसकी कॉपी storyNNN.py बनाओ और
# TITLE, SUBTITLE, SENTS, SCENE_FIRST और compose() बदलो; बाक़ी हेल्पर (decorate, लोगो-प्लेट, कैप्शन, संगीत) जस के तस रखो।
"""Story #3 : तुलसी विवाह  -> 1080x1920 reel builder (art.py kit)."""
import sys, os, json, math, subprocess, random, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache
from art import *

FPS = 30
OUT = 'out'
TITLE = 'तुलसी विवाह'
SUBTITLE = 'देवउठनी एकादशी की पावन कथा'
END_TEXT = 'The Meet More | फ़ॉलो करें, कल की कथा'
SENTS = [
    'क्या आप जानते हैं, भगवान विष्णु हर साल तुलसी से विवाह क्यों करते हैं?',
    'बहुत पहले, जालंधर नाम का एक शक्तिशाली असुर राजा था।',
    'उसकी पत्नी वृंदा, विष्णु जी की परम भक्त और महान पतिव्रता थीं।',
    'वृंदा के सतीत्व की शक्ति से, जालंधर को कोई हरा नहीं पाता था।',
    'अहंकार में जालंधर ने देवताओं को सताया, और स्वर्ग छीन लिया।',
    'जब वह भगवान शिव से युद्ध करने गया, तो वृंदा पूजा में बैठ गईं।',
    'देवताओं ने विष्णु जी से प्रार्थना की, प्रभु, संसार को बचाइए।',
    'तब विष्णु जी, जालंधर का रूप धरकर वृंदा के पास पहुँचे।',
    'वृंदा ने उन्हें पति समझा, और उनका संकल्प टूट गया।',
    'उसी क्षण युद्ध में, भगवान शिव ने जालंधर का अंत कर दिया।',
    'सच जानकर वृंदा दुखी हुईं, और विष्णु जी को पत्थर बनने का श्राप दिया।',
    'विष्णु जी ने श्राप स्वीकार किया, और पत्थर बन गए।',
    'माता लक्ष्मी की विनती पर, वृंदा ने श्राप वापस लिया, और सती हो गईं।',
    'जहाँ उनकी राख थी, वहाँ एक पावन पौधा उगा, तुलसी।',
    'विष्णु जी बोले, तुलसी के बिना मेरी पूजा अधूरी रहेगी।',
    'मेरा शालिग्राम रूप, हर साल तुलसी से विवाह करेगा।',
    'इसीलिए देवउठनी एकादशी पर, घर-घर तुलसी विवाह होता है।',
    'सच्ची भक्ति के आगे, स्वयं भगवान भी झुक जाते हैं।',
    'जय तुलसी माता! जय श्री हरि!',
]
SCENE_FIRST = [0, 1, 2, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 16, 17]
CAP_BOTTOM = 1535
LOGO_W = 230


def font(sz):
    return ImageFont.truetype(FONT, sz)


# ------------------------------------------------------------ timing
def estimate_timing(total=57.0, start=0.6):
    n = [len(x) for x in SENTS]
    rate = 0.0805  # sec / char
    t, out = start, []
    for k in n:
        out.append([t, t + k * rate])
        t += k * rate + 0.28
    return {'total': total, 'sents': out}


def timing_from_audio(path, offset=0.4, total=None, tempo=1.0):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'silencedetect=noise=-35dB:d=0.15',
                        '-f', 'null', '-'], capture_output=True, text=True)
    dur = None
    m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r.stderr)
    if m:
        dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r.stderr)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r.stderr)]
    gaps = list(zip(st, en))
    lead = gaps[0][1] if gaps and gaps[0][0] < 0.05 else 0.0
    tail_start = st[-1] if len(st) > len(en) else dur
    inner = [g for g in gaps if g[0] > lead + 0.3 and g[1] < tail_start - 0.2]
    n = len(SENTS)
    chars = [len(x) for x in SENTS]
    tot = sum(chars)
    speech = tail_start - lead
    cum, c = [], 0
    for k in chars[:-1]:
        c += k
        cum.append(lead + speech * c / tot)
    mids = [(a + b) / 2 for a, b in inner]
    # DP: assign increasing gaps to boundaries minimising distance to proportional estimate
    INF = 1e9
    m_, g_ = len(cum), len(inner)
    dp = [[INF] * (g_ + 1) for _ in range(m_ + 1)]
    bk = [[None] * (g_ + 1) for _ in range(m_ + 1)]
    for j in range(g_ + 1):
        dp[0][j] = 0
    for i in range(1, m_ + 1):
        for j in range(1, g_ + 1):
            cost = abs(mids[j - 1] - cum[i - 1]) - 0.4 * (inner[j - 1][1] - inner[j - 1][0])
            a, b = dp[i][j - 1], dp[i - 1][j - 1] + cost
            if b <= a:
                dp[i][j], bk[i][j] = b, 'take'
            else:
                dp[i][j], bk[i][j] = a, 'skip'
    pick, j = [], g_
    i = m_
    while i > 0 and j > 0:
        if bk[i][j] == 'take':
            pick.append(inner[j - 1])
            i -= 1
        j -= 1
    pick = pick[::-1]
    sents = []
    for i in range(n):
        s0 = lead if i == 0 else pick[i - 1][1]
        e0 = tail_start if i == n - 1 else pick[i][0]
        sents.append([s0 / tempo + offset, e0 / tempo + offset])
    return {'sents': sents, 'narr_end': tail_start / tempo + offset, 'dur': dur / tempo + offset, 'total': total,
            'tempo': tempo, 'offset': offset, 'lead': lead}


def scene_bounds(tm):
    T = tm['total']
    st = [0.0] + [tm['sents'][i][0] - 0.1 for i in SCENE_FIRST[1:]] + [T]
    return st


# ------------------------------------------------------------ assets
_PLATE = []


def logo_plate():
    # लोगो हमेशा ऊपर-बाएँ कोने में, छोटी मरून प्लेट पर (आसमान/चाँद/बादल से टकराए नहीं)
    if not _PLATE:
        lg = logo_img()
        pl = Image.new('RGBA', (lg.width + 36, lg.height + 24), (0, 0, 0, 0))
        ImageDraw.Draw(pl).rounded_rectangle([0, 0, pl.width - 1, pl.height - 1], 26, fill=(74, 12, 24, 175), outline=(224, 176, 72, 210), width=3)
        pl.alpha_composite(lg, (18, 12))
        _PLATE.append(pl)
    return _PLATE[0]


@lru_cache(None)
def logo_img():
    im = Image.open('logo.png').convert('RGBA')
    im = im.resize((LOGO_W, int(im.height * LOGO_W / im.width)), Image.LANCZOS)
    a = np.array(im)
    a[..., 3] = (a[..., 3] * 0.88).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


@lru_cache(None)
def bgimg(name):
    cv = BACKGROUNDS[name]()
    return cv.im.convert('RGB')


@lru_cache(None)
def SP(kind, H=640, **kw):
    kw = dict(kw)
    for k in ('arms',):
        if k in kw and isinstance(kw[k], str):
            kw[k] = json.loads(kw[k])
    return person(kind, H, **kw)


def A(*a):  # hashable arms
    return json.dumps(a)


@lru_cache(None)
def PAIR(h=640):
    return hug_pair(h)


@lru_cache(None)
def SUD_BUNDLE():
    return SP('sudama', 640, arms=A((-1.4, 5.6), (1.2, 4.6)), bundle=True)


def wrap(text, f, maxw):
    words, lines, cur = text.split(' '), [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if f.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    lines.append(cur)
    return lines


@lru_cache(None)
def caption_strip(idx):
    for fs, mw in ((64, 800), (60, 810), (56, 820), (52, 830), (48, 840)):
        f = font(fs)
        lines = wrap(SENTS[idx], f, mw)
        if len(lines) <= 2:
            break
    lh = int(fs * 1.5)
    ph = lh * len(lines) + 34
    w = 880
    im = Image.new('RGBA', (w, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([0, 0, w - 1, ph - 1], 36, fill=hx('#4A0C18', 170), outline=hx(GOLD, 230), width=4)
    for i, ln in enumerate(lines):
        tw = f.getlength(ln)
        d.text(((w - tw) / 2, 14 + i * lh), ln, font=f, fill=hx('#FFF6DC'), stroke_width=5, stroke_fill=hx('#3A0812'))
    return im


@lru_cache(None)
def title_strip():
    im = Image.new('RGBA', (1000, 270), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, 'RGBA')
    f = font(160)
    tw = f.getlength(TITLE)
    d.text(((1000 - tw) / 2, 0), TITLE, font=f, fill=hx('#FFE08A'), stroke_width=14, stroke_fill=hx(MAROON))
    f2 = font(50)
    tw = f2.getlength(SUBTITLE)
    d.rounded_rectangle([(1000 - tw) / 2 - 30, 190, (1000 + tw) / 2 + 30, 262], 36, fill=hx('#4A0C18', 200),
                        outline=hx(GOLD, 230), width=3)
    d.text(((1000 - tw) / 2, 197), SUBTITLE, font=f2, fill=hx('#FFF6DC'), stroke_width=3, stroke_fill=hx('#3A0812'))
    return im


@lru_cache(None)
def end_strip():
    f = font(46)
    tw = f.getlength(END_TEXT)
    w, h = int(tw + 90), 110
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle([0, 0, w - 1, h - 1], 55, fill=hx('#4A0C18', 215), outline=hx(GOLD, 255), width=5)
    d.text((45, 22), END_TEXT, font=f, fill=hx('#FFE08A'), stroke_width=3, stroke_fill=hx('#2A0610'))
    return im


@lru_cache(None)
def throne_front():
    cv = Cv(W, H)
    cv.rrect(250, 960, 830, 1210, 30, hx('#C9892B'))
    cv.rrect(300, 920, 780, 1020, 30, hx('#B5262F'))
    cv.line([(280, 1210), (280, 1260)], hx(GOLD2), 12)
    cv.line([(800, 1210), (800, 1260)], hx(GOLD2), 12)
    return cv.out()


def crop_waist(im, frac=.57):
    return im.crop((0, 0, im.width, int(im.height * frac)))


# ------------------------------------------------------------ drawing helpers
def put(fr, img, cx, feet, scale=1.0, alpha=1.0):
    if scale != 1.0:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BILINEAR)
    if alpha < 1.0:
        a = np.array(img)
        a[..., 3] = (a[..., 3] * alpha).astype(np.uint8)
        img = Image.fromarray(a, 'RGBA')
    fr.paste(img, (int(cx - img.width / 2), int(feet - img.height)), img)


def sparkle_burst(fr, cx, cy, t, dur=1.0, n=22, seed=1, rad=380):
    if t < 0 or t > dur:
        return
    rnd = random.Random(seed)
    d = ImageDraw.Draw(fr, 'RGBA')
    p = t / dur
    for _ in range(n):
        ang, sp_, sz = rnd.random() * 6.283, .4 + rnd.random() * .6, 6 + rnd.random() * 10
        r = rad * sp_ * (1 - (1 - p) ** 2)
        x, y = cx + math.cos(ang) * r, cy + math.sin(ang) * r
        a = int(255 * (1 - p))
        d.polygon([(x, y - sz * 2), (x + sz * .5, y - sz * .5), (x + sz * 2, y), (x + sz * .5, y + sz * .5), (x, y + sz * 2),
                   (x - sz * .5, y + sz * .5), (x - sz * 2, y), (x - sz * .5, y - sz * .5)], fill=(255, 230, 150, a))


def float_sparkles(fr, t, seed, n=14, y0=500, y1=1250):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(fr, 'RGBA')
    for _ in range(n):
        x0, ph, sp_, sz = rnd.random() * 1000 + 40, rnd.random(), .08 + rnd.random() * .12, 4 + rnd.random() * 6
        y = y1 - ((t * sp_ + ph) % 1.0) * (y1 - y0)
        a = int(200 * math.sin(((t * sp_ + ph) % 1.0) * math.pi))
        x = x0 + math.sin(t + ph * 6) * 14
        d.polygon([(x, y - sz * 2), (x + sz * .5, y - sz * .5), (x + sz * 2, y), (x + sz * .5, y + sz * .5), (x, y + sz * 2),
                   (x - sz * .5, y + sz * .5), (x - sz * 2, y), (x - sz * .5, y - sz * .5)], fill=(255, 236, 160, a))


def draw_bg(fr, name, p, pan=(0, 0), zoom=0.07, zin=True):
    bg = bgimg(name)
    z = 1 + zoom * (p if zin else 1 - p)
    cw, ch = W * S / z, H * S / z
    cx = W * S / 2 + pan[0] * p * 30
    cy = H * S / 2 + pan[1] * p * 30
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    fr.paste(bg.resize((W, H), Image.BILINEAR, box=box), (0, 0))


# ------------------------------------------------------------ scenes


@lru_cache(None)
def VI(H=640, step=0, **kw):
    return vishnu(H, t=step / 6.0, **kw)


def VS(gt, **kw):
    return VI(640, int(gt * 6) % 12, **kw)


@lru_cache(None)
def JL(H=640, **kw):
    return jalandhar(H, **kw)


@lru_cache(None)
def TP(g10=10):
    return tulsi_plant(420, g10 / 10.0)


@lru_cache(None)
def SHL(r=70, g=1.0):
    return shaligram(r, g)


@lru_cache(None)
def CHAURA():
    return tulsi_chaura(300)


def flames(fr, gt, xs, base, scale=1.0, seed=1):
    d = ImageDraw.Draw(fr, 'RGBA')
    rnd = random.Random(seed)
    for k, x in enumerate(xs):
        fl = math.sin(gt * 9 + k * 1.7) * .15
        r = (46 + (k % 3) * 14) * scale
        y = base - (k % 2) * 40
        d.polygon([(x - r, y), (x - r * .5, y - r * 1.3), (x + fl * r, y - r * 2.4), (x + r * .55, y - r * 1.2), (x + r, y)], fill=(232, 70, 30, 235))
        d.polygon([(x - r * .62, y), (x - r * .2, y - r * 1.0), (x + fl * r * .8, y - r * 1.75), (x + r * .4, y - r * .9), (x + r * .62, y)], fill=(247, 154, 30, 240))
        d.polygon([(x - r * .3, y), (x, y - r * 1.05), (x + r * .3, y)], fill=(255, 228, 92, 245))


def embers(fr, gt, n=26, seed=3, y0=300, y1=1300):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(fr, 'RGBA')
    for _ in range(n):
        x0, ph, sp_, sz = rnd.random() * 1080, rnd.random(), .12 + rnd.random() * .2, 3 + rnd.random() * 5
        q = (gt * sp_ + ph) % 1.0
        y = y1 - q * (y1 - y0)
        x = x0 + math.sin(gt * 2 + ph * 9) * 26
        d.ellipse([x - sz, y - sz, x + sz, y + sz], fill=(255, 190, 80, int(230 * math.sin(q * math.pi))))


def falling(fr, gt, n=30, seed=5, cols=((232, 70, 46), (60, 150, 70))):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(fr, 'RGBA')
    for k in range(n):
        x0, ph, sp_, sz = rnd.random() * 1080, rnd.random(), .25 + rnd.random() * .3, 7 + rnd.random() * 9
        q = (gt * sp_ + ph) % 1.0
        y = 250 + q * 1100
        x = x0 + math.sin(gt * 3 + ph * 8) * 40
        c = cols[k % 2]
        d.ellipse([x - sz, y - sz * .6, x + sz, y + sz * .6], fill=c + (225,))


@lru_cache(None)
def _glow_img(r, col, k100):
    n = 2 * r
    y, x = np.mgrid[0:n, 0:n]
    d = np.sqrt((x - r) ** 2 + (y - r) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 1.6 * 200 * k100 / 100.0
    arr = np.zeros((n, n, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = col
    arr[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


def glow(fr, cx, cy, r, col=(255, 226, 140), k=1.0):
    r = max(4, int(r // 8 * 8))
    g = _glow_img(r, col, int(max(0, min(1.3, k)) * 20) * 5)
    fr.alpha_composite(g, (int(cx - r), int(cy - r))) if cx - r >= 0 and cy - r >= 0 and cx + r <= W and cy + r <= H else fr.paste(g, (int(cx - r), int(cy - r)), g)


def diya(fr, x, y, gt, flame=1.0):
    d = ImageDraw.Draw(fr, 'RGBA')
    if flame > 0.02:
        glow(fr, x, y - 40, 120 * flame, k=flame)
    d.polygon([(x - 60, y - 18), (x + 60, y - 18), (x + 40, y + 16), (x - 40, y + 16)], fill=hx(GOLD))
    d.rectangle([x - 60, y - 24, x + 60, y - 14], fill=hx('#FFE08A'))
    if flame > 0.02:
        f = flame * (1 + .08 * math.sin(gt * 13))
        d.polygon([(x - 16 * f, y - 22), (x, y - 22 - 70 * f), (x + 16 * f, y - 22)], fill=(255, 176, 46, 255))
        d.polygon([(x - 8 * f, y - 22), (x, y - 22 - 40 * f), (x + 8 * f, y - 22)], fill=(255, 242, 168, 255))
    else:
        for k in range(3):  # smoke wisp
            yy = y - 40 - k * 40 - (gt * 30) % 40
            d.ellipse([x - 14 + k * 6, yy - 14, x + 14 + k * 6, yy + 14], fill=(200, 200, 210, 70))


def lightning(fr, gt, seed=1):
    ph = (gt * 0.9 + seed * .37) % 1.0
    if ph > .12:
        return
    rnd = random.Random(int(gt * 0.9) * 7 + seed)
    x = 150 + rnd.random() * 780
    pts, y = [(x, 160)], 160
    while y < 900:
        y += 70 + rnd.random() * 60
        x += (rnd.random() - .5) * 140
        pts.append((x, y))
    d = ImageDraw.Draw(fr, 'RGBA')
    d.line(pts, fill=(235, 240, 255, 230), width=9)
    d.line(pts, fill=(255, 255, 255, 255), width=3)
    fr.alpha_composite(Image.new('RGBA', (W, H), (220, 225, 255, int(70 * (1 - ph / .12)))))


def trishul(fr, cx, cy, sc, gt):
    glow(fr, cx, cy - 120 * sc, 330 * sc, (190, 220, 255), 1.0 + .3 * math.sin(gt * 4))
    d = ImageDraw.Draw(fr, 'RGBA')
    g, g2 = hx('#F2F5FA'), hx('#AFC3DA')
    d.rectangle([cx - 10 * sc, cy - 260 * sc, cx + 10 * sc, cy + 380 * sc], fill=g2)
    d.rectangle([cx - 6 * sc, cy - 260 * sc, cx + 6 * sc, cy + 380 * sc], fill=g)
    d.polygon([(cx - 22 * sc, cy - 250 * sc), (cx, cy - 470 * sc), (cx + 22 * sc, cy - 250 * sc)], fill=g)
    for sg in (-1, 1):
        d.line([(cx, cy - 190 * sc), (cx + sg * 120 * sc, cy - 230 * sc), (cx + sg * 135 * sc, cy - 400 * sc)], fill=g, width=int(20 * sc))
        d.polygon([(cx + sg * 115 * sc, cy - 390 * sc), (cx + sg * 138 * sc, cy - 470 * sc), (cx + sg * 160 * sc, cy - 390 * sc)], fill=g)
    d.rectangle([cx - 90 * sc, cy - 200 * sc, cx + 90 * sc, cy - 170 * sc], fill=g2)
    d.ellipse([cx - 34 * sc, cy - 120 * sc, cx + 34 * sc, cy - 50 * sc], fill=hx('#C98A1B'))  # damru-knot


def petals(fr, gt, n=34, seed=11):
    falling(fr, gt, n, seed, cols=((245, 158, 11), (239, 68, 68)))


def compose(si, fr, t, p, L, ctx):
    gt = ctx['t0'] + t
    s_t = ctx['sents']
    bob = math.sin(t * 2.6)
    if si == 0:   # cover
        draw_bg(fr, 'angan', p, pan=(0, -1), zoom=.05)
        glow(fr, 700, 1080, 330)
        put(fr, CHAURA(), 720, 1335, 1.0)
        put(fr, TP(10), 720, 1060, 1.0)
        put(fr, VS(gt, mouth='smile', bless=True), 330, 1340 + bob * 4, .88)
        float_sparkles(fr, gt, 3, n=14, y0=700, y1=1300)
    elif si == 1:  # Jalandhar
        draw_bg(fr, 'court', p, zoom=.05)
        put(fr, JL(640), 540, 1300 + bob * 3, .92)
        embers(fr, gt, 12, 4, 500, 1250)
    elif si == 2:  # Vrinda + protective aura
        draw_bg(fr, 'palace', p, pan=(1, 0))
        glow(fr, 330, 1000, 300, k=1.0 + .25 * math.sin(gt * 3))
        put(fr, SP('vrinda', 640, namaste=True, eyes='closed' if gt >= s_t[3][0] else 'open'), 330, 1330 + bob * 2, .9)
        if gt >= s_t[3][0]:
            glow(fr, 770, 980, 330, (255, 215, 120), .9)
            sparkle_burst(fr, 770, 980, (gt - s_t[3][0]) % 1.6, 1.6, n=16, seed=4, rad=300)
        put(fr, JL(640), 770, 1300, .78)
    elif si == 3:  # arrogance, heaven taken
        draw_bg(fr, 'svarga', p, zoom=.06)
        lightning(fr, gt, 1)
        put(fr, JL(640, angry=True, point=True), 480 + math.sin(gt * 18) * 3, 1330, .95)
        embers(fr, gt, 20, 6, 300, 1300)
    elif si == 4:  # Vrinda in puja
        draw_bg(fr, 'pooja', p, zoom=.05)
        put(fr, SP('vrinda', 640, namaste=True, eyes='closed'), 540, 1300 + bob * 2, .9)
        diya(fr, 300, 1250, gt, 1.0)
        diya(fr, 780, 1250, gt, 1.0)
        float_sparkles(fr, gt, 5, n=12, y0=500, y1=1200)
    elif si == 5:  # devas pray to Vishnu
        draw_bg(fr, 'kshira', p, pan=(0, -1), zoom=.06)
        put(fr, VS(gt, mouth='smile', bless=True), 540, 1360 + bob * 5, 1.0)
        float_sparkles(fr, gt, 7, n=16, y0=400, y1=1250)
    elif si == 6:  # disguise; resolve breaks
        draw_bg(fr, 'pooja', p, zoom=.04)
        broke = gt >= s_t[8][0]
        q = min(1.0, t / 2.0)
        glow(fr, 330 - 120 * (1 - q), 1000, 260, (150, 190, 255), .8 + .3 * math.sin(gt * 5))
        put(fr, JL(640), 330 - 120 * (1 - q), 1320, .8)
        put(fr, SP('vrinda', 640, namaste=not broke, eyes='open', mouth='smile' if not broke else 'flat',
                   arms=A((-1.4, 5.6), (1.6, 4.3)) if broke else None), 780, 1320 + bob * 2, .86)
        fl = 1.0 if not broke else max(0.0, 1 - (gt - s_t[8][0]) / 1.2)
        diya(fr, 560, 1250, gt, fl)
    elif si == 7:  # Shiva ends Jalandhar
        draw_bg(fr, 'svarga', p, zoom=.07)
        lightning(fr, gt, 3)
        a = max(0.0, 1 - p * 1.4)
        if a > 0:
            put(fr, JL(640, angry=True), 760, 1330, .75, alpha=a)
        trishul(fr, 400, 900 + (1 - min(1, p * 2)) * -200, 1.1, gt)
        sparkle_burst(fr, 760, 1050, t - .6, 1.4, n=26, seed=7, rad=420)
    elif si == 8:  # Vrinda's curse
        draw_bg(fr, 'pooja', p, zoom=.04, zin=False)
        put(fr, VS(gt, mouth='flat', eyes='closed'), 320, 1330, .84)
        put(fr, SP('vrinda', 640, mouth='flat', arms=A((-2.6, 3.4), (1.5, 5.7))), 790, 1320, .86)
        diya(fr, 560, 1250, gt, 0.0)
    elif si == 9:  # becomes stone
        draw_bg(fr, 'pooja', p, zoom=.05)
        a = max(0.0, 1 - p * 1.3)
        glow(fr, 540, 1150, 260 * (0.6 + p), k=1.0)
        if a > 0:
            put(fr, VS(gt, eyes='closed', mouth='smile', namaste=True), 540, 1330, .9, alpha=a)
        put(fr, SHL(70, 1.0), 540, 1270, min(1.0, .25 + p * 1.2))
        sparkle_burst(fr, 540, 1250, (p * 3) % 1.0, 1.0, n=18, seed=9, rad=260)
    elif si == 10:  # Lakshmi pleads, Vrinda becomes light
        draw_bg(fr, 'glow', p, zoom=.05)
        put(fr, SP('lakshmi', 640, namaste=True), 300, 1330 + bob * 2, .86)
        late = s_t[12][0] + (s_t[12][1] - s_t[12][0]) * .62
        a = 1.0 if gt < late else max(0.0, 1 - (gt - late) / 1.4)
        glow(fr, 780, 1000, 300 * (1.4 - a * .4), (255, 236, 170), 1.3 - a * .3)
        if a > 0:
            put(fr, SP('vrinda', 640, namaste=True, eyes='closed'), 780, 1330, .86, alpha=a)
        float_sparkles(fr, gt, 10, n=18, y0=400, y1=1250)
    elif si == 11:  # tulsi grows
        draw_bg(fr, 'angan', p, zoom=.05)
        g = min(1.0, .1 + p * 1.3)
        glow(fr, 540, 1150, 340 * g + 80)
        put(fr, TP(max(1, int(g * 10))), 540, 1340, 1.25)
        float_sparkles(fr, gt, 12, n=18, y0=500, y1=1300)
    elif si == 12:  # Vishnu's blessing
        draw_bg(fr, 'kshira', p, zoom=.05, pan=(1, 0))
        put(fr, VS(gt, mouth='smile', bless=True), 330, 1350 + bob * 4, .92)
        put(fr, TP(10), 780, 1250, 1.0)
        put(fr, SHL(70, 1.0), 780, 1285, 1.0)
        float_sparkles(fr, gt, 14, n=14, y0=500, y1=1250)
    elif si == 13:  # Tulsi Vivah at home
        draw_bg(fr, 'angan', p, zoom=.06, pan=(0, 1))
        glow(fr, 540, 1080, 340)
        put(fr, CHAURA(), 540, 1340, 1.05)
        put(fr, TP(10), 540, 1050, 1.0)
        put(fr, SHL(55, 1.0), 300, 1270, 1.0)
        diya(fr, 790, 1250, gt, 1.0)
        petals(fr, gt)
    elif si == 14:  # closing
        draw_bg(fr, 'glow', p, zoom=.06)
        put(fr, VS(gt, mouth='smile', bless=True), 380, 1340 + bob * 4, .9)
        put(fr, TP(10), 790, 1330, .95)
        float_sparkles(fr, gt, 16, n=20, y0=300, y1=1250)

def decorate(fr, t, ctx):
    gt = ctx['t0'] + t
    T = ctx['T']
    si = ctx['si']
    d = ImageDraw.Draw(fr, 'RGBA')
    if si == 0:  # cover title
        ts = title_strip()
        a = 1.0 if t < ctx['dur'] - .5 else max(0, (ctx['dur'] - t) / .5)
        if a >= 1.0:
            fr.paste(ts, (40, 425), ts)
        else:
            x = np.array(ts)
            x[..., 3] = (x[..., 3] * a).astype(np.uint8)
            tt = Image.fromarray(x, 'RGBA')
            fr.paste(tt, (40, 425), tt)
    # caption: sentence active at gt
    k = None
    for i, (s0, e0) in enumerate(ctx['sents']):
        nxt = ctx['sents'][i + 1][0] if i + 1 < len(ctx['sents']) else T
        if s0 - 0.05 <= gt < nxt:
            k = i
            break
        if i == 0 and gt < s0:
            k = None
    if k is not None and gt >= ctx['sents'][k][0] - .05:
        cs = caption_strip(k)
        a = min(1.0, (gt - (ctx['sents'][k][0] - .05)) / .15)
        if a < 1.0:
            x = np.array(cs)
            x[..., 3] = (x[..., 3] * a).astype(np.uint8)
            cs = Image.fromarray(x, 'RGBA')
        fr.paste(cs, (int(500 - cs.width / 2), CAP_BOTTOM - cs.height), cs)
    # logo (hidden during ending brand)
    end_on = gt >= T - 3.0
    if not end_on:
        pl = logo_plate()
        fr.paste(pl, (30, 262), pl)
    else:
        a = min(1.0, (gt - (T - 3.0)) / .4)
        es = end_strip()
        if a < 1.0:
            x = np.array(es)
            x[..., 3] = (x[..., 3] * a).astype(np.uint8)
            es = Image.fromarray(x, 'RGBA')
        fr.paste(es, (int(500 - es.width / 2), 290), es)
    # scene-change golden flash
    if si > 0 and t < .18:
        ov = Image.new('RGBA', (W, H), (255, 232, 170, int(150 * (1 - t / .18))))
        fr.alpha_composite(ov)


def render_frame(si, t, p, ctx):
    fr = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    compose(si, fr, t, p, None, ctx)
    decorate(fr, t, ctx)
    gt = ctx['t0'] + t
    fo = 1.5
    if gt > ctx['T'] - fo:
        f = (gt - (ctx['T'] - fo)) / fo
        ov = Image.new('RGBA', (W, H), (0, 0, 0, int(255 * min(1, f))))
        fr.alpha_composite(ov)
    return fr.convert('RGB')


def render_scene(args):
    si, tm, bounds, out = args
    t0, t1 = bounds[si], bounds[si + 1]
    f0, f1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    ctx = {'si': si, 't0': t0, 'dur': t1 - t0, 'T': tm['total'], 'sents': tm['sents']}
    tmp = out + '.tmp.mp4'
    pr = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                           '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp], stdin=subprocess.PIPE)
    n = f1 - f0
    for k in range(n):
        t = k / FPS
        fr = render_frame(si, t, min(1.0, t / max(.01, t1 - t0)), ctx)
        pr.stdin.write(fr.tobytes())
    pr.stdin.close()
    pr.wait()
    os.replace(tmp, out)
    return out


# ------------------------------------------------------------ music
def make_music(total, bounds, path, sr=44100):
    n = int(total * sr)
    t = np.arange(n) / sr
    mix = np.zeros(n, np.float64)
    sa = 146.83
    pat = [sa * 1.5, sa * 2, sa * 2, sa]  # Pa Sa' Sa' Sa
    period = 1.55
    k = 0
    tt = 0.0
    while tt < total:
        f0 = pat[k % 4]
        L = int(min(4.2, total - tt) * sr)
        tl = np.arange(L) / sr
        env = np.exp(-tl / 1.6) * np.minimum(1, tl / .01)
        sig = np.zeros(L)
        for h, amp in ((1, 1.0), (2, .6), (3, .45), (4, .38), (5, .3), (6, .22), (7, .18), (8, .14)):
            sig += amp * np.sin(2 * np.pi * f0 * h * tl + h) * (1 + .15 * np.sin(2 * np.pi * 5 * tl + h))
        s0 = int(tt * sr)
        mix[s0:s0 + L] += .11 * sig * env
        tt += period
        k += 1
    # soft constant drone
    mix += .035 * (np.sin(2 * np.pi * sa * t) + .5 * np.sin(2 * np.pi * sa * 1.5 * t) + .3 * np.sin(2 * np.pi * sa * 2 * t))
    rnd = np.random.RandomState(3)
    # dholak: 90 bpm, simple pattern
    beat = 60 / 64.0
    pat_d = ['d', 't', 't', 'd', 't', 'd', 't', 't']
    tdh = 0.0
    i = 0
    while tdh < total - .3:
        c = pat_d[i % 8]
        L = int(.3 * sr)
        tl = np.arange(L) / sr
        if c == 'd':
            f = 130 * np.exp(-tl * 10) + 58
            ph = 2 * np.pi * np.cumsum(f) / sr
            sig = np.sin(ph) * np.exp(-tl * 12) * .7
        else:
            nz = rnd.randn(L)
            sig = nz * np.exp(-tl * 55) * .12 * np.sin(2 * np.pi * 900 * tl + 1)
        s0 = int(tdh * sr)
        e = min(n, s0 + L)
        mix[s0:e] += .10 * sig[:e - s0]
        tdh += beat / 2
        i += 1
    # bells at scene changes + end
    for bt in list(bounds[:-1]) + [total - 3.0]:
        L = int(2.6 * sr)
        tl = np.arange(L) / sr
        sig = np.zeros(L)
        for r, a in ((1, 1), (2.76, .6), (5.4, .35), (8.93, .2)):
            sig += a * np.sin(2 * np.pi * 988 * r * tl) * np.exp(-tl * (2.2 + r * .5))
        s0 = int(bt * sr)
        e = min(n, s0 + L)
        mix[s0:e] += .09 * sig[:e - s0]
    fade = np.minimum(1, t / .05)
    mix *= fade
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * .8
    import wave
    st = np.stack([mix, np.roll(mix, int(.012 * sr))], 1)
    pcm = (st * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# ------------------------------------------------------------ main
def preview(tm, frames):
    bounds = scene_bounds(tm)
    os.makedirs(OUT, exist_ok=True)
    for si, tf in frames:
        t0, t1 = bounds[si], bounds[si + 1]
        ctx = {'si': si, 't0': t0, 'dur': t1 - t0, 'T': tm['total'], 'sents': tm['sents']}
        t = min(tf, t1 - t0 - .01)
        fr = render_frame(si, t, t / (t1 - t0), ctx)
        fr.save(f'{OUT}/prev_s{si}_{int(tf * 10)}.png')
    return bounds


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'preview':
        tm = timing_from_audio('voice.mp3', tempo=1.0, total=95.0, offset=0.4)
        b = scene_bounds(tm)
        fr = [(0, 0.0)] + [(i, (b[i + 1] - b[i]) * .6) for i in range(1, len(b) - 1)] + [(len(b) - 2, b[-1] - b[-2] - 1.0)]
        preview(tm, fr)
        print([round(x, 1) for x in b])
