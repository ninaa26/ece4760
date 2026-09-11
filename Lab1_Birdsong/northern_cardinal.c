#include "northern_cardinal.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define SIL(ms) { (ms), 0.f, 0.f, 0.f }      // silence

// ---------------------------------------------------------------------------
// MEASURED from the reference recording - nothing below is constructed.
//
// Source: Macaulay Library asset 130905, the recording the lab handout links
// to. Downloaded, decoded, and analysed by tracking the dominant frequency
// through a spectrogram across all 414 seconds. 386 syllables were found and
// grouped by shape; each entry below is the MEDIAN contour of its group.
//
//   RISE        117 ms   2250 -> 2372 -> 2634 -> 2934 -> 3844 -> 4594 Hz
//   RISE short   96 ms   2250 -> 2400 -> 2634 -> 2934 -> 3797 -> 4359
//   RISE long   128 ms   2203 -> 2372 -> 2634 -> 2939 -> 3872 -> 4664
//   FALL        133 ms   4781 -> 4134 -> 3722 -> 3309 -> 2709 -> 2484
//   FALL short  101 ms   4406 -> 4031 -> 3750 -> 3431 -> 3188 -> 2906
//   FALL long   144 ms   4992 -> 4266 -> 3741 -> 3291 -> 2672 -> 2438
//   ARCH         64 ms   2391 -> 2316 -> 2212 -> 2128 -> 2053 -> 1969
//
//   gaps between syllables: median 283 ms (quartiles 160 and 304)
//   2nd harmonic measured at 0.3 % of the fundamental - an almost perfectly
//   pure whistle, which is why a plain sine table is the right choice here
//
// Note how far this is from a guess: the syllables mostly RISE, they last
// about 100 ms rather than 600, and they top out near 4.6 kHz, not 6.5.
// ---------------------------------------------------------------------------

// SONG rise x6 - 2117 ms. Every syllable is a measured median contour.
static const cardinal_segment_t seg_song1[] = {
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
};

// SONG fall x6 - 2213 ms. Every syllable is a measured median contour.
static const cardinal_segment_t seg_song2[] = {
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
    SIL(283),
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
    SIL(283),
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
    SIL(283),
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
    SIL(283),
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
    SIL(283),
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
};

// SONG rise fast x8 - 1888 ms. Every syllable is a measured median contour.
static const cardinal_segment_t seg_song3[] = {
    {   38,  2250.0f,  2400.0f,  2634.0f },
    {   38,  2634.0f,  2934.0f,  3797.0f },
    {   20,  3797.0f,  4078.0f,  4359.0f },
    SIL(160),
    {   38,  2250.0f,  2400.0f,  2634.0f },
    {   38,  2634.0f,  2934.0f,  3797.0f },
    {   20,  3797.0f,  4078.0f,  4359.0f },
    SIL(160),
    {   38,  2250.0f,  2400.0f,  2634.0f },
    {   38,  2634.0f,  2934.0f,  3797.0f },
    {   20,  3797.0f,  4078.0f,  4359.0f },
    SIL(160),
    {   38,  2250.0f,  2400.0f,  2634.0f },
    {   38,  2634.0f,  2934.0f,  3797.0f },
    {   20,  3797.0f,  4078.0f,  4359.0f },
    SIL(160),
    {   38,  2250.0f,  2400.0f,  2634.0f },
    {   38,  2634.0f,  2934.0f,  3797.0f },
    {   20,  3797.0f,  4078.0f,  4359.0f },
    SIL(160),
    {   38,  2250.0f,  2400.0f,  2634.0f },
    {   38,  2634.0f,  2934.0f,  3797.0f },
    {   20,  3797.0f,  4078.0f,  4359.0f },
    SIL(160),
    {   38,  2250.0f,  2400.0f,  2634.0f },
    {   38,  2634.0f,  2934.0f,  3797.0f },
    {   20,  3797.0f,  4078.0f,  4359.0f },
    SIL(160),
    {   38,  2250.0f,  2400.0f,  2634.0f },
    {   38,  2634.0f,  2934.0f,  3797.0f },
    {   20,  3797.0f,  4078.0f,  4359.0f },
};

// SONG fall long x5 - 1936 ms. Every syllable is a measured median contour.
static const cardinal_segment_t seg_song4[] = {
    {   58,  4992.0f,  4266.0f,  3741.0f },
    {   58,  3741.0f,  3291.0f,  2672.0f },
    {   28,  2672.0f,  2555.0f,  2438.0f },
    SIL(304),
    {   58,  4992.0f,  4266.0f,  3741.0f },
    {   58,  3741.0f,  3291.0f,  2672.0f },
    {   28,  2672.0f,  2555.0f,  2438.0f },
    SIL(304),
    {   58,  4992.0f,  4266.0f,  3741.0f },
    {   58,  3741.0f,  3291.0f,  2672.0f },
    {   28,  2672.0f,  2555.0f,  2438.0f },
    SIL(304),
    {   58,  4992.0f,  4266.0f,  3741.0f },
    {   58,  3741.0f,  3291.0f,  2672.0f },
    {   28,  2672.0f,  2555.0f,  2438.0f },
    SIL(304),
    {   58,  4992.0f,  4266.0f,  3741.0f },
    {   58,  3741.0f,  3291.0f,  2672.0f },
    {   28,  2672.0f,  2555.0f,  2438.0f },
};

// SONG arch x8 - 1632 ms. Every syllable is a measured median contour.
static const cardinal_segment_t seg_song5[] = {
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(160),
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(160),
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(160),
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(160),
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(160),
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(160),
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(160),
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
};

// SONG rise-fall pairs - 1919 ms. Every syllable is a measured median contour.
static const cardinal_segment_t seg_song6[] = {
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
    SIL(160),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
    SIL(160),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
};

// SONG fall x3 then rise x3 - 2165 ms. Every syllable is a measured median contour.
static const cardinal_segment_t seg_song7[] = {
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
    SIL(283),
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
    SIL(283),
    {   53,  4781.0f,  4134.0f,  3722.0f },
    {   53,  3722.0f,  3309.0f,  2709.0f },
    {   27,  2709.0f,  2596.5f,  2484.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
};

// SONG rise accelerating - 1745 ms. Every syllable is a measured median contour.
static const cardinal_segment_t seg_song8[] = {
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(240),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(200),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(160),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(160),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
};

// SONG arch x4 then rise x3 - 1936 ms. Every syllable is a measured median contour.
static const cardinal_segment_t seg_song9[] = {
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(160),
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(160),
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(160),
    {   26,  2391.0f,  2316.0f,  2212.0f },
    {   26,  2212.0f,  2128.0f,  2053.0f },
    {   12,  2053.0f,  2011.0f,  1969.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
    SIL(283),
    {   47,  2250.0f,  2372.0f,  2634.0f },
    {   47,  2634.0f,  2934.0f,  3844.0f },
    {   23,  3844.0f,  4219.0f,  4594.0f },
};

#define CALL(k, nm, arr) { (k), (nm), (arr), (int)(sizeof(arr)/sizeof((arr)[0])) }

static const cardinal_call_t calls[] = {
    CALL(1, "SONG rise x6", seg_song1),
    CALL(2, "SONG fall x6", seg_song2),
    CALL(3, "SONG rise fast x8", seg_song3),
    CALL(4, "SONG fall long x5", seg_song4),
    CALL(5, "SONG arch x8", seg_song5),
    CALL(6, "SONG rise-fall pairs", seg_song6),
    CALL(7, "SONG fall x3 then rise x3", seg_song7),
    CALL(8, "SONG rise accelerating", seg_song8),
    CALL(9, "SONG arch x4 then rise x3", seg_song9),
};

#define N_CALLS ((int)(sizeof(calls) / sizeof(calls[0])))

int         cardinal_call_count(void)     { return N_CALLS; }
const char *cardinal_call_name(int i)     { return calls[i].name; }
int         cardinal_call_key(int i)      { return calls[i].key; }

int cardinal_call_ms(int i)
{
    int total = 0;
    for (int k = 0; k < calls[i].n_seg; k++) total += calls[i].seg[k].ms;
    return total;
}

// Pitch at fraction t (0..1) through one segment: two raised-cosine eases,
// start -> mid then mid -> end, so the contour is smooth at both ends and at
// the join between them.
static float segment_freq(const cardinal_segment_t *s, float t)
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

    for (int c = 0; c < N_CALLS; c++) {
        const cardinal_call_t *call = &calls[c];
        if (call->key < 0 || call->key >= num_keys) continue;

        int written = 0;

        for (int g = 0; g < call->n_seg && written < max_samples; g++) {
            const cardinal_segment_t *s = &call->seg[g];

            int n = s->ms;                       // one sample per millisecond
            if (n < 1) continue;
            if (written + n > max_samples) n = max_samples - written;

            int silent = (s->f_start == 0.f && s->f_mid == 0.f && s->f_end == 0.f);

            for (int k = 0; k < n; k++) {
                int adc;

                if (silent) {
                    // Zero increment freezes the oscillator, so nothing moves
                    // and nothing is heard.
                    adc = 0;
                } else {
                    float t = (n > 1) ? (float)k / (float)(n - 1) : 0.f;
                    float f = segment_freq(s, t);

                    // Store what the ADC would have read for this pitch, so the
                    // existing adc_to_phase_incr() on playback turns it back
                    // into the same frequency. The inverse of that mapping.
                    adc = (int)((f * 4095.0f / max_freq_hz) + 0.5f);
                    if (adc < 0)    adc = 0;
                    if (adc > 4095) adc = 4095;
                }

                recordings[call->key * max_samples + written + k] = (uint16_t)adc;
            }

            written += n;
        }

        lengths[call->key] = (uint16_t)written;
        loaded++;
    }

    return loaded;
}
