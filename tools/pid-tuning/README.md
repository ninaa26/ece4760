# PID tuning tools (Lab 3)

Bench tools used on 23 Oct to find gains for the helicopter arm. Results and
what they showed are in `notes/lab3-status.md`.

| File | What it is |
| --- | --- |
| `firmware-trial/` | Week 2 code (group repo, `week2_IMU_Demo`) plus test-only additions: streams `L,<ms>,<angle>,<target>,<motor>,<rate>,<pid_on>,<imu_errors>,<cap>,<aim>` at 20 Hz, counts failed IMU reads (and keeps the last good values), cuts the motor above +60 deg. Extra commands: `x` motor cap, `r` target ramp (deg/s), `b` I band (deg), `c` I clamp (0/1), `f` feedforward gain (adds f·cos(aim)^1.8; I may then go below 0), `u` startup ramp (deg/s, only from a fresh start until the first target is reached; `--sramp`). All off by default |
| `trial.sh` | Runs `pid-trial.py` and prints just the trace and one summary line per target |
| `pid-trial.py` | Runs **one** experiment (gains, cap, target or target sequence, or open-loop duty) from a hanging start, prints a trace and the metrics, appends to `/tmp/pid-trials.jsonl`. For trying things one at a time |
| `firmware-sweep/` | Earlier version: 7-field stream, no error counter or cap |
| `pid-sweep.py` | Automatic search (grid, refine, add I, range check) for `firmware-sweep` |

Build and flash a firmware folder like any project:

    ./build.sh tools/pid-tuning/firmware-trial
    # BOOTSEL, then copy build/firmware-trial-pico2/MPU6050_IMU.uf2 to /Volumes/RP2350

Talk to it through the Debug Probe's UART (GP0/GP1). Close every serial
terminal first: two programs on the port split the data between them.

    python3 tools/pid-tuning/pid-trial.py --kp 100 --kd 12 --ki 80 --cap 4500
    python3 tools/pid-tuning/pid-trial.py --kp 100 --kd 12 --ki 80 --cap 4500 --targets 0,30,-30,0 --secs 8
    python3 tools/pid-tuning/pid-trial.py --manual 3000 --secs 8 --abort 40

Keep a hand on the killswitch. Every run starts and ends with the motor off.

Building on this Mac: the host compiler can't link (Command Line Tools SDK 27),
so the SDK can't build pioasm/picotool itself. These folders' `CMakeLists.txt`
include the Pico VS Code extension block, which points at the installed tools in
`~/.pico-sdk`; build from VS Code or with the extension's cmake/ninja.
