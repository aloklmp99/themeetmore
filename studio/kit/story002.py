"""Story #1 : सुदामा मित्रता  -> 1080x1920 reel builder (art.py kit)."""
import sys, os, json, math, subprocess, random, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache
from art import *

FPS = 30
OUT = 'out'
TITLE = 'लंका दहन'
SUBTITLE = 'हनुमान जी की भक्ति कथा'
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
def HN(H=640, **kw):
    kw = dict(kw)
    if 'arms' in kw and isinstance(kw['arms'], str):
        kw['arms'] = json.loads(kw['arms'])
    return hanuman(H, **kw)


@lru_cache(None)
def RV(H=640, **kw):
    return ravana(H, **kw)


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


def compose(si, fr, t, p, L, ctx):
    gt = ctx['t0'] + t
    s_t = ctx['sents']
    bob = math.sin(t * 2.6)
    if si == 0:
        draw_bg(fr, 'lanka', p, pan=(-1, 0))
        jump = .0
        put(fr, HN(640, arms=A((-1.7, 5.6), (1.9, 4.2))), 540, 1320 + bob * 6, .78)
        float_sparkles(fr, gt, 3, n=12, y0=700, y1=1250)
    elif si == 1:
        draw_bg(fr, 'vatika', p, pan=(1, 0))
        put(fr, SP('sita', 640, namaste=True, mouth='smile'), 790, 1320 + bob * 3, .85)
        put(fr, HN(640, gada=False, ring=True, arms=A((2.3, 3.8), (1.5, 5.2)), mouth='smile'), 370, 1330 + bob * 3, .85)
        g = .5 + .5 * math.sin(gt * 5)
        sparkle_burst(fr, 560, 880, (gt * 1.1) % 1.2, 1.2, n=8, seed=2, rad=120)
        float_sparkles(fr, gt, 6, n=8, y0=400, y1=1200)
    elif si == 2:
        draw_bg(fr, 'vatika', p, pan=(-1, 0), zoom=.06)
        x = 540 + math.sin(t * 1.7) * 180
        j = abs(math.sin(t * 2.4))
        put(fr, HN(640, jump=.8 if j > .35 else 0.0, mouth='open', arms=A((-2.1, 3.0), (1.9, 4.2))), x, 1330 - j * 90, .9)
        falling(fr, gt, 34, 5)
    elif si == 3:
        draw_bg(fr, 'court', p, zoom=.04)
        put(fr, RV(640, angry=False), 720, 1240 + bob * 3, .78)
        spoke = gt >= s_t[4][0]
        put(fr, HN(640, gada=False, bound=True, mouth='open' if spoke and math.sin(gt * 9) > 0 else 'flat', arms=A((-1.7, 5.6), (1.9, 4.2))), 320, 1330, .85)
        float_sparkles(fr, gt, 8, n=8, y0=400, y1=1100)
    elif si == 4:
        draw_bg(fr, 'court', p, zoom=.05)
        shake = math.sin(gt * 22) * 4 if gt < s_t[6][0] else 0
        put(fr, RV(640, angry=True, point=True), 720 + shake, 1240, .8)
        fire = gt >= s_t[6][0]
        ff = int((gt * 8) % 3)
        put(fr, HN(640, gada=False, bound=True, tail_fire=fire, t=ff * .6, mouth='flat', arms=A((-1.7, 5.6), (1.9, 4.2))), 320, 1330, .85)
        if fire:
            embers(fr, gt, 18, 4, 500, 1200)
    elif si == 5:
        draw_bg(fr, 'fire', p, zoom=.04)
        flames(fr, gt, [110, 300, 480, 690, 880, 1010], 1300, 1.0, 2)
        q = min(1.0, p / .85)
        x = 160 + 760 * q
        j = abs(math.sin(gt * 3.2))
        ff = int((gt * 8) % 3)
        put(fr, HN(640, jump=.9, gada=False, tail_fire=True, t=ff * .6, mouth='open', arms=A((-2.0, 3.2), (1.9, 3.6))), x, 1050 - j * 160, .78)
        embers(fr, gt, 34, 6, 300, 1300)
    elif si == 6:
        draw_bg(fr, 'fire', p, zoom=.04)
        flames(fr, gt, [100, 260, 820, 980], 1300, 1.0, 3)
        d = ImageDraw.Draw(fr, 'RGBA')
        glow = int(70 + 40 * math.sin(gt * 3))
        for r, a in ((260, 40), (200, 60), (150, 80)):
            d.ellipse([540 - r, 1120 - r, 540 + r, 1120 + r], fill=(255, 226, 140, a + glow // 4))
        d.rectangle([420, 1080, 660, 1300], fill=(196, 150, 90, 255))
        d.polygon([(390, 1090), (540, 940), (690, 1090)], fill=(150, 90, 40, 255))
        d.rectangle([505, 1170, 575, 1300], fill=(80, 40, 20, 255))
        f = ImageFont.truetype(FONT, 78)
        tx = 'राम'
        tw = f.getlength(tx)
        d.text((540 - tw / 2, 1010), tx, font=f, fill=(255, 226, 120, 255), stroke_width=5, stroke_fill=(90, 20, 20, 255))
        put(fr, HN(640, gada=False, namaste=True, mouth='smile', eyes='closed'), 220, 1330 + bob * 2, .72)
        embers(fr, gt, 24, 7, 400, 1300)
    elif si == 7:
        draw_bg(fr, 'sea', p, zoom=.05)
        q = min(1.0, p / .9)
        x = 180 + 720 * q
        y = 760 + 260 * math.sin(q * math.pi * .9) * -1 + 200 * q
        dip = p > .35
        ff = int((gt * 8) % 3)
        put(fr, HN(640, jump=.7, gada=False, tail_fire=not dip, t=ff * .6, mouth='smile', arms=A((-2.0, 3.0), (2.0, 3.0))), x, y + 520, .72)
        if dip:
            sparkle_burst(fr, 380, 1120, (gt * 1.4) % 1.3, 1.3, n=18, seed=9, rad=160)
        float_sparkles(fr, gt, 12, n=10, y0=400, y1=1100)
    elif si == 8:
        draw_bg(fr, 'glow', p, zoom=.06)
        put(fr, HN(640, gada=False, namaste=True, mouth='smile', eyes='closed'), 540, 1330 + bob * 4, .95)
        float_sparkles(fr, gt, 14, n=18, y0=300, y1=1250)

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
        b = preview(tm, [(0, 0.0), (1, 1.0), (1, 4.0), (2, 4.0), (3, 2.0), (4, 1.0), (4, 5.0), (5, 3.0), (6, 3.0), (7, 1.0), (7, 4.0), (8, 5.0), (8, 8.0)])
        print([round(x, 1) for x in b])
