# Every code change in the Lab 3 field guide, in order.
#
# Each edit attaches to an anchor: text that must appear exactly once in the
# file at that point. op is "after" (insert new below the anchor), "before"
# (insert new above it) or "change" (replace the anchor with new).
#
# Week 1 starts from PWM/PWM_Demo/pwm-demo.c, week 2 from
# Sensors/MPU6050_IMU_Demo/imu_demo.c (course demo repo, 21 Sep 2026).

WEEKS = {
  1: {"demo": "PWM/PWM_Demo", "file": "pwm-demo.c", "folder": "Lab3_Motor"},
  2: {"demo": "Sensors/MPU6050_IMU_Demo", "file": "imu_demo.c", "folder": "Lab3_Helicopter"},
}

# STEPS[(week, step)] = list of edits
STEPS = {}

# ---------------------------------------------------------------- week 1
STEPS[(1, 2)] = [
  {"id": "2.1", "op": "change",
   "title": "Start with the motor off",
   "where": "In <code>main()</code>, the line under <code>// This sets duty cycle</code>.",
   "simple": "The demo switches the output on at half power the moment the Pico starts. With a motor attached, that means the arm jumps up before you've typed anything. We make it start at zero.",
   "anchor": "    pwm_set_chan_level(slice_num, PWM_CHAN_A, 3000);\n",
   "new": "    // Start with the motor OFF. The demo started at 3000 (half power),\n"
          "    // which would spin the motor as soon as the Pico powers up.\n"
          "    pwm_set_chan_level(slice_num, PWM_CHAN_A, 0);\n",
   "why": "<ul>\n"
          "<li><code>pwm_set_chan_level(slice, channel, level)</code> sets how long the pin stays high in each PWM period. The period is 6000 counts (<code>WRAPVAL</code>), so 0 is always off, 3000 is half the time, 6000 is always on.</li>\n"
          "<li>Nothing else changes: the interrupt only writes a new level after you type one (<code>control != old_control</code>), so until then the motor stays off.</li>\n"
          "</ul>"},
  {"id": "2.2", "op": "change",
   "title": "Say back what was set",
   "where": "In <code>protothread_serial</code>, the last line inside <code>while(1)</code>.",
   "simple": "When you type a number, the Pico now answers with what it set, as counts and as a percentage. That way you know it heard you, and you can read the number off the screen into your notebook.",
   "anchor": "        else control = test_in ;\n",
   "new": "        else {\n"
          "            control = test_in ;\n"
          "            // Say what was set, so you know the Pico heard you\n"
          "            sprintf(pt_serial_out_buffer, \"duty %d of 6000 = %d%%\\r\\n\", control, control / 60) ;\n"
          "            serial_write ;\n"
          "        }\n",
   "why": "<ul>\n"
          "<li><code>sprintf</code> writes text into a buffer instead of printing it. <code>%d</code> is replaced by a whole number; <code>%%</code> prints a single <code>%</code> sign.</li>\n"
          "<li><code>control / 60</code> is the percentage: 6000 counts is 100 %, so 60 counts is 1 %.</li>\n"
          "<li><code>serial_write</code> is the course library's way of sending that buffer out of the UART without stopping the rest of the program.</li>\n"
          "<li><code>\\r\\n</code> moves the terminal's cursor to the start of the next line.</li>\n"
          "</ul>"},
]

# ---------------------------------------------------------------- week 2
STEPS[(2, 2)] = [
  {"id": "2.1", "op": "after",
   "title": "Add the angle settings and variables",
   "where": "Near the top, right after <code>#define ACCEL_SCALE 120.0</code>.",
   "simple": "We write down which of the sensor's three directions points along the arm, which points up, and which one the arm turns around. You found these in step 1. We also make a box to keep the arm's angle in.",
   "anchor": "#define ACCEL_SCALE 120.0\n",
   "new": "\n"
          "// === arm angle (complementary filter) ===\n"
          "// Which IMU axis is which depends on how the IMU sits on YOUR arm.\n"
          "// Week 2, step 1 shows how to find them. 0 = x, 1 = y, 2 = z.\n"
          "#define ARM_AXIS   0      // accelerometer axis pointing along the arm\n"
          "#define UP_AXIS    1      // accelerometer axis pointing up when the arm is level\n"
          "#define GYRO_AXIS  2      // gyro axis pointing along the hinge\n"
          "// +1.0f or -1.0f, chosen so that each reading goes UP as you lift the arm\n"
          "#define ARM_SIGN   1.0f\n"
          "#define UP_SIGN    1.0f\n"
          "#define GYRO_SIGN  1.0f\n"
          "\n"
          "#define DT           0.001f    // seconds between samples (the interrupt runs at 1 kHz)\n"
          "#define ACCEL_SMOOTH 0.05f     // low-pass on the accelerometer: smaller = smoother, slower\n"
          "#define ACCEL_WEIGHT 0.01f     // how much to trust the accelerometer each sample\n"
          "#define RAD_TO_DEG   57.29578f // 180 / pi\n"
          "\n"
          "// Smoothed accelerometer readings, in g\n"
          "float arm_g = 0.0f ;\n"
          "float up_g = 0.0f ;\n"
          "// Best guess of the arm angle, degrees. 0 = level, -90 = hanging straight down\n"
          "volatile float angle = 0.0f ;\n"
          "// How fast the arm is turning, degrees per second (straight from the gyro)\n"
          "volatile float angle_rate = 0.0f ;\n"
          "// 0 until the first sample has set the starting angle\n"
          "int angle_started = 0 ;\n",
   "why": "<ul>\n"
          "<li>The IMU measures along its own x, y and z, which depend on how it is screwed to the arm. The six <code>#define</code>s say which axis is which, and which way round. Change them here, not in the maths below.</li>\n"
          "<li><code>DT</code> is the time between samples: the PWM interrupt runs 1000 times a second, so 0.001 s.</li>\n"
          "<li><code>float</code> is a number with a decimal point. The RP2350 has a <b>floating-point unit</b> (hardware for decimal maths), so floats are fast enough here. Lab 2 needed fixed point; at 1000 samples a second this doesn't.</li>\n"
          "<li><code>volatile</code>: the interrupt changes <code>angle</code> while the drawing code reads it, so the compiler must re-read it every time.</li>\n"
          "</ul>"},
  {"id": "2.2", "op": "after",
   "title": "Work out the angle in the interrupt",
   "where": "In <code>on_pwm_wrap()</code>, right after the line that reads the IMU, <code>mpu6050_read_raw(acceleration, gyro);</code>.",
   "simple": "Every millisecond: take the sensor's reading of gravity and smooth it, turn it into an angle, then blend it with the gyro. The gyro says how much the arm turned since last time. The blend is mostly gyro (smooth) with a pinch of gravity (so it never drifts).",
   "anchor": "    // the raw measurements.\n    mpu6050_read_raw(acceleration, gyro);\n",
   "new": "\n"
          "    // --- Estimate the arm angle ---\n"
          "    // 1. This sample's accelerometer readings along the arm and \"up\", in g\n"
          "    float arm_now = ARM_SIGN * fix2float15(acceleration[ARM_AXIS]) ;\n"
          "    float up_now  = UP_SIGN  * fix2float15(acceleration[UP_AXIS]) ;\n"
          "    if (!angle_started) {\n"
          "        arm_g = arm_now ;\n"
          "        up_g  = up_now ;\n"
          "    }\n"
          "    // 2. Smooth them: the motor shakes the accelerometer\n"
          "    arm_g += ACCEL_SMOOTH * (arm_now - arm_g) ;\n"
          "    up_g  += ACCEL_SMOOTH * (up_now  - up_g) ;\n"
          "    // 3. Angle from gravity alone: noisy, but it never drifts\n"
          "    float accel_angle = atan2f(arm_g, up_g) * RAD_TO_DEG ;\n"
          "    // 4. Turn rate from the gyro, degrees per second: smooth, but it drifts\n"
          "    angle_rate = GYRO_SIGN * fix2float15(gyro[GYRO_AXIS]) ;\n"
          "    // 5. Blend: last angle + what the gyro says we turned, nudged toward gravity\n"
          "    if (!angle_started) {\n"
          "        angle = accel_angle ;\n"
          "        angle_started = 1 ;\n"
          "    }\n"
          "    angle = (1.0f - ACCEL_WEIGHT) * (angle + angle_rate * DT) + ACCEL_WEIGHT * accel_angle ;\n",
   "why": "<ul>\n"
          "<li><code>fix2float15</code> turns the library's fixed-point reading into a normal decimal number: g for the accelerometer, degrees per second for the gyro.</li>\n"
          "<li>Step 2 is the same low-pass as the handout's motor display: move a small fraction (5 %) of the way toward each new reading.</li>\n"
          "<li><code>atan2f(along, up)</code> gives the angle of the gravity arrow, in radians, the right way round in every quarter of the circle. Level: along = 0, up = 1, so 0°. Hanging down: along = −1, up = 0, so −90°.</li>\n"
          "<li>Step 5 is the <b>complementary filter</b>: 99 % \"where I was, plus what the gyro says I turned in 1 ms\" and 1 % \"what gravity says\". The 1 % slowly pulls any gyro drift back to the truth.</li>\n"
          "<li>The first sample sets the angle straight from gravity, so it doesn't start at 0 and take a second to swing round.</li>\n"
          "</ul>"},
  {"id": "2.3", "op": "after",
   "title": "Show the angle on the screen",
   "where": "In <code>protothread_draw</code>, inside the <code>while(1)</code> loop, right after <code>clearLowFrame(0, BLACK) ;</code> and <code>drawAxes() ;</code>.",
   "simple": "Every frame, write the angle as a number in the top-left corner, so you can check it against a protractor.",
   "anchor": "        clearLowFrame(0, BLACK) ;\n        drawAxes() ;\n",
   "new": "\n"
          "        // Show the angle as a number, top left\n"
          "        setTextSize(2) ;\n"
          "        setCursor(10, 10) ;\n"
          "        sprintf(screentext, \"angle %6.1f deg\", angle) ;\n"
          "        writeString(screentext) ;\n",
   "why": "<ul>\n"
          "<li><code>%6.1f</code> prints a decimal number 6 characters wide with 1 digit after the point, so the text doesn't jump around as the number changes.</li>\n"
          "<li><code>setTextSize(2)</code> doubles the letters. <code>drawAxes()</code> sets it back to 1 at the start of every frame.</li>\n"
          "</ul>"},
]

STEPS[(2, 3)] = [
  {"id": "3.1", "op": "after",
   "title": "Add two helpers that place a value on the screen",
   "where": "Near the top, right after <code>#define PLOT_WIDTH 530</code>.",
   "simple": "Two little formulas: \"this angle goes this many dots down the screen\" and \"this motor power goes this many dots down\". Writing them once keeps the drawing code short.",
   "anchor": "#define PLOT_WIDTH 530\n",
   "new": "// Screen row for an angle in degrees: +90 at row 80, 0 at row 155, -90 at row 230\n"
          "#define ANGLE_Y(a) (TOP_PLOT_BOTTOM - 75 - (int)((a) * 75.0f / 90.0f))\n"
          "// Screen row for a motor command: 0 at row 430, 6000 at row 280\n"
          "#define MOTOR_Y(m) (BOTTOM_PLOT_BOTTOM - (int)((m) * 150 / 6000))\n",
   "why": "<ul>\n"
          "<li>Screen rows count <b>down</b> from the top, so a bigger value means a smaller row number: that's why both formulas subtract.</li>\n"
          "<li>Each plot is 150 rows tall. The angle plot puts 0° in the middle, so ±90° is ±75 rows.</li>\n"
          "<li>A <code>#define</code> with brackets is a <b>macro</b>: the compiler pastes the formula in wherever you write <code>ANGLE_Y(...)</code>.</li>\n"
          "</ul>"},
  {"id": "3.2", "op": "change",
   "title": "Keep a history of angle and motor instead of the six raw readings",
   "where": "Near the top, the block under <code>// Arrays for circular display buffer</code>.",
   "simple": "The demo remembered the last 530 raw readings of all six sensor channels, to draw them as wiggly lines. We only need two things on screen now, so we remember those instead.",
   "anchor": "// Arrays for circular display buffer\n"
             "fix15 ax[PLOT_WIDTH] ;\n"
             "fix15 ay[PLOT_WIDTH] ;\n"
             "fix15 az[PLOT_WIDTH] ;\n"
             "fix15 gx[PLOT_WIDTH] ;\n"
             "fix15 gy[PLOT_WIDTH] ;\n"
             "fix15 gz[PLOT_WIDTH] ;\n",
   "new": "// Arrays for circular display buffer: the last PLOT_WIDTH samples\n"
          "float angle_hist[PLOT_WIDTH] ;   // arm angle, degrees\n"
          "int motor_hist[PLOT_WIDTH] ;     // low-passed motor command, 0-6000\n",
   "why": "<p>A <b>circular buffer</b> is a fixed row of boxes where the newest value overwrites the oldest, like a 530-slot conveyor belt. <code>head</code> points at the slot to overwrite next. Drawing starts at <code>head</code> (oldest) and goes round, so the plot scrolls.</p>"},
  {"id": "3.3", "op": "after",
   "title": "Add the motor variables",
   "where": "Right after <code>uint slice_num ;</code> (under <code>// Some paramters for PWM</code>).",
   "simple": "A box for how hard the motor should push (0 to 6000), and a smoothed copy of it just for drawing.",
   "anchor": "uint slice_num ;\n",
   "new": "\n"
          "// === motor ===\n"
          "// The motor's PWM is on GPIO 4 (physical pin 6): PWM slice 2, channel A\n"
          "// 0 = off, WRAPVAL (6000) = full power\n"
          "volatile int motor_cmd = 0 ;\n"
          "// Smoothed copy of motor_cmd, only for the screen\n"
          "volatile int motor_disp = 0 ;\n",
   "why": "<ul>\n"
          "<li>The demo already sets GPIO 4 and 5 up as PWM outputs on slice 2 and starts them at 0. GPIO 4 is channel A, the pin you used in week 1.</li>\n"
          "<li><code>motor_cmd</code> is what the motor gets. Right now you set it by hand; in step 4 the controller sets it.</li>\n"
          "</ul>"},
  {"id": "3.4", "op": "after",
   "title": "Drive the motor and smooth the command for the screen",
   "where": "In <code>on_pwm_wrap()</code>, right after the last line of the angle code from 2.2 (the line starting <code>angle = (1.0f - ACCEL_WEIGHT)</code>).",
   "simple": "Every millisecond, give the motor its power level, and update a smoothed copy for the screen. The raw command jumps around; the smoothed one shows its shape.",
   "anchor": "    angle = (1.0f - ACCEL_WEIGHT) * (angle + angle_rate * DT) + ACCEL_WEIGHT * accel_angle ;\n",
   "new": "\n"
          "    // --- Drive the motor ---\n"
          "    pwm_set_chan_level(slice_num, PWM_CHAN_A, motor_cmd) ;\n"
          "    // Smooth the command for the screen (the handout's low-pass, about 16 samples)\n"
          "    motor_disp = motor_disp + ((motor_cmd - motor_disp) >> 4) ;\n",
   "why": "<ul>\n"
          "<li>This is the handout's line from the Data display page. <code>&gt;&gt; 4</code> shifts right 4 bits, which divides by 16: each sample moves the display 1/16 of the way to the real command.</li>\n"
          "<li>It's a digital version of an RC low-pass filter. Shift by 5 instead of 4 if the trace is still too noisy.</li>\n"
          "<li>Only the <b>display</b> is smoothed. The motor gets <code>motor_cmd</code> itself.</li>\n"
          "</ul>"},
  {"id": "3.5", "op": "change",
   "title": "Store angle and motor in the history",
   "where": "In <code>on_pwm_wrap()</code>, inside <code>if ((throttle &gt;= threshold))</code>.",
   "simple": "Every 10 ms, drop the newest angle and motor value onto the conveyor belt.",
   "anchor": "        // Replace oldest data in accel arrays with new sample\n"
             "        ax[head] = acceleration[0] ;\n"
             "        ay[head] = acceleration[1] ;\n"
             "        az[head] = acceleration[2] ;\n"
             "\n"
             "        // Replace oldest data in gyro arrays with new sample\n"
             "        gx[head] = gyro[0] ;\n"
             "        gy[head] = gyro[1] ;\n"
             "        gz[head] = gyro[2] ;\n",
   "new": "        // Replace the oldest sample with the newest\n"
          "        angle_hist[head] = angle ;\n"
          "        motor_hist[head] = motor_disp ;\n",
   "why": "<p><code>threshold</code> (10) means only every 10th sample is kept, so 530 points cover 5.3 seconds. Type <code>t</code> over serial to change it: 30 gives 16 seconds, enough for the week 3 demo sequence.</p>"},
  {"id": "3.6", "op": "change",
   "title": "Relabel the bottom plot for the motor",
   "where": "In <code>drawAxes()</code>, the three labels under <code>// Draw bottom plot</code>.",
   "simple": "The bottom plot's labels said −2 to +2 (g). They now say 0 to 6000 (motor power), with a title.",
   "anchor": "    sprintf(screentext, \"0\") ;\n"
             "    setCursor(50, 350) ;\n"
             "    writeString(screentext) ;\n"
             "    sprintf(screentext, \"+2\") ;\n"
             "    setCursor(50, 280) ;\n"
             "    writeString(screentext) ;\n"
             "    sprintf(screentext, \"-2\") ;\n"
             "    setCursor(50, 425) ;\n"
             "    writeString(screentext) ;\n",
   "new": "    sprintf(screentext, \"3000\") ;\n"
          "    setCursor(45, 350) ;\n"
          "    writeString(screentext) ;\n"
          "    sprintf(screentext, \"6000\") ;\n"
          "    setCursor(45, 280) ;\n"
          "    writeString(screentext) ;\n"
          "    sprintf(screentext, \"0\") ;\n"
          "    setCursor(50, 425) ;\n"
          "    writeString(screentext) ;\n"
          "    sprintf(screentext, \"motor command (low-passed)\") ;\n"
          "    setCursor(85, 265) ;\n"
          "    writeString(screentext) ;\n",
   "why": "<p><code>setCursor(x, y)</code> places the next text: x across from the left, y down from the top. Each small letter is 6 dots wide and 8 tall.</p>"},
  {"id": "3.7", "op": "change",
   "title": "Relabel the top plot for the angle",
   "where": "In <code>drawAxes()</code>, the <code>+250</code> and <code>-250</code> labels under <code>// Draw top plot</code>.",
   "simple": "The top plot's labels said ±250 (degrees per second). They now say ±90 (degrees of arm angle), with a title.",
   "anchor": "    sprintf(screentext, \"+250\") ;\n"
             "    setCursor(45, 75) ;\n"
             "    writeString(screentext) ;\n"
             "    sprintf(screentext, \"-250\") ;\n"
             "    setCursor(45, 225) ;\n"
             "    writeString(screentext) ;\n",
   "new": "    sprintf(screentext, \"+90\") ;\n"
          "    setCursor(50, 75) ;\n"
          "    writeString(screentext) ;\n"
          "    sprintf(screentext, \"-90\") ;\n"
          "    setCursor(50, 225) ;\n"
          "    writeString(screentext) ;\n"
          "    sprintf(screentext, \"arm angle (deg)\") ;\n"
          "    setCursor(85, 65) ;\n"
          "    writeString(screentext) ;\n",
   "why": "<p>The middle label, <code>0</code>, stays. On this plot 0 means level.</p>"},
  {"id": "3.8", "op": "change",
   "title": "Draw two traces instead of six",
   "where": "In <code>protothread_draw</code>, the six <code>drawPixel(...)</code> calls inside the <code>for</code> loop.",
   "simple": "For each of the 530 columns, put one white dot for the angle and one green dot for the motor.",
   "anchor": "            drawPixel(LEFT_EDGE + i, (BOTTOM_PLOT_BOTTOM -\n"
             "                (int)(NEW_RANGE*((float)((fix2float15(ax[start])*ACCEL_SCALE)-OLD_MIN)/OLD_RANGE))), WHITE) ;\n"
             "            drawPixel(LEFT_EDGE + i, (BOTTOM_PLOT_BOTTOM -\n"
             "                (int)(NEW_RANGE*((float)((fix2float15(ay[start])*ACCEL_SCALE)-OLD_MIN)/OLD_RANGE))), RED) ;\n"
             "            drawPixel(LEFT_EDGE + i, (BOTTOM_PLOT_BOTTOM -\n"
             "                (int)(NEW_RANGE*((float)((fix2float15(az[start])*ACCEL_SCALE)-OLD_MIN)/OLD_RANGE))), GREEN) ;\n"
             "            drawPixel(LEFT_EDGE + i, (TOP_PLOT_BOTTOM -\n"
             "                (int)(NEW_RANGE*((float)((fix2float15(gx[start]))-OLD_MIN)/OLD_RANGE))), WHITE) ;\n"
             "            drawPixel(LEFT_EDGE + i, (TOP_PLOT_BOTTOM -\n"
             "                (int)(NEW_RANGE*((float)((fix2float15(gy[start]))-OLD_MIN)/OLD_RANGE))), RED) ;\n"
             "            drawPixel(LEFT_EDGE + i, (TOP_PLOT_BOTTOM -\n"
             "                (int)(NEW_RANGE*((float)((fix2float15(gz[start]))-OLD_MIN)/OLD_RANGE))), GREEN) ;\n",
   "new": "            // Top plot: arm angle, white\n"
          "            drawPixel(LEFT_EDGE + i, ANGLE_Y(angle_hist[start]), WHITE) ;\n"
          "            // Bottom plot: low-passed motor command, green\n"
          "            drawPixel(LEFT_EDGE + i, MOTOR_Y(motor_hist[start]), GREEN) ;\n",
   "why": "<p><code>start</code> walks from the oldest sample to the newest, wrapping round at the end, so the newest is always at the right-hand edge. <code>drawPixel</code> ignores dots that fall off the screen, so an out-of-range value can't crash anything.</p>"},
  {"id": "3.9", "op": "after",
   "title": "Add an <code>m</code> command to set the motor by hand",
   "where": "In <code>protothread_serial</code>, right after the closing <code>}</code> of the <code>if (classifier=='t')</code> block.",
   "simple": "Type <code>m</code>, press Enter, then a number from 0 to 6000: the motor runs at that power. Same as week 1, but now you can watch the arm's angle and the motor trace move together.",
   "anchor": "            if (test_in > 0) {\n"
             "                threshold = test_in ;\n"
             "            }\n"
             "        }\n",
   "new": "        // m: set the motor power directly (open loop), 0-6000\n"
          "        else if (classifier=='m') {\n"
          "            sprintf(pt_serial_out_buffer, \"motor (0-6000): \");\n"
          "            serial_write ;\n"
          "            serial_read ;\n"
          "            sscanf(pt_serial_in_buffer,\"%d\", &test_in) ;\n"
          "            if (test_in >= 0 && test_in <= WRAPVAL) {\n"
          "                motor_cmd = test_in ;\n"
          "            }\n"
          "        }\n",
   "why": "<ul>\n"
          "<li>The demo reads one letter (<code>classifier</code>), then asks for a value. We follow the same pattern for each new command.</li>\n"
          "<li><code>sscanf(text, \"%d\", &amp;test_in)</code> reads a whole number out of what you typed. The <code>&amp;</code> means \"put it in <code>test_in</code>\".</li>\n"
          "<li>Anything outside 0–6000 is ignored, so a typo can't ask for more than full power.</li>\n"
          "</ul>"},
]

STEPS[(2, 4)] = [
  {"id": "4.1", "op": "change",
   "title": "Make the text buffer longer",
   "where": "Near the top, under <code>// character array</code>.",
   "simple": "The new status line is longer than 40 letters, so the box that holds the text needs to be bigger.",
   "anchor": "char screentext[40];\n",
   "new": "char screentext[80];\n",
   "why": "<p>Writing more characters than an array holds overwrites whatever is stored next to it in memory. That kind of bug shows up somewhere else entirely, so it's worth avoiding up front.</p>"},
  {"id": "4.2", "op": "after",
   "title": "Remember the target too",
   "where": "Right after <code>int motor_hist[PLOT_WIDTH] ;</code> (from 3.2).",
   "simple": "One more conveyor belt, for where you asked the arm to go, so the screen can show target and actual side by side.",
   "anchor": "int motor_hist[PLOT_WIDTH] ;     // low-passed motor command, 0-6000\n",
   "new": "float target_hist[PLOT_WIDTH] ;  // target angle, degrees\n",
   "why": "<p>Same circular buffer as the other two. In week 3 the target changes every 5 seconds, and this lets you see it step.</p>"},
  {"id": "4.3", "op": "after",
   "title": "Add the controller's settings",
   "where": "Right after <code>volatile int motor_disp = 0 ;</code> (from 3.3).",
   "simple": "An on/off switch for the controller, the angle you want, and the three gains: how hard to push for being off now (P), for having been off a while (I), and against moving too fast (D).",
   "anchor": "volatile int motor_disp = 0 ;\n",
   "new": "\n"
          "// === PID controller ===\n"
          "// 0 = motor set by hand ('m'), 1 = the controller sets it\n"
          "volatile int pid_on = 0 ;\n"
          "// Where we want the arm, degrees (0 = level)\n"
          "volatile float target = 0.0f ;\n"
          "// The three gains. Set them over serial with p, i and d\n"
          "volatile float Kp = 0.0f ;\n"
          "volatile float Ki = 0.0f ;\n"
          "volatile float Kd = 0.0f ;\n"
          "// The I term so far, already in motor units (0-6000)\n"
          "volatile float i_term = 0.0f ;\n",
   "why": "<ul>\n"
          "<li>All gains start at 0, so turning the controller on with no gains set does nothing. You raise them over serial.</li>\n"
          "<li>Units: <code>Kp</code> is motor counts per degree of error. <code>Ki</code> is counts per degree per second. <code>Kd</code> is counts per (degree per second) of turning speed.</li>\n"
          "</ul>"},
  {"id": "4.4", "op": "before",
   "title": "The PID controller",
   "where": "In <code>on_pwm_wrap()</code>, right above <code>// --- Drive the motor ---</code> (from 3.4).",
   "simple": "Every millisecond: how far is the arm from where we want it? Push harder the further off it is (P). Push a bit more if it's been off for a while (I). Ease off if it's already swinging up fast (D). Then keep the answer between off and full power.",
   "anchor": "    // --- Drive the motor ---\n",
   "new": "    // --- PID: work out the motor command from the angle ---\n"
          "    if (pid_on) {\n"
          "        // How far off are we? Positive = the arm is too low\n"
          "        float error = target - angle ;\n"
          "        // I: add up the error over time (stored already multiplied by Ki)\n"
          "        i_term += Ki * error * DT ;\n"
          "        if (i_term > WRAPVAL) i_term = WRAPVAL ;   // don't let it grow forever\n"
          "        if (i_term < 0) i_term = 0 ;\n"
          "        // P + I + D. For D, the gyro already measures how fast the angle changes\n"
          "        float out = Kp * error + i_term - Kd * angle_rate ;\n"
          "        // The motor can only push up, from off to full power\n"
          "        if (out < 0) out = 0 ;\n"
          "        if (out > WRAPVAL) out = WRAPVAL ;\n"
          "        motor_cmd = (int)out ;\n"
          "    }\n"
          "\n",
   "why": "<ul>\n"
          "<li><b>P</b>: <code>Kp * error</code>. 10° too low with <code>Kp</code> = 20 asks for 200 more counts.</li>\n"
          "<li><b>I</b>: each sample adds <code>Ki × error × 0.001 s</code>. A small error that lasts keeps adding up until the motor pushes enough to fix it. Storing it already multiplied by <code>Ki</code> means changing <code>Ki</code> doesn't make the motor jump. Keeping it between 0 and 6000 is <b>anti-windup</b>: it can't pile up to a huge value while the arm is stuck.</li>\n"
          "<li><b>D</b>: the derivative of the error is minus the arm's turning speed (the target isn't moving), and the gyro measures that speed directly. So D is <code>−Kd × angle_rate</code>: no subtracting noisy angles needed.</li>\n"
          "<li>The motor can't pull the arm down, so anything below 0 becomes 0. Gravity does the pulling down.</li>\n"
          "<li>When <code>pid_on</code> is 0 this whole block is skipped and <code>motor_cmd</code> keeps whatever <code>m</code> set.</li>\n"
          "</ul>"},
  {"id": "4.5", "op": "after",
   "title": "Store the target in the history",
   "where": "In <code>on_pwm_wrap()</code>, right after <code>motor_hist[head] = motor_disp ;</code> (from 3.5).",
   "simple": "Drop the target onto its conveyor belt too.",
   "anchor": "        motor_hist[head] = motor_disp ;\n",
   "new": "        target_hist[head] = target ;\n",
   "why": "<p>Stored at the same moment as the angle, so the two line up on screen.</p>"},
  {"id": "4.6", "op": "before",
   "title": "Draw the target in yellow",
   "where": "In <code>protothread_draw</code>, in the <code>for</code> loop, right above <code>// Top plot: arm angle, white</code> (from 3.8).",
   "simple": "A yellow line for where the arm should be, under the white line for where it is.",
   "anchor": "            // Top plot: arm angle, white\n",
   "new": "            // Target angle, yellow (drawn first so the white angle trace is on top)\n"
          "            drawPixel(LEFT_EDGE + i, ANGLE_Y(target_hist[start]), YELLOW) ;\n",
   "why": "<p>Later drawing covers earlier drawing, so when the arm sits exactly on target you'll see white, not yellow.</p>"},
  {"id": "4.7", "op": "after",
   "title": "Show the target, gains and mode on the screen",
   "where": "In <code>protothread_draw</code>, right after the angle text from 2.3.",
   "simple": "A second, smaller line of text: what you've asked for, the three gains, and whether the controller or you is driving the motor.",
   "anchor": "        sprintf(screentext, \"angle %6.1f deg\", angle) ;\n        writeString(screentext) ;\n",
   "new": "        // Second line: target, gains and who is driving the motor\n"
          "        setTextSize(1) ;\n"
          "        setCursor(10, 34) ;\n"
          "        sprintf(screentext, \"%s  target %.1f  Kp %.2f  Ki %.2f  Kd %.2f  motor %d\",\n"
          "                pid_on ? \"PID\" : \"manual\", target, Kp, Ki, Kd, motor_cmd) ;\n"
          "        writeString(screentext) ;\n",
   "why": "<p><code>pid_on ? \"PID\" : \"manual\"</code> is a short if/else: if <code>pid_on</code> is 1 use the first text, otherwise the second. <code>%s</code> prints text, <code>%.2f</code> a decimal number with 2 digits after the point.</p>"},
  {"id": "4.8", "op": "change",
   "title": "Make <code>m</code> switch the controller off",
   "where": "In the <code>m</code> command from 3.9, the line <code>motor_cmd = test_in ;</code>.",
   "simple": "If you set the motor by hand, the controller stops, so the two don't fight over it.",
   "anchor": "                motor_cmd = test_in ;\n",
   "new": "                pid_on = 0 ;\n"
          "                motor_cmd = test_in ;\n",
   "why": "<p>Without this, the controller would overwrite your number 1 ms later.</p>"},
  {"id": "4.9", "op": "after",
   "title": "Add the <code>a</code>, <code>p</code>, <code>i</code>, <code>d</code> and <code>s</code> commands",
   "where": "In <code>protothread_serial</code>, right after the closing <code>}</code> of the <code>m</code> command.",
   "simple": "<code>a</code> sets the angle you want and switches the controller on. <code>p</code>, <code>i</code> and <code>d</code> set the three gains, which work from the very next millisecond. <code>s</code> stops everything.",
   "anchor": "                pid_on = 0 ;\n"
             "                motor_cmd = test_in ;\n"
             "            }\n"
             "        }\n",
   "new": "        // a: set the target angle (degrees) and switch the controller on\n"
          "        else if (classifier=='a') {\n"
          "            sprintf(pt_serial_out_buffer, \"target angle (deg): \");\n"
          "            serial_write ;\n"
          "            serial_read ;\n"
          "            if (sscanf(pt_serial_in_buffer,\"%f\", &float_in) == 1) {\n"
          "                target = float_in ;\n"
          "                if (!pid_on) i_term = 0 ;   // fresh start if it was off\n"
          "                pid_on = 1 ;\n"
          "            }\n"
          "        }\n"
          "        // p, i, d: set a gain. It takes effect on the next sample\n"
          "        else if (classifier=='p' || classifier=='i' || classifier=='d') {\n"
          "            sprintf(pt_serial_out_buffer, \"K%c: \", classifier);\n"
          "            serial_write ;\n"
          "            serial_read ;\n"
          "            if (sscanf(pt_serial_in_buffer,\"%f\", &float_in) == 1) {\n"
          "                if (classifier=='p') Kp = float_in ;\n"
          "                if (classifier=='i') Ki = float_in ;\n"
          "                if (classifier=='d') Kd = float_in ;\n"
          "            }\n"
          "        }\n"
          "        // s: stop. Controller off, motor off\n"
          "        else if (classifier=='s') {\n"
          "            pid_on = 0 ;\n"
          "            motor_cmd = 0 ;\n"
          "        }\n",
   "why": "<ul>\n"
          "<li><code>\"%f\"</code> reads a decimal number into <code>float_in</code>, which the demo already declares. <code>== 1</code> checks that a number was actually found, so pressing Enter on an empty line changes nothing.</li>\n"
          "<li>Changing the target while the controller is already on keeps the I term, so the arm doesn't drop for a moment. It only resets when the controller was off.</li>\n"
          "<li><code>s</code> is your quick stop. The killswitch on the motor board is the hardware one.</li>\n"
          "</ul>"},
]
