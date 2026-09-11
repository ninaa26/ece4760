/**
 * northern_cardinal.h — synthesised Northern Cardinal syllables
 *
 * Preloads the recording slots with frequency contours shaped like a cardinal's
 * song, so keys 1-6 hold bird syllables at power-on instead of being empty.
 *
 * This is an ADDITION, not a replacement. Recording over any of these keys
 * works exactly as before and overwrites the preset; the lab's required
 * record / playback / compose path is untouched. At a demo, say which keys are
 * presets and which you recorded - a preset is not a recording, and the
 * checkoff asks you to record a sequence a TA invents on the spot.
 *
 * SOURCES
 *   V. Hunter Adams, "Synthesizing birdsong via Direct Digital Synthesis"
 *     https://vanhunteradams.com/Pico/Birds/Birdsong_synthesis.html
 *     - the song decomposes into a swoop, a chirp, and silence between them
 *     - swoop: 130 ms, y = -260*sin(-pi*x/5200) + 1740
 *       i.e. 1740 Hz -> 2000 Hz -> 1740 Hz
 *     - chirp: ~130 ms, "moves rapidly from low frequency to high frequency"
 *     - amplitude ramped up and down at the edges of each element
 *   Birds of the World, "Northern Cardinal - Sounds and Vocal Behavior"
 *     https://birdsoftheworld.org/bow/species/norcar/cur/sounds
 *     - pure-toned whistles, fundamentals roughly 1-8 kHz
 *     - syllables separated by silences under 1 second, sung in a set order
 *   ECE 4760 Lab 1 handout, Fig. 2 spectrogram: sweeps about 2 kHz to 7 kHz
 *
 * The swoop below is Hunter's equation exactly. The others are shaped to the
 * ranges above and are meant to be TUNED BY EAR against the Merlin app - treat
 * them as a starting point, not as measured data.
 */

#ifndef NORTHERN_CARDINAL_H
#define NORTHERN_CARDINAL_H

#include <stdint.h>

// One syllable: a frequency contour that starts at f_start, passes through
// f_mid at the halfway point, and ends at f_end. Both halves are eased with a
// raised cosine so the pitch never changes direction abruptly.
typedef struct {
    int         key;        // which keypad key to load it onto (1-9)
    int         ms;         // duration in milliseconds
    float       f_start;    // Hz
    float       f_mid;      // Hz at the midpoint
    float       f_end;      // Hz
    const char *name;
} cardinal_syllable_t;

// How many syllables the table holds.
int cardinal_syllable_count(void);

// Name of syllable i, for printing at boot.
const char *cardinal_syllable_name(int i);

// Which key syllable i is loaded onto.
int cardinal_syllable_key(int i);

/**
 * Fill the recording slots with the synthesised syllables.
 *
 * recordings   flat pointer to the [keys][max_samples] array
 * lengths      the per-key length array
 * num_keys     first dimension of recordings
 * max_samples  second dimension of recordings
 * max_freq_hz  the value MAX_FREQ_HZ has in your code, so the stored ADC
 *              values map back to the right frequencies on playback
 *
 * Returns the number of syllables actually loaded.
 */
int cardinal_load_presets(uint16_t *recordings, uint16_t *lengths,
                          int num_keys, int max_samples, float max_freq_hz);

#endif
