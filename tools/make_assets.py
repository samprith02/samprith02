#!/usr/bin/env python3
"""Generate the animated SVGs that README.md shows.

Run from the repo root:   python tools/make_assets.py

Every SVG is self-contained: no external fonts, scripts or images, because
GitHub serves README images through a proxy that blocks outside requests and
never runs JavaScript. Motion is plain CSS keyframes plus a little SMIL, and
every file has a prefers-reduced-motion fallback that shows a still frame.
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"

SANS = "ui-sans-serif,system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

BG, EDGE, CELL, PANEL = "#0a0d12", "#1c2430", "#131a23", "#0e131a"
TEXT, MUTED, DIM = "#e6edf3", "#8b98a9", "#4d5967"
CYAN, GREEN, AMBER, RED, VIOLET, PINK = (
    "#22d3ee", "#3ddc97", "#f59f00", "#ff5f56", "#a78bfa", "#f472b6")

# Inferno-like ramp: cold purple -> orange -> hot white. Reads well on near-black.
HEAT = [(0.0, "#2a1b3d"), (0.25, "#6a1f5c"), (0.45, "#b0304f"), (0.62, "#e8590c"),
        (0.8, "#f59f00"), (0.92, "#ffd43b"), (1.0, "#fff3bf")]

BASE_CSS = (
    f".sans{{font-family:{SANS}}}.mono{{font-family:{MONO}}}"
    ".blink{animation:blink 1.1s steps(1,end) infinite}"
    "@keyframes blink{50%{opacity:0}}"
)


def heat(v):
    v = max(0.0, min(1.0, v))
    for (a, ca), (b, cb) in zip(HEAT, HEAT[1:]):
        if v <= b:
            t = (v - a) / (b - a)
            rgb = [round(int(ca[i:i + 2], 16) * (1 - t) + int(cb[i:i + 2], 16) * t)
                   for i in (1, 3, 5)]
            return "#" + "".join(f"{c:02x}" for c in rgb)
    return HEAT[-1][1]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=12, fill=MUTED, font="mono", weight=None, anchor=None,
         ls=None, cls="", extra=""):
    a = [f'x="{x}"', f'y="{y}"', f'class="{(font + " " + cls).strip()}"',
         f'font-size="{size}"', f'fill="{fill}"']
    if weight:
        a.append(f'font-weight="{weight}"')
    if anchor:
        a.append(f'text-anchor="{anchor}"')
    if ls:
        a.append(f'letter-spacing="{ls}"')
    return f'<text {" ".join(a)} {extra}>{s}</text>'


def appear(name, on, off, period, fade=0.12):
    """Keyframes: hidden until `on` seconds, shown until `off`, within `period`."""
    p = lambda t: f"{max(0.0, min(100.0, t / period * 100)):.2f}%"
    return (f"@keyframes {name}{{0%,{p(on)}{{opacity:0}}{p(on + fade)},{p(off)}{{opacity:1}}"
            f"{p(off + fade)},100%{{opacity:0}}}}")


def svg(w, h, title, desc, css, body, reduced):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
        f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        f'<style>{BASE_CSS}{css}'
        f'@media (prefers-reduced-motion:reduce){{{reduced}}}</style>'
        f'<rect width="{w}" height="{h}" rx="14" fill="{BG}"/>'
        f'{body}'
        # Border last, so nothing drawn above can paint over it.
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="none" '
        f'stroke="{EDGE}"/></svg>'
    )


def typer(x, y, s, pitch, period, start, type_s, name, size, hold_until=None, erase_s=0.5):
    """Typewriter effect that does not depend on which monospace font loads.

    textLength pins the line to n * pitch, so a background-coloured cover can
    step right exactly one character at a time, with the cursor riding its edge.
    With hold_until=None the line stays typed until the period restarts.
    Returns (css, svg, width).
    """
    n, w = len(s), len(s) * pitch
    p = lambda t: f"{t / period * 100:.2f}%"
    if hold_until is None:
        tail = f"{p(type_s)},100%{{transform:translateX({w:.1f}px)}}"
    else:
        tail = (f"{p(type_s)}{{transform:translateX({w:.1f}px)}}"
                f"{p(hold_until)}{{transform:translateX({w:.1f}px);"
                f"animation-timing-function:steps({n},end)}}"
                f"{p(hold_until + erase_s)},100%{{transform:translateX(0)}}")
    css = (
        f"@keyframes {name}{{0%{{transform:translateX(0);animation-timing-function:steps({n},end)}}"
        f"{tail}}}"
        f".{name}{{animation:{name} {period}s infinite;animation-delay:{start}s}}"
    )
    body = (
        f'<text x="{x}" y="{y}" class="mono" font-size="{size}" fill="{TEXT}" '
        f'textLength="{w:.1f}" lengthAdjust="spacing" xml:space="preserve">{esc(s)}</text>'
        f'<rect class="{name}" x="{x - 1}" y="{y - size}" width="{w + pitch + 4:.1f}" '
        f'height="{size + 8}" fill="{BG}"/>'
        f'<g class="{name}"><rect class="blink" x="{x}" y="{y - size + 2}" '
        f'width="{pitch * 0.9:.1f}" height="{size + 1}" fill="{CYAN}"/></g>'
    )
    return css, body, w


def chip(x, y, label):
    w = len(label) * 6.6 + 16
    return (f'<rect x="{x}" y="{y}" width="{w:.1f}" height="22" rx="11" fill="#111821" '
            f'stroke="#223042"/>'
            + text(x + w / 2, y + 15, esc(label), 11, MUTED, anchor="middle")), w


def pulse(x1, y1, x2, y2, start, travel, period, r=2.6, color=CYAN):
    """A dot that runs x1,y1 -> x2,y2 once per period (SMIL, works in <img>)."""
    t = travel / period
    return (
        f'<circle r="{r}" fill="{color}" opacity="0">'
        f'<animateMotion path="M{x1},{y1} L{x2},{y2}" dur="{period}s" begin="{start}s" '
        f'repeatCount="indefinite" calcMode="linear" keyPoints="0;1;1" '
        f'keyTimes="0;{t:.4f};1"/>'
        f'<animate attributeName="opacity" values="0;1;1;0;0" '
        f'keyTimes="0;0.005;{t:.4f};{t + 0.01:.4f};1" dur="{period}s" begin="{start}s" '
        f'repeatCount="indefinite"/></circle>'
    )


def crc16_ccitt(data: bytes) -> int:
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF. Check value for b"123456789" is 0x29B1."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return crc


# --------------------------------------------------------------------------- hero
def hero():
    W, H = 1000, 340
    X0, Y0, P, COLS, ROWS = 20, 52, 10, 96, 14   # the real lobby matrix is 14 x 96
    T, STEP = 7.5, 0.42                           # walk cycle, seconds per footfall
    LINE_X = X0 + 65 * P
    rnd = random.Random(7)
    # One footprint, heel on the left, toes on the right; rows are outer/middle/inner.
    FOOT = [[.45, .6, .5, .5, .65, .35],
            [.8, 1.0, .55, .6, .95, .7],
            [.4, .55, 0, .15, .85, .8]]

    css = (
        f".warm,.hot,.noise,.flash,.slot{{opacity:0}}"
        f".warm{{animation:warm {T}s linear infinite}}"
        f".hot{{animation:hot {T}s linear infinite}}"
        f"@keyframes hot{{0%{{opacity:0}}1.5%,6%{{opacity:1}}11%,100%{{opacity:0}}}}"
        f"@keyframes warm{{0%{{opacity:0}}2%{{opacity:1}}9%{{opacity:.9}}24%,100%{{opacity:0}}}}"
        ".noise{animation:noise 3s ease-in-out infinite}"
        "@keyframes noise{50%{opacity:.75}}"
        f".flash{{animation:flash {T}s linear infinite;animation-delay:{8 * STEP:.2f}s}}"
        "@keyframes flash{0%{opacity:0}1.5%,22%{opacity:1}26%,100%{opacity:0}}"
        f".line{{stroke-opacity:.35;animation:line {T}s linear infinite;"
        f"animation-delay:{8 * STEP:.2f}s}}"
        "@keyframes line{0%,22%{stroke-opacity:1}30%,100%{stroke-opacity:.35}}"
        ".live{animation:live 1.6s ease-in-out infinite}"
        "@keyframes live{50%{opacity:.25}}"
    )
    reduced = ("*{animation:none!important}"
               ".static,.flash{opacity:1!important}.line{stroke-opacity:1!important}")

    b = [f'<defs><pattern id="cell" x="{X0}" y="{Y0}" width="{P}" height="{P}" '
         f'patternUnits="userSpaceOnUse"><rect x="1" y="1" width="8" height="8" rx="1.6" '
         f'fill="{CELL}"/></pattern></defs>']

    # status bar
    b.append(f'<circle class="live" cx="28" cy="32" r="4" fill="{RED}"/>')
    b.append(text(40, 36, f'<tspan fill="{TEXT}" font-weight="700">LIVE</tspan>'
                          '   tk://lobby-matrix   14 × 96 = 1,344 cells', 12, MUTED,
                  extra='xml:space="preserve"'))
    b.append(text(W - 20, 36, f'30 FPS  ·  15 ms end-to-end  ·  CRC16 '
                              f'<tspan fill="{GREEN}" font-weight="700">OK</tspan>',
                  12, MUTED, anchor="end", extra='xml:space="preserve"'))

    # the mat
    b.append(f'<rect x="{X0}" y="{Y0}" width="{COLS * P}" height="{ROWS * P}" fill="url(#cell)"/>')
    for _ in range(46):   # sensor noise floor, flickering faintly
        c, r = rnd.randrange(COLS), rnd.randrange(ROWS)
        b.append(f'<rect class="noise" x="{X0 + c * P + 1}" y="{Y0 + r * P + 1}" width="8" '
                 f'height="8" rx="1.6" fill="{heat(rnd.uniform(.05, .22))}" '
                 f'style="animation-duration:{rnd.uniform(2.2, 4.5):.2f}s;'
                 f'animation-delay:-{rnd.uniform(0, 4):.2f}s"/>')

    for i in range(12):   # a raider walking left to right, alternating feet
        c0 = 2 + 8 * i
        rows = [3, 4, 5] if i % 2 == 0 else [10, 9, 8]   # outer, middle, inner
        hot, warm = [], []
        for k, row in enumerate(rows):
            for j, v in enumerate(FOOT[k]):
                if v <= 0:
                    continue
                v = v + rnd.uniform(-.08, .08)
                xy = f'x="{X0 + (c0 + j) * P + 1}" y="{Y0 + row * P + 1}"'
                hot.append(f'<rect {xy} width="8" height="8" rx="1.6" fill="{heat(v)}"/>')
                warm.append(f'<rect {xy} width="8" height="8" rx="1.6" fill="{heat(v * .5)}"/>')
        d = f"animation-delay:{i * STEP:.2f}s"
        b.append(f'<g class="warm{" static" if 5 <= i <= 8 else ""}" style="{d}">{"".join(warm)}</g>')
        b.append(f'<g class="hot{" static" if 7 <= i <= 8 else ""}" style="{d}">{"".join(hot)}</g>')

    # the line and its call
    b.append(f'<line class="line" x1="{LINE_X}" y1="{Y0 - 4}" x2="{LINE_X}" '
             f'y2="{Y0 + ROWS * P + 4}" stroke="{CYAN}" stroke-width="2" stroke-dasharray="4 4"/>')
    b.append(f'<g class="flash"><rect x="{LINE_X + 8}" y="{Y0 + 3}" width="162" height="20" '
             f'rx="5" fill="{BG}" stroke="{CYAN}"/>'
             + text(LINE_X + 18, Y0 + 17, "▲ LINE CROSS DETECTED", 11, CYAN, weight="700")
             + '</g>')
    b.append(text(LINE_X, Y0 + ROWS * P + 18, "LINE", 10, CYAN, anchor="middle", ls="1.5"))
    b.append(text(X0, Y0 + ROWS * P + 18, "heat = pressure · each cell is one sensor", 10, DIM))

    # who
    b.append(text(X0 - 2, 268, "Samprith C Amin", 50, TEXT, font="sans", weight="800",
                  ls="-1"))
    b.append(text(W - 20, 240, "Co-Founder &amp; CTO · Vyanika Innovations", 15, TEXT,
                  font="sans", weight="600", anchor="end"))
    b.append(text(W - 20, 262, "B.E. AI &amp; ML · MITE · class of 2027", 12, MUTED,
                  anchor="end"))
    b.append(text(W - 20, 280, "Mangaluru, India", 12, MUTED, anchor="end"))

    lines = [
        "building Tech Kabaddi: sensor-based kabaddi officiating",
        "from embedded C firmware to FastAPI to the browser",
        "multi-agent LLM systems, MCP servers, federated learning",
        "patent filed · NAIN-funded · 1st of 130 teams",
    ]
    slot = 5.0
    period = slot * len(lines)
    css += (f".slot{{animation:slot {period}s infinite}}"
            f"@keyframes slot{{0%,{slot / period * 100 - .05:.2f}%{{opacity:1}}"
            f"{slot / period * 100:.2f}%,100%{{opacity:0}}}}")
    b.append(text(X0, 316, "›", 20, CYAN, weight="700"))
    for idx, s in enumerate(lines):
        c, body, w = typer(44, 316, s, 10.8, period, idx * slot, 1.6, f"ty{idx}", 18,
                           hold_until=4.1, erase_s=0.55)
        css += c
        if idx == 0:
            reduced += (f".s0{{opacity:1!important}}"
                        f".ty0{{transform:translateX({w:.1f}px)!important}}")
        b.append(f'<g class="slot s{idx}" style="animation-delay:{idx * slot}s">{body}</g>')

    return svg(W, H, "Samprith C Amin",
               "A live pressure-sensor heatmap: footprints walk across a 14 by 96 cell mat "
               "and a line cross is detected. Samprith C Amin, Co-Founder and CTO of "
               "Vyanika Innovations, B.E. AI and ML at MITE, Mangaluru.",
               css, "".join(b), reduced)


# --------------------------------------------------------------------------- boot
def boot():
    W, H = 1000, 322
    period = 14.0
    css, reduced = "", "*{animation:none!important}.ln{opacity:1!important}"
    b = [f'<rect x="1" y="1" width="{W - 2}" height="36" rx="13" fill="#10161e"/>',
         f'<rect x="1" y="24" width="{W - 2}" height="13" fill="#10161e"/>',
         f'<line x1="1" y1="37" x2="{W - 1}" y2="37" stroke="{EDGE}"/>']
    for i, col in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        b.append(f'<circle cx="{24 + i * 20}" cy="19" r="6" fill="{col}"/>')
    b.append(text(W / 2, 23, "samprith@vyanika: ~", 12, MUTED, anchor="middle"))

    PITCH, SIZE = 9.0, 15
    prompt = (f'<text x="24" y="{{y}}" class="mono" font-size="{SIZE}" '
              f'textLength="{19 * PITCH}" lengthAdjust="spacing">'
              f'<tspan fill="{GREEN}">samprith@vyanika</tspan><tspan fill="{MUTED}">:~$</tspan>'
              f'</text>')
    y = 74
    b.append(prompt.format(y=y))
    c, body, w = typer(24 + 20 * PITCH, y, "./boot --profile", PITCH, period, 0, 0.7,
                       "cmd", SIZE)
    css += c
    reduced += f".cmd{{transform:translateX({w:.1f}px)!important}}"
    b.append(body)

    rows = [
        ("Started", "firmware.service", "STM32 + Giga R1 nodes · ~2,700 cells · 120 → 15 ms"),
        ("Started", "server.service", "FastAPI + WebSockets on a Raspberry Pi 5 kiosk"),
        ("Started", "browser.service", "framework-free JS · Canvas heatmaps · WCAG AA"),
        ("Started", "agents.service", "21 agents · 82 tools · humans approve every write"),
        ("Started", "research.service", "FedAvg + FedProx from scratch · 100 clients"),
        ("Started", "student.service", "B.E. AI & ML @ MITE · class of 2027"),
        ("Reached", "target cto.target", "Co-Founder & CTO, Vyanika Innovations LLP"),
    ]
    off = period - 1.2
    for k, (verb, unit, what) in enumerate(rows):
        y += 28
        on = 1.0 + 0.45 * k
        css += appear(f"l{k}", on, off, period) + appear(f"k{k}", on + 0.3, off, period)
        css += f".l{k}{{animation:l{k} {period}s infinite}}.k{k}{{animation:k{k} {period}s infinite}}"
        b.append(f'<g class="ln l{k}">'
                 + text(24, y, "[      ]", SIZE, MUTED, extra='xml:space="preserve"')
                 + text(110, y, f'{verb} <tspan fill="{TEXT}">{esc(unit)}</tspan>', SIZE, MUTED)
                 + text(356, y, esc(what), SIZE, MUTED if k < len(rows) - 1 else AMBER,
                        weight=None if k < len(rows) - 1 else "700")
                 + '</g>')
        b.append(f'<g class="ln k{k}">'
                 + text(24, y, f'   <tspan fill="{GREEN}" font-weight="700">OK</tspan>', SIZE,
                        MUTED, extra='xml:space="preserve"') + '</g>')
    y += 28
    on = 1.0 + 0.45 * len(rows) + 0.2
    css += appear("fin", on, off, period) + f".fin{{animation:fin {period}s infinite}}"
    b.append(f'<g class="ln fin">{prompt.format(y=y)}'
             f'<rect class="blink" x="{24 + 20 * PITCH}" y="{y - SIZE + 2}" width="{PITCH * .9}" '
             f'height="{SIZE + 1}" fill="{CYAN}"/></g>')
    css = ".ln{opacity:0}" + css
    return svg(W, H, "Boot log",
               "A terminal boots Samprith's profile: firmware, server, browser, agents, "
               "research and student services start, then it reaches Co-Founder and CTO, "
               "Vyanika Innovations LLP.", css, "".join(b), reduced)


# --------------------------------------------------------------------------- signal path
def signal_path():
    W, H = 1000, 372
    css = (
        ".pk{opacity:0;animation:mv 1.5s linear infinite}"
        ".pk.raw{animation-name:mvraw}"
        "@keyframes mv{0%{transform:translateX(0);opacity:0}15%,85%{opacity:1}"
        "100%{transform:translateX(46px);opacity:0}}"
        "@keyframes mvraw{0%{transform:translateX(0);opacity:0}15%,85%{opacity:1}"
        "100%{transform:translateX(38px);opacity:0}}"
        ".led{opacity:.18;animation:led 1.8s linear infinite}"
        "@keyframes led{0%,30%{opacity:.95}60%,100%{opacity:.18}}"
        ".bar{transform-box:fill-box;transform-origin:0 50%}"
        ".g1{animation:g1 9s ease-out infinite}.g2{animation:g2 9s ease-out infinite}"
        "@keyframes g1{0%{transform:scaleX(0)}9%,100%{transform:scaleX(1)}}"
        "@keyframes g2{0%,11%{transform:scaleX(0)}16%,100%{transform:scaleX(1)}}"
        ".l1{animation:l1 9s infinite}.l2{animation:l2 9s infinite}"
        "@keyframes l1{0%,6%{opacity:0}9%,100%{opacity:1}}"
        "@keyframes l2{0%,13%{opacity:0}16%,100%{opacity:1}}"
    )
    reduced = "*{animation:none!important}.pk{opacity:1!important}"
    b = [text(20, 38, "TECH KABADDI", 13, AMBER, font="sans", weight="800", ls="2"),
         text(150, 38, "sensor → referee, end to end", 12, MUTED),
         text(W - 20, 38, "patent filed · NAIN-funded · source private", 12, DIM, anchor="end")]

    stages = [
        ("01 · SENSE", "Pressure mat", ["3 sensing nodes", "~2,700 pressure cells",
                                         "boot-time calibration"], heat(.85)),
        ("02 · ENCODE", "Embedded firmware", ["STM32H747 · Giga R1", "CRC16 · RLE framing",
                                              "adaptive rate control"], AMBER),
        ("03 · SERVE", "FastAPI + WebSocket", ["Raspberry Pi 5 kiosk", "NumPy · 40k packets/s",
                                               "O(log n) replay seeks"], CYAN),
        ("04 · DECIDE", "Referee review", ["Canvas 2D heatmaps", "adaptive line calls",
                                           "replay at 0.1×–4×"], GREEN),
    ]
    BX, BW, BY, BH = [20, 275, 530, 785], 195, 58, 140
    for (label, title, subs, col), x in zip(stages, BX):
        b.append(f'<rect x="{x}" y="{BY}" width="{BW}" height="{BH}" rx="12" fill="{PANEL}" '
                 f'stroke="{EDGE}"/>')
        b.append(text(x + 16, BY + 24, label, 11, col, weight="700", ls="1"))
        b.append(text(x + 16, BY + 48, esc(title), 16, TEXT, font="sans", weight="700"))
        for k, s in enumerate(subs):
            b.append(text(x + 16, BY + 72 + k * 17, esc(s), 11, MUTED))
        for k in range(14):   # activity LEDs: a chaser running along the box floor
            b.append(f'<rect class="led" x="{x + 16 + k * 12}" y="{BY + BH - 16}" width="8" '
                     f'height="4" rx="1" fill="{col}" style="animation-delay:{k * 0.09:.2f}s"/>')

    cy = BY + BH / 2
    for n, (xa, xb) in enumerate(zip([x + BW for x in BX[:-1]], BX[1:])):
        b.append(f'<line x1="{xa}" y1="{cy}" x2="{xb}" y2="{cy}" stroke="#263241" '
                 f'stroke-width="2" stroke-dasharray="3 3"/>')
        for k in range(3):
            d = f"animation-delay:{k * 0.5:.1f}s"
            if n == 0:   # raw frames are fat ...
                b.append(f'<rect class="pk raw" x="{xa + 3}" y="{cy - 4}" width="16" height="8" '
                         f'rx="2" fill="{AMBER}" style="{d}"/>')
            else:        # ... after the firmware they are tiny
                b.append(f'<rect class="pk" x="{xa + 4}" y="{cy - 3}" width="6" height="6" '
                         f'rx="1.5" fill="{CYAN}" style="{d}"/>')

    # before/after bars
    def bars(y, label, verdict, before, after, ratio):
        TW = 380
        out = [text(20, y, label, 12, MUTED),
               text(490, y, verdict, 13, AMBER, weight="700", anchor="end"),
               f'<rect class="bar g1" x="20" y="{y + 10}" width="{TW}" height="12" rx="3" fill="#273241"/>',
               text(TW + 30, y + 20, before, 11, MUTED, cls="l1"),
               f'<rect class="bar g2" x="20" y="{y + 28}" width="{TW / ratio:.1f}" height="12" '
               f'rx="3" fill="{CYAN}"/>',
               text(20 + TW / ratio + 10, y + 38, after, 11, CYAN, weight="700", cls="l2")]
        return "".join(out)
    b.append(bars(232, "end-to-end latency", "8× lower", "120 ms", "15 ms", 8))
    b.append(bars(300, "packet size", "40× smaller", "~8 KB", "~200 B", 40))

    tiles = [("243", "automated tests in CI"), ("11", "releases in 3 weeks"),
             ("~13k", "lines of Python + JS"), ("AA", "WCAG contrast, both themes")]
    for k, (num, label) in enumerate(tiles):
        x, y = 530 + (k % 2) * 235, 222 + (k // 2) * 72
        b.append(f'<rect x="{x}" y="{y}" width="215" height="60" rx="10" fill="{PANEL}" '
                 f'stroke="{EDGE}"/>')
        b.append(text(x + 16, y + 34, num, 26, TEXT, font="sans", weight="800"))
        b.append(text(x + 16, y + 50, esc(label), 10, MUTED))
    return svg(W, H, "Tech Kabaddi signal path",
               "Pressure mat with about 2,700 cells, then embedded firmware on STM32H747 and "
               "Arduino Giga R1, then a FastAPI and WebSocket server on a Raspberry Pi 5, then "
               "the referee's browser. Latency fell from 120 ms to 15 ms, packets from about "
               "8 KB to about 200 B. 243 automated tests, 11 releases in 3 weeks.",
               css, "".join(b), reduced)


# --------------------------------------------------------------------------- cards
def card(name, tag, title, desc, stats, chips, viz, css, reduced, alt):
    W, H = 500, 262
    b = [text(24, 38, esc(tag), 11, CYAN, weight="700", ls="1"),
         text(300, 40, "↗", 16, DIM, font="sans", anchor="end"),
         text(23, 72, esc(title), 26, TEXT, font="sans", weight="800")]
    for k, line in enumerate(desc):
        b.append(text(24, 98 + k * 18, esc(line), 13.5, MUTED, font="sans"))
    for x, num, label in stats:
        b.append(text(x, 176, esc(num), 22, TEXT, font="sans", weight="800"))
        b.append(text(x, 193, esc(label), 10, DIM))
    x = 24
    for c in chips:
        s, w = chip(x, 214, c)
        b.append(s)
        x += w + 6
    b.append(f'<rect x="316" y="20" width="164" height="222" rx="10" fill="{PANEL}" '
             f'stroke="{EDGE}"/>')
    b.append(viz)
    (OUT / f"card-{name}.svg").write_text(
        svg(W, H, title, alt, css, "".join(b), "*{animation:none!important}" + reduced),
        encoding="utf-8")


def card_vidyaerp():
    period = 5.0
    cx = 398
    specs = [338, 368, 398, 428, 458]
    v = [text(cx, 44, '"cover Dr. X on Monday"', 9.5, DIM, anchor="middle"),
         f'<circle cx="{cx}" cy="84" r="13" fill="#2a1f0a" stroke="{AMBER}" stroke-width="1.5"/>',
         text(cx, 88, "S", 11, AMBER, weight="700", anchor="middle"),
         text(cx, 113, "supervisor", 9, MUTED, anchor="middle")]
    for x in specs:
        v.append(f'<line x1="{cx}" y1="97" x2="{x}" y2="{139}" stroke="#24303d"/>')
    for x in specs:
        v.append(f'<circle cx="{x}" cy="146" r="7" fill="{PANEL}" stroke="{CYAN}" '
                 f'stroke-opacity=".75"/>')
    v.append(text(cx, 168, "specialist agents", 9, MUTED, anchor="middle"))
    v.append(f'<line x1="428" y1="153" x2="428" y2="186" stroke="#24303d" stroke-dasharray="2 2"/>')
    v.append(f'<rect class="guard" x="330" y="186" width="136" height="38" rx="8" fill="{BG}" '
             f'stroke="{DIM}"/>')
    v.append(text(cx, 209, "PolicyGuard", 10, MUTED, anchor="middle", cls="g0"))
    v.append(text(cx, 209, "⏸ awaiting a human", 10, AMBER, anchor="middle", cls="ga",
                  extra='opacity="0"'))
    v.append(text(cx, 209, "✓ approved, undo kept", 10, GREEN, anchor="middle", cls="gg",
                  extra='opacity="0"'))
    v.append(pulse(cx, 50, cx, 70, 0.0, 0.4, period))
    for k, x in enumerate(specs):
        v.append(pulse(cx, 97, x, 139, 0.5 + k * 0.07, 0.45, period))
    v.append(pulse(428, 153, 428, 186, 1.3, 0.4, period, color=AMBER))
    css = (
        ".g0{animation:g0 5s infinite}.ga{animation:ga 5s infinite}.gg{animation:gg 5s infinite}"
        ".guard{animation:guard 5s infinite}"
        "@keyframes g0{0%,33%{opacity:1}34%,91%{opacity:0}92%,100%{opacity:1}}"
        "@keyframes ga{0%,33%{opacity:0}34%,63%{opacity:1}64%,100%{opacity:0}}"
        "@keyframes gg{0%,63%{opacity:0}64%,91%{opacity:1}92%,100%{opacity:0}}"
        f"@keyframes guard{{0%,33%{{stroke:{DIM}}}34%,63%{{stroke:{AMBER}}}64%,91%{{stroke:{GREEN}}}"
        f"92%,100%{{stroke:{DIM}}}}}"
    )
    card("vidyaerp", "FINAL-YEAR PROJECT · PYTHON", "VidyaERP",
         ["Agentic ERP for engineering colleges:",
          "a supervisor routes requests to specialist",
          "agents; a human approves every write."],
         [(24, "21", "agents"), (84, "82", "tools"), (144, "456/456", "periods, 0 clashes")],
         ["Python", "FastAPI", "MCP", "multi-agent"],
         "".join(v), css, "",
         "VidyaERP: agentic ERP for engineering colleges. A supervisor routes a request to "
         "specialist agents and a PolicyGuard holds each write until a human approves it. "
         "21 agents, 82 tools, timetable solver places 456 of 456 periods with 0 clashes.")


def card_setu():
    period = 8.0
    log = [
        ("› buy earbuds · Rs 2,499", TEXT),
        ("  cap ✓ budget ✓ cat ✓", GREEN),
        ("  order → razorpay ✓ paid", GREEN),
        ("  signature ✓ HMAC-SHA256", MUTED),
        ("› buy monitor · Rs 18,000", TEXT),
        ("  cap ✕ blocked pre-order", RED),
        ("  ↳ 2 substitutes offered", AMBER),
    ]
    v = [text(330, 44, "mandate · cap Rs 5,000", 9.5, DIM)]
    css = ""
    for k, (s, col) in enumerate(log):
        on = 0.4 + 0.75 * k
        css += appear(f"s{k}", on, period - 0.7, period) + f".s{k}{{animation:s{k} {period}s infinite}}"
        v.append(text(330, 70 + k * 23, esc(s), 9.5, col, cls=f"sl s{k}",
                      extra='xml:space="preserve" opacity="0"'))
    card("setu", "RAZORPAY AI BUILDATHON 2026", "Setu",
         ["MCP server that lets an AI agent buy",
          "over Razorpay's test-mode rails, inside",
          "a spend mandate enforced in code."],
         [(24, "5", "MCP tools"), (84, "59", "tests"), (144, "4", "mandate rules")],
         ["Node.js", "Express", "Razorpay API", "MCP"],
         "".join(v), ".sl{opacity:0}" + css, ".sl{opacity:1!important}",
         "Setu: an MCP server that lets an AI agent buy over Razorpay test-mode rails inside "
         "a spend mandate. A purchase over the cap is blocked before an order is created and "
         "substitutes are offered. 5 MCP tools, 59 tests.")


def card_fedlearn():
    rnd = random.Random(3)
    X0, X1, Y0, Y1 = 332, 440, 200, 60   # chart box; Y0 is the 0% line
    yv = lambda acc: Y0 - (acc / 50) * (Y0 - Y1)
    n = 40
    prox, avg = [], []
    for i in range(n + 1):
        t = i / n
        x = X0 + t * (X1 - X0)
        p = 36.6 * (1 - (1 - t) ** 2.2) + (rnd.uniform(-1.4, 1.4) if 0 < i < n else 0)
        a = 22.1 * t ** 0.8 + (rnd.uniform(-5, 5) * (1 - t * .6) if 0 < i < n else 0)
        prox.append(f"{x:.1f},{yv(max(p, 0)):.1f}")
        avg.append(f"{x:.1f},{yv(max(a, 0)):.1f}")
    css = (
        ".cv{stroke-dasharray:100;stroke-dashoffset:100;animation:draw 8s ease-out infinite}"
        "@keyframes draw{0%{stroke-dashoffset:100}40%,100%{stroke-dashoffset:0}}"
        ".end{opacity:0;animation:endl 8s infinite}"
        "@keyframes endl{0%,40%{opacity:0}44%,100%{opacity:1}}"
    )
    v = [text(330, 40, "α = 0.1 · extreme non-IID", 9.5, DIM)]
    for acc in (0, 25, 50):
        v.append(f'<line x1="{X0}" y1="{yv(acc)}" x2="{X1}" y2="{yv(acc)}" stroke="#1d2631"/>')
        v.append(text(X0 - 4, yv(acc) + 3, f"{acc}", 8, DIM, anchor="end"))
    v.append(f'<polyline class="cv" pathLength="100" points="{" ".join(avg)}" fill="none" '
             f'stroke="{CYAN}" stroke-width="1.8" stroke-linejoin="round"/>')
    v.append(f'<polyline class="cv" pathLength="100" points="{" ".join(prox)}" fill="none" '
             f'stroke="{AMBER}" stroke-width="2.2" stroke-linejoin="round"/>')
    v.append(text(X1 + 4, yv(36.6) + 3, "36.6%", 9.5, AMBER, weight="700", cls="end"))
    v.append(text(X1 + 4, yv(22.1) + 3, "22.1%", 9.5, CYAN, weight="700", cls="end"))
    v.append(f'<line x1="330" y1="221" x2="344" y2="221" stroke="{AMBER}" stroke-width="2.2"/>')
    v.append(text(348, 224, "FedProx", 9.5, MUTED))
    v.append(f'<line x1="400" y1="221" x2="414" y2="221" stroke="{CYAN}" stroke-width="1.8"/>')
    v.append(text(418, 224, "FedAvg", 9.5, MUTED))
    v.append(text(X1, 211, "rounds →", 8, DIM, anchor="end"))
    card("fedlearn", "RESEARCH · PYTORCH", "Federated Learning",
         ["FedAvg and FedProx from scratch:",
          "100 simulated clients on CIFAR-10,",
          "IID and Dirichlet non-IID splits."],
         [(24, "99.02%", "MNIST IID"), (124, "+14.5", "pts for FedProx"), (234, "100", "clients")],
         ["Python", "PyTorch", "FedAvg", "FedProx"],
         "".join(v), css, ".cv{stroke-dashoffset:0!important}.end{opacity:1!important}",
         "Federated learning research framework: FedAvg and FedProx implemented from scratch, "
         "100 simulated clients on CIFAR-10. At alpha 0.1, FedProx reaches 36.6% final "
         "accuracy against FedAvg's 22.1% (curve shapes are illustrative; the final values "
         "come from the repo).")


def card_chronos():
    rnd = random.Random(11)
    period = 9.0
    COLS, ROWS, CW, CH, G = 5, 6, 22, 19, 4
    x0 = 316 + (164 - (COLS * (CW + G) - G)) / 2
    y0 = 58
    palette = [AMBER, CYAN, VIOLET, GREEN, PINK]
    cells = [(c, r) for c in range(COLS) for r in range(ROWS)]
    rnd.shuffle(cells)
    clashes = {6, 15, 23}          # these get a red "conflict, backtrack" flash first
    css = (".tt{opacity:0}" + appear("ok", 6.4, period - 0.5, period)
           + appear("run", 0.0, 6.3, period) + f".ok{{animation:ok {period}s infinite}}"
           f".run{{animation:run {period}s infinite}}")
    v = []
    for c, d in enumerate("MTWTF"):
        v.append(text(x0 + c * (CW + G) + CW / 2, 50, d, 9, DIM, anchor="middle"))
    for c in range(COLS):
        for r in range(ROWS):
            v.append(f'<rect x="{x0 + c * (CW + G)}" y="{y0 + r * (CH + G)}" width="{CW}" '
                     f'height="{CH}" rx="3" fill="#141b24"/>')
    for k, (c, r) in enumerate(cells):
        on = 0.3 + 0.2 * k
        x, y = x0 + c * (CW + G), y0 + r * (CH + G)
        css += appear(f"c{k}", on, period - 0.5, period) + f".c{k}{{animation:c{k} {period}s infinite}}"
        v.append(f'<rect class="tt c{k}" x="{x}" y="{y}" width="{CW}" height="{CH}" rx="3" '
                 f'fill="{rnd.choice(palette)}" fill-opacity=".8"/>')
        if k in clashes:
            css += appear(f"x{k}", on - 0.5, on - 0.15, period) + f".x{k}{{animation:x{k} {period}s infinite}}"
            v.append(f'<rect class="tt x{k}" x="{x + .75}" y="{y + .75}" width="{CW - 1.5}" '
                     f'height="{CH - 1.5}" rx="3" fill="none" stroke="{RED}" stroke-width="1.5"/>')
    v.append(text(398, 216, "MRV backtracking…", 9.5, MUTED, anchor="middle", cls="run"))
    v.append(text(398, 216, "✓ solved · 0 clashes", 9.5, GREEN, anchor="middle", cls="ok",
                  extra='opacity="0"'))
    v.append(text(398, 231, "then hill-climbing", 8.5, DIM, anchor="middle"))
    card("chronos", "FULL-STACK · TYPESCRIPT", "Chronos",
         ["Teacher ERP and timetable engine:",
          "MRV backtracking plus hill-climbing,",
          "with a live, animated solver trace."],
         [(24, "~6k", "lines of TypeScript"), (144, "21", "React components")],
         ["Next.js", "TypeScript", "Drizzle ORM"],
         "".join(v), css,
         "[class*=' c']{opacity:1!important}.x6,.x15,.x23,.run{opacity:0!important}"
         ".ok{opacity:1!important}",
         "Chronos: a teacher ERP and timetable engine. A timetable grid fills cell by cell "
         "as an MRV backtracking solver runs, flashing red on a conflict before it backtracks.")


# --------------------------------------------------------------------------- buttons
def button(name, label, value, icon, width, title):
    H = 52
    b = [icon,
         text(58, 21, label, 9.5, CYAN, weight="700", ls="1.5"),
         text(58, 39, esc(value), 15, TEXT, font="sans", weight="600"),
         f'<circle class="live" cx="{width - 18}" cy="{H / 2}" r="3" fill="{GREEN}"/>']
    css = ".live{animation:live 2.4s ease-in-out infinite}@keyframes live{50%{opacity:.2}}"
    (OUT / f"btn-{name}.svg").write_text(
        svg(width, H, f"{title}: {value}", f"{title}: {value}", css,
            "".join(b), "*{animation:none!important}"), encoding="utf-8")


def buttons():
    ic = f'stroke="{AMBER}" stroke-width="1.6" fill="none"'
    globe = (f'<circle cx="30" cy="26" r="11" {ic}/><ellipse cx="30" cy="26" rx="5" ry="11" {ic}/>'
             f'<line x1="19" y1="26" x2="41" y2="26" {ic}/>')
    linked = (f'<rect x="19" y="15" width="22" height="22" rx="4" {ic}/>'
              f'<line x1="25" y1="24" x2="25" y2="32" {ic}/><circle cx="25" cy="20" r="1.2" '
              f'fill="{AMBER}"/><path d="M29 32 V24 M29 27 Q29 24 32 24 Q35 24 35 27 V32" {ic}/>')
    mail = (f'<rect x="18" y="17" width="24" height="18" rx="3" {ic}/>'
            f'<path d="M19 19 L30 28 L41 19" {ic}/>')
    button("site", "WEBSITE", "vyanikatech.com", globe, 230, "Website")
    button("linkedin", "LINKEDIN", "samprith-c-amin", linked, 230, "LinkedIn")
    button("email", "EMAIL", "samprith02@gmail.com", mail, 262, "Email")


# --------------------------------------------------------------------------- footer
def footer():
    W, H = 1000, 104
    rnd = random.Random(5)
    pts = []
    for i in range(0, W - 39, 4):
        x = 20 + i
        v = 0.05 + rnd.uniform(-.02, .02)
        ph = (i % 120) / 120            # one footfall every 120 px: heel strike, then toe-off
        v += 0.85 * math.exp(-((ph - .25) / .05) ** 2) + 0.6 * math.exp(-((ph - .42) / .06) ** 2)
        pts.append(f"{x},{62 - v * 40:.1f}")
    crc = crc16_ccitt(b"samprith02")
    css = (".wave{stroke-dasharray:1000;stroke-dashoffset:1000;animation:wave 7s linear infinite}"
           "@keyframes wave{0%{stroke-dashoffset:1000}55%,100%{stroke-dashoffset:0}}")
    b = [f'<defs><linearGradient id="hg" x1="0" x2="1">'
         + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in HEAT[1:])
         + '</linearGradient></defs>',
         f'<polyline class="wave" pathLength="1000" points="{" ".join(pts)}" fill="none" '
         f'stroke="url(#hg)" stroke-width="2" stroke-linejoin="round"/>',
         text(20, 88, "end of packet", 11, DIM),
         text(W / 2, 88, "thanks for scrolling this far", 11, MUTED, anchor="middle"),
         text(W - 20, 88, f'CRC16-CCITT("samprith02") = 0x{crc:04X} '
                          f'<tspan fill="{GREEN}" font-weight="700">✓</tspan>', 11, DIM,
              anchor="end")]
    return svg(W, H, "End of packet",
               f"A pressure trace of footfalls. CRC16-CCITT of samprith02 is 0x{crc:04X}.",
               css, "".join(b), "*{animation:none!important}.wave{stroke-dashoffset:0!important}")


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "hero.svg").write_text(hero(), encoding="utf-8")
    (OUT / "boot.svg").write_text(boot(), encoding="utf-8")
    (OUT / "signal-path.svg").write_text(signal_path(), encoding="utf-8")
    (OUT / "footer.svg").write_text(footer(), encoding="utf-8")
    card_vidyaerp()
    card_setu()
    card_fedlearn()
    card_chronos()
    buttons()
    for f in sorted(OUT.glob("*.svg")):
        print(f"{f.name:22} {f.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
