/**
 * ENVELOPE-FREE BUILD.
 *
 * Identical to ../Lab1_Birdsong/birdsong.c in every respect except that the
 * amplitude envelope is absent: notes switch on and off instantly instead of
 * ramping over 5 ms. It exists so the ISR execution time can be measured with
 * and without the envelope by flashing two binaries, rather than editing and
 * rebuilding between readings. That difference is the cost of one multfix15,
 * and it is the code-characterisation figure the lab report asks for.
 *
 * Expect this build to click audibly at every note boundary, and to show a
 * vertical smear at each boundary on a spectrogram. That is the thing the
 * envelope exists to remove.
 *
 * Not the code to hand in. See ../Lab1_Birdsong/.
 *
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
#include "northern_cardinal.h"



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

// DDS sine table. Plain ints here: with no envelope there is nothing to
// multiply the sine by, so the fix15 format is not needed.
#define sine_table_size 256
volatile int sin_table[sine_table_size] ;

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
// 2500 samples. At the 10 ms recording rate that is 25 seconds per key; at the
// 1 ms playback rate it is 2.5 seconds, which is what a full cardinal song
// needs (Cornell Lab: songs last 2 to 3 seconds).
#define MAX_SAMPLES 2500

// Silence between the notes of a composed phrase. Back-to-back recordings
// slur into one sound; real birdsong has gaps, and Merlin is matching a
// pattern that includes them. Try 0 and try 60000 and keep what convinces.
#define NOTE_GAP_US 50000

uint16_t recordings[NUM_RECORD_KEYS][MAX_SAMPLES];
uint16_t record_length[NUM_RECORD_KEYS];

// A key "has a recording" when its stored length is greater than zero, so a
// separate recorded[] flag array is not needed - and cannot fall out of step
// with the data, the way a second copy of the truth eventually always does.

bool record_mode = false;
bool recording = false;
bool playing = false;

int record_key = -1;

// ---- Compose mode ----
// The sequence stores KEY NUMBERS, not sound. All of the audio already lives
// in recordings[]; a whole phrase is just a short list of which keys to fire.
#define MAX_SEQUENCE 32

int  sequence[MAX_SEQUENCE] ;    // the key numbers, in order
int  sequence_length  = 0 ;      // how many slots are actually used
int  seq_index        = 0 ;      // which slot the replay is on
bool compose_mode     = false ;  // collecting key presses right now?
bool playing_sequence = false ;  // replaying a phrase right now?

// Alarm ISR
static void alarm_irq(void) {

    // Assert a GPIO when we enter the interrupt
    gpio_put(ISR_GPIO, 1) ;

    // Clear the alarm irq
    hw_clear_bits(&timer_hw->intr, 1u << ALARM_NUM);

    // Reset the alarm register
    timer_hw->alarm[ALARM_NUM] = timer_hw->timerawl + DELAY ;

    // No envelope: the note is either at full scale or silent, switched
    // instantly. The step in amplitude is what makes the click.
    if (tone) {
        phase_accum_main += phase_incr_main  ;
        DAC_data = (DAC_config_chan_B |
                    ((sin_table[phase_accum_main>>24] + 2048) & 0xffff)) ;
    } else {
        // Hold at mid-scale. Silent, but arriving there is still a full-scale
        // step from wherever the wave happened to be.
        DAC_data = (DAC_config_chan_B | 2048) ;
    }

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
    static uint64_t play_t0;      // when this recording started, in us

    while(1) {

        if (playing && record_key >= 0) {

            // Latch the key now: record_key can change under us if another key
            // is pressed while this recording is still playing.
            play_key = record_key;

            // Timebase for the whole recording. Every sample is scheduled
            // against THIS instant, not against the previous sample, so the
            // scheduler's overhead cannot accumulate.
            play_t0 = time_us_64();

            for (sample = 0;
                 playing && sample < record_length[play_key];
                 sample++) {

                playback_adc = recordings[play_key][sample];

                // A stored value of zero means silence. Driving `tone` from it
                // makes the ISR's 5 ms attack/decay ramp every syllable in and
                // out, instead of every note starting and stopping as a step.
                //
                // This matters for more than the clicks. Merlin identifies
                // birds with a convolutional network looking at a SPECTROGRAM
                // IMAGE, and a step in amplitude draws a vertical smear across
                // the whole frequency band at every note edge - a mark no real
                // bird makes. Ramped edges remove it, so the picture is just
                // the frequency contour, which is what the model was trained
                // on.
                tone = (playback_adc > 0) ;

                if (playback_adc > 0) {
                    phase_incr_main = adc_to_phase_incr(playback_adc);
                }

                // Wait until sample N is DUE, measured from the start of the
                // recording. PT_YIELD_usec(1000) would instead wait "at least
                // 1000 us from now", so the ISR's share of the CPU and the
                // other threads would be added on at every step and the song
                // would stretch by a few percent - every syllable and every
                // gap alike. Spacing and timing are most of what a bird-ID
                // model keys on, so the drift has to go somewhere it cannot
                // build up.
                PT_YIELD_UNTIL(pt,
                    time_us_64() >= play_t0 + (uint64_t)(sample + 1) * 1000ull) ;
            }

            // Only report a single key press. printf blocks for a few ms on
            // the UART, and while the absolute deadline below absorbs that,
            // there is no reason to put it between every note of a phrase.
            if (!playing_sequence) {
                printf("played key %d: %d samples in %llu ms\n",
                       play_key, sample,
                       (unsigned long long)((time_us_64() - play_t0) / 1000)) ;
            }

            playing = false;

            // If a phrase is running, start the next note instead of stopping.
            if (playing_sequence) {

                // Step past any sequence entries whose key holds no recording,
                // so one empty slot cannot stall the whole phrase. Without this
                // the thread would sit with playing false and playing_sequence
                // true, and nothing would ever advance it again.
                do {
                    seq_index++ ;
                } while (seq_index < sequence_length &&
                         record_length[sequence[seq_index]] == 0) ;

                if (seq_index < sequence_length) {
                    record_key = sequence[seq_index] ;
                    // Scheduled against the end of the note that just
                    // finished, for the same reason as the samples above.
                    PT_YIELD_UNTIL(pt,
                        time_us_64() >= play_t0
                                      + (uint64_t)sample * 1000ull
                                      + (uint64_t)NOTE_GAP_US) ;
                    playing = true ;
                } else {
                    playing_sequence = false ;     // phrase finished
                }
            }
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
                        // Key 0 toggles the tone generator, and doubles as the
                        // escape hatch: it returns every mode to a known state.
                        // The demo forbids resetting the board, so there has to
                        // be a way back from any state the machine can reach.
                        recording        = false ;
                        playing          = false ;
                        playing_sequence = false ;
                        compose_mode     = false ;
                        record_mode      = false ;

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

                    } else if (possible_key == 11){
                        // The # key. First press starts collecting a sequence;
                        // second press stops collecting and plays it back.
                        if (!compose_mode) {
                            compose_mode = true ;
                            sequence_length = 0 ;
                            printf("compose mode on\n") ;

                        } else {
                            compose_mode = false ;
                            printf("composed %d notes\n", sequence_length) ;

                            if (sequence_length > 0) {
                                seq_index = 0 ;
                                record_key = sequence[0] ;
                                playing_sequence = true ;
                                playing = true ;
                                tone = true ;
                            }
                        }

                    } else if (possible_key > 0 && possible_key < 10){
                        record_key = possible_key;

                        if (compose_mode) {
                            // Collecting a phrase: append the key number and
                            // make no sound. This has to be tested BEFORE the
                            // record and play branches, or pressing 3 while
                            // composing would play key 3 instead of adding it.
                            if (sequence_length < MAX_SEQUENCE) {
                                sequence[sequence_length] = possible_key ;
                                sequence_length++ ;
                                printf("added %d (%d notes)\n",
                                       possible_key, sequence_length) ;
                            }

                        } else if (record_mode) {
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
         sin_table[ii] = (int)(2047*sin((float)ii*6.283/(float)sine_table_size));
    }

    // Preload all nine keys with transcribed cardinal calls: single syllables
    // on 1-6, complete songs on 7-9. Recording over any
    // of them replaces the preset, so this changes nothing about how the lab's
    // record / playback / compose path behaves - it just means the keys are
    // not empty at power-on.
    {
        int n = cardinal_load_presets(&recordings[0][0], record_length,
                                      NUM_RECORD_KEYS, MAX_SAMPLES,
                                      MAX_FREQ_HZ) ;
        printf("loaded %d cardinal presets:\n", n) ;
        for (int i = 0 ; i < cardinal_call_count() ; i++) {
            printf("  key %d = %-28s %4d ms\n",
                   cardinal_call_key(i), cardinal_call_name(i),
                   cardinal_call_ms(i)) ;
        }
    }

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
