#!/usr/bin/env python3
"""
Makes EOM detection tolerant of lost bursts (fixes live URL / mic streams that never "finish" an alert).

  python patch_eom.py easyweb.html              -> easyweb-eomfix.html
  python patch_eom.py easyweb-obs.html out.html -> out.html

Works on the original file and on the OBS build.
"""
import sys, pathlib
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "easyweb.html")
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name(src.stem + "-eomfix.html")
h = src.read_text(encoding="utf-8")
if "/*eomfix*/" in h: sys.exit("Already patched.")

def rep(old, new):
    global h
    n = h.count(old)
    if n != 1:
        sys.exit(f"Could not patch: anchor found {n} times (expected 1):\n  {old[:100]!r}")
    h = h.replace(old, new)

# 1) decoder: remember when the last EOM burst was heard
rep('inv=0,eom=0,fast=false;const S=[0,0,0,0];', 'inv=0,eom=0,le=0,fast=false;const S=[0,0,0,0];/*eomfix*/')
# 2) a stale burst count (older than 8 s) is dropped, so one lost burst can't poison the next alert
rep('if(msg==="NNNN"){eom++;const f=eom===3;',
    'if(msg==="NNNN"){if(eom>0&&n-le>fs*8)eom=0;eom++;le=n;const f=eom===3;')
# 3) if 1 or 2 EOM bursts were heard and no more follow within 3.5 s, the EOM is final anyway
rep('  n++}}}\n/*B*/',
    '  n++}\n if(eom>0&&n-le>fs*3.5){eom=0;onE({type:"NNNN",raw:"NNNN",final:true,to:true,n:le,t:le/fs})}}}\n/*B*/')
# 4) the burst finder works from the real bursts only, it must ignore this synthetic "final"
rep('m=>b.push({k:"E",raw:"NNNN",t:m.t-20*8/520.8333,e:m.t}));',
    'm=>{if(!m.to)b.push({k:"E",raw:"NNNN",t:m.t-20*8/520.8333,e:m.t})});')
# 5) live recording ends measured from the last burst, not from the moment the timeout fired
rep('if(M.rec)M.rec.end=M.rec.n;else if(M.last',
    'if(M.rec)M.rec.end=M.rec.n-Math.max(0,M.total-(m.n||M.total));else if(M.last')
# 6) imported files: let the timeout run after the last sample
rep('for(let i=0;i<x.length;i+=16384)dd.push(x.subarray(i,i+16384));',
    'for(let i=0;i<x.length;i+=16384)dd.push(x.subarray(i,i+16384));dd.push(new Float32Array(Math.ceil(buf.sampleRate*4)));')
out.write_text(h, encoding="utf-8"); print("Wrote", out)
