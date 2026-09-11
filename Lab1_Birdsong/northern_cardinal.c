#include "northern_cardinal.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define SIL(ms) { (ms), 0.f, 0.f, 0.f }      // silence

// ---------------------------------------------------------------------------
// Nine complete songs. Cardinals have 8-10 song types built from 8-21 syllable
// types, each song lasting 2-3 seconds, with a phrase usually repeated 2-3
// times (Cornell Lab / Birds of the World).
//
// Keys 1 and 2 use the measured Wisconsin figures. The other seven are built
// from the qualitative descriptions - down-slurred whistles, two-parted
// whistles, series that speed up and end in a trill - and are the ones to tune
// by ear against Merlin.
// ---------------------------------------------------------------------------

// SONG what-cheer-cheer-cheer - Wisconsin type A, measured. 2140 ms.
static const cardinal_segment_t seg_song_a[] = {
    {  100,  2000.0f,  3000.0f,  4000.0f },
    SIL(80),
    {  600,  6000.0f,  4000.0f,  2000.0f },
    SIL(80),
    {  600,  6000.0f,  4000.0f,  2000.0f },
    SIL(80),
    {  600,  6000.0f,  4000.0f,  2000.0f },
};

// SONG what-cheer-cheer (low) - Wisconsin type B, measured. 1460 ms.
static const cardinal_segment_t seg_song_b[] = {
    {  500,  2000.0f,  3000.0f,  4000.0f },
    SIL(80),
    {  400,  2500.0f,  1750.0f,  1000.0f },
    SIL(80),
    {  400,  2500.0f,  1750.0f,  1000.0f },
};

// SONG cheer-cheer-cheer - down-slurred whistles. 1980 ms.
static const cardinal_segment_t seg_song_cheer[] = {
    {  600,  6000.0f,  4000.0f,  2000.0f },
    SIL(90),
    {  600,  6000.0f,  4000.0f,  2000.0f },
    SIL(90),
    {  600,  6000.0f,  4000.0f,  2000.0f },
};

// SONG birdy-birdy-birdy - two-parted, speeding up. 1630 ms.
static const cardinal_segment_t seg_song_birdy[] = {
    {  120,  2000.0f,  3000.0f,  4000.0f },
    {  120,  4000.0f,  3000.0f,  2000.0f },
    SIL(150),
    {  120,  2000.0f,  3000.0f,  4000.0f },
    {  120,  4000.0f,  3000.0f,  2000.0f },
    SIL(120),
    {  120,  2000.0f,  3000.0f,  4000.0f },
    {  120,  4000.0f,  3000.0f,  2000.0f },
    SIL(90),
    {  120,  2000.0f,  3000.0f,  4000.0f },
    {  120,  4000.0f,  3000.0f,  2000.0f },
    SIL(70),
    {  120,  2000.0f,  3000.0f,  4000.0f },
    {  120,  4000.0f,  3000.0f,  2000.0f },
};

// SONG purty-purty-purty - slower two-parted. 1380 ms.
static const cardinal_segment_t seg_song_purty[] = {
    {  180,  2200.0f,  3200.0f,  4200.0f },
    {  180,  4200.0f,  3000.0f,  1800.0f },
    SIL(150),
    {  180,  2200.0f,  3200.0f,  4200.0f },
    {  180,  4200.0f,  3000.0f,  1800.0f },
    SIL(150),
    {  180,  2200.0f,  3200.0f,  4200.0f },
    {  180,  4200.0f,  3000.0f,  1800.0f },
};

// SONG what-cheer + trill - ends in a trill. 2300 ms.
static const cardinal_segment_t seg_song_trill[] = {
    {  100,  2000.0f,  3000.0f,  4000.0f },
    SIL(80),
    {  600,  6000.0f,  4000.0f,  2000.0f },
    SIL(80),
    {  100,  2000.0f,  3000.0f,  4000.0f },
    SIL(80),
    {  600,  6000.0f,  4000.0f,  2000.0f },
    SIL(100),
    {   60,  3200.0f,  4200.0f,  3200.0f },
    SIL(40),
    {   60,  3200.0f,  4200.0f,  3200.0f },
    SIL(40),
    {   60,  3200.0f,  4200.0f,  3200.0f },
    SIL(40),
    {   60,  3200.0f,  4200.0f,  3200.0f },
    SIL(40),
    {   60,  3200.0f,  4200.0f,  3200.0f },
    SIL(40),
    {   60,  3200.0f,  4200.0f,  3200.0f },
};

// SONG rising series - ascending whistles. 1650 ms.
static const cardinal_segment_t seg_song_rise[] = {
    {  250,  2000.0f,  3500.0f,  5000.0f },
    SIL(100),
    {  250,  2000.0f,  3500.0f,  5000.0f },
    SIL(100),
    {  250,  2000.0f,  3500.0f,  5000.0f },
    SIL(100),
    {  250,  2000.0f,  3500.0f,  5000.0f },
    SIL(100),
    {  250,  2000.0f,  3500.0f,  5000.0f },
};

// SONG slow downslurs - long down-slurred. 2340 ms.
static const cardinal_segment_t seg_song_slow[] = {
    {  700,  6500.0f,  4000.0f,  1800.0f },
    SIL(120),
    {  700,  6500.0f,  4000.0f,  1800.0f },
    SIL(120),
    {  700,  6500.0f,  4000.0f,  1800.0f },
};

// SONG chip series - contact-call series. 1170 ms.
static const cardinal_segment_t seg_song_chip[] = {
    {   45,  5000.0f,  4000.0f,  3000.0f },
    SIL(80),
    {   45,  5000.0f,  4000.0f,  3000.0f },
    SIL(80),
    {   45,  5000.0f,  4000.0f,  3000.0f },
    SIL(80),
    {   45,  5000.0f,  4000.0f,  3000.0f },
    SIL(80),
    {   45,  5000.0f,  4000.0f,  3000.0f },
    SIL(80),
    {   45,  5000.0f,  4000.0f,  3000.0f },
    SIL(80),
    {   45,  5000.0f,  4000.0f,  3000.0f },
    SIL(80),
    {   45,  5000.0f,  4000.0f,  3000.0f },
    SIL(80),
    {   45,  5000.0f,  4000.0f,  3000.0f },
    SIL(80),
    {   45,  5000.0f,  4000.0f,  3000.0f },
};

#define CALL(k, nm, arr) { (k), (nm), (arr), (int)(sizeof(arr)/sizeof((arr)[0])) }

static const cardinal_call_t calls[] = {
    CALL(1, "SONG what-cheer-cheer-cheer", seg_song_a),
    CALL(2, "SONG what-cheer-cheer (low)", seg_song_b),
    CALL(3, "SONG cheer-cheer-cheer", seg_song_cheer),
    CALL(4, "SONG birdy-birdy-birdy", seg_song_birdy),
    CALL(5, "SONG purty-purty-purty", seg_song_purty),
    CALL(6, "SONG what-cheer + trill", seg_song_trill),
    CALL(7, "SONG rising series", seg_song_rise),
    CALL(8, "SONG slow downslurs", seg_song_slow),
    CALL(9, "SONG chip series", seg_song_chip),
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
