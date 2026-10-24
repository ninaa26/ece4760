#!/usr/bin/env python3
"""Run ONE PID experiment on the helicopter arm and report what happened.

Meant to be run repeatedly by a person (or Claude) who decides the next
experiment from the last result. Needs the trial firmware
(tools/pid-tuning/firmware-trial), which streams
"L,<ms>,<angle>,<target>,<motor>,<rate>,<pid_on>,<imu_errors>,<cap>[,<aim>]" at
20 Hz, cuts the motor itself above +60 deg, and has x (motor cap), r (target
ramp, deg/s), b (I band, deg), c (I clamp, 0/1) and f (feedforward gain) commands.

    python3 tools/pid-tuning/pid-trial.py --kp 80 --kd 6                    # target 0, 12 s
    python3 tools/pid-tuning/pid-trial.py --kp 60 --kd 6 --ki 10 --secs 16
    python3 tools/pid-tuning/pid-trial.py --kp 60 --kd 6 --cap 4500
    python3 tools/pid-tuning/pid-trial.py --kp 60 --kd 6 --ki 10 --targets 0,30,-30,0 --secs 8
    python3 tools/pid-tuning/pid-trial.py --manual 3600 --secs 8            # open loop, no PID
    python3 tools/pid-tuning/pid-trial.py --kp 100 --kd 12 --ki 80 --ramp 40 --targets 0,30

Every run starts with the motor off and the arm hanging still, and ends with
the motor off. The script also stops the motor above --abort degrees.
Each run is appended to /tmp/pid-trials.jsonl.
"""
import argparse, glob, json, os, select, statistics, sys, termios, threading, time

ap = argparse.ArgumentParser()
ap.add_argument("--kp", type=float, default=0)
ap.add_argument("--kd", type=float, default=0)
ap.add_argument("--ki", type=float, default=0)
ap.add_argument("--targets", default="0", help="comma list, held --secs each, no stop between")
ap.add_argument("--secs", type=float, default=12)
ap.add_argument("--cap", type=int, default=6000, help="highest motor command (0-6000)")
ap.add_argument("--manual", type=int, help="open loop: set this duty instead of PID")
ap.add_argument("--sramp", type=float, default=0, help="ramp only on the fresh start, until the first target is reached (0 = off)")
ap.add_argument("--ramp", type=float, default=0, help="target slides at this many deg/s (0 = jump)")
ap.add_argument("--iband", type=float, default=0, help="only add up I within this many deg (0 = always)")
ap.add_argument("--clamp", type=int, default=0, help="1 = don't add up I while the output is at its limit")
ap.add_argument("--ff", type=float, default=0, help="feedforward gain: adds ff*cos(target)^1.8 (0 = off)")
ap.add_argument("--abort", type=float, default=50)
ap.add_argument("--stall", type=float, default=3, help="stop after this many s at full command with the arm not moving (0 = off)")
ap.add_argument("--trace", type=float, default=0.5, help="seconds between trace lines (0 = none)")
args = ap.parse_args()

ports = sorted(glob.glob("/dev/tty.usbmodem*"))
if not ports:
    sys.exit("No /dev/tty.usbmodem* port: is the Debug Probe plugged in?")
fd = os.open(ports[0], os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
a = termios.tcgetattr(fd)
a[0] = a[1] = a[3] = 0
a[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL
a[4] = a[5] = termios.B115200
termios.tcsetattr(fd, termios.TCSANOW, a)

rows = []      # (t, angle, target, motor, rate, pid_on, imu_err, cap)
lock = threading.Lock()
done = False


def reader():
    buf = ""
    while not done:
        try:
            r, _, _ = select.select([fd], [], [], 0.1)
            if not r:
                continue
            buf += os.read(fd, 4096).decode(errors="replace")
        except BlockingIOError:
            continue
        except OSError:
            return
        *lines, buf = buf.split("\n")
        for line in lines:
            f = line.strip().split(",")
            if len(f) in (9, 10) and f[0] == "L":
                try:
                    row = (time.time(), float(f[2]), float(f[3]), int(f[4]), float(f[5]),
                           int(f[6]), int(f[7]), int(f[8]))
                except ValueError:
                    continue
                with lock:
                    rows.append(row)


threading.Thread(target=reader, daemon=True).start()


def latest():
    with lock:
        return rows[-1] if rows else None


def send(cmd, value=None):
    os.write(fd, cmd.encode() + b"\r")
    time.sleep(0.25)
    if value is not None:
        os.write(fd, str(value).encode() + b"\r")
        time.sleep(0.25)


def stop():
    send("s")
    send("s")


def alive():
    s = latest()
    return s is not None and time.time() - s[0] < 1.0


def wait_hanging(timeout=25):
    t0, still = time.time(), None
    while time.time() - t0 < timeout:
        time.sleep(0.1)
        s = latest()
        if not alive():
            return "pico quiet"
        if s[5] == 0 and s[1] < -55 and abs(s[4]) < 8:
            still = still or time.time()
            if time.time() - still > 1.5:
                return ""
        else:
            still = None
    return "arm didn't settle hanging"


def metrics(seg, target):
    t = [r[0] for r in seg]
    ang = [r[1] for r in seg]
    mot = [r[3] for r in seg]
    rate = [r[4] for r in seg]
    t0 = t[0]
    tail_i = [i for i, tt in enumerate(t) if tt > t[-1] - 3.0]
    tail = [ang[i] for i in tail_i]
    tt_ = [t[i] for i in tail_i]
    final = statistics.mean(tail)
    tm = statistics.mean(tt_)
    den = sum((x - tm) ** 2 for x in tt_) or 1e-9
    slope = sum((x - tm) * (y - final) for x, y in zip(tt_, tail)) / den
    wobble = statistics.pstdev([y - (final + slope * (x - tm)) for x, y in zip(tt_, tail)])
    up = target >= ang[0]
    peak = max(ang) if up else min(ang)
    overshoot = max(0.0, (peak - target) if up else (target - peak))
    settle = 0.0
    for tt, x in zip(t, ang):
        if abs(x - final) > 3.0:
            settle = tt - t0
    rise = None
    for tt, x in zip(t, ang):
        if abs(x - final) <= 5.0:
            rise = tt - t0
            break
    # do the angle's changes agree with the gyro? (bad sensor data won't)
    d_ang = [(ang[i + 1] - ang[i]) / max(1e-3, t[i + 1] - t[i]) for i in range(len(t) - 1)]
    g = [(rate[i] + rate[i + 1]) / 2 for i in range(len(t) - 1)]
    mism = statistics.mean([abs(x - y) for x, y in zip(d_ang, g)]) if g else 0.0
    moving = statistics.mean([abs(y) for y in g]) if g else 0.0
    return dict(target=target, start=round(ang[0], 1), final=round(final, 1),
                err=round(target - final, 1), wobble=round(wobble, 2), drift=round(slope, 2),
                peak=round(peak, 1), overshoot=round(overshoot, 1),
                rise=None if rise is None else round(rise, 2), settle=round(settle, 2),
                min_angle=round(min(ang), 1), max_angle=round(max(ang), 1),
                motor_mean=int(statistics.mean(mot)), motor_tail=int(statistics.mean([mot[i] for i in tail_i])),
                at_cap=round(sum(1 for m in mot if m >= seg[0][7] - 10) / len(mot), 2),
                gyro_vs_angle_mismatch=round(mism, 1), mean_abs_rate=round(moving, 1),
                imu_errors=seg[-1][6] - seg[0][6], samples=len(seg))


result = dict(kp=args.kp, kd=args.kd, ki=args.ki, cap=args.cap, manual=args.manual,
              ramp=args.ramp, sramp=args.sramp, iband=args.iband, clamp=args.clamp, ff=args.ff,
              targets=args.targets, secs=args.secs, when=time.strftime("%H:%M:%S"))
segments, why = [], ""
try:
    time.sleep(0.8)
    if not alive():
        sys.exit("No data from the Pico: wrong firmware, or a serial terminal is open.")
    stop()
    why = wait_hanging()
    if why == "pico quiet":
        raise SystemExit("Pico went quiet.")
    result["note"] = why
    send("x", args.cap)
    send("r", args.ramp)
    if args.sramp:
        send("u", args.sramp)
    send("b", args.iband)
    send("c", args.clamp)
    send("f", args.ff)
    if args.manual is None:
        send("p", args.kp)
        send("d", args.kd)
        send("i", args.ki)
    targets = [float(x) for x in args.targets.split(",")] if args.manual is None else [None]
    last_trace = 0
    if args.trace:
        print(" time  angle  motor   rate  imu_err")
    for tg in targets:
        with lock:
            start = len(rows)
        t0 = time.time()
        if args.manual is None:
            send("a", tg)
        else:
            send("m", args.manual)
        abort = ""
        recent = []   # (time, angle, motor) for the stall check
        while time.time() - t0 < args.secs:
            time.sleep(0.05)
            if not alive():
                abort = "PICO QUIET - use the killswitch"
                break
            s = latest()
            # Stall: near full command for --stall seconds but the arm hasn't
            # moved 3 deg (loose wire, weak supply, broken MOSFET). Stop before
            # the MOSFET cooks.
            recent = [r for r in recent if s[0] - r[0] <= args.stall] + [(s[0], s[1], s[3])]
            full = 0.95 * (args.cap if args.manual is None else max(args.manual, 1))
            if (args.stall > 0 and s[0] - recent[0][0] >= args.stall - 0.1
                    and all(r[2] >= full for r in recent)
                    and max(r[1] for r in recent) - min(r[1] for r in recent) < 3.0):
                abort = f"STALL: full power {args.stall:.0f} s, arm not moving"
                break
            if args.trace and s[0] - last_trace >= args.trace:
                last_trace = s[0]
                print(f"{s[0] - t0:5.1f} {s[1]:6.1f} {s[3]:6d} {s[4]:6.1f} {s[6]:6d}", flush=True)
            if s[1] > args.abort:
                abort = f"above {args.abort:.0f} deg"
                break
            if args.manual is None and s[5] == 0 and time.time() - t0 > 1.0:
                abort = "Pico cut the motor (above 60 deg)"
                break
        with lock:
            seg = rows[start:]
        if len(seg) > 10:
            m = metrics(seg, tg if tg is not None else seg[-1][1])
            m["abort"] = abort
            segments.append(m)
        if abort:
            break
finally:
    try:
        stop()
    except OSError:
        pass
    done = True

result["segments"] = segments
print(json.dumps(result, indent=1))
with open("/tmp/pid-trials.jsonl", "a") as f:
    f.write(json.dumps(result) + "\n")
os.close(fd)
