#!/usr/bin/env python3
"""26885 sealed three-stage staging. Exact 26884 successful compiled universe."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def man(n):
 out={}
 for line in (R/n).read_text().splitlines():
  h,k=line.split('  ',1)
  assert len(h)==64 and k not in out
  out[k]=h
 return out
old=man('26885_BASE_26884_FULL_APP.sha256');new=man('26885_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=man('26885_UNCHANGED_PROTECTED.sha256')
allow=(R/'26885_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(old)==2009 and len(new)==2010 and len(allow)==8 and len(protected)==2002
assert allow==sorted(set(allow))
assert set(old)<set(new) and set(new)-set(old)=={'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'}
assert set(allow)=={k for k in set(old)|set(new) if old.get(k)!=new.get(k)}
assert set(protected)==set(old)-set(allow)
assert all(old[k]==new[k]==h for k,h in protected.items())
assert (R/'26885_DELETIONS.txt').read_bytes()==b''
base=R/'handoff_payload_26885'
actual={'app/'+p.relative_to(base/'app').as_posix() for p in (base/'app').rglob('*') if p.is_file()}
assert actual==set(allow),('runtime payload mismatch',actual^set(allow))
assert all(sha(base/k)==new[k] for k in allow)
assert man('26885_PAYLOAD_SHA256.txt')=={'handoff_payload_26885/'+k:new[k] for k in allow}
assert (R/'TRIGGER_26885.txt').read_bytes()==b'RUN_26885_B_ON_WRONSKI_RGB_CHROMA_CONSISTENCY_V2_SCOPE_REPAIR\n'
w=(R/'.github/workflows/build-26885-iris-rawr.yml').read_text()
assert "      - 'TRIGGER_26885.txt'" in w and "      - 'TRIGGER_26884.txt'" not in w
assert w.count('bash build_26885_iris_rawr.sh')==1 and 'bash build_26884_iris_rawr.sh' not in w
assert 'sha256sum -c 26884_GENERATED_BUILD_SHA256.txt' in w
assert 'sha256sum -c 26885_GENERATED_BUILD_SHA256.txt' in w
assert "test -f TRIGGER_26885.txt && grep -Fx 'RUN_26885_B_ON_WRONSKI_RGB_CHROMA_CONSISTENCY_V2_SCOPE_REPAIR'" in w
assert (R/'generate_26885_build.py').is_file() and 'f8aff63b074ee6195d6b137858ad5a3f23cb149a40c9f72cb69b51f315b4679f' in (R/'generate_26885_build.py').read_text()
for n in ('generate_26885_build.py','verify_26885_candidate.py','verify_26885_patches.py','verify_26885_semantics.py','verify_26885_expanded_glsl.py','regressions/26885_successor_contract.py','regressions/26885_actions_40604341240_historical_scope.py','regressions/26885_chroma_controls.py','regressions/26885_wronski_chroma_evidence.py','regressions/26885_universal_pattern_controls.py','regressions/_26885_vector_math.py'):
 assert (R/n).is_file(),('missing guarded validator',n)
package=man('26885_HANDOFF_HASHES.sha256')
assert all((R/k).is_file() and sha(R/k)==h for k,h in package.items())
actual_upload=set((R/'26885_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
expected=set(package)|{'26885_HANDOFF_HASHES.sha256','26885_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert actual_upload==expected,('strict upload scope mismatch',sorted(actual_upload^expected))
assert all(not k.startswith('app/') for k in actual_upload)
assert not any('__pycache__' in k.split('/') or k.endswith(('.pyc','.pyo')) for k in actual_upload)
assert 'build_26885_iris_rawr.sh' not in actual_upload
print('PASS 26885 three-stage exact 8-runtime source/2002 protected, 2009->2010, deterministic hash-and-trigger namespace')
