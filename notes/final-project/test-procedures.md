# Test procedures

Step-by-step instructions for every test in the catalogue: what it proves, how to set it up, what each Pico does, what gets measured, and how it passes. Limits marked \_\_\_ are set after our first runs.

## How every test runs

Every test is started from the ground station menu and follows the same four steps: setup, stimulus, measure, evaluate. The ground station never trusts the satellite's own opinion of how it did: it compares the satellite's telemetry against the test stand's encoder and timestamps.

| Role | Pico | During a test it… |
| --- | --- | --- |
| Test runner | 3, ground station | Sends commands, collects data, compares against limits, shows PASS/FAIL |
| Instrument | 2, test stand | Reports the true angle every 5 ms over CAN, switches the lamp, stamps the time of each event |
| System under test | 1, satellite | Flies normally, obeys test commands, sends telemetry once per second (faster during a test) |

**Before any test (the bench checklist).**

1. Room lights in the same state as our calibration runs.
2. Lamp at its marked spot on the bench, 30 cm from the turntable (adjust once we measure).
3. Encoder zeroed: turn the satellite to face the lamp by hand, press "zero" on the ground station.
4. Satellite battery charged; T01 link check passes.

**What every result records:** test ID, date and run number, measured value(s), limit, units, PASS/FAIL, run time, and any notes the test adds (for example the worst sample). The report page shows the latest run of each test; we photograph the screen or copy the numbers into our lab notebook after every run.

**Commands the tests are built from** (defined once in the shared header):

| To the satellite (WiFi) | To the test stand (CAN) |
| --- | --- |
| `PING`, `GET_STATUS`, `SET_MODE(mode)`, `POINT_TO(angle)`, `IV_SWEEP(panel)`, `MPPT(on/off)`, `INJECT_FAULT(type)`, `TELEM_RATE(Hz)` | `PING`, `ZERO`, `GET_ANGLE`, `STREAM_ANGLE(on/off)`, `LAMP(on/off)` |

Stretch tests add `SET_BATTERY(%)` and `RESTART_MISSION`, and the satellite sends a `BOOT` packet every time it starts up. Modes used below: IDLE (wheel off), POINT, ACQUIRE, SUN\_HOLD, ECLIPSE, SAFE.

## Core tests: links and pointing

### T01 Link check

**Proves:** all three boards can talk, and how long a message takes. **Needs:** WiFi and CAN working, nothing else.

1. Ground station sends `PING` to the satellite over WiFi 20 times, one every 100 ms, noting the time each one leaves (`time_us_64()`).
2. The satellite answers each `PING` straight away with the same sequence number.
3. Ground station repeats this with the test stand over CAN.
4. For each reply it computes round-trip time = time back − time sent.

**Measured:** replies received out of 20, average and worst round-trip time for each link. **Pass if:** 20/20 on both links, worst round trip < \_\_\_ ms.

**Why it matters later:** the WiFi round-trip time tells us how late telemetry can arrive, which sets how tight the timing limits in other tests can be.

### T02 Encoder vs. gyro

**Proves:** the satellite's own idea of its angle (from the gyro) matches the true angle (from the encoder), and how fast it drifts. **Needs:** IMU, encoder, links.

1. Ground station sets the satellite to IDLE (wheel off) and zeroes the encoder.
2. Satellite holds still for 2 s and averages the gyro to find its bias (the small reading it gives when not moving), then subtracts that from every later reading.
3. Test stand streams the encoder angle; satellite streams its gyro-integrated angle at 20 Hz.
4. One of us turns the platform by hand, back and forth about ±90°, for 30 s.
5. Leave it untouched for 60 s.
6. Ground station pairs up samples by time and computes the difference.

**Measured:** worst difference during the hand-turning phase; drift rate (difference at 60 s ÷ 1 min) during the still phase. **Pass if:** worst difference < \_\_\_°, drift < \_\_\_°/min.

**Plain words:** the gyro is like counting your steps with your eyes closed. You end up close, but small mistakes add up. The encoder is someone watching with their eyes open.

### T03 Point to angle

**Proves:** the reaction wheel and PID loop can turn the satellite to any angle we ask for. **Needs:** wheel, H-bridge, PID, encoder.

1. Satellite starts at 0° (encoder zeroed), in POINT mode, holding.
2. Ground station sends `POINT_TO(+90)`, and the test stand streams the encoder at 200 Hz.
3. Wait 15 s, then send `POINT_TO(0)`, then `POINT_TO(+45)`: three steps per run.
4. For each step the ground station finds, from the encoder: overshoot (how far past the target it swung), settling time (when it entered ±2° of the target and stayed), and steady-state error (average error over the last 5 s).
5. It also logs wheel speed, to check the wheel never hits its speed limit.

**Measured:** overshoot, settling time and steady-state error for each step. **Pass if:** all three steps settle within ±\_\_\_° in < \_\_\_ s, with overshoot < \_\_\_ %.

**For the report:** plot target vs. encoder angle over time for one run. This is the classic step-response plot, and it shows our PID tuning.

## Core tests: solar power and the sun

### T04 I-V sweep

**Proves:** we can map each solar panel's full behaviour and find its true maximum power point. **Needs:** INA219s, DAC, MOSFET loads.

1. Satellite holds facing the lamp (encoder at 0°), with MPPT off.
2. Ground station sends `IV_SWEEP(A)`.
3. The satellite steps the DAC for panel A from 0 (load off) to full in 64 steps. At each step it waits 20 ms for things to settle, then reads the panel's voltage and current from the INA219.
4. It sends the 64 (voltage, current) pairs to the ground station, which plots the I-V curve and the power curve (P = V × I) on screen.
5. Repeat for panel B.

**Measured:** open-circuit voltage (load off), short-circuit current (load fully on), and the peak power with the voltage it happens at, for each panel. **Pass if:** both curves have the expected shape (current falls as voltage rises), a clear peak is found, and panels A and B peak within \_\_\_ % of each other when facing the lamp equally.

**Plain words:** it's like testing a water pump by slowly closing a valve and writing down the pressure and flow at every setting. The best setting is where pressure × flow is biggest.

### T05 MPPT accuracy

**Proves:** our MPPT loop finds the peak by itself and stays there. **Needs:** T04 working (it is the reference).

1. Run T04 first, so we know each panel's true peak power under the same light.
2. Set both DACs to 0, then send `MPPT(on)`.
3. Each 100 ms the satellite nudges the DAC one step, checks whether power went up or down, and keeps going or turns around (perturb and observe). It reports power for both panels.
4. Record for 20 s.

**Measured:** time to reach within 5 % of the T04 peak; tracking efficiency = average power over the last 10 s ÷ T04 peak power × 100 %. **Pass if:** efficiency ≥ \_\_\_ % on both panels and settling time < \_\_\_ s.

**For the report:** the power-vs-time plot will show a small wobble around the peak. That's normal for perturb and observe, and we can measure how the step size changes it.

### T06 Sun acquisition

**Proves:** starting from any direction, the satellite finds the lamp and locks on. **Needs:** pointing (T03), both panels, MPPT.

1. Encoder zeroed while facing the lamp, so 0° means "facing the sun".
2. Ground station sends `POINT_TO(180)`, so the satellite faces directly away. This makes every run start the same way.
3. Ground station sends `SET_MODE(ACQUIRE)` and starts a timer.
4. The satellite turns slowly until the total panel power rises above a threshold, then switches to SUN\_HOLD and centres using the panel difference.
5. The test stand streams the encoder angle the whole time.
6. Repeat from 5 start angles: 180°, 90°, −90°, 45°, −135°.

**Measured:** for each start: time until the encoder is within ±5° of 0° and stays there for 3 s, plus the final error. **Pass if:** all 5 starts acquire in < \_\_\_ s with final error < \_\_\_°.

### T07 Sun hold

**Proves:** once locked on, the satellite stays on the sun, recovers when pushed, and keeps the power high. **Needs:** T06 working.

1. Start in SUN\_HOLD, locked on the lamp.
2. Run for 3 minutes, with the encoder streaming at 50 Hz and the satellite sending panel power at 10 Hz.
3. At 30 s, 75 s and 120 s the ground station shows PUSH NOW, and one of us nudges the platform about 30° with a finger.
4. The ground station splits the run into quiet periods and recovery periods.

**Measured:** RMS pointing error during quiet periods; worst error; recovery time after each push (back within ±3°); average total panel power ÷ the best total from T04. **Pass if:** RMS error < \_\_\_°, every recovery < \_\_\_ s, power ≥ \_\_\_ % of best.

**Bonus, calibrating the sun sensor:** during the quiet periods we know the true angle from the encoder and the satellite's estimate k · (P\_A − P\_B) / (P\_A + P\_B). Plotting one against the other gives the best value of k, which then goes back into the code.

## Core tests: faults in the light

### T08 Eclipse

**Proves:** when the sun disappears, the satellite notices, holds its heading on the gyro alone, and finds the sun again when it comes back. **Needs:** sun hold (T07), lamp switch.

1. Before the run, measure the background: panel power with the lamp off. The eclipse threshold must sit clearly above it, or room light will fool the satellite.
2. Start in SUN\_HOLD, locked on.
3. At 10 s the ground station tells the test stand `LAMP(off)`. The test stand switches the lamp off and records the exact time.
4. The satellite sees total panel power below the threshold for 3 samples in a row (0.3 s), switches to ECLIPSE, and holds its last heading using the gyro. It reports the mode change, including how long it took from the first dark sample to deciding.
5. Leave the lamp off for 60 s while the encoder records how far the satellite drifts.
6. Ground station sends `LAMP(on)`. The satellite sees power return, goes back to SUN\_HOLD and re-centres.

**Measured:** detection delay (ECLIPSE reported − lamp off, minus the WiFi delay from T01); drift during the 60 s eclipse (encoder); time to re-centre after the lamp comes on. **Pass if:** detection < \_\_\_ ms, drift < \_\_\_°, re-centred in < \_\_\_ s.

**Tie-in:** the eclipse drift should match the gyro drift rate measured in T02. If it doesn't, something else is pushing the platform.

### T09 Shaded panel

**Proves:** the satellite can tell "one panel is blocked" apart from "the sun moved", and doesn't turn away from the real sun. **Needs:** sun hold (T07).

1. Start in SUN\_HOLD, locked on.
2. The ground station shows COVER PANEL A. One of us holds a piece of cardboard just in front of panel A for 20 s, without touching the platform.
3. Without fault detection, the satellite would think the sun moved toward panel B and turn the wrong way. Our rule: if one panel's power drops by more than \_\_\_ % within 0.5 s while the gyro says the satellite isn't turning, the drop can't come from pointing. So the satellite flags PANEL A FAULT and holds its heading on the gyro.
4. Remove the cardboard. Once panel A's power returns, the satellite clears the flag and goes back to normal sun hold.
5. Repeat with panel B.

**Measured:** time from covering to the fault flag; worst encoder angle while covered; time to clear the flag after uncovering. **Pass if:** flag within \_\_\_ s, worst angle < \_\_\_°, back to normal within \_\_\_ s, for both panels.

**Plain words:** if your left cheek suddenly goes cold but you didn't turn your head, a cloud or a hand blocked the sun. The sun didn't move.

## Stretch tests: software and radio faults

### T10 Watchdog

**Proves:** if the flight code freezes, the chip resets itself and the satellite comes back on its own. **Needs:** links; the satellite's hardware watchdog enabled.

1. In the satellite code, `watchdog_enable(500, true)` at start-up, and the control loop calls `watchdog_update()` every 10 ms. If 500 ms pass without an update, the chip resets.
2. At boot, `watchdog_caused_reboot()` tells the code whether the watchdog caused the reset. If so, it adds 1 to a reboot counter kept in a watchdog scratch register (these survive a reset).
3. For safety, start with the wheel stopped (IDLE).
4. Ground station sends `INJECT_FAULT(HANG)`. The satellite deliberately enters an endless loop.
5. The ground station waits for the next beacon and reads the reboot counter in it.

**Measured:** time from the HANG command to the first beacon after the reset; reboot counter before and after. **Pass if:** the counter goes up by exactly 1 and the beacon returns within \_\_\_ s.

**Something to watch for:** while the code is frozen, the PWM hardware keeps driving the wheel at its last setting. The reset stops it, which is why the 500 ms timeout matters. Write this up as a real finding.

### T11 Command loss

**Proves:** if the satellite stops hearing the ground, it recovers by itself instead of staying lost. **Needs:** links.

1. The satellite keeps a "no contact" timer that every valid ground packet resets to zero.
2. Ground station sends `INJECT_FAULT(BAD_RADIO)`. The satellite switches to a wrong WiFi network name and can no longer connect.
3. The ground station stops hearing beacons and starts timing the silence.
4. After \_\_\_ s with no contact, the satellite falls back to the default network name stored in its code and reconnects.
5. Second version: switch the ground station's WiFi off for 40 s. The satellite must keep flying (sun hold continues) and reconnect when it comes back.

**Measured:** length of the silence; whether pointing stayed good during it (encoder). **Pass if:** silence = timeout ± \_\_\_ s, the satellite is heard again, and pointing never stopped.

### T12 Packet compatibility

**Proves:** the ground station rejects bad data instead of showing garbage. **Needs:** the shared packet header with version, length and a CRC-16 checksum.

1. The ground station keeps counters: good, bad CRC, bad version, out of range.
2. Ground station sends `INJECT_FAULT(BAD_PACKETS)`. The satellite sends 10 normal packets, then 10 of each bad kind, then 10 normal:
   1. One flipped bit, so the CRC check fails.
   2. Version number + 1.
   3. A value with its bytes in the wrong order but a correct CRC. The CRC can't catch this, so only a range check (for example, panel voltage must be 0–7 V) does.
3. The ground station checks every packet before using it.

**Measured:** each counter after the run. **Pass if:** exactly 20 good and 10 in each bad category, and nothing bad ever reaches the live screen.

**Lesson for the report:** a checksum proves the packet arrived unchanged, not that both sides agree on what it means. That's why real missions test flight software against ground software ("test like you fly").

### T13 Link margin

**Proves:** how much weaker the radio signal can get before the link breaks. **Needs:** links; the satellite reports its WiFi signal strength (RSSI) in every packet.

1. Take the satellite off the turntable (on its battery). The ground station stays put.
2. The satellite sends telemetry at 10 Hz with sequence numbers.
3. Hold it at 1, 2, 5, 10 and 20 m, then inside a metal tin, for 30 s each.
4. The ground station computes packet loss for each spot from gaps in the sequence numbers, and logs the average RSSI.

**Measured:** packet loss vs. RSSI for every spot; the RSSI where loss passes 10 % (the breaking point); margin = RSSI at our normal bench distance − breaking point, in dB. **Pass if:** margin ≥ \_\_\_ dB.

**Be clear in the report:** WiFi stands in for a real spacecraft radio; the method is the same.

## Stretch tests: whole-mission and power

### T14 Lost-in-space recovery

**Proves:** from the worst possible start, the satellite saves itself with no help: stops spinning, finds the sun, gets enough power, and calls home. **Needs:** T03, T06, T10, plus the virtual battery and the supply INA219.

1. The ground station sets the virtual battery to low (\_\_\_ %) and tells the satellite to restart into its start-of-mission sequence. After that, the ground station only listens and sends nothing.
2. In the start-of-mission sequence the radio stays off until the satellite is power-positive (measured panel power > measured power used) and the virtual battery is above \_\_\_ %.
3. One of us spins the platform by hand, about one turn per second, from a random starting angle, and lets go. The encoder shows the exact moment of release (the spin rate stops rising).
4. The satellite runs by itself: detumble, then sun acquisition, then sun hold, then it waits for the battery to charge and starts sending a beacon (a short "I'm alive" packet) every 2 s.
5. Repeat 5 times from different starting angles and spin directions.

**Measured:** for each run, the times from release to: stopped spinning, facing the lamp, power-positive, first beacon heard. **Pass if:** the first beacon arrives within \_\_\_ s on every run.

**For the demo:** this is the headline test. Hunter spins it, and we watch the phases appear on screen one by one.

### T15 Brownout sweep

**Proves:** with a slowly dying power supply, the satellite doesn't get stuck restarting over and over, and only turns the radio on when there's enough power. **Needs:** bench power supply, oscilloscope. The satellite is taken off the platform, with the wheel disabled.

1. Power the satellite from the bench supply through the supply INA219, with the current limit set.
2. The satellite code only turns the radio on when the supply has stayed above \_\_\_ V for 2 s, and turns it off below a lower voltage. The gap between the two (hysteresis) stops it flickering on and off.
3. Every time the satellite boots, it sends a BOOT packet, which the ground station counts.
4. Sweep the supply down from 5.0 V in 0.1 V steps every 2 s until the Pico stops, then back up the same way.
5. Scope on the supply line, triggered on a falling edge, to capture the dip when the radio switches on.

**Measured:** number of boots during the sweep; voltage where the radio turned on and off; depth of the dip on the scope. **Pass if:** no repeated boots at any steady voltage, radio on only above \_\_\_ V, beacons resume on the way back up.

**For the report:** the scope trace of the dip goes straight into the Results section.

### T16 Day-in-the-life soak

**Proves:** nothing goes wrong over a long run that short tests can't catch: no surprise resets, no slow drift, no missed eclipses. **Needs:** T08 working.

1. The ground station runs "orbits": lamp on for \_\_\_ min (day), off for \_\_\_ min (eclipse), repeated for 30 min to 2 hours.
2. For runs longer than the battery lasts, power the satellite through a USB cable with plenty of slack. It only moves a few degrees, so the cable won't wind up.
3. The ground station keeps counters: orbits completed, eclipses detected vs. commanded, unplanned resets, missed beacons (gaps in sequence numbers), worst pointing error per orbit, lowest virtual battery.
4. Someone stays in the room the whole time: the lamp gets hot.
5. At the end, the ground station shows a summary page.

**Measured:** every counter above. **Pass if:** eclipses detected = eclipses commanded, 0 unplanned resets, missed beacons < \_\_\_ %.

**For the report:** a long run with zero problems is a strong result, and any problem it does find is an even better story.
