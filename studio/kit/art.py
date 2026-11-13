"""2D flat-vector (PIL) art kit for The Meet More bhakti reels."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, math, random

W, H = 1080, 1920
S = 2  # supersample
FONT = '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'

MAROON = '#5A0F1E'; MAROON2 = '#7A1A2C'; GOLD = '#E8B84A'; GOLD2 = '#C98A1B'
CREAM = '#FFF1D0'; SAFF = '#F08A24'; KBLUE = '#4A86D6'; PITAM = '#F4C430'


def hx(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


class Cv:
    def __init__(s, w, h, bg=(0, 0, 0, 0)):
        s.w, s.h = w, h
        s.im = Image.new('RGBA', (w * S, h * S), bg)
        s.d = ImageDraw.Draw(s.im, 'RGBA')
        s.oy = 0

    def P(s, pts):
        return [(x * S, (y + s.oy) * S) for x, y in pts]

    def poly(s, pts, fill):
        s.d.polygon(s.P(pts), fill=fill)

    def ell(s, cx, cy, rx, ry, fill, out=None, w=0):
        s.d.ellipse([(cx - rx) * S, (cy - ry + s.oy) * S, (cx + rx) * S, (cy + ry + s.oy) * S], fill=fill,
                    outline=out, width=max(1, int(w * S)) if out else 0)

    def rect(s, x0, y0, x1, y1, fill):
        s.d.rectangle([x0 * S, (y0 + s.oy) * S, x1 * S, (y1 + s.oy) * S], fill=fill)

    def rrect(s, x0, y0, x1, y1, r, fill, out=None, w=0):
        s.d.rounded_rectangle([x0 * S, (y0 + s.oy) * S, x1 * S, (y1 + s.oy) * S], r * S, fill=fill, outline=out,
                              width=max(1, int(w * S)) if out else 0)

    def line(s, pts, fill, w):
        P = s.P(pts)
        s.d.line(P, fill=fill, width=max(1, int(w * S)), joint='curve')
        r = w * S / 2
        for x, y in (P[0], P[-1]):
            s.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def arc(s, cx, cy, rx, ry, a0, a1, fill, w):
        s.d.arc([(cx - rx) * S, (cy - ry + s.oy) * S, (cx + rx) * S, (cy + ry + s.oy) * S], a0, a1, fill=fill,
                width=max(1, int(w * S)))

    def vgrad(s, y0, y1, c0, c1, x0=0, x1=None):
        x1 = s.w if x1 is None else x1
        n = int((y1 - y0) * S)
        t = np.linspace(0, 1, n)[:, None]
        a = np.array(c0, float)[None, :] * (1 - t) + np.array(c1, float)[None, :] * t
        arr = np.repeat(a[:, None, :], int((x1 - x0) * S), axis=1).astype(np.uint8)
        s.im.paste(Image.fromarray(arr, 'RGBA'), (int(x0 * S), int(y0 * S)))

    def paste(s, im, x, y):
        s.im.alpha_composite(im, (int(x * S), int(y * S)))

    def out(s):
        return s.im.resize((s.w, s.h), Image.LANCZOS)


# ---------------------------------------------------------------- people
SKIN = {'krishna': '#4A86D6', 'sudama': '#B87B4F', 'susheela': '#C48A5C', 'sita': '#E2A574'}
SAREE = {'susheela': ('#D9772B', '#9B3B1E', '#B8601F', '#7C2D12', '#F2A33C'),
         'sita': ('#C8202E', '#F2B632', '#9E1622', '#E8A21C', '#F7C948')}


def _arm(c, sh, hand, col, wid, sign):
    sx, sy = sh
    hx_, hy_ = hand
    vx, vy = hx_ - sx, hy_ - sy
    L = math.hypot(vx, vy) or 1
    px, py = -vy / L, vx / L
    c1 = (sx + vx / 2 + px * L * .18, sy + vy / 2 + py * L * .18)
    c2 = (sx + vx / 2 - px * L * .18, sy + vy / 2 - py * L * .18)
    el = c1 if c1[1] > c2[1] else c2
    c.line([sh, el, hand], col, wid)
    c.ell(hand[0], hand[1], wid * .62, wid * .62, col)


def person(kind, Hh=760, arms=None, bundle=False, walk=0.0, eyes='open', mouth='smile',
           flip=False, layer='all', kid=False, namaste=False, head_dx=0.0):
    """Flat-vector standing figure. Returns RGBA sprite, feet at bottom centre."""
    w = int(Hh * .95)
    pad = int(Hh * .16)
    c = Cv(w, Hh + pad)
    c.oy = pad
    u = Hh / 10.0
    cx = w / 2
    skin = hx(SKIN[kind])
    dark = hx('#2A1208')
    thin = kind == 'sudama'
    tw = 1.55 * u if thin else 2.2 * u  # torso half-width*... full
    head_r = (1.25 if kid else 0.95) * u
    head_cy = 2.0 * u if not kid else 2.3 * u
    if arms is None:
        arms = ((-1.5, 5.7), (1.5, 5.7))
    if namaste:
        arms = ((-.25, 4.0), (.25, 4.0))
    shL = (cx - tw / 2 + .1 * u, 3.2 * u)
    shR = (cx + tw / 2 - .1 * u, 3.2 * u)
    awid = (.42 if thin else .55) * u

    def draw_arms():
        _arm(c, shL, (cx + arms[0][0] * u, arms[0][1] * u), skin, awid, -1)
        _arm(c, shR, (cx + arms[1][0] * u, arms[1][1] * u), skin, awid, 1)
        if bundle:
            bx, by = cx + arms[1][0] * u, arms[1][1] * u
            c.ell(bx, by + .55 * u, .62 * u, .55 * u, hx('#F3E2B8'), hx('#B58A4A'), 2)
            c.poly([(bx - .2 * u, by + .05 * u), (bx + .2 * u, by + .05 * u), (bx, by - .35 * u)], hx('#F3E2B8'))
            c.ell(bx, by - .3 * u, .12 * u, .12 * u, hx('#B58A4A'))
            c.line([(bx - .3 * u, by + .5 * u), (bx + .3 * u, by + .6 * u)], hx('#B58A4A'), 2)
        if kind == 'krishna' and not namaste:
            pass

    if layer == 'arms':
        draw_arms()
        im = c.out()
        return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im

    # legs / feet
    sw = math.sin(walk) * .35 * u
    for sgn, off in ((-1, sw), (1, -sw)):
        fx = cx + sgn * .65 * u + off
        c.rrect(fx - .28 * u, 8.6 * u, fx + .28 * u, 9.75 * u, .2 * u, skin)
        c.ell(fx + sgn * .02 * u, 9.78 * u, .45 * u, .2 * u, skin)

    # lower garment
    if kind == 'krishna':
        gc, gd = hx(PITAM), hx('#D9A41A')
        c.poly([(cx - 1.25 * u, 5.1 * u), (cx + 1.25 * u, 5.1 * u), (cx + 1.7 * u, 9.1 * u), (cx - 1.7 * u, 9.1 * u)], gc)
        for k in (-.8, -.3, .3, .8):
            c.line([(cx + k * u * .8, 5.4 * u), (cx + k * u * 1.15, 9.0 * u)], gd, 2)
        c.rrect(cx - 1.3 * u, 5.0 * u, cx + 1.3 * u, 5.4 * u, .1 * u, hx('#C0392B'))
    elif kind == 'sudama':
        gc = hx('#EADFC4')
        c.poly([(cx - 1.0 * u, 5.1 * u), (cx + 1.0 * u, 5.1 * u), (cx + 1.35 * u, 8.7 * u), (cx - 1.35 * u, 8.7 * u)], gc)
        # torn hem
        zz = [(cx - 1.35 * u, 8.7 * u)]
        for i in range(1, 8):
            zz.append((cx - 1.35 * u + i * .386 * u, 8.7 * u + (.25 * u if i % 2 else 0)))
        c.poly([(cx - 1.35 * u, 8.5 * u), (cx + 1.35 * u, 8.5 * u)] + zz[::-1][:0] + zz[::-1], gc)
        c.rect(cx - .7 * u, 6.2 * u, cx - .2 * u, 6.8 * u, hx('#B7956A'))  # patches
        c.rect(cx + .2 * u, 7.3 * u, cx + .75 * u, 7.9 * u, hx('#9C8A6A'))
        c.rrect(cx - 1.05 * u, 5.0 * u, cx + 1.05 * u, 5.3 * u, .1 * u, hx('#A9835A'))
    else:  # susheela - saree
        sc = SAREE.get(kind, SAREE['susheela'])
        gc = hx(sc[0])
        c.poly([(cx - 1.1 * u, 4.6 * u), (cx + 1.1 * u, 4.6 * u), (cx + 1.9 * u, 9.3 * u), (cx - 1.9 * u, 9.3 * u)], gc)
        c.poly([(cx - 1.6 * u, 8.6 * u), (cx + 1.6 * u, 8.6 * u), (cx + 1.9 * u, 9.3 * u), (cx - 1.9 * u, 9.3 * u)], hx(sc[1]))
        for k in (-.7, 0, .7):
            c.line([(cx + k * u, 5.2 * u), (cx + k * 1.35 * u, 9.0 * u)], hx(sc[2]), 2)

    # torso
    if kind in SAREE:
        sc = SAREE.get(kind, SAREE['susheela'])
        c.poly([(cx - 1.05 * u, 3.0 * u), (cx + 1.05 * u, 3.0 * u), (cx + .95 * u, 4.8 * u), (cx - .95 * u, 4.8 * u)], hx(sc[3]))
        c.poly([(cx - 1.05 * u, 3.0 * u), (cx + 1.05 * u, 3.0 * u), (cx + 1.9 * u, 6.4 * u), (cx + .9 * u, 6.4 * u)], hx(sc[4]))
        if kind == 'sita':
            c.line([(cx - .7 * u, 3.15 * u), (cx, 3.9 * u), (cx + .7 * u, 3.15 * u)], hx(GOLD), 5)
            c.ell(cx, 3.9 * u, .12 * u, .12 * u, hx('#E63946'))
    else:
        c.poly([(cx - tw / 2, 2.95 * u), (cx + tw / 2, 2.95 * u), (cx + tw * .42, 5.3 * u), (cx - tw * .42, 5.3 * u)], skin)
        c.ell(cx, 2.95 * u, tw / 2, .28 * u, skin)
    if kind == 'krishna':
        # garland (vaijayanti) + pitambar shawl
        c.line([(cx - .95 * u, 3.1 * u), (cx - .5 * u, 4.4 * u), (cx + .5 * u, 4.4 * u), (cx + .95 * u, 3.1 * u)], hx('#F8F3E8'), 5)
        for t in np.linspace(0, 1, 9):
            px = cx - .95 * u + t * 1.9 * u
            py = 3.1 * u + math.sin(t * math.pi) * 1.3 * u
            c.ell(px, py, .13 * u, .13 * u, hx('#E8507A' if int(t * 8) % 2 else '#F7D44C'))
        c.ell(cx, 4.05 * u, .1 * u, .1 * u, hx('#C0392B'))
    if kind == 'sudama':
        c.line([(cx - .75 * u, 3.1 * u), (cx + .55 * u, 5.0 * u)], hx('#F4EFE0'), 3)  # janeu
        c.poly([(cx - 1.0 * u, 3.0 * u), (cx - .15 * u, 3.1 * u), (cx - .45 * u, 5.8 * u), (cx - 1.25 * u, 5.4 * u)], hx('#D9A066'))  # shawl

    draw_arms()

    # neck + head
    c.rect(cx - .3 * u, 2.7 * u, cx + .3 * u, 3.15 * u, skin)
    hcx = cx + head_dx * u
    c.ell(hcx - head_r + .02 * u, head_cy, .17 * u, .26 * u, skin)
    c.ell(hcx + head_r - .02 * u, head_cy, .17 * u, .26 * u, skin)
    c.ell(hcx, head_cy, head_r, head_r * 1.06, skin)

    if kind == 'krishna':
        c.poly([(hcx - head_r * 1.02, head_cy - .05 * u), (hcx - head_r * 1.12, head_cy + .85 * u), (hcx - head_r * .75, head_cy + .5 * u),
                (hcx - head_r * .55, head_cy - .75 * u)], dark)
        c.poly([(hcx + head_r * 1.02, head_cy - .05 * u), (hcx + head_r * 1.12, head_cy + .85 * u), (hcx + head_r * .75, head_cy + .5 * u),
                (hcx + head_r * .55, head_cy - .75 * u)], dark)
        c.arc(hcx, head_cy - .1 * u, head_r * 1.04, head_r * 1.1, 180, 360, dark, int(.5 * u))
        c.ell(hcx, head_cy - head_r * .95, head_r * .78, head_r * .34, dark)
        # crown
        by = head_cy - head_r * 1.02
        c.poly([(hcx - .85 * u, by + .2 * u), (hcx - .85 * u, by - .15 * u), (hcx - .5 * u, by - .5 * u), (hcx - .25 * u, by - .12 * u),
                (hcx, by - .7 * u), (hcx + .25 * u, by - .12 * u), (hcx + .5 * u, by - .5 * u), (hcx + .85 * u, by - .15 * u),
                (hcx + .85 * u, by + .2 * u)], hx(GOLD))
        c.rect(hcx - .85 * u, by + .02 * u, hcx + .85 * u, by + .22 * u, hx(GOLD2))
        for k in (-.5, 0, .5):
            c.ell(hcx + k * u, by + .12 * u, .07 * u, .07 * u, hx('#E63946'))
        # mor-pankh
        c.line([(hcx + .1 * u, by - .5 * u), (hcx + .35 * u, by - 1.15 * u)], hx('#2E7D32'), 3)
        c.ell(hcx + .38 * u, by - 1.3 * u, .27 * u, .4 * u, hx('#1E8E6E'))
        c.ell(hcx + .38 * u, by - 1.3 * u, .16 * u, .26 * u, hx('#1B4F9C'))
        c.ell(hcx + .38 * u, by - 1.25 * u, .08 * u, .12 * u, hx('#F2C94C'))
    elif kind == 'sudama':
        c.arc(hcx, head_cy - .1 * u, head_r * .98, head_r * 1.0, 195, 345, hx('#5B4B3A'), int(.28 * u))
        c.ell(hcx, head_cy - head_r * 1.12, .22 * u, .26 * u, hx('#4A3A2A'))  # shikha
        # beard
        if not kid:
          c.poly([(hcx - head_r * .78, head_cy + .35 * u), (hcx + head_r * .78, head_cy + .35 * u), (hcx + .35 * u, head_cy + 1.45 * u),
                (hcx, head_cy + 1.6 * u), (hcx - .35 * u, head_cy + 1.45 * u)], hx('#D8D3C8'))
    else:
        c.ell(hcx, head_cy - .1 * u, head_r * 1.08, head_r * 1.05, hx('#2A1810'))
        c.ell(hcx, head_cy + .12 * u, head_r * .86, head_r * .9, skin)
        c.ell(hcx, head_cy - head_r * 1.2, .5 * u, .5 * u, hx('#2A1810'))  # bun
        if kind == 'sita':
            c.rect(hcx - head_r * .5, head_cy - head_r * .96, hcx + head_r * .5, head_cy - head_r * .86, hx(GOLD))
            c.line([(hcx, head_cy - head_r * .98), (hcx, head_cy - head_r * .7)], hx('#C0392B'), 3)
            for sg in (-1, 1):
                c.ell(hcx + sg * head_r * 1.0, head_cy + .35 * u, .1 * u, .14 * u, hx(GOLD))

    # face
    ey = head_cy + .02 * u
    for sgn in (-1, 1):
        ex = hcx + sgn * .38 * u
        if eyes == 'open':
            c.ell(ex, ey, .13 * u, .09 * u, hx('#FFFFFF'))
            c.ell(ex, ey, .06 * u, .08 * u, dark)
        else:
            c.arc(ex, ey, .14 * u, .1 * u, 200, 340, dark, 3)
        c.line([(ex - .17 * u, ey - .22 * u), (ex + .17 * u, ey - .27 * u)] if sgn > 0 else
               [(ex + .17 * u, ey - .22 * u), (ex - .17 * u, ey - .27 * u)], dark, 3)
    if mouth == 'smile':
        c.arc(hcx, head_cy + .42 * u, .26 * u, .16 * u, 20, 160, hx('#7A2A2A'), 4)
    elif mouth == 'open':
        c.ell(hcx, head_cy + .5 * u, .13 * u, .09 * u, hx('#7A2A2A'))
    else:
        c.line([(hcx - .12 * u, head_cy + .5 * u), (hcx + .12 * u, head_cy + .5 * u)], hx('#7A2A2A'), 3)
    # tilak / bindi
    if kind == 'krishna':
        c.line([(hcx, head_cy - .62 * u), (hcx, head_cy - .3 * u)], hx('#E63946'), 4)
    elif kind == 'sudama':
        for k in (0, 1, 2):
            c.line([(hcx - .25 * u, head_cy - .62 * u + k * .1 * u), (hcx + .25 * u, head_cy - .62 * u + k * .1 * u)], hx('#F4EFE0'), 3)
    else:
        c.ell(hcx, head_cy - .38 * u, .07 * u, .07 * u, hx('#C0392B'))
    im = c.out()
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def hug_pair(Hh=760):
    """Sudama (left) and Krishna (right) in an embrace."""
    pw = int(Hh * 1.35)
    pair = Image.new('RGBA', (pw, int(Hh * 1.16)), (0, 0, 0, 0))
    u = Hh / 10.0
    sud = person('sudama', Hh, arms=((-1.2, 4.2), (1.6, 4.5)), eyes='closed', mouth='smile')
    kri = person('krishna', Hh, arms=((-1.9, 4.2), (1.2, 4.6)), eyes='closed', mouth='smile')
    pair.alpha_composite(sud, (int(pw / 2 - sud.width / 2 - 0.95 * u), 0))
    pair.alpha_composite(kri, (int(pw / 2 - kri.width / 2 + 0.95 * u), 0))
    sa = person('sudama', Hh, arms=((-1.2, 4.2), (2.6, 4.2)), layer='arms')
    pair.alpha_composite(sa, (int(pw / 2 - sa.width / 2 - 0.95 * u), 0))
    return pair


# ---------------------------------------------------------------- backgrounds
def _vignette(cv):
    """Soft maroon vignette at edges."""
    w, h = cv.w, cv.h
    yy, xx = np.mgrid[0:h // 4, 0:w // 4]
    nx = (xx / (w / 4) - .5) * 2
    ny = (yy / (h / 4) - .5) * 2
    r = np.clip((np.maximum(abs(nx), abs(ny) * .85) - .62) / .45, 0, 1) ** 1.6
    a = (r * 105).astype(np.uint8)
    arr = np.zeros((h // 4, w // 4, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3] = 60, 8, 22, a
    ov = Image.fromarray(arr, 'RGBA').resize((w * S, h * S), Image.BILINEAR)
    cv.im.alpha_composite(ov)


def _sun(cv, x, y, r, col='#FFF6D8'):
    R = int(r * 2.6)
    yy, xx = np.mgrid[-R:R, -R:R]
    d = np.sqrt(xx ** 2 + yy ** 2) / R
    a = (np.clip(1 - d, 0, 1) ** 2.2 * 190).astype(np.uint8)
    arr = np.zeros((2 * R, 2 * R, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3] = 255, 233, 168, a
    g = Image.fromarray(arr, 'RGBA').resize((2 * R * S, 2 * R * S), Image.BILINEAR)
    cv.im.alpha_composite(g, (int((x - R) * S), int((y - R) * S)))
    cv.ell(x, y, r, r, hx(col))


def _dome(cv, cx, base, w, h, body, dome, gold=GOLD):
    cv.rect(cx - w / 2, base - h, cx + w / 2, base, body)
    r = w / 2 * .85
    cv.ell(cx, base - h, r, r * 1.05, dome)
    cv.rect(cx - r, base - h, cx + r, base - h + 4, body)
    cv.line([(cx, base - h - r * 1.0), (cx, base - h - r * 1.5)], hx(gold), 4)
    cv.ell(cx, base - h - r * 1.55, 6, 8, hx(gold))
    aw = w * .22
    cv.rect(cx - aw / 2, base - h * .55, cx + aw / 2, base, hx('#3A0C16'))
    cv.ell(cx, base - h * .55, aw / 2, aw / 2, hx('#3A0C16'))
    cv.rect(cx - w / 2, base - h * .12, cx + w / 2, base - h * .06, hx(gold))


def _hills(cv, base, col, amp, seed, n=7):
    rnd = random.Random(seed)
    pts = [(0, cv.h)]
    for i in range(n + 1):
        pts.append((i * cv.w / n, base - rnd.random() * amp))
    pts.append((cv.w, cv.h))
    cv.poly(pts, col)


def _tree(cv, x, base, h, trunk='#6B4226', leaf='#3F7D3A', leaf2='#56A04A'):
    cv.rect(x - h * .05, base - h * .55, x + h * .05, base, hx(trunk))
    cv.ell(x, base - h * .72, h * .32, h * .3, hx(leaf))
    cv.ell(x - h * .15, base - h * .62, h * .22, h * .2, hx(leaf2))
    cv.ell(x + h * .17, base - h * .68, h * .22, h * .22, hx(leaf2))


def _sparkles(cv, n, seed, y0, y1, col='#FFE9A8'):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y, r = rnd.random() * cv.w, y0 + rnd.random() * (y1 - y0), 4 + rnd.random() * 9
        cv.poly([(x, y - r * 2), (x + r * .5, y - r * .5), (x + r * 2, y), (x + r * .5, y + r * .5), (x, y + r * 2),
                 (x - r * .5, y + r * .5), (x - r * 2, y), (x - r * .5, y - r * .5)], hx(col, 200))


def bg_dwarka():
    cv = Cv(W, H)
    cv.vgrad(0, 1100, hx('#FFE7A6'), hx('#F7A94B'))
    cv.vgrad(1100, H, hx('#F7A94B'), hx('#B5532A'))
    _sun(cv, 540, 640, 230)
    _hills(cv, 1180, hx('#8C2B3A'), 80, 3)
    for x, hgt, w in ((130, 330, 200), (950, 360, 210), (330, 250, 170), (760, 270, 170)):
        _dome(cv, x, 1260, w, hgt, hx('#A63A4B'), hx('#C14B5E'))
    _dome(cv, 540, 1290, 300, 480, hx('#7A1A2C'), hx('#9C2A3E'))
    cv.rect(0, 1290, W, H, hx('#2C6F7E'))
    cv.vgrad(1290, H, hx('#2F7A8A'), hx('#173F52'))
    for i in range(14):
        y = 1330 + i * 44
        for x in range(-40 + (i % 2) * 90, W, 180):
            cv.arc(x + 70, y, 70, 14, 200, 340, hx('#BFE3E8', 110), 4)
    cv.rect(0, 1286, W, 1296, hx(GOLD))
    _sparkles(cv, 26, 5, 120, 900)
    _vignette(cv)
    return cv


def bg_ashram():
    cv = Cv(W, H)
    cv.vgrad(0, 1250, hx('#FFD9A0'), hx('#FFF0C8'))
    _sun(cv, 300, 520, 150, '#FFF3C4')
    _hills(cv, 1160, hx('#8DB36B'), 110, 11)
    _hills(cv, 1230, hx('#5F9A4F'), 70, 12)
    cv.rect(0, 1240, W, H, hx('#6EA85A'))
    cv.vgrad(1240, H, hx('#6EA85A'), hx('#3E7A3A'))
    for x, h in ((70, 520), (950, 600), (870, 430), (180, 400)):
        _tree(cv, x, 1300, h)
    # hut
    cv.rect(560, 1050, 820, 1290, hx('#C9A06C'))
    cv.poly([(520, 1060), (690, 880), (860, 1060)], hx('#B07A33'))
    for i in range(5):
        cv.line([(560 + i * 30, 1050), (690, 890)], hx('#8E5E22', 160), 3)
    cv.rect(655, 1150, 725, 1290, hx('#5A3A1A'))
    # yajna fire
    cv.rect(260, 1260, 420, 1300, hx('#7B4A22'))
    cv.poly([(285, 1262), (340, 1090), (395, 1262)], hx('#F58A1F'))
    cv.poly([(315, 1262), (340, 1150), (368, 1262)], hx('#FFD34E'))
    _sparkles(cv, 12, 7, 200, 700)
    _vignette(cv)
    return cv


def bg_hut():
    cv = Cv(W, H)
    cv.vgrad(0, 1100, hx('#2B2A5C'), hx('#E9854B'))
    cv.vgrad(1100, H, hx('#C9733B'), hx('#4B2A1A'))
    cv.ell(850, 420, 90, 90, hx('#FFF4CF'))
    cv.ell(880, 400, 80, 80, hx('#2F2D62'))
    _hills(cv, 1160, hx('#6B3A28'), 80, 21)
    # poor hut
    cv.rect(190, 840, 890, 1330, hx('#B58B58'))
    cv.poly([(110, 860), (540, 560), (970, 860)], hx('#8A5A22'))
    for i in range(14):
        cv.line([(150 + i * 60, 855), (540, 580)], hx('#5E3A12', 150), 4)
    cv.poly([(330, 730), (420, 700), (400, 790)], hx('#2B2A5C'))  # hole in thatch
    cv.rect(440, 980, 640, 1330, hx('#4A2E14'))
    cv.rect(300, 960, 400, 1060, hx('#2A1A0E'))
    cv.line([(520, 980), (520, 1330)], hx('#2E1A0A'), 4)
    # empty pot + diya
    cv.ell(740, 1290, 70, 50, hx('#8B4A2B'))
    cv.rect(690, 1215, 790, 1290, hx('#8B4A2B'))
    cv.ell(740, 1218, 50, 14, hx('#3A1D0F'))
    cv.ell(160, 1310, 38, 14, hx('#C96A1F'))
    cv.poly([(150, 1300), (160, 1250), (170, 1300)], hx('#FFD34E'))
    _sparkles(cv, 20, 4, 80, 520, '#FFFFFF')
    _vignette(cv)
    return cv


def bg_road():
    cv = Cv(W, H)
    cv.vgrad(0, 1200, hx('#FFE0A0'), hx('#FFF3D2'))
    _sun(cv, 760, 520, 170)
    _hills(cv, 1000, hx('#C79A6B'), 150, 31)
    _hills(cv, 1110, hx('#7FA85C'), 110, 32)
    cv.rect(0, 1150, W, H, hx('#6DA254'))
    cv.vgrad(1150, H, hx('#74AC5A'), hx('#3C7C3A'))
    cv.poly([(470, 1150), (610, 1150), (1180, H), (-120, H)], hx('#D8B27A'))
    cv.poly([(500, 1150), (580, 1150), (900, H), (160, H)], hx('#E6C690'))
    for x, h in ((80, 480), (200, 360), (940, 520), (840, 340)):
        _tree(cv, x, 1260, h)
    _sparkles(cv, 8, 9, 200, 700)
    _vignette(cv)
    return cv


def bg_gate():
    cv = Cv(W, H)
    cv.vgrad(0, 1170, hx('#FFE7A6'), hx('#F7A94B'))
    _sun(cv, 540, 560, 200)
    cv.rect(0, 1160, W, H, hx('#2C6F7E'))
    cv.vgrad(1160, H, hx('#2F7A8A'), hx('#173F52'))
    _dome(cv, 540, 1170, 260, 420, hx('#A63A4B'), hx('#C14B5E'))
    # gate: two pillars + arch
    for x0 in (0, 800):
        cv.rect(x0, 300, x0 + 280, 1320, hx('#EFD9A8'))
        cv.rect(x0, 300, x0 + 280, 340, hx(GOLD))
        cv.rect(x0, 1260, x0 + 280, 1320, hx(GOLD2))
        for k in range(5):
            cv.rect(x0 + 30 + k * 48, 420, x0 + 52 + k * 48, 1240, hx('#D9BE86'))
    cv.arc(540, 560, 540, 400, 180, 360, hx(GOLD), 40)
    cv.rect(0, 160, W, 330, hx('#EFD9A8'))
    cv.rect(0, 160, W, 200, hx(GOLD))
    cv.ell(540, 160, 100, 70, hx(GOLD))
    cv.line([(540, 100), (540, 40)], hx(GOLD2), 6)
    cv.poly([(540, 30), (640, 60), (540, 90)], hx('#E63946'))
    cv.rect(0, 1316, W, H, hx('#C9B38A'))
    cv.vgrad(1316, H, hx('#D9C497'), hx('#9C7E4E'))
    _sparkles(cv, 14, 6, 340, 900)
    _vignette(cv)
    return cv


def bg_throne():
    cv = Cv(W, H)
    cv.vgrad(0, H, hx('#7A1A2C'), hx('#4A0E1B'))
    cv.rect(0, 1240, W, H, hx('#3A0C16'))
    cv.vgrad(1240, H, hx('#A63A2B'), hx('#5A1A1A'))
    for x in (60, 1020):
        cv.rect(x - 60, 200, x + 60, 1340, hx(GOLD2))
        cv.rect(x - 40, 220, x + 40, 1320, hx(GOLD))
        for k in range(10):
            cv.line([(x - 36, 260 + k * 105), (x + 36, 260 + k * 105)], hx(GOLD2), 4)
    cv.arc(540, 700, 440, 520, 180, 360, hx(GOLD), 36)
    for x in (200, 540, 880):
        cv.line([(x, 120), (x, 300)], hx(GOLD2), 4)
        cv.ell(x, 330, 48, 40, hx('#F4C430'))
        cv.ell(x, 335, 26, 22, hx('#FFF2B3'))
    # divan
    cv.rrect(250, 960, 830, 1210, 30, hx('#C9892B'))
    cv.rrect(280, 840, 800, 980, 50, hx('#E6B24A'))
    cv.rrect(300, 920, 780, 1020, 30, hx('#B5262F'))
    cv.line([(280, 1210), (280, 1260)], hx(GOLD2), 12)
    cv.line([(800, 1210), (800, 1260)], hx(GOLD2), 12)
    # brass plate with water
    cv.ell(540, 1290, 200, 38, hx('#C9892B'))
    cv.ell(540, 1282, 168, 24, hx('#8FD3E0'))
    _sparkles(cv, 22, 8, 360, 900)
    _vignette(cv)
    return cv


def bg_palace():
    cv = Cv(W, H)
    cv.vgrad(0, 1300, hx('#7FC4EA'), hx('#FFF3D2'))
    for i, (x, y, r) in enumerate(((200, 260, 70), (820, 380, 90), (520, 180, 60))):
        cv.ell(x, y, r * 1.6, r * .6, hx('#FFFFFF', 220))
    cv.rect(0, 1280, W, H, hx('#6DB05A'))
    cv.vgrad(1280, H, hx('#78B85F'), hx('#3E7D3A'))
    for x, hgt, w in ((200, 380, 230), (880, 380, 230)):
        _dome(cv, x, 1290, w, hgt, hx('#F2E2BC'), hx(GOLD))
    _dome(cv, 540, 1310, 420, 620, hx('#FBEFD2'), hx(GOLD))
    cv.line([(540, 480), (540, 330)], hx(GOLD2), 7)
    cv.poly([(540, 330), (650, 365), (540, 400)], hx('#E63946'))
    for x in (100, 980):
        _tree(cv, x, 1330, 360, leaf='#2F8A3A', leaf2='#4BAA4B')
    # path
    cv.poly([(470, 1300), (610, 1300), (900, H), (180, H)], hx('#E8D3A2'))
    _sparkles(cv, 40, 12, 300, 1200, '#FFF6C0')
    _vignette(cv)
    return cv


BACKGROUNDS = {'dwarka': bg_dwarka, 'ashram': bg_ashram, 'hut': bg_hut, 'road': bg_road,
               'gate': bg_gate, 'throne': bg_throne, 'palace': bg_palace}



# ---------------------------------------------------------------- Hanuman / Ravana (added for story 002)
HSKIN = '#E8792B'; HFACE = '#F6D3A2'


def _flame(c, x, y, r, t=0.0):
    """Stylised flame centred at base (x,y), height ~2.2r."""
    k = math.sin(t * 9 + x * .05) * .18
    c.poly([(x - r, y), (x - r * .5, y - r * 1.3), (x + k * r, y - r * 2.3), (x + r * .55, y - r * 1.2), (x + r, y)], hx('#E8461E'))
    c.poly([(x - r * .62, y), (x - r * .2, y - r * 1.0), (x + k * r * .8, y - r * 1.7), (x + r * .4, y - r * .9), (x + r * .62, y)], hx('#F79A1E'))
    c.poly([(x - r * .3, y), (x, y - r * 1.05), (x + r * .3, y)], hx('#FFE45C'))


def hanuman(Hh=760, arms=None, gada=True, tail_fire=False, bound=False, jump=0.0, eyes='open',
            mouth='smile', flip=False, namaste=False, ring=False, t=0.0):
    """Flat-vector Hanuman ji. Feet at bottom centre. jump 0..1 tucks legs (leap pose)."""
    w = int(Hh * 1.25)
    pad = int(Hh * .3)
    c = Cv(w, Hh + pad)
    c.oy = pad
    u = Hh / 10.0
    cx = w / 2 - .3 * u
    skin = hx(HSKIN)
    face = hx(HFACE)
    dark = hx('#2A1208')
    tw = 2.5 * u
    if arms is None:
        arms = ((-1.7, 5.6), (1.9, 4.2))
    if namaste:
        arms = ((-.25, 4.0), (.25, 4.0))
    # tail (behind body): curl rising up on the right
    tp = [(cx + .6 * u, 5.6 * u), (cx + 2.2 * u, 6.2 * u), (cx + 3.2 * u, 5.0 * u), (cx + 3.3 * u, 3.2 * u),
          (cx + 2.8 * u, 1.9 * u), (cx + 3.4 * u, 1.0 * u)]
    c.line(tp, skin, .42 * u)
    c.line(tp[1:], hx('#C85E1C'), .14 * u)
    tip = tp[-1]
    if tail_fire:
        c.rrect(tip[0] - .32 * u, tip[1] - .1 * u, tip[0] + .32 * u, tip[1] + .5 * u, .1 * u, hx('#D9C6A0'))
        _flame(c, tip[0], tip[1] + .05 * u, .55 * u, t)
    else:
        c.ell(tip[0], tip[1], .3 * u, .3 * u, skin)
    # legs
    lift = jump * 1.6 * u
    for sgn in (-1, 1):
        fx = cx + sgn * .8 * u
        if jump > 0:
            c.line([(fx, 7.6 * u), (fx + sgn * .9 * u * jump, 8.6 * u - lift * .3), (fx, 9.6 * u - lift)], skin, .6 * u)
            c.ell(fx + sgn * .1 * u, 9.7 * u - lift, .48 * u, .22 * u, skin)
        else:
            c.rrect(fx - .32 * u, 7.6 * u, fx + .32 * u, 9.7 * u, .22 * u, skin)
            c.ell(fx + sgn * .05 * u, 9.75 * u, .5 * u, .22 * u, skin)
            c.rect(fx - .34 * u, 8.9 * u, fx + .34 * u, 9.05 * u, hx(GOLD))  # anklet
    # red langot / dhoti with gold border
    c.poly([(cx - 1.3 * u, 5.1 * u), (cx + 1.3 * u, 5.1 * u), (cx + 1.55 * u, 7.9 * u), (cx - 1.55 * u, 7.9 * u)], hx('#C8202E'))
    c.rect(cx - 1.55 * u, 7.7 * u, cx + 1.55 * u, 7.95 * u, hx(GOLD))
    c.poly([(cx - .35 * u, 5.3 * u), (cx + .35 * u, 5.3 * u), (cx + .2 * u, 8.4 * u), (cx - .2 * u, 8.4 * u)], hx('#E8A21C'))
    c.rrect(cx - 1.35 * u, 4.95 * u, cx + 1.35 * u, 5.35 * u, .1 * u, hx(GOLD))
    # torso (broad, muscular)
    c.poly([(cx - tw / 2, 2.95 * u), (cx + tw / 2, 2.95 * u), (cx + tw * .4, 5.2 * u), (cx - tw * .4, 5.2 * u)], skin)
    c.ell(cx, 3.0 * u, tw / 2, .4 * u, skin)
    c.arc(cx - .55 * u, 3.7 * u, .6 * u, .35 * u, 20, 160, hx('#C85E1C'), 3)
    c.arc(cx + .55 * u, 3.7 * u, .6 * u, .35 * u, 20, 160, hx('#C85E1C'), 3)
    # janeu + gold necklace
    c.line([(cx - 1.0 * u, 3.0 * u), (cx + .7 * u, 5.0 * u)], hx('#FFF4D6'), 3)
    c.line([(cx - .8 * u, 3.05 * u), (cx, 3.75 * u), (cx + .8 * u, 3.05 * u)], hx(GOLD), 6)
    c.ell(cx, 3.8 * u, .16 * u, .16 * u, hx('#E63946'))
    shL = (cx - tw / 2 + .15 * u, 3.25 * u)
    shR = (cx + tw / 2 - .15 * u, 3.25 * u)
    awid = .68 * u
    hL = (cx + arms[0][0] * u, arms[0][1] * u)
    hR = (cx + arms[1][0] * u, arms[1][1] * u)
    if gada and not namaste and not bound:
        # mace held in right hand, resting on shoulder
        gx, gy = hR
        c.line([(gx, gy + .9 * u), (gx + .9 * u, gy - 1.6 * u)], hx('#B8860B'), .26 * u)
        hdx, hdy = gx + 1.05 * u, gy - 2.1 * u
        c.ell(hdx, hdy, .78 * u, .82 * u, hx(GOLD2))
        c.ell(hdx - .15 * u, hdy - .2 * u, .55 * u, .6 * u, hx(GOLD))
        for k in (-1, 0, 1):
            c.line([(hdx - .7 * u, hdy + k * .32 * u), (hdx + .7 * u, hdy + k * .32 * u)], hx('#A0700E'), 3)
        c.poly([(hdx - .14 * u, hdy - .8 * u), (hdx, hdy - 1.25 * u), (hdx + .14 * u, hdy - .8 * u)], hx(GOLD))
    for sh, hd in ((shL, hL), (shR, hR)):
        _arm(c, sh, hd, skin, awid, 1)
        c.rect(sh[0] + (hd[0] - sh[0]) * .82 - .3 * u, sh[1] + (hd[1] - sh[1]) * .82 - .12 * u,
               sh[0] + (hd[0] - sh[0]) * .82 + .3 * u, sh[1] + (hd[1] - sh[1]) * .82 + .12 * u, hx(GOLD))
    if ring:
        c.ell(hL[0], hL[1] - .55 * u, .3 * u, .3 * u, None, hx('#FFD34E'), 5)
        c.ell(hL[0], hL[1] - .85 * u, .12 * u, .12 * u, hx('#7FD3FF'))
    if bound:
        for k in range(4):
            y = 3.6 * u + k * .55 * u
            c.line([(cx - tw * .6, y), (cx + tw * .6, y + .25 * u)], hx('#E9D9A8'), 6)
            c.line([(cx - tw * .6, y), (cx + tw * .6, y + .25 * u)], hx('#FFF6C0', 140), 2)
    # neck + head
    c.rect(cx - .35 * u, 2.6 * u, cx + .35 * u, 3.15 * u, skin)
    hcx, hcy, hr = cx, 1.95 * u, 1.0 * u
    for sg in (-1, 1):
        c.ell(hcx + sg * hr * 1.0, hcy + .05 * u, .26 * u, .32 * u, skin)
        c.ell(hcx + sg * hr * 1.0, hcy + .05 * u, .14 * u, .18 * u, face)
        c.ell(hcx + sg * hr * 1.02, hcy + .38 * u, .09 * u, .12 * u, hx(GOLD))  # kundal
    c.ell(hcx, hcy, hr, hr * 1.04, skin)
    # face plate (lighter) + muzzle
    c.ell(hcx, hcy + .1 * u, hr * .78, hr * .7, face)
    c.ell(hcx, hcy + .55 * u, hr * .62, hr * .42, face)
    c.ell(hcx, hcy + .32 * u, .14 * u, .08 * u, hx('#7A3A1A'))  # nose
    # eyes / brows
    ey = hcy - .05 * u
    for sg in (-1, 1):
        ex = hcx + sg * .35 * u
        if eyes == 'open':
            c.ell(ex, ey, .13 * u, .1 * u, hx('#FFFFFF'))
            c.ell(ex, ey, .065 * u, .085 * u, dark)
        else:
            c.arc(ex, ey, .14 * u, .1 * u, 200, 340, dark, 3)
        c.line([(ex - sg * .18 * u, ey - .2 * u), (ex + sg * .16 * u, ey - .27 * u)], dark, 3)
    if mouth == 'smile':
        c.arc(hcx, hcy + .55 * u, .3 * u, .17 * u, 15, 165, hx('#7A2A2A'), 4)
    elif mouth == 'open':
        c.ell(hcx, hcy + .66 * u, .17 * u, .12 * u, hx('#7A2A2A'))
    else:
        c.line([(hcx - .16 * u, hcy + .66 * u), (hcx + .16 * u, hcy + .66 * u)], hx('#7A2A2A'), 3)
    # tilak (sindoor U)
    c.line([(hcx, hcy - .62 * u), (hcx, hcy - .28 * u)], hx('#E63946'), 5)
    # mukut
    by = hcy - hr * .82
    c.poly([(hcx - .9 * u, by + .15 * u), (hcx - .9 * u, by - .35 * u), (hcx - .55 * u, by - .7 * u), (hcx - .3 * u, by - .35 * u),
            (hcx, by - 1.15 * u), (hcx + .3 * u, by - .35 * u), (hcx + .55 * u, by - .7 * u), (hcx + .9 * u, by - .35 * u),
            (hcx + .9 * u, by + .15 * u)], hx(GOLD))
    c.rect(hcx - .92 * u, by - .05 * u, hcx + .92 * u, by + .18 * u, hx(GOLD2))
    for k in (-.55, 0, .55):
        c.ell(hcx + k * u, by + .06 * u, .08 * u, .08 * u, hx('#E63946'))
    c.ell(hcx, by - .55 * u, .13 * u, .13 * u, hx('#2E9E6E'))
    im = c.out()
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def ravana(Hh=760, angry=False, point=False, seated=False):
    """Crowned Lanka king with five visible heads (centre + 2 each side)."""
    w = int(Hh * 1.5)
    pad = int(Hh * .2)
    c = Cv(w, Hh + pad)
    c.oy = pad
    u = Hh / 10.0
    cx = w / 2
    skin = hx('#9C5B3B')
    dark = hx('#1E0E08')
    tw = 2.7 * u
    # legs + dhoti
    for sg in (-1, 1):
        fx = cx + sg * .8 * u
        c.rrect(fx - .34 * u, 8.0 * u, fx + .34 * u, 9.7 * u, .2 * u, skin)
        c.ell(fx, 9.75 * u, .5 * u, .22 * u, hx('#3A1A0A'))
    c.poly([(cx - 1.45 * u, 5.0 * u), (cx + 1.45 * u, 5.0 * u), (cx + 1.9 * u, 8.9 * u), (cx - 1.9 * u, 8.9 * u)], hx('#2B1B4F'))
    c.rect(cx - 1.9 * u, 8.6 * u, cx + 1.9 * u, 8.9 * u, hx(GOLD))
    # torso with gold armour
    c.poly([(cx - tw / 2, 2.95 * u), (cx + tw / 2, 2.95 * u), (cx + tw * .42, 5.3 * u), (cx - tw * .42, 5.3 * u)], skin)
    c.poly([(cx - tw * .45, 3.3 * u), (cx + tw * .45, 3.3 * u), (cx + tw * .4, 5.2 * u), (cx - tw * .4, 5.2 * u)], hx(GOLD2))
    c.poly([(cx - tw * .38, 3.5 * u), (cx + tw * .38, 3.5 * u), (cx + tw * .33, 5.0 * u), (cx - tw * .33, 5.0 * u)], hx(GOLD))
    c.ell(cx, 4.2 * u, .3 * u, .3 * u, hx('#B5262F'))
    c.rrect(cx - 1.5 * u, 4.95 * u, cx + 1.5 * u, 5.3 * u, .1 * u, hx('#B5262F'))
    # cape
    c.poly([(cx - tw / 2 - .2 * u, 3.0 * u), (cx - tw / 2 - 1.0 * u, 8.6 * u), (cx - tw / 2 + .3 * u, 8.4 * u)], hx('#7A1A2C'))
    c.poly([(cx + tw / 2 + .2 * u, 3.0 * u), (cx + tw / 2 + 1.0 * u, 8.6 * u), (cx + tw / 2 - .3 * u, 8.4 * u)], hx('#7A1A2C'))
    shL = (cx - tw / 2 + .2 * u, 3.3 * u)
    shR = (cx + tw / 2 - .2 * u, 3.3 * u)
    _arm(c, shL, (cx - 1.8 * u, 5.6 * u), skin, .62 * u, -1)
    _arm(c, shR, (cx + 3.3 * u, 2.9 * u) if point else (cx + 1.8 * u, 5.6 * u), skin, .62 * u, 1)
    c.rect(cx - .35 * u, 2.6 * u, cx + .35 * u, 3.15 * u, skin)

    def head(hcx, hcy, r, main):
        c.ell(hcx, hcy, r, r * 1.05, skin)
        ey = hcy
        for sg in (-1, 1):
            ex = hcx + sg * .38 * r / .95
            c.ell(ex, ey, .14 * r, .09 * r, hx('#FFFFFF'))
            c.ell(ex, ey, .06 * r, .08 * r, dark)
            if angry:
                c.line([(ex - sg * .2 * r, ey - .3 * r), (ex + sg * .18 * r, ey - .16 * r)], dark, 4 if main else 3)
            else:
                c.line([(ex - .18 * r, ey - .25 * r), (ex + .18 * r, ey - .25 * r)], dark, 3)
        # moustache
        c.poly([(hcx, hcy + .35 * r), (hcx - .55 * r, hcy + .5 * r), (hcx - .7 * r, hcy + .3 * r), (hcx - .35 * r, hcy + .38 * r)], dark)
        c.poly([(hcx, hcy + .35 * r), (hcx + .55 * r, hcy + .5 * r), (hcx + .7 * r, hcy + .3 * r), (hcx + .35 * r, hcy + .38 * r)], dark)
        if angry and main:
            c.ell(hcx, hcy + .66 * r, .16 * r, .1 * r, hx('#5A1A1A'))
        else:
            c.line([(hcx - .14 * r, hcy + .66 * r), (hcx + .14 * r, hcy + .66 * r)], hx('#5A1A1A'), 3)
        c.line([(hcx - .25 * r, hcy - .6 * r), (hcx + .25 * r, hcy - .6 * r)], hx('#F4EFE0'), 3)
        by = hcy - r * .85
        c.poly([(hcx - .8 * r, by + .15 * r), (hcx - .8 * r, by - .5 * r), (hcx - .4 * r, by - .9 * r), (hcx, by - 1.35 * r),
                (hcx + .4 * r, by - .9 * r), (hcx + .8 * r, by - .5 * r), (hcx + .8 * r, by + .15 * r)], hx(GOLD))
        c.rect(hcx - .82 * r, by - .05 * r, hcx + .82 * r, by + .16 * r, hx(GOLD2))
        c.ell(hcx, by - .45 * r, .13 * r, .13 * r, hx('#E63946'))

    hcy = 1.95 * u
    for k, (dx, sc) in enumerate(((-2.6, .72), (2.6, .72), (-1.45, .84), (1.45, .84))):
        head(cx + dx * u, hcy + .15 * u, .95 * u * sc, False)
    head(cx, hcy, .98 * u, True)
    return c.out()


def _lanka_city(cv, base, gold=True, seed=41):
    rnd = random.Random(seed)
    xs = [(60, 230, 150), (220, 320, 190), (420, 260, 160), (660, 300, 200), (870, 360, 220), (1020, 220, 150)]
    for x, h, w in xs:
        _dome(cv, x, base, w, h, hx('#C98A1B' if gold else '#6B3A1A'), hx('#E8B84A' if gold else '#8A4A20'), gold='#FFE08A')
        for k in range(3):
            wy = base - h * (.2 + k * .25)
            cv.rect(x - w * .3, wy, x - w * .18, wy + 22, hx('#FFE9A0', 220))
            cv.rect(x + w * .18, wy, x + w * .3, wy + 22, hx('#FFE9A0', 220))


def bg_lanka():
    """Golden Lanka on Trikuta hills at dusk, across the sea."""
    cv = Cv(W, H)
    cv.vgrad(0, 1150, hx('#3B1D5A'), hx('#F2994A'))
    _sun(cv, 820, 860, 120, '#FFE2A0')
    _hills(cv, 1050, hx('#5C2A3E'), 160, 44)
    _lanka_city(cv, 1120)
    cv.rect(0, 1150, W, H, hx('#1F4E6B'))
    cv.vgrad(1150, H, hx('#2F6F8A'), hx('#102A3E'))
    for i in range(14):
        y = 1190 + i * 48
        for x in range(-40 + (i % 2) * 90, W, 180):
            cv.arc(x + 70, y, 70, 14, 200, 340, hx('#BFE3E8', 100), 4)
    cv.rect(0, 1146, W, 1156, hx(GOLD))
    _sparkles(cv, 22, 42, 100, 700, '#FFFFFF')
    _vignette(cv)
    return cv


def bg_vatika():
    """Ashok Vatika: night garden, ashoka tree, moon."""
    cv = Cv(W, H)
    cv.vgrad(0, 1200, hx('#14234A'), hx('#3E5C7A'))
    cv.ell(260, 420, 95, 95, hx('#FFF4CF'))
    _sun(cv, 260, 420, 60, '#FFF8E0')
    _hills(cv, 1150, hx('#1E3A2E'), 90, 51)
    cv.rect(0, 1220, W, H, hx('#2F5A34'))
    cv.vgrad(1220, H, hx('#3F7A3E'), hx('#1E3A22'))
    # big ashoka tree on the right
    cv.rect(850, 520, 930, 1300, hx('#4A2E1A'))
    for (x, y, r, col) in ((890, 470, 260, '#1F5A2E'), (760, 560, 170, '#2B7A3A'), (1010, 580, 170, '#2B7A3A'),
                           (880, 360, 170, '#3A8A44')):
        cv.ell(x, y, r, r * .85, hx(col))
    rnd = random.Random(5)
    for _ in range(40):  # red ashoka flowers
        x, y = 650 + rnd.random() * 450, 260 + rnd.random() * 460
        cv.ell(x, y, 10, 10, hx('#E8462E'))
    for x, h in ((90, 380), (220, 300)):
        _tree(cv, x, 1260, h, leaf='#1F5A2E', leaf2='#2B7A3A')
    _sparkles(cv, 26, 52, 80, 900, '#FFFFFF')
    _vignette(cv)
    return cv


def bg_court():
    """Ravana's dark-gold court."""
    cv = Cv(W, H)
    cv.vgrad(0, H, hx('#2A0E2E'), hx('#12060F'))
    cv.rect(0, 1260, W, H, hx('#2A0A12'))
    cv.vgrad(1260, H, hx('#5A1A22'), hx('#1A0608'))
    for x in (80, 1000):
        cv.rect(x - 70, 160, x + 70, 1300, hx('#6B4A12'))
        cv.rect(x - 50, 180, x + 50, 1280, hx(GOLD2))
        for k in range(10):
            cv.line([(x - 46, 240 + k * 105), (x + 46, 240 + k * 105)], hx('#6B4A12'), 5)
    cv.arc(540, 760, 420, 560, 180, 360, hx(GOLD2), 30)
    # throne back
    cv.rrect(330, 560, 750, 1180, 80, hx('#7A1A2C'))
    cv.rrect(360, 590, 720, 1150, 60, hx('#B5262F'))
    cv.ell(540, 560, 150, 90, hx(GOLD))
    for x in (230, 850):  # torches
        cv.rect(x - 14, 820, x + 14, 1050, hx('#5A3A1A'))
        cv.ell(x, 820, 40, 14, hx(GOLD2))
        cv.poly([(x - 34, 818), (x - 16, 760), (x, 700), (x + 18, 760), (x + 34, 818)], hx('#F2671F'))
        cv.poly([(x - 18, 818), (x, 745), (x + 18, 818)], hx('#FFD34E'))
        _sun(cv, x, 770, 1, '#F79A1E')
    _sparkles(cv, 14, 61, 200, 900, '#FFD08A')
    _vignette(cv)
    return cv


def bg_fire():
    """Lanka at night, sky glowing (flames drawn per-frame on top)."""
    cv = Cv(W, H)
    cv.vgrad(0, 1250, hx('#1A0610'), hx('#C2401A'))
    _hills(cv, 1100, hx('#2A0C14'), 140, 71)
    _lanka_city(cv, 1300, gold=True, seed=72)
    cv.rect(0, 1300, W, H, hx('#3A1408'))
    cv.vgrad(1300, H, hx('#5A2410'), hx('#1A0806'))
    _vignette(cv)
    return cv


def bg_sea():
    """Dawn sea with distant shore; Hanuman returns."""
    cv = Cv(W, H)
    cv.vgrad(0, 1150, hx('#FFD9A0'), hx('#FF9E6B'))
    _sun(cv, 540, 980, 170, '#FFF1C8')
    cv.rect(0, 1100, W, H, hx('#2C6F7E'))
    cv.vgrad(1100, H, hx('#3C8EA0'), hx('#173F52'))
    for i in range(16):
        y = 1140 + i * 46
        for x in range(-40 + (i % 2) * 90, W, 180):
            cv.arc(x + 70, y, 70, 14, 200, 340, hx('#E9F6F8', 120), 4)
    cv.rect(0, 1096, W, 1104, hx(GOLD))
    cv.poly([(0, 1100), (0, 1072), (190, 1054), (420, 1078), (700, 1050), (1080, 1074), (1080, 1100)], hx('#B5625A'))
    cv.rect(0, 1100, W, 1104, hx('#E9C38A'))
    for i, (x, y, r) in enumerate(((200, 300, 70), (820, 420, 90))):
        cv.ell(x, y, r * 1.6, r * .6, hx('#FFFFFF', 200))
    _sparkles(cv, 18, 82, 200, 900)
    _vignette(cv)
    return cv


def bg_ramdarbar():
    """Soft golden glow halo backdrop for the closing message."""
    cv = Cv(W, H)
    cv.vgrad(0, H, hx('#FFE8B0'), hx('#E07A2A'))
    _sun(cv, 540, 820, 330, '#FFF6DA')
    for k in range(24):
        a = k / 24 * 2 * math.pi
        cv.line([(540 + math.cos(a) * 380, 820 + math.sin(a) * 380), (540 + math.cos(a) * 620, 820 + math.sin(a) * 620)], hx('#FFF1C8', 120), 10)
    _hills(cv, 1330, hx('#B5532A'), 60, 91)
    cv.rect(0, 1330, W, H, hx('#8C2B3A'))
    cv.vgrad(1330, H, hx('#A63A4B'), hx('#4A0E1B'))
    _sparkles(cv, 30, 92, 150, 1200, '#FFF6C0')
    _vignette(cv)
    return cv


BACKGROUNDS.update({'lanka': bg_lanka, 'vatika': bg_vatika, 'court': bg_court, 'fire': bg_fire, 'sea': bg_sea,
                    'glow': bg_ramdarbar})

# ---------------------------------------------------------------- logo
def make_logo(path='logo.png', width=640):
    """Golden diya + lotus badge with THE MEET MORE, transparent PNG."""
    s = width / 640.0
    cv = Cv(640, 250)
    # badge circle
    cv.ell(110, 125, 100, 100, hx(MAROON))
    cv.ell(110, 125, 100, 100, None, hx(GOLD), 6)
    cv.ell(110, 125, 88, 88, None, hx(GOLD2, 160), 2)
    # lotus petals
    for ang, col in ((-60, GOLD2), (60, GOLD2), (-30, GOLD), (30, GOLD), (0, '#FFE08A')):
        a = math.radians(ang)
        px, py = 110 + math.sin(a) * 40, 150 - math.cos(a) * 12
        pts = [(110, 160), (110 + math.sin(a) * 64 - 16, 160 - math.cos(a) * 62), (px + math.sin(a) * 4, 160 - math.cos(a) * 70),
               (110 + math.sin(a) * 64 + 16, 160 - math.cos(a) * 62)]
        cv.poly(pts, hx(col))
    # diya
    cv.poly([(62, 160), (158, 160), (138, 188), (82, 188)], hx(GOLD))
    cv.rect(62, 156, 158, 164, hx('#FFE08A'))
    # flame
    cv.poly([(110, 78), (127, 112), (110, 126), (93, 112)], hx('#FFB02E'))
    cv.poly([(110, 94), (119, 114), (110, 124), (101, 114)], hx('#FFF2A8'))
    im = cv.out()
    d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(FONT, 58)
    f2 = ImageFont.truetype(FONT, 30)
    d.text((232, 62), 'THE MEET', font=f1, fill=hx(GOLD), stroke_width=3, stroke_fill=hx(MAROON, 230))
    d.text((232, 124), 'MORE', font=f1, fill=hx(GOLD), stroke_width=3, stroke_fill=hx(MAROON, 230))
    d.text((234, 192), 'BHAKTI SHORTS', font=f2, fill=hx(CREAM), stroke_width=2, stroke_fill=hx(MAROON, 230))
    bbox = im.getbbox()
    im = im.crop(bbox)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    im.save(path)
    return im


if __name__ == '__main__':
    make_logo('logo.png')
