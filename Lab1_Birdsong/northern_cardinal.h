/**
 * northern_cardinal.h — real Northern Cardinal recordings as presets
 *
 * Preloads all nine recording slots with the pitch of a real cardinal: nine
 * recordings from the Cornell Lab's All About Birds / Macaulay Library page
 * (Common subspecies) - songs on keys 1-4, a duet on 5, calls on 6-9. For
 * each, the dominant frequency of the densest 2.2 s was tracked once per
 * millisecond and stored as the ADC value that reproduces it (cardinal_data.h).
 * Zero means the bird was silent. Labels with recordist and year are in
 * cardinal_labels[].
 *
 * This is an ADDITION, not a replacement. Recording over any key works exactly
 * as before and overwrites the preset; the lab's required record / playback /
 * compose path is untouched. At a demo, say which keys are presets and which
 * you recorded - a preset is not a recording, and the checkoff asks you to
 * record a sequence a TA invents on the spot.
 */

#ifndef NORTHERN_CARDINAL_H
#define NORTHERN_CARDINAL_H

#include <stdint.h>

int         cardinal_call_count(void);
const char *cardinal_call_name(int i);
int         cardinal_call_key(int i);
int         cardinal_call_ms(int i);      // total duration in milliseconds

/**
 * Fill the recording slots with the transcribed recordings.
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
