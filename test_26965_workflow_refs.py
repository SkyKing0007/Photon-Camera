#!/usr/bin/env python3
"""No predecessor 26964 historical/26904 regression step or real compiler gate weakened."""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
old=(R/'26964_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_bytes()
assert hashlib.sha256(old).hexdigest()=='f5a7febd71192cf262e29862b95111b954d1384684de399e72ac1cf615a725ad'
new=(R/'.github/workflows/build-26965-change-aware.yml').read_text()
s=old.decode()
start='      - name: Fail closed on original successful 26923 and current 26926 executable references and three-stage seal'
cut='      - name: Fetch only exact successful 26963 Actions artifact 14498242333'
assert start in s and cut in s
prefix=s[s.index(start):s.index(cut)]
assert prefix in new and new.count(prefix)==1,'original 26964 historical steps mutated'
assert new.count('actions/upload-artifact@v4')==1
for q in ('runs-on: ubuntu-24.04','branches:\n      - experimental-clean-photon-rebuild','      - TRIGGER_26965.txt',
  'python3 -S build_26965_incremental.py seal','python3 -S test_26965_source.py --payload',
  'python3 -S test_26965_hdrq_pipeline.py --payload','python3 -S test_26965_patches.py --payload',
  'python3 -S test_26965_sealed_negatives.py','python3 -S build_26965_incremental.py fetch',
  'python3 -S build_26965_incremental.py prepare-base','python3 -S test_26964_source.py --live',
  'bash compile_26964_shaders.sh','bash compile_26904_shaders_v2.sh',
  'python3 -S verify_26904_v3_cmake_handoff.py --handoff','python3 -S build_26965_incremental.py install',
  'bash compile_26965_shaders.sh','python3 -S build_26965_incremental.py verify-compiled',
  './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
  'python3 -S verify_26906_native_cache.py postflight','python3 -S build_26965_incremental.py finalize',
  'actions/cache/restore@v4','actions/cache/save@v4','IrisCamera-0.9726965-26965-iris-rawr-debug.apk',
  'photon-26965-26964-rawr-hdrq-quality-protected'):
 assert q in new,q
assert '      - TRIGGER_26964.txt' not in new.split('jobs:',1)[0]
assert not re.search(r'(?m)^\s*-\s*dev\s*$',new)
if (R/'gradlew').is_file():
 names=set(re.findall(r'\bpython3\s+-S\s+([\w./-]+\.py)',new))
 names|=set(re.findall(r'\bbash\s+([\w./-]+\.sh)',new))
 absent=sorted(p for p in names if not (R/p).is_file())
 assert not absent,'unresolved old/current workflow executables: '+str(absent[:12])
print('PASS 26965 exact 26964 historical prefix and full pinned shader/SPIR-V/NDK/Kotlin/Java/assemble gates')
