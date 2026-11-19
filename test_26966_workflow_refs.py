#!/usr/bin/env python3
"""Workflow equivalence: exact successful 26965 historical preflight and change-aware building mechanics retained."""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
old=(R/'26965_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
new=(R/'.github/workflows/build-26966-change-aware.yml').read_text()
marker='      - name: Fetch only exact successful 26964 Actions artifact 14543555009'
assert old.count(marker)==1 and new.count('      - name: Fetch only exact successful 26965 Actions artifact 14564574142')==1
p=old.split(marker)[0]
q=new.split('      - name: Seal new 26966 A-only scope and retain 26965 real compiled baseline')[0]
p=p.replace('name: Photon 26965 - 26964-backed RAWR latest HDR+ Quality B OFF motion merge','name: Photon 26966 - 26965-backed Experiment A GPU Sabre Resolve and shadow chroma',1)
p=p.replace('      - TRIGGER_26965.txt','      - TRIGGER_26966.txt',1)
assert p==q,'historical 26965 steps modified or missing'
for token in ('      - TRIGGER_26966.txt','  workflow_dispatch:',"    runs-on: ubuntu-24.04",'python3 -S build_26966_incremental.py seal','python3 -S build_26966_incremental.py fetch','python3 -S build_26966_incremental.py prepare-base','bash compile_26965_shaders.sh','bash compile_26966_shaders.sh','python3 -S build_26966_incremental.py install','python3 -S build_26966_incremental.py verify-compiled','./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace','python3 -S build_26966_incremental.py finalize','actions/upload-artifact@v4','IrisCamera-0.9726966-26966-iris-rawr-debug.apk','photon_26966_outputs/','verify_26904_v3_cmake_handoff.py --handoff','bash compile_26904_shaders_v2.sh'):
 assert token in new, 'missing workflow requirement: '+token
assert '      - TRIGGER_26965.txt' not in new
assert new.count('      - TRIGGER_26966.txt')==1
assert new.count('      - name: One mandatory real 26966 Android NDK dual-ABI Kotlin Java and full app assembleDebug')==1
assert new.index('build_26966_incremental.py fetch')<new.index('build_26966_incremental.py prepare-base')<new.index('bash compile_26965_shaders.sh')<new.index('build_26966_incremental.py install')<new.index('bash compile_26966_shaders.sh')<new.index('build_26966_incremental.py verify-compiled')<new.index('assembleDebug --stacktrace')<new.index('build_26966_incremental.py finalize')<new.index('actions/upload-artifact@v4')
assert hashlib.sha256(old.encode()).hexdigest()=='23c64356dab6c179e1d37344d50e4735df091bfda842b992b54d45e55f76094d'
print('PASS unchanged 26965 historical preflight; guarded 26966 exact-source, shader, NDK, Kotlin/Java/assemble, output publication mechanics')
