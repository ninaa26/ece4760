# Early DDS sketch

Not the lab code — see [`../Lab1_Birdsong/`](../Lab1_Birdsong/).

`dactest.c` is an early standalone step from Hunter Adams' timer-interrupt DDS
demo: sine out of the MCP4822, keypad scan, pot on the ADC. It is kept as a
record of where `birdsong.c` started.

Two later snapshots, `dactest (1).c` and `dactest (2).c`, were near-identical
drafts of what became `Lab1_Birdsong/birdsong.c`. They were removed; both are
still in git history at commit `3095ded`.

It does not build as-is: this folder has no `pico_sdk_import.cmake` or
`pt_cornell_rp2040_v1_4.h`. Copy both from `../Lab1_Birdsong/` if you need to.
