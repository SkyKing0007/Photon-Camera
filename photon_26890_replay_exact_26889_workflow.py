#!/usr/bin/env python3
"""Replay the EXACT successful 26889 pre-guard workflow shell steps, literally.
Source Git blob SHA1 pinned to successful commit 17366e5d..., not a rewritten approximation.
"""
import pathlib,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parent
wf=R/'.github/workflows/build-26889-iris-rawr.yml'
assert wf.is_file(), 'successful 26889 workflow missing'
b=wf.read_bytes()
assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()=='cb70bb862054e3c3fedc6982bdd6b9685d9cea4f','actual successful 26889 predecessor workflow changed'
s=b.decode('utf-8')
steps=(
 ('Replay exact SHA-pinned successful 26888 historical setup and GLSL cleanup',
  'Derive and seal exact-successor guarded 26889 runner'),
 ('Derive and seal exact-successor guarded 26889 runner',
  'Run inherited guarded 17-stage 26889 build')
)
for before,after in steps:
 start=f'      - name: {before}\n        shell: bash\n        run: |\n'
 end=f'      - name: {after}\n'
 assert s.count(start)==1 and s.count(end)==1,(before,'stage anchors missing')
 segment=s.split(start,1)[1].split(end,1)[0]
 assert segment and all(ln.startswith('          ') or not ln for ln in segment.splitlines()),'historical workflow changed indentation'
 exact='\n'.join(ln[10:] if ln.startswith('          ') else '' for ln in segment.splitlines())+'\n'
 assert exact.startswith('set -euo pipefail\n')
 assert 'bash build_26889_iris_rawr.sh' not in exact
 subprocess.run(['bash','-euo','pipefail','-c',exact],cwd=R,check=True)
assert hashlib.sha256((R/'build_26889_iris_rawr.sh').read_bytes()).hexdigest()=='4070c3a0f47fb043d99ad18a1b2d53a629be26891d1147ef9bfc60d790cb7d73'
print('PASS executed BOTH complete exact successful 26889 pre-guard workflow stages and exact Actions runner SHA')
