import os, re, html, difflib, importlib.util
S=os.path.dirname(os.path.abspath(__file__))
GUIDE=os.path.join(S,'..','..','docs','ECE4760_galton-lab-field-guide.html')
spec=importlib.util.spec_from_file_location('edits', os.path.join(S,'edits.py')); E=importlib.util.module_from_spec(spec); spec.loader.exec_module(E)
# re-run apply to fill 'removed' for range edits
spec2=importlib.util.spec_from_file_location('apply', os.path.join(S,'apply.py'))
src=open(os.path.join(S,'apply.py')).read().replace("spec=importlib.util.spec_from_file_location('edits', os.path.join(S,'edits.py')); E=importlib.util.module_from_spec(spec); spec.loader.exec_module(E)","")
g={'__file__':os.path.join(S,'apply.py'),'E':E,'__name__':'x'}
import sys; argv=sys.argv; sys.argv=['apply.py']; exec(src,g); sys.argv=argv

exec(open(os.path.join(S,'simple.py')).read())
doc=open(GUIDE).read()
esc=html.escape
def grab(start_marker, end_marker, frm=0, include_end=True):
    i=doc.index(start_marker, frm); j=doc.index(end_marker, i)
    return doc[i:j+(len(end_marker) if include_end else 0)]
def figure_containing(marker):
    k=doc.index(marker); i=doc.rindex('<figure', 0, k); j=doc.index('</figure>', k)+len('</figure>')
    return doc[i:j]
WIRING=grab('<h4>How the hardware is set up</h4>','<h4>Make your copy of the demo</h4>' if '<h4>Make your copy of the demo</h4>' in doc else '<h4>The build-and-flash routine</h4>',include_end=False)
WIRING=re.sub(r'\n      <div class="simple">.*?</div>','',WIRING,flags=re.S)
QUAD=figure_containing('Quadrature waveforms for one clockwise click')
RING='''<div class="ring" aria-label="State circle: 11 to 01 to 00 to 10 and back to 11 is clockwise">
        <span>11</span><i>→</i><span>01</span><i>→</i><span>00</span><i>→</i><span>10</span><i>→</i><span>11</span>
      </div>'''
ENCFIG=figure_containing('Rotary encoder seen from above')
ENCFIG=ENCFIG if '>GP4 ←<' in ENCFIG else ENCFIG.replace('text-anchor="middle">GP3</text>','text-anchor="middle">@A@</text>').replace('text-anchor="middle">GP4</text>','text-anchor="middle">@B@</text>').replace('>GP2 ←<','>@SW@ ←<')
ENCFIG=ENCFIG.replace('@A@','GP2').replace('@B@','GP3').replace('@SW@','GP4')
COLL=figure_containing('Ball touching a peg')
SCOPE=figure_containing('Expected scope trace of one thunk')

stage={n:open(f'{S}/out/stages/animation_step{n}.c').read() for n in range(1,7)}
cmake6=open(f'{S}/out/stages/CMakeLists_step6.txt').read()

# ---------- edit cards
OPNAME={'after':('Add','add'),'before':('Add','add'),'delete':('Delete','del'),'delete_range':('Delete','del'),'replace':('Change','chg'),'replace_range':('Change','chg')}
def lines(t, cls):
    t=t.strip('\n')
    return ''.join(f'<span class="l {cls}">{esc(l) if l else " "}</span>' for l in t.split('\n'))
def summarize(t, cls, keep=3):
    ls=t.strip('\n').split('\n')
    if len(ls)<=keep*2+1: return lines(t,cls)
    return lines('\n'.join(ls[:keep]),cls)+f'<span class="l skip">⋮  {len(ls)-2*keep} more lines  ⋮</span>'+lines('\n'.join(ls[-keep:]),cls)
def ctx(t, last=True):
    ls=[l for l in t.strip('\n').split('\n')]
    l=ls[-1] if last else ls[0]
    return f'<span class="l ctx">{esc(l)}</span>'
def card(e):
    name,cls=OPNAME[e['op']]; op=e['op']
    body=''
    if op=='after':
        body=f'<pre class="code">{ctx(e["anchor"],True)}{lines(e["new"],"add")}</pre>'
    elif op=='before':
        body=f'<pre class="code">{lines(e["new"],"add")}{ctx(e["anchor"],False)}</pre>'
    elif op=='delete':
        body=f'<div class="lbl">Delete these lines</div><pre class="code">{lines(e["anchor"],"del")}</pre>'
    elif op=='delete_range':
        body=f'<div class="lbl">Delete this whole block</div><pre class="code">{summarize(e["removed"],"del")}</pre>'
    elif op=='replace':
        body=f'<div class="lbl">Find</div><pre class="code">{lines(e["anchor"],"del")}</pre><div class="lbl">Replace with</div><pre class="code">{lines(e["new"],"add")}</pre>'
    elif op=='replace_range':
        body=f'<div class="lbl">Find this whole block</div><pre class="code">{summarize(e["removed"],"del")}</pre><div class="lbl">Replace it with</div><pre class="code">{lines(e["new"],"add")}</pre>'
    fname='CMakeLists.txt' if e.get('file')=='cmake' else 'animation.c'
    why=e['why'] if e['why'].lstrip().startswith('<') else f'<p>{e["why"]}</p>'
    return f'''
      <div class="edit" id="e{e["id"].replace(".","-")}">
        <div class="edit-h"><span class="edit-n">{e["id"]}</span><span class="op {cls}">{name}</span><b>{e["title"]}</b><span class="fname">{fname}</span></div>
        <p class="where"><b>Where:</b> {e["where"]}</p>
        <div class="simple"><b>In simple words</b> {SIMPLE[e["id"]]}</div>
        {body}
        <div class="why"><b>What it does</b>{why}</div>
      </div>'''
def diffcount(a,b):
    add=rem=0
    for l in difflib.ndiff(a.split('\n'),b.split('\n')):
        if l.startswith('+ '): add+=1
        elif l.startswith('- '): rem+=1
    return add,rem
def edits_block(n):
    es=E.STEPS[n]; a,r=diffcount(stage[n-1],stage[n])
    extra=' plus one line in <code>CMakeLists.txt</code>' if n==6 else ''
    return f'''
      <h4>Change the code</h4>
      <p class="tally">{len(es)} edits · {a} lines added, {r} removed in <code>animation.c</code>{extra}. Do them in order, save, then build.</p>
      {''.join(card(e) for e in es)}'''
def fullfile(n):
    extra=f'<div class="lbl">CMakeLists.txt</div><pre class="code full">{esc(cmake6)}</pre>' if n==6 else ''
    return f'''
      <details class="full">
        <summary>Full <code>animation.c</code> after step {n}, to check your work against</summary>
        <pre class="code full">{esc(stage[n])}</pre>{extra}
      </details>'''

# ---------- screen mockups
def screen(inner,label,cap):
    return f'''
      <figure class="screenfig">
        <div class="screenwrap">
          <svg class="screen" viewBox="0 0 640 480" role="img" aria-label="{label}">
            <rect x="0" y="0" width="640" height="480" fill="#000"/>
            {inner}
          </svg>
        </div>
        <figcaption>{cap}</figcaption>
      </figure>'''
def txt(x,y,t,sz=20): return f'<text x="{x}" y="{y}" font-size="{sz}" fill="#fff" font-family="JetBrains Mono, monospace">{t}</text>'
def anno(x,y,t,anchor='start'): return f'<text x="{x}" y="{y}" font-size="15" fill="#F2C94C" font-family="Archivo, sans-serif" font-style="italic" text-anchor="{anchor}">{t}</text>'
def ghost(x,y,o,r=4,fill='#27D3E6'): return f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{fill}" opacity="{o}"/>'
NOTE='Text is enlarged here so it can be read. <span class="yl">Yellow notes</span> explain; they are not on the real screen.'
BOX='<rect x="100" y="100" width="440" height="280" fill="none" stroke="#fff" stroke-width="2"/>'
def hdr(enc=True, spare='16498'):
    out=txt(10,32,'Encoder Count: 3',22) if enc else ''
    if spare: out+=txt(10,54,f'Spare time: {spare} us',13)
    return out
arrow=lambda x1,y1,x2,y2:f'<path d="M{x1} {y1} L{x2} {y2}" stroke="#F2C94C" stroke-width="1.6" stroke-dasharray="4 4" marker-end="url(#yarr)"/>'
YDEF='<defs><marker id="yarr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#F2C94C"/></marker></defs>'
m1=screen(YDEF+BOX+ghost(230,200,1,15,'#fff')+ghost(420,290,1,15,'#fff')+arrow(250,210,300,230)+arrow(400,300,350,315)
          +anno(120,130,'two white balls bounce around inside the box')+anno(120,360,'the demo, unchanged'),
          'Mock monitor, step 1: a white rectangle outline with two white balls bouncing inside',
          'Step 1: the untouched demo. A white box and two white balls bouncing off its walls. '+NOTE)
m2=screen(YDEF+BOX+ghost(230,200,1,15,'#fff')+ghost(420,290,1,15,'#fff')+hdr(True,None)
          +anno(250,32,'← +1 per click clockwise, −1 counter-clockwise')+anno(120,360,'the demo\'s two balls keep bouncing'),
          'Mock monitor, step 2: Encoder Count: 3 at the top left, above the demo box with its two white balls',
          'Step 2: the demo still runs, with the encoder count at the top. '+NOTE)
m3=screen(YDEF+BOX+ghost(300,240,1,15,'#fff')+arrow(320,250,370,270)+hdr(True,'16410')
          +anno(260,54,'← new: spare time, jiggles a little')+anno(120,360,'one ball now (core 1\'s ball is gone)'),
          'Mock monitor, step 3: the box with one white ball, Encoder Count and Spare time text at top left',
          'Step 3: one ball in the box, the count, and the spare-time line. '+NOTE)
pts=[(0,320,4),(10,322,21),(20,324,74),(30,326,165),(40,328,293),(50,330,457)]
g4=''.join(ghost(x,y,0.25+0.12*i) for i,(n,x,y) in enumerate(pts[:-1]))+ghost(pts[-1][1],pts[-1][2],1)
g4+=''.join(anno(x+14,y+5,f'frame {n}') for n,x,y in pts)+anno(420,250,'gaps grow each frame:')+anno(420,270,'it is speeding up')+anno(420,420,'then drops again from the top')
m4=screen(hdr(True,'16430')+g4,'Mock monitor, step 4: one small cyan ball shown at six moments of its fall, with growing gaps',
          'Step 4: no box; one small cyan ball, shown here at six moments of one drop (the real screen shows one ball at a time). About 50 frames, under a second, top to bottom. '+NOTE)
def bounce(sign,o=1.0,dash=False):
    pp=[(320,4),(322,21),(324,74),(320+7*sign,112)]+[(320+sign*(x-320),y) for x,y in [(373,129),(420,183),(466,274),(513,402),(531,470)]]
    d='M'+' L'.join(f'{x} {y}' for x,y in pp)
    return f'<path d="{d}" fill="none" stroke="#27D3E6" stroke-width="1.5" opacity="{0.5*o}" stroke-dasharray="{"4 5" if dash else "2 4"}"/>'
PEG='<circle cx="320" cy="120" r="6" fill="#fff"/>'
m5=screen(hdr(True,'16410')+bounce(1)+bounce(-1,0.6,True)+PEG+ghost(327,112,0.6)+ghost(466,274,1)
          +anno(340,112,'hits the peg ≈ frame 25')+anno(470,260,'bounces off, slower')+anno(80,330,'or this way: random')+anno(170,150,'peg at (320, 120)'),
          'Mock monitor, step 5: a white peg; the ball path comes down onto it and curves away to the right, with a faint mirrored path to the left',
          'Step 5: the peg, and the path of one drop (dotted). Which side it goes changes every drop. '+NOTE)
burst='<g stroke="#F2C94C" stroke-width="2"><path d="M350 86 L362 76 M352 100 L368 100 M348 72 L352 60"/></g>'
m6=screen(hdr(True,'16400')+bounce(1)+PEG+ghost(327,112,1)+burst+anno(372,94,'thunk! (you hear it; the screen looks like step 5)'),
          'Mock monitor, step 6: same as step 5, with a note that a thunk sounds at the moment of impact',
          'Step 6: the screen looks the same as step 5. What changes is the sound at the moment of impact. '+NOTE)

def see(t): return f'<div class="see"><b>You should see</b> {t}</div>'
def flash(n): return f'''
      <h4>Build and flash</h4>
      <p>Save the file, then run <code>./flash.sh Lab2_Galton</code> and double-press reset.</p>'''

W=[]
W.append('''  <!-- ============================ WEEK 1 ============================ -->
  <section class="panel" id="week1" role="tabpanel" aria-labelledby="tab-week1" hidden>
    <h2>Week 1, one step at a time</h2>
    <p class="lede">Checkoff: end of your lab section, week of 9/21. You start from the course's <b>Animation Demo</b>, exactly as provided, and change it in six small steps. Every change is shown: where it goes, the code, and what it does. After each step you flash the board and check one new thing works.</p>

    <div class="note"><b>Where the code comes from.</b> The only starting code is what the course provides: <code>VGA_Graphics/Animation_Demo</code> (your file, <code>animation.c</code>, plus the VGA library and protothreads, which you never edit) and <code>Audio/e_DMA_Demo</code> (read it for step 6). The changes below were written with Claude, and each step was compiled to check it builds; none has been run on a board yet. That means the report's <b>AI prompt log</b> applies to this code: keep a note of it as you go (see Checkoff).</div>

    <div class="legend">
      <span><span class="op add">Add</span> type in the green lines</span>
      <span><span class="op del">Delete</span> remove the red lines</span>
      <span><span class="op chg">Change</span> replace the red lines with the green ones</span>
      <span><span class="l ctx inline">grey line</span> already in the file, just a landmark</span>
    </div>

    <nav class="stepnav" aria-label="Week 1 steps">
      <a href="#w1-s0">0 · Set up</a>
      <a href="#w1-s1">1 · Run the demo</a>
      <a href="#w1-s2">2 · Trim it down</a>
      <a href="#w1-s3">3 · Encoder</a>
      <a href="#w1-s4">4 · Falling ball</a>
      <a href="#w1-s5">5 · Peg and bounce</a>
      <a href="#w1-s6">6 · Thunk sound</a>
      <a href="#w1-check">Checkoff</a>
      <a href="#w1-words">Word list</a>
    </nav>''')

# STEP 0
W.append(f'''
    <div class="step" id="w1-s0">
      <div class="step-h"><span class="step-n">Step 0</span><h3>Set up</h3></div>
      <p>Goal: everything on the bench, the wiring understood, and your own copy of the demo ready to edit.</p>

      <h4>Gather</h4>
      <ul class="tick">
        <li>A breadboard with the Pico 2. Nothing from Lab 1 is needed.</li>
        <li>A VGA monitor and the VGA connector with its resistors (330 Ω × 3, 470 Ω × 1).</li>
        <li>The rotary encoder (Bourns PEC11) and five jumper wires.</li>
        <li>For step 6: an MCP4822 DAC, a 3.5 mm audio jack, and a speaker or headphones. The oscilloscope.</li>
        <li>Optional: a push button for reset (RUN to GND). Without one, hold BOOTSEL while plugging in USB to flash.</li>
      </ul>

{WIRING}
      <h4>Make your copy of the demo</h4>
      <p>The starting code is the course's <a href="https://github.com/vha3/Hunter-Adams-RP2040-Demos/tree/master/VGA_Graphics/Animation_Demo">Animation Demo on GitHub</a>. Your laptop has a copy of that repository in the ECE4760 folder. In Terminal:</p>
<pre><code>cd ~/Developer/Active/ECE4760
git -C Hunter-Adams-RP2040-Demos pull
cp -R Hunter-Adams-RP2040-Demos/VGA_Graphics/Animation_Demo Lab2_Galton</code></pre>
      <p>The first line goes to the course folder. The second updates your copy of the demos to match GitHub (Hunter still makes small fixes; the version this guide starts from is from 15 Sep 2026). The third copies the whole demo folder to a new folder, <code>Lab2_Galton</code>, which is yours to change. The original stays untouched, so you can always compare.</p>
      <div class="tbl"><table>
        <thead><tr><th>In <code>Lab2_Galton/</code></th><th>What it is</th><th>You edit it?</th></tr></thead>
        <tbody>
          <tr><td><code>animation.c</code></td><td>the program: this is where all your changes go</td><td><b>Yes</b></td></tr>
          <tr><td><code>CMakeLists.txt</code></td><td>the build recipe: which files and libraries</td><td>One line, in step 6</td></tr>
          <tr><td><code>VGA/</code></td><td>the course VGA library (drawing, text, the VGA signals)</td><td>No</td></tr>
          <tr><td><code>pt_cornell_rp2040_v1_4.h</code></td><td>protothreads, the course's lightweight threads</td><td>No</td></tr>
          <tr><td><code>pico_sdk_import.cmake</code></td><td>connects the build to the Pico SDK</td><td>No</td></tr>
        </tbody>
      </table></div>

      <h4>The build-and-flash routine</h4>
      <p>You'll do this after every step:</p>
<pre><code>./flash.sh Lab2_Galton</code></pre>
      <p>It compiles, then waits for the board. <b>Double-press the reset button</b> (or, with no reset button, unplug USB, hold BOOTSEL and plug it back in): the Pico shows up as a drive, the script copies the program onto it, and the board restarts running it. When it prints <code>FLASHED</code>, you're done. If the compile fails, read the <em>first</em> error; it names the file and line. Later errors are usually knock-on effects.</p>
    </div>''')

# STEP 1
W.append(f'''
    <div class="step" id="w1-s1">
      <div class="step-h"><span class="step-n">Step 1</span><h3>Run the demo as it is</h3></div>
      <p>Goal: prove the VGA wiring and the build work, with code you haven't touched. If this works, any later problem is in your own changes.</p>

      <h4>Wire the VGA connector</h4>
      <div class="tbl"><table>
        <thead><tr><th>Pico pin</th><th>Through</th><th>VGA connector</th><th>What it carries</th></tr></thead>
        <tbody>
          <tr><td><code>21 · GP16</code></td><td>wire</td><td>Hsync (pin 13)</td><td>"start a new line"</td></tr>
          <tr><td><code>22 · GP17</code></td><td>wire</td><td>Vsync (pin 14)</td><td>"start a new screen"</td></tr>
          <tr><td><code>24 · GP18</code></td><td>470 Ω</td><td>Green (pin 2)</td><td>green, dim bit</td></tr>
          <tr><td><code>25 · GP19</code></td><td>330 Ω</td><td>Green (pin 2)</td><td>green, bright bit</td></tr>
          <tr><td><code>26 · GP20</code></td><td>330 Ω</td><td>Blue (pin 3)</td><td>blue</td></tr>
          <tr><td><code>27 · GP21</code></td><td>330 Ω</td><td>Red (pin 1)</td><td>red</td></tr>
          <tr><td><code>GND</code></td><td>wire</td><td>Ground (pins 5–10)</td><td>shared reference</td></tr>
        </tbody>
      </table></div>

      <h4>Change the code</h4>
      <p class="tally">Nothing this step.</p>
{flash(1)}
      {see('a white box with two white balls bouncing around inside it.')}
{m1}
      <h4>How it works: VGA</h4>
      <p>The monitor paints 640 × 480 dots (pixels), one row at a time from top to bottom, 60 times per second. Two timing wires tell it where it is: a pulse on <b>Hsync</b> means "next row", a pulse on <b>Vsync</b> means "back to the top". The colour wires carry a small voltage for how bright red, green and blue should be at that instant. The resistors turn the Pico's 3.3 V into the low voltage VGA expects. Two green wires give green four levels and one each for red and blue gives two, so there are <b>16 colours</b>, the names like <code>WHITE</code>, <code>CYAN</code> and <code>BLACK</code> in the code.</p>
      <p>Your code doesn't produce those signals. The VGA library sets up the Pico's <b>PIO</b> (small hardware units that toggle pins with exact timing) and <b>DMA</b> (hardware that copies memory, more in step 6) to send the picture continuously. Your code only changes pixels in memory, with calls like <code>fillCircle()</code>.</p>
      <p><b>Double buffering:</b> there are two copies of the screen in memory. The monitor shows one while you draw on the other, and they swap every frame. You never see a half-drawn picture.</p>

      <h4>How it works: a tour of the demo's <code>animation.c</code></h4>
      <p>Open it and find each part. Reading it once now makes every later step easier.</p>
      <div class="tbl"><table>
        <thead><tr><th>Part of the file</th><th>What it does</th></tr></thead>
        <tbody>
          <tr><td><code>#include</code> lines</td><td>Bring in the libraries: VGA, the Pico SDK, protothreads.</td></tr>
          <tr><td>"fixed point macros"</td><td><code>fix15</code> numbers: fractions stored as whole numbers. Step 4 explains them.</td></tr>
          <tr><td><code>hitBottom</code> … <code>hitRight</code></td><td>Is a position past the box's walls?</td></tr>
          <tr><td><code>boid0_…</code>, <code>boid1_…</code></td><td>Position and velocity of the two balls ("boid" is just the demo's name for a moving thing).</td></tr>
          <tr><td><code>spawnBoid</code>, <code>wallsAndEdges</code>, <code>drawArena</code></td><td>Start a ball; move it and bounce it off walls; draw the box.</td></tr>
          <tr><td><code>protothread_serial</code></td><td>Reads a colour number typed over USB serial.</td></tr>
          <tr><td><code>protothread_anim</code></td><td>Core 0's loop: wait for the frame signal, clear, move and draw ball 0, draw the box.</td></tr>
          <tr><td><code>protothread_anim1</code>, <code>core1_main</code></td><td>The same for ball 1, on the Pico's second core.</td></tr>
          <tr><td><code>main()</code></td><td>Runs first: sets the clock, starts VGA, starts core 1, starts the threads.</td></tr>
        </tbody>
      </table></div>
      <p><b>Protothreads</b> let several jobs take turns on one core. The key line is <code>PT_YIELD_UNTIL(pt, condition)</code>: "pause this job here until the condition is true, and let other jobs run meanwhile". The animation loop starts with <code>PT_YIELD_UNTIL(pt, draw_start_signal())</code>, which waits until the VGA library says a new frame has begun.</p>

      <h4>If it doesn't work</h4>
      <div class="tbl"><table>
        <thead><tr><th>What you see</th><th>Check</th></tr></thead>
        <tbody>
          <tr><td>Monitor says "no signal"</td><td>Hsync on GPIO 16 (pin 21), Vsync on GPIO 17 (pin 22), ground connected. Try the monitor's input button.</td></tr>
          <tr><td>Picture, wrong colours</td><td>Red, green and blue swapped between GPIO 18–21.</td></tr>
          <tr><td><code>flash.sh</code> keeps waiting</td><td>Double-press reset quickly (both presses within about ⅕ s), or hold BOOTSEL while plugging in USB.</td></tr>
        </tbody>
      </table></div>
    </div>''')

# STEP 2 (encoder, the handout's first item)
SEE2=see('the demo&#x27;s two balls still bouncing in the box, and "Encoder Count: 0" at the top left. One click clockwise: 1. Two clicks back: −1.')
W.append(f"""
    <div class="step" id="w1-s2">
      <div class="step-h"><span class="step-n">Step 2</span><h3>Make the knob count</h3></div>
      <p>Goal: turn the knob clockwise and a number on the monitor goes up by one per click; counter-clockwise, down. <b>This is the first checkoff item in the handout.</b> The code is your group's encoder program, fixed so contact rattle can't miscount (see 2.2), and merged into the demo so the demo keeps running underneath.</p>

      <h4>Know the part</h4>
      <p>The encoder has <b>three pins on one side</b> (A, C, B, with C, common, in the middle) and <b>two on the other</b> (the push button, not needed until week 3). Look at the part number printed on it, something like <code>PEC11R-4215K-S0024</code>. The digit after <code>-4</code> is clicks per turn (2 → 24, 3 → 12, 1 → 18) and the last digits are pulses per turn. The code counts a click each time the knob gets back to rest with both switches open, which is once per click when the two numbers match (24 and 24). On a 24-click, 12-pulse part it would count every other click.</p>
{ENCFIG}
      <h4>Wire it</h4>
      <div class="tbl"><table>
        <thead><tr><th>Encoder pin</th><th>Goes to</th></tr></thead>
        <tbody>
          <tr><td>A (end of the 3-pin row)</td><td><code>4 · GP2</code></td></tr>
          <tr><td>C (middle of the 3-pin row)</td><td><code>GND</code> (e.g. pin 3)</td></tr>
          <tr><td>B (other end of the 3-pin row)</td><td><code>5 · GP3</code></td></tr>
          <tr><td>Button pin 1</td><td><code>6 · GP4</code> (week 3; not needed yet)</td></tr>
          <tr><td>Button pin 2</td><td><code>GND</code> (week 3)</td></tr>
        </tbody>
      </table></div>
      <p>No resistors: the code turns on the Pico's built-in pull-ups. <b>On your board</b> pins 3, 4 and 5 are on the Pico's bottom edge, counting from the USB end (pin 1 is the corner by the USB port). Push the encoder's pins into the breadboard, with A, C and B in three different numbered strips, so nothing wiggles loose.</p>

      <h4>Before the code: how an encoder works</h4>
      <p><b>Switches and pull-ups.</b> Inside, A and B are two switches to C, which is ground. An input pin reads 1 (3.3 V) or 0 (0 V). With a switch open, the pin connects to nothing and would read randomly. A <b>pull-up</b> is a weak resistor inside the Pico from the pin to 3.3 V, so open reads <b>1</b> and closed (tied to ground) reads <b>0</b>.</p>
      <p><b>Direction.</b> One click clockwise closes A, then B, then opens A, then B. Counter-clockwise is the reverse: B first.</p>
{QUAD}
      <p>Written as two digits (A then B), the knob moves around this circle one position at a time. Right is clockwise, left is counter-clockwise. This two-signal pattern is called <b>quadrature</b>.</p>
      {RING}
      <p>Your group's first version checked B at the moment A fell: still HIGH means clockwise, already LOW means counter-clockwise. The fixed version follows every step around the circle, which gives the same answer and also copes with rattle.</p>
      <p><b>Interrupts.</b> Rather than checking the pins over and over, the code asks for an <b>interrupt</b>. It works like a doorbell: whenever A or B changes, the Pico pauses, runs one short function, and carries on. It costs nothing while the knob is still.</p>
      <p><b>Bounce.</b> Metal contacts rattle for up to 5 ms (datasheet) as they touch and as they open. A rattle goes one step forward and back, +1 then −1, which adds to zero, and the count only changes when the knob is back at rest. So no debounce timer is needed.</p>
{edits_block(2)}
{flash(2)}
      {SEE2}
{m2}
      <h4>If it doesn't work</h4>
      <div class="tbl"><table>
        <thead><tr><th>What you see</th><th>Fix</th></tr></thead>
        <tbody>
          <tr><td>Clockwise counts <em>down</em></td><td>A and B swapped: swap the two wires, or the numbers in <code>ENCODER_A</code> and <code>ENCODER_B</code>.</td></tr>
          <tr><td>Never changes</td><td>Is C (middle pin) on ground? Scope GPIO 2 (pin 4): it should sit at 3.3 V and drop to 0 V as you turn.</td></tr>
          <tr><td>Changes only every other click</td><td>A 24-click, 12-pulse encoder rests with both switches closed every other click. Also count at state 0: change <code>if (new_state == 3)</code> to <code>if (new_state == 3 || new_state == 0)</code>.</td></tr>
          <tr><td>Doesn't count unless you turn fast</td><td>A wire is loose, so the circle is missing a step. Push the encoder's pins fully into the breadboard.</td></tr>
        </tbody>
      </table></div>
      <h4>Try this</h4>
      <p>Turn exactly 10 clicks clockwise, slowly, then 10 back. The count should go 0 → 10 → 0. Then do it fast. Note the result in the lab notebook; it's a good accuracy test for the report. Scope A on channel 1 and B on channel 2 while turning slowly to see the picture above, and zoom into an edge to see the bounce.</p>
      {fullfile(2)}
    </div>""")

# STEP 3 (trim to one core, time each frame)
W.append(f"""
    <div class="step" id="w1-s3">
      <div class="step-h"><span class="step-n">Step 3</span><h3>Trim it to one core, and time each frame</h3></div>
      <p>Goal: a simpler program you understand fully (one ball, one core, one thread), plus a readout of how much time each frame leaves spare. You'll use that number all through the lab.</p>
{edits_block(3)}
{flash(3)}
      {see('one white ball bouncing in the box, "Encoder Count" still working, and "Spare time: …" near 16 400 µs under it.')}
{m3}
      <h4>How it works</h4>
      <p>Edits 3.1–3.7 only <em>remove</em> things. The program now has one thread on one core, and it's much easier to follow. Edits 3.8–3.12 add the <b>frame budget</b>. At 60 frames per second each frame is 16 667 µs. Everything your code does in a frame (physics, drawing) has to fit in that, or the picture falls behind. <code>Spare time</code> is how much was left. With one ball it's nearly all of it. In week 3 you'll add balls until it approaches zero, and the LED is the warning light.</p>
      {fullfile(3)}
    </div>""")

# STEP 4
W.append(f'''
    <div class="step" id="w1-s4">
      <div class="step-h"><span class="step-n">Step 4</span><h3>Drop one ball</h3></div>
      <p>Goal: replace the demo's bouncing ball with a Galton ball: dropped from the top middle, falling faster and faster under gravity, and dropped again when it leaves the bottom. No peg yet.</p>

      <h4>Before the code: three ideas</h4>
      <p><b>Screen coordinates.</b> (0, 0) is the <b>top-left</b> corner. x grows to the right (to 639), and <b>y grows downward</b> (to 479). So falling means y increasing, and gravity is a positive number.</p>
      <p><b>Moving one frame at a time.</b> The ball has a position (<code>x</code>, <code>y</code>) and a velocity (<code>vx</code>, <code>vy</code>), in pixels per frame. Every frame: position += velocity, then velocity += gravity. With the handout's gravity of 0.37:</p>
      <div class="tbl"><table>
        <thead><tr><th class="num">Frame</th><th class="num">y (px)</th><th class="num">vy (px/frame)</th></tr></thead>
        <tbody>
          <tr><td class="num">0</td><td class="num">4.00</td><td class="num">0.00</td></tr>
          <tr><td class="num">1</td><td class="num">4.00</td><td class="num">0.37</td></tr>
          <tr><td class="num">2</td><td class="num">4.37</td><td class="num">0.74</td></tr>
          <tr><td class="num">3</td><td class="num">5.11</td><td class="num">1.11</td></tr>
          <tr><td class="num">4</td><td class="num">6.22</td><td class="num">1.48</td></tr>
        </tbody>
      </table></div>
      <p><b>Fixed point.</b> 0.37 isn't a whole number, and whole-number maths is the fastest thing the Pico does. So every value is stored multiplied by 32 768 (2¹⁵) as a whole number, in the type <code>fix15</code>. For example, 1 is stored as 32 768 and 0.37 as 12 124. Adding works as normal. Multiplying needs a divide by 32 768 afterwards, which is what <code>multfix15</code> does. To draw, <code>fix2int15</code> converts back to whole pixels.</p>
{edits_block(4)}
{flash(4)}
      {see('the box is gone. A small cyan ball starts at the top middle, slowly at first, then faster, drifting a little sideways. It reaches the bottom in under a second, then starts again at the top.')}
{m4}
      <h4>Try this</h4>
      <p>Change <code>GRAVITY</code> to <code>float2fix15(0.1)</code> and flash: it floats down. Set it back to 0.37; the checkoff uses the handout's values.</p>
      {fullfile(4)}
    </div>''')

# STEP 5
W.append(f'''
    <div class="step" id="w1-s5">
      <div class="step-h"><span class="step-n">Step 5</span><h3>Add the peg and bounce off it</h3></div>
      <p>Goal: a white peg under the drop point. The ball hits it, bounces off to one side, slower, and keeps falling.</p>

      <h4>Before the code: the bounce in five ideas</h4>
{COLL}
      <ol>
        <li><b>Touching?</b> The gaps between centres are <code>dx = ball.x − peg.x</code> and <code>dy = ball.y − peg.y</code>. They touch when the centres are closer than 4 + 6 = <b>10 px</b>. A quick check first: if |dx| or |dy| is already 10 or more, they can't be touching.</li>
        <li><b>How far exactly?</b> √(dx² + dy²) is slow, so <b>alpha max plus beta min</b> estimates it: 0.960 × the bigger + 0.398 × the smaller. For dx = 6, dy = −8 that's 10.07; the true value is 10.</li>
        <li><b>The normal</b> is an arrow of length 1 from the peg's centre through the ball's: (dx/distance, dy/distance) = (0.6, −0.8) in the picture.</li>
        <li><b>Bounce:</b> flip the part of the velocity that points into the peg, like a ball off a wall. The dot product <code>n·v = nx·vx + ny·vy</code> measures that part. With v = (0, 5): n·v = −4, so −2 × n·v = 8, and the new v = (0 + 0.6×8, 5 − 0.8×8) = <b>(4.8, −1.4)</b>. The speed is still 5.</li>
        <li><b>Tidy up:</b> move the ball to 11 px from the peg's centre so it isn't still overlapping next frame. On a <i>new</i> peg only, multiply the velocity by the bounciness (0.5): (2.4, −0.7).</li>
      </ol>
{edits_block(5)}
{flash(5)}
      {see('a white peg at (320, 120). The ball lands on it about 25 frames (under half a second) after dropping, flies off left or right, and falls off the bottom. Each drop differs.')}
{m5}
      <h4>If it doesn't work</h4>
      <div class="tbl"><table>
        <thead><tr><th>What you see</th><th>Likely cause</th></tr></thead>
        <tbody>
          <tr><td>Ball goes straight through</td><td>The peg loop isn't running: check 5.6 is inside <code>update_ball</code>, and 5.8 sets the peg.</td></tr>
          <tr><td>Ball sticks or jitters on the peg</td><td>The teleport distance: it should be radius + radius + 1 = 11.</td></tr>
          <tr><td>Always the same bounce</td><td>The random <code>vx</code> isn't changing: check <code>spawn_ball</code> and <code>srand</code>.</td></tr>
        </tbody>
      </table></div>
      <h4>Try this</h4>
      <p><code>BOUNCINESS</code> at <code>float2fix15(1.0)</code> keeps all the energy (big bounces); at 0.2 it barely bounces. Put it back to 0.5.</p>
      {fullfile(5)}
    </div>''')

# STEP 6
W.append(f'''
    <div class="step" id="w1-s6">
      <div class="step-h"><span class="step-n">Step 6</span><h3>Make it go "thunk"</h3></div>
      <p>Goal: a short, low thunk every time the ball hits the peg, played by <b>DMA</b> as the handout requires. After this step, week 1 is complete.</p>

      <h4>Wire it</h4>
      <p>This is the first time the DAC goes on this board. It sits on the left of the Pico, below the encoder:</p>
      <div class="tbl"><table>
        <thead><tr><th>MCP4822 pin</th><th>Goes to</th></tr></thead>
        <tbody>
          <tr><td>1 VDD</td><td>3V3 (Pico pin 36), the + rail</td></tr>
          <tr><td>2 CS</td><td><code>7 · GP5</code></td></tr>
          <tr><td>3 SCK</td><td><code>9 · GP6</code></td></tr>
          <tr><td>4 SDI</td><td><code>10 · GP7</code></td></tr>
          <tr><td>5 LDAC</td><td>GND</td></tr>
          <tr><td>6 VOUTB</td><td>audio jack tip (sleeve to GND), and the scope</td></tr>
          <tr><td>7 VSS</td><td>GND</td></tr>
        </tbody>
      </table></div>
      <p>These are the course DMA demo's pins, except MISO: the demo also claims GPIO 4, which is your encoder's B, and the DAC never sends anything back, so this code leaves MISO out.</p>

      <h4>Before the code: a sound is a list of numbers, and DMA sends it</h4>
      <p>As in Lab 1, the speaker follows the DAC's voltage. Here the whole thunk is worked out <b>once at startup</b> and stored as 1 323 numbers: a low tone that drops in pitch and fades out. Playing it means sending those numbers to the DAC 44 105 times a second, which takes 30 ms. Each number is a 16-bit word: the top 4 bits are settings (channel B, gain, on) and the bottom 12 bits are the level, 0–4095, where 2048, the middle, is silence.</p>
      <p>In Lab 1 an interrupt sent every sample, 50 000 times a second. <b>DMA</b> (direct memory access) is hardware that copies data from memory to a peripheral <i>by itself</i>. It's like switching on a conveyor belt instead of carrying 1 323 buckets: the CPU says "go" once and goes back to the balls.</p>
      <div class="pipe">
        <div class="stage cpu"><b>Your code</b>ball hits a new peg → <code>play_thunk()</code><span>one line</span></div>
        <div class="arrow" aria-hidden="true">→</div>
        <div class="stage"><b>Control channel</b>"rewind to the start of the list, and go"<span>1 transfer</span></div>
        <div class="arrow" aria-hidden="true">→</div>
        <div class="stage"><b>Data channel</b>sends the list to SPI, one number per timer tick<span>1 323 transfers</span></div>
        <div class="arrow" aria-hidden="true">→</div>
        <div class="stage"><b>DAC → speaker</b>channel B, the audio jack<span>thunk</span></div>
      </div>
      <p><b>Why two channels?</b> After playing, the data channel is left pointing at the <i>end</i> of the list. The control channel's only job is to put the start address back and restart it, all in hardware. Open <code>Hunter-Adams-RP2040-Demos/Audio/e_DMA_Demo/dma-demo.c</code> next to your file: 6.4 is built from it.</p>
{edits_block(6)}
{flash(6)}
      {see('the same picture as step 5. <b>You should hear</b> one short thunk, about 30 ms, each time the ball lands on the peg, and nothing while it falls.')}
{m6}
{SCOPE}
      <h4>If it doesn't work</h4>
      <div class="tbl"><table>
        <thead><tr><th>What you hear or see</th><th>Check</th></tr></thead>
        <tbody>
          <tr><td>Build error "undefined reference to spi_…"</td><td>Edit 6.1: <code>hardware_spi</code> in <code>CMakeLists.txt</code>.</td></tr>
          <tr><td>Silence, nothing on VOUTB</td><td>Is <code>init_thunk_dma()</code> called in <code>main()</code> (6.6)? DAC VDD on 3V3, VSS and LDAC on ground.</td></tr>
          <tr><td>Burst on the scope, no sound</td><td>Volume, or the jack on VOUTA instead of VOUTB.</td></tr>
          <tr><td>Monitor goes black after 6.6</td><td><code>init_thunk_dma()</code> placed before <code>initVGA()</code>: it must come after.</td></tr>
          <tr><td>One click at startup</td><td>Normal: the DAC jumps to its middle level when the program starts.</td></tr>
        </tbody>
      </table></div>
      <h4>Try this</h4>
      <p>Scope VOUTB and trigger on a hit to capture one thunk: a report figure. In <code>build_thunk_table</code>, change <code>110.0f + 220.0f</code> to <code>220.0f + 440.0f</code> for a higher "tock".</p>
      {fullfile(6)}
    </div>''')

# CHECKOFF + WORDS (reuse existing, with prompt-log note)
chk=grab('    <!-- CHECKOFF -->','    <!-- WORD LIST -->',include_end=False)
chk=chk.replace('Flash with <code>STEP 5</code> and <code>GRAVITY</code> and <code>BOUNCINESS</code> back at 0.37 and 0.5.','Flash the step 6 code with <code>GRAVITY</code> and <code>BOUNCINESS</code> back at 0.37 and 0.5.')
if 'Log the AI use' not in chk: chk=chk.replace('<p>Afterwards, write in the lab notebook:','''<h4>Log the AI use</h4>
      <p>The report needs a prompt log for any AI-generated code: words exchanged, and how many additions, deletions and modifications were suggested and accepted. This guide's changes came from Claude. The tally at the top of each step ("N edits · X lines added, Y removed") gives you the suggested numbers; note which you used as given and which you changed.</p>
      <p>Afterwards, write in the lab notebook:''')
words=grab('    <!-- WORD LIST -->','  </section>',include_end=False)
W.append('\n'+chk+words+'  </section>\n\n')
new_w1=''.join(W)
for sid,t in BIG.items():
    k=new_w1.index(f'id="{sid}"'); k=new_w1.index('</p>',k)+4
    new_w1=new_w1[:k]+f'\n      <div class="bigidea"><b>The big idea</b> {t}</div>'+new_w1[k:]
for h,t in CONCEPT.items():
    assert new_w1.count(h)==1, h
    new_w1=new_w1.replace(h, h+f'\n      <div class="simple"><b>In simple words</b> {t}</div>')

a=doc.index('  <!-- ============================ WEEK 1 ')
b=doc.index('  <!-- ============================ WEEK 2 ')
doc=doc[:a]+new_w1+doc[b:]

css='''
/* edit cards */
.legend{display:flex;flex-wrap:wrap;gap:8px 18px;margin:0 0 18px;font-family:"Archivo",sans-serif;font-size:13px;color:var(--ink-2);align-items:center}
.legend>span{display:flex;gap:6px;align-items:center}
.op{font-family:"Archivo",sans-serif;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:1px 7px;border-radius:2px;white-space:nowrap}
.op.add{background:var(--good-soft);color:var(--good)}
.op.del{background:var(--bad-soft);color:var(--bad)}
.op.chg{background:var(--warn-soft);color:var(--warn)}
.tally{font-family:"Archivo",sans-serif;font-size:13.5px;color:var(--ink-2)}
.edit{border:1px solid var(--rule);background:var(--paper);margin:0 0 16px;padding:12px 14px 4px}
.edit-h{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline;margin-bottom:6px;font-family:"Archivo",sans-serif}
.edit-h b{font-size:15px}
.edit-n{font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--accent);font-weight:500}
.fname{margin-left:auto;font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--ink-3)}
.where{font-size:15px;margin:0 0 8px}
.edit .lbl{font-family:"Archivo",sans-serif;font-size:11.5px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);margin:6px 0 3px}
pre.code{padding:8px 0;font-size:12.5px;line-height:1.5;margin:0 0 10px}
pre.code .l{display:block;padding:0 12px;white-space:pre;min-height:1.5em}
pre.code .add{background:var(--good-soft)}
pre.code .del{background:var(--bad-soft);color:var(--ink-2)}
pre.code .ctx{color:var(--ink-3)}
pre.code .skip{color:var(--ink-3);font-style:italic}
.l.ctx.inline{display:inline;font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--ink-3);background:var(--code-bg);padding:1px 6px}
.why{font-size:15px;border-top:1px dashed var(--rule);padding-top:8px;margin-top:4px}
.why>b{display:block;font-family:"Archivo",sans-serif;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);margin-bottom:4px}
.why p,.why ul,.why ol{margin:0 0 10px}
details.full{margin:10px 0 0;border:1px solid var(--rule)}
details.full summary{cursor:pointer;padding:8px 12px;font-family:"Archivo",sans-serif;font-size:13.5px;font-weight:600;color:var(--accent)}
details.full pre.code.full{margin:0;border:0;border-top:1px solid var(--rule);padding:12px 14px;max-height:520px;overflow:auto;white-space:pre}
'''
if '/* edit cards */' not in doc: doc=doc.replace('/* week 1 walkthrough */', css.strip()+'\n\n/* week 1 walkthrough */',1)
# red tokens in all three palettes
if '--bad-soft:' not in doc:
    doc=doc.replace('  --good-soft:#E1EBDB;\n','  --good-soft:#E1EBDB;\n  --bad:#A33A2E;\n  --bad-soft:#F4E0DC;\n',1)
    doc=doc.replace('--good-soft:#1B2718;','--good-soft:#1B2718; --bad:#E8857A; --bad-soft:#321C1A;')
assert doc.count('--bad-soft:')==3, doc.count('--bad-soft:')
doc=doc.replace('<p>Rotary encoder moves a number on screen. One ball bounces off one peg with a DMA thunk. Written as a five-step walkthrough.</p>',
                '<p>Rotary encoder moves a number on screen. One ball bounces off one peg with a DMA thunk. Six steps from the course demo, every edit shown.</p>')
PWCSS='''/* plain-words boxes */
.bigidea{border-left:4px solid var(--accent);background:var(--accent-soft);padding:12px 16px;margin:4px 0 22px;font-size:16.5px;line-height:1.55}
.bigidea b,.simple b{display:block;font-family:"Archivo",sans-serif;font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--accent-ink);margin-bottom:3px}
.simple{background:var(--accent-soft);border-radius:4px;padding:9px 13px;margin:0 0 12px;font-size:15.5px;line-height:1.55}'''
if '/* plain-words boxes */' not in doc: doc=doc.replace('/* week 1 walkthrough */', PWCSS+'\n\n/* week 1 walkthrough */',1)
open(os.environ.get('GEN_OUT',GUIDE),'w').write(doc)
print('ok', len(doc))
