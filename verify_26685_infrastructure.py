#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26685_infrastructure.py BUILD WORKFLOW')
b=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text();marker='\nverify_package\nverify_scope\nobtain_authority\n';start=b.find(marker)
if start<0:raise SystemExit('FAIL authoritative invocation block missing')
inv=b[start:]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shader_invariance','verify_successful_26684_mechanics','prepare_inherited_glslang_for_native','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','26685 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for tok in order:
 n=inv.find(tok,pos+1)
 if n<0:raise SystemExit('FAIL build invocation order token '+tok)
 pos=n
for tok in ['experimental-clean-photon-rebuild','build-26685-r1-spektra-verified-autodiscovery-native-geometry.yml','handoff_payload_26685/**','actions/upload-artifact@v4']:
 if tok not in w:raise SystemExit('FAIL workflow token '+tok)
for tok in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','resolve_glslang_compiler()','prepare_inherited_glslang_for_native()','export IRIS26681_SPEKTRA_GLSLANG="$compiler"','"$compiler" --version']:
 if tok not in b:raise SystemExit('FAIL inherited native glslang repair '+tok)
setup=inv.find('prepare_inherited_glslang_for_native');native=inv.find('buildCMakeDebug[arm64-v8a]');assemble=inv.find('./gradlew :app:assembleDebug')
if not (0<=setup<native<assemble):raise SystemExit('FAIL compiler/build order')
for tok in ['AUTH_26684_BUILD_SCRIPT_BLOB="89af94ceabcdb27b3cdcae61934998583606767b"','AUTH_26684_WORKFLOW_BLOB="af232a1cd701379bbc4db519a37d079f839d05c5"','MECHANICS_AUTHORITY_COMMIT="5ebcacea589af9fd6e00514f135a40af43d786c0"']:
 if tok not in b:raise SystemExit('FAIL successful 26684 mechanics pin '+tok)
print('PASS 26685 infrastructure: exact successful 26684 R1 mechanics pinned; compiler/build ordering and native-glslang repair retained')
