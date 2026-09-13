#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
if len(sys.argv)!=5 or sys.argv[3]!='--out': raise SystemExit('usage: verify_26636_r1_shaders.py BASE CAND --out OUT')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); O=Path(sys.argv[4]); O.mkdir(parents=True,exist_ok=True); pkg=Path(__file__).resolve().parent
changed=set(x for x in (pkg/'R1_26636_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x)
assert not any('/shaders/' in x for x in changed),'26636 must not modify shaders'
def sh(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app/src/main/assets/shaders').rglob('*')) if p.is_file()}
a,b=sh(B),sh(C); assert a==b,'shader universe changed despite zero shader allowlist'
(O/'R1_26636_RUNTIME_EXPANDED_SHADERS.sha256').write_text('')
(O/'R1_26636_SHADER_VERIFICATION.json').write_text(json.dumps({'count':0,'compiler':None,'status':'NOT_APPLICABLE_NO_MODIFIED_GLSL'},indent=2,sort_keys=True)+'\n')
print(f'PASS 26636 shader gate NOT APPLICABLE: 0 modified GLSL; complete shader universe invariant files={len(a)}')
