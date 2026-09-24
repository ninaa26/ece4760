import sys, os, shutil, subprocess, importlib.util
S=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location('edits', os.path.join(S,'edits.py')); E=importlib.util.module_from_spec(spec); spec.loader.exec_module(E)
ROOT=os.path.abspath(os.path.join(S,'..','..'))
DEMO=os.environ.get('DEMO') or next(p for p in [os.path.join(ROOT,'Hunter-Adams-RP2040-Demos/VGA_Graphics/Animation_Demo'), os.path.expanduser('~/Developer/Active/ECE4760/Hunter-Adams-RP2040-Demos/VGA_Graphics/Animation_Demo')] if os.path.isdir(p))
strip=lambda t:'\n'.join(l.rstrip() for l in t.split('\n'))  # trailing spaces are invisible in the guide
files={'c':strip(open(DEMO+'/animation.c').read()),'cmake':strip(open(DEMO+'/CMakeLists.txt').read())}
def once(txt,a,eid):
    n=txt.count(a)
    if n!=1: sys.exit(f'{eid}: anchor found {n} times: {a[:60]!r}')
    return txt.index(a)
def apply(e):
    f=e.get('file','c'); t=files[f]; op=e['op']
    if op in('after','before','replace','delete'):
        i=once(t,e['anchor'],e['id']); a=e['anchor']
        if op=='after': t=t[:i+len(a)]+e['new']+t[i+len(a):]
        elif op=='before': t=t[:i]+e['new']+t[i:]
        elif op=='replace': t=t[:i]+e['new']+t[i+len(a):]
        else: t=t[:i]+t[i+len(a):]
    else:
        i=once(t,e['start'],e['id']); j=once(t,e['end'],e['id']); assert j>i
        e['removed']=t[i:j]
        t=t[:i]+(e.get('new','') if op=='replace_range' else '')+t[j:]
    files[f]=t
os.makedirs(S+'/out/stages',exist_ok=True)
open(S+'/out/stages/animation_step1.c','w').write(files['c'])
for n in sorted(E.STEPS):
    for e in E.STEPS[n]: apply(e)
    open(f'{S}/out/stages/animation_step{n}.c','w').write(files['c'])
    open(f'{S}/out/stages/CMakeLists_step{n}.txt','w').write(files['cmake'])
    if '--build' in sys.argv:
        proj=f'{S}/out/proj/Lab2Step{n}'
        if os.path.exists(proj): shutil.rmtree(proj)
        shutil.copytree(DEMO,proj)
        open(proj+'/animation.c','w').write(files['c']); open(proj+'/CMakeLists.txt','w').write(files['cmake'])
        r=subprocess.run([os.path.join(ROOT,'build.sh'),proj],capture_output=True,text=True)
        out=r.stdout+r.stderr
        warns=[l for l in out.splitlines() if 'animation.c' in l and ('warning' in l or 'error' in l)]
        print(f'step {n}: exit {r.returncode}, {len(warns)} warnings/errors', *warns[:8], sep='\n  ')
