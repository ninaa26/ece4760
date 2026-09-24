
/**
 * Hunter Adams (vha3@cornell.edu)
 *
 * This demonstration animates two balls bouncing about the screen.
 * Through a serial interface, the user can change the ball color.
 *
 * HARDWARE CONNECTIONS
  - GPIO 16 ---> VGA Hsync
  - GPIO 17 ---> VGA Vsync
  - GPIO 18 ---> VGA Green lo-bit --> 470 ohm resistor --> VGA_Green
  - GPIO 19 ---> VGA Green hi_bit --> 330 ohm resistor --> VGA_Green
  - GPIO 20 ---> 330 ohm resistor ---> VGA-Blue
  - GPIO 21 ---> 330 ohm resistor ---> VGA-Red
  - RP2040 GND ---> VGA-GND
 *
 * RESOURCES USED
 *  - PIO state machines 0, 1, and 2 on PIO instance 0
 *  - DMA channels (2, by claim mechanism)
 *  - 153.6 kBytes of RAM (for pixel color data)
 *
 */

// Include the VGA grahics library
#include "VGA/vga16_graphics_v3.h"
// Include standard libraries
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
// Include Pico libraries
#include "pico/stdlib.h"
#include "pico/divider.h"
#include "pico/multicore.h"
#include "pico/sync.h"
// Include hardware libraries
#include "hardware/pio.h"
#include "hardware/dma.h"
#include "hardware/clocks.h"
#include "hardware/pll.h"
// Include protothreads
#include "pt_cornell_rp2040_v1_4.h"

// === the fixed point macros ========================================
typedef signed int fix15 ;
#define multfix15(a,b) ((fix15)((((signed long long)(a))*((signed long long)(b)))>>15))
#define float2fix15(a) ((fix15)((a)*32768.0)) // 2^15
#define fix2float15(a) ((float)(a)/32768.0)
#define absfix15(a) abs(a)
#define int2fix15(a) ((fix15)(a << 15))
#define fix2int15(a) ((int)(a >> 15))
#define char2fix15(a) (fix15)(((fix15)(a)) << 15)
#define divfix(a,b) (fix15)(div_s64s64( (((signed long long)(a)) << 15), ((signed long long)(b))))

// Wall detection
#define hitBottom(b) (b>int2fix15(380))
#define hitTop(b) (b<int2fix15(100))
#define hitLeft(a) (a<int2fix15(100))
#define hitRight(a) (a>int2fix15(540))

// uS per frame at 60 fps, and the Pico's on-board LED
#define FRAME_PERIOD_US 16667
#define LED_PIN 25

// === rotary encoder ===
// These numbers mean GP2 and GP3, NOT physical header pins 2 and 3.
// Encoder A -> GP2 (pin 4), B -> GP3 (pin 5), COM (middle pin) -> GND.
#define ENCODER_A 2
#define ENCODER_B 3

// The number shown on the screen. volatile because the interrupt changes it.
volatile int encoder_count = 0 ;

// Last reading of the two switches, as (A << 1) | B.
// At rest both are open (HIGH, pulled up): 0b11 = 3.
volatile int encoder_state = 3 ;

// Quarter-steps moved since the knob was last at rest
volatile int encoder_steps = 0 ;

// Direction table, indexed by (old_state << 2) | new_state.
// Clockwise, A closes first:  11 -> 01 -> 00 -> 10 -> 11, each move +1.
// Counter-clockwise is the same backwards, each move -1.
// No change, or a jump of two (a missed edge), is 0.
const signed char encoder_table[16] = {
   0, -1, +1,  0,
  +1,  0,  0, -1,
  -1,  0,  0, +1,
   0, +1, -1,  0
} ;

// the color of the boid
char color = WHITE ;

// Boid on core 0
fix15 boid0_x ;
fix15 boid0_y ;
fix15 boid0_vx ;
fix15 boid0_vy ;

// Runs by itself every time encoder A or B changes (either direction)
void encoder_callback(uint gpio, uint32_t events)
{
  // Read A and B at the same instant
  uint32_t pins = gpio_get_all() ;
  int a = (pins >> ENCODER_A) & 1 ;
  int b = (pins >> ENCODER_B) & 1 ;
  int new_state = (a << 1) | b ;

  // Look up +1 / -1 / 0 for this move and add it up
  encoder_steps += encoder_table[(encoder_state << 2) | new_state] ;
  encoder_state = new_state ;

  // Back at rest (both switches open)? Then one whole click just finished.
  // A clean click adds up to +4 or -4. Contact rattle adds +1 then -1, which
  // cancels, so no debounce timer is needed.
  if (new_state == 3) {
    if (encoder_steps >= 2)       encoder_count++ ;   // clockwise
    else if (encoder_steps <= -2) encoder_count-- ;   // counter-clockwise
    encoder_steps = 0 ;
  }
}

// Create a boid
void spawnBoid(fix15* x, fix15* y, fix15* vx, fix15* vy, int direction)
{
  // Start in center of screen
  *x = int2fix15(320) ;
  *y = int2fix15(240) ;
  // Choose left or right
  if (direction) *vx = int2fix15(3) ;
  else *vx = int2fix15(-3) ;
  // Moving down
  *vy = int2fix15(1) ;
}

// Draw the boundaries
void drawArena() {
  drawVLine(100, 100, 280, WHITE) ;
  drawVLine(540, 100, 280, WHITE) ;
  drawHLine(100, 100, 440, WHITE) ;
  drawHLine(100, 380, 440, WHITE) ;
}

// Detect wallstrikes, update velocity and position
void wallsAndEdges(fix15* x, fix15* y, fix15* vx, fix15* vy)
{
  // Reverse direction if we've hit a wall
  if (hitTop(*y)) {
    *vy = (-*vy) ;
    *y  = (*y + int2fix15(5)) ;
  }
  if (hitBottom(*y)) {
    *vy = (-*vy) ;
    *y  = (*y - int2fix15(5)) ;
  }
  if (hitRight(*x)) {
    *vx = (-*vx) ;
    *x  = (*x - int2fix15(5)) ;
  }
  if (hitLeft(*x)) {
    *vx = (-*vx) ;
    *x  = (*x + int2fix15(5)) ;
  }

  // Update position using velocity
  *x = *x + *vx ;
  *y = *y + *vy ;
}

// Animation on core 0
static PT_THREAD (protothread_anim(struct pt *pt))
{
    // Mark beginning of thread
    PT_BEGIN(pt);

    // Space to build on-screen text in
    static char text[48] ;
    // Frame timing
    static uint32_t frame_start ;           // when this frame's work began (us)
    static int spare_us = FRAME_PERIOD_US ; // time left over last frame (us)

    // Spawn a boid
    spawnBoid(&boid0_x, &boid0_y, &boid0_vx, &boid0_vy, 0);

    while(1) {
      // Wait for the signal that the buffer's changed
      PT_YIELD_UNTIL(pt, draw_start_signal()) ;
      frame_start = time_us_32() ;
      // Clear the buffer
      clearLowFrame(0, BLACK);
      // update boid's position and velocity
      wallsAndEdges(&boid0_x, &boid0_y, &boid0_vx, &boid0_vy) ;
      // draw the boid at its new position
      fillCircle(fix2int15(boid0_x), fix2int15(boid0_y), 15, color);
      // draw the boundaries
      drawArena() ;
      // Show the encoder count in the top-left corner
      sprintf(text, "Encoder Count: %d", encoder_count) ;
      drawTextArial24(10, 10, text, WHITE, BLACK) ;

      // Spare time, under the count
      sprintf(text, "Spare time: %d us", spare_us) ;
      drawTextGLCD(10, 40, text, WHITE, BLACK) ;

      // How much of the 16.7 ms frame was left? LED on if we ran over.
      spare_us = FRAME_PERIOD_US - (int)(time_us_32() - frame_start) ;
      gpio_put(LED_PIN, spare_us < 0) ;
     // NEVER exit while
    } // END WHILE(1)
  PT_END(pt);
} // animation thread


// ========================================
// === main
// ========================================
// USE ONLY C-sdk library
int main(){
  set_sys_clock_khz(150000, true) ;
  // initialize stio
  stdio_init_all() ;

  // initialize VGA
  initVGA() ;

  // On-board LED: lights when a frame runs late
  gpio_init(LED_PIN) ;
  gpio_set_dir(LED_PIN, GPIO_OUT) ;

  // Rotary encoder: A and B are inputs with pull-ups
  // (not touching COM = HIGH, touching COM/GND = LOW)
  gpio_init(ENCODER_A) ;
  gpio_set_dir(ENCODER_A, GPIO_IN) ;
  gpio_pull_up(ENCODER_A) ;
  gpio_init(ENCODER_B) ;
  gpio_set_dir(ENCODER_B, GPIO_IN) ;
  gpio_pull_up(ENCODER_B) ;

  // Start from wherever the knob really is
  encoder_state = (gpio_get(ENCODER_A) << 1) | gpio_get(ENCODER_B) ;

  // Run encoder_callback on every change of A and of B (falling and rising)
  gpio_set_irq_enabled_with_callback(ENCODER_A, GPIO_IRQ_EDGE_FALL | GPIO_IRQ_EDGE_RISE, true, &encoder_callback) ;
  gpio_set_irq_enabled(ENCODER_B, GPIO_IRQ_EDGE_FALL | GPIO_IRQ_EDGE_RISE, true) ;

  // add threads
  pt_add_thread(protothread_anim);

  // start scheduler
  pt_schedule_start ;
}
