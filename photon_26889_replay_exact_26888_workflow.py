#!/usr/bin/env python3
"""Execute original successful 26888 ancestor generator steps literally, pinned.

Do not substitute a new handcrafted 26871..26888 workflow: this source itself
is the exact pre-guard workflow of successful run 40954102038.
"""
from pathlib import Path
import hashlib, subprocess
r=Path(__file__).resolve().parent
old=r/'.github/workflows/build-26888-iris-rawr.yml'
assert old.is_file(), 'original successful predecessor workflow missing'
content=old.read_bytes()
assert hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()=='b5eaed8ca6399c4ac4c7266e5a059fb0146fcfcf', '26888 exact successful workflow blob drift'
s=content.decode()
a='      - name: Reconstruct the exact successful 26881 runner then derive 26882\n        shell: bash\n        run: |\n'
b='      - name: Preserve exact inherited GLSL cleanup guard\n'
assert s.count(a)==1 and s.count(b)==1
body=s.split(a,1)[1].split(b,1)[0]
assert body and all(line.startswith('          ') or not line for line in body.splitlines()),'non-literal unexpected Actions YAML indentation'
script='\n'.join(line[10:] if line.startswith('          ') else '' for line in body.splitlines())+'\n'
assert script.startswith('set -euo pipefail\n')
assert 'python3 -S generate_26888_build.py .' in script
assert 'sha256sum -c 26888_GENERATED_BUILD_SHA256.txt' in script
assert 'python3 -S regressions/26888_successor_contract.py --generated' in script
assert 'bash build_26888_iris_rawr.sh' not in script
assert 'test "$(sha256sum build_26887_iris_rawr.sh' in script
subprocess.run(['bash','-euo','pipefail','-c',script],cwd=r,check=True)
assert hashlib.sha256((r/'build_26888_iris_rawr.sh').read_bytes()).hexdigest()=='5e9bc28287ba38099390b9cad99168c314e3058473e9924137aaf2f02d7f4753'
# Successful 26888 separate GLSL cleanup was an independent real workflow step:
section=s.split(b,1)[1].split('      - name: Run inherited guarded 17-stage 26888 build',1)[0]
assert section.startswith('        shell: bash\n        run: |\n')
g=section.split('        run: |\n',1)[1]
assert all(line.startswith('          ') or not line for line in g.splitlines())
guard='\n'.join(line[10:] if line.startswith('          ') else '' for line in g.splitlines())+'\n'
assert 'python3 -S guard_26854_accidental_glsl.py' in guard
subprocess.run(['bash','-euo','pipefail','-c',guard],cwd=r,check=True)
print('PASS: exact successful 26888 predecessor workflow generation & GL cleanup guard replay')
