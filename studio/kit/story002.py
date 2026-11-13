"""Story #2 : लंका दहन  -> 1080x1920 reel builder (art.py kit)."""
import sys, os, json, math, subprocess, random, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache
from art import *

FPS = 30
OUT = 'out'
TITLE = 'लंका दहन'
SUBTITLE = 'हनुमान जी की वीर कथा'
END_TEXT = 'The Meet More | फ़ॉलो करें, कल की कथा'
SENTS = [
    'सीता माता की खोज में, हनुमान जी लंका पहुँचे।',
    'अशोक वाटिका में माता को श्रीराम की अँगूठी दी।',
    'फिर वाटिका उजाड़ी, और राक्षसों को हरा दिया।',
    'मेघनाद उन्हें बाँधकर रावण की सभा में ले गया।',
    'हनुमान जी बोले, सीता माता को लौटा दो।',
    'क्रोधित रावण बोला, इस वानर की पूँछ जला दो।',
    'पूँछ पर कपड़ा लपेटकर आग लगा दी गई।',
    'हनुमान जी बंधन से छूटे, और महलों पर कूदने लगे।',
    'देखते ही देखते, सोने की लंका जल उठी।',
    'बस विभीषण का घर बचा, जहाँ राम नाम था।',
    'समुद्र में आग बुझाकर, वे राम जी के पास लौटे।',
    'जिसके मन में राम हैं, उसे कोई आग नहीं जला सकती।',
    'जय बजरंगबली!',
]
SCENE_FIRST = [0, 1, 2, 3, 5, 7, 9, 10, 11]
CAP_BOTTOM = 1535
LOGO_W = 230


def font(sz):
    return ImageFont.truetype(FONT, sz)


# ------------------------------------------------------------ timing
def estimate_timing(total=55.0, start=1.6):
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
OFFSET = 1.6


@lru_cache(None)
def HN(H_=640, **kw):
    kw = dict(kw)
    if 'arms' in kw and isinstance(kw['arms'], str):
        kw['arms'] = json.loads(kw['arms'])
    return hanuman(H_, **kw)


@lru_cache(None)
def RV(H_=640, **kw):
    return ravana(H_, **kw)


def flames(fr, t, inten=1.0, seed=3, y0=1000, y1=1320, n=26, big=1.0):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(fr, 'RGBA')
    glow = Image.new('RGBA', (W, H), (255, 110, 30, int(70 * inten)))
    fr.alpha_composite(glow)
    for i in range(n):
        if rnd.random() > inten:
            rnd.random(); rnd.random(); rnd.random()
            continue
        x = rnd.random() * (W + 80) - 40
        y = y0 + rnd.random() * (y1 - y0)
        r = (30 + rnd.random() * 55) * big
        ph = rnd.random() * 6
        k = math.sin(t * 8 + ph) * .22
        hh = r * (2.0 + .35 * math.sin(t * 6 + ph * 2))
        d.polygon([(x - r, y), (x - r * .5, y - hh * .55), (x + k * r, y - hh), (x + r * .55, y - hh * .5), (x + r, y)], fill=(232, 70, 30, 235))
        d.polygon([(x - r * .6, y), (x - r * .2, y - hh * .45), (x + k * r * .8, y - hh * .75), (x + r * .4, y - hh * .4), (x + r * .6, y)], fill=(247, 154, 30, 240))
        d.polygon([(x - r * .3, y), (x, y - hh * .45), (x + r * .3, y)], fill=(255, 228, 92, 245))
    # embers
    for i in range(30):
        ex = rnd.random() * W
        sp_ = .15 + rnd.random() * .2
        q = (t * sp_ + rnd.random()) % 1.0
        ey = y1 - q * (y1 - 250)
        a = int(220 * (1 - q) * inten)
        d.ellipse([ex - 4, ey - 4, ex + 4, ey + 4], fill=(255, 200, 80, a))


def smoke(fr, t, seed=5, a=90):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(fr, 'RGBA')
    for i in range(10):
        x = rnd.random() * W
        q = (t * .06 + rnd.random()) % 1.0
        y = 900 - q * 700
        r = 80 + q * 160
        d.ellipse([x - r, y - r * .6, x + r, y + r * .6], fill=(40, 20, 25, int(a * math.sin(q * math.pi))))


@lru_cache(None)
def vib_house():
    cv = Cv(W, H)
    cv.rect(330, 900, 750, 1320, hx('#EADBB8'))
    cv.poly([(290, 910), (540, 700), (790, 910)], hx('#C98A1B'))
    cv.rect(500, 1120, 580, 1320, hx('#7A4A22'))
    cv.ell(540, 780, 30, 30, hx('#FFE08A'))
    cv.rect(390, 1000, 470, 1080, hx('#3A1A10')); cv.rect(610, 1000, 690, 1080, hx('#3A1A10'))
    # tulsi
    cv.rect(760, 1240, 840, 1320, hx('#B5532A'))
    for k in range(5):
        cv.ell(800 + (k - 2) * 14, 1215 - k % 2 * 18, 22, 30, hx('#3F8A3A'))
    im = cv.out()
    d = ImageDraw.Draw(im, 'RGBA')
    f = font(78)
    tw = f.getlength('राम')
    d.rounded_rectangle([540 - tw / 2 - 22, 925, 540 + tw / 2 + 22, 1030], 20, fill=hx('#FFF1D0', 235), outline=hx(GOLD2), width=4)
    d.text((540 - tw / 2, 930), 'राम', font=f, fill=hx('#C0392B'), stroke_width=2, stroke_fill=hx('#7A1A1A'))
    return im


def halo(fr, cx, cy, r, a=150):
    R = int(r)
    yy, xx = np.mgrid[-R:R, -R:R]
    dd = np.sqrt(xx ** 2 + yy ** 2) / R
    al = (np.clip(1 - dd, 0, 1) ** 1.6 * a).astype(np.uint8)
    arr = np.zeros((2 * R, 2 * R, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3] = 255, 236, 170, al
    g = Image.fromarray(arr, 'RGBA')
    fr.alpha_composite(g, (int(cx - R), int(cy - R)))


def compose(si, fr, t, p, L, ctx):
    gt = ctx['t0'] + t
    s_t = ctx['sents']
    bob = math.sin(t * 2.6)
    if si == 0:  # cover + leap to Lanka
        draw_bg(fr, 'lanka', p, pan=(0, -1))
        halo(fr, 540, 1060, 330, 120)
        hn = HN(640, jump=1.0, arms=A((-2.6, 2.2), (1.9, 4.2)))
        x = 540 + 120 * p
        y = 1400 - 60 * math.sin(min(1, p) * math.pi)
        put(fr, hn, x, y + bob * 6, .82)
        float_sparkles(fr, gt, 3)
    elif si == 1:  # Ashok Vatika, ring
        draw_bg(fr, 'vatika', p, zoom=.05)
        st = SP('sita', 640, arms=A((-1.5, 5.7), (1.2, 4.6)) if p > .45 else A((-1.5, 5.7), (1.5, 5.7)),
                eyes='open', mouth='smile' if p > .45 else 'flat')
        put(fr, st, 330, 1330 + bob * 2, .9)
        hn = HN(640, gada=False, ring=True, arms=A((-2.2, 4.0), (1.5, 5.6)), flip=False)
        put(fr, hn.transpose(Image.FLIP_LEFT_RIGHT), 790, 1330 - abs(math.sin(gt * 2)) * 6, .78)
        if p > .45:
            sparkle_burst(fr, 560, 1000, (p - .45) * ctx['dur'], 1.2, n=18, seed=11, rad=240)
        float_sparkles(fr, gt, 12, n=10, y0=300, y1=1100)
    elif si == 2:  # vatika destroyed
        draw_bg(fr, 'vatika', p, pan=(1, 0), zoom=.08)
        d = ImageDraw.Draw(fr, 'RGBA')
        rnd = random.Random(4)
        for k in range(26):  # falling leaves/flowers
            x0 = rnd.random() * W
            q = (gt * (.25 + rnd.random() * .3) + rnd.random()) % 1.0
            x = x0 + math.sin(gt * 3 + k) * 30
            y = 250 + q * 1150
            col = (232, 70, 46, 230) if k % 3 == 0 else (60, 140, 70, 230)
            d.ellipse([x - 12, y - 7, x + 12, y + 7], fill=col)
        jump = abs(math.sin(gt * 4.2)) * 70
        hn = HN(640, jump=min(1, jump / 70), arms=A((-2.6, 3.0), (2.0, 3.6)), mouth='open')
        put(fr, hn, 520 + math.sin(gt * 2.1) * 120, 1340 - jump, .85)
    elif si == 3:  # bound, Ravana court; speaks
        draw_bg(fr, 'court', p, zoom=.05)
        put(fr, RV(560), 540, 1200, 1.1)
        speak = gt >= s_t[4][0]
        hn = HN(640, bound=True, gada=False, arms=A((-1.3, 5.4), (1.3, 5.4)), mouth='open' if speak else 'flat')
        put(fr, hn, 540 - 30, 1420 + bob * 3, .78)
        float_sparkles(fr, gt, 13, n=6, y0=300, y1=900)
    elif si == 4:  # Ravana orders, tail set ablaze
        draw_bg(fr, 'court', p, zoom=.06, zin=False)
        put(fr, RV(560, angry=True, point=True), 620, 1200 + bob * 2, 1.1)
        fire = gt >= s_t[6][0] + .4
        hn = HN(640, bound=True, gada=False, tail_fire=fire, arms=A((-1.3, 5.4), (1.3, 5.4)), mouth='flat', t=gt if fire else 0)
        put(fr, hn, 300, 1420, .74)
        if fire:
            sparkle_burst(fr, 440, 860, gt - (s_t[6][0] + .4), 1.0, n=14, seed=21, rad=200)
            ov = Image.new('RGBA', (W, H), (255, 90, 20, 40))
            fr.alpha_composite(ov)
    elif si == 5:  # leaping over burning Lanka
        draw_bg(fr, 'fire', p, zoom=.05)
        inten = .35 + .65 * p
        smoke(fr, gt, a=int(60 + 60 * p))
        flames(fr, gt, inten, seed=5, y0=950, y1=1330, n=30, big=1.0 + .5 * p)
        cyc = (gt * .55) % 1.0
        x = -100 + cyc * (W + 200)
        y = 1050 - math.sin(cyc * math.pi) * 380
        hn = HN(640, jump=1.0, tail_fire=True, gada=True, arms=A((-2.6, 2.2), (1.9, 4.2)), t=gt)
        put(fr, hn, x, y, .62)
    elif si == 6:  # Vibhishan house spared
        draw_bg(fr, 'fire', p, zoom=.04, zin=False)
        smoke(fr, gt, seed=8, a=90)
        flames(fr, gt, .9, seed=9, y0=1050, y1=1340, n=30, big=1.2)
        halo(fr, 540, 1000, 420, 170)
        vh = vib_house()
        fr.alpha_composite(vh)
        float_sparkles(fr, gt, 14, n=12, y0=600, y1=1300)
    elif si == 7:  # back over the sea
        draw_bg(fr, 'sea', p, pan=(-1, 0))
        x = 860 - 520 * p
        y = 1150 - math.sin(p * math.pi) * 250
        hn = HN(640, jump=1.0, gada=True, arms=A((-2.6, 2.2), (1.9, 4.2)))
        put(fr, hn.transpose(Image.FLIP_LEFT_RIGHT), x, y, .66)
        d = ImageDraw.Draw(fr, 'RGBA')
        if p < .35:  # splash/steam where tail was dipped
            q = p / .35
            for k in range(8):
                sx = 880 + k * 18 - 70
                d.ellipse([sx - 20 * q - 10, 1120 - 140 * q - 10, sx + 20 * q + 10, 1120 - 140 * q + 10],
                          fill=(255, 255, 255, int(170 * (1 - q))))
        float_sparkles(fr, gt, 15, n=8, y0=300, y1=900)
    elif si == 8:  # closing: devotion
        draw_bg(fr, 'glow', p, zoom=.05)
        halo(fr, 540, 900, 380, 140)
        hn = HN(640, namaste=True, gada=False, eyes='closed')
        put(fr, hn, 540, 1340 + bob * 3, .9)
        float_sparkles(fr, gt, 16, n=18, y0=300, y1=1300)
        if gt >= s_t[12][0]:
            sparkle_burst(fr, 540, 820, gt - s_t[12][0], 1.4, n=30, seed=17, rad=460)


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
        lg = logo_img()
        fr.paste(lg, (48, 270), lg)
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
    beat = 60 / 90.0
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
        mix[s0:e] += .16 * sig[:e - s0]
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


_timing_raw = timing_from_audio


def timing_from_audio(path, offset=0.4, total=None, tempo=1.0):
    """Story-specific fix: silence at 28.88-29.22s (raw) is the 7/8 sentence boundary; 30.54s is a comma."""
    tm = _timing_raw(path, offset=offset, total=total, tempo=tempo)
    tm['sents'][7][1] = 28.88 / tempo + offset
    tm['sents'][8][0] = 29.22 / tempo + offset
    return tm


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
        tm = estimate_timing()
        b = preview(tm, [(0, 0.0), (0, 3.0), (1, 2.5), (2, 1.5), (3, 1.0), (3, 6.0), (4, 2.0), (4, 7.0), (5, 2.0), (5, 7.0), (6, 2.0), (7, 1.0), (7, 3.0), (8, 2.0), (8, 9.0)])
        print([round(x, 1) for x in b])
