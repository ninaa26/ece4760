"""Report diagrams for ECE 4760 Lab 1, drawn from the submitted code and wiring."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch, Rectangle
import os, sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
INK = "#1f2328"; MUTE = "#57606a"; BLUE = "#0969da"; GREEN = "#1a7f37"; ORANGE = "#bc4c00"; PURPLE = "#8250df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

def box(ax, x, y, w, h, label, fc="#f6f8fa", ec=INK, fs=9, weight="normal", r=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, weight=weight, color=INK)

def wire(ax, pts, color=INK, lw=1.3):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="round")

def arrow(ax, a, b, color=INK, text=None, rad=0.0, fs=8, lw=1.3, toff=(0, 0)):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=11, color=color, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))
    if text:
        mx, my = (a[0] + b[0]) / 2 + toff[0], (a[1] + b[1]) / 2 + toff[1]
        ax.text(mx, my, text, ha="center", va="center", fontsize=fs, color=color,
                bbox=dict(fc="white", ec="none", pad=1.2))

def dot(ax, x, y, c=INK):
    ax.add_patch(Circle((x, y), 0.06, color=c, zorder=5))

# ---------------------------------------------------------------- schematic
fig, ax = plt.subplots(figsize=(12.5, 7.4))
ax.set_xlim(-1.2, 23.8); ax.set_ylim(0, 14.4); ax.axis("off")

# Pico
px, py, pw, ph = 8.2, 1.2, 5.8, 11.0
ax.add_patch(Rectangle((px, py), pw, ph, fc="#eef6ee", ec=INK, lw=1.5))
ax.text(px + pw / 2, py + ph - 0.45, "Raspberry Pi\nPico 2 (RP2350)", ha="center", va="top", weight="bold", fontsize=10)
left = {  # label: y   (left edge = to DAC / audio)
    "3V3(OUT)  pin 36": 10.6, "GND  pin 38": 9.9,
    "GPIO 5  (CS)": 9.0, "GPIO 6  (SCK)": 8.3, "GPIO 7  (MOSI)": 7.6,
    "GPIO 2  (ISR timing)": 6.4, "GPIO 26  (ADC0)": 4.2,
}
right = {"GPIO 9   (row 1)": 10.4, "GPIO 10  (row 2)": 9.7, "GPIO 11  (row 3)": 9.0, "GPIO 12  (row 4)": 8.3,
         "GPIO 13  (col 1)": 7.3, "GPIO 14  (col 2)": 6.6, "GPIO 15  (col 3)": 5.9,
         "RUN  pin 30": 3.4, "GND  pin 28": 2.6}
for lab, y in left.items():
    ax.text(px + 0.12, y, lab, ha="left", va="center", fontsize=8)
for lab, y in right.items():
    ax.text(px + pw - 0.12, y, lab, ha="right", va="center", fontsize=8)

# MCP4822
dx, dy, dw, dh = 1.4, 6.9, 3.6, 4.6
ax.add_patch(Rectangle((dx, dy), dw, dh, fc="#eef3fb", ec=INK, lw=1.5))
ax.text(dx + dw / 2, dy + dh + 0.3, "MCP4822 DAC", ha="center", weight="bold", fontsize=10)
dl = {"1 VDD": 10.6, "2 CS": 9.0, "3 SCK": 8.3, "4 SDI": 7.6}   # right-hand side faces Pico
dr = {"8 VOUTA": 10.6, "7 VSS": 9.9, "6 VOUTB": 7.3, "5 LDAC": 9.3}
for lab, y in dl.items():
    ax.text(dx + dw - 0.1, y, lab, ha="right", va="center", fontsize=8)
for lab, y in {"8 VOUTA (n/c)": 11.1, "7 VSS": 9.9, "5 LDAC": 9.3, "6 VOUTB": 7.3}.items():
    ax.text(dx + 0.1, y, lab, ha="left", va="center", fontsize=8)

# power rails
wire(ax, [(px, 10.6), (dx + dw, 10.6)], color="#cf222e")                 # 3V3 -> VDD
ax.text(7.3, 10.75, "3.3 V", color="#cf222e", fontsize=8, ha="center")
wire(ax, [(px, 9.9), (6.4, 9.9), (6.4, 12.6), (0.6, 12.6), (0.6, 9.9), (dx, 9.9)], color=MUTE)  # GND -> VSS
wire(ax, [(0.6, 9.3), (dx, 9.3)], color=MUTE); dot(ax, 0.6, 9.3, MUTE); dot(ax, 0.6, 9.9, MUTE)
wire(ax, [(0.6, 9.9), (0.6, 9.3)], color=MUTE)
ax.text(3.5, 12.8, "GND (LDAC tied low → output updates on every word)", color=MUTE, fontsize=7.5, ha="center")
# SPI
for y in (9.0, 8.3, 7.6):
    wire(ax, [(px, y), (dx + dw, y)], color=BLUE)
ax.text(6.6, 8.45, "SPI0, 20 MHz, 16-bit", color=BLUE, fontsize=8, ha="center")

# Audio jack
wire(ax, [(dx, 7.3), (0.2, 7.3), (0.2, 5.6)], color=ORANGE)
box(ax, -1.0, 4.4, 2.6, 1.2, "3.5 mm socket\ntip ← VOUTB\nsleeve → GND", fc="#fff4e5", fs=7.5)
wire(ax, [(0.2, 6.5), (2.9, 6.5), (2.9, 6.0)], color=ORANGE); dot(ax, 0.2, 6.5, ORANGE)
box(ax, 2.0, 4.8, 1.8, 1.2, "scope\nprobe", fc="#fff4e5", fs=8)

# ISR timing pin
wire(ax, [(px, 6.4), (7.4, 6.4), (7.4, 5.6)], color=PURPLE)
box(ax, 6.6, 4.4, 1.5, 1.2, "scope\nGPIO 2", fc="#f5f0ff", fs=7.5)

# Pot
wire(ax, [(px, 4.2), (5.4, 4.2), (5.4, 3.2)], color=GREEN)
ax.add_patch(Rectangle((2.4, 2.2), 4.2, 0.6, fc="#eaf5ea", ec=INK, lw=1.2))
ax.text(4.5, 1.85, "slide potentiometer (Adafruit 4219, linear)", ha="center", fontsize=8)
arrow(ax, (5.4, 3.2), (5.4, 2.85), color=GREEN)
ax.text(5.55, 3.4, "pin 2 wiper", fontsize=7.5, color=GREEN)
ax.text(2.2, 2.5, "pin 1\n3.3 V", ha="right", va="center", fontsize=7.5)
ax.text(6.8, 2.5, "pin 3\nGND", ha="left", va="center", fontsize=7.5)

# Keypad
kx, ky = 18.6, 5.4
ax.add_patch(Rectangle((kx, ky), 4.2, 5.6, fc="#f6f8fa", ec=INK, lw=1.5))
ax.text(kx + 2.1, ky + 5.9, "3×4 keypad", ha="center", weight="bold", fontsize=10)
keys = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["*", "0", "#"]]
for r in range(4):
    for c in range(3):
        box(ax, kx + 0.5 + c * 1.2, ky + 4.3 - r * 1.25, 0.9, 0.9, keys[r][c], fc="white", fs=10)
rows_y = [10.4, 9.7, 9.0, 8.3]
for i, y in enumerate(rows_y):
    ky_row = ky + 4.75 - i * 1.25
    wire(ax, [(px + pw, y), (15.3, y)], color=INK)
    ax.add_patch(Rectangle((15.3, y - 0.12), 0.9, 0.24, fc="white", ec=INK, lw=1.1))
    wire(ax, [(16.2, y), (17.6 - i * 0.2, y), (17.6 - i * 0.2, ky_row), (kx, ky_row)], color=INK)
ax.text(15.75, 10.75, "330 Ω ×4", ha="center", fontsize=8)
for j, y in enumerate([7.3, 6.6, 5.9]):
    cx = kx + 0.95 + j * 1.2
    wire(ax, [(px + pw, y), (14.8 + j * 0.25, y), (14.8 + j * 0.25, 4.6 - j * 0.35), (cx, 4.6 - j * 0.35), (cx, ky)], color=GREEN)
ax.text(20.7, 12.3, "rows driven low one at a time;\ncolumns use internal pull-ups", fontsize=7.5, color=GREEN, ha="center")
ax.text(20.7, 1.5, "header order on the part:\nCol1 Col2 Col3 Row1 Row2 Row3 Row4 NC", ha="center", fontsize=7, color=MUTE)

# Reset button
wire(ax, [(px + pw, 3.4), (16.5, 3.4)]); wire(ax, [(px + pw, 2.6), (16.5, 2.6)])
wire(ax, [(16.5, 3.4), (16.5, 3.15)]); wire(ax, [(16.5, 2.6), (16.5, 2.85)])
wire(ax, [(16.2, 3.15), (16.8, 3.15)]); ax.plot([16.2, 16.8], [2.85, 2.85], color=INK, lw=1.3)
ax.text(17.1, 3.0, "reset button\n1 press: reset\n2 presses: bootloader", va="center", ha="left", fontsize=7.5)

ax.text(11.3, 0.35, "Pin numbers from the MCP4822 datasheet and the course's keypad and program-button pages; wiring as built.",
        ha="center", fontsize=7.5, color=MUTE)
fig.savefig(f"{OUT}/fig_schematic.png", dpi=220, bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- block diagram
fig, ax = plt.subplots(figsize=(11.5, 5.6))
ax.set_xlim(0, 23); ax.set_ylim(0, 11.2); ax.axis("off")
box(ax, 0.4, 8.2, 3.6, 1.6, "Slide pot\n(ADC0)", fc="#eaf5ea")
box(ax, 0.4, 4.6, 3.6, 1.6, "Keypad\n(GPIO 9–15)", fc="#f6f8fa")
box(ax, 5.2, 8.0, 5.4, 2.0, "protothread_toggle25\n100 Hz\nread ADC · set pitch · record", fc="#eaf5ea", fs=8.5)
box(ax, 5.2, 4.4, 5.4, 2.0, "protothread_core_0\n33 Hz\nscan · debounce · set modes", fc="#f6f8fa", fs=8.5)
box(ax, 5.2, 0.8, 5.4, 2.0, "protothread_playback\n1 kHz\nreplay key or sequence", fc="#fff4e5", fs=8.5)
box(ax, 12.5, 2.6, 5.0, 6.6, "shared globals\n\nphase_incr_main\ntone\n\nrecording, playing\nrecord_mode, record_key\ncompose_mode,\ncompose_playing\n\nrecordings[10][1000]\nrecord_length[10]\ncompose_sequence[10]",
    fc="#fbfbfb", fs=7.8)
box(ax, 19.0, 6.4, 3.6, 2.6, "alarm_irq\n50 kHz ISR\nDDS, sine table,\nSPI write", fc="#eef3fb", fs=8.5, weight="bold")
box(ax, 19.0, 2.4, 3.6, 1.8, "MCP4822\nVOUTB → speaker,\nscope", fc="#eef3fb", fs=8)
arrow(ax, (4.0, 9.0), (5.2, 9.0))
arrow(ax, (4.0, 5.4), (5.2, 5.4))
arrow(ax, (10.6, 9.0), (12.6, 8.4), text="pitch (unless playing),\nsamples", fs=7, toff=(0, 0.55))
arrow(ax, (10.6, 5.4), (12.6, 5.4), text="mode flags", fs=7, toff=(0, 0.35))
arrow(ax, (12.6, 3.0), (10.6, 2.2), text="which key(s)", fs=7, toff=(0, 0.45))
arrow(ax, (10.6, 1.4), (13.2, 2.6), text="pitch", fs=7, rad=0.25, toff=(0.6, -0.6))
arrow(ax, (17.5, 7.7), (19.0, 7.7), text="phase_incr_main,\ntone", fs=7, toff=(0, 0.6))
arrow(ax, (20.8, 6.4), (20.8, 4.2), text="SPI, 16-bit", fs=7, toff=(1.0, 0))
ax.text(11.5, 10.8, "Threads are cooperative (protothreads, core 0); the ISR pre-empts them every 20 µs. GPIO 2 is high while the ISR runs.",
        ha="center", fontsize=8, color=MUTE)
fig.savefig(f"{OUT}/fig_block.png", dpi=220, bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- debounce FSM
fig, ax = plt.subplots(figsize=(9, 5.4))
ax.set_xlim(0, 18); ax.set_ylim(0, 10.8); ax.axis("off")
S = {"NOT_PRESSED": (3.2, 7.6), "MAYBE_PRESSED": (14.8, 7.6), "PRESSED": (14.8, 2.6), "MAYBE_NOT_PRESSED": (3.2, 2.6)}
for n, (x, y) in S.items():
    ax.add_patch(Circle((x, y), 1.55, fc="#f6f8fa", ec=INK, lw=1.5))
    ax.text(x, y, n.replace("_", "_\n", 1) if len(n) > 11 else n, ha="center", va="center", fontsize=8.5, weight="bold")
arrow(ax, (4.8, 8.1), (13.2, 8.1), text="valid key i ≥ 0\npossible_key = i", fs=8, toff=(0, 0.55))
arrow(ax, (13.2, 7.1), (4.8, 7.1), text="i ≠ possible_key", fs=8, toff=(0, -0.45))
arrow(ax, (14.8, 6.05), (14.8, 4.15), color=BLUE, text="i == possible_key\n→ ACTION FIRES\n(0, *, #, 1–9)", fs=8, toff=(0, 0))
arrow(ax, (13.2, 2.6), (4.8, 2.6), text="i ≠ possible_key", fs=8, toff=(0, 0.45))
arrow(ax, (4.6, 3.3), (13.3, 3.3), text="", rad=-0.0)
ax.text(9.0, 3.75, "i == possible_key (bounce)", ha="center", fontsize=8, bbox=dict(fc="white", ec="none", pad=1))
arrow(ax, (3.2, 4.15), (3.2, 6.05), color=ORANGE, text="i ≠ possible_key\n→ if recording this key:\nstop recording", fs=8)
ax.text(9, 0.35, "Sampled every 30 ms. A key must read the same on two consecutive scans; each action fires once per press.",
        ha="center", fontsize=8, color=MUTE)
ax.text(1.0, 9.8, "self-loops: NOT_PRESSED while i = −1;  PRESSED while i == possible_key", fontsize=7.5, color=MUTE)
fig.savefig(f"{OUT}/fig_fsm.png", dpi=220, bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- key handling flowchart
fig, ax = plt.subplots(figsize=(10, 7.2))
ax.set_xlim(0, 20); ax.set_ylim(-1.6, 12.8); ax.axis("off")
def dia(x, y, t):
    ax.add_patch(plt.Polygon([(x, y + 0.75), (x + 1.9, y), (x, y - 0.75), (x - 1.9, y)], fc="#fff8c5", ec=INK, lw=1.2))
    ax.text(x, y, t, ha="center", va="center", fontsize=8)
box(ax, 0.2, 11.2, 5.0, 1.0, "debounced press of key k", fc="#eef3fb", fs=8.5, weight="bold")
dia(2.7, 9.6, "k == 0 ?"); dia(2.7, 7.4, "k == * ?"); dia(2.7, 5.2, "k == # ?"); dia(2.7, 3.0, "k in 1–9 ?")
arrow(ax, (2.7, 11.2), (2.7, 10.35))
for y1, y2 in [(8.85, 8.15), (6.65, 5.95), (4.45, 3.75)]:
    arrow(ax, (2.7, y1), (2.7, y2), text="no", fs=7.5, toff=(0.4, 0))
box(ax, 6.0, 9.1, 4.8, 1.0, "tone = !tone", fs=8.5)
box(ax, 6.0, 6.9, 4.8, 1.0, "record_mode = !record_mode\nstop recording / playback", fs=8)
arrow(ax, (4.6, 9.6), (6.0, 9.6), text="yes", fs=7.5)
arrow(ax, (4.6, 7.4), (6.0, 7.4), text="yes", fs=7.5)
dia(7.9, 5.2, "compose_mode ?")
arrow(ax, (4.6, 5.2), (6.0, 5.2), text="yes", fs=7.5)
box(ax, 10.8, 5.3, 5.0, 1.0, "no → compose_mode on,\nsequence cleared", fs=8)
box(ax, 10.8, 4.0, 5.0, 1.0, "yes → compose_mode off,\nplay sequence", fs=8)
arrow(ax, (9.8, 5.3), (10.8, 5.8)); arrow(ax, (9.8, 5.1), (10.8, 4.5))
dia(7.9, 3.0, "compose_mode ?")
arrow(ax, (4.6, 3.0), (6.0, 3.0), text="yes", fs=7.5)
box(ax, 10.8, 2.5, 4.6, 1.0, "append k to sequence\n(max 10)", fs=8)
arrow(ax, (9.8, 3.0), (10.8, 3.0), text="yes", fs=7.5)
dia(7.9, 1.0, "record_mode ?")
arrow(ax, (7.9, 2.25), (7.9, 1.75), text="no", fs=7.5, toff=(0.4, 0))
box(ax, 10.8, 0.1, 4.6, 1.0, "clear key k, start recording\n(stops when k is released)", fs=8)
arrow(ax, (9.8, 1.0), (10.8, 0.6), text="yes", fs=7.5)
box(ax, 5.6, -1.5, 4.6, 1.0, "if key k has a recording,\nplay it at 10×; else \"empty\"", fs=8)
arrow(ax, (7.9, 0.25), (7.9, -0.5), text="no", fs=7.5, toff=(0.4, 0))
fig.savefig(f"{OUT}/fig_keys.png", dpi=220, bbox_inches="tight"); plt.close(fig)
print("ok")
