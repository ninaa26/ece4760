# Envelope-free build

Not the code to hand in — see [`../Lab1_Birdsong/`](../Lab1_Birdsong/). Part of
the personal extension in [`../Lab1_Birdsong_Cardinal/`](../Lab1_Birdsong_Cardinal/).

Identical to `Lab1_Birdsong_Cardinal` except the amplitude envelope is absent: notes
switch on and off instantly instead of ramping over 5 ms.
The cardinal presets are compiled in from `../Lab1_Birdsong_Cardinal/` rather than
copied. If `birdsong.c` changes, regenerate this file so the two stay identical
except for the envelope.

## Why it exists

The report asks for code characterisation — how long the ISR takes, and what a
change costs. The envelope adds one `multfix15` (a 64-bit multiply and a shift)
to every one of the 50,000 interrupts per second. Measuring that means reading
GPIO 2 with and without it.

Keeping both builds means flashing twice rather than editing, rebuilding and
losing the first reading.

## Use

    ./build.sh Lab1_Birdsong_NoEnvelope     # -> build/Lab1_Birdsong_NoEnvelope-pico2/birdsong_no_envelope.uf2
    ./build.sh Lab1_Birdsong_Cardinal       # -> build/Lab1_Birdsong_Cardinal-pico2/birdsong.uf2

Flash one, probe GPIO 2, record the pulse width. Flash the other, record it
again. The difference is the envelope's cost per sample.

## What it sounds like

It clicks at every note boundary, and a spectrogram shows a vertical smear
across the whole band at each one. That is what the envelope exists to remove,
and it is worth capturing both spectrograms for the report — the comparison
makes the argument better than either picture alone.
