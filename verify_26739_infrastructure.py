#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26739_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
# Exact sealed 26738 nine-role mechanics authority must remain byte-identical in live repository.
auth=load('26739_SEALED_26738_INFRASTRUCTURE_AUTHORITY.sha256'); assert len(auth)==9
for p,h in auth.items():
 q=Path(p); assert q.exists(),('missing sealed 26738 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26738 mechanics authority drift',p)
for t in ['ROOT_ACTIONS_AUTHORITY_COMMIT="271f52be81d8222e5f04fdfd0e9085a55bbd5e2c"','ROOT_RUN_ID="36637337435"','ROOT_ARTIFACT_ID="11064304462"','ROOT_ARTIFACT_NAME="photon-26735-neutral-chroma-digital-luma-retry"','ROOT_ARTIFACT_SHA="37b6ef1cf0735403765291f15fe7b639d67d1ff406a54617b639e97221bbf8bd"','ROOT_TAR_SHA="8159fbf01e8e02d8d4a0480dd2bc53348f2e57938f63111db7fd69a6ac76ba0a"','VERSION_NAME="0.9726739"','VERSION_BUILD="26739"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26739_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:
 assert t in s,t
# Authority chain is successful 26735 artifact -> sealed 26736 -> sealed 26737 -> sealed 26738 -> 26739.
for t in ['authority_payload_26736','26739_BASE_26736_FULL_APP.sha256','authority_payload_26737','26739_BASE_26737_FULL_APP.sha256','authority_payload_26738','26739_BASE_26738_FULL_APP.sha256','26739_EXACT_26738_CANDIDATE_AUTHORITY.sha256','pass "exact 26738 candidate reconstructed from successful 26735 Actions authority plus sealed 26736, 26737 and 26738 payloads"']:
 assert t in s,t
marker='# IRIS_26739_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26738_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26739 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26739 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26738 stage order drift',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26739_faithful_wronski_rgb_highlight_integrity.sh']:
 assert t in s+w,t
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
# Base compiler replay is the exact successful prior verifier; changed candidate has only current verifier.
assert 'IRIS_26739_CURRENT_AUTHORITY_BASE_SHADER_REPLAY' in s
assert 'python3 -S verify_26738_shaders.py "$ROOT" "$BASE37" "$BASE" --compiler "$IRIS26739_GLSLANG"' in s
assert 'python3 -S verify_26739_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26739_GLSLANG"' in s
compile_body=s[s.index('compile_modified_runtime_shaders(){'):s.index('compile_spektra_raw_shader(){')]
for stale in ['verify_26727_shaders.py','verify_26735_shaders.py','verify_26736_shaders.py','verify_26737_shaders.py']:
 assert stale not in compile_body
assert 'verify_26738_shaders.py "$ROOT" "$BASE" "$AFTER"' not in compile_body
assert 'compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" \\( -type f -o -type l \\) -name glslangValidator -print -quit)"' in s
assert '"$(find handoff_payload_26739 -type f|wc -l)" -eq 5' in s
assert '"$(find authority_payload_26736 -type f|wc -l)" -eq 3' in s and '"$(find authority_payload_26737 -type f|wc -l)" -eq 4' in s and '"$(find authority_payload_26738 -type f|wc -l)" -eq 5' in s
for t in ["- '26739_*'","- 'handoff_payload_26739/**'","- 'authority_payload_26736/**'","- 'authority_payload_26737/**'","- 'authority_payload_26738/**'",'.github/workflows/build-26739-faithful-wronski-rgb-highlight-integrity.yml']:
 assert t in w,t
print('PASS 26739 infrastructure: exact sealed 26738 nine-role mechanics hash-pinned; successful 26735 root -> 26736 -> 26737 -> 26738 authority chain; compiler/build stage order unchanged; exact prior-base + current-candidate shader compile; no backup/commit/push')
