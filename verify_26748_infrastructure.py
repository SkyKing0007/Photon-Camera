#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26748_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
auth=load('26748_SEALED_26747_INFRASTRUCTURE_AUTHORITY.sha256'); assert len(auth)==9
for p,h in auth.items():
 q=Path(p); assert q.exists(),('missing sealed 26747 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26747 mechanics authority drift',p)
for t in [
 'ROOT_ACTIONS_AUTHORITY_COMMIT="c2523a14725a92e1ff85d153578cb4bf9e6fdce2"',
 'ROOT_ARTIFACT_NAME="photon-26747-full-26727-unrecoverable-highlight-authority"',
 'ROOT_ARTIFACT_SHA="ada8732b21276627983850e7fa1d8bdbbcd49b62fa4147c848caaf61816f4108"',
 'ROOT_TAR_SHA="87152a94fa39751431c47c92b8f208c6ae37a3d77266a92ed0d28a30eb0216d1"',
 'HIST26746_ACTIONS_AUTHORITY_COMMIT="58dfdb0d423cad988afcbd4918e673fbac8d2558"',
 'HIST26746_ARTIFACT_NAME="photon-26746-extreme-flattened-highlight-veto"',
 'HIST26746_ARTIFACT_SHA="d0b71cccddd702e3be7d43a10b08c06541913308b11fec779e8d79d0586465a2"',
 'HIST26746_TAR_SHA="d3f9c244bb7fe0d2e519b7633aab9bc35ebec784791394fe55ac8088ddecdf62"',
 'HIST26746_FULL_MANIFEST_SHA="8825a17936a3f10827b3ebb208d71df5934e42f091f8452f05a56a2349d0ab04"',
 'HIST26746_INFRA_MANIFEST_SHA="2747ca3bc6c9064afb43b8e08cd3f928b223bbf7e538d69f9a16b3571bc15b26"',
 'HIST26745_ACTIONS_AUTHORITY_COMMIT="a8473f519a8d77926510a8a01a5658942dcf9645"',
 'HIST26743_ACTIONS_AUTHORITY_COMMIT="c927843ea78f58f632082758142ee061a1c05166"',
 'VERSION_NAME="0.9726748"','VERSION_BUILD="26748"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"']:
 assert t in s,t
marker='# IRIS_26748_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26747_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26748 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26748 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26747 stage order drift',t); pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26748_temporal_raw_chroma_provenance.sh']:
 assert t in s+w,t
compile_block=s[s.index('compile_modified_runtime_shaders(){'):s.index('compile_spektra_raw_shader(){')]
roles=[
 'verify_26743_shaders.py "$ROOT" "$HIST26743_BASE" "$HIST26743_BASE" --compiler "$IRIS26748_GLSLANG"',
 'verify_26745_shaders.py "$ROOT" "$HIST26743_BASE" "$HIST26745_BASE" --compiler "$IRIS26748_GLSLANG"',
 'verify_26746_shaders.py "$ROOT" "$HIST26745_BASE" "$HIST26746_BASE" --compiler "$IRIS26748_GLSLANG"',
 'verify_26747_shaders.py "$ROOT" "$HIST26746_BASE" "$BASE" --compiler "$IRIS26748_GLSLANG"',
 'verify_26748_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26748_GLSLANG"']
for t in roles: assert t in compile_block,t
assert [compile_block.index(t) for t in roles]==sorted(compile_block.index(t) for t in roles)
for bad in ['verify_26745_shaders.py "$ROOT" "$BASE" "$BASE"','verify_26746_shaders.py "$ROOT" "$BASE" "$BASE"','verify_26747_shaders.py "$ROOT" "$BASE" "$BASE"','verify_26747_shaders.py "$ROOT" "$BASE" "$AFTER"']:
 assert bad not in compile_block,('wrong-role inherited shader replay survived',bad)
# 26746 post-assemble sed regression remains permanently locked.
assert "sed -i 's#APK JNI CONTRACT:.*#APK JNI CONTRACT: PASS (full assemble APK present; Super Res remains shared Sabre/VGN chroma owner; true2x native publication compiled in both ABIs)#'" in s
assert "sed -i 's/APK JNI CONTRACT:" not in s
assert not re.search(r"sed\s+-i\s+'s/[^']*Sabre/VGN",s)
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
assert '"$(find handoff_payload_26748 -type f|wc -l)" -eq 4' in s
assert '"$(wc -l < 26748_RUNTIME_CHANGED_PATHS.txt)" -eq 4' in s
assert "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" in s
assert '13 applicable runtime-expanded variants' in s
sv=(pkg/'verify_26748_shaders.py').read_text(); assert '26748_BASE_26747_RUNTIME_EXPANDED.sha256' in sv and 'sabre_merge.frag' in sv
print('PASS 26748 infrastructure: exact successful-26747 stage/toolchain/order preserved; historical shader roles locked 26743->26745->26746->26747->26748; post-assemble sed regression locked; 4-file runtime payload; both-ABI native stage; no backup/commit/push')
