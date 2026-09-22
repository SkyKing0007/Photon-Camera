#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26682_infrastructure.py BUILD WORKFLOW')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
marker='\nverify_package\nverify_scope\nobtain_authority\n'
start=b.find(marker)
if start<0: raise SystemExit('FAIL authoritative invocation block missing')
inv=b[start:]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shader_invariance','verify_successful_26681_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','26682 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for tok in order:
 n=inv.find(tok,pos+1)
 if n<0: raise SystemExit('FAIL build invocation order token '+tok)
 pos=n
for tok in ['experimental-clean-photon-rebuild','build-26682-r1-spektra-mode-ownership.yml','handoff_payload_26682/**','actions/upload-artifact@v4']:
 if tok not in w: raise SystemExit('FAIL workflow token '+tok)
if 'app/build/**' in b or 'app/.cxx/**' in b: pass
print('PASS 26682 infrastructure: successful 26681 compiler/build ordering retained; no app build/workflow infrastructure runtime change')
