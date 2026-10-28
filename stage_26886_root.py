#!/usr/bin/env python3
"""Seal the 26886 handoff root against successful compiled 26885 authority."""
from pathlib import Path
import hashlib,sys
R=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def man(n):
 out={}
 for line in (R/n).read_text().splitlines():
  h,k=line.split('  ',1);assert len(h)==64 and k not in out
  out[k]=h
 return out
old=man('26886_BASE_26885_FULL_APP.sha256');new=man('26886_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=man('26886_UNCHANGED_PROTECTED.sha256')
allow=(R/'26886_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(old)==len(new)==2010 and len(protected)==2008 and len(allow)==2
assert allow==sorted(set(allow))
assert set(allow)=={'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp','app/version.properties'}
assert set(old)==set(new) and {k for k in old if old[k]!=new[k]}==set(allow)
assert set(protected)==set(old)-set(allow)
assert all(old[k]==new[k]==v for k,v in protected.items())
assert not (R/'26886_DELETIONS.txt').read_bytes()
base=R/'handoff_payload_26886'
actual={'app/'+f.relative_to(base/'app').as_posix() for f in (base/'app').rglob('*') if f.is_file()}
assert actual==set(allow) and all(sha(base/k)==new[k] for k in allow)
assert man('26886_PAYLOAD_SHA256.txt')=={'handoff_payload_26886/'+k:new[k] for k in allow}
assert (R/'TRIGGER_26886.txt').read_bytes()==b'RUN_26886_B_ON_WRONSKI_CHROMA_NOISE_ALIAS_V1\nREPAIR_26886_ACTIONS_40630270318_RESERVED_SAMPLE_GLSL_V5\n'
w=(R/'.github/workflows/build-26886-iris-rawr.yml').read_text()
assert "      - 'TRIGGER_26886.txt'" in w and "      - 'TRIGGER_26885.txt'" not in w
assert w.count('bash build_26886_iris_rawr.sh')==1 and 'bash build_26885_iris_rawr.sh' not in w
assert 'sha256sum -c 26885_GENERATED_BUILD_SHA256.txt' in w and 'sha256sum -c 26886_GENERATED_BUILD_SHA256.txt' in w
assert 'sha256sum build_26885_iris_rawr.sh' in w and '2138db01cbfb3a8421c12e54ba29d4f0a893d1cdd4a219ee34a40a4dc0c54379' in w
assert "test -f TRIGGER_26886.txt && grep -Fx 'RUN_26886_B_ON_WRONSKI_CHROMA_NOISE_ALIAS_V1'" in w
for n in ('generate_26886_build.py','stage_26886_root.py','verify_26886_candidate.py','verify_26886_patches.py','verify_26886_semantics.py','verify_26886_expanded_glsl.py','regressions/26886_chroma_controls.py','regressions/26886_successor_contract.py','regressions/26886_historical_scope_all_stages.py'):
 assert (R/n).is_file(),('missing successor validator',n)
assert '2138db01cbfb3a8421c12e54ba29d4f0a893d1cdd4a219ee34a40a4dc0c54379' in (R/'generate_26886_build.py').read_text()
package=man('26886_HANDOFF_HASHES.sha256')
assert all((R/k).is_file() and sha(R/k)==v for k,v in package.items())
actual_upload=set((R/'26886_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
assert actual_upload==set(package)|{'26886_HANDOFF_HASHES.sha256','26886_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert all(not k.startswith('app/') for k in actual_upload)
assert not any(x in k for k in actual_upload for x in ('__pycache__','.pyc','.pyo'))
assert 'build_26886_iris_rawr.sh' not in actual_upload
assert all(not p.is_file() or p.suffix.lower()!='.apk' for p in R.rglob('*'))
print('PASS 26886 three-stage strict 2010->2010 two-file source 2008 unchanged, root SHA/trigger/manifests')
