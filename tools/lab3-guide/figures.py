"""SVG figures that are easier to compute than to hand-write: the Pico pin map and
the mock VGA screens. gen.py fills {{FIG name}} markers in template.html with these."""
import math, random

# Physical pin -> name on the Pico 2
PINS = {1: "GP0", 2: "GP1", 3: "GND", 4: "GP2", 5: "GP3", 6: "GP4", 7: "GP5", 8: "GND",
        9: "GP6", 10: "GP7", 11: "GP8", 12: "GP9", 13: "GND", 14: "GP10", 15: "GP11",
        16: "GP12", 17: "GP13", 18: "GND", 19: "GP14", 20: "GP15", 21: "GP16", 22: "GP17",
        23: "GND", 24: "GP18", 25: "GP19", 26: "GP20", 27: "GP21", 28: "GND", 29: "GP22",
        30: "RUN", 31: "GP26", 32: "GP27", 33: "GND", 34: "GP28", 35: "VREF", 36: "3V3",
        37: "3V3_EN", 38: "GND", 39: "VSYS", 40: "VBUS"}


def pin_xy(p):
    """Left column: pins 1-20 top to bottom. Right column: 40 at the top down to 21."""
    if p <= 20:
        return 300, 62 + 23 * (p - 1)
    return 420, 62 + 23 * (40 - p)


def pinmap():
    # (pin, label at the far end, week it's needed)
    left = [(1, "RX (adapter's input)"), (2, "TX (adapter's output)"), (3, "GND"),
            (6, "PWM terminal"), (8, "MCU GND terminal"),
            (11, "SDA"), (12, "SCL"), (13, "GND"),
            (19, "probe: interrupt, 500 Hz"), (20, "probe: frame toggle")]
    right = [(27, "RED"), (26, "BLUE"), (25, "H GREEN"), (24, "L GREEN"), (23, "GND"),
             (22, "VSYNC"), (21, "HSYNC"), (36, "IMU VCC (3.3 V)")]
    o = ['<svg class="wiring" viewBox="0 0 760 540" role="img" aria-label="Pico 2 pin map for Lab 3: '
         'USB-to-serial adapter on pins 1 to 3, motor board on pins 6 and 8, IMU on pins 11 to 13 plus 3V3 on pin 36, '
         'scope probe points on pins 19 and 20, VGA adapter on pins 21 to 27.">']
    o.append('<rect class="pico" x="300" y="30" width="120" height="494" rx="6"/>')
    o.append('<rect class="pico" x="340" y="16" width="40" height="18" rx="2"/>')
    o.append('<text class="tiny" x="360" y="12" text-anchor="middle">USB</text>')
    o.append('<text class="blkh" x="360" y="300" text-anchor="middle" transform="rotate(-90 360 300)">Raspberry Pi Pico 2</text>')
    o.append('<text class="tiny" x="306" y="48">pin 1</text><text class="tiny" x="414" y="48" text-anchor="end">pin 40</text>')
    for p in range(1, 41):
        x, y = pin_xy(p)
        o.append(f'<circle class="pinhole" cx="{x}" cy="{y}" r="3.2"/>')
    for p, lbl in left:
        x, y = pin_xy(p)
        o.append(f'<circle class="pinused" cx="{x}" cy="{y}" r="4"/>')
        o.append(f'<text class="pinlbl" x="{x + 8}" y="{y + 3.5}">{PINS[p]} · {p}</text>')
        o.append(f'<path class="wire" d="M{x - 4} {y} H226"/>')
        o.append(f'<text class="blk" x="218" y="{y + 4}" text-anchor="end">{lbl}</text>')
    for p, lbl in right:
        x, y = pin_xy(p)
        o.append(f'<circle class="pinused" cx="{x}" cy="{y}" r="4"/>')
        o.append(f'<text class="pinlbl" x="{x - 8}" y="{y + 3.5}" text-anchor="end">{p} · {PINS[p]}</text>')
        o.append(f'<path class="wire" d="M{x + 4} {y} H500"/>')
        o.append(f'<text class="blk" x="508" y="{y + 4}">{lbl}</text>')
    # group boxes, left
    def lbox(p0, p1, title, note=""):
        y0 = pin_xy(p0)[1] - 14
        y1 = pin_xy(p1)[1] + 14
        o.append(f'<rect class="block" x="20" y="{y0}" width="210" height="{y1 - y0}" fill-opacity=".35"/>')
        o.append(f'<text class="blkh" x="20" y="{y0 - 6}">{title}</text>')
        if note:
            o.append(f'<text class="tiny" x="28" y="{y1 - 6}">{note}</text>')
    lbox(1, 3, "USB-to-serial adapter · week 1")
    lbox(6, 8, "Motor board · week 1", "its other side has no wire to the Pico")
    lbox(11, 13, "IMU (MPU6050) · week 2", "+ VCC to pin 36, on the right")
    lbox(19, 20, "Scope test points · week 2")
    y0 = pin_xy(36)[1] - 14
    o.append(f'<rect class="block" x="496" y="{y0}" width="250" height="28" fill-opacity=".35"/>')
    o.append(f'<text class="blkh" x="496" y="{y0 - 6}">IMU power · week 2</text>')
    y0 = pin_xy(27)[1] - 14
    y1 = pin_xy(21)[1] + 14
    o.append(f'<rect class="block" x="496" y="{y0}" width="250" height="{y1 - y0}" fill-opacity=".35"/>')
    o.append(f'<text class="blkh" x="496" y="{y0 - 6}">4760 VGA adapter board · week 2</text>')
    o.append(f'<text class="tiny" x="610" y="{y1 - 8}">same as Lab 2</text>')
    o.append('</svg>')
    return "\n".join(o)


# ---------------------------------------------------------------- mock VGA screens
YEL = "#F2C94C"
COL = {"WHITE": "#fff", "RED": "#ff3b30", "GREEN": "#34c759", "CYAN": "#32d0e0", "YELLOW": "#ffd60a"}


def _axes(top_labels, bottom_labels, top_title="", bottom_title=""):
    o = []
    c = COL["CYAN"]
    for y in (80, 155, 230, 280, 355, 430):
        o.append(f'<path d="M75 {y} H80" stroke="{c}" stroke-width="2"/>')
    o.append(f'<path d="M80 80 V230 M80 280 V430" stroke="{c}" stroke-width="2"/>')
    for (y, t) in zip((80, 155, 230), top_labels):
        o.append(f'<text x="70" y="{y + 4}" font-size="11" fill="#fff" text-anchor="end" font-family="JetBrains Mono, monospace">{t}</text>')
    for (y, t) in zip((280, 355, 430), bottom_labels):
        o.append(f'<text x="70" y="{y + 4}" font-size="11" fill="#fff" text-anchor="end" font-family="JetBrains Mono, monospace">{t}</text>')
    if top_title:
        o.append(f'<text x="85" y="72" font-size="11" fill="#fff" font-family="JetBrains Mono, monospace">{top_title}</text>')
    if bottom_title:
        o.append(f'<text x="85" y="272" font-size="11" fill="#fff" font-family="JetBrains Mono, monospace">{bottom_title}</text>')
    return o


def _trace(fn, color, seed, noise, x0=81, x1=611, step=3):
    rnd = random.Random(seed)
    pts = []
    for x in range(x0, x1, step):
        pts.append(f"{x},{fn(x) + rnd.uniform(-noise, noise):.1f}")
    return f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.6"/>'


def _note(x, y, text, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="15" fill="{YEL}" font-family="Archivo, sans-serif" '
            f'font-style="italic" text-anchor="{anchor}">{text}</text>')


def _wrap(label, body):
    return (f'<svg class="screen" viewBox="0 0 640 480" role="img" aria-label="{label}">'
            '<rect x="0" y="0" width="640" height="480" fill="#000"/>' + "".join(body) + "</svg>")


def screen_demo():
    """The unmodified IMU demo with the arm held level and still."""
    o = _axes(("+250", "0", "-250"), ("+2", "0", "-2"))
    # gyro: all three near zero
    o.append(_trace(lambda x: 155, COL["WHITE"], 1, 1.5))
    o.append(_trace(lambda x: 157, COL["RED"], 2, 1.5))
    o.append(_trace(lambda x: 153, COL["GREEN"], 3, 1.5))
    # accel: one axis at +1 g (36 px above 0 with the demo's scaling), two near 0
    o.append(_trace(lambda x: 319, COL["WHITE"], 4, 2.5))
    o.append(_trace(lambda x: 356, COL["RED"], 5, 2.5))
    o.append(_trace(lambda x: 353, COL["GREEN"], 6, 2.5))
    o.append(_note(90, 110, "top: gyro x, y, z (deg/s): all near 0 when still"))
    o.append(_note(90, 300, "one accelerometer trace sits at +1 g:"))
    o.append(_note(90, 400, "that axis points up (here x, white)"))
    return _wrap("Mock monitor: the IMU demo unchanged. Top plot: three gyro traces near zero. "
                 "Bottom plot: one accelerometer trace at plus 1 g, two near zero.", o)


def _settle(x, x0, start, end, tau, wob=0.0, period=60):
    if x < x0:
        return start
    t = x - x0
    return end + (start - end) * math.exp(-t / tau) * math.cos(2 * math.pi * t / period * wob)


def screen_open_loop():
    """Week 2 step 3: motor set by hand. Arm rises from hanging to roughly level."""
    o = _axes(("+90", "0", "-90"), ("6000", "3000", "0"), "arm angle (deg)", "motor command (low-passed)")
    ang = lambda x: 230 if x < 200 else 162 + (230 - 162) * math.exp(-(x - 200) / 40) * math.cos((x - 200) / 22)
    o.append(_trace(ang, COL["WHITE"], 7, 1.2))
    mot = lambda x: 430 if x < 200 else 430 - 60 * (1 - math.exp(-(x - 200) / 5))
    o.append(_trace(mot, COL["GREEN"], 8, 0.4, step=2))
    o.append('<text x="10" y="26" font-size="20" fill="#fff" font-family="JetBrains Mono, monospace">angle  ___._ deg</text>')
    o.append(_note(210, 210, "you type m, then a power level", "start"))
    o.append(_note(330, 120, "the arm swings up, wobbles, settles", "start"))
    o.append(_note(330, 350, "motor steps to the level you typed", "start"))
    return _wrap("Mock monitor, week 2 step 3: angle trace rising from minus 90 to near level after the motor "
                 "command steps up; motor trace steps from 0 to a constant level.", o)


def screen_pid():
    """Week 2 step 4: P-only control. Target 0, arm settles below it."""
    o = _axes(("+90", "0", "-90"), ("6000", "3000", "0"), "arm angle (deg)", "motor command (low-passed)")
    o.append(f'<path d="M81 155 H611" stroke="{COL["YELLOW"]}" stroke-width="1.6"/>')
    ang = lambda x: 230 if x < 180 else 178 + (230 - 178) * math.exp(-(x - 180) / 30) * math.cos((x - 180) / 16)
    o.append(_trace(ang, COL["WHITE"], 9, 1.2))
    mot = lambda x: 430 if x < 180 else 365 + (300 - 365) * math.exp(-(x - 180) / 20) * math.cos((x - 180) / 16)
    o.append(_trace(mot, COL["GREEN"], 10, 1.0, step=2))
    o.append('<text x="10" y="26" font-size="20" fill="#fff" font-family="JetBrains Mono, monospace">angle  ___._ deg</text>')
    o.append('<text x="10" y="46" font-size="11" fill="#fff" font-family="JetBrains Mono, monospace">PID  target 0.0  Kp __  Ki 0.00  Kd 0.00  motor ____</text>')
    o.append(_note(400, 145, "yellow: target (0, level)", "start"))
    o.append(_note(400, 205, "white: P alone settles below it", "start"))
    o.append(_note(200, 300, "motor jumps up, then settles", "start"))
    return _wrap("Mock monitor, week 2 step 4: yellow target line at 0; white angle rises from minus 90, "
                 "overshoots a little, and settles below the target; green motor trace jumps up then settles.", o)


FIGS = {"pinmap": pinmap, "screen_demo": screen_demo, "screen_open": screen_open_loop, "screen_pid": screen_pid}


# ---------------------------------------------------------------- parts, as they look
# Each returns a small SVG (viewBox 0 0 200 120). Part bodies use their real colours;
# all text uses the theme classes so it reads in light and dark.

def _part(label, body):
    return (f'<svg viewBox="0 0 200 120" role="img" aria-label="{label}">' + body + '</svg>')


def _res(bands):
    b = "".join(f'<rect x="{78 + i * 12}" y="47" width="6" height="26" fill="{c}"/>' for i, c in enumerate(bands))
    return ('<path d="M10 60 H62 M138 60 H190" stroke="#9aa0a3" stroke-width="3"/>'
            '<rect x="62" y="46" width="76" height="28" rx="12" fill="#d9c49a" stroke="#a38d5f"/>' + b +
            '<rect x="122" y="47" width="6" height="26" fill="#c9a227"/>')


def parts():
    P = []
    P.append(("Raspberry Pi Pico 2", "Green board, 40 pins. Micro-USB at one end, white BOOTSEL button beside it. Pin 1 is next to USB, marked with a square pad.",
      _part("Pico 2", '<rect x="20" y="30" width="160" height="60" rx="4" fill="#1f7a3a"/>'
        '<rect x="6" y="48" width="18" height="24" rx="2" fill="#b8bec2"/>'
        + "".join(f'<circle cx="{30 + i * 7.6}" cy="36" r="2" fill="#d6c27a"/><circle cx="{30 + i * 7.6}" cy="84" r="2" fill="#d6c27a"/>' for i, _ in enumerate(range(20)))
        + '<rect x="90" y="48" width="24" height="24" fill="#222"/><rect x="40" y="52" width="10" height="10" rx="2" fill="#f2f2f2"/>'
        '<text class="tiny" x="40" y="108">BOOTSEL</text><text class="tiny" x="6" y="24">USB</text><text class="tiny" x="34" y="24">pin 1 ↓</text>')))
    P.append(("USB-to-serial adapter", "A small board or a cable with a USB plug. Labelled pins GND, RX, TX and a power pin (5V or VCC: leave it off). On the common 4-wire cable: black GND, white RX, green TX, red power.",
      _part("USB-to-serial adapter", '<rect x="6" y="46" width="34" height="28" rx="3" fill="#b8bec2"/>'
        '<rect x="40" y="38" width="110" height="44" rx="4" fill="#2a4f9a"/><rect x="80" y="50" width="20" height="20" fill="#111"/>'
        + "".join(f'<rect x="152" y="{42 + i * 10}" width="14" height="5" fill="#d6c27a"/><text class="tiny" x="170" y="{48 + i * 10}">{t}</text>' for i, t in enumerate(["GND", "RX", "TX", "5V"])))))
    P.append(("Motor board (PCB)", "Green square board. Blue screw terminals: 12V + POWER SUPPLY GROUND (top), PWM + MCU GND (bottom), MOTOR+ / MOTOR− (right). Black barrel jack top-right, slide KILLSWITCH on the left.",
      _part("Motor control board", '<rect x="30" y="8" width="140" height="104" rx="3" fill="#2e8b3e"/>'
        '<rect x="40" y="10" width="30" height="18" fill="#2f6fd0"/><circle cx="48" cy="19" r="4" fill="#c9ced1"/><circle cx="62" cy="19" r="4" fill="#c9ced1"/>'
        '<rect x="70" y="92" width="30" height="18" fill="#2f6fd0"/><circle cx="78" cy="101" r="4" fill="#c9ced1"/><circle cx="92" cy="101" r="4" fill="#c9ced1"/>'
        '<rect x="150" y="50" width="18" height="30" fill="#2f6fd0"/><circle cx="159" cy="58" r="4" fill="#c9ced1"/><circle cx="159" cy="72" r="4" fill="#c9ced1"/>'
        '<rect x="140" y="10" width="26" height="24" fill="#111"/><rect x="36" y="40" width="10" height="28" fill="#111"/>'
        '<rect x="90" y="60" width="18" height="22" fill="#111"/><rect x="112" y="64" width="26" height="14" fill="#222"/>'
        '<text class="tiny" x="0" y="20">12V</text><text class="tiny" x="0" y="108">PWM</text><text class="tiny" x="172" y="58">M+</text><text class="tiny" x="172" y="80">M−</text>')))
    P.append(("4N35 optoisolator", "Black chip, 6 legs (3 per side). A small round dimple marks pin 1; it goes where the board's outline has its notch or dot.",
      _part("4N35", '<rect x="70" y="30" width="60" height="60" rx="3" fill="#1b1b1b"/><circle cx="80" cy="40" r="4" fill="#444"/>'
        + "".join(f'<rect x="{60}" y="{38 + i * 18}" width="10" height="6" fill="#b8bec2"/><rect x="130" y="{38 + i * 18}" width="10" height="6" fill="#b8bec2"/>' for i in range(3))
        + '<text class="tiny" x="20" y="44">pin 1</text><text x="100" y="66" font-size="10" fill="#ddd" text-anchor="middle" font-family="JetBrains Mono, monospace">4N35</text>')))
    P.append(("IRLB8721 MOSFET", "Black body with a metal tab and a hole, 3 legs. Facing the printed side, legs are G, D, S from left to right.",
      _part("IRLB8721", '<rect x="70" y="6" width="60" height="30" fill="#c9ced1"/><circle cx="100" cy="20" r="7" fill="#7d8688"/>'
        '<rect x="70" y="36" width="60" height="40" fill="#1b1b1b"/>'
        '<rect x="79" y="76" width="5" height="30" fill="#c9ced1"/><rect x="97" y="76" width="5" height="30" fill="#c9ced1"/><rect x="115" y="76" width="5" height="30" fill="#c9ced1"/>'
        '<text class="tiny" x="78" y="118">G</text><text class="tiny" x="96" y="118">D</text><text class="tiny" x="114" y="118">S</text>')))
    P.append(("1N4001 diode", "Small black cylinder with a grey or silver stripe at one end. The stripe is the cathode: match it to the stripe on the board.",
      _part("1N4001", '<path d="M10 60 H70 M130 60 H190" stroke="#9aa0a3" stroke-width="3"/>'
        '<rect x="70" y="46" width="60" height="28" rx="4" fill="#1b1b1b"/><rect x="116" y="46" width="8" height="28" fill="#c9ced1"/>'
        '<text class="tiny" x="110" y="96">stripe</text>')))
    P.append(("0.1 µF ceramic capacitor", "A small yellow or orange blob on two legs, printed 104 (10 × 10⁴ pF = 0.1 µF). Either way round.",
      _part("0.1 uF capacitor", '<path d="M92 70 V110 M108 70 V110" stroke="#9aa0a3" stroke-width="3"/>'
        '<ellipse cx="100" cy="50" rx="20" ry="24" fill="#e0a526"/><text x="100" y="54" font-size="11" fill="#3a2a00" text-anchor="middle" font-family="JetBrains Mono, monospace">104</text>')))
    P.append(("330 Ω resistor", "Bands: orange, orange, brown, then gold. Goes in the spot labelled 330.", _part("330 ohm", _res(["#e07b1a", "#e07b1a", "#7a4a1d"]))))
    P.append(("1 MΩ resistor", "Bands: brown, black, green, then gold. Spot labelled 1M.", _part("1 megaohm", _res(["#7a4a1d", "#111", "#2e9e4a"]))))
    P.append(("10 kΩ resistor (×2)", "Bands: brown, black, orange, then gold. Both 10k spots. (A 5-band resistor reads brown, black, black, red: check with the meter if unsure.)", _part("10 kilohm", _res(["#7a4a1d", "#111", "#e07b1a"]))))
    P.append(("Killswitch", "Small black slide switch. Off cuts the 12 V gate drive, so the motor can't run.",
      _part("Slide switch", '<rect x="50" y="40" width="100" height="40" rx="3" fill="#1b1b1b"/><rect x="60" y="48" width="80" height="24" fill="#333"/><rect x="66" y="50" width="22" height="20" fill="#9aa0a3"/>'
        '<text class="tiny" x="62" y="100">off ←  → on (check the board)</text>')))
    P.append(("Screw terminal (×3) and barrel jack", "Blue blocks: loosen the screw, push the bare wire end in from the side, tighten. Barrel jack: round socket for a DC plug.",
      _part("Screw terminal and barrel jack", '<rect x="20" y="40" width="60" height="40" fill="#2f6fd0"/><circle cx="36" cy="52" r="7" fill="#c9ced1"/><circle cx="64" cy="52" r="7" fill="#c9ced1"/>'
        '<rect x="28" y="70" width="14" height="8" fill="#111"/><rect x="58" y="70" width="14" height="8" fill="#111"/>'
        '<rect x="120" y="36" width="56" height="48" rx="4" fill="#1b1b1b"/><circle cx="148" cy="60" r="12" fill="#333"/><circle cx="148" cy="60" r="3" fill="#c9ced1"/>')))
    P.append(("MPU6050 IMU (GY-521 board)", "Small blue board, a square chip in the middle, a row of 8 pins: VCC, GND, SCL, SDA, XDA, XCL, AD0, INT. Arrows printed on it show its X and Y axes.",
      _part("MPU6050 board", '<rect x="40" y="10" width="120" height="84" rx="4" fill="#2a4f9a"/><rect x="88" y="34" width="24" height="24" fill="#111"/>'
        '<path d="M60 74 H84 M60 74 V50" stroke="#fff" stroke-width="2"/><text x="88" y="78" font-size="9" fill="#fff">X</text><text x="56" y="46" font-size="9" fill="#fff">Y</text>'
        + "".join(f'<rect x="{48 + i * 14}" y="88" width="6" height="10" fill="#d6c27a"/>' for i in range(8))
        + '<text class="tiny" x="40" y="114">VCC GND SCL SDA XDA XCL AD0 INT</text>')))
    P.append(("4760 VGA adapter board", "The green board from Lab 2 with the VGA socket and 7 pins (HSYNC, VSYNC, GND, L GREEN, H GREEN, BLUE, RED). Resistors are on it.",
      _part("VGA adapter", '<rect x="40" y="20" width="120" height="70" rx="3" fill="#2e8b3e"/><path d="M60 30 h50 l-6 26 h-38 z" fill="#2f6fd0"/>'
        + "".join(f'<rect x="{50 + i * 15}" y="90" width="6" height="14" fill="#d6c27a"/>' for i in range(7))
        + '<rect x="120" y="40" width="30" height="8" fill="#d9c49a"/><rect x="120" y="54" width="30" height="8" fill="#d9c49a"/>')))
    P.append(("Motor and propeller", "Small DC motor with two wires, propeller pressed on its shaft, mounted at the end of the arm.",
      _part("Motor and propeller", '<rect x="84" y="50" width="32" height="44" rx="6" fill="#9aa0a3"/><rect x="98" y="38" width="4" height="12" fill="#555"/>'
        '<ellipse cx="100" cy="34" rx="70" ry="7" fill="#e14b3b"/><path d="M92 94 C90 108 70 110 60 112 M108 94 C110 108 130 110 140 112" stroke-width="2" fill="none" stroke="#c0392b"/>'
        '<path d="M108 94 C112 106 132 106 142 106" stroke="#111" stroke-width="2" fill="none"/>')))
    P.append(("Bench power supply", "Two outputs: 12 V for the gate drive, 5–6 V for the motor (or a 5 V adapter into the barrel jack, as the TA sets up). Set the voltage before connecting.",
      _part("Bench supply", '<rect x="20" y="20" width="160" height="84" rx="4" fill="#d5d8d4" stroke="#8a8f8d"/>'
        '<rect x="34" y="32" width="56" height="22" fill="#111"/><text x="62" y="48" font-size="12" fill="#ff5a3c" text-anchor="middle" font-family="JetBrains Mono, monospace">12.0</text>'
        '<rect x="110" y="32" width="56" height="22" fill="#111"/><text x="138" y="48" font-size="12" fill="#ff5a3c" text-anchor="middle" font-family="JetBrains Mono, monospace">5.0</text>'
        '<circle cx="50" cy="82" r="7" fill="#d33"/><circle cx="74" cy="82" r="7" fill="#111"/><circle cx="126" cy="82" r="7" fill="#d33"/><circle cx="150" cy="82" r="7" fill="#111"/>')))
    out = ['<div class="parts">']
    for name, desc, svg in P:
        out.append(f'<figure class="part"><div class="fig">{svg}</div><figcaption><b>{name}</b> {desc}</figcaption></figure>')
    out.append('</div>')
    return "\n".join(out)


def system():
    """Everything connected: laptop, adapter, Pico, motor board, supply, motor, IMU, VGA."""
    def py(p):  # pin y on this drawing
        return 140 + 17 * (p - 1) if p <= 20 else 140 + 17 * (40 - p)
    o = ['<svg class="wiring sys" viewBox="0 0 920 560" role="img" aria-label="Whole Lab 3 system wired up. '
         'Laptop to USB-serial adapter to Pico pins 1 to 3. Pico pin 6 and 8 to the motor board PWM and MCU GND terminals. '
         'Bench supply 12 V and ground to the motor board, 5 V to its barrel jack. Motor to MOTOR+ and MOTOR-. '
         'IMU on pins 11 to 13 and 3V3 pin 36. VGA adapter on pins 21 to 27 to the monitor.">']
    o.append('<defs><style>.wa{stroke:var(--accent);stroke-width:2;fill:none}.wm{stroke:var(--warn);stroke-width:2.4;fill:none}'
             '.wg{stroke:var(--ink-2);stroke-width:2;fill:none}</style></defs>')
    # Pico
    o.append('<rect x="430" y="120" width="110" height="360" rx="5" fill="#1f7a3a"/>'
             '<rect x="472" y="104" width="26" height="18" rx="2" fill="#b8bec2"/>'
             '<text x="485" y="310" font-size="13" font-weight="700" fill="#fff" text-anchor="middle" transform="rotate(-90 485 310)" font-family="Archivo, sans-serif">Pico 2</text>')
    for p in range(1, 41):
        x = 430 if p <= 20 else 540
        o.append(f'<circle cx="{x}" cy="{py(p)}" r="3" fill="#d6c27a"/>')
    def lab(p, side):
        x = 436 if side == "l" else 534
        a = "start" if side == "l" else "end"
        o.append(f'<text x="{x}" y="{py(p) + 3}" font-size="9" fill="#fff" text-anchor="{a}" font-family="JetBrains Mono, monospace">{p}·{PINS[p]}</text>')
    for p in (1, 2, 3, 6, 8, 11, 12, 13, 19, 20):
        lab(p, "l")
    for p in (36, 21, 22, 23, 24, 25, 26, 27):
        lab(p, "r")
    # laptop + adapter
    o.append('<rect class="boxf" x="280" y="20" width="110" height="50"/><text class="blkh" x="290" y="42">Laptop</text><text class="tiny" x="290" y="58">screen … 115200</text>')
    o.append('<path class="wg" d="M335 70 V122"/>')
    o.append('<rect x="290" y="122" width="90" height="64" rx="3" fill="#2a4f9a"/><text x="296" y="114" class="tiny">USB-serial adapter</text>')
    for p, t in ((1, "RX"), (2, "TX"), (3, "GND")):
        o.append(f'<text x="374" y="{py(p) + 3}" font-size="9" fill="#fff" text-anchor="end" font-family="JetBrains Mono, monospace">{t}</text>')
        o.append(f'<path class="{"wg" if t == "GND" else "wa"}" d="M380 {py(p)} H427"/>')
    # motor board
    o.append('<rect x="200" y="200" width="180" height="90" rx="3" fill="#2e8b3e"/><text x="206" y="194" class="blkh">Motor board</text>')
    o.append('<rect x="200" y="200" width="180" height="90" rx="3" fill="none" stroke="#1d5c2a"/>')
    for p, t in ((6, "PWM"), (8, "MCU GND")):
        o.append(f'<rect x="366" y="{py(p) - 7}" width="14" height="14" fill="#2f6fd0"/><text x="362" y="{py(p) + 3}" font-size="9" fill="#fff" text-anchor="end" font-family="JetBrains Mono, monospace">{t}</text>')
        o.append(f'<path class="{"wg" if p == 8 else "wa"}" d="M380 {py(p)} H427"/>')
    o.append('<rect x="200" y="206" width="14" height="14" fill="#2f6fd0"/><rect x="200" y="226" width="14" height="14" fill="#2f6fd0"/>'
             '<text x="218" y="216" font-size="9" fill="#fff" font-family="JetBrains Mono, monospace">12V</text><text x="218" y="236" font-size="9" fill="#fff" font-family="JetBrains Mono, monospace">PSU GND</text>'
             '<rect x="200" y="254" width="20" height="22" fill="#111"/><text x="224" y="268" font-size="9" fill="#fff" font-family="JetBrains Mono, monospace">jack</text>'
             '<rect x="276" y="276" width="14" height="14" fill="#2f6fd0"/><rect x="300" y="276" width="14" height="14" fill="#2f6fd0"/>'
             '<text x="270" y="272" font-size="9" fill="#fff" font-family="JetBrains Mono, monospace">M+  M−</text>'
             '<rect x="300" y="214" width="22" height="10" fill="#111"/><text x="296" y="244" font-size="9" fill="#fff" font-family="JetBrains Mono, monospace">KILL</text>')
    # supply
    o.append('<rect x="20" y="200" width="120" height="86" rx="4" fill="#d5d8d4" stroke="#8a8f8d"/><text class="blkh" x="20" y="194">Bench supply</text>'
             '<text x="30" y="226" font-size="10" fill="#222" font-family="JetBrains Mono, monospace">12 V +</text><text x="30" y="246" font-size="10" fill="#222" font-family="JetBrains Mono, monospace">12 V −</text>'
             '<text x="30" y="270" font-size="10" fill="#222" font-family="JetBrains Mono, monospace">5 V</text>')
    o.append('<path class="wm" d="M140 213 H200"/><path class="wg" d="M140 233 H200"/><path class="wm" d="M140 265 H200"/>')
    # motor
    o.append('<path class="wm" d="M283 290 V340 M307 290 V340"/>'
             '<rect x="279" y="340" width="32" height="40" rx="5" fill="#9aa0a3"/><ellipse cx="295" cy="390" rx="50" ry="6" fill="#e14b3b"/>'
             '<text class="tiny" x="272" y="356" text-anchor="end">motor + propeller</text><text class="tiny" x="272" y="370" text-anchor="end">(end of the arm)</text>')
    # IMU
    o.append('<rect x="250" y="440" width="120" height="70" rx="4" fill="#2a4f9a"/><rect x="298" y="462" width="22" height="22" fill="#111"/>'
             '<text class="blkh" x="250" y="528">IMU (on the arm)</text>')
    # each wire turns at its own x and y so none cross
    for p, t, cls in ((11, "SDA", "wa"), (12, "SCL", "wa"), (13, "GND", "wg")):
        xi, xv, yl = {11: (290, 394, 404), 12: (320, 402, 414), 13: (350, 410, 424)}[p]
        o.append(f'<path class="{cls}" d="M427 {py(p)} H{xv} V{yl} H{xi} V440"/>')
        o.append(f'<text x="{xi}" y="452" font-size="8" fill="#fff" text-anchor="middle" font-family="JetBrains Mono, monospace">{t}</text>')
    o.append(f'<path class="wa" d="M543 {py(36)} H580 V540 H270 V510"/>'
             '<text x="270" y="503" font-size="8" fill="#fff" text-anchor="middle" font-family="JetBrains Mono, monospace">VCC</text>'
             f'<text class="tiny" x="586" y="{py(36) + 4}">3.3 V to IMU VCC</text>')
    # scope
    for p in (19, 20):
        o.append(f'<path class="wg" d="M427 {py(p)} H405" stroke-dasharray="3 3"/>')
    o.append(f'<text class="tiny" x="402" y="{py(20) + 16}" text-anchor="end">scope</text>')
    # VGA
    o.append(f'<rect x="610" y="{py(27) - 10}" width="110" height="{py(21) - py(27) + 20}" rx="3" fill="#2e8b3e"/>'
             f'<text class="blkh" x="610" y="{py(27) - 16}">VGA adapter</text>')
    for p in range(21, 28):
        o.append(f'<path class="{"wg" if p == 23 else "wa"}" d="M543 {py(p)} H610"/>')
    o.append(f'<rect x="760" y="{py(27)}" width="140" height="90" rx="4" fill="#111" stroke="#555"/><text x="830" y="{py(27) + 50}" font-size="11" fill="#ddd" text-anchor="middle" font-family="Archivo, sans-serif">VGA monitor</text>'
             f'<path class="wg" d="M720 {py(24)} H760"/>')
    # legend
    o.append('<path class="wa" d="M620 40 H650"/><text class="tiny" x="656" y="44">Pico-side signal (3.3 V)</text>'
             '<path class="wm" d="M620 60 H650"/><text class="tiny" x="656" y="64">motor-side power (12 V, 5 V, motor)</text>'
             '<path class="wg" d="M620 80 H650"/><text class="tiny" x="656" y="84">ground / cable</text>'
             '<text class="tiny" x="620" y="110">Orange never touches blue.</text>'
             '<text class="tiny" x="620" y="124">PSU GND and Pico GND stay separate.</text>')
    o.append('</svg>')
    return "\n".join(o)


FIGS["parts"] = parts
FIGS["system"] = system
