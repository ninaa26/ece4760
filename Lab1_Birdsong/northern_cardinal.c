#include "northern_cardinal.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define SIL(ms) { (ms), 0.f, 0.f, 0.f }      // silence

// ---------------------------------------------------------------------------
// Building blocks. The figures in square brackets are the published ones.
// ---------------------------------------------------------------------------

// [Hunter Adams] 130 ms, 1740 -> 2000 -> 1740
static const cardinal_segment_t seg_swoop[] = {
    { 130, 1740.f, 2000.f, 1740.f },
};

// [Wisconsin type A] "what": ~0.1 s ascending 2 -> 4 kHz
static const cardinal_segment_t seg_what_fast[] = {
    { 100, 2000.f, 3000.f, 4000.f },
};

// [Wisconsin type A] "cheer": ~0.6 s descending 6 -> 2 kHz
static const cardinal_segment_t seg_cheer_high[] = {
    { 600, 6000.f, 4000.f, 2000.f },
};

// [Wisconsin type B] "what": ~0.5 s ascending 2 -> 4 kHz
static const cardinal_segment_t seg_what_slow[] = {
    { 500, 2000.f, 3000.f, 4000.f },
};

// [Wisconsin type B] "cheer": ~0.4 s descending 2.5 -> 1 kHz
static const cardinal_segment_t seg_cheer_low[] = {
    { 400, 2500.f, 1750.f, 1000.f },
};

// Sharp "chip" contact note. Shaped, not measured.
static const cardinal_segment_t seg_chip[] = {
    {  40, 5000.f, 4000.f, 3000.f },
};

// ---------------------------------------------------------------------------
// Complete songs. Cornell Lab: a string of down-slurred or two-parted
// whistles, a phrase repeated 2-3 times, whole song 2-3 seconds.
// ---------------------------------------------------------------------------

// "what cheer, cheer, cheer" - Wisconsin type A. 2140 ms.
static const cardinal_segment_t seg_song_a[] = {
    { 100, 2000.f, 3000.f, 4000.f },   // what
    SIL(80),
    { 600, 6000.f, 4000.f, 2000.f },   // cheer
    SIL(80),
    { 600, 6000.f, 4000.f, 2000.f },   // cheer
    SIL(80),
    { 600, 6000.f, 4000.f, 2000.f },   // cheer
};

// "what cheer, cheer" - Wisconsin type B, lower and slower. 1460 ms.
static const cardinal_segment_t seg_song_b[] = {
    { 500, 2000.f, 3000.f, 4000.f },   // what
    SIL(80),
    { 400, 2500.f, 1750.f, 1000.f },   // cheer
    SIL(80),
    { 400, 2500.f, 1750.f, 1000.f },   // cheer
};

// "birdy birdy birdy" - two-parted whistles, speeding up. 1270 ms.
static const cardinal_segment_t seg_song_birdy[] = {
    { 120, 2000.f, 3000.f, 4000.f },   // bir-
    { 120, 4000.f, 3000.f, 2000.f },   // -dy
    SIL(140),
    { 120, 2000.f, 3000.f, 4000.f },
    { 120, 4000.f, 3000.f, 2000.f },
    SIL(100),
    { 120, 2000.f, 3000.f, 4000.f },
    { 120, 4000.f, 3000.f, 2000.f },
    SIL(70),
    { 120, 2000.f, 3000.f, 4000.f },
    { 120, 4000.f, 3000.f, 2000.f },
};

#define CALL(k, nm, arr) { (k), (nm), (arr), (int)(sizeof(arr)/sizeof((arr)[0])) }

static const cardinal_call_t calls[] = {
    CALL(1, "swoop",             seg_swoop      ),
    CALL(2, "what (fast)",       seg_what_fast  ),
    CALL(3, "cheer (high fall)", seg_cheer_high ),
    CALL(4, "what (slow)",       seg_what_slow  ),
    CALL(5, "cheer (low fall)",  seg_cheer_low  ),
    CALL(6, "chip",              seg_chip       ),
    CALL(7, "SONG what-cheer-cheer-cheer", seg_song_a     ),
    CALL(8, "SONG what-cheer-cheer",       seg_song_b     ),
    CALL(9, "SONG birdy-birdy-birdy",      seg_song_birdy ),
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
