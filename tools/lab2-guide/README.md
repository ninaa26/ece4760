# Lab 2 guide generator

Builds the code shown in the field guide's Week 1 tab, steps 2–6, and checks
that every step compiles. The guide never shows code that hasn't compiled.

| File | What it is |
| --- | --- |
| `edits.py` | Every edit, in order. The anchor text it attaches to, the new code, and the "Where" and "What it does" text. **Edit this to change the code.** |
| `simple.py` | The "In simple words" line for each edit, the "big idea" boxes, and the plain-words boxes under some headings |
| `apply.py` | Applies the edits to the course demo and writes `out/stages/animation_stepN.c`. With `--build`, compiles every step |
| `gen.py` | Renders the Week 1 tab: edit cards, full-file listings, mock screens |
| `splice.py` | Puts only steps 2–6 from `gen.py`'s output into the live guide. Everything else stays as it is |
| `test_encoder.sh` | Laptop test of the step 2 encoder decoder, with contact bounce |

## Changing the guide's code

    cd tools/lab2-guide
    python3 apply.py --build              # every step must say "exit 0, 0 warnings/errors"
    ./test_encoder.sh                      # if you touched the encoder
    GEN_OUT=/tmp/gen_out.html python3 gen.py
    python3 splice.py /tmp/gen_out.html    # updates docs/ECE4760_galton-lab-field-guide.html

Then publish the guide as an Artifact (see `CLAUDE.md`: read the live version
first and merge, because other sessions edit it).

Notes:

- `apply.py` starts from `Hunter-Adams-RP2040-Demos/VGA_Graphics/Animation_Demo`
  in the repo root, or set `DEMO=` to another path. Pull it first; the guide
  assumes the GitHub version of 15 Sep 2026.
- Each anchor must match **exactly once** in the file at that point, or
  `apply.py` stops and names the edit.
- `gen.py` reads some figures (wiring, quadrature, collision, scope) from the
  current guide, so run it against an up-to-date `docs/` copy.
- Never publish `gen.py`'s whole output: steps 0–1, the checkoff and the other
  tabs are edited by hand and would be lost. Always go through `splice.py`.
