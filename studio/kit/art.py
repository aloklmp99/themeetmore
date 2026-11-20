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
SKIN = {'krishna': '#4A86D6', 'sudama': '#B87B4F', 'susheela': '#C48A5C', 'sita': '#E2A574',
        'vishnu': '#3F7FD0', 'vrinda': '#E0A270', 'lakshmi': '#EDB283',
        'shiva': '#9FB8D6', 'parvati': '#EBAA7C', 'kartikeya': '#E3A06C'}
SAREE = {'susheela': ('#D9772B', '#9B3B1E', '#B8601F', '#7C2D12', '#F2A33C'),
         'sita': ('#C8202E', '#F2B632', '#9E1622', '#E8A21C', '#F7C948'),
         'vrinda': ('#2E8B57', '#E8B84A', '#1F6B42', '#C98A1B', '#F2C94C'),
         'lakshmi': ('#D6336C', '#F2B632', '#A61E4D', '#E8A21C', '#F7C948'),
         'parvati': ('#C8163E', '#F2B632', '#8E1030', '#2E8B57', '#F7C948')}
JEWEL = ('sita', 'vrinda', 'lakshmi', 'parvati')


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
        if kind in ('krishna', 'vishnu', 'deva', 'raja') and not namaste:
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
    if kind in ('krishna', 'vishnu', 'deva', 'raja'):
        gc, gd = (hx('#E0662A'), hx('#B04A18')) if kind == 'raja' else (hx(PITAM), hx('#D9A41A'))
        c.poly([(cx - 1.25 * u, 5.1 * u), (cx + 1.25 * u, 5.1 * u), (cx + 1.7 * u, 9.1 * u), (cx - 1.7 * u, 9.1 * u)], gc)
        for k in (-.8, -.3, .3, .8):
            c.line([(cx + k * u * .8, 5.4 * u), (cx + k * u * 1.15, 9.0 * u)], gd, 2)
        c.rrect(cx - 1.3 * u, 5.0 * u, cx + 1.3 * u, 5.4 * u, .1 * u, hx('#C0392B'))
    elif kind == 'shiva':  # tiger-skin
        c.poly([(cx - 1.25 * u, 5.1 * u), (cx + 1.25 * u, 5.1 * u), (cx + 1.6 * u, 8.5 * u), (cx - 1.6 * u, 8.5 * u)], hx('#E89A3C'))
        for k in range(6):
            yy = 5.6 * u + k * .5 * u
            c.line([(cx - 1.2 * u + (k % 2) * .4 * u, yy), (cx - .6 * u + (k % 2) * .4 * u, yy + .18 * u)], hx('#3A2010'), 4)
            c.line([(cx + .5 * u - (k % 2) * .3 * u, yy + .1 * u), (cx + 1.1 * u - (k % 2) * .3 * u, yy - .05 * u)], hx('#3A2010'), 4)
        c.rrect(cx - 1.3 * u, 5.0 * u, cx + 1.3 * u, 5.35 * u, .1 * u, hx('#6B4226'))
    elif kind == 'kartikeya':
        c.poly([(cx - 1.25 * u, 5.1 * u), (cx + 1.25 * u, 5.1 * u), (cx + 1.6 * u, 9.0 * u), (cx - 1.6 * u, 9.0 * u)], hx('#D9452B'))
        for k in (-.8, 0, .8):
            c.line([(cx + k * u * .8, 5.4 * u), (cx + k * u * 1.1, 8.9 * u)], hx('#A8321E'), 2)
        c.rect(cx - 1.55 * u, 8.55 * u, cx + 1.55 * u, 8.75 * u, hx(GOLD))
        c.rrect(cx - 1.3 * u, 5.0 * u, cx + 1.3 * u, 5.4 * u, .1 * u, hx(GOLD))
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
        if kind in JEWEL:
            c.line([(cx - .7 * u, 3.15 * u), (cx, 3.9 * u), (cx + .7 * u, 3.15 * u)], hx(GOLD), 5)
            c.ell(cx, 3.9 * u, .12 * u, .12 * u, hx('#E63946'))
    else:
        c.poly([(cx - tw / 2, 2.95 * u), (cx + tw / 2, 2.95 * u), (cx + tw * .42, 5.3 * u), (cx - tw * .42, 5.3 * u)], skin)
        c.ell(cx, 2.95 * u, tw / 2, .28 * u, skin)
    if kind in ('krishna', 'vishnu', 'deva', 'raja'):
        # garland (vaijayanti) + pitambar shawl
        c.line([(cx - .95 * u, 3.1 * u), (cx - .5 * u, 4.4 * u), (cx + .5 * u, 4.4 * u), (cx + .95 * u, 3.1 * u)], hx('#F8F3E8'), 5)
        for t in np.linspace(0, 1, 9):
            px = cx - .95 * u + t * 1.9 * u
            py = 3.1 * u + math.sin(t * math.pi) * 1.3 * u
            c.ell(px, py, .13 * u, .13 * u, hx('#E8507A' if int(t * 8) % 2 else '#F7D44C'))
        c.ell(cx, 4.05 * u, .1 * u, .1 * u, hx('#C0392B'))
    if kind == 'shiva':
        for t in np.linspace(0, 1, 11):  # rudraksha mala
            c.ell(cx - .9 * u + t * 1.8 * u, 3.1 * u + math.sin(t * math.pi) * 1.4 * u, .1 * u, .1 * u, hx('#6B3A1E'))
        # serpent around the neck
        c.arc(cx, 2.95 * u, .95 * u, .45 * u, 0, 180, hx('#2E7D4F'), int(.22 * u))
        c.ell(cx + .95 * u, 2.75 * u, .2 * u, .14 * u, hx('#2E7D4F'))
        c.ell(cx + 1.0 * u, 2.72 * u, .04 * u, .04 * u, hx('#FFE45C'))
    if kind == 'kartikeya':
        c.line([(cx - .7 * u, 3.15 * u), (cx, 3.95 * u), (cx + .7 * u, 3.15 * u)], hx(GOLD), 6)
        c.ell(cx, 3.95 * u, .13 * u, .13 * u, hx('#E63946'))
        c.line([(cx - 1.0 * u, 3.0 * u), (cx + .9 * u, 5.0 * u)], hx('#F2B632'), 7)  # sash
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

    if kind in ('krishna', 'vishnu', 'deva', 'raja'):
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
        # mor-pankh (Krishna only; Vishnu gets a tall kirit)
        if kind in ('vishnu', 'deva', 'raja'):
            c.poly([(hcx - .55 * u, by - .1 * u), (hcx - .35 * u, by - 1.15 * u), (hcx, by - 1.55 * u), (hcx + .35 * u, by - 1.15 * u),
                    (hcx + .55 * u, by - .1 * u)], hx(GOLD))
            c.ell(hcx, by - .7 * u, .14 * u, .14 * u, hx('#E63946'))
            c.ell(hcx, by - 1.2 * u, .08 * u, .08 * u, hx('#2E8B57'))
        else:
            c.line([(hcx + .1 * u, by - .5 * u), (hcx + .35 * u, by - 1.15 * u)], hx('#2E7D32'), 3)
            c.ell(hcx + .38 * u, by - 1.3 * u, .27 * u, .4 * u, hx('#1E8E6E'))
            c.ell(hcx + .38 * u, by - 1.3 * u, .16 * u, .26 * u, hx('#1B4F9C'))
            c.ell(hcx + .38 * u, by - 1.25 * u, .08 * u, .12 * u, hx('#F2C94C'))
    elif kind == 'shiva':
        jc = hx('#3A2618')
        c.arc(hcx, head_cy - .1 * u, head_r * 1.04, head_r * 1.1, 180, 360, jc, int(.5 * u))
        for sg in (-1, 1):  # locks on shoulders
            c.poly([(hcx + sg * head_r * 1.0, head_cy - .2 * u), (hcx + sg * head_r * 1.35, head_cy + 1.3 * u),
                    (hcx + sg * head_r * .95, head_cy + 1.1 * u), (hcx + sg * head_r * .7, head_cy - .5 * u)], jc)
        c.ell(hcx, head_cy - head_r * 1.35, .62 * u, .75 * u, jc)  # jata bun
        c.ell(hcx, head_cy - head_r * 1.0, .75 * u, .3 * u, jc)
        for k in (-1, 0, 1):
            c.arc(hcx + k * .25 * u, head_cy - head_r * 1.4, .3 * u, .5 * u, 200, 340, hx('#5A3E2A'), 3)
        c.ell(hcx + .25 * u, head_cy - head_r * 1.95, .35 * u, .35 * u, hx('#FFF6D8'))  # crescent moon
        c.ell(hcx + .38 * u, head_cy - head_r * 2.02, .3 * u, .3 * u, jc)
    elif kind == 'kartikeya':
        dk = hx('#2A1208')
        c.arc(hcx, head_cy - .1 * u, head_r * 1.04, head_r * 1.1, 180, 360, dk, int(.5 * u))
        for sg in (-1, 1):
            c.poly([(hcx + sg * head_r * 1.02, head_cy - .05 * u), (hcx + sg * head_r * 1.1, head_cy + .8 * u),
                    (hcx + sg * head_r * .75, head_cy + .5 * u), (hcx + sg * head_r * .55, head_cy - .75 * u)], dk)
        by = head_cy - head_r * 1.02
        c.poly([(hcx - .8 * u, by + .2 * u), (hcx - .7 * u, by - .45 * u), (hcx - .35 * u, by - .2 * u), (hcx, by - .85 * u),
                (hcx + .35 * u, by - .2 * u), (hcx + .7 * u, by - .45 * u), (hcx + .8 * u, by + .2 * u)], hx(GOLD))
        c.rect(hcx - .82 * u, by + .02 * u, hcx + .82 * u, by + .22 * u, hx(GOLD2))
        c.ell(hcx, by - .25 * u, .1 * u, .1 * u, hx('#E63946'))
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
        if kind in ('lakshmi', 'parvati'):
            by = head_cy - head_r * 1.0
            c.poly([(hcx - .7 * u, by + .15 * u), (hcx - .6 * u, by - .35 * u), (hcx - .3 * u, by - .1 * u), (hcx, by - .6 * u),
                    (hcx + .3 * u, by - .1 * u), (hcx + .6 * u, by - .35 * u), (hcx + .7 * u, by + .15 * u)], hx(GOLD))
            c.ell(hcx, by - .15 * u, .08 * u, .08 * u, hx('#E63946'))
        if kind in JEWEL:
            c.rect(hcx - head_r * .5, head_cy - head_r * .96, hcx + head_r * .5, head_cy - head_r * .86, hx(GOLD))
            c.line([(hcx, head_cy - head_r * .98), (hcx, head_cy - head_r * .7)], hx('#C0392B'), 3)
            for sg in (-1, 1):
                c.ell(hcx + sg * head_r * 1.0, head_cy + .35 * u, .1 * u, .14 * u, hx(GOLD))

    if kind == 'raja':
        c.poly([(hcx - head_r * .8, head_cy + .3 * u), (hcx + head_r * .8, head_cy + .3 * u), (hcx + .4 * u, head_cy + 1.35 * u),
                (hcx, head_cy + 1.5 * u), (hcx - .4 * u, head_cy + 1.35 * u)], hx('#3A2618'))
        c.ell(hcx, head_cy + .5 * u, .3 * u, .14 * u, skin)
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
    if kind in ('krishna', 'vishnu', 'deva', 'raja'):
        c.line([(hcx, head_cy - .62 * u), (hcx, head_cy - .3 * u)], hx('#E63946'), 4)
    elif kind == 'shiva':
        for k in (0, 1, 2):
            c.line([(hcx - .3 * u, head_cy - .66 * u + k * .1 * u), (hcx + .3 * u, head_cy - .66 * u + k * .1 * u)], hx('#FFFFFF'), 3)
        c.ell(hcx, head_cy - .56 * u, .06 * u, .06 * u, hx('#E63946'))
    elif kind == 'kartikeya':
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


def ravana(Hh=760, angry=False, point=False, seated=False, heads=5, skin_col='#9C5B3B', dhoti='#2B1B4F', cape='#7A1A2C'):
    """Crowned Lanka king with five visible heads (centre + 2 each side)."""
    w = int(Hh * 1.5)
    pad = int(Hh * .2)
    c = Cv(w, Hh + pad)
    c.oy = pad
    u = Hh / 10.0
    cx = w / 2
    skin = hx(skin_col)
    dark = hx('#1E0E08')
    tw = 2.7 * u
    # legs + dhoti
    for sg in (-1, 1):
        fx = cx + sg * .8 * u
        c.rrect(fx - .34 * u, 8.0 * u, fx + .34 * u, 9.7 * u, .2 * u, skin)
        c.ell(fx, 9.75 * u, .5 * u, .22 * u, hx('#3A1A0A'))
    c.poly([(cx - 1.45 * u, 5.0 * u), (cx + 1.45 * u, 5.0 * u), (cx + 1.9 * u, 8.9 * u), (cx - 1.9 * u, 8.9 * u)], hx(dhoti))
    c.rect(cx - 1.9 * u, 8.6 * u, cx + 1.9 * u, 8.9 * u, hx(GOLD))
    # torso with gold armour
    c.poly([(cx - tw / 2, 2.95 * u), (cx + tw / 2, 2.95 * u), (cx + tw * .42, 5.3 * u), (cx - tw * .42, 5.3 * u)], skin)
    c.poly([(cx - tw * .45, 3.3 * u), (cx + tw * .45, 3.3 * u), (cx + tw * .4, 5.2 * u), (cx - tw * .4, 5.2 * u)], hx(GOLD2))
    c.poly([(cx - tw * .38, 3.5 * u), (cx + tw * .38, 3.5 * u), (cx + tw * .33, 5.0 * u), (cx - tw * .33, 5.0 * u)], hx(GOLD))
    c.ell(cx, 4.2 * u, .3 * u, .3 * u, hx('#B5262F'))
    c.rrect(cx - 1.5 * u, 4.95 * u, cx + 1.5 * u, 5.3 * u, .1 * u, hx('#B5262F'))
    # cape
    c.poly([(cx - tw / 2 - .2 * u, 3.0 * u), (cx - tw / 2 - 1.0 * u, 8.6 * u), (cx - tw / 2 + .3 * u, 8.4 * u)], hx(cape))
    c.poly([(cx + tw / 2 + .2 * u, 3.0 * u), (cx + tw / 2 + 1.0 * u, 8.6 * u), (cx + tw / 2 - .3 * u, 8.4 * u)], hx(cape))
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
    side = ((-2.6, .72), (2.6, .72), (-1.45, .84), (1.45, .84)) if heads == 5 else ()
    for k, (dx, sc) in enumerate(side):
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

# ---------------------------------------------------------------- Tulsi Vivah (added for story 003)
def jalandhar(Hh=760, angry=False, point=False):
    """Asura king Jalandhar: single crowned head, dark-teal armour look."""
    return ravana(Hh, angry=angry, point=point, heads=1, skin_col='#7E5A44', dhoti='#123E3A', cape='#3B1650')


def chakra_img(r=60, t=0.0):
    cv = Cv(int(r * 2.6), int(r * 2.6))
    c = r * 1.3
    cv.ell(c, c, r * 1.15, r * 1.15, hx('#FFE9A0', 90))
    cv.ell(c, c, r, r, hx(GOLD))
    cv.ell(c, c, r * .72, r * .72, hx('#FFF2B3'))
    for k in range(12):
        a = t * 4 + k * math.pi / 6
        cv.line([(c + math.cos(a) * r * .25, c + math.sin(a) * r * .25), (c + math.cos(a) * r * .72, c + math.sin(a) * r * .72)], hx(GOLD2), max(2, r * .07))
        tx, ty = c + math.cos(a) * r, c + math.sin(a) * r
        cv.poly([(tx + math.cos(a) * r * .22, ty + math.sin(a) * r * .22), (tx + math.cos(a + 1.6) * r * .12, ty + math.sin(a + 1.6) * r * .12),
                 (tx + math.cos(a - 1.6) * r * .12, ty + math.sin(a - 1.6) * r * .12)], hx(GOLD))
    cv.ell(c, c, r * .2, r * .2, hx('#E63946'))
    return cv.out()


def vishnu(Hh=760, eyes='open', mouth='smile', namaste=False, bless=False, t=0.0, halo=True, chakra=True):
    """Four-armed Vishnu: front arms from person('vishnu'), rear arms hold chakra (R) and shankh (L)."""
    base = person('vishnu', Hh, eyes=eyes, mouth=mouth, namaste=namaste,
                  arms=((-1.4, 5.6), (1.0, 3.6)) if bless else None)
    w, h = base.size
    c = Cv(w, h)
    pad = int(Hh * .16)
    u = Hh / 10.0
    cx = w / 2
    skin = hx(SKIN['vishnu'])
    if halo:
        hy = pad + 2.0 * u
        for r, a in ((2.2, 60), (1.85, 90), (1.55, 120)):
            c.ell(cx, hy, r * u, r * u, hx('#FFE9A0', a))
    shy = pad + 3.25 * u
    for sg in (-1, 1):
        sh = (cx + sg * .9 * u, shy)
        hand = (cx + sg * 2.25 * u, pad + 1.9 * u)
        _arm(c, sh, hand, skin, .5 * u, sg)
    im = c.out()
    im.alpha_composite(base)
    # attributes in rear hands
    if chakra:
        ch = chakra_img(int(.55 * u), t)
        im.alpha_composite(ch, (int(cx + 2.25 * u - ch.width / 2), int(pad + 1.9 * u - .55 * u - ch.height / 2)))
    else:  # lotus in the rear right hand (before receiving Sudarshan)
        lt = lotus_img(int(.42 * u))
        im.alpha_composite(lt, (int(cx + 2.25 * u - lt.width / 2), int(pad + 1.9 * u - lt.height * .7)))
    sc = Cv(int(1.4 * u), int(1.4 * u))
    sc.poly([(.2 * u, .9 * u), (.7 * u, .15 * u), (1.2 * u, .55 * u), (1.0 * u, 1.2 * u), (.45 * u, 1.25 * u)], hx('#FBF7EE'))
    sc.arc(.75 * u, .75 * u, .32 * u, .32 * u, 0, 300, hx('#D9C9A8'), 3)
    sc.ell(.75 * u, .75 * u, .08 * u, .08 * u, hx(GOLD))
    s2 = sc.out()
    im.alpha_composite(s2, (int(cx - 2.25 * u - s2.width / 2), int(pad + 1.9 * u - .55 * u - s2.height / 2)))
    return im


def shaligram(r=70, glow=0.0):
    cv = Cv(int(r * 3.2), int(r * 2.6))
    cx, cy = r * 1.6, r * 1.4
    if glow > 0:
        for k, a in ((1.55, 50), (1.3, 80)):
            cv.ell(cx, cy, r * k, r * k * .85, hx('#FFE9A0', int(a * glow)))
    cv.ell(cx, cy, r, r * .78, hx('#1E1E24'))
    cv.ell(cx - r * .25, cy - r * .3, r * .45, r * .22, hx('#4A4A58'))
    cv.arc(cx + r * .15, cy + r * .1, r * .3, r * .24, 0, 330, hx('#E8E2D0'), max(2, r * .05))
    cv.arc(cx + r * .15, cy + r * .1, r * .15, r * .12, 40, 360, hx('#E8E2D0'), max(2, r * .04))
    cv.line([(cx - r * .15, cy - r * .55), (cx - r * .15, cy - r * .3)], hx('#E63946'), max(2, r * .06))
    return cv.out()


def tulsi_plant(Hh=420, grow=1.0, seed=7):
    """Holy basil bush with purple manjari; grow 0..1 scales from a sprout."""
    g = max(.05, min(1.0, grow))
    w = int(Hh * 1.1)
    cv = Cv(w, Hh + 40)
    cx, base = w / 2, Hh + 30
    rnd = random.Random(seed)
    stems = [(-0.42, .78), (-0.2, .95), (0, 1.0), (.22, .92), (.42, .76), (-.3, .6), (.32, .62)]
    for k, (dx, hh) in enumerate(stems):
        top = (cx + dx * w * .55 * g, base - Hh * hh * g)
        cv.line([(cx + dx * 20, base), (cx + dx * w * .3 * g, base - Hh * hh * .5 * g), top], hx('#4B6B2A'), max(2, 6 * g))
        n = int(5 + 4 * g)
        for j in range(n):
            q = (j + 1) / (n + 1)
            px = cx + dx * 20 + (top[0] - cx - dx * 20) * q
            py = base + (top[1] - base) * q
            for sg in (-1, 1):
                lx = px + sg * (18 + rnd.random() * 10) * g
                cv.ell(lx, py, 17 * g + 3, 10 * g + 2, hx('#2F8A3A' if (j + k) % 2 else '#3FA34A'))
        if g > .6:
            for j in range(4):
                cv.ell(top[0], top[1] - j * 12, 7, 9, hx('#8E3B8E'))
    return cv.out()


def bg_angan():
    """Evening courtyard: tulsi chaura, rangoli, diyas, marigold torans."""
    cv = Cv(W, H)
    cv.vgrad(0, 1150, hx('#3A1E5A'), hx('#F29A4A'))
    _sun(cv, 540, 1000, 150, '#FFE2A0')
    # house walls
    cv.rect(0, 700, 230, 1250, hx('#E9C99A'))
    cv.rect(850, 700, W, 1250, hx('#E9C99A'))
    cv.rect(0, 690, 230, 720, hx(MAROON2))
    cv.rect(850, 690, W, 720, hx(MAROON2))
    cv.rect(60, 900, 170, 1250, hx('#7A4A22'))
    cv.rect(910, 900, 1020, 1250, hx('#7A4A22'))
    # marigold toran
    for k in range(26):
        x = 20 + k * 42
        y = 330 + math.sin(k / 25 * math.pi) * 90
        cv.ell(x, y, 17, 17, hx('#F59E0B' if k % 2 else '#F97316'))
        if k % 3 == 0:
            cv.ell(x, y + 34, 14, 22, hx('#2F8A3A'))
    cv.rect(0, 1240, W, H, hx('#B9773E'))
    cv.vgrad(1240, H, hx('#C98A50'), hx('#6B3A1A'))
    # rangoli
    for r, col in ((230, '#F2C94C'), (180, '#E63946'), (130, '#2F8A3A'), (80, '#FFFFFF')):
        cv.ell(540, 1560, r * 1.4, r * .45, hx(col, 220))
    # diyas along the floor edge
    for x in (120, 260, 820, 960):
        cv.ell(x, 1290, 34, 12, hx('#C96A1F'))
        cv.poly([(x - 9, 1284), (x, 1240), (x + 9, 1284)], hx('#FFD34E'))
    _sparkles(cv, 24, 13, 120, 800, '#FFF6C0')
    _vignette(cv)
    return cv


def tulsi_chaura(Hh=300):
    w = int(Hh * 1.0)
    cv = Cv(w, Hh)
    cv.rect(w * .12, Hh * .25, w * .88, Hh, hx('#F4E2C0'))
    cv.rect(w * .05, Hh * .15, w * .95, Hh * .28, hx('#D9772B'))
    cv.rect(w * .05, Hh * .9, w * .95, Hh, hx('#D9772B'))
    for k in range(3):
        cv.ell(w * (.3 + k * .2), Hh * .6, w * .06, w * .06, hx('#E63946'))
    cv.line([(w * .2, Hh * .45), (w * .8, Hh * .45)], hx(GOLD2), 4)
    cv.line([(w * .2, Hh * .75), (w * .8, Hh * .75)], hx(GOLD2), 4)
    return cv.out()


def bg_pooja():
    """Vrinda's inner prayer room: arched niche, lamps, warm glow."""
    cv = Cv(W, H)
    cv.vgrad(0, H, hx('#5A1A2C'), hx('#2A0A14'))
    cv.rrect(240, 420, 840, 1260, 300, hx('#7A2A3C'))
    cv.rrect(280, 460, 800, 1250, 260, hx('#3A0E1C'))
    _sun(cv, 540, 820, 200, '#FFD98A')
    cv.rect(0, 1250, W, H, hx('#4A1A10'))
    cv.vgrad(1250, H, hx('#7A3A1A'), hx('#2A0E06'))
    for x in (130, 950):
        cv.rect(x - 10, 900, x + 10, 1250, hx(GOLD2))
        cv.ell(x, 1250, 60, 18, hx(GOLD2))
        cv.ell(x, 900, 46, 14, hx(GOLD))
        cv.poly([(x - 12, 896), (x, 830), (x + 12, 896)], hx('#FFD34E'))
    for k in range(18):
        x = 30 + k * 60
        cv.ell(x, 300 + math.sin(k / 17 * math.pi) * 60, 20, 20, hx('#F59E0B' if k % 2 else '#F97316'))
    _sparkles(cv, 16, 17, 200, 900, '#FFD08A')
    _vignette(cv)
    return cv


def bg_svarga():
    """Storm-dark sky over the battlefield mountains (Kailash in distance)."""
    cv = Cv(W, H)
    cv.vgrad(0, 1200, hx('#0F1A33'), hx('#5A4A7A'))
    _hills(cv, 1050, hx('#2A2A4A'), 260, 101)
    cv.poly([(380, 1050), (540, 640), (700, 1050)], hx('#DDE6F2'))
    cv.poly([(470, 820), (540, 640), (610, 820), (570, 790), (540, 830), (505, 790)], hx('#FFFFFF'))
    _hills(cv, 1180, hx('#1E1E36'), 120, 102)
    cv.rect(0, 1250, W, H, hx('#2A1E2A'))
    cv.vgrad(1250, H, hx('#3A2A3A'), hx('#120A12'))
    for x, y, r in ((200, 300, 130), (800, 380, 160), (520, 220, 110)):
        cv.ell(x, y, r * 1.6, r * .55, hx('#3A3A5A', 220))
    _vignette(cv)
    return cv


def bg_kshira():
    """Kshir Sagar: pale milky ocean at dawn, lotuses."""
    cv = Cv(W, H)
    cv.vgrad(0, 1150, hx('#BFE3F2'), hx('#FFF1D0'))
    _sun(cv, 540, 760, 280, '#FFF8E6')
    for k in range(24):
        a = k / 24 * 2 * math.pi
        cv.line([(540 + math.cos(a) * 320, 760 + math.sin(a) * 320), (540 + math.cos(a) * 560, 760 + math.sin(a) * 560)], hx('#FFFFFF', 110), 9)
    cv.rect(0, 1150, W, H, hx('#EAF4F4'))
    cv.vgrad(1150, H, hx('#F4FAF8'), hx('#9FC7D0'))
    for i in range(16):
        y = 1180 + i * 46
        for x in range(-40 + (i % 2) * 90, W, 180):
            cv.arc(x + 70, y, 70, 14, 200, 340, hx('#8FB8C4', 140), 4)
    for x, y in ((140, 1500), (930, 1440), (300, 1700), (820, 1720)):
        for ang in (-50, -25, 0, 25, 50):
            a = math.radians(ang)
            cv.poly([(x, y), (x + math.sin(a) * 40 - 12, y - math.cos(a) * 44), (x + math.sin(a) * 50, y - math.cos(a) * 60),
                     (x + math.sin(a) * 40 + 12, y - math.cos(a) * 44)], hx('#F7A8C4'))
        cv.ell(x, y + 6, 46, 12, hx('#3F8A4A'))
    _sparkles(cv, 26, 111, 150, 1100, '#FFFFFF')
    _vignette(cv)
    return cv


BACKGROUNDS.update({'angan': bg_angan, 'pooja': bg_pooja, 'svarga': bg_svarga, 'kshira': bg_kshira})


# ---------------------------------------------------------------- Ganesh parikrama (added for story 005)
GSKIN = '#F2A97E'


def ganesha(Hh=640, namaste=False, bless=False, eyes='open', mouth='smile', walk=0.0, flip=False, modak=False):
    """Bal Ganesh: plump body, elephant head with curled trunk and one tusk, small crown. Feet at bottom centre."""
    w = int(Hh * 1.05)
    pad = int(Hh * .2)
    c = Cv(w, Hh + pad)
    c.oy = pad
    u = Hh / 10.0
    cx = w / 2
    skin = hx(GSKIN)
    sd = hx('#D98A5E')
    dark = hx('#2A1208')
    # legs
    sw = math.sin(walk) * .35 * u
    for sgn, off in ((-1, sw), (1, -sw)):
        fx = cx + sgn * .75 * u + off
        c.rrect(fx - .38 * u, 8.3 * u, fx + .38 * u, 9.75 * u, .25 * u, skin)
        c.ell(fx + sgn * .05 * u, 9.78 * u, .55 * u, .22 * u, skin)
    # dhoti
    c.poly([(cx - 1.6 * u, 6.2 * u), (cx + 1.6 * u, 6.2 * u), (cx + 1.85 * u, 8.7 * u), (cx - 1.85 * u, 8.7 * u)], hx('#F4C430'))
    for k in (-.9, -.3, .3, .9):
        c.line([(cx + k * u, 6.5 * u), (cx + k * 1.15 * u, 8.6 * u)], hx('#D9A41A'), 2)
    c.rect(cx - 1.85 * u, 8.45 * u, cx + 1.85 * u, 8.7 * u, hx('#C0392B'))
    # belly / torso
    c.ell(cx, 5.6 * u, 1.75 * u, 1.65 * u, skin)
    c.ell(cx, 5.9 * u, 1.3 * u, 1.15 * u, hx('#F6B892'))
    c.ell(cx, 6.0 * u, .1 * u, .1 * u, sd)
    c.rrect(cx - 1.7 * u, 6.15 * u, cx + 1.7 * u, 6.45 * u, .1 * u, hx('#C0392B'))
    # sacred thread + necklace
    c.line([(cx - 1.1 * u, 4.1 * u), (cx + 1.2 * u, 6.1 * u)], hx('#FFF6DC'), 3)
    c.line([(cx - .9 * u, 4.0 * u), (cx, 4.7 * u), (cx + .9 * u, 4.0 * u)], hx(GOLD), 6)
    # arms
    if namaste:
        arms = ((-.25, 4.7), (.25, 4.7))
    elif bless:
        arms = ((-1.9, 6.3), (1.6, 3.9))
    else:
        arms = ((-1.9, 6.3), (1.9, 6.3))
    shL, shR = (cx - 1.35 * u, 4.2 * u), (cx + 1.35 * u, 4.2 * u)
    _arm(c, shL, (cx + arms[0][0] * u, arms[0][1] * u), skin, .62 * u, -1)
    _arm(c, shR, (cx + arms[1][0] * u, arms[1][1] * u), skin, .62 * u, 1)
    if bless:
        c.ell(cx + 1.6 * u, 3.9 * u, .5 * u, .38 * u, skin)
    if modak:
        mx, my = cx + arms[0][0] * u, arms[0][1] * u - .2 * u
        c.poly([(mx - .4 * u, my), (mx, my - .6 * u), (mx + .4 * u, my)], hx('#FFF1D0'))
        c.ell(mx, my, .4 * u, .2 * u, hx('#FFF1D0'))
    # ears (big)
    hy = 2.5 * u
    for sg in (-1, 1):
        c.ell(cx + sg * 1.45 * u, hy + .1 * u, .95 * u, 1.15 * u, sd)
        c.ell(cx + sg * 1.45 * u, hy + .1 * u, .72 * u, .9 * u, hx('#F7C2A2'))
    # head
    c.ell(cx, hy, 1.15 * u, 1.2 * u, skin)
    # trunk curling to the (viewer) right
    tr = [(cx, hy + .4 * u), (cx - .05 * u, hy + 1.3 * u), (cx + .2 * u, hy + 2.0 * u), (cx + .7 * u, hy + 2.25 * u), (cx + 1.0 * u, hy + 1.95 * u)]
    c.line(tr, skin, .55 * u)
    for k in range(4):
        y = hy + .9 * u + k * .3 * u
        c.arc(cx, y, .26 * u, .08 * u, 20, 160, sd, 2)
    # tusk (one)
    c.poly([(cx - .45 * u, hy + .75 * u), (cx - .25 * u, hy + .8 * u), (cx - .55 * u, hy + 1.35 * u)], hx('#FFFBEF'))
    # eyes
    for sgn in (-1, 1):
        ex, ey = cx + sgn * .5 * u, hy - .05 * u
        if eyes == 'open':
            c.ell(ex, ey, .14 * u, .1 * u, hx('#FFFFFF'))
            c.ell(ex, ey, .065 * u, .085 * u, dark)
        else:
            c.arc(ex, ey, .15 * u, .1 * u, 200, 340, dark, 3)
    if mouth == 'smile':
        c.arc(cx - .45 * u, hy + .85 * u, .2 * u, .12 * u, 20, 160, hx('#7A2A2A'), 3)
    # tilak + crown
    c.line([(cx, hy - .75 * u), (cx, hy - .4 * u)], hx('#E63946'), 4)
    by = hy - 1.05 * u
    c.poly([(cx - .9 * u, by + .25 * u), (cx - .8 * u, by - .35 * u), (cx - .4 * u, by - .1 * u), (cx, by - .95 * u),
            (cx + .4 * u, by - .1 * u), (cx + .8 * u, by - .35 * u), (cx + .9 * u, by + .25 * u)], hx(GOLD))
    c.rect(cx - .92 * u, by + .05 * u, cx + .92 * u, by + .28 * u, hx(GOLD2))
    for k in (-.5, 0, .5):
        c.ell(cx + k * u, by + .16 * u, .07 * u, .07 * u, hx('#E63946'))
    im = c.out()
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def peacock(Hh=420, fan=1.0, flap=0.0, flip=False):
    """Peacock vahan; side view facing right. fan 0..1 spreads the tail. Feet at bottom centre."""
    w = int(Hh * 2.0)
    c = Cv(w, int(Hh * 1.3))
    c.oy = int(Hh * .3)
    u = Hh / 10.0
    cx = w * .55
    # tail fan
    if fan > .05:
        for k in range(13):
            a = math.radians(-170 + k * 12 * fan + (1 - fan) * 60)
            L = 8.5 * u * (.55 + .45 * fan)
            x1, y1 = cx - 1.5 * u + math.cos(a) * L, 5.0 * u + math.sin(a) * L * .85
            c.line([(cx - 1.5 * u, 5.0 * u), (x1, y1)], hx('#2E8B57'), 6)
            c.ell(x1, y1, .9 * u, .75 * u, hx('#1E8E6E'))
            c.ell(x1, y1, .55 * u, .48 * u, hx('#1B4F9C'))
            c.ell(x1, y1, .25 * u, .22 * u, hx('#F2C94C'))
    else:
        c.poly([(cx - 1.5 * u, 5.0 * u), (cx - 8.5 * u, 6.3 * u), (cx - 8.3 * u, 7.0 * u), (cx - 1.2 * u, 6.0 * u)], hx('#2E8B57'))
        for k in range(5):
            x = cx - 3.0 * u - k * 1.2 * u
            c.ell(x, 6.0 * u + k * .2 * u, .45 * u, .3 * u, hx('#1B4F9C'))
    # legs
    for dx in (-.5, .4):
        c.line([(cx + dx * u, 6.4 * u), (cx + dx * u, 9.4 * u)], hx('#9C7A4A'), 5)
        c.line([(cx + dx * u - .4 * u, 9.6 * u), (cx + dx * u + .5 * u, 9.6 * u)], hx('#9C7A4A'), 5)
    # body
    c.ell(cx, 5.4 * u, 2.1 * u, 1.35 * u, hx('#1F5FBF'))
    # wing
    wy = 5.2 * u - flap * 1.6 * u
    c.poly([(cx - 1.5 * u, 4.9 * u), (cx + .9 * u, 4.7 * u), (cx + .2 * u, wy + 1.3 * u), (cx - 1.9 * u, wy + .8 * u)], hx('#2C7A6A'))
    # neck + head
    c.line([(cx + 1.3 * u, 4.9 * u), (cx + 1.9 * u, 3.2 * u), (cx + 2.2 * u, 1.9 * u)], hx('#1F5FBF'), 1.1 * u)
    c.ell(cx + 2.3 * u, 1.6 * u, .62 * u, .55 * u, hx('#1F5FBF'))
    c.poly([(cx + 2.8 * u, 1.45 * u), (cx + 3.5 * u, 1.75 * u), (cx + 2.8 * u, 1.9 * u)], hx('#C9A06C'))
    c.ell(cx + 2.45 * u, 1.45 * u, .12 * u, .12 * u, hx('#FFFFFF'))
    c.ell(cx + 2.48 * u, 1.45 * u, .06 * u, .06 * u, hx('#111111'))
    for k in (-1, 0, 1):  # crest
        c.line([(cx + 2.2 * u, 1.1 * u), (cx + 2.0 * u + k * .3 * u, .25 * u)], hx('#1F5FBF'), 2)
        c.ell(cx + 2.0 * u + k * .3 * u, .2 * u, .12 * u, .12 * u, hx('#1B4F9C'))
    im = c.out()
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def mushak(Hh=160, flip=False):
    """Little mouse vahan (side view facing right). Feet at bottom centre."""
    w = int(Hh * 2.2)
    c = Cv(w, int(Hh * 1.2))
    c.oy = int(Hh * .2)
    u = Hh / 10.0
    cx = w * .5
    c.line([(cx - 4 * u, 7.5 * u), (cx - 6.5 * u, 6.0 * u), (cx - 8.5 * u, 7.8 * u)], hx('#8A8A96'), 3)
    c.ell(cx - .5 * u, 6.4 * u, 4.0 * u, 3.1 * u, hx('#8E8E9C'))
    c.ell(cx - .2 * u, 7.0 * u, 2.6 * u, 1.8 * u, hx('#B4B4C2'))
    c.ell(cx + 3.6 * u, 5.2 * u, 2.1 * u, 1.8 * u, hx('#8E8E9C'))
    c.poly([(cx + 5.2 * u, 4.6 * u), (cx + 7.0 * u, 5.6 * u), (cx + 5.2 * u, 6.3 * u)], hx('#8E8E9C'))
    c.ell(cx + 7.0 * u, 5.6 * u, .45 * u, .4 * u, hx('#E8798A'))
    c.ell(cx + 2.9 * u, 3.2 * u, 1.2 * u, 1.3 * u, hx('#8E8E9C'))
    c.ell(cx + 2.9 * u, 3.3 * u, .75 * u, .85 * u, hx('#F2B8C2'))
    c.ell(cx + 4.4 * u, 4.7 * u, .32 * u, .32 * u, hx('#1A1A1A'))
    c.ell(cx + 4.5 * u, 4.6 * u, .1 * u, .1 * u, hx('#FFFFFF'))
    for dx in (-2.5, 1.5):
        c.ell(cx + dx * u, 9.3 * u, .8 * u, .45 * u, hx('#E8A0AA'))
    # tiny red saddle-cloth
    c.poly([(cx - 2.2 * u, 3.6 * u), (cx + 1.2 * u, 3.5 * u), (cx + 1.0 * u, 5.4 * u), (cx - 2.0 * u, 5.5 * u)], hx('#C0392B'))
    c.rect(cx - 2.2 * u, 5.2 * u, cx + 1.1 * u, 5.5 * u, hx(GOLD))
    im = c.out()
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def bg_kailash_dawn():
    """Dawn on Mount Kailash: snow peaks, crescent sky, rocky ledge."""
    cv = Cv(W, H)
    cv.vgrad(0, 1150, hx('#2B3A78'), hx('#F6C08A'))
    _sun(cv, 540, 1020, 170, '#FFE9B8')
    cv.ell(820, 300, 60, 60, hx('#FFF6D8'))
    cv.ell(845, 285, 52, 52, hx('#3A4A86'))
    _sparkles(cv, 26, 51, 120, 650, '#FFFFFF')
    _hills(cv, 1000, hx('#7C8FB8'), 220, 52, n=6)
    # main peak
    cv.poly([(230, 1120), (540, 470), (850, 1120)], hx('#B9C6E0'))
    cv.poly([(540, 470), (850, 1120), (640, 1120)], hx('#93A4C8'))
    cv.poly([(430, 700), (540, 470), (650, 700), (600, 670), (560, 720), (515, 668), (470, 712)], hx('#FFFFFF'))
    _hills(cv, 1150, hx('#5A6A94'), 110, 53, n=8)
    # rocky ledge (seat area)
    cv.rect(0, 1240, W, H, hx('#9A8A7A'))
    cv.vgrad(1240, H, hx('#9A8A7A'), hx('#4A3A3A'))
    for x, y, r in ((160, 1640, 120), (900, 1700, 150), (520, 1820, 110)):
        cv.ell(x, y, r * 1.5, r * .45, hx('#5A5668'))
    cv.rect(0, 1236, W, 1246, hx('#F2F4FA'))
    _vignette(cv)
    return cv


def bg_aakash():
    """High sky over the earth: clouds, distant hills, river, sea on the horizon."""
    cv = Cv(W, H)
    cv.vgrad(0, 1200, hx('#5FB3F0'), hx('#E9F6FF'))
    _sun(cv, 860, 330, 110, '#FFF6D8')
    cv.rect(0, 1150, W, H, hx('#7DB862'))
    cv.vgrad(1150, H, hx('#8CC26C'), hx('#3F7D3A'))
    cv.rect(0, 1140, W, 1175, hx('#5AA9D6'))  # sea on horizon
    _hills(cv, 1230, hx('#6D9E58'), 90, 61, n=9)
    cv.poly([(470, 1240), (520, 1240), (760, H), (360, H)], hx('#6EC1E8'))  # river
    for x, h in ((90, 300), (240, 230), (880, 320), (990, 240)):
        _tree(cv, x, 1420, h)
    for x, y, r in ((180, 520, 90), (640, 720, 120), (300, 980, 80), (880, 900, 100)):
        cv.ell(x, y, r * 1.8, r * .6, hx('#FFFFFF', 235))
        cv.ell(x - r * .6, y - r * .25, r * .9, r * .5, hx('#FFFFFF', 235))
    _vignette(cv)
    return cv


def bg_jungle():
    """Deep green forest and waterfall."""
    cv = Cv(W, H)
    cv.vgrad(0, 1150, hx('#9FD8C8'), hx('#E8F5D0'))
    _hills(cv, 900, hx('#5E9A6A'), 200, 71)
    cv.rect(470, 640, 610, 1250, hx('#CFEFFF'))
    for k in range(6):
        cv.line([(480 + k * 24, 650), (480 + k * 24, 1240)], hx('#FFFFFF', 160), 4)
    _hills(cv, 1150, hx('#3F7D4A'), 140, 72)
    cv.rect(0, 1240, W, H, hx('#356B3A'))
    cv.vgrad(1240, H, hx('#4A8A4A'), hx('#1E4A26'))
    cv.ell(540, 1300, 260, 60, hx('#8FD0E8'))
    for x, h in ((60, 640), (200, 520), (330, 420), (760, 430), (890, 560), (1030, 660)):
        _tree(cv, x, 1330, h, leaf='#2F6E3A', leaf2='#4A9A4A')
    _vignette(cv)
    return cv


BACKGROUNDS.update({'kailash_dawn': bg_kailash_dawn, 'aakash': bg_aakash, 'jungle': bg_jungle})


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


# ---------------------------------------------------------------- Tripurari (added for story 004)
SKIN['shiva'] = '#9FC0D8'   # ash-blue (vibhuti)


def shiva(Hh=760, eyes='open', mouth='smile', bless=False, bow=False, namaste=False, trishul=True, halo=True):
    """Mahadev: ash-blue skin, jata with crescent + Ganga stream, tiger-skin, rudraksha, snake, trishul.
    bow=True: left arm forward holding (drawn separately) bow, right arm drawn back."""
    w = int(Hh * 1.2)
    pad = int(Hh * .3)
    c = Cv(w, Hh + pad)
    c.oy = pad
    u = Hh / 10.0
    cx = w / 2
    skin = hx(SKIN['shiva'])
    dark = hx('#1E2433')
    jata = hx('#3A2A22')
    tw = 2.3 * u
    if halo:
        for r, a in ((2.4, 50), (2.0, 80), (1.65, 110)):
            c.ell(cx, 1.6 * u, r * u, r * u, hx('#DCEBFF', a))
    if trishul and not bow:
        tx = cx + 2.3 * u
        c.line([(tx, -1.6 * u), (tx, 9.6 * u)], hx('#8C99AE'), .2 * u)
        c.line([(tx, -1.6 * u), (tx, 9.6 * u)], hx('#E8EEF6'), .1 * u)
        c.poly([(tx - .16 * u, -1.5 * u), (tx, -2.6 * u), (tx + .16 * u, -1.5 * u)], hx('#E8EEF6'))
        for sg in (-1, 1):
            c.line([(tx, -.9 * u), (tx + sg * .6 * u, -1.1 * u), (tx + sg * .68 * u, -2.0 * u)], hx('#E8EEF6'), .14 * u)
            c.poly([(tx + sg * .58 * u, -1.95 * u), (tx + sg * .7 * u, -2.5 * u), (tx + sg * .82 * u, -1.95 * u)], hx('#E8EEF6'))
        # damru tied below the prongs
        c.poly([(tx - .32 * u, -.45 * u), (tx + .32 * u, -.45 * u), (tx, .0 * u)], hx('#C98A1B'))
        c.poly([(tx - .32 * u, .45 * u), (tx + .32 * u, .45 * u), (tx, .0 * u)], hx('#C98A1B'))
        c.line([(tx - .4 * u, 0), (tx - .7 * u, .3 * u)], hx('#B5262F'), 3)
    # legs
    for sgn in (-1, 1):
        fx = cx + sgn * .7 * u
        c.rrect(fx - .3 * u, 8.4 * u, fx + .3 * u, 9.75 * u, .2 * u, skin)
        c.ell(fx + sgn * .03 * u, 9.78 * u, .46 * u, .2 * u, skin)
    # tiger skin (bagh-chhal)
    c.poly([(cx - 1.3 * u, 5.0 * u), (cx + 1.3 * u, 5.0 * u), (cx + 1.6 * u, 8.6 * u), (cx - 1.6 * u, 8.6 * u)], hx('#E8A23A'))
    for k in range(7):
        yy = 5.4 * u + k * .45 * u
        c.line([(cx - 1.2 * u + (k % 2) * .3 * u, yy), (cx - .7 * u + (k % 2) * .3 * u, yy + .15 * u)], hx('#3A2410'), 4)
        c.line([(cx + .5 * u - (k % 2) * .3 * u, yy + .1 * u), (cx + 1.1 * u - (k % 2) * .3 * u, yy)], hx('#3A2410'), 4)
    zz = [(cx - 1.6 * u + i * .4 * u, 8.6 * u + (.28 * u if i % 2 else 0)) for i in range(9)]
    c.poly([(cx - 1.6 * u, 8.4 * u), (cx + 1.6 * u, 8.4 * u)] + zz[::-1], hx('#E8A23A'))
    c.rrect(cx - 1.35 * u, 4.9 * u, cx + 1.35 * u, 5.25 * u, .1 * u, hx('#6B4226'))
    # torso
    c.poly([(cx - tw / 2, 2.95 * u), (cx + tw / 2, 2.95 * u), (cx + tw * .42, 5.2 * u), (cx - tw * .42, 5.2 * u)], skin)
    c.ell(cx, 2.95 * u, tw / 2, .28 * u, skin)
    # rudraksha mala
    for t in np.linspace(0, 1, 13):
        px = cx - .95 * u + t * 1.9 * u
        py = 3.05 * u + math.sin(t * math.pi) * 1.5 * u
        c.ell(px, py, .12 * u, .12 * u, hx('#7A3A1A'))
    # snake (Vasuki) around the neck
    c.arc(cx, 2.95 * u, .95 * u, .55 * u, 10, 170, hx('#2F7A4A'), int(.22 * u))
    c.ell(cx + .95 * u, 2.75 * u, .2 * u, .15 * u, hx('#2F7A4A'))
    c.ell(cx + 1.0 * u, 2.72 * u, .04 * u, .04 * u, hx('#FFE08A'))
    # arms
    shL = (cx - tw / 2 + .1 * u, 3.2 * u)
    shR = (cx + tw / 2 - .1 * u, 3.2 * u)
    if bow:
        arms = ((-3.2, 3.3), (1.0, 3.5))
    elif namaste:
        arms = ((-.25, 4.0), (.25, 4.0))
    elif bless:
        arms = ((-1.4, 5.6), (1.1, 3.6))
    else:
        arms = ((-1.5, 5.7), (1.9, 4.6) if trishul else (1.5, 5.7))
    _arm(c, shL, (cx + arms[0][0] * u, arms[0][1] * u), skin, .55 * u, -1)
    _arm(c, shR, (cx + arms[1][0] * u, arms[1][1] * u), skin, .55 * u, 1)
    if bless and not bow:
        c.ell(cx + 1.1 * u, 3.35 * u, .32 * u, .4 * u, skin)
    # neck + head
    c.rect(cx - .3 * u, 2.65 * u, cx + .3 * u, 3.15 * u, skin)
    hr = .95 * u
    hcy = 2.0 * u
    # jata (matted hair falling to shoulders)
    c.ell(cx, hcy - .05 * u, hr * 1.12, hr * 1.12, jata)
    c.poly([(cx - hr * 1.1, hcy), (cx - hr * 1.35, hcy + 1.3 * u), (cx - hr * .7, hcy + 1.0 * u)], jata)
    c.poly([(cx + hr * 1.1, hcy), (cx + hr * 1.35, hcy + 1.3 * u), (cx + hr * .7, hcy + 1.0 * u)], jata)
    # top bun of jata
    c.ell(cx, hcy - hr * 1.25, .7 * u, .6 * u, jata)
    c.ell(cx, hcy - hr * 1.7, .45 * u, .42 * u, jata)
    c.rect(cx - .7 * u, hcy - hr * 1.05, cx + .7 * u, hcy - hr * .92, hx('#7A3A1A'))
    # Ganga stream from the jata
    c.line([(cx - .25 * u, hcy - hr * 2.0), (cx - .45 * u, hcy - hr * 2.5), (cx - .2 * u, hcy - hr * 2.9)], hx('#BFE6FF', 230), .16 * u)
    # crescent moon
    c.ell(cx + .5 * u, hcy - hr * 1.5, .32 * u, .32 * u, hx('#FFF6D8'))
    c.ell(cx + .62 * u, hcy - hr * 1.58, .27 * u, .27 * u, jata)
    # ears + face
    c.ell(cx - hr + .02 * u, hcy, .17 * u, .26 * u, skin)
    c.ell(cx + hr - .02 * u, hcy, .17 * u, .26 * u, skin)
    c.ell(cx, hcy, hr, hr * 1.06, skin)
    for sg in (-1, 1):
        c.ell(cx + sg * hr * 1.0, hcy + .35 * u, .1 * u, .14 * u, hx(GOLD))
    ey = hcy + .05 * u
    for sgn in (-1, 1):
        ex = cx + sgn * .38 * u
        if eyes == 'open':
            c.ell(ex, ey, .13 * u, .09 * u, hx('#FFFFFF'))
            c.ell(ex, ey, .06 * u, .08 * u, dark)
        else:
            c.arc(ex, ey, .14 * u, .1 * u, 200, 340, dark, 3)
        c.line([(ex - .17 * u, ey - .24 * u), (ex + .17 * u, ey - .27 * u)] if sgn > 0 else
               [(ex + .17 * u, ey - .24 * u), (ex - .17 * u, ey - .27 * u)], dark, 3)
    # tripund (three ash lines) + third eye closed (calm, respectful)
    for k in range(3):
        c.line([(cx - .42 * u, hcy - .7 * u + k * .1 * u), (cx + .42 * u, hcy - .7 * u + k * .1 * u)], hx('#F4F7FA'), 3)
    c.ell(cx, hcy - .6 * u, .07 * u, .12 * u, hx('#C0392B'))
    if mouth == 'smile':
        c.arc(cx, hcy + .44 * u, .26 * u, .16 * u, 20, 160, hx('#4A2A3A'), 4)
    else:
        c.line([(cx - .14 * u, hcy + .52 * u), (cx + .14 * u, hcy + .52 * u)], hx('#4A2A3A'), 3)
    return c.out()


def asura(Hh=760, col='#7E5A44', dhoti='#5A1A1A', cape='#2B1B4F', angry=False, point=False):
    """Simple crowned asura prince (one head) for the three Tripura brothers."""
    return ravana(Hh, angry=angry, point=point, heads=1, skin_col=col, dhoti=dhoti, cape=cape)


SKIN['deva'] = '#E9B47A'


def deva(Hh=760, namaste=True, eyes='open', mouth='flat'):
    """Generic devata (Indra-like): fair skin, gold kirit, pitambar, folded hands."""
    return person('deva', Hh, namaste=namaste, eyes=eyes, mouth=mouth)


def city_img(kind='gold', w=360):
    """A floating fortress-city: gold / silver / iron, on a rock base."""
    h = int(w * .9)
    cv = Cv(w, h)
    pal = {'gold': ('#E8B84A', '#C98A1B', '#FFE08A'), 'silver': ('#D9DEE6', '#9AA4B4', '#FFFFFF'),
           'iron': ('#6A6E78', '#3E424C', '#A9AEB8')}[kind]
    b, d_, hl = pal
    cv.poly([(w * .08, h * .62), (w * .92, h * .62), (w * .7, h * .92), (w * .5, h), (w * .3, h * .9)], hx('#5A4A3A'))
    cv.poly([(w * .08, h * .62), (w * .92, h * .62), (w * .8, h * .72), (w * .2, h * .72)], hx('#7A6A5A'))
    for x, hh, ww in ((.22, .3, .16), (.5, .48, .22), (.78, .3, .16), (.36, .22, .12), (.64, .22, .12)):
        X = w * x
        top = h * (.62 - hh)
        cv.rect(X - w * ww / 2, top, X + w * ww / 2, h * .63, hx(b))
        cv.ell(X, top, w * ww / 2 * .9, w * ww / 2, hx(d_))
        cv.line([(X, top - w * ww / 2), (X, top - w * ww * .9)], hx(hl), 3)
        cv.rect(X - w * ww * .12, h * .63 - hh * h * .45, X + w * ww * .12, h * .63, hx('#2A1A10'))
    cv.rect(w * .1, h * .58, w * .9, h * .63, hx(d_))
    return cv.out()


def bow_img(Hh=700, drawn=0.0):
    """Meru-bow (golden) with Vasuki as the string, vertical; drawn 0..1 pulls the string right."""
    w = int(Hh * .5)
    cv = Cv(w, Hh)
    x0 = w * .25
    pts = [(x0 + math.sin(t * math.pi) * -w * .05 + (1 - math.sin(t * math.pi)) * w * .18, t * Hh) for t in np.linspace(0.02, .98, 30)]
    cv.line(pts, hx('#8A5A1A'), Hh * .035)
    cv.line(pts, hx(GOLD), Hh * .02)
    top, bot = pts[0], pts[-1]
    mid = (top[0] + w * .1 + drawn * w * .55, Hh / 2)
    cv.line([top, mid, bot], hx('#2F7A4A'), Hh * .012)
    cv.ell(top[0], top[1] + 6, Hh * .02, Hh * .015, hx('#2F7A4A'))
    return cv.out()


def ratha_img(w=620, t=0.0):
    """Divine chariot: earth-coloured body, Sun wheel (left) and Moon wheel (right)."""
    h = int(w * .55)
    cv = Cv(w, h)
    cv.poly([(w * .1, h * .25), (w * .9, h * .25), (w * .82, h * .62), (w * .18, h * .62)], hx('#6B8E3A'))
    cv.poly([(w * .14, h * .3), (w * .86, h * .3), (w * .8, h * .55), (w * .2, h * .55)], hx('#8FB14A'))
    cv.rect(w * .1, h * .2, w * .9, h * .27, hx(GOLD))
    cv.line([(w * .9, h * .4), (w * 1.0, h * .3)], hx(GOLD2), 8)
    for X, sun in ((w * .27, True), (w * .73, False)):
        R = h * .32
        cy = h * .66
        col = '#FFC93C' if sun else '#EEF3FA'
        cv.ell(X, cy, R * 1.15, R * 1.15, hx('#FFE9A0' if sun else '#DCE6F5', 90))
        cv.ell(X, cy, R, R, hx(col))
        cv.ell(X, cy, R * .78, R * .78, hx('#E8901A' if sun else '#B9C6DA'))
        for k in range(8):
            a = t * 3 + k * math.pi / 4
            cv.line([(X, cy), (X + math.cos(a) * R * .78, cy + math.sin(a) * R * .78)], hx(col), 5)
        cv.ell(X, cy, R * .2, R * .2, hx(col))
    return cv.out()


def bg_kailash():
    """Kailash at twilight: snowy peak, deep blue sky, moon."""
    cv = Cv(W, H)
    cv.vgrad(0, 1250, hx('#16234A'), hx('#7A8CC4'))
    _sun(cv, 820, 420, 70, '#FFF6D8')
    _sparkles(cv, 34, 141, 120, 800, '#FFFFFF')
    _hills(cv, 1100, hx('#3A4A7A'), 200, 142)
    cv.poly([(250, 1150), (540, 560), (830, 1150)], hx('#E6EEF8'))
    cv.poly([(400, 860), (540, 560), (680, 860), (620, 820), (580, 880), (540, 830), (500, 880), (460, 820)], hx('#FFFFFF'))
    cv.poly([(540, 560), (600, 1150), (830, 1150)], hx('#C9D6EA'))
    _hills(cv, 1230, hx('#2A3660'), 90, 143)
    cv.rect(0, 1260, W, H, hx('#B9C6E0'))
    cv.vgrad(1260, H, hx('#C9D4EA'), hx('#5A6A9A'))
    _vignette(cv)
    return cv


def bg_tripura_sky():
    """Cosmic sky (three levels) for the flying cities, drawn per-frame on top."""
    cv = Cv(W, H)
    cv.vgrad(0, H, hx('#1A0E3A'), hx('#7A2A4A'))
    _sparkles(cv, 50, 151, 100, 1500, '#FFFFFF')
    for x, y, r in ((180, 900, 130), (900, 1100, 160), (500, 1400, 140)):
        cv.ell(x, y, r * 1.8, r * .5, hx('#B07AA8', 90))
    _hills(cv, 1600, hx('#2A0E2A'), 120, 152)
    cv.rect(0, 1650, W, H, hx('#1A0612'))
    _vignette(cv)
    return cv


def bg_tapas():
    """Barren rocky land, dusky orange sky: asuras' penance."""
    cv = Cv(W, H)
    cv.vgrad(0, 1200, hx('#3A1A2A'), hx('#E8803A'))
    _sun(cv, 540, 1020, 160, '#FFD27A')
    _hills(cv, 1120, hx('#6A3A2A'), 220, 161)
    _hills(cv, 1220, hx('#4A2A1E'), 120, 162)
    cv.rect(0, 1260, W, H, hx('#5A3420'))
    cv.vgrad(1260, H, hx('#7A4A2A'), hx('#2A140A'))
    _vignette(cv)
    return cv


def bg_ghat():
    """Kashi ghats at night on Dev Deepawali: steps, temples, river reflecting diyas."""
    cv = Cv(W, H)
    cv.vgrad(0, 1000, hx('#0E1236'), hx('#3A2A6A'))
    _sun(cv, 820, 330, 64, '#FFF6D8')   # full moon
    _sparkles(cv, 26, 171, 100, 600, '#FFFFFF')
    for x, h_, w_ in ((120, 380, 160), (330, 300, 180), (560, 460, 200), (790, 340, 170), (980, 280, 150)):
        base = 1000
        cv.rect(x - w_ / 2, base - h_, x + w_ / 2, base, hx('#A8683A'))
        cv.poly([(x - w_ * .35, base - h_), (x, base - h_ - w_ * .9), (x + w_ * .35, base - h_)], hx('#C98A4A'))
        cv.line([(x, base - h_ - w_ * .9), (x, base - h_ - w_ * 1.1)], hx(GOLD), 4)
        cv.poly([(x, base - h_ - w_ * 1.1), (x + 30, base - h_ - w_ * 1.03), (x, base - h_ - w_ * .98)], hx('#F08A24'))
    for k in range(6):  # ghat steps
        y = 1000 + k * 40
        cv.rect(0, y, W, y + 40, hx('#8A5A3A' if k % 2 else '#7A4A2E'))
    cv.rect(0, 1240, W, H, hx('#14204A'))
    cv.vgrad(1240, H, hx('#22306A'), hx('#0A1030'))
    for i in range(14):
        y = 1270 + i * 46
        for x in range(-40 + (i % 2) * 90, W, 180):
            cv.arc(x + 70, y, 70, 12, 200, 340, hx('#6A7AC0', 110), 3)
    _vignette(cv)
    return cv


BACKGROUNDS.update({'kailash': bg_kailash, 'tripura': bg_tripura_sky, 'tapas': bg_tapas, 'ghat': bg_ghat})


# ---------------------------------------------------------------- Matsya avatar (added for story 006)
SKIN['raja'] = '#D99A68'


def raja(Hh=760, **kw):
    """Rajarshi Satyavrata: saffron dhoti, gold kirit, dark beard."""
    return person('raja', Hh, **kw)


def matsya_img(L=600, horn=False, flip=False, glow=0.0, t=0.0, gold=True):
    """Side-view fish facing right. L = body length. horn=True: the single golden horn of Matsya avatar."""
    w, h = int(L * 1.5), int(L * .9)
    cv = Cv(w, h)
    cx, cy = w * .55, h * .55
    body = hx('#F2B632') if gold else hx('#F08A3C')
    body2 = hx('#E8901A') if gold else hx('#D4642A')
    belly = hx('#FFE9A0')
    if glow > 0:
        for k, a in ((1.0, 50), (.8, 80)):
            cv.ell(cx, cy, L * .62 * k + 30, L * .3 * k + 30, hx('#FFF1B0', int(a * glow)))
    wag = math.sin(t * 6) * .08
    tx = cx - L * .5
    cv.poly([(tx + L * .08, cy), (tx - L * .25, cy - L * (.28 + wag)), (tx - L * .16, cy), (tx - L * .25, cy + L * (.28 - wag))], body2)
    cv.poly([(cx - L * .05, cy - L * .2), (cx + L * .12, cy - L * .36), (cx + L * .2, cy - L * .19)], body2)  # dorsal
    cv.poly([(cx - L * .05, cy + L * .18), (cx + L * .06, cy + L * .32), (cx + L * .14, cy + L * .17)], body2)
    cv.ell(cx, cy, L * .5, L * .22, body)
    cv.ell(cx + L * .04, cy + L * .08, L * .4, L * .1, belly)
    for i in range(5):  # scales
        for j in (-1, 0, 1):
            cv.arc(cx - L * .25 + i * L * .1, cy + j * L * .08 - L * .02, L * .05, L * .045, 270, 90, hx('#C98A1B', 200), max(2, L * .008))
    hx_ = cx + L * .33
    cv.arc(hx_, cy, L * .1, L * .19, 280, 80, hx('#C98A1B'), max(2, L * .01))  # gill
    cv.ell(cx + L * .4, cy - L * .05, L * .045, L * .045, hx('#FFFFFF'))
    cv.ell(cx + L * .41, cy - L * .05, L * .025, L * .03, hx('#2A1208'))
    cv.arc(cx + L * .45, cy + L * .06, L * .04, L * .025, 20, 160, hx('#7A2A2A'), max(2, L * .008))
    if horn:
        hb = (cx + L * .36, cy - L * .17)
        cv.poly([(hb[0] - L * .05, hb[1] + L * .03), (hb[0] + L * .2, hb[1] - L * .32), (hb[0] + L * .06, hb[1] + L * .02)], hx('#FFE08A'))
        cv.line([(hb[0] - L * .02, hb[1]), (hb[0] + L * .19, hb[1] - L * .3)], hx(GOLD2), max(2, L * .008))
        # tilak + small crown-jewel
        cv.line([(cx + L * .37, cy - L * .14), (cx + L * .37, cy - L * .09)], hx('#E63946'), max(2, L * .012))
    im = cv.out()
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def horn_tip(L, flip=False):
    """(x, y) of the horn tip inside matsya_img(L) sprite (sprite coords)."""
    w, h = int(L * 1.5), int(L * .9)
    x, y = w * .55 + L * .36 + L * .2, h * .55 - L * .17 - L * .32
    return (w - x, y) if flip else (x, y)


def kamandalu_img(Hh=220, water=True):
    w = int(Hh * 1.2)
    cv = Cv(w, Hh)
    cx = w / 2
    cv.arc(cx + Hh * .05, Hh * .38, Hh * .4, Hh * .3, 180, 360, hx('#6B4226'), Hh * .05)
    cv.ell(cx, Hh * .65, Hh * .36, Hh * .32, hx('#8A5A2A'))
    cv.ell(cx - Hh * .1, Hh * .58, Hh * .12, Hh * .08, hx('#B0804A'))
    cv.poly([(cx + Hh * .3, Hh * .55), (cx + Hh * .55, Hh * .38), (cx + Hh * .52, Hh * .45), (cx + Hh * .33, Hh * .68)], hx('#8A5A2A'))
    cv.ell(cx, Hh * .38, Hh * .2, Hh * .06, hx('#4FA3C4') if water else hx('#3A2410'))
    return cv.out()


def ghada_img(Hh=380):
    w = int(Hh * 1.0)
    cv = Cv(w, Hh)
    cx = w / 2
    cv.ell(cx, Hh * .6, Hh * .44, Hh * .38, hx('#B5532A'))
    cv.ell(cx - Hh * .14, Hh * .5, Hh * .12, Hh * .1, hx('#D9773E'))
    cv.rect(cx - Hh * .2, Hh * .12, cx + Hh * .2, Hh * .28, hx('#B5532A'))
    cv.ell(cx, Hh * .12, Hh * .26, Hh * .07, hx('#8C3A1A'))
    cv.ell(cx, Hh * .12, Hh * .2, Hh * .045, hx('#4FA3C4'))
    for k in (.45, .7):
        cv.arc(cx, Hh * k, Hh * .4, Hh * .08, 0, 180, hx('#F2C94C'), 4)
    return cv.out()


def naav_img(w=720, rishis=7, t=0.0):
    """Wooden boat with a thatched canopy, small rishis and seed sacks."""
    h = int(w * .62)
    cv = Cv(w, h)
    deck = h * .62
    cv.poly([(w * .02, deck - h * .1), (w * .98, deck - h * .14), (w * .84, h * .92), (w * .14, h * .92)], hx('#7A4A22'))
    cv.poly([(w * .06, deck - h * .06), (w * .94, deck - h * .1), (w * .9, deck + h * .02), (w * .1, deck + h * .04)], hx('#9C6232'))
    for k in range(4):
        y = deck + h * (.08 + k * .07)
        cv.line([(w * (.12 + k * .01), y), (w * (.86 - k * .01), y - h * .02)], hx('#5A3416'), 3)
    # canopy
    cv.poly([(w * .3, deck - h * .08), (w * .5, deck - h * .5), (w * .7, deck - h * .1)], hx('#C9A25A'))
    cv.poly([(w * .34, deck - h * .1), (w * .5, deck - h * .44), (w * .66, deck - h * .12)], hx('#A8823E'))
    # rishis (small heads with white beards / shikha)
    rnd = random.Random(5)
    xs = [w * (.14 + i * .72 / max(1, rishis - 1)) for i in range(rishis)]
    for i, x in enumerate(xs):
        if .42 * w < x < .58 * w:
            continue
        y = deck - h * .1 - (i % 2) * 6
        cv.rrect(x - w * .03, y - h * .02, x + w * .03, y + h * .1, 10, hx('#F2E6C8'))
        cv.ell(x, y - h * .06, w * .026, w * .028, hx('#C48A5C'))
        cv.poly([(x - w * .02, y - h * .05), (x + w * .02, y - h * .05), (x, y + h * .02)], hx('#F4F1EA'))
        cv.ell(x, y - h * .1, w * .01, w * .012, hx('#F4F1EA'))
    # seed sacks / herbs
    for x in (w * .44, w * .56):
        cv.ell(x, deck - h * .06, w * .04, h * .06, hx('#D9C089'))
        cv.ell(x, deck - h * .13, w * .02, h * .03, hx('#3F8A4A'))
    cv.line([(w * .95, deck - h * .14), (w * .99, deck - h * .3)], hx('#5A3416'), 6)  # prow post
    return cv.out()


def vasuki_rope(fr, p0, p1, sag=60, t=0.0, width=14):
    """Green serpent-rope between two frame points (drawn per frame)."""
    d = ImageDraw.Draw(fr, 'RGBA')
    pts = []
    for k in range(25):
        q = k / 24
        x = p0[0] + (p1[0] - p0[0]) * q
        y = p0[1] + (p1[1] - p0[1]) * q + math.sin(q * math.pi) * sag + math.sin(q * 12 + t * 4) * 5
        pts.append((x, y))
    d.line(pts, fill=(40, 110, 70, 255), width=width, joint='curve')
    d.line(pts, fill=(90, 170, 100, 255), width=max(2, width // 3), joint='curve')
    hx0, hy0 = pts[-1]
    d.ellipse([hx0 - width * 1.1, hy0 - width * .8, hx0 + width * 1.1, hy0 + width * .8], fill=(40, 110, 70, 255))
    d.ellipse([hx0 + width * .2, hy0 - width * .4, hx0 + width * .5, hy0 - width * .1], fill=(255, 228, 92, 255))


def veda_img(w=200, glow=1.0):
    """Four glowing palm-leaf manuscripts (the Vedas)."""
    h = int(w * .9)
    cv = Cv(w, h)
    if glow > 0:
        cv.ell(w / 2, h / 2, w * .5, h * .5, hx('#FFF1B0', int(90 * glow)))
    for k in range(4):
        y = h * (.25 + k * .15)
        cv.rrect(w * .12, y, w * .88, y + h * .11, 8, hx('#E9D3A0'))
        cv.line([(w * .2, y + h * .055), (w * .8, y + h * .055)], hx('#8A5A2A'), 2)
        cv.ell(w * .5, y + h * .055, w * .025, w * .025, hx('#C0392B'))
    return cv.out()


def hayagriva(Hh=760, angry=True, point=False, veda=False):
    """Asura Hayagriva: dark asura body with a horse head."""
    base = ravana(Hh, angry=angry, point=point, heads=1, skin_col='#4A3A5A', dhoti='#1E1030', cape='#5A1A2C')
    w, h = base.size
    u = Hh / 10.0
    pad = int(Hh * .2)
    cx = w / 2
    cv = Cv(w, h)
    hy = pad + 2.0 * u
    mane = hx('#1A1020')
    head = hx('#5A4A6A')
    # mane behind
    cv.poly([(cx - 1.2 * u, hy - 1.6 * u), (cx + .3 * u, hy - 1.9 * u), (cx + .9 * u, hy + .9 * u), (cx - 1.5 * u, hy + 1.2 * u)], mane)
    # long horse head angled down-right
    cv.poly([(cx - .9 * u, hy - 1.2 * u), (cx + .5 * u, hy - 1.3 * u), (cx + 1.9 * u, hy + .4 * u), (cx + 1.7 * u, hy + 1.0 * u),
             (cx + .9 * u, hy + 1.0 * u), (cx - .8 * u, hy + .4 * u)], head)
    cv.ell(cx + 1.75 * u, hy + .7 * u, .32 * u, .32 * u, hx('#3A2A4A'))  # muzzle
    cv.ell(cx + 1.8 * u, hy + .6 * u, .07 * u, .05 * u, hx('#120A16'))
    cv.poly([(cx - .5 * u, hy - 1.15 * u), (cx - .25 * u, hy - 1.9 * u), (cx, hy - 1.2 * u)], head)  # ears
    cv.poly([(cx + .05 * u, hy - 1.2 * u), (cx + .3 * u, hy - 1.85 * u), (cx + .5 * u, hy - 1.2 * u)], head)
    cv.ell(cx + .35 * u, hy - .45 * u, .17 * u, .12 * u, hx('#FFE45C'))
    cv.ell(cx + .38 * u, hy - .45 * u, .06 * u, .08 * u, hx('#C0182A') if angry else hx('#120A16'))
    cv.line([(cx + .1 * u, hy - .7 * u), (cx + .6 * u, hy - .58 * u)], hx('#120A16'), 4)
    # crown
    cv.poly([(cx - .7 * u, hy - 1.1 * u), (cx - .6 * u, hy - 1.6 * u), (cx - .3 * u, hy - 1.3 * u), (cx - .05 * u, hy - 1.75 * u),
             (cx + .2 * u, hy - 1.25 * u), (cx + .1 * u, hy - 1.05 * u)], hx(GOLD))
    im = base.copy()
    im.alpha_composite(cv.out())
    if veda:
        v = veda_img(int(2.2 * u))
        im.alpha_composite(v, (int(cx - 2.9 * u), int(pad + 4.0 * u)))
    return im


def bg_nadi():
    """Kritamala river at sunrise: banks, trees, lotus, ripples."""
    cv = Cv(W, H)
    cv.vgrad(0, 1050, hx('#FFC98A'), hx('#FFE9C4'))
    _sun(cv, 700, 820, 140, '#FFF3C8')
    _hills(cv, 1000, hx('#9FB07A'), 120, 201)
    for x, hh in ((90, 420), (230, 330), (900, 400), (1010, 300)):
        _tree(cv, x, 1060, hh)
    cv.rect(0, 1050, W, H, hx('#5AA6B8'))
    cv.vgrad(1050, H, hx('#7FC2CC'), hx('#2C6F7E'))
    for i in range(16):
        y = 1080 + i * 50
        for x in range(-40 + (i % 2) * 90, W, 180):
            cv.arc(x + 70, y, 70, 12, 200, 340, hx('#E9F6F8', 120), 4)
    cv.poly([(0, 1050), (0, 1120), (260, 1080), (420, 1050)], hx('#8A6A3A'))
    cv.poly([(1080, 1050), (1080, 1120), (820, 1075), (680, 1050)], hx('#8A6A3A'))
    for x, y in ((140, 1650), (950, 1600)):
        for ang in (-50, -25, 0, 25, 50):
            a = math.radians(ang)
            cv.poly([(x, y), (x + math.sin(a) * 40 - 12, y - math.cos(a) * 44), (x + math.sin(a) * 50, y - math.cos(a) * 60),
                     (x + math.sin(a) * 40 + 12, y - math.cos(a) * 44)], hx('#F7A8C4'))
        cv.ell(x, y + 6, 46, 12, hx('#3F8A4A'))
    _vignette(cv)
    return cv


def bg_sarovar():
    """A big lotus lake at noon surrounded by trees."""
    cv = Cv(W, H)
    cv.vgrad(0, 950, hx('#8CC8EA'), hx('#E6F4FA'))
    _hills(cv, 930, hx('#6E9A5A'), 100, 211)
    for x in range(40, W, 150):
        _tree(cv, x, 980, 260 + (x * 7) % 90)
    cv.rect(0, 960, W, H, hx('#3E8EA8'))
    cv.vgrad(960, H, hx('#5AAAC0'), hx('#1E5A70'))
    for i in range(18):
        y = 990 + i * 52
        for x in range(-40 + (i % 2) * 90, W, 180):
            cv.arc(x + 70, y, 70, 12, 200, 340, hx('#E9F6F8', 110), 4)
    for x, y in ((120, 1500), (300, 1760), (880, 1520), (760, 1780)):
        cv.ell(x, y + 6, 56, 16, hx('#3F8A4A'))
        for ang in (-40, -15, 15, 40):
            a = math.radians(ang)
            cv.poly([(x, y), (x + math.sin(a) * 36 - 11, y - math.cos(a) * 40), (x + math.sin(a) * 46, y - math.cos(a) * 54),
                     (x + math.sin(a) * 36 + 11, y - math.cos(a) * 40)], hx('#F7A8C4'))
    _vignette(cv)
    return cv


def bg_pralaya():
    """The deluge: black-violet storm sky, towering dark waves."""
    cv = Cv(W, H)
    cv.vgrad(0, 1100, hx('#0A0E1E'), hx('#3A3A5A'))
    for x, y, r in ((160, 260, 170), (620, 200, 200), (980, 340, 160), (380, 480, 150), (860, 560, 140)):
        cv.ell(x, y, r * 1.7, r * .6, hx('#2A2A40', 235))
        cv.ell(x + 30, y + 20, r * 1.3, r * .4, hx('#4A4A66', 180))
    cv.rect(0, 1000, W, H, hx('#14304A'))
    cv.vgrad(1000, H, hx('#1E4A66'), hx('#06121E'))
    rnd = random.Random(221)
    for i in range(12):
        y = 1010 + i * 75
        for x in range(-100 + (i % 2) * 120, W + 100, 240):
            a = 60 + rnd.random() * 30
            cv.poly([(x - 120, y + 30), (x - 40, y - a), (x + 20, y - a * .7), (x + 120, y + 30)], hx('#2A5A7A'))
            cv.arc(x - 30, y - a * .6, 60, 30, 200, 320, hx('#C9E2EE', 170), 5)
    _vignette(cv)
    return cv


def bg_gahra():
    """Deep ocean floor: dark teal, light shafts, coral and rocks."""
    cv = Cv(W, H)
    cv.vgrad(0, H, hx('#1E6A80'), hx('#041824'))
    lay = Image.new('RGBA', cv.im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for x in (220, 520, 840):
        ld.polygon([((x - 60) * S, 0), ((x + 60) * S, 0), ((x + 220) * S, 1400 * S), ((x - 40) * S, 1400 * S)], fill=hx('#9FE0EE', 38))
    cv.im.alpha_composite(lay)
    _hills(cv, 1500, hx('#0A2A30'), 160, 231)
    for x in (120, 300, 760, 960):
        for k in range(4):
            a = -0.6 + k * .4
            cv.line([(x, 1520), (x + math.sin(a) * 120, 1520 - math.cos(a) * 180)], hx('#C2405A'), 10)
    rnd = random.Random(232)
    for _ in range(40):
        x, y, r = rnd.random() * W, rnd.random() * 1400, 3 + rnd.random() * 9
        cv.ell(x, y, r, r, hx('#CFF4FA', 90), hx('#E9FCFF', 140), 1.5)
    _vignette(cv)
    return cv


BACKGROUNDS.update({'nadi': bg_nadi, 'sarovar': bg_sarovar, 'pralaya': bg_pralaya, 'gahra': bg_gahra})


# ---------------------------------------------------------------- Bal Hanuman aur Surya (added for story 007)
SKIN['anjana'] = '#C98E5E'
SAREE['anjana'] = ('#E07A1F', '#2E8B57', '#B85F12', '#1F6B42', '#F2C94C')
JEWEL = JEWEL + ('anjana',)


def tinted(fn, kind, skin, *a, **kw):
    """Call a person-like sprite function with SKIN[kind] temporarily replaced."""
    old = SKIN[kind]
    SKIN[kind] = skin
    try:
        return fn(*a, **kw)
    finally:
        SKIN[kind] = old


def _recolor(im, src, dst, tol=10):
    a = np.array(im).astype(int)
    s = np.array(hx(src)[:3])
    m = (np.abs(a[..., :3] - s).sum(-1) < tol * 3) & (a[..., 3] > 0)
    a[m, :3] = hx(dst)[:3]
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def brahma(Hh=760, bless=True):
    """Brahma ji: golden-rose skin, white beard, gold kirit, saffron dhoti (raja figure recoloured)."""
    im = tinted(person, 'raja', '#E3A27A', 'raja', Hh, arms=((-1.4, 5.6), (1.6, 3.4)) if bless else None)
    return _recolor(im, '#3A2618', '#F4F1EA', 14)


def surya_dev(Hh=760, bless=True):
    """Surya dev as a devata: warm golden skin (rays drawn behind in the scene)."""
    return tinted(person, 'deva', '#F0A957', 'deva', Hh, arms=((-1.4, 5.6), (1.6, 3.4)) if bless else None)


def vayu_dev(Hh=760, angry=False, namaste=False):
    return tinted(person, 'deva', '#9EC3DE', 'deva', Hh, namaste=namaste, mouth='flat' if angry else 'smile',
                  arms=((-1.5, 5.7), (1.5, 5.7)))


def indra(Hh=760, throw=False):
    """Indra with the vajra raised in the right hand."""
    arms = ((-1.5, 5.6), (2.2, 1.2)) if throw else ((-1.5, 5.6), (1.9, 4.0))
    im = person('deva', Hh, arms=arms, mouth='flat')
    u = Hh / 10.0
    pad = int(Hh * .16)
    hxp = im.width / 2 + arms[1][0] * u
    hyp = pad + arms[1][1] * u
    v = vajra_img(int(2.2 * u))
    im.alpha_composite(v, (int(hxp - v.width / 2), int(max(0, hyp - v.height * .6))))
    return im


def vajra_img(Hh=160, glow_=True):
    w = int(Hh * .55)
    c = Cv(w, Hh)
    cx = w / 2
    g, g2 = hx('#FFE27A'), hx('#C98A1B')
    c.rrect(cx - .07 * Hh, .38 * Hh, cx + .07 * Hh, .62 * Hh, .03 * Hh, g2)
    c.ell(cx, .5 * Hh, .1 * Hh, .07 * Hh, g)
    for sgn in (-1, 1):
        y0 = .5 * Hh + sgn * .12 * Hh
        tip = .5 * Hh + sgn * .5 * Hh
        c.poly([(cx - .05 * Hh, y0), (cx, tip - sgn * .02 * Hh), (cx + .05 * Hh, y0)], g)
        for sx in (-1, 1):
            c.line([(cx, y0), (cx + sx * .22 * Hh, y0 + sgn * .16 * Hh), (cx + sx * .06 * Hh, tip - sgn * .06 * Hh)], g, .035 * Hh)
    return c.out()


def bal_hanuman(Hh=420, pose='stand', eyes='open', mouth='smile', arm_up=False):
    """Little Maruti: chubby, big head, red langot, tail, no crown (a small tuft).
    pose: 'stand' | 'fly' (rotated, arms reaching ahead to the right) | 'lie' (lying on back)."""
    w = int(Hh * 1.2)
    pad = int(Hh * .2)
    c = Cv(w, Hh + pad)
    c.oy = pad
    u = Hh / 10.0
    cx = w / 2 - .4 * u
    skin, face, dark = hx(HSKIN), hx(HFACE), hx('#2A1208')
    # tail
    tp = [(cx + .7 * u, 6.6 * u), (cx + 2.2 * u, 7.2 * u), (cx + 3.1 * u, 6.0 * u), (cx + 3.0 * u, 4.5 * u), (cx + 3.6 * u, 3.7 * u)]
    c.line(tp, skin, .5 * u)
    c.ell(tp[-1][0], tp[-1][1], .34 * u, .34 * u, skin)
    # legs (short, chubby)
    for sgn in (-1, 1):
        fx = cx + sgn * .75 * u
        c.rrect(fx - .45 * u, 7.0 * u, fx + .45 * u, 9.6 * u, .4 * u, skin)
        c.ell(fx + sgn * .1 * u, 9.65 * u, .6 * u, .3 * u, skin)
        c.rect(fx - .47 * u, 8.9 * u, fx + .47 * u, 9.08 * u, hx(GOLD))
    # belly + langot
    c.ell(cx, 6.0 * u, 1.7 * u, 1.6 * u, skin)
    c.ell(cx, 6.1 * u, 1.1 * u, 1.0 * u, face)
    c.poly([(cx - 1.5 * u, 6.9 * u), (cx + 1.5 * u, 6.9 * u), (cx + 1.2 * u, 7.9 * u), (cx - 1.2 * u, 7.9 * u)], hx('#C8202E'))
    c.rect(cx - 1.5 * u, 6.8 * u, cx + 1.5 * u, 7.05 * u, hx(GOLD))
    c.line([(cx - .9 * u, 4.6 * u), (cx, 5.2 * u), (cx + .9 * u, 4.6 * u)], hx(GOLD), 5)
    c.ell(cx, 5.25 * u, .15 * u, .15 * u, hx('#E63946'))
    # arms
    if pose == 'fly' or arm_up:
        aL, aR = (cx + 1.0 * u, 2.2 * u), (cx + 2.3 * u, 2.8 * u)
    else:
        aL, aR = (cx - 2.2 * u, 6.2 * u), (cx + 2.2 * u, 6.2 * u)
    for sh, hd in (((cx - 1.2 * u, 4.9 * u), aL), ((cx + 1.2 * u, 4.9 * u), aR)):
        c.line([sh, hd], skin, .6 * u)
        c.ell(hd[0], hd[1], .4 * u, .4 * u, skin)
        c.rect(sh[0] + (hd[0] - sh[0]) * .75 - .28 * u, sh[1] + (hd[1] - sh[1]) * .75 - .1 * u,
               sh[0] + (hd[0] - sh[0]) * .75 + .28 * u, sh[1] + (hd[1] - sh[1]) * .75 + .1 * u, hx(GOLD))
    # head (big)
    hcx, hcy, hr = cx, 2.7 * u, 1.75 * u
    for sg in (-1, 1):
        c.ell(hcx + sg * hr, hcy + .1 * u, .42 * u, .5 * u, skin)
        c.ell(hcx + sg * hr, hcy + .1 * u, .24 * u, .3 * u, face)
    c.ell(hcx, hcy, hr, hr, skin)
    c.ell(hcx, hcy + .2 * u, hr * .8, hr * .7, face)
    c.ell(hcx, hcy + .85 * u, hr * .58, hr * .38, face)
    c.ell(hcx, hcy + .5 * u, .2 * u, .12 * u, hx('#7A3A1A'))
    for sg in (-1, 1):  # cheeks
        c.ell(hcx + sg * .95 * u, hcy + .65 * u, .28 * u, .18 * u, hx('#F2A08A', 150))
    ey = hcy - .05 * u
    for sg in (-1, 1):
        ex = hcx + sg * .58 * u
        if eyes == 'open':
            c.ell(ex, ey, .24 * u, .26 * u, hx('#FFFFFF'))
            c.ell(ex + .03 * u, ey + .02 * u, .14 * u, .17 * u, dark)
            c.ell(ex + .07 * u, ey - .06 * u, .05 * u, .05 * u, hx('#FFFFFF'))
        else:
            c.arc(ex, ey, .22 * u, .14 * u, 200, 340, dark, 3)
    if mouth == 'smile':
        c.arc(hcx, hcy + .85 * u, .45 * u, .28 * u, 15, 165, hx('#7A2A2A'), 4)
    elif mouth == 'open':
        c.ell(hcx, hcy + 1.0 * u, .25 * u, .2 * u, hx('#7A2A2A'))
    else:
        c.line([(hcx - .2 * u, hcy + 1.0 * u), (hcx + .2 * u, hcy + 1.0 * u)], hx('#7A2A2A'), 3)
    c.line([(hcx, hcy - .9 * u), (hcx, hcy - .5 * u)], hx('#E63946'), 5)
    # tuft
    c.poly([(hcx - .3 * u, hcy - hr + .2 * u), (hcx - .05 * u, hcy - hr - .55 * u), (hcx + .1 * u, hcy - hr + .1 * u),
            (hcx + .45 * u, hcy - hr - .35 * u), (hcx + .35 * u, hcy - hr + .3 * u)], hx('#C85E1C'))
    im = c.out()
    if pose == 'fly':
        im = im.rotate(-62, expand=True, resample=Image.BICUBIC)
    elif pose == 'lie':
        im = im.rotate(90, expand=True, resample=Image.BICUBIC)
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def surya_disc(r=200, col='#FF7A2E', face=True, t=0.0):
    """Rising sun with rays and a gentle calm face."""
    n = int(r * 3.4)
    c = Cv(n, n)
    cx = cy = n / 2
    for k in range(16):
        a = k * math.pi / 8 + t * .25
        r0, r1 = r * 1.08, r * (1.5 if k % 2 == 0 else 1.32)
        c.poly([(cx + math.cos(a - .09) * r0, cy + math.sin(a - .09) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
                (cx + math.cos(a + .09) * r0, cy + math.sin(a + .09) * r0)], hx('#FFC24A', 220))
    c.ell(cx, cy, r * 1.06, r * 1.06, hx('#FFB03A'))
    c.ell(cx, cy, r, r, hx(col))
    c.ell(cx - r * .15, cy - r * .15, r * .72, r * .72, hx('#FF9548'))
    if face:
        dk = hx('#8A3A10')
        for sg in (-1, 1):
            c.arc(cx + sg * r * .32, cy - r * .05, r * .14, r * .09, 200, 340, dk, max(2, r * .03))
        c.arc(cx, cy + r * .25, r * .22, r * .12, 20, 160, dk, max(2, r * .03))
        c.line([(cx, cy - r * .42), (cx, cy - r * .22)], hx('#E63946'), max(2, r * .04))
    return c.out()


def airavat(w=640, flip=False):
    """White elephant (side view facing left) with gold-red caparison."""
    Hh = int(w * .75)
    c = Cv(w, Hh)
    wh, sh = hx('#F3F1EE'), hx('#D9D6D2')
    # legs
    for x in (.3, .42, .68, .8):
        c.rrect(w * x - w * .05, Hh * .55, w * x + w * .05, Hh * .98, w * .03, sh if x in (.42, .8) else wh)
    c.ell(w * .58, Hh * .5, w * .32, Hh * .26, wh)  # body
    c.ell(w * .9, Hh * .45, w * .03, Hh * .12, wh)  # tail stub
    # caparison
    c.poly([(w * .38, Hh * .3), (w * .74, Hh * .3), (w * .78, Hh * .62), (w * .34, Hh * .62)], hx('#B5262F'))
    c.rect(w * .34, Hh * .58, w * .78, Hh * .63, hx(GOLD))
    for k in range(5):
        c.ell(w * (.4 + k * .085), Hh * .64, w * .014, w * .014, hx(GOLD))
    # head, ear, trunk, tusk
    c.ell(w * .25, Hh * .36, w * .16, Hh * .2, wh)
    c.ell(w * .33, Hh * .38, w * .1, Hh * .17, sh)
    c.line([(w * .14, Hh * .42), (w * .09, Hh * .62), (w * .08, Hh * .82), (w * .12, Hh * .9)], wh, w * .06)
    c.line([(w * .18, Hh * .5), (w * .1, Hh * .57)], hx('#FFF8E0'), w * .022)
    c.ell(w * .2, Hh * .3, w * .015, w * .015, hx('#2A1208'))
    c.poly([(w * .18, Hh * .18), (w * .3, Hh * .16), (w * .27, Hh * .24), (w * .2, Hh * .25)], hx(GOLD))  # forehead gold
    im = c.out()
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def rahu_head(Hh=420):
    """Rahu: just a crowned dark head (from the asura sprite), floating."""
    im = asura(int(Hh * 3.2), col='#4B3F5E', dhoti='#22182E', cape='#22182E', angry=True)
    bb = im.getbbox()
    im = im.crop(bb)
    return im.crop((int(im.width * .22), 0, int(im.width * .78), int(im.height * .3)))


def bg_bhor():
    """Pre-dawn horizon: violet-to-coral sky, forest silhouette, Anjana's hill (sun drawn per frame)."""
    cv = Cv(W, H)
    cv.vgrad(0, 1100, hx('#3B2A6B'), hx('#FF9A5A'))
    cv.vgrad(1100, H, hx('#FFB36B'), hx('#3E6B3A'))
    _hills(cv, 1180, hx('#6B4A7A'), 90, 3)
    _hills(cv, 1300, hx('#3E5A3A'), 70, 8)
    for x in range(-20, 1100, 110):
        _tree(cv, x, 1360 + (x % 3) * 20, 300 + (x % 5) * 30, trunk='#3A2618', leaf='#2E4A2A', leaf2='#3F5F35')
    cv.vgrad(1380, H, hx('#3E6B3A'), hx('#22401F'))
    _sparkles(cv, 26, 5, 80, 600)
    _vignette(cv)
    return cv


def bg_antariksh():
    """High sky at sunrise: golden clouds, earth curving far below."""
    cv = Cv(W, H)
    cv.vgrad(0, H, hx('#FF8A3D'), hx('#FFE3A8'))
    rnd = random.Random(4)
    for k in range(9):
        x, y, s = rnd.random() * 1080, 300 + rnd.random() * 1300, 80 + rnd.random() * 120
        for dx in (-1, 0, 1):
            cv.ell(x + dx * s * .8, y + (0 if dx == 0 else s * .25), s * (1.0 if dx == 0 else .7), s * .55 * (1.0 if dx == 0 else .7), hx('#FFF4DC', 200))
    cv.ell(540, 2500, 1400, 820, hx('#4E8B5A'))
    cv.ell(540, 2500, 1400, 820, None, hx('#9ED0FF', 160), 18)
    _vignette(cv)
    return cv


BACKGROUNDS.update({'bhor': bg_bhor, 'antariksh': bg_antariksh})


# ------------------------------------------------------------ 008 वैकुंठ चतुर्दशी: kamal, shivling, bilva, Kashi mandir/bhor
def lotus_img(r=60, open_=1.0, col='#F48FB1', col2='#E8608C'):
    """Pink lotus seen from the side: two rows of petals + gold centre. Bottom-centre = stem top."""
    cv = Cv(int(r * 2.8), int(r * 2.2))
    cx, by = r * 1.4, r * 1.9
    for ang, sc, c in ((-70, .8, col2), (70, .8, col2), (-42, .95, col), (42, .95, col), (-18, 1.0, col2), (18, 1.0, col2), (0, 1.05, col)):
        a = math.radians(ang * (.55 + .45 * open_))
        L = r * 1.5 * sc
        tx, ty = cx + math.sin(a) * L, by - math.cos(a) * L
        nx, ny = math.cos(a) * r * .38, math.sin(a) * r * .38
        mx, my = cx + math.sin(a) * L * .5, by - math.cos(a) * L * .5
        cv.poly([(cx, by), (mx - nx, my - ny), (tx, ty), (mx + nx, my + ny)], hx(c))
        cv.line([(cx, by), (cx + math.sin(a) * L * .8, by - math.cos(a) * L * .8)], hx('#FFFFFF', 70), max(1, r * .04))
    cv.ell(cx, by - r * .12, r * .32, r * .14, hx(GOLD))
    cv.ell(cx, by + r * .05, r * .75, r * .16, hx('#3F8A4A'))
    return cv.out()


def thali_img(w=420, n=12, seed=3):
    """Golden plate heaped with n lotuses (n=0 -> empty plate)."""
    h = int(w * .75)
    cv = Cv(w, h)
    im = None
    cv.ell(w / 2, h * .82, w * .48, w * .12, hx(GOLD2))
    cv.ell(w / 2, h * .79, w * .44, w * .1, hx(GOLD))
    cv.ell(w / 2, h * .79, w * .32, w * .065, hx('#FFE08A'))
    im = cv.out()
    rnd = random.Random(seed)
    pos = []
    rows = [(0.78, 5), (0.66, 4), (0.55, 3), (0.45, 2), (0.36, 1)]
    for yy, k in rows:
        for j in range(k):
            pos.append((w / 2 + (j - (k - 1) / 2) * w * .16 + rnd.uniform(-6, 6), h * yy))
    for i, (x, y) in enumerate(pos[:n]):
        lt = lotus_img(int(w * .085), 1.0, '#F48FB1' if i % 2 else '#F7A8C4')
        im.alpha_composite(lt, (int(x - lt.width / 2), int(y - lt.height * .85)))
    return im


def shivling_img(Hh=360, glow_=0.0, bel=True):
    """Shivling on yoni-peetha, tripundra, a few bilva leaves and a flower."""
    w = int(Hh * 1.5)
    cv = Cv(w, Hh)
    cx = w / 2
    stone, stone2 = hx('#3E4656'), hx('#2A303C')
    # peetha (base) + spout
    cv.rrect(cx - Hh * .55, Hh * .78, cx + Hh * .55, Hh * .98, 18, stone2)
    cv.ell(cx, Hh * .68, Hh * .62, Hh * .13, stone)
    cv.poly([(cx + Hh * .5, Hh * .64), (cx + Hh * .72, Hh * .66), (cx + Hh * .74, Hh * .72), (cx + Hh * .5, Hh * .76)], stone)
    cv.rect(cx - Hh * .5, Hh * .68, cx + Hh * .5, Hh * .8, stone)
    cv.ell(cx, Hh * .8, Hh * .5, Hh * .08, stone2)
    # linga
    cv.rect(cx - Hh * .22, Hh * .25, cx + Hh * .22, Hh * .68, hx('#4A5468'))
    cv.ell(cx, Hh * .25, Hh * .22, Hh * .2, hx('#4A5468'))
    cv.rect(cx + Hh * .1, Hh * .2, cx + Hh * .16, Hh * .66, hx('#6A748A'))
    for k in range(3):  # tripundra
        y = Hh * (.33 + k * .045)
        cv.line([(cx - Hh * .16, y), (cx + Hh * .16, y)], hx('#F2EDE2'), max(2, Hh * .018))
    cv.ell(cx, Hh * .38, Hh * .03, Hh * .03, hx('#D62828'))
    if bel:
        for dx in (-.32, .3):
            bx, by = cx + Hh * dx, Hh * .68
            for a in (-40, 0, 40):
                ar = math.radians(a)
                cv.ell(bx + math.sin(ar) * Hh * .06, by - math.cos(ar) * Hh * .06, Hh * .04, Hh * .065, hx('#3F8A3A'))
    cv.ell(cx, Hh * .14, Hh * .06, Hh * .04, hx('#F59E0B'))
    return cv.out()


def bilva_img(Hh=160):
    """Bilva (bel) patra: three leaves on a stalk."""
    cv = Cv(int(Hh * 1.1), Hh)
    cx = Hh * .55
    cv.line([(cx, Hh), (cx, Hh * .55)], hx('#4A6B2A'), Hh * .04)
    for a, L in ((-55, .42), (0, .5), (55, .42)):
        ar = math.radians(a)
        ex, ey = cx + math.sin(ar) * Hh * L, Hh * .55 - math.cos(ar) * Hh * L
        mx, my = (cx + ex) / 2, (Hh * .55 + ey) / 2
        nx, ny = math.cos(ar) * Hh * .11, math.sin(ar) * Hh * .11
        cv.poly([(cx, Hh * .55), (mx - nx, my - ny), (ex, ey), (mx + nx, my + ny)], hx('#3F8A3A'))
        cv.line([(cx, Hh * .55), (ex, ey)], hx('#7FC06A'), max(1, Hh * .012))
    return cv.out()


def bg_kashi_mandir():
    """Kashi Vishwanath garbhagriha: carved arch, hanging bells, lamps, warm saffron glow."""
    cv = Cv(W, H)
    cv.vgrad(0, H, hx('#6A2412'), hx('#2A0A06'))
    for x in (60, 1020):
        cv.rect(x - 50, 300, x + 50, 1300, hx('#8A4A1E'))
        for y in range(340, 1300, 90):
            cv.rect(x - 50, y, x + 50, y + 12, hx(GOLD2))
    cv.rrect(170, 380, 910, 1320, 370, hx('#A0581E'))
    cv.rrect(210, 420, 870, 1310, 330, hx('#4A1A0C'))
    _sun(cv, 540, 900, 260, '#FFC56A')
    for k in range(13):  # carved arch beads
        a = math.pi + k / 12 * math.pi
        cv.ell(540 + math.cos(a) * 350, 750 + math.sin(a) * 350, 16, 16, hx(GOLD))
    for x in (300, 780):  # bells
        cv.line([(x, 250), (x, 470)], hx(GOLD2), 5)
        cv.poly([(x - 34, 540), (x - 22, 470), (x + 22, 470), (x + 34, 540)], hx(GOLD))
        cv.ell(x, 545, 10, 10, hx(GOLD2))
    for k in range(16):
        x = 40 + k * 66
        cv.ell(x, 300 + math.sin(k / 15 * math.pi) * 50, 20, 20, hx('#F59E0B' if k % 2 else '#F97316'))
    cv.rect(0, 1300, W, H, hx('#5A2A12'))
    cv.vgrad(1300, H, hx('#8A4A22'), hx('#2A1006'))
    for x in range(0, W, 120):
        cv.line([(x, 1300), (x - 140, H)], hx('#6A341A'), 4)
    _sparkles(cv, 18, 181, 300, 1100, '#FFD08A')
    _vignette(cv)
    return cv


def bg_kashi_bhor():
    """Kashi ghats at golden dawn: sunrise over Ganga, temple spires, boats."""
    cv = Cv(W, H)
    cv.vgrad(0, 1050, hx('#F7B267'), hx('#FFE8B8'))
    _sun(cv, 300, 640, 120, '#FFF3C4')
    for x, h_, w_ in ((640, 520, 170), (820, 420, 160), (990, 360, 140), (470, 340, 150)):
        base = 1050
        cv.rect(x - w_ / 2, base - h_, x + w_ / 2, base, hx('#C47A3E'))
        cv.poly([(x - w_ * .35, base - h_), (x, base - h_ - w_ * .9), (x + w_ * .35, base - h_)], hx('#E09A55'))
        cv.line([(x, base - h_ - w_ * .9), (x, base - h_ - w_ * 1.12)], hx(GOLD2), 4)
        cv.poly([(x, base - h_ - w_ * 1.12), (x + 32, base - h_ - w_ * 1.05), (x, base - h_ - w_ * .99)], hx('#E8461E'))
        for yy in range(base - h_ + 40, base - 20, 80):
            cv.rect(x - 16, yy, x + 16, yy + 40, hx('#7A3A1A'))
    for k in range(6):
        y = 1050 + k * 36
        cv.rect(0, y, W, y + 36, hx('#B07A4A' if k % 2 else '#9A6238'))
    cv.vgrad(1266, H, hx('#F2C58A'), hx('#8A5A3A'))
    cv.rect(0, 1266, W, 1272, hx('#FFE8B8'))
    for i in range(14):
        y = 1300 + i * 44
        for x in range(-40 + (i % 2) * 90, W, 180):
            cv.arc(x + 70, y, 70, 12, 200, 340, hx('#FFF1D0', 120), 3)
    cv.poly([(80, 1420), (300, 1420), (270, 1460), (110, 1460)], hx('#5A3420'))
    cv.line([(190, 1420), (190, 1330)], hx('#5A3420'), 5)
    _vignette(cv)
    return cv


BACKGROUNDS.update({'kashi_mandir': bg_kashi_mandir, 'kashi_bhor': bg_kashi_bhor})
