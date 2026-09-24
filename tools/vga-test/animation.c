// VGA test: four full-height colour stripes, and the on-board LED blinks
// once a second so you can see the program is running. Not lab code.
//
//   ./flash.sh tools/vga-test
//
// LED blinking once a second = the Pico is producing 60 frames per second
// (the LED flips every 30 frames). If the LED blinks but the monitor stays
// black, the problem is after the Pico's pins: adapter, cable or monitor.
// On 2026-09-23 the first monitor tried stayed black; a second one worked.
#include "VGA/vga16_graphics_v3.h"
#include "pico/stdlib.h"
#include "hardware/clocks.h"

int main() {
  set_sys_clock_khz(150000, true) ;
  stdio_init_all() ;
  initVGA() ;
  gpio_init(25) ;
  gpio_set_dir(25, GPIO_OUT) ;

  int frame = 0 ;
  while (1) {
    while (!draw_start_signal()) ;          // wait for the next frame
    fillRect(0,   0, 160, 480, RED) ;
    fillRect(160, 0, 160, 480, GREEN) ;
    fillRect(320, 0, 160, 480, BLUE) ;
    fillRect(480, 0, 160, 480, WHITE) ;
    setTextColor2(WHITE, BLACK) ;
    setTextSize(3) ;
    setCursor(200, 220) ;
    writeString("VGA TEST") ;
    frame++ ;
    gpio_put(25, (frame / 30) & 1) ;       // on half a second, off half a second
  }
}
