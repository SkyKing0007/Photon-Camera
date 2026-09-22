#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26687_infrastructure.py BUILD WORKFLOW')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text(); marker='\nverify_package\nverify_scope\nobtain_authority\n'; start=b.find(marker)
if start<0: raise SystemExit('FAIL authoritative invocation block missing')
inv=b[start:]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26686_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','26687 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for tok in order:
    n=inv.find(tok,pos+1)
    if n<0: raise SystemExit('FAIL build invocation order token '+tok)
    pos=n
for tok in ['experimental-clean-photon-rebuild','build-26687-r1-spektra-isolated-mode-owner.yml','handoff_payload_26687/**','actions/upload-artifact@v4']:
    if tok not in w: raise SystemExit('FAIL workflow token '+tok)
for tok in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','resolve_glslang_compiler()','export IRIS26681_SPEKTRA_GLSLANG="$compiler"','"$compiler" -V "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp"']:
    if tok not in b: raise SystemExit('FAIL pinned glslang contract '+tok)
for tok in ['AUTH_26686_BUILD_SCRIPT_BLOB="85222dd3d3d05c60f37771ae12bd56c3fa3328e4"','AUTH_26686_WORKFLOW_BLOB="8dcdaa6bc131443417563fc1a37d0c6dca3eaa52"','MECHANICS_AUTHORITY_COMMIT="b0620bfc0b750db35b8737e46aa0c5e92083be29"']:
    if tok not in b: raise SystemExit('FAIL successful 26686 mechanics pin '+tok)
for tok in ['build_26686_r1_spektra_native_raw_vulkan_owner.sh','.github/workflows/build-26686-r1-spektra-native-raw-vulkan-owner.yml']:
    if tok not in b: raise SystemExit('FAIL successful 26686 mechanics authority path '+tok)
for stale in ['build_26686_r1_spektra_verified_autodiscovery_native_geometry.sh','.github/workflows/build-26686-r1-spektra-verified-autodiscovery-native-geometry.yml']:
    if stale in b: raise SystemExit('FAIL stale 26685-derived mechanics path '+stale)
# No new CMake/workflow compiler phase: 26687 runtime scope does not include CMake/shader/build.gradle.
for rel in ['app/src/main/cpp/CMakeLists.txt','app/src/main/cpp/spektra/EmbedSpektraSpirv.cmake','app/build.gradle']:
    if rel in Path(Path(sys.argv[1]).parent/'R1_26687_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines(): raise SystemExit('FAIL infrastructure/runtime scope broadened '+rel)
print('PASS 26687 infrastructure: exact successful 26686 mechanics pinned; compiler/build invocation order preserved; infrastructure delta limited to authority/version/scope/regression identities')
