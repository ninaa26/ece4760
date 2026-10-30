# Final project: Mini-Sat (start here)

Status on 29 Oct 2026: idea chosen by the student, proposal drafted, not yet
agreed with the group or submitted. Nothing has been built or measured.

**Mini-Sat** is a reaction-wheel satellite on a turntable that turns two solar
panels toward a lamp "sun" and keeps them at maximum power, plus a Pico-based
automated test stand that grades it test by test. Three Pico 2 boards, no
laptop.

## Live docs (claude.ai, edited by the group)

| Doc | Link | Copy in this folder |
| --- | --- | --- |
| Final project proposal (main tab + "Test procedures" tab) | https://claude.ai/artifact/W9TnAD1FCV8HWrH9HiFUyB | `proposal.md`, `test-procedures.md` |
| Team pitch (for the group meeting) | https://claude.ai/artifact/1xSSAcWzxP5pNcSSc5nWW4 | `team-pitch.md` |
| Pet spec (desk-pet personality on top of Mini-Sat) | https://claude.ai/artifact/5YcCHzAxkoehVV6yxvTqoj | `pet-spec.md` |

The live docs are the source of truth; the copies here are snapshots from
29 Oct 2026 without the diagrams. Read the live doc before editing, and
re-export after big changes.

Handout: https://vanhunteradams.com/Pico/CourseMaterials/Final_Project.html
(4–5 weeks, proposal 2–5 pages, report 40 %, demo 30 %, weekly progress 20 %).

## Design in one table

| Pico | Role | Hardware |
| --- | --- | --- |
| 1, Pico 2 W | Satellite (system under test), on the turntable | MPU6050, 2 solar panels in a V, 3× INA219, MCP4822 + 2 MOSFET loads, TB6612FNG + DC motor + flywheel, USB battery pack |
| 2, Pico 2 | Test stand (instrument), fixed base | AS5600 magnetic encoder under the shaft, MOSFET lamp switch (12 V) |
| 3, Pico 2 W | Ground station (test runner) | VGA (Lab 2 adapter), PEC11 knob + button |

Links: WiFi UDP satellite ↔ ground (ground is the access point), CAN test
stand ↔ ground (course PIO demo, UART fallback), I2C sensors, SPI DAC.

Key decisions and why:

- **No custom PCB** (may not be able to order): breadboard, then soldered protoboard.
- **No laptop**: the ground station Pico runs the tests and shows PASS/FAIL on VGA.
- **Two panels angled in a V are the sun sensor**: angle ≈ k·(P_A − P_B)/(P_A + P_B).
- **MPPT on a dummy load** (DAC → MOSFET gate), no buck converter. Energy becomes
  heat, so a software "virtual battery" uses measured panel power and measured
  consumption (third INA219).
- **AS5600 instead of the PEC11 encoder** for true angle: the PEC11 has 24
  detents and friction; the AS5600 is contactless (magnet on the shaft).
- **H-bridge, not one MOSFET**: the wheel must spin both ways (and Lab 3's
  IRF520 faded).
- **Test catalogue**: every test is separate and selectable from the menu, so
  tests are built one at a time. Core T01–T09, stretch T10–T16. Limits are `___`
  until measured.

## Desk-pet direction (30 Oct 2026)

The teammates like a cute desk-pet idea, so `pet-spec.md` adds personality
without dropping the test-engineering core: an SSD1306 OLED face on the
satellite (on I2C1, GP14/GP15, redrawn on core 1) whose 12 moods are set only
by measured states, each checked by a test (T17 mood mapping, T18 no false
happiness, T19 health certificate). The student picked the **wake-up
self-test** (power-on built-in test: eyes open = IMU OK, wiggle = wheel OK and
turning the right way, squint = panels OK, then hello) with T20 to prove it
catches planted faults. T17–T20 are not yet in the proposal's catalogue.

## Ideas from the planning chat not yet in the docs

- **Depth upgrades** to stand out (add after the core tests pass):
  1. Complementary, then Kalman, filter fusing gyro + panel sun sensor,
     with its error measured against the encoder.
  2. Hall sensor on the flywheel read by our own PIO program → cascaded control
     (wheel speed inner loop, pointing outer loop) and a measured inertia ratio
     I_body / I_wheel = −Δω_wheel / Δω_body.
  3. Control loop on core 0 from a timer interrupt, radio on core 1; GPIO toggle
     on the scope to measure loop time and jitter.
  4. Live scrolling plots on the VGA ground station.
- **Satellite with a face**: now worked out in `pet-spec.md` (above).

## Week-1 checks before committing

- Logic-level MOSFET fully on with ≤ 3.3 V from the MCP4822.
- Hunter's `Networking/CAN` demo (written for RP2040) runs on the RP2350.
- Pico-to-Pico WiFi with one board as access point.
- Panel current under the lamp at ~30 cm is big enough to measure.

## AI use

The proposal, team pitch and test procedures were drafted with Claude in a
planning chat on 29 Oct 2026 from the student's requirements. No code has been
written yet. Record AI-generated code in the project notebook when there is any.
