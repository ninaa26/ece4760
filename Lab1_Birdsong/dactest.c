/**
 * V. Hunter Adams
 * DDS of sine wave on MCP4822 DAC w/ ISR
 * 
 * Modified example code from Raspberry Pi
 * Copyright (c) 2020 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 *
   GPIO 5 (pin 7) Chip select
   GPIO 6 (pin 9) SCK/spi0_sclk
   GPIO 7 (pin 10) MOSI/spi0_tx
   GPIO 2 (pin 4) GPIO output for timing ISR
   3.3v (pin 36) -> VCC on DAC 
   GND (pin 3)  -> GND on DAC 
 */

#include <stdio.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/timer.h"
#include "hardware/irq.h"
#include "hardware/spi.h"

#include "hardware/gpio.h"
#include "hardware/adc.h"
#include <string.h>
#include "stdlib.h"

#include "hardware/sync.h"
#include "hardware/clocks.h"

#include "pt_cornell_rp2040_v1_4.h"



// Low-level alarm infrastructure we'll be using
#define ALARM_NUM 0
#define ALARM_IRQ timer_hardware_alarm_get_irq_num(timer_hw, ALARM_NUM)

//DDS parameters
#define two32 4294967296.0 // 2^32 
#define Fs 50000
#define DELAY 20 // 1/Fs (in microseconds)
// the DDS units:
volatile unsigned int phase_accum_main;
volatile unsigned int phase_incr_main;

// turn on/off the tone. Starts true: the spec says the system boots in
// tone generator mode, and key 0 is what silences it.
volatile bool tone = true;

// SPI data
uint16_t DAC_data ; // output value

//DAC parameters
// A-channel, 1x, active
#define DAC_config_chan_A 0b0011000000000000
// B-channel, 1x, active
#define DAC_config_chan_B 0b1011000000000000

//SPI configurations
#define PIN_MISO 4
#define PIN_CS   5
#define PIN_SCK  6
#define PIN_MOSI 7
#define SPI_PORT spi0

//GPIO for timing the ISR
#define ISR_GPIO 2

// ---- Fixed-point arithmetic, same macros as the course beep demo ----
// A fix15 is a 32-bit int holding 15 fractional bits, so 1.0 is stored as 32768.
// Used in the ISR because it is integer maths: no floating point in the
// interrupt, which is what keeps it inside the 20 us budget.
typedef signed int fix15 ;
#define multfix15(a,b) ((fix15)((((signed long long)(a))*((signed long long)(b)))>>15))
#define float2fix15(a) ((fix15)((a)*32768.0))
#define int2fix15(a)   ((fix15)(a << 15))
#define fix2int15(a)   ((int)(a >> 15))
#define divfix(a,b)    (fix15)((((signed long long)(a)) << 15) / (b))

// DDS sine table
#define sine_table_size 256
volatile fix15 sin_table[sine_table_size] ;

// ---- Amplitude envelope ----
// A note that starts and stops instantly is a step change in amplitude, which
// spreads energy across every frequency: you hear a click and the spectrogram
// shows a vertical smear. Ramping in and out removes both.
// Times are in ISR ticks, so 250 ticks at Fs = 50 kHz is 5 ms.
#define ATTACK_TIME 250
#define DECAY_TIME  250

fix15 max_amplitude = int2fix15(1) ;   // full scale
fix15 attack_inc ;                     // added per tick while ramping up
fix15 decay_inc ;                      // subtracted per tick while ramping down
volatile fix15 current_amplitude = 0 ; // lives in the ISR

// The checkpoint asks for 0 to ~10 kHz, but a raw ADC reading only runs 0-4095,
// so stretch it before it becomes a phase increment.
// Recording and playback BOTH call this, so the two can never drift apart.
#define MAX_FREQ_HZ 10000.0f
static inline unsigned int adc_to_phase_incr(unsigned int adc) {
    float freq = ((float)adc * MAX_FREQ_HZ) / 4095.0f ;
    return (unsigned int)(((double)freq * two32) / Fs) ;
}

// Keys are numbered 1-9, so index N holds key N and slot 0 is simply unused.
// Sizing these [9] would overflow on key 9.
#define NUM_RECORD_KEYS 10
#define MAX_SAMPLES 1000      // 1000 / 100 Hz = 10 seconds per key

uint16_t recordings[NUM_RECORD_KEYS][MAX_SAMPLES];
uint16_t record_length[NUM_RECORD_KEYS];

// A key "has a recording" when its stored length is greater than zero, so a
// separate recorded[] flag array is not needed - and cannot fall out of step
// with the data, the way a second copy of the truth eventually always does.

bool record_mode = false;
bool recording = false;
bool playing = false;

int record_key = -1;

// Alarm ISR
static void alarm_irq(void) {

    // Assert a GPIO when we enter the interrupt
    gpio_put(ISR_GPIO, 1) ;

    // Clear the alarm irq
    hw_clear_bits(&timer_hw->intr, 1u << ALARM_NUM);

    // Reset the alarm register
    timer_hw->alarm[ALARM_NUM] = timer_hw->timerawl + DELAY ;

    // ---- Envelope ----
    // Note on: ramp up to full scale and hold there (attack, then sustain).
    // Note off: ramp back down to zero (decay). At zero the sine is multiplied
    // away, the output sits at mid-scale 2048, and that is silence.
    if (tone) {
        if (current_amplitude < max_amplitude) {
            current_amplitude += attack_inc ;
            if (current_amplitude > max_amplitude) {
                current_amplitude = max_amplitude ;
            }
        }
    } else {
        if (current_amplitude > 0) {
            current_amplitude -= decay_inc ;
            if (current_amplitude < 0) {
                current_amplitude = 0 ;
            }
        }
    }

    // DDS phase and sine table lookup, scaled by the envelope
    phase_accum_main += phase_incr_main  ;
    DAC_data = (DAC_config_chan_B |
                ((fix2int15(multfix15(current_amplitude,
                                      sin_table[phase_accum_main>>24])) + 2048) & 0xffff)) ;

    // Perform an SPI transaction
    spi_write16_blocking(SPI_PORT, &DAC_data, 1) ;
    
    // De-assert the GPIO when we leave the interrupt
    gpio_put(ISR_GPIO, 0) ;

}

// ==========================================
// === protothreads globals
// ==========================================
// protothreads header

#define LED_PIN 25
#define ADC_PIN 26
#define ADC_MUX 0

// ==================================================
// === toggle25 thread 
// ==================================================
//  
static PT_THREAD (protothread_toggle25(struct pt *pt))
{
    PT_BEGIN(pt);

    static unsigned int adc_val ;

      while(1) {
        // Read the ADC
        adc_val = adc_read() ;

        // FIX 3 - the mode gate. protothread_playback also writes
        // phase_incr_main, at the same 100 Hz. Without this guard the two
        // threads fight and you hear the slider instead of the recording.
        if (!playing) {
            phase_incr_main = adc_to_phase_incr(adc_val) ;
        }
        // Print the value
        // printf("ADC value: %d\n", adc_val) ;

        // record 
        if (recording && record_key >= 0) {
            if (record_length[record_key] < MAX_SAMPLES) {
                recordings[record_key][record_length[record_key]] = adc_val;
                record_length[record_key]++;
            } else {
                recording = false; // stop recording if max samples reached
            }
        }
        // Yield
        PT_YIELD_usec(10000) ; // 10 ms -> this thread runs at 100 Hz
      } // END WHILE(1)
      // every thread ends with PT_END(pt);
      PT_END(pt);
} // end blink thread

static PT_THREAD (protothread_playback(struct pt *pt))
{
    PT_BEGIN(pt);

    static int sample;
    static int play_key;
    static unsigned int playback_adc;

    while(1) {

        if (playing && record_key >= 0) {

            // Latch the key now: record_key can change under us if another key
            // is pressed while this recording is still playing.
            play_key = record_key;

            for (sample = 0;
                 playing && sample < record_length[play_key];
                 sample++) {

                playback_adc = recordings[play_key][sample];

                phase_incr_main = adc_to_phase_incr(playback_adc);

                PT_YIELD_usec(10000);
            }

            playing = false;
        }

        PT_YIELD_usec(1000);
    }
      // every thread ends with PT_END(pt);
      PT_END(pt);
}


// Keypad pin configurations
#define BASE_KEYPAD_PIN 9
#define KEYROWS         4
#define NUMKEYS         12

unsigned int keycodes[NUMKEYS] = {      0x57, 0x6E, 0x5E, 0x3E, 0x6D,
                                        0x5D, 0x3D, 0x6B, 0x5B, 0x3B,
                                        0x67, 0x37} ;
unsigned int scancodes[KEYROWS] = {   0xE, 0xD, 0xB, 0x7} ;
unsigned int button = 0x70 ;


#define NOT_PRESSED       0
#define MAYBE_PRESSED     1
#define PRESSED           2
#define MAYBE_NOT_PRESSED 3

// This thread runs on core 0
static PT_THREAD (protothread_core_0(struct pt *pt))
{
    // Indicate thread beginning
    PT_BEGIN(pt) ;

    // Some variables
    static int i ;
    static uint32_t keypad ;
    static int state = NOT_PRESSED ;
    static int possible_key;

    while(1) {

        // Heartbeat. This thread is the only owner of the LED, so a steady
        // blink means the keypad thread is still being scheduled.
        gpio_put(LED_PIN, !gpio_get(LED_PIN)) ;

        // Scan the keypad!
        for (i=0; i<KEYROWS; i++) {
            // Drive one row LOW (each scancode has a single zero bit)
            gpio_put_masked((0xF << BASE_KEYPAD_PIN),
                            (scancodes[i] << BASE_KEYPAD_PIN)) ;
            // Small delay required
            sleep_us(1) ;
            // Read the keycode
            keypad = ((gpio_get_all() >> BASE_KEYPAD_PIN) & 0x7F) ;
            // Break if button(s) are pressed
            if ((~keypad) & button) break ;
        }
        // If we found a button . . .
        if ((~keypad) & button) {
            // Look for a valid keycode.
            for (i=0; i<NUMKEYS; i++) {
                if (keypad == keycodes[i]) break ;
            }
            // If we don't find one, report invalid keycode
            if (i==NUMKEYS) (i = -1) ;
        }
        // Otherwise, indicate invalid/non-pressed buttons
        else (i=-1) ;

        // Debouncing state machine

        switch (state) {
            case NOT_PRESSED:
                if (i >= 0) {
                    possible_key = i ;
                    state = MAYBE_PRESSED ;
                }
                break ;
            case MAYBE_PRESSED:
                if (i == possible_key) {
                    state = PRESSED ;

                    if (possible_key == 0){
                        // FIX 4 - key 0 toggles the tone generator on and off
                        tone = !tone ;
                        if (tone) {
                            printf("tone on\n") ;
                        } else {
                            printf("tone off\n") ;
                        }

                    } else if (possible_key == 10){
                        // The * key ARMS recording for the next key pressed.
                        // It erases nothing: recordings persist until that key
                        // is deliberately recorded over.
                        record_mode = !record_mode ;
                        recording = false;
                        playing = false;
                        if (record_mode) {
                            printf("record mode armed\n") ;
                        } else {
                            printf("record mode off\n") ;
                        }

                    } else if (possible_key > 0 && possible_key < 10){
                        record_key = possible_key;

                        if (record_mode) {
                            // Armed -> capture into this key, clearing only it
                            record_length[record_key] = 0;
                            recording = true;
                            playing = false;
                            tone = true;
                            printf("Recording key %d\n", possible_key);

                        } else if (record_length[record_key] > 0) {
                            // Not armed -> play it back. No mode required.
                            recording = false;
                            playing = true;
                            tone = true;
                            printf("Playing key %d\n", possible_key);

                        } else {
                            printf("key %d is empty\n", possible_key);
                        }
                    }
                } else {
                    state = NOT_PRESSED ;
                }
                break ;
            case PRESSED:
                if (i != possible_key) {
                    state = MAYBE_NOT_PRESSED ;
                }
                break ;
            case MAYBE_NOT_PRESSED:
                if (i == possible_key) {
                    state = PRESSED ;
                    //tone = false ;
                } else {
                    state = NOT_PRESSED ;
                    // if (recording){
                    //     recording = false;
                    //     printf("recording stopped\n") ;
                    // }

                    if (recording && possible_key == record_key){
                        recording   = false;
                        record_mode = false;   // one recording per * press
                        printf("key %d: %d samples\n",
                               record_key, record_length[record_key]);
                    }
                }
                break ;
        }

        PT_YIELD_usec(30000) ;
    }
    // Indicate thread end
    PT_END(pt) ;
}


int main() {
    // Overclock
    set_sys_clock_khz(150000, true) ;

    // Initialize stdio
    stdio_init_all();
    // printf("Hello, DAC!\n");

    // Initialize SPI channel (channel, baud rate set to 20MHz)
    spi_init(SPI_PORT, 20000000) ;
    // Format (channel, data bits per transfer, polarity, phase, order)
    spi_set_format(SPI_PORT, 16, 0, 0, 0);

    // Setup the ISR-timing GPIO
    gpio_init(ISR_GPIO) ;
    gpio_set_dir(ISR_GPIO, GPIO_OUT);
    gpio_put(ISR_GPIO, 0) ;

    // Setup the ADC
    adc_init() ;
    adc_gpio_init(ADC_PIN) ;
    adc_select_input(ADC_MUX) ;

    // set up LED gpio 25
    gpio_init(LED_PIN) ;  
    gpio_set_dir(LED_PIN, GPIO_OUT) ;
    gpio_put(LED_PIN, true);

    ////////////////// KEYPAD INITS ///////////////////////
    // Initialize the keypad GPIO's
    gpio_init_mask((0x7F << BASE_KEYPAD_PIN)) ;
    gpio_set_dir((BASE_KEYPAD_PIN+4), GPIO_IN);
    gpio_set_dir((BASE_KEYPAD_PIN+5), GPIO_IN);
    gpio_set_dir((BASE_KEYPAD_PIN+6), GPIO_IN);
    // Set row-pins to output
    gpio_set_dir_out_masked((0xF << BASE_KEYPAD_PIN)) ;
    // Idle all four row outputs HIGH
    gpio_put_masked((0xF << BASE_KEYPAD_PIN), (0xF << BASE_KEYPAD_PIN)) ;
    // Turn on pull-UP resistors for the column pins, so an unpressed column
    // reads 1 and a closed switch pulls it to 0
    gpio_pull_up((BASE_KEYPAD_PIN+4)) ;
    gpio_pull_up((BASE_KEYPAD_PIN+5)) ;
    gpio_pull_up((BASE_KEYPAD_PIN+6)) ;


    // Map SPI signals to GPIO ports
    gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);
    gpio_set_function(PIN_SCK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);
    gpio_set_function(PIN_CS, GPIO_FUNC_SPI) ;

    // === build the sine lookup table =======
    // scaled to produce values between 0 and 4096
    int ii;
    for (ii = 0; ii < sine_table_size; ii++){
         sin_table[ii] = float2fix15(2047*sin((float)ii*6.283/(float)sine_table_size));
    }

    // Envelope ramp rates: reach full scale in ATTACK_TIME ticks, and fall
    // back to zero in DECAY_TIME ticks.
    attack_inc = divfix(max_amplitude, int2fix15(ATTACK_TIME)) ;
    decay_inc  = divfix(max_amplitude, int2fix15(DECAY_TIME)) ;

    // Enable the interrupt for the alarm (we're using Alarm 0)
    hw_set_bits(&timer_hw->inte, 1u << ALARM_NUM) ;
    // Associate an interrupt handler with the ALARM_IRQ
    irq_set_exclusive_handler(ALARM_IRQ, alarm_irq) ;
    // Enable the alarm interrupt
    irq_set_enabled(ALARM_IRQ, true) ;
    // Write the lower 32 bits of the target time to the alarm register, arming it.
    timer_hw->alarm[ALARM_NUM] = timer_hw->timerawl + DELAY ;

      // === config threads ========================
    pt_add_thread(protothread_toggle25);

    pt_add_thread(protothread_playback);

    // Add core 0 threads
    pt_add_thread(protothread_core_0) ;

  
    // === initalize the scheduler ===============
    pt_schedule_start ;

}
