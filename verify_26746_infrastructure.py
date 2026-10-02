#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26746_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
auth=load('26746_SEALED_26745_INFRASTRUCTURE_AUTHORITY.sha256'); assert len(auth)==9
for p,h in auth.items():
 q=Path(p); assert q.exists(),('missing sealed 26745 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26745 mechanics authority drift',p)
for t in ['ROOT_ACTIONS_AUTHORITY_COMMIT="a8473f519a8d77926510a8a01a5658942dcf9645"','HIST26743_ACTIONS_AUTHORITY_COMMIT="c927843ea78f58f632082758142ee061a1c05166"','HIST26743_ARTIFACT_NAME="photon-26743-visible-highlight-neutrality"','HIST26743_ARTIFACT_SHA="051fd7ef96e46f176e9e9e72cb55ecf14fa670177075aab6f3d39b60da75119f"','HIST26743_TAR_SHA="7d7fe097d3a978813a78da8bfcbc883bbf2f2855f729b88d376b532b14f4f5c7"','HIST26743_FULL_MANIFEST_SHA="cf5c15be188f17aaff3761be8b6dd1c254ccdf902a7c6cd1dc039287d97d7965"','HIST26743_INFRA_MANIFEST_SHA="6a9d3790025931a6415841e0af048123e00e95684731e9c6c134260fc19f20af"','ROOT_ARTIFACT_NAME="photon-26745-bright-fringe-hue-authority"','ROOT_ARTIFACT_SHA="8660f67ec30ddb2a8945de387f3ae19270f4679684698dcccc6faf34b093e834"','ROOT_TAR_SHA="a915d476cf2832e9f8874735106230f73176c27fb7c66018fab105245e8a1e89"','VERSION_NAME="0.9726746"','VERSION_BUILD="26746"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"']:
 assert t in s,t
marker='# IRIS_26746_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26745_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26746 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26746 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26745 stage order drift',t); pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26746_extreme_flattened_highlight_veto.sh']:
 assert t in s+w,t
assert 'verify_26745_shaders.py "$ROOT" "$BASE" "$BASE" --compiler "$IRIS26746_GLSLANG"' not in s
for t in [
 'obtain_inherited_26745_shader_authority',
 'verify_26743_shaders.py "$ROOT" "$HIST26743_BASE" "$HIST26743_BASE" --compiler "$IRIS26746_GLSLANG"',
 'verify_26745_shaders.py "$ROOT" "$HIST26743_BASE" "$BASE" --compiler "$IRIS26746_GLSLANG"',
 'verify_26746_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26746_GLSLANG"',
 '26745_BASE_26743_FULL_APP.sha256',
 '26745_EXACT_26743_CANDIDATE_AUTHORITY.sha256',
 '26745_SEALED_26743_INFRASTRUCTURE_AUTHORITY.sha256']:
 assert t in s,t
# Permanent regression for the failed first 26746 Actions attempt: the sealed 26745
# verifier's base role is 26743, never the current 26745 base. Check only the
# real compiler function so earlier structural verifier calls cannot confuse ordering.
compile_block=s[s.index('compile_modified_runtime_shaders(){'):s.index('compile_spektra_raw_shader(){')]
assert compile_block.index('verify_26743_shaders.py "$ROOT" "$HIST26743_BASE" "$HIST26743_BASE"') < compile_block.index('verify_26745_shaders.py "$ROOT" "$HIST26743_BASE" "$BASE"') < compile_block.index('verify_26746_shaders.py "$ROOT" "$BASE" "$AFTER"')
# IRIS_26746_R2_SED_DELIMITER_REGRESSION: failed R1 Actions after successful assemble because
# the '/' delimiter collided with the literal 'Sabre/VGN' in replacement text.
unsafe_sed = "sed -i 's/APK JNI CONTRACT:.*/APK JNI CONTRACT: PASS (full assemble APK present; Super Res remains shared Sabre/VGN chroma owner; true2x native publication compiled in both ABIs)/'"
safe_sed = "sed -i 's#APK JNI CONTRACT:.*#APK JNI CONTRACT: PASS (full assemble APK present; Super Res remains shared Sabre/VGN chroma owner; true2x native publication compiled in both ABIs)#'"
assert unsafe_sed not in s
assert safe_sed in s
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
assert '"$(find handoff_payload_26746 -type f|wc -l)" -eq 2' in s
assert '"$(wc -l < 26746_RUNTIME_CHANGED_PATHS.txt)" -eq 2' in s
print('PASS 26746 R2 infrastructure: successful-26745 stage/toolchain/order unchanged; wrong-role shader replay rejected; post-assemble sed delimiter regression fixed; exact 26743->26745 then 26745->26746 shader replay preserved; both-ABI native stage preserved; no backup/commit/push')
