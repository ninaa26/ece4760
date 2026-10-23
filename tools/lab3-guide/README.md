# Lab 3 guide generator

Builds the whole Lab 3 field guide (`docs/ECE4760_helicopter-lab-field-guide.html`)
and checks that every code step compiles. The guide never shows code that hasn't compiled.

| File | What it is |
| --- | --- |
| `edits.py` | Every code edit, in order: anchor, new code, "Where", "In simple words", "What it does" |
| `apply.py` | Applies the edits to the course demos, writes `out/stages/`. `--build` compiles every step for the Pico 2 |
| `figures.py` | Computed SVGs: parts gallery, full system wiring, pin map, mock VGA screens |
| `template.html` | All the page text and hand-drawn figures, with `{{CARDS w s}}`, `{{TALLY w s}}`, `{{FIG name}}` markers |
| `style.css` | Copied from the Lab 2 guide so both look the same |
| `gen.py` | Fills the template and writes the page |

    cd tools/lab3-guide
    python3 apply.py --build     # every step must say "exit 0, 0 warnings/errors"
    python3 gen.py

Then publish to https://claude.ai/artifact/J1Ph47rMfgdW2Pdn9zQvKS (read the live
version first; see `CLAUDE.md`).

Notes:

- The demos come from `Hunter-Adams-RP2040-Demos` in the main checkout (or `DEMO=`).
  Assumes the GitHub version of 21 Sep 2026.
- This Mac's host compiler can't link (Command Line Tools SDK 27), so the SDK
  can't build pioasm or picotool. `apply.py` uses the installed ones from
  `~/.pico-sdk`, with a pioasm copy relabelled 2.3.0 to match the SDK.
- `out/` is build output; it's ignored.
