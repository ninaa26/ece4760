#!/usr/bin/env python3
"""Render the Lab 3 field guide: template.html + style.css + the edit cards.

    python3 apply.py --build     # first: every step must compile
    python3 gen.py               # writes docs/ECE4760_helicopter-lab-field-guide.html

In template.html, {{CARDS w s}} becomes the edit cards for week w step s plus a
full listing of the file after that step, and {{TALLY w s}} the one-line
summary of how many lines change, {{FIG name}} a figure from figures.py.
{{CSS}} is style.css.
"""
import html, re
from pathlib import Path
from edits import WEEKS, STEPS
from apply import stages, apply_edit
from figures import FIGS

HERE = Path(__file__).resolve().parent
OUT_HTML = HERE.parents[1] / "docs" / "ECE4760_helicopter-lab-field-guide.html"

OPS = {"after": ("add", "Add"), "before": ("add", "Add"), "change": ("chg", "Change")}


def lines(text):
    return text.rstrip("\n").split("\n")


def code_lines(cls, text):
    return "".join(f'<span class="l {cls}">{html.escape(l) or " "}</span>' for l in lines(text))


def line_hint(src, e):
    """Where the edit goes, as line numbers in the file just before this edit."""
    i = src.index(e["anchor"])
    first = src.count("\n", 0, i) + 1
    last = first + len(lines(e["anchor"])) - 1
    if e["op"] == "after":
        return f"right below line {last}"
    if e["op"] == "before":
        return f"right above line {first}"
    return f"replaces line {first}" if first == last else f"replaces lines {first}–{last}"


def card(week, e, fname, hint):
    cls, label = OPS[e["op"]]
    if e["op"] == "after":
        code = code_lines("ctx", e["anchor"]) + code_lines("add", e["new"])
    elif e["op"] == "before":
        code = code_lines("add", e["new"]) + code_lines("ctx", e["anchor"])
    else:
        code = code_lines("del", e["anchor"]) + code_lines("add", e["new"])
    eid = f"e{week}-" + e["id"].replace(".", "-")
    return f'''      <div class="edit" id="{eid}">
        <div class="edit-h"><span class="edit-n">{e["id"]}</span><span class="op {cls}">{label}</span><b>{e["title"]}</b><span class="fname">{fname}</span></div>
        <p class="where"><b>Where:</b> {e["where"]} <span class="lineno">{fname}: {hint}</span></p>
        <div class="simple"><b>In simple words</b> {e["simple"]}</div>
        <pre class="code">{code}</pre>
        <div class="why"><b>What it does</b>{e["why"]}</div>
      </div>
'''


def tally(week, step):
    edits = STEPS[(week, step)]
    added = sum(len(lines(e["new"])) for e in edits)
    removed = sum(len(lines(e["anchor"])) for e in edits if e["op"] == "change")
    fname = WEEKS[week]["file"]
    n = len(edits)
    return (f'{n} edit{"s" if n != 1 else ""} · {added} lines added, {removed} removed in '
            f'<code>{fname}</code>. Do them in order, save, then build.')


def main():
    after, before = {}, {}
    for w, s, b, a in stages():
        after[(w, s)], before[(w, s)] = a, b
    tpl = (HERE / "template.html").read_text()
    tpl = tpl.replace("{{CSS}}", (HERE / "style.css").read_text())

    def cards(m):
        w, s = int(m.group(1)), int(m.group(2))
        fname = WEEKS[w]["file"]
        body, src = "", before[(w, s)]
        for e in STEPS[(w, s)]:
            body += card(w, e, fname, line_hint(src, e))
            src = apply_edit(src, e)
        full = html.escape(after[(w, s)])
        body += f'''      <details class="full">
        <summary>Full <code>{fname}</code> after step {s}, to check your work against</summary>
        <pre class="code full">{full}</pre>
      </details>
'''
        return body

    tpl = re.sub(r"\{\{CARDS (\d) (\d)\}\}", cards, tpl)
    tpl = re.sub(r"\{\{FIG (\w+)\}\}", lambda m: FIGS[m.group(1)](), tpl)
    tpl = re.sub(r"\{\{TALLY (\d) (\d)\}\}", lambda m: tally(int(m.group(1)), int(m.group(2))), tpl)
    left = re.findall(r"\{\{[^}]*\}\}", tpl)
    if left:
        raise SystemExit(f"unfilled markers: {left}")
    OUT_HTML.write_text(tpl)
    print(f"wrote {OUT_HTML} ({len(tpl) // 1024} KB)")


if __name__ == "__main__":
    main()
