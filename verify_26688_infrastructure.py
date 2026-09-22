#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26688_infrastructure.py BUILD WORKFLOW')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text(); root=Path(sys.argv[1]).resolve().parent
marker='\nverify_package\nverify_scope\nobtain_authority\n'; start=b.find(marker)
if start<0: raise SystemExit('FAIL authoritative invocation block missing')
inv=b[start:]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26687_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','26688 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for tok in order:
    n=inv.find(tok,pos+1)
    if n<0: raise SystemExit('FAIL build invocation order token '+tok)
    pos=n
for tok in ['experimental-clean-photon-rebuild','build-26688-r1-spektra-cpu-raw-frontend.yml','handoff_payload_26688/**','actions/upload-artifact@v4']:
    if tok not in w: raise SystemExit('FAIL workflow token '+tok)
for tok in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','resolve_glslang_compiler()','export IRIS26681_SPEKTRA_GLSLANG="$compiler"','"$compiler" -V "$AFTER/app/src/main/cpp/spektra/SpektraRawDevelop.comp"']:
    if tok not in b: raise SystemExit('FAIL pinned glslang/order contract '+tok)
for tok in ['AUTH_26687_BUILD_SCRIPT_BLOB="2ef3d5a0e90f8b912a29d49427a94895fec12d57"','AUTH_26687_WORKFLOW_BLOB="0d2de3abab3086d96876bfbb0bb393c7fbef46b9"','MECHANICS_AUTHORITY_COMMIT="641fa7062cf70e53aef9e72bf56c0f2b5bc96b0b"','BASE_ARTIFACT_ID="10717405771"','BASE_ARTIFACT_SHA="40204ba0ecdb9a041915ddd6a998faaf7e85788f4357b09b71f5f50f244d565f"','BASE_TAR_SHA="19295a3b333e6820e4d15817dedc95b8951bf6b13581e0f8bce31a3a12c583bd"']:
    if tok not in b: raise SystemExit('FAIL successful 26687 mechanics/runtime pin '+tok)
# Exact successful-mechanics path names are themselves a permanent regression after the 26687 R1 filename failure.
for tok in ['${MECHANICS_AUTHORITY_COMMIT}:build_26687_r1_spektra_isolated_mode_owner.sh','${MECHANICS_AUTHORITY_COMMIT}:.github/workflows/build-26687-r1-spektra-isolated-mode-owner.yml']:
    if tok not in b: raise SystemExit('FAIL successful 26687 mechanics path '+tok)
for stale in ['build_26687_r1_spektra_verified_autodiscovery_native_geometry.sh','.github/workflows/build-26687-r1-spektra-verified-autodiscovery-native-geometry.yml']:
    if stale in b: raise SystemExit('FAIL stale mechanics path returned '+stale)
# Runtime CMake is intentionally inside the candidate; build/workflow infrastructure ordering is not broadened.
changed=set((root/'R1_26688_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
expected_runtime_build={'app/src/main/cpp/CMakeLists.txt'}
if {p for p in changed if p.endswith('build.gradle') or p.endswith('settings.gradle') or p.endswith('gradle.properties')}:
    raise SystemExit('FAIL Gradle infrastructure entered runtime scope')
if expected_runtime_build-{p for p in changed}: raise SystemExit('FAIL intentional native source-selection CMake delta missing')
if 'app/src/main/cpp/spektra/SpektraRawDevelop.comp' in changed: raise SystemExit('FAIL dormant inherited RAW shader unexpectedly changed')
print('PASS 26688 infrastructure: exact successful 26687 R1.1 mechanics/runtime authority pinned; compiler/build invocation order preserved; only intended native source-selection CMake runtime delta added')
