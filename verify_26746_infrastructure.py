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
for t in ['ROOT_ACTIONS_AUTHORITY_COMMIT="a8473f519a8d77926510a8a01a5658942dcf9645"','ROOT_ARTIFACT_NAME="photon-26745-bright-fringe-hue-authority"','ROOT_ARTIFACT_SHA="8660f67ec30ddb2a8945de387f3ae19270f4679684698dcccc6faf34b093e834"','ROOT_TAR_SHA="a915d476cf2832e9f8874735106230f73176c27fb7c66018fab105245e8a1e89"','VERSION_NAME="0.9726746"','VERSION_BUILD="26746"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"']:
 assert t in s,t
marker='# IRIS_26746_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26745_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26746 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26746 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26745 stage order drift',t); pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26746_extreme_flattened_highlight_veto.sh']:
 assert t in s+w,t
assert 'verify_26745_shaders.py "$ROOT" "$BASE" "$BASE" --compiler "$IRIS26746_GLSLANG"' in s
assert 'verify_26746_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26746_GLSLANG"' in s
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
assert '"$(find handoff_payload_26746 -type f|wc -l)" -eq 2' in s
assert '"$(wc -l < 26746_RUNTIME_CHANGED_PATHS.txt)" -eq 2' in s
print('PASS 26746 infrastructure: exact successful 26745 nine-role mechanics hash-pinned; stage/toolchain/order unchanged; exact 26745 authority identity hash-pinned; inherited base + current shader compile; both-ABI native stage preserved; no backup/commit/push')
