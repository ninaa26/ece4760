"""Put freshly generated week 1 steps 2-6 into the guide, leaving everything else alone.

gen.py rebuilds the whole week 1 tab from its own templates, but steps 0-1, the
checkoff table and the other tabs have been edited by hand (and by other
sessions) since. So never publish gen.py's output directly: generate to a temp
file, then splice only the steps 2-6 region into the live guide with this.

    GEN_OUT=/tmp/gen_out.html python3 gen.py
    python3 splice.py /tmp/gen_out.html
"""
import os, sys
S = os.path.dirname(os.path.abspath(__file__))
GUIDE = os.path.join(S, '..', '..', 'docs', 'ECE4760_galton-lab-field-guide.html')
A = '    <div class="step" id="w1-s2">'
B = '    <!-- CHECKOFF -->'
new = open(sys.argv[1]).read()
doc = open(GUIDE).read()
doc = doc[:doc.index(A)] + new[new.index(A):new.index(B)] + doc[doc.index(B):]
open(GUIDE, 'w').write(doc)
print('spliced steps 2-6 into', os.path.normpath(GUIDE))
