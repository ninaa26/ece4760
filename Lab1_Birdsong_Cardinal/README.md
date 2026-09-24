# Birdsong with cardinal presets (personal extension)

Not the code submitted with the report. See [`../Lab1_Birdsong/`](../Lab1_Birdsong/).

A personal extension of Lab 1, built with Claude. Compared with the submitted
code it adds:

- **Cardinal presets.** Keys 1–9 start up holding 2.2 s pitch tracks of real
  Northern Cardinal recordings from the Macaulay Library: songs on 1–4, a duet
  on 5, calls on 6–9 (`northern_cardinal.{c,h}`, `cardinal_data.h`).
- **A 5 ms linear amplitude envelope** in the ISR, in fix15, which removes the
  clicks at note edges.
- **Its own compose mode,** with up to 32 notes and a 50 ms gap between them.
- **Playback on an absolute timebase,** so the 10× replay cannot drift.
- **Key 0 as an escape hatch** that also cancels record, playback and compose.

`../Lab1_Birdsong_NoEnvelope/` is this version with the envelope removed, for
measuring the envelope's cost on GPIO 2.

    ./build.sh Lab1_Birdsong_Cardinal
    ./flash.sh Lab1_Birdsong_Cardinal
