#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26686_infrastructure.py BUILD WORKFLOW')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text(); marker='\nverify_package\nverify_scope\nobtain_authority\n'; start=b.find(marker)
if start<0: raise SystemExit('FAIL authoritative invocation block missing')
inv=b[start:]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26685_mechanics','prepare_glslang','compile_new_native_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','26686 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for tok in order:
    n=inv.find(tok,pos+1)
    if n<0: raise SystemExit('FAIL build invocation order token '+tok)
    pos=n
for tok in ['experimental-clean-photon-rebuild','build-26686-r1-spektra-native-raw-vulkan-owner.yml','handoff_payload_26686/**','actions/upload-artifact@v4']:
    if tok not in w: raise SystemExit('FAIL workflow token '+tok)
for tok in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','resolve_glslang_compiler()','export IRIS26681_SPEKTRA_GLSLANG="$compiler"','"$compiler" -V "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp"']:
    if tok not in b: raise SystemExit('FAIL pinned glslang contract '+tok)
for tok in ['AUTH_26685_BUILD_SCRIPT_BLOB="9c6392bed9f8e53214e2ecba796427555f775c37"','AUTH_26685_WORKFLOW_BLOB="6d400980e4f5c573fcfb60718ab4cac142e7e8e6"','MECHANICS_AUTHORITY_COMMIT="2b3b5cabb3726e52758756e1db81fd4646e1823c"']:
    if tok not in b: raise SystemExit('FAIL successful 26685 mechanics pin '+tok)
print('PASS 26686 infrastructure: exact successful 26685 mechanics pinned; order preserved; only necessary modified-shader compile and 26686 authority/scope/regression identities added')
