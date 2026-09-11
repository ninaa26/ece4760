/**
 * northern_cardinal.h — synthesised Northern Cardinal calls
 *
 * Preloads all nine recording slots with frequency contours shaped like a
 * cardinal's vocabulary. Keys 1-6 are single syllables; keys 7-9 are complete
 * multi-syllable songs with the silences built in.
 *
 * This is an ADDITION, not a replacement. Recording over any key works exactly
 * as before and overwrites the preset; the lab's required record / playback /
 * compose path is untouched. At a demo, say which keys are presets and which
 * you recorded - a preset is not a recording, and the checkoff asks you to
 * record a sequence a TA invents on the spot.
 *
 * SOURCES
 *   V. Hunter Adams, "Synthesizing birdsong via Direct Digital Synthesis"
 *     https://vanhunteradams.com/Pico/Birds/Birdsong_synthesis.html
 *     swoop: 130 ms, y = -260*sin(-pi*x/5200) + 1740, i.e. 1740 -> 2000 -> 1740
 *     chirp: ~130 ms, "moves rapidly from low frequency to high frequency"
 *
 *   Birds of the World, "Northern Cardinal - Sounds and Vocal Behavior"
 *     https://birdsoftheworld.org/bow/species/norcar/cur/sounds
 *     8-10 song types built from 8-21 syllable types; pure-toned whistles,
 *     fundamentals roughly 1-8 kHz; syllables separated by silences under 1 s.
 *     Two measured song types from south-central Wisconsin:
 *       type A: "what" ~0.1 s ascending 2 -> 4 kHz,
 *               "cheer" ~0.6 s descending 6 -> 2 kHz
 *       type B: "what" ~0.5 s ascending 2 -> 4 kHz,
 *               "cheer" ~0.4 s descending 2.5 -> 1 kHz
 *
 *   Cornell Lab, All About Birds - Northern Cardinal Sounds
 *     https://www.allaboutbirds.org/guide/Northern_Cardinal/sounds
 *     a string of clear down-slurred or two-parted whistles, often speeding up
 *     and ending in a trill; songs last 2 to 3 seconds; a phrase is usually
 *     repeated 2-3 times.
 *
 *   ECE 4760 Lab 1 handout, Fig. 2 spectrogram: sweeps about 2 kHz to 7 kHz.
 *
 * The swoop and the two Wisconsin song types use the published figures. The
 * rest are shaped to the same ranges and are meant to be TUNED BY EAR against
 * the Merlin app - a starting point, not measured data.
 */

#ifndef NORTHERN_CARDINAL_H
#define NORTHERN_CARDINAL_H

#include <stdint.h>

// One piece of a call. The pitch runs f_start -> f_mid -> f_end, eased with a
// raised cosine at each half so it never turns a corner abruptly.
// All three zero means SILENCE: a phase increment of zero freezes the
// oscillator, which produces no sound.
typedef struct {
    int   ms;
    float f_start;
    float f_mid;
    float f_end;
} cardinal_segment_t;

// A call is a list of segments loaded onto one key.
typedef struct {
    int                       key;
    const char               *name;
    const cardinal_segment_t *seg;
    int                       n_seg;
} cardinal_call_t;

int         cardinal_call_count(void);
const char *cardinal_call_name(int i);
int         cardinal_call_key(int i);
int         cardinal_call_ms(int i);      // total duration in milliseconds

/**
 * Fill the recording slots with the synthesised calls.
 *
 * recordings   flat pointer to the [keys][max_samples] array
 * lengths      the per-key length array
 * num_keys     first dimension of recordings
 * max_samples  second dimension of recordings
 * max_freq_hz  whatever MAX_FREQ_HZ is in your code, so the stored ADC values
 *              map back to the right frequencies on playback
 *
 * Returns the number of calls loaded. A call longer than max_samples is
 * truncated rather than skipped.
 */
int cardinal_load_presets(uint16_t *recordings, uint16_t *lengths,
                          int num_keys, int max_samples, float max_freq_hz);

#endif
