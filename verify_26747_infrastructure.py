#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26747_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent

def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d

auth=load('26747_SEALED_26746_INFRASTRUCTURE_AUTHORITY.sha256'); assert len(auth)==9
for p,h in auth.items():
 q=Path(p); assert q.exists(),('missing sealed 26746 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26746 mechanics authority drift',p)

for t in [
 'ROOT_ACTIONS_AUTHORITY_COMMIT="58dfdb0d423cad988afcbd4918e673fbac8d2558"',
 'ROOT_ARTIFACT_NAME="photon-26746-extreme-flattened-highlight-veto"',
 'ROOT_ARTIFACT_SHA="d0b71cccddd702e3be7d43a10b08c06541913308b11fec779e8d79d0586465a2"',
 'ROOT_TAR_SHA="d3f9c244bb7fe0d2e519b7633aab9bc35ebec784791394fe55ac8088ddecdf62"',
 'HIST26745_ACTIONS_AUTHORITY_COMMIT="a8473f519a8d77926510a8a01a5658942dcf9645"',
 'HIST26745_ARTIFACT_NAME="photon-26745-bright-fringe-hue-authority"',
 'HIST26745_ARTIFACT_SHA="8660f67ec30ddb2a8945de387f3ae19270f4679684698dcccc6faf34b093e834"',
 'HIST26745_TAR_SHA="a915d476cf2832e9f8874735106230f73176c27fb7c66018fab105245e8a1e89"',
 'HIST26745_FULL_MANIFEST_SHA="d0d59bf36f685270500faa49304a8a5b375ffd16855b61c2f5dc237085fa0b75"',
 'HIST26745_INFRA_MANIFEST_SHA="13bca7e38a727137980cf0a929190958e2440848821d9c3ff152d27fb48ec74f"',
 'HIST26743_ACTIONS_AUTHORITY_COMMIT="c927843ea78f58f632082758142ee061a1c05166"',
 'HIST26743_ARTIFACT_NAME="photon-26743-visible-highlight-neutrality"',
 'HIST26743_ARTIFACT_SHA="051fd7ef96e46f176e9e9e72cb55ecf14fa670177075aab6f3d39b60da75119f"',
 'HIST26743_TAR_SHA="7d7fe097d3a978813a78da8bfcbc883bbf2f2855f729b88d376b532b14f4f5c7"',
 'HIST26743_FULL_MANIFEST_SHA="cf5c15be188f17aaff3761be8b6dd1c254ccdf902a7c6cd1dc039287d97d7965"',
 'HIST26743_INFRA_MANIFEST_SHA="6a9d3790025931a6415841e0af048123e00e95684731e9c6c134260fc19f20af"',
 'VERSION_NAME="0.9726747"','VERSION_BUILD="26747"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"']:
 assert t in s,t

marker='# IRIS_26747_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26746_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26747 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26747 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26746 stage order drift',t); pos=n

for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26747_full_26727_unrecoverable_highlight_authority.sh']:
 assert t in s+w,t

# Permanent regression for the first 26746 failure: every inherited verifier keeps its original
# historical base/candidate role. Never mechanically advance the verifier name against the new base.
compile_block=s[s.index('compile_modified_runtime_shaders(){'):s.index('compile_spektra_raw_shader(){')]
role43='verify_26743_shaders.py "$ROOT" "$HIST26743_BASE" "$HIST26743_BASE" --compiler "$IRIS26747_GLSLANG"'
role45='verify_26745_shaders.py "$ROOT" "$HIST26743_BASE" "$HIST26745_BASE" --compiler "$IRIS26747_GLSLANG"'
role46='verify_26746_shaders.py "$ROOT" "$HIST26745_BASE" "$BASE" --compiler "$IRIS26747_GLSLANG"'
role47='verify_26747_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26747_GLSLANG"'
for t in [role43,role45,role46,role47]: assert t in compile_block,t
assert compile_block.index(role43)<compile_block.index(role45)<compile_block.index(role46)<compile_block.index(role47)
for bad in [
 'verify_26745_shaders.py "$ROOT" "$BASE" "$BASE"',
 'verify_26746_shaders.py "$ROOT" "$BASE" "$BASE"',
 'verify_26746_shaders.py "$ROOT" "$BASE" "$AFTER"']:
 assert bad not in compile_block,('wrong-role inherited shader replay survived',bad)

# Permanent regression for the second 26746 failure: replacement text containing Sabre/VGN must
# never use '/' as the sed substitution delimiter.
assert "sed -i 's#APK JNI CONTRACT:.*#APK JNI CONTRACT: PASS (full assemble APK present; Super Res remains shared Sabre/VGN chroma owner; true2x native publication compiled in both ABIs)#'" in s
assert "sed -i 's/APK JNI CONTRACT:" not in s
assert not re.search(r"sed\s+-i\s+'s/[^']*Sabre/VGN",s)

assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
assert '"$(find handoff_payload_26747 -type f|wc -l)" -eq 4' in s
assert '"$(wc -l < 26747_RUNTIME_CHANGED_PATHS.txt)" -eq 4' in s
assert "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" in s
assert '12 applicable runtime-expanded variants' in s
shader_verify=(pkg/'verify_26747_shaders.py').read_text()
assert '26747_BASE_26746_RUNTIME_EXPANDED.sha256' in shader_verify
assert '26747_BASE_26745_RUNTIME_EXPANDED.sha256' not in shader_verify
print('PASS 26747 infrastructure: exact successful-26746 stage/toolchain/order preserved; historical shader roles locked 26743->26745->26746->26747; post-assemble Sabre/VGN sed delimiter regression locked; 4-file runtime payload; both-ABI native stage; no backup/commit/push')
