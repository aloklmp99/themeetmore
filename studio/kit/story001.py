"""Story #1 : सुदामा मित्रता  -> 1080x1920 reel builder (art.py kit)."""
import sys, os, json, math, subprocess, random, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache
from art import *

FPS = 30
OUT = 'out'
TITLE = 'सुदामा मित्रता'
SUBTITLE = 'कृष्ण और सुदामा की भक्ति कथा'
END_TEXT = 'The Meet More | फ़ॉलो करें, कल की कथा'
SENTS = [
    'द्वारका के राजा श्रीकृष्ण, और गरीब ब्राह्मण सुदामा, बचपन के दो सच्चे मित्र।',
    'संदीपनी आश्रम में साथ पढ़े थे, पर समय ने दोनों को अलग कर दिया।',
    'सुदामा के घर में अन्न का दाना नहीं था।',
    'पत्नी ने कहा, जाओ, अपने मित्र कृष्ण से मिल आओ।',
    'सुदामा के पास भेंट देने को बस मुट्ठी भर चिवड़ा था, जिसे वे फटे वस्त्र में छुपाए थे।',
    'द्वारका पहुँचे तो कृष्ण ने उन्हें देखते ही नंगे पाँव दौड़कर गले लगा लिया।',
    'अपने आँसुओं से मित्र के पाँव धोए, और उन्हें अपने आसन पर बिठाया।',
    'फिर कृष्ण ने प्रेम से वही चिवड़ा खाया।',
    'सुदामा संकोच में कुछ माँग न सके।',
    'घर लौटे तो झोंपड़ी की जगह सुंदर महल खड़ा था।',
    'सच्ची मित्रता में अमीरी-गरीबी नहीं, सिर्फ़ प्रेम होता है।',
    'जय श्रीकृष्ण!',
]
SCENE_FIRST = [0, 1, 2, 4, 5, 6, 7, 9, 10]  # first sentence index of each scene
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
def compose(si, fr, t, p, L, ctx):
    """t: seconds in scene, p: progress 0..1, L: dict with global sentence times."""
    gt = ctx['t0'] + t
    s_t = ctx['sents']
    bob = math.sin(t * 2.6)
    if si == 0:
        draw_bg(fr, 'dwarka', p, pan=(0, -1))
        K = SP('krishna', 640, arms=A((-1.9, 5.0), (1.9, 5.0)))
        S_ = SUD_BUNDLE()
        put(fr, K, 360, 1310 + bob * 4, .82)
        put(fr, S_, 730, 1310 - bob * 4, .82)
        float_sparkles(fr, gt, 3)
    elif si == 1:
        draw_bg(fr, 'ashram', p, pan=(1, 0))
        kk = SP('krishna', 430, kid=True, arms=A((-1.7, 5.0), (1.7, 5.0)))
        ss = SP('sudama', 430, kid=True, arms=A((-1.5, 5.0), (1.5, 5.0)))
        gap = 150 + 600 * max(0, (p - .42) / .58) ** 1.4
        jump = abs(math.sin(gt * 4.0)) * 26 * (1 - min(1, max(0, (p - .35) / .2)))
        if p > .55:
            kk = SP('krishna', 430, kid=True, mouth='flat', eyes='open', arms=A((-1.2, 5.2), (1.2, 5.2)))
            ss = SP('sudama', 430, kid=True, mouth='flat', arms=A((-1.2, 5.2), (1.2, 5.2)))
        put(fr, kk, 540 - gap / 2, 1300 - jump)
        put(fr, ss, 540 + gap / 2, 1300 - jump * .9)
    elif si == 2:
        draw_bg(fr, 'hut', p, pan=(-1, 0))
        su = SP('sudama', 640, mouth='flat', arms=A((-1.2, 5.6), (1.2, 5.6)))
        pointing = gt >= s_t[3][0]
        sus = SP('susheela', 640, arms=A((-1.5, 5.7), (3.0, 3.7)), mouth='open') if pointing else \
            SP('susheela', 640, arms=A((-1.5, 5.7), (1.5, 5.7)), mouth='flat')
        put(fr, su, 330, 1300 + bob * 3)
        put(fr, sus, 740, 1300 - bob * 3)
    elif si == 3:
        draw_bg(fr, 'road', p, zoom=0.04)
        ph = int((gt * 7) % 8)
        wk = SP('sudama', 640, arms=A((-1.4, 5.6), (1.2, 4.6)), bundle=True, walk=ph * math.pi / 4)
        sc = .55 + .45 * p
        put(fr, wk, 540, 1215 + 150 * p, sc)
        float_sparkles(fr, gt, 9, n=6, y0=300, y1=900)
    elif si == 4:
        draw_bg(fr, 'gate', p, zoom=0.05)
        hug_t = 0.55
        if p < hug_t:
            q = p / hug_t
            ph = int((gt * 9) % 8)
            kr = SP('krishna', 640, arms=A((-2.1, 3.6), (2.1, 3.6)), walk=ph * math.pi / 4, mouth='open')
            put(fr, SUD_BUNDLE(), 270, 1300)
            put(fr, kr, 980 - 520 * q, 1300 + (abs(math.sin(gt * 9)) * -14))
        else:
            tt = (p - hug_t) * ctx['dur']
            pop = 1 + .06 * max(0, 1 - tt / .3)
            put(fr, PAIR(640), 440, 1300, pop)
            sparkle_burst(fr, 440, 780, tt, 1.1, seed=4)
            float_sparkles(fr, gt, 5, n=10)
    elif si == 5:
        draw_bg(fr, 'throne', p, zoom=0.05)
        su = SP('sudama', 640, arms=A((-1.2, 5.2), (1.2, 5.2)), eyes='closed')
        put(fr, su, 560, 1210, .9)
        fr.paste(throne_front(), (0, 0), throne_front())
        kr = crop_waist(SP('krishna', 640, arms=A((2.6, 5.0), (3.3, 5.4)), eyes='closed'), .6)
        put(fr, kr, 380, 1312 + bob * 3, .9)
        d = ImageDraw.Draw(fr, 'RGBA')
        for fx in (505, 605):
            d.ellipse([fx - 34, 1262, fx + 34, 1292], fill=hx(SKIN['sudama']))
        for k in range(5):  # tear drops
            q = ((gt * 0.9 + k * .21) % 1.0)
            x = 470 + k * 38 + math.sin(k * 7) * 8
            y = 1000 + q * 270
            d.ellipse([x - 7, y - 11, x + 7, y + 11], fill=(150, 215, 245, int(230 * (1 - q * .4))))
        float_sparkles(fr, gt, 6, n=8, y0=300, y1=900)
    elif si == 6:
        draw_bg(fr, 'throne', p, zoom=0.05, zin=False)
        eat = .5 + .5 * math.sin(gt * 3.0)
        kr = SP('krishna', 640, arms=A((-1.1, 4.6), (.35 + .2 * eat, 3.8 - .15 * eat)), eyes='closed')
        put(fr, kr, 650, 1210, .9)
        fr.paste(throne_front(), (0, 0), throne_front())
        d = ImageDraw.Draw(fr, 'RGBA')
        bx, by = 650 + (-1.1) * 64 * .9, 1210 - (640 + 102) * .9 + (4.6 * 64 + 102) * .9
        d.ellipse([bx - 52, by - 14, bx + 52, by + 40], fill=hx('#F3E2B8'), outline=hx('#B58A4A'), width=3)
        rnd = random.Random(2)
        for _ in range(14):
            px, py = bx - 40 + rnd.random() * 80, by - 6 + rnd.random() * 34
            d.ellipse([px - 4, py - 3, px + 4, py + 3], fill=hx('#E3C47A'))
        su = SP('sudama', 640, namaste=True, eyes='closed', mouth='flat')
        put(fr, su, 220, 1330 + bob * 2, .85)
        float_sparkles(fr, gt, 8, n=8, y0=300, y1=900)
    elif si == 7:
        cut = .4
        if p < cut:
            draw_bg(fr, 'hut', p / cut, pan=(0, 0), zoom=.04)
            su = SP('sudama', 640, mouth='flat', arms=A((-1.2, 5.6), (1.2, 5.6)))
            put(fr, su, 540, 1350, .95)
        else:
            q = (p - cut) * ctx['dur']
            draw_bg(fr, 'palace', (p - cut) / (1 - cut), zoom=.05)
            su = SP('sudama', 640, arms=A((-1.7, 2.7), (1.7, 2.7)), mouth='open')
            put(fr, su, 540, 1350 + math.sin(gt * 3) * 5, .95)
            sparkle_burst(fr, 540, 760, q, 1.4, n=30, seed=7, rad=460)
            float_sparkles(fr, gt, 10, n=16, y0=300, y1=1300)
            fl = max(0, 1 - q / .35)
            if fl > 0:
                ov = Image.new('RGBA', (W, H), (255, 236, 170, int(200 * fl)))
                fr.alpha_composite(ov)
    elif si == 8:
        draw_bg(fr, 'dwarka', p, zoom=.06)
        put(fr, PAIR(640), 540, 1290 + bob * 2, .88)
        float_sparkles(fr, gt, 11, n=16)


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
