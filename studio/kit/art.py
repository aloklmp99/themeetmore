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
        if kind in ('krishna', 'vishnu') and not namaste:
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
    if kind in ('krishna', 'vishnu'):
        gc, gd = hx(PITAM), hx('#D9A41A')
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
    if kind in ('krishna', 'vishnu'):
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

    if kind in ('krishna', 'vishnu'):
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
        if kind == 'vishnu':
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
    if kind in ('krishna', 'vishnu'):
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


def vishnu(Hh=760, eyes='open', mouth='smile', namaste=False, bless=False, t=0.0, halo=True):
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
    ch = chakra_img(int(.55 * u), t)
    im.alpha_composite(ch, (int(cx + 2.25 * u - ch.width / 2), int(pad + 1.9 * u - .55 * u - ch.height / 2)))
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


def bg_kailash():
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


BACKGROUNDS.update({'kailash': bg_kailash, 'aakash': bg_aakash, 'jungle': bg_jungle})


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
