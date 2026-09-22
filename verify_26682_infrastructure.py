#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26682_infrastructure.py BUILD WORKFLOW')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
marker='\nverify_package\nverify_scope\nobtain_authority\n'
start=b.find(marker)
if start<0: raise SystemExit('FAIL authoritative invocation block missing')
inv=b[start:]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shader_invariance','verify_successful_26681_mechanics','prepare_inherited_glslang_for_native','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','26682 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for tok in order:
 n=inv.find(tok,pos+1)
 if n<0: raise SystemExit('FAIL build invocation order token '+tok)
 pos=n
for tok in ['experimental-clean-photon-rebuild','build-26682-r1-spektra-mode-ownership.yml','handoff_payload_26682/**','actions/upload-artifact@v4']:
 if tok not in w: raise SystemExit('FAIL workflow token '+tok)
# Permanent regression from failed 26682 run 35674183799: inherited CMake still consumes the
# successful-26681 pinned glslang path even when no shader bytes changed.
required_build_tokens=[
 'GLSLANG_VERSION=\"16.5.0\"',
 'GLSLANG_ARCHIVE_SHA=\"b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657\"',
 'resolve_glslang_compiler()',
 'prepare_inherited_glslang_for_native()',
 'export IRIS26681_SPEKTRA_GLSLANG=\"$compiler\"',
 '\"$compiler\" --version',
]
for tok in required_build_tokens:
 if tok not in b: raise SystemExit('FAIL 26682 native glslang regression token '+tok)
setup=inv.find('prepare_inherited_glslang_for_native')
native=inv.find('buildCMakeDebug[arm64-v8a]')
assemble=inv.find('./gradlew :app:assembleDebug')
if not (0 <= setup < native < assemble): raise SystemExit('FAIL 26682 glslang setup must precede native CMake and assemble')
if 'app/build/**' in b or 'app/.cxx/**' in b: pass
print('PASS 26682 infrastructure: successful 26681 compiler/build ordering retained; failed-26682 native glslang environment regression sealed')
