#include "northern_cardinal.h"
#include "cardinal_data.h"

/**
 * Load the transcribed contours into the recording slots.
 *
 * cardinal_data.h holds one array per key: the dominant frequency of a real
 * Macaulay Library recording, sampled once per millisecond and already
 * converted to the ADC value that reproduces that pitch. So loading is a
 * straight copy - no synthesis, no curve fitting, nothing to get wrong.
 *
 * Playback steps one stored sample per millisecond, so a 2200-sample track
 * plays for 2.2 seconds, the same duration as the window it was taken from.
 */

int cardinal_call_count(void)         { return CARDINAL_N_KEYS; }
const char *cardinal_call_name(int i) { return cardinal_labels[i]; }
int cardinal_call_key(int i)          { return i + 1; }      /* keys 1-9 */
int cardinal_call_ms(int i)           { (void)i; return CARDINAL_SAMPLES; }

int cardinal_load_presets(uint16_t *recordings, uint16_t *lengths,
                          int num_keys, int max_samples, float max_freq_hz)
{
    (void)max_freq_hz;   /* already applied when the data was generated */

    int loaded = 0;

    for (int i = 0; i < CARDINAL_N_KEYS; i++) {
        int key = i + 1;
        if (key >= num_keys) continue;

        int n = CARDINAL_SAMPLES;
        if (n > max_samples) n = max_samples;

        for (int k = 0; k < n; k++) {
            recordings[key * max_samples + k] = cardinal_tracks[i][k];
        }
        lengths[key] = (uint16_t)n;
        loaded++;
    }
    return loaded;
}
