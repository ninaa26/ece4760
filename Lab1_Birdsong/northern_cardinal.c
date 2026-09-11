#include "northern_cardinal.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// ---- The syllable table -------------------------------------------------
//
// Durations and frequencies are chosen to sit inside the cardinal's real
// range. The swoop is Hunter's published equation; the rest are shaped to
// match the 2-7 kHz sweeps in the lab handout's spectrogram and should be
// adjusted by ear once you can hear them.
//
// Playback steps one stored sample per millisecond, so a syllable of N ms is
// stored as N samples and plays for N ms.

static const cardinal_syllable_t syllables[] = {
    // key  ms   start    mid     end     name
    {  1,  130,  1740.f, 2000.f, 1740.f, "swoop"        },  // Hunter's equation
    {  2,  130,  2000.f, 4200.f, 7000.f, "chirp up"     },  // the rapid rise
    {  3,  130,  7000.f, 4200.f, 2000.f, "cheer down"   },  // the classic downslur
    {  4,   70,  2500.f, 4000.f, 5500.f, "short rise"   },
    {  5,  220,  6500.f, 4000.f, 1800.f, "long fall"    },
    {  6,   45,  3000.f, 3400.f, 3000.f, "chip"         },
};

#define N_SYLLABLES ((int)(sizeof(syllables) / sizeof(syllables[0])))

int cardinal_syllable_count(void)        { return N_SYLLABLES; }
const char *cardinal_syllable_name(int i){ return syllables[i].name; }
int cardinal_syllable_key(int i)         { return syllables[i].key; }

// Frequency at fraction t (0..1) through a syllable. Two raised-cosine eases,
// start -> mid over the first half and mid -> end over the second, so the
// contour is smooth at both ends and at the join.
static float syllable_freq(const cardinal_syllable_t *s, float t)
{
    float u, ease;

    if (t < 0.5f) {
        u    = t * 2.0f;
        ease = 0.5f - 0.5f * cosf((float)M_PI * u);
        return s->f_start + (s->f_mid - s->f_start) * ease;
    } else {
        u    = (t - 0.5f) * 2.0f;
        ease = 0.5f - 0.5f * cosf((float)M_PI * u);
        return s->f_mid + (s->f_end - s->f_mid) * ease;
    }
}

int cardinal_load_presets(uint16_t *recordings, uint16_t *lengths,
                          int num_keys, int max_samples, float max_freq_hz)
{
    int loaded = 0;

    for (int i = 0; i < N_SYLLABLES; i++) {
        const cardinal_syllable_t *s = &syllables[i];

        if (s->key < 0 || s->key >= num_keys) continue;

        int n = s->ms;                       // one sample per millisecond
        if (n > max_samples) n = max_samples;
        if (n < 2) continue;

        for (int k = 0; k < n; k++) {
            float t = (float)k / (float)(n - 1);
            float f = syllable_freq(s, t);

            // Store what the ADC would have read for this pitch, so playback's
            // existing adc_to_phase_incr() turns it back into the same
            // frequency. This is the inverse of that mapping.
            int adc = (int)((f * 4095.0f / max_freq_hz) + 0.5f);
            if (adc < 0)    adc = 0;
            if (adc > 4095) adc = 4095;

            recordings[s->key * max_samples + k] = (uint16_t)adc;
        }

        lengths[s->key] = (uint16_t)n;
        loaded++;
    }

    return loaded;
}
