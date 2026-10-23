#!/usr/bin/env python3
"""Search for good PID gains on the helicopter arm.

Needs the sweep test firmware (tools/pid-tuning/firmware-sweep), which
prints "L,<ms>,<angle>,<target>,<motor>,<rate>,<pid_on>" 20 times a second and
turns the motor off by itself above +60 deg.

    python3 tools/pid-tuning/pid-sweep.py            # full search (about 20-25 minutes)
    python3 tools/pid-tuning/pid-sweep.py --quick    # short version, to check it works

Phases:
  1. coarse grid of Kp x Kd (Ki = 0), target 0 deg, starting from hanging
  2. refine Kp and Kd around the best (nudge each up/down, keep improvements)
  3. add Ki: a few values, then refine
  4. check the result over the range: 0 -> +30 -> -30 -> 0 deg without stopping
     (the week 3 demo sequence), scoring each step

Each try starts with the motor off and the arm hanging still. The script stops
the motor above ABORT_DEG, and stops everything if the Pico goes quiet. Keep a
hand on the killswitch anyway.

Results: printed as it goes, and saved to /tmp/pid-sweep-summary.txt and
/tmp/pid-sweep-samples.csv.
"""
import glob, os, select, statistics, sys, termios, threading, time

# The Debug Probe's serial port; its number changes with the USB port it's in
PORTS = sorted(glob.glob("/dev/tty.usbmodem*"))
if not PORTS:
    sys.exit("No /dev/tty.usbmodem* port: is the Debug Probe plugged in?")
PORT = PORTS[0]
ABORT_DEG = 50.0      # script stops the motor above this (the Pico itself cuts at 60)
SETTLE_BAND = 3.0     # deg: "settled" = stays within this of its final angle
LIMITS = (200.0, 40.0, 120.0)   # highest Kp, Kd, Ki the search may try
QUICK = "--quick" in sys.argv
MAX_TRIES = 12 if QUICK else 60

if QUICK:
    GRID = [(kp, kd) for kp in (20, 40) for kd in (6, 2)]
else:
    GRID = [(kp, kd) for kp in (20, 30, 45, 60, 80) for kd in (10, 6, 3, 0)]

samples = []          # (host_time, ms, angle, target, motor, rate, pid_on)
lock = threading.Lock()
log_lines = []


def say(text=""):
    print(text, flush=True)
    log_lines.append(text)


fd = os.open(PORT, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
a = termios.tcgetattr(fd)
a[0] = a[1] = a[3] = 0
a[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL
a[4] = a[5] = termios.B115200
termios.tcsetattr(fd, termios.TCSANOW, a)


def reader():
    buf = ""
    while True:
        r, _, _ = select.select([fd], [], [], 0.2)
        if not r:
            continue
        try:
            buf += os.read(fd, 4096).decode(errors="replace")
        except BlockingIOError:
            continue
        except OSError:
            return
        *lines, buf = buf.split("\n")
        for line in lines:
            f = line.strip().split(",")
            if len(f) == 7 and f[0] == "L":
                try:
                    row = (time.time(), int(f[1]), float(f[2]), float(f[3]),
                           int(f[4]), float(f[5]), int(f[6]))
                except ValueError:
                    continue
                with lock:
                    samples.append(row)


threading.Thread(target=reader, daemon=True).start()


class PicoQuiet(Exception):
    pass


class TooMany(Exception):
    pass


def latest():
    with lock:
        return samples[-1] if samples else None


def check_alive():
    s = latest()
    if s is None or time.time() - s[0] > 1.0:
        raise PicoQuiet()


def send(cmd, value=None):
    os.write(fd, cmd.encode() + b"\r")
    time.sleep(0.25)
    if value is not None:
        os.write(fd, str(value).encode() + b"\r")
        time.sleep(0.25)


def stop():
    send("s")
    send("s")


def wait_hanging(timeout=20.0):
    """Wait until the arm hangs still (motor off, low, not moving)."""
    t0 = time.time()
    still_since = None
    while time.time() - t0 < timeout:
        time.sleep(0.1)
        check_alive()
        s = latest()
        if s[6] == 0 and s[2] < -55 and abs(s[5]) < 8:
            still_since = still_since or time.time()
            if time.time() - still_since > 1.5:
                return True
        else:
            still_since = None
    return False


def record(seconds, t0):
    """Record until `seconds` after t0; return an abort reason or ''."""
    while time.time() - t0 < seconds:
        time.sleep(0.05)
        check_alive()
        s = latest()
        if s[2] > ABORT_DEG:
            return f"went above {ABORT_DEG:.0f} deg"
        if s[6] == 0 and time.time() - t0 > 1.0:
            return "Pico cut the motor (above 60 deg)"
    return ""


def analyse(rs, t0, target, aborted):
    if len(rs) < 20:
        return dict(ok=False, why=aborted or "too few samples")
    t = [r[0] - t0 for r in rs]
    ang = [r[2] for r in rs]
    mot = [r[4] for r in rs]
    tail_t = [tt for tt in t if tt > t[-1] - 3.0]
    tail = ang[-len(tail_t):]
    final = statistics.mean(tail)
    # split the last 3 s into a straight-line drift and the swinging around it
    tm = statistics.mean(tail_t)
    slope = (sum((tt - tm) * (x - final) for tt, x in zip(tail_t, tail))
             / max(1e-9, sum((tt - tm) ** 2 for tt in tail_t)))
    wobble = statistics.pstdev([x - (final + slope * (tt - tm)) for tt, x in zip(tail_t, tail)])
    drift = slope
    start = ang[0]
    up = target >= start
    peak = max(ang) if up else min(ang)
    overshoot = max(0.0, (peak - target) if up else (target - peak))
    settle = 0.0
    for tt, x in zip(t, ang):
        if abs(x - final) > SETTLE_BAND:
            settle = tt
    sat = sum(1 for m in mot if m >= 5990) / len(mot)
    return dict(ok=not aborted, why=aborted, final=final, err=target - final,
                wobble=wobble, drift=drift, peak=peak, overshoot=overshoot,
                settle=settle, sat=sat)


tries = 0


def run(kp, kd, ki, target=0.0):
    """One try from hanging still. Returns the analysis."""
    global tries
    if tries >= MAX_TRIES:
        raise TooMany()
    tries += 1
    stop()
    if not wait_hanging():
        say("  (arm didn't settle hanging; going on anyway)")
    send("p", kp)
    send("d", kd)
    send("i", ki)
    with lock:
        start = len(samples)
    t0 = time.time()
    send("a", target)
    aborted = record(16.0 if ki else 12.0, t0)
    with lock:
        rs = samples[start:]      # only up to now: after stop() the arm falls
    stop()
    return analyse(rs, t0, target, aborted)


def score(r):
    """Lower is better. Failing, or never getting near the target, is worst."""
    if not r.get("ok"):
        return 1e9
    if r["final"] < -55:            # never really lifted off the bottom
        return 1e6 + abs(r["err"])
    # distance from target and swinging matter most; then creeping, overshoot,
    # and how long it took to settle
    return (2 * abs(r["err"]) + 3 * r["wobble"] + 3 * abs(r["drift"])
            + 0.5 * r["overshoot"] + 0.5 * r["settle"])


def fmt(kp, kd, ki, r, target=0.0):
    head = f"Kp {kp:>5.1f} Kd {kd:>5.1f} Ki {ki:>5.1f} -> {target:+4.0f}"
    if "final" not in r:
        return f"{head} | {r['why']}"
    flag = "" if r["ok"] else f"  ABORTED: {r['why']}"
    return (f"{head} | final {r['final']:6.1f}  wobble ±{r['wobble']:4.1f}"
            f"  drift {r['drift']:+5.1f}/s  overshoot {r['overshoot']:5.1f}  settle {r['settle']:4.1f} s"
            f"  full-power {100 * r['sat']:3.0f}%  score {score(r):6.1f}{flag}")


results = {}          # (kp, kd, ki) -> analysis


def trial(kp, kd, ki):
    key = (round(kp, 1), round(kd, 1), round(ki, 1))
    if key not in results:
        results[key] = run(*key)
        say(fmt(*key, results[key]))
    return results[key]


def refine(point, which, factors=(0.75, 1.33), rounds=3):
    """Nudge the gains named in `which` up and down; keep what helps."""
    best = point
    best_s = score(trial(*best))
    for _ in range(rounds):
        improved = False
        for i in which:
            for f in factors:
                cand = list(best)
                cand[i] = min(LIMITS[i], max(0.0, round(best[i] * f if best[i] else 2.0, 1)))
                if tuple(cand) == best:
                    continue
                s = score(trial(*cand))
                if s < best_s:
                    best, best_s, improved = tuple(cand), s, True
        if not improved:
            break
    return best


def sequence(kp, kd, ki):
    """Week 3 demo shape: 0 -> +30 -> -30 -> 0, without stopping in between."""
    say(f"\nRange check with Kp {kp} Kd {kd} Ki {ki}: 0 -> +30 -> -30 -> 0 deg")
    stop()
    wait_hanging()
    send("p", kp)
    send("d", kd)
    send("i", ki)
    out = []
    for target in (0, 30, -30, 0):
        with lock:
            start = len(samples)
        t0 = time.time()
        send("a", target)
        aborted = record(10.0, t0)
        with lock:
            rs = samples[start:]
        r = analyse(rs, t0, target, aborted)
        out.append((target, r))
        say("  " + fmt(kp, kd, ki, r, target))
        if aborted:
            break
    stop()
    return out


best = None
try:
    time.sleep(1.0)
    check_alive()
    say("Connected. Hand on the killswitch.\n\nPhase 1: coarse Kp x Kd grid, Ki = 0, target 0 deg")
    unstable_kd = set()
    for kp, kd in GRID:
        if kd in unstable_kd:
            say(f"Kp {kp:>5.1f} Kd {kd:>5.1f} skipped (unstable at a lower Kp)")
            continue
        r = trial(kp, kd, 0)
        if not r.get("ok") or r.get("wobble", 0) > 10:
            unstable_kd.add(kd)
    ok = [k for k, r in results.items() if r.get("ok")]
    if not ok:
        raise SystemExit("Nothing in the coarse grid was stable. Check the motor and wiring.")
    best = min(ok, key=lambda k: score(results[k]))

    say(f"\nPhase 2: refine Kp and Kd around {best}")
    best = refine(best, which=(0, 1))

    say(f"\nPhase 3: add Ki to {best}")
    for ki in ((10,) if QUICK else (5, 10, 20, 40)):
        trial(best[0], best[1], ki)
    best = min((k for k in results if k[:2] == best[:2] and results[k].get("ok")),
               key=lambda k: score(results[k]))
    if best[2]:
        best = refine(best, which=(2,), rounds=2)
        best = refine(best, which=(0, 1), rounds=1)

    seq = sequence(*best)
except PicoQuiet:
    say("\nThe Pico stopped sending data. Use the KILLSWITCH: the motor may still be on.")
    seq = []
except TooMany:
    say(f"\nStopped after {MAX_TRIES} tries.")
    seq = []
except KeyboardInterrupt:
    say("\nStopped by you.")
    seq = []
finally:
    try:
        stop()
    except OSError:
        pass

ranked = sorted(results.items(), key=lambda kv: score(kv[1]))
say("\n=== Ranked (best first) ===")
for (kp, kd, ki), r in ranked:
    say(fmt(kp, kd, ki, r))
if best:
    say(f"\nBest found: Kp {best[0]}  Kd {best[1]}  Ki {best[2]}")
    if seq:
        bad = [t for t, r in seq if not r.get("ok") or r["wobble"] > 3 or abs(r["err"]) > 5]
        say("Range check: " + ("passed" if not bad else f"problems at {bad} deg"))
open("/tmp/pid-sweep-summary.txt", "w").write("\n".join(log_lines) + "\n")
with lock, open("/tmp/pid-sweep-samples.csv", "w") as f:
    f.write("host_time,ms,angle,target,motor,rate,pid_on\n")
    for row in samples:
        f.write(",".join(str(x) for x in row) + "\n")
os.close(fd)
