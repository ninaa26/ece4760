# Week 1 edit path: encoder first, group's code with the both-edge fix. Generated.
STEPS = {2: [{'id': '2.1',
      'title': "Add the encoder's pins, variables and direction table",
      'op': 'after',
      'where': 'Near the top, right after the four <code>// Wall detection</code> lines (the last one is <code>#define '
               'hitRight…</code>).',
      'anchor': '#define hitRight(a) (a>int2fix15(540))\n',
      'new': '\n'
             '// === rotary encoder ===\n'
             '// These numbers mean GP2 and GP3, NOT physical header pins 2 and 3.\n'
             '// Encoder A -> GP2 (pin 4), B -> GP3 (pin 5), COM (middle pin) -> GND.\n'
             '#define ENCODER_A 2\n'
             '#define ENCODER_B 3\n'
             '\n'
             '// The number shown on the screen. volatile because the interrupt changes it.\n'
             'volatile int encoder_count = 0 ;\n'
             '\n'
             '// Last reading of the two switches, as (A << 1) | B.\n'
             '// At rest both are open (HIGH, pulled up): 0b11 = 3.\n'
             'volatile int encoder_state = 3 ;\n'
             '\n'
             '// Quarter-steps moved since the knob was last at rest\n'
             'volatile int encoder_steps = 0 ;\n'
             '\n'
             '// Direction table, indexed by (old_state << 2) | new_state.\n'
             '// Clockwise, A closes first:  11 -> 01 -> 00 -> 10 -> 11, each move +1.\n'
             '// Counter-clockwise is the same backwards, each move -1.\n'
             '// No change, or a jump of two (a missed edge), is 0.\n'
             'const signed char encoder_table[16] = {\n'
             '   0, -1, +1,  0,\n'
             '  +1,  0,  0, -1,\n'
             '  -1,  0,  0, +1,\n'
             '   0, +1, -1,  0\n'
             '} ;\n',
      'why': '<ul>\n'
             '<li><code>#define ENCODER_A 2</code> gives GPIO 2 a name. These are <b>GPIO</b> numbers, not the '
             'physical pin numbers printed on the board.</li>\n'
             '<li><code>encoder_count</code> is the number on the screen. <b><code>volatile</code></b> tells the '
             'compiler "this can change at any moment behind your back": the interrupt changes it while the drawing '
             'loop reads it.</li>\n'
             '<li><code>encoder_state</code> is where the knob is right now, as a 2-bit number: A is the left bit, B '
             'the right. <code>&lt;&lt; 1</code> means "shift left one bit", which is ×2, so A=1, B=1 gives 3.</li>\n'
             '<li><code>encoder_steps</code> adds up quarter-steps between clicks.</li>\n'
             '<li><code>encoder_table</code> is the answer sheet for "I was at state <i>old</i>, now I\'m at '
             '<i>new</i>: forward, backward, or neither?" Index = old×4 + new. Example: rest (3) → A closes (1) is '
             'clockwise, so entry 3×4+1 = 13 is +1.</li>\n'
             '</ul>'},
     {'id': '2.2',
      'title': 'Add the encoder interrupt',
      'op': 'before',
      'where': 'Above the comment <code>// Create a boid</code>.',
      'anchor': '// Create a boid\n',
      'new': '// Runs by itself every time encoder A or B changes (either direction)\n'
             'void encoder_callback(uint gpio, uint32_t events)\n'
             '{\n'
             '  // Read A and B at the same instant\n'
             '  uint32_t pins = gpio_get_all() ;\n'
             '  int a = (pins >> ENCODER_A) & 1 ;\n'
             '  int b = (pins >> ENCODER_B) & 1 ;\n'
             '  int new_state = (a << 1) | b ;\n'
             '\n'
             '  // Look up +1 / -1 / 0 for this move and add it up\n'
             '  encoder_steps += encoder_table[(encoder_state << 2) | new_state] ;\n'
             '  encoder_state = new_state ;\n'
             '\n'
             '  // Back at rest (both switches open)? Then one whole click just finished.\n'
             '  // A clean click adds up to +4 or -4. Contact rattle adds +1 then -1, which\n'
             '  // cancels, so no debounce timer is needed.\n'
             '  if (new_state == 3) {\n'
             '    if (encoder_steps >= 2)       encoder_count++ ;   // clockwise\n'
             '    else if (encoder_steps <= -2) encoder_count-- ;   // counter-clockwise\n'
             '    encoder_steps = 0 ;\n'
             '  }\n'
             '}\n'
             '\n',
      'why': '<p>This is the <b>interrupt</b> function. You never call it yourself; the hardware runs it every time A '
             'or B changes (set up in 2.3).</p>\n'
             '<ul>\n'
             '<li><code>gpio_get_all()</code> reads every pin at once. <code>(pins &gt;&gt; ENCODER_A) &amp; 1</code> '
             'picks out A: shift bit 2 down to the bottom and keep only that bit.</li>\n'
             '<li>The table lookup turns "where it was → where it is now" into +1, −1 or 0, and '
             '<code>encoder_steps</code> adds them up.</li>\n'
             '<li>When the knob is back at rest, one click has finished: a total of +2 or more is clockwise, −2 or '
             'less counter-clockwise. A clean click totals ±4; accepting ±2 tolerates a missed edge. Then the total '
             'resets.</li>\n'
             '</ul>\n'
             "<p><b>What changed from your group's first version, and why.</b> The first version only woke up when A "
             'fell, waited 3 ms to skip rattle, and read B. That works most of the time. But A also rattles when it '
             '<i>opens</i>, half-way through a clockwise click, and by then B is LOW, so a rattle there could count −1 '
             'by mistake. The datasheet also allows up to 5 ms of rattle, longer than the 3 ms filter. Watching every '
             'change of both switches, and counting only when the knob is back at rest, makes both problems '
             'impossible: a rattle is just a step forward and back.</p>'},
     {'id': '2.3',
      'title': 'Set up the encoder pins and switch on the interrupts',
      'op': 'after',
      'where': 'In <code>main()</code> at the bottom of the file, right after <code>initVGA() ;</code>.',
      'anchor': '  initVGA() ;\n',
      'new': '\n'
             '  // Rotary encoder: A and B are inputs with pull-ups\n'
             '  // (not touching COM = HIGH, touching COM/GND = LOW)\n'
             '  gpio_init(ENCODER_A) ;\n'
             '  gpio_set_dir(ENCODER_A, GPIO_IN) ;\n'
             '  gpio_pull_up(ENCODER_A) ;\n'
             '  gpio_init(ENCODER_B) ;\n'
             '  gpio_set_dir(ENCODER_B, GPIO_IN) ;\n'
             '  gpio_pull_up(ENCODER_B) ;\n'
             '\n'
             '  // Start from wherever the knob really is\n'
             '  encoder_state = (gpio_get(ENCODER_A) << 1) | gpio_get(ENCODER_B) ;\n'
             '\n'
             '  // Run encoder_callback on every change of A and of B (falling and rising)\n'
             '  gpio_set_irq_enabled_with_callback(ENCODER_A, GPIO_IRQ_EDGE_FALL | GPIO_IRQ_EDGE_RISE, true, '
             '&encoder_callback) ;\n'
             '  gpio_set_irq_enabled(ENCODER_B, GPIO_IRQ_EDGE_FALL | GPIO_IRQ_EDGE_RISE, true) ;\n',
      'why': '<p>Each pin is initialised, set as an input, and given its internal <b>pull-up</b>, so it reads HIGH '
             'when the switch is open and LOW when the switch connects it to ground. Then the code records where the '
             'knob starts.</p>\n'
             '<p>The first interrupt call switches on A, for both a <b>falling</b> edge (HIGH → LOW) and a '
             '<b>rising</b> edge (LOW → HIGH), and names the function to run. The second switches on B the same way; '
             "one function serves every pin's interrupt. It all has to be in <code>main()</code>, which runs once at "
             'power-up.</p>'},
     {'id': '2.4',
      'title': 'Make space to build text in',
      'op': 'after',
      'where': 'Inside <code>protothread_anim</code> (the core 0 animation thread), right after the line '
               '<code>PT_BEGIN(pt);</code>.',
      'anchor': 'static PT_THREAD (protothread_anim(struct pt *pt))\n'
                '{\n'
                '    // Mark beginning of thread\n'
                '    PT_BEGIN(pt);\n',
      'new': '\n    // Space to build on-screen text in\n    static char text[48] ;\n',
      'why': "A place to write the words before they're drawn: 48 characters. It must be <b><code>static</code></b>. A "
             "protothread pauses and resumes at <code>PT_YIELD_UNTIL</code>, and ordinary local variables don't "
             'survive the pause; <code>static</code> ones do.'},
     {'id': '2.5',
      'title': 'Show the count on the screen',
      'op': 'after',
      'where': 'Inside the loop of <code>protothread_anim</code>, right after <code>drawArena() ;</code>.',
      'anchor': '      drawArena() ;\n',
      'new': '      // Show the encoder count in the top-left corner\n'
             '      sprintf(text, "Encoder Count: %d", encoder_count) ;\n'
             '      drawTextArial24(10, 10, text, WHITE, BLACK) ;\n',
      'why': '<code>sprintf</code> builds the text: <code>%d</code> is replaced by the number in '
             "<code>encoder_count</code>. <code>drawTextArial24</code> draws it in the library's 24-pixel font at x = "
             '10, y = 10, white on black. It runs every frame, and the frame is wiped at the top of the loop, so the '
             'number is always current.'}],
 3: [{'id': '3.1',
      'title': "Delete the second ball's variables",
      'op': 'delete',
      'where': 'Near the top, under the comment <code>// Boid on core 1</code>.',
      'anchor': '// Boid on core 1\nfix15 boid1_x ;\nfix15 boid1_y ;\nfix15 boid1_vx ;\nfix15 boid1_vy ;\n\n',
      'why': "The demo animates two balls, one per core. We only need one, so the core-1 ball's position "
             '(<code>x</code>, <code>y</code>) and velocity (<code>vx</code>, <code>vy</code>) go. <code>fix15</code> '
             "is the demo's fixed-point number type, explained in step 4."},
     {'id': '3.2',
      'title': 'Delete the semaphore',
      'op': 'delete',
      'where': 'Just below, under <code>// Create a semaphore</code>.',
      'anchor': '// Create a semaphore\nsemaphore_t draw_semaphore ;\n\n',
      'why': 'A <b>semaphore</b> is a signal between the two cores: core 0 used it to tell core 1 "the screen is '
             'cleared, you can draw now". With one core there\'s nobody to signal.'},
     {'id': '3.3',
      'title': 'Delete the serial-input thread',
      'op': 'delete_range',
      'where': 'The whole function <code>protothread_serial</code>, from the comment block <code>// === users serial '
               'input thread</code> down to and including the line <code>} // timer thread</code>.',
      'start': '// ==================================================\n// === users serial input thread',
      'end': '// Animation on core 0',
      'why': 'This thread read numbers typed over a USB-serial cable to change the ball colour. We control things with '
             'the knob instead, and removing it keeps the program simple. (The <code>color</code> variable it changed '
             'stays for now; the ball still uses it.)'},
     {'id': '3.4',
      'title': "Delete core 1's animation and its main",
      'op': 'delete_range',
      'where': 'Everything from the comment <code>// Animation on core 1</code> down to just above <code>// === '
               'main</code>. That is the function <code>protothread_anim1</code> and the function '
               '<code>core1_main</code>.',
      'start': '// Animation on core 1',
      'end': '// ========================================\n// === main',
      'why': 'This was the code the second core ran for the second ball. With both gone, only core 0 runs your '
             'program. Week 3 brings the second core back to animate more balls.'},
     {'id': '3.5',
      'title': 'Stop signalling core 1',
      'op': 'delete',
      'where': 'Inside <code>protothread_anim</code> (the core 0 animation thread), just after <code>clearLowFrame(0, '
               'BLACK);</code>.',
      'anchor': '      // Signal core 1 that it can start drawing\n      PT_SEM_SDK_SIGNAL(pt, &draw_semaphore) ;\n',
      'why': "This line used the semaphore deleted in 2.2. Left in, it wouldn't compile."},
     {'id': '3.6',
      'title': "Don't start core 1",
      'op': 'delete',
      'where': 'In <code>main()</code> at the bottom of the file, just after <code>initVGA() ;</code>.',
      'anchor': '  // Initialize the semaphore\n'
                '  // Arguments: pointer to sem, initial count, max count\n'
                '  sem_init(&draw_semaphore, 0, 1) ;\n'
                '\n'
                '  // start core 1\n'
                '  multicore_reset_core1();\n'
                '  multicore_launch_core1(&core1_main);\n'
                '\n',
      'why': 'These lines set up the semaphore and started the second core running <code>core1_main</code>, which no '
             'longer exists.'},
     {'id': '3.7',
      'title': "Don't start the serial thread",
      'op': 'delete',
      'where': 'In <code>main()</code>, under <code>// add threads</code>.',
      'anchor': '  pt_add_thread(protothread_serial);\n',
      'why': '<code>pt_add_thread</code> tells the protothread scheduler to run a thread. The serial thread is gone, '
             'so only <code>protothread_anim</code> is added now.'},
     {'id': '3.8',
      'title': 'Add the frame time and the LED pin',
      'op': 'after',
      'where': 'Near the top, right after the four <code>// Wall detection</code> lines (the last one is <code>#define '
               'hitRight…</code>).',
      'anchor': '#define hitRight(a) (a>int2fix15(540))\n',
      'new': '\n'
             "// uS per frame at 60 fps, and the Pico's on-board LED\n"
             '#define FRAME_PERIOD_US 16667\n'
             '#define LED_PIN 25\n',
      'why': '<code>#define</code> gives a number a name, so the code can say <code>FRAME_PERIOD_US</code> instead of '
             "a bare 16667. At 60 frames per second each frame lasts 1/60 s = <b>16 667 µs</b>, and that's the budget "
             'for all the work in one frame. The LED on the Pico board is wired to GPIO 25; it will light when a frame '
             'runs over that budget.'},
     {'id': '3.9',
      'title': 'Add variables for timing',
      'op': 'after',
      'where': 'Inside <code>protothread_anim</code>, right after <code>static char text[48] ;</code> (from 2.4).',
      'anchor': '    static char text[48] ;\n',
      'new': '    // Frame timing\n'
             "    static uint32_t frame_start ;           // when this frame's work began (us)\n"
             '    static int spare_us = FRAME_PERIOD_US ; // time left over last frame (us)\n',
      'why': 'Two more notes for the loop, <code>static</code> for the same reason as 2.4. <code>uint32_t</code> is an '
             'unsigned 32-bit whole number, the type the microsecond timer returns.'},
     {'id': '3.10',
      'title': 'Note the time when each frame starts',
      'op': 'after',
      'where': 'Inside the <code>while(1)</code> loop, right after <code>PT_YIELD_UNTIL(pt, draw_start_signal()) '
               ';</code>.',
      'anchor': '      PT_YIELD_UNTIL(pt, draw_start_signal()) ;\n',
      'new': '      frame_start = time_us_32() ;\n',
      'why': "<code>time_us_32()</code> reads the Pico's microsecond clock. The line above waits for the VGA library's "
             '"start drawing" signal, so this is the moment the frame\'s work begins.'},
     {'id': '3.11',
      'title': 'Show the spare time, light the LED if late',
      'op': 'after',
      'where': 'Inside the loop, right after the <code>drawTextArial24(…)</code> line from 2.5.',
      'anchor': '      drawTextArial24(10, 10, text, WHITE, BLACK) ;\n',
      'new': '\n'
             '      // Spare time, under the count\n'
             '      sprintf(text, "Spare time: %d us", spare_us) ;\n'
             '      drawTextGLCD(10, 40, text, WHITE, BLACK) ;\n'
             '\n'
             '      // How much of the 16.7 ms frame was left? LED on if we ran over.\n'
             '      spare_us = FRAME_PERIOD_US - (int)(time_us_32() - frame_start) ;\n'
             '      gpio_put(LED_PIN, spare_us < 0) ;\n',
      'why': 'A second line of text, in the small built-in font, under the count. Then: time now minus '
             "<code>frame_start</code> is how long this frame's work took, and 16 667 minus that is what's left. "
             '<code>gpio_put(LED_PIN, …)</code> turns the LED on only if the answer is negative. The number shows on '
             "the <i>next</i> frame, because this frame's text is already drawn by then."},
     {'id': '3.12',
      'title': 'Set up the LED pin',
      'op': 'after',
      'where': 'In <code>main()</code>, right after <code>initVGA() ;</code> (above the encoder setup from 2.3).',
      'anchor': '  initVGA() ;\n',
      'new': '\n'
             '  // On-board LED: lights when a frame runs late\n'
             '  gpio_init(LED_PIN) ;\n'
             '  gpio_set_dir(LED_PIN, GPIO_OUT) ;\n',
      'why': 'Before a pin can be used it must be initialised (<code>gpio_init</code>) and set as an input or an '
             'output (<code>gpio_set_dir</code>). The LED is an output: the code drives it.'}],
 4: [{'id': '4.1',
      'title': 'Fix two fixed-point macros',
      'op': 'replace',
      'where': 'Near the top, in <code>// === the fixed point macros</code>.',
      'anchor': '#define int2fix15(a) ((fix15)(a << 15))\n#define fix2int15(a) ((int)(a >> 15))\n',
      'new': '#define int2fix15(a) ((fix15)((a) << 15))\n#define fix2int15(a) ((int)((a) >> 15))\n',
      'why': 'A <b>macro</b> is copy-and-paste done by the compiler: <code>int2fix15(a)</code> pastes whatever you '
             "pass in place of <code>a</code>. The demo's version doesn't bracket <code>a</code>, so the shift can "
             'grab only part of the argument when it contains other operators. C does <code>+</code> and '
             '<code>-</code> before <code>&lt;&lt;</code>, so the sums in this lab would work either way, but '
             "bracketing macro arguments is a standard habit that stops a whole class of bugs. That's a good thing to "
             'be able to say in the debugging quiz.'},
     {'id': '4.2',
      'title': 'Replace the box walls with the Galton parameters',
      'op': 'replace',
      'where': 'Just below the macros, under <code>// Wall detection</code>.',
      'anchor': '// Wall detection\n'
                '#define hitBottom(b) (b>int2fix15(380))\n'
                '#define hitTop(b) (b<int2fix15(100))\n'
                '#define hitLeft(a) (a<int2fix15(100))\n'
                '#define hitRight(a) (a>int2fix15(540))\n',
      'new': '// Galton board parameters, handout Fig. 2. Time in frames, space in pixels.\n'
             '#define GRAVITY      float2fix15(0.37)  // added to vy every frame\n'
             '#define BALL_RADIUS  4\n'
             '#define SCREEN_W     640\n'
             '#define SCREEN_H     480\n'
             '#define DROP_X       320                // balls drop from the middle\n',
      'why': "The demo's ball bounced inside a box from (100, 100) to (540, 380). Ours falls down the whole 640 × 480 "
             "screen, so the box goes and the handout's numbers come in. <code>float2fix15(0.37)</code> converts 0.37 "
             "into fixed point (12 124). Because it's a constant, the compiler works that out once, not every frame."},
     {'id': '4.3',
      'title': 'Replace the demo ball with a Galton ball',
      'op': 'replace',
      'where': 'Near the top: the colour variable and the four <code>boid0</code> variables under <code>// Boid on '
               'core 0</code>.',
      'anchor': '// the color of the boid\n'
                'char color = WHITE ;\n'
                '\n'
                '// Boid on core 0\n'
                'fix15 boid0_x ;\n'
                'fix15 boid0_y ;\n'
                'fix15 boid0_vx ;\n'
                'fix15 boid0_vy ;\n',
      'new': '// One ball: position (px) and velocity (px per frame), in fixed point\n'
             'typedef struct {\n'
             '  fix15 x, y ;\n'
             '  fix15 vx, vy ;\n'
             '} ball_t ;\n'
             '\n'
             'ball_t ball ;\n',
      'why': 'A <b><code>struct</code></b> bundles related variables under one name. <code>ball_t</code> is a new '
             'type, "a ball", with four numbers inside, and <code>ball</code> is one of them. You write '
             "<code>ball.x</code> for its x. In week 2 you'll make an array of these for many balls, which is why it's "
             'worth doing now.'},
     {'id': '4.4',
      'title': "Replace the demo's ball functions with spawn and update",
      'op': 'replace_range',
      'where': 'Three demo functions in a row: from the comment <code>// Create a boid</code> down to just above '
               '<code>// Animation on core 0</code>. That is <code>spawnBoid</code>, <code>drawArena</code> and '
               '<code>wallsAndEdges</code>.',
      'start': '// Create a boid\n',
      'end': '// Animation on core 0',
      'new': '// Put the ball at the top middle: not falling yet, drifting a little sideways\n'
             'void spawn_ball(ball_t *b)\n'
             '{\n'
             '  b->x  = int2fix15(DROP_X) ;\n'
             '  b->y  = int2fix15(BALL_RADIUS) ;\n'
             '  // random whole number 0..16383, minus 8192 -> -0.25 .. +0.25 in fix15\n'
             '  b->vx = (fix15)((rand() & 0x3FFF) - 0x2000) ;\n'
             '  b->vy = 0 ;\n'
             '}\n'
             '\n'
             "// Move the ball one frame (the handout's pseudocode)\n"
             'void update_ball(ball_t *b)\n'
             '{\n'
             '  // Move by the velocity\n'
             '  b->x += b->vx ;\n'
             '  b->y += b->vy ;\n'
             '\n'
             '  // Fell out of the bottom: start again at the top\n'
             '  if (b->y > int2fix15(SCREEN_H + BALL_RADIUS)) {\n'
             '    spawn_ball(b) ;\n'
             '    return ;\n'
             '  }\n'
             '\n'
             '  // Hit a side or the top: flip that part of the velocity\n'
             '  if (b->x < int2fix15(BALL_RADIUS)) {\n'
             '    b->x = int2fix15(BALL_RADIUS) ;\n'
             '    b->vx = -b->vx ;\n'
             '  }\n'
             '  else if (b->x > int2fix15(SCREEN_W - 1 - BALL_RADIUS)) {\n'
             '    b->x = int2fix15(SCREEN_W - 1 - BALL_RADIUS) ;\n'
             '    b->vx = -b->vx ;\n'
             '  }\n'
             '  if (b->y < int2fix15(BALL_RADIUS)) {\n'
             '    b->y = int2fix15(BALL_RADIUS) ;\n'
             '    b->vy = -b->vy ;\n'
             '  }\n'
             '\n'
             '  // Gravity: a little faster downward every frame\n'
             '  b->vy += GRAVITY ;\n'
             '}\n'
             '\n',
      'why': '<p><b><code>spawn_ball</code></b> drops a ball, as the handout asks: top middle, <code>vy = 0</code>, '
             'small random <code>vx</code>. <code>ball_t *b</code> means "a pointer to a ball": the function changes '
             'the actual ball you hand it, and <code>b-&gt;x</code> is how you reach its x through the pointer.</p>\n'
             '<p><b><code>update_ball</code></b> is the handout pseudocode without the pegs. Move by the velocity. If '
             "it's below the screen, drop it again (<code>return</code> skips the rest). Bounce off the sides and top "
             'by flipping the sign of that velocity. Finally add gravity. Note it checks <code>SCREEN_H + '
             'BALL_RADIUS</code>, so the ball has fully left the screen before it respawns.</p>'},
     {'id': '4.5',
      'title': 'Drop the first ball',
      'op': 'replace',
      'where': 'In <code>protothread_anim</code>, above the <code>while(1)</code> loop, under <code>// Spawn a '
               'boid</code>.',
      'anchor': '    // Spawn a boid\n    spawnBoid(&boid0_x, &boid0_y, &boid0_vx, &boid0_vy, 0);\n',
      'new': '    // Drop the first ball\n    spawn_ball(&ball) ;\n',
      'why': 'Runs once, before the loop starts. <code>&amp;ball</code> means "the address of <code>ball</code>", '
             'which is the pointer <code>spawn_ball</code> expects.'},
     {'id': '4.6',
      'title': 'Move and draw the ball each frame',
      'op': 'replace',
      'where': "Inside the loop, the lines under <code>// update boid's position and velocity</code>, down to "
               '<code>drawArena() ;</code>.',
      'anchor': "      // update boid's position and velocity\n"
                '      wallsAndEdges(&boid0_x, &boid0_y, &boid0_vx, &boid0_vy) ;\n'
                '      // draw the boid at its new position\n'
                '      fillCircle(fix2int15(boid0_x), fix2int15(boid0_y), 15, color);\n'
                '      // draw the boundaries\n'
                '      drawArena() ;\n',
      'new': '      // Move the ball and draw it\n'
             '      update_ball(&ball) ;\n'
             '      fillCircle(fix2int15(ball.x), fix2int15(ball.y), BALL_RADIUS, CYAN) ;\n',
      'why': 'Every frame: one physics update, then draw a filled circle. The screen works in whole pixels, so '
             '<code>fix2int15</code> converts the fixed-point position (dropping the fraction). Radius 4, colour cyan. '
             'The frame was already wiped by <code>clearLowFrame</code> at the top of the loop, so the old ball '
             "doesn't linger."},
     {'id': '4.7',
      'title': 'Mix up the random numbers',
      'op': 'after',
      'where': 'In <code>main()</code>, right after the <code>gpio_set_irq_enabled(ENCODER_B, …)</code> line (from '
               '2.3).',
      'anchor': '  gpio_set_irq_enabled(ENCODER_B, GPIO_IRQ_EDGE_FALL | GPIO_IRQ_EDGE_RISE, true) ;\n',
      'new': '\n  // Seed the random numbers used for the drift\n  srand(time_us_32()) ;\n',
      'why': '<code>rand()</code> gives a fixed sequence of "random" numbers starting from a seed. <code>srand</code> '
             "sets the seed, here from the clock, so the sequence isn't identical every time. Each new drop takes the "
             'next number, so drops differ either way.'}],
 5: [{'id': '5.1',
      'title': 'Add the peg and collision constants',
      'op': 'after',
      'where': 'Near the top, right after <code>#define BALL_RADIUS  4</code> (from 4.2).',
      'anchor': '#define BALL_RADIUS  4\n',
      'new': '#define PEG_RADIUS   6\n'
             '#define BOUNCINESS   float2fix15(0.5)   // speed kept after hitting a new peg\n'
             '// Touching distance (centre to centre), and where to put the ball after a hit\n'
             '#define COLLIDE_DIST  int2fix15(BALL_RADIUS + PEG_RADIUS)\n'
             '#define TELEPORT_DIST int2fix15(BALL_RADIUS + PEG_RADIUS + 1)\n'
             '// Alpha max plus beta min: distance ~= ALPHA * bigger + BETA * smaller\n'
             '#define AMBM_ALPHA   float2fix15(0.960433870)\n'
             '#define AMBM_BETA    float2fix15(0.397824735)\n',
      'why': "The rest of the handout's numbers. <code>COLLIDE_DIST</code> is 4 + 6 = 10 px: closer than that, centre "
             'to centre, means touching. <code>TELEPORT_DIST</code> is 11 px, 1 px clear. The two <code>AMBM</code> '
             'numbers are the standard alpha max plus beta min constants.'},
     {'id': '5.2',
      'title': 'Give the ball a memory of the last peg',
      'op': 'after',
      'where': 'Inside <code>typedef struct { … } ball_t</code> (from 4.3), after the line <code>fix15 vx, vy '
               ';</code>.',
      'anchor': '  fix15 vx, vy ;\n',
      'new': '  int last_peg ;     // index of the last peg hit, -1 = none\n',
      'why': 'The ball has to know which peg it hit last, so it loses energy (and makes a sound) only on a <i>new</i> '
             'peg. A ball can touch one peg for several frames in a row.'},
     {'id': '5.3',
      'title': 'Add the peg list',
      'op': 'after',
      'where': 'Right after <code>ball_t ball ;</code>.',
      'anchor': 'ball_t ball ;\n',
      'new': '\n'
             '// The pegs. One for now; week 2 fills in all 136.\n'
             '#define NUM_PEGS 1\n'
             'fix15 peg_x[NUM_PEGS] ;\n'
             'fix15 peg_y[NUM_PEGS] ;\n',
      'why': "Two <b>arrays</b>, lists of numbers: <code>peg_x[0]</code> is the first peg's x. With one peg they hold "
             'one number each, but written this way week 2 only has to change <code>NUM_PEGS</code> and fill them in.'},
     {'id': '5.4',
      'title': "A new ball hasn't hit anything",
      'op': 'after',
      'where': 'In <code>spawn_ball</code>, after <code>b->vy = 0 ;</code>.',
      'anchor': '  b->vy = 0 ;\n',
      'new': '  b->last_peg = -1 ;\n',
      'why': "−1 isn't a real peg index, so the first peg the ball meets always counts as new."},
     {'id': '5.5',
      'title': 'Add the distance estimate',
      'op': 'before',
      'where': 'Above <code>// Move the ball one frame</code>, between <code>spawn_ball</code> and '
               '<code>update_ball</code>.',
      'anchor': '// Move the ball one frame',
      'new': '// Distance from (0,0) to (dx,dy) without a square root: within about 4 %\n'
             'fix15 ambm_distance(fix15 dx, fix15 dy)\n'
             '{\n'
             '  fix15 ax = absfix15(dx) ;\n'
             '  fix15 ay = absfix15(dy) ;\n'
             '  fix15 big   = ax > ay ? ax : ay ;\n'
             '  fix15 small = ax > ay ? ay : ax ;\n'
             '  return multfix15(AMBM_ALPHA, big) + multfix15(AMBM_BETA, small) ;\n'
             '}\n'
             '\n',
      'why': "Replaces the pseudocode's <code>sqrt(dx² + dy²)</code>. Take the sizes of dx and dy "
             '(<code>absfix15</code> drops the minus sign), then 0.96 × the bigger + 0.40 × the smaller. <code>a &gt; '
             'b ? a : b</code> means "a if a is bigger, else b". It must come above <code>update_ball</code>, because '
             "in C a function has to be defined before it's used."},
     {'id': '5.6',
      'title': 'Check the peg and bounce off it',
      'op': 'before',
      'where': 'In <code>update_ball</code>, between the &ldquo;move by the velocity&rdquo; lines and <code>// Fell '
               'out of the bottom</code>.',
      'anchor': '  // Fell out of the bottom',
      'new': '  // Check every peg\n'
             '  for (int p = 0; p < NUM_PEGS; p++) {\n'
             '    fix15 dx = b->x - peg_x[p] ;\n'
             '    fix15 dy = b->y - peg_y[p] ;\n'
             '\n'
             '    // Quick test first: too far in x or in y means no contact\n'
             '    if (absfix15(dx) < COLLIDE_DIST && absfix15(dy) < COLLIDE_DIST) {\n'
             '      fix15 distance = ambm_distance(dx, dy) ;\n'
             '\n'
             '      if (distance < COLLIDE_DIST && distance > 0) {\n'
             "        // Normal: length-1 arrow from the peg's centre through the ball's\n"
             '        fix15 inv_distance = divfix(int2fix15(1), distance) ;\n'
             '        fix15 normal_x = multfix15(dx, inv_distance) ;\n'
             '        fix15 normal_y = multfix15(dy, inv_distance) ;\n'
             '\n'
             '        // -2 x (how much of the velocity points along the normal)\n'
             '        fix15 intermediate = -2 * (multfix15(normal_x, b->vx) +\n'
             '                                   multfix15(normal_y, b->vy)) ;\n'
             '\n'
             '        // Put the ball just outside the peg, along the normal\n'
             '        b->x = peg_x[p] + multfix15(normal_x, TELEPORT_DIST) ;\n'
             '        b->y = peg_y[p] + multfix15(normal_y, TELEPORT_DIST) ;\n'
             '\n'
             '        // Bounce: flip the part of the velocity that points into the peg\n'
             '        b->vx += multfix15(normal_x, intermediate) ;\n'
             '        b->vy += multfix15(normal_y, intermediate) ;\n'
             '\n'
             '        // First contact with this peg: lose energy (step 6 adds the sound)\n'
             '        if (p != b->last_peg) {\n'
             '          b->vx = multfix15(BOUNCINESS, b->vx) ;\n'
             '          b->vy = multfix15(BOUNCINESS, b->vy) ;\n'
             '          b->last_peg = p ;\n'
             '        }\n'
             '      }\n'
             '    }\n'
             '  }\n'
             '\n',
      'why': 'This is the handout pseudocode, line for line, in fixed point. Walk through it with the picture above:\n'
             '<ol>\n'
             "<li><code>dx</code>, <code>dy</code>: the gaps from the peg's centre to the ball's.</li>\n"
             "<li>The quick box test skips everything if either gap is 10 px or more. That's true on almost every "
             'frame.</li>\n'
             '<li><code>distance</code> via alpha max plus beta min. <code>distance &gt; 0</code> guards against '
             'dividing by zero.</li>\n'
             '<li>The normal: dx and dy divided by the distance. Dividing is slow, so it divides once '
             '(<code>divfix</code>, for 1/distance) and multiplies twice.</li>\n'
             '<li><code>intermediate</code> = −2 × the dot product, then the ball is moved to 11 px out and the '
             'velocity is reflected.</li>\n'
             '<li>Only on a new peg: multiply the velocity by 0.5 and remember this peg.</li>\n'
             '</ol>'},
     {'id': '5.7',
      'title': 'Draw the peg',
      'op': 'after',
      'where': "In the loop, right after the ball's <code>fillCircle(…, BALL_RADIUS, CYAN) ;</code> line (from 4.6).",
      'anchor': '      fillCircle(fix2int15(ball.x), fix2int15(ball.y), BALL_RADIUS, CYAN) ;\n',
      'new': '\n'
             '      // Draw the pegs\n'
             '      for (int p = 0; p < NUM_PEGS; p++) {\n'
             '        fillCircle(fix2int15(peg_x[p]), fix2int15(peg_y[p]), PEG_RADIUS, WHITE) ;\n'
             '      }\n',
      'why': 'A white filled circle of radius 6 at each peg. The <code>for</code> loop goes through the list; with one '
             'peg it runs once.'},
     {'id': '5.8',
      'title': 'Place the peg',
      'op': 'after',
      'where': 'In <code>main()</code>, right after <code>srand(time_us_32()) ;</code> (from 4.7).',
      'anchor': '  srand(time_us_32()) ;\n',
      'new': '\n'
             '  // The one peg, straight under the drop point\n'
             '  peg_x[0] = int2fix15(DROP_X) ;\n'
             '  peg_y[0] = int2fix15(120) ;\n',
      'why': 'x = 320 is the drop point, so the ball lands on it. y = 120 leaves room for the text above and a visible '
             'fall before the hit.'}],
 6: [{'id': '6.1',
      'title': 'Link the SPI library',
      'op': 'after',
      'file': 'cmake',
      'where': 'In <b><code>CMakeLists.txt</code></b> (not the .c file), in the <code>target_link_libraries</code> '
               'list, after <code>hardware_dma</code>.',
      'anchor': '                        hardware_dma\n',
      'new': '                        hardware_spi\n',
      'why': '<code>CMakeLists.txt</code> is the build recipe: which files to compile and which SDK libraries to '
             "include. The DAC talks over SPI, and the demo didn't use SPI, so its library has to be added or the "
             'build fails with "undefined reference to spi_init".'},
     {'id': '6.2',
      'title': 'Include the SPI header',
      'op': 'after',
      'where': 'In the <code>#include</code> lines at the top, after <code>#include "hardware/dma.h"</code>.',
      'anchor': '#include "hardware/dma.h"\n',
      'new': '#include "hardware/spi.h"\n',
      'why': 'The header declares the SPI functions (<code>spi_init</code> and so on) so the compiler knows them. 6.1 '
             'supplies the actual code; this tells the compiler it exists.'},
     {'id': '6.3',
      'title': "Add the sound's settings and storage",
      'op': 'before',
      'where': 'Above <code>// === rotary encoder ===</code> (from 2.1).',
      'anchor': '// === rotary encoder ===',
      'new': '// === thunk sound ===\n'
             '// SPI pins to the DAC, as in the course DMA demo\n'
             '#define PIN_CS   5\n'
             '#define PIN_SCK  6\n'
             '#define PIN_MOSI 7\n'
             '#define SPI_PORT spi0\n'
             '// DAC word: top 4 bits = channel B, 1x gain, on. Bottom 12 bits = level.\n'
             '#define DAC_config_chan_B 0b1011000000000000\n'
             '#define DAC_MIDSCALE      2048          // the middle level = silence\n'
             '// DMA timer 0 ticks at 150 MHz x 1/3401 = 44 105 times a second\n'
             '#define THUNK_TIMER_X     1\n'
             '#define THUNK_TIMER_Y     3401\n'
             '#define THUNK_FS          (150000000.0f * THUNK_TIMER_X / THUNK_TIMER_Y)\n'
             '#define THUNK_LEN         1323          // 1323 samples = 30 ms\n'
             '\n'
             'unsigned short thunk_table[THUNK_LEN] ;            // the sound, as DAC words\n'
             'unsigned short * thunk_pointer = &thunk_table[0] ; // where the sound starts\n'
             'int thunk_data_chan ;                               // DMA channel numbers,\n'
             'int thunk_ctrl_chan ;                               // picked at startup\n'
             '\n',
      'why': '<ul>\n'
             '<li>Pins and DAC settings are the same as the DMA demo, but using <b>channel B</b>, which your jack is '
             'wired to.</li>\n'
             '<li>The timer numbers set the playback speed: 150 000 000 × 1 / 3401 ≈ 44 105 samples per second, like '
             'CD audio.</li>\n'
             '<li><code>thunk_table</code> will hold the 1 323 DAC words of the sound (<code>unsigned short</code> = '
             '16-bit whole number, the size of one DAC word).</li>\n'
             "<li><code>thunk_pointer</code> holds the <i>address</i> of the table's first entry. The control DMA "
             'channel copies it, which is how the sound gets "rewound".</li>\n'
             '</ul>'},
     {'id': '6.4',
      'title': 'Add the functions that build, set up and play the sound',
      'op': 'before',
      'where': 'Above <code>// Runs by itself every time encoder A or B changes</code> (from 2.2).',
      'anchor': '// Runs by itself every time encoder A or B changes (either direction)',
      'new': '// Work out the thunk once, at startup: a low tone that drops in pitch and\n'
             '// fades out. Starts and ends at the middle level, so no click.\n'
             'void build_thunk_table(void)\n'
             '{\n'
             '  float phase = 0.0f ;\n'
             '  const float taper_len = 0.002f * THUNK_FS ;      // last 2 ms fade to silence\n'
             '  for (int i = 0; i < THUNK_LEN; i++) {\n'
             '    float t = (float)i / THUNK_FS ;                // time in seconds\n'
             '    float freq = 110.0f + 220.0f * expf(-t / 0.008f) ;          // 330 -> 110 Hz\n'
             '    float amp = 1800.0f * (1.0f - expf(-t / 0.0003f)) * expf(-t / 0.007f) ;\n'
             '    float remaining = (float)(THUNK_LEN - 1 - i) ;\n'
             '    if (remaining < taper_len) amp *= remaining / taper_len ;\n'
             '\n'
             '    phase += 6.2831853f * freq / THUNK_FS ;\n'
             '    int sample = DAC_MIDSCALE + (int)(amp * sinf(phase)) ;\n'
             '    thunk_table[i] = DAC_config_chan_B | (sample & 0x0fff) ;\n'
             '  }\n'
             '}\n'
             '\n'
             '// SPI to the DAC, plus two DMA channels (adapted from e_DMA_Demo)\n'
             'void init_thunk_dma(void)\n'
             '{\n'
             '  // SPI at 20 MHz, 16-bit words, as in Lab 1\n'
             '  spi_init(SPI_PORT, 20000000) ;\n'
             '  spi_set_format(SPI_PORT, 16, 0, 0, 0) ;\n'
             '  gpio_set_function(PIN_CS, GPIO_FUNC_SPI) ;\n'
             '  gpio_set_function(PIN_SCK, GPIO_FUNC_SPI) ;\n'
             '  gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI) ;\n'
             '\n'
             '  // Park the DAC at the middle level, where every thunk starts and ends\n'
             '  uint16_t rest = DAC_config_chan_B | DAC_MIDSCALE ;\n'
             '  spi_write16_blocking(SPI_PORT, &rest, 1) ;\n'
             '\n'
             '  build_thunk_table() ;\n'
             '\n'
             '  // Ask for two free DMA channels (the VGA library already took four)\n'
             '  thunk_data_chan = dma_claim_unused_channel(true) ;\n'
             '  thunk_ctrl_chan = dma_claim_unused_channel(true) ;\n'
             '\n'
             '  // Control channel: copy one 32-bit word, thunk_pointer, into the data\n'
             '  // channel\'s "read address + trigger" register. That rewinds it and starts it.\n'
             '  dma_channel_config c = dma_channel_get_default_config(thunk_ctrl_chan) ;\n'
             '  channel_config_set_transfer_data_size(&c, DMA_SIZE_32) ;\n'
             '  channel_config_set_read_increment(&c, false) ;\n'
             '  channel_config_set_write_increment(&c, false) ;\n'
             '  dma_channel_configure(\n'
             '    thunk_ctrl_chan, &c,\n'
             '    &dma_hw->ch[thunk_data_chan].al3_read_addr_trig,  // write to here\n'
             '    &thunk_pointer,                                   // read from here\n'
             '    1,                                                // one word\n'
             "    false                                             // don't start yet\n"
             '  ) ;\n'
             '\n'
             '  // Data channel: copy THUNK_LEN 16-bit words from the table to the SPI port,\n'
             '  // one each time DMA timer 0 ticks. Not chained to anything: plays once.\n'
             '  dma_channel_config c2 = dma_channel_get_default_config(thunk_data_chan) ;\n'
             '  channel_config_set_transfer_data_size(&c2, DMA_SIZE_16) ;\n'
             '  channel_config_set_read_increment(&c2, true) ;\n'
             '  channel_config_set_write_increment(&c2, false) ;\n'
             '  dma_timer_set_fraction(0, THUNK_TIMER_X, THUNK_TIMER_Y) ;\n'
             '  channel_config_set_dreq(&c2, DREQ_DMA_TIMER0) ;\n'
             '  dma_channel_configure(\n'
             '    thunk_data_chan, &c2,\n'
             '    &spi_get_hw(SPI_PORT)->dr,   // write to the SPI data register\n'
             '    thunk_table,                 // read from the table\n'
             '    THUNK_LEN,                   // this many samples\n'
             "    false                        // don't start yet\n"
             '  ) ;\n'
             '}\n'
             '\n'
             '// Play the thunk: one line of work for the CPU. If one is already playing,\n'
             '// let it finish instead of restarting it.\n'
             'void play_thunk(void)\n'
             '{\n'
             '  if (!dma_channel_is_busy(thunk_data_chan)) {\n'
             '    dma_start_channel_mask(1u << thunk_ctrl_chan) ;\n'
             '  }\n'
             '}\n'
             '\n',
      'why': "Compare <code>init_thunk_dma</code> with <code>e_DMA_Demo/dma-demo.c</code> side by side. It's the same "
             'shape, with these changes:\n'
             '<ul>\n'
             '<li><b>No <code>channel_config_set_chain_to</code> lines.</b> In the demo, each channel restarted the '
             'other when it finished, forever, so the sine never stopped. Without the chain, each start plays the '
             'table once.</li>\n'
             '<li>The control channel writes to <code>al3_read_addr_trig</code>, not <code>read_addr</code>. "trig" '
             'means writing it also <i>starts</i> the data channel. So one start of the control channel rewinds and '
             'plays.</li>\n'
             "<li><code>DREQ_DMA_TIMER0</code> instead of the demo's raw <code>0x3b</code>. It's the same value, but "
             'with a readable name.</li>\n'
             "<li>The timer fraction is 1/3401, because the demo's comment assumed a 125 MHz clock and we run at 150 "
             'MHz.</li>\n'
             "<li>MISO isn't set up: the DAC never sends anything back, and the demo's MISO pin, GPIO 4, is where your "
             "encoder's push switch goes.</li>\n"
             '</ul>\n'
             '<p><b><code>build_thunk_table</code></b> works out the sound once. For each sample it computes a sine '
             'wave whose pitch falls (<code>freq</code>) and whose loudness rises in 0.3 ms then decays '
             '(<code>amp</code>). It adds that to the middle level 2048, and puts the channel-B settings in the top 4 '
             'bits with <code>|</code> (bitwise OR). <code>&amp; 0x0fff</code> keeps the level to 12 bits.</p>\n'
             "<p><b><code>play_thunk</code></b> checks the data channel isn't still playing, then starts the control "
             "channel. <code>1u &lt;&lt; thunk_ctrl_chan</code> is a number with just that channel's bit set, which is "
             'the form <code>dma_start_channel_mask</code> wants.</p>'},
     {'id': '6.5',
      'title': 'Play the thunk on a new peg',
      'op': 'before',
      'where': 'In <code>update_ball</code>, inside <code>if (p != b->last_peg) {</code> (from 5.6), before the '
               'bounciness lines.',
      'anchor': '          b->vx = multfix15(BOUNCINESS, b->vx) ;\n',
      'new': '          play_thunk() ;\n',
      'why': 'The pseudocode\'s <code>dma.trigger()</code>. It\'s inside the "new peg" check, so a ball resting '
             'against a peg for a few frames only thunks once.'},
     {'id': '6.6',
      'title': 'Set up the sound at startup',
      'op': 'after',
      'where': 'In <code>main()</code>, right after the LED setup (<code>gpio_set_dir(LED_PIN, GPIO_OUT) ;</code>).',
      'anchor': '  gpio_set_dir(LED_PIN, GPIO_OUT) ;\n',
      'new': '\n  // SPI to the DAC and the two DMA channels for the thunk\n  init_thunk_dma() ;\n',
      'why': 'It must come <b>after <code>initVGA()</code></b>. The VGA library takes specific DMA channels, and '
             "<code>dma_claim_unused_channel</code> then hands us two it didn't take. The other way round, we might "
             'grab a channel the VGA library needs.'}]}
