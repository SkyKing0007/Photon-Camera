#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26683_infrastructure.py BUILD WORKFLOW')
b=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text();marker='\nverify_package\nverify_scope\nobtain_authority\n';start=b.find(marker)
if start<0:raise SystemExit('FAIL authoritative invocation block missing')
inv=b[start:]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shader_invariance','verify_successful_26682_mechanics','prepare_inherited_glslang_for_native','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','26683 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for tok in order:
 n=inv.find(tok,pos+1)
 if n<0:raise SystemExit('FAIL build invocation order token '+tok)
 pos=n
for tok in ['experimental-clean-photon-rebuild','build-26683-r1-spektra-end-to-end-owner.yml','handoff_payload_26683/**','actions/upload-artifact@v4']:
 if tok not in w:raise SystemExit('FAIL workflow token '+tok)
# Exact successful 26682 R1.1 repair: inherited native CMake consumes this pinned compiler path.
for tok in ['GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','resolve_glslang_compiler()','prepare_inherited_glslang_for_native()','export IRIS26681_SPEKTRA_GLSLANG="$compiler"','"$compiler" --version']:
 if tok not in b:raise SystemExit('FAIL successful-26682 native glslang token '+tok)
setup=inv.find('prepare_inherited_glslang_for_native');native=inv.find('buildCMakeDebug[arm64-v8a]');assemble=inv.find('./gradlew :app:assembleDebug')
if not (0<=setup<native<assemble):raise SystemExit('FAIL pinned glslang setup order')
for tok in ['AUTH_26682_BUILD_SCRIPT_BLOB="2d92d9fc1122a2ef9c8d1b1223101fe08c780083"','AUTH_26682_WORKFLOW_BLOB="9cbf2a3b4622041672ffd7f0387677e56345766d"','MECHANICS_AUTHORITY_COMMIT="807d51185046298761edba21e1a8311bec8bd59a"']:
 if tok not in b:raise SystemExit('FAIL successful 26682 mechanics pin '+tok)
print('PASS 26683 infrastructure: exact successful 26682 R1.1 compiler/build ordering and pinned native-glslang repair retained')
