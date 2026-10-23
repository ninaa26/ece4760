#!/usr/bin/env python3
"""Apply the edits in edits.py to the course demos and (with --build) compile every step.

    python3 apply.py            # writes out/stages/w<week>_step<n>.c
    python3 apply.py --build    # ...and builds each one for the Pico 2

DEMO= points at the course demo repo; by default it is Hunter-Adams-RP2040-Demos
in the main checkout.
"""
import os, shutil, subprocess, sys
from pathlib import Path
from edits import WEEKS, STEPS

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def demo_root():
    if os.environ.get("DEMO"):
        return Path(os.environ["DEMO"])
    common = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=HERE,
                            capture_output=True, text=True).stdout.strip()
    main_root = (HERE / common).resolve().parent
    return main_root / "Hunter-Adams-RP2040-Demos"


def apply_edit(src, e):
    n = src.count(e["anchor"])
    if n != 1:
        sys.exit(f"edit {e['id']}: anchor found {n} times, expected once:\n{e['anchor']}")
    if e["op"] == "after":
        return src.replace(e["anchor"], e["anchor"] + e["new"])
    if e["op"] == "before":
        return src.replace(e["anchor"], e["new"] + e["anchor"])
    if e["op"] == "change":
        return src.replace(e["anchor"], e["new"])
    sys.exit(f"edit {e['id']}: unknown op {e['op']}")


def stages():
    """Yield (week, step, source before, source after) for every step with edits."""
    root = demo_root()
    for week, info in WEEKS.items():
        src = (root / info["demo"] / info["file"]).read_text()
        yield week, 1, src, src
        for (w, step) in sorted(k for k in STEPS if k[0] == week):
            before = src
            for e in STEPS[(w, step)]:
                src = apply_edit(src, e)
            yield week, step, before, src


def pioasm_shim():
    """The VGA library needs pioasm. This Mac can't build host tools, and the
    installed pioasm (2.3.1) is one patch newer than the SDK (2.3.0) accepts,
    so give cmake a copy that reports the SDK's version."""
    shim = OUT / "pioasm-shim" / "pioasm"
    if not shim.exists():
        shutil.copytree(Path.home() / ".pico-sdk/tools/2.3.1/pioasm", shim)
        v = shim / "pioasmConfigVersion.cmake"
        v.write_text(v.read_text().replace("2.3.1", "2.3.0"))
    return shim


def build(week, step, src):
    root = demo_root()
    info = WEEKS[week]
    proj = OUT / "src" / f"w{week}_step{step}"
    if proj.exists():
        shutil.rmtree(proj)
    shutil.copytree(root / info["demo"], proj)
    (proj / info["file"]).write_text(src)
    env = dict(os.environ)
    env.setdefault("PICO_SDK_PATH", str(Path.home() / "Developer/pico-sdk"))
    tc = Path(env.get("PICO_TOOLCHAIN_PATH", Path.home() / ".pico-sdk/toolchain/14_2_Rel1"))
    env["PATH"] = f"{tc}/bin:/opt/homebrew/bin:" + env["PATH"]
    bdir = OUT / "build" / f"w{week}_step{step}"
    subprocess.run(["cmake", "-S", proj, "-B", bdir, "-G", "Ninja", "-DPICO_BOARD=pico2",
                    f"-Dpicotool_DIR={Path.home()}/.pico-sdk/picotool/2.3.1/picotool",
                    f"-Dpioasm_DIR={pioasm_shim()}"],
                   env=env, check=True, capture_output=True)
    r = subprocess.run(["cmake", "--build", bdir], env=env, capture_output=True, text=True)
    log = r.stdout + r.stderr
    mine = [l for l in log.splitlines() if info["file"] in l and ("warning:" in l or "error:" in l)]
    print(f"week {week} step {step}: exit {r.returncode}, {len(mine)} warnings/errors in {info['file']}")
    for l in mine:
        print("   ", l)
    return r.returncode == 0 and not mine


if __name__ == "__main__":
    (OUT / "stages").mkdir(parents=True, exist_ok=True)
    ok = True
    for week, step, _, src in stages():
        (OUT / "stages" / f"w{week}_step{step}.c").write_text(src)
        if "--build" in sys.argv:
            ok = build(week, step, src) and ok
    sys.exit(0 if ok else 1)
