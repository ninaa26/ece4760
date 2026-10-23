#!/bin/zsh
# Run one pid-trial.py experiment and print only the trace and a one-line
# summary per target. Arguments go straight to pid-trial.py.
#   tools/pid-tuning/trial.sh --kp 100 --kd 12 --ki 80 --cap 4500 --targets=0,30,40 --secs 6
# Use --targets=... (with =) when the list starts with a minus sign.
# Don't pipe this into `head`: closing the pipe early kills the run.
cd "${0:A:h}/../.."
python3 tools/pid-tuning/pid-trial.py "$@" > /tmp/trial-out.txt 2>&1
grep -E '^ *[0-9]+\.[0-9] ' /tmp/trial-out.txt
grep -E '^(No |Pico )' /tmp/trial-out.txt
tail -1 /tmp/pid-trials.jsonl | python3 -c "
import json,sys;d=json.loads(sys.stdin.read())
for s in d['segments']:
    print('Kp',d['kp'],'Kd',d['kd'],'Ki',d['ki'],'cap',d['cap'],'ramp',d.get('ramp'),'sramp',d.get('sramp'),'band',d.get('iband'),
          'clamp',d.get('clamp'),'ff',d.get('ff'),'->',s['target'],
          {k:s[k] for k in ('final','wobble','drift','overshoot','rise','settle','min_angle','max_angle','motor_tail','at_cap','imu_errors','abort')})"
