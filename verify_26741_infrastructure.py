#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26741_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
# Exact successful 26740 nine-role mechanics authority must remain byte-identical in live repository.
auth=load('26741_SEALED_26740_INFRASTRUCTURE_AUTHORITY.sha256'); assert len(auth)==9
for p,h in auth.items():
 q=Path(p); assert q.exists(),('missing sealed 26740 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26740 mechanics authority drift',p)
for t in [
 'ROOT_ACTIONS_AUTHORITY_COMMIT="b68cc33d8ea44a1ed8e2f6122c226c37e9241ec7"',
 'ROOT_ARTIFACT_NAME="photon-26740-wronski-confidence-highlight-integrity"',
 'ROOT_ARTIFACT_SHA="e71b950bf8a4f492093ece79b15d7d3eab87100a14ff11f8995afcf0be3f647d"',
 'ROOT_TAR_SHA="e4acb22f4dd4c44778f9a56de155f5826acc60d5f9b04be6215ebc4d7b6a9003"',
 'VERSION_NAME="0.9726741"','VERSION_BUILD="26741"','GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26741_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:
 assert t in s,t
# Same 26740 authority lookup mechanic: exact name + exact successful head SHA + full archive hash + candidate TAR hash.
for t in ['actions/artifacts?name=${ROOT_ARTIFACT_NAME}&per_page=100','head_sha','expected exactly one artifact matching exact 26740 archive SHA','26741_EXACT_26740_CANDIDATE_AUTHORITY.sha256','pass "exact successful 26740 Actions compiled candidate authority reconstructed directly from exact archive/tar hashes"']:
 assert t in s,t
marker='# IRIS_26741_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26740_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26741 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26741 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26740 stage order drift',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26741_superres_confidence_bright_neutrality.sh']:
 assert t in s+w,t
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
# Base compiler replay is the exact successful 26740 verifier; changed candidate has only current verifier.
assert 'IRIS_26741_CURRENT_AUTHORITY_BASE_SHADER_REPLAY' in s
assert 'python3 -S verify_26740_shaders.py "$ROOT" "$BASE" "$BASE" --compiler "$IRIS26741_GLSLANG"' in s
assert 'python3 -S verify_26741_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26741_GLSLANG"' in s
compile_body=s[s.index('compile_modified_runtime_shaders(){'):s.index('compile_spektra_raw_shader(){')]
for stale in ['verify_26735_shaders.py','verify_26736_shaders.py','verify_26737_shaders.py','verify_26738_shaders.py','verify_26739_shaders.py']:
 assert stale not in compile_body,stale
assert 'compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" \\( -type f -o -type l \\) -name glslangValidator -print -quit)"' in s
assert '"$(find handoff_payload_26741 -type f|wc -l)" -eq 5' in s
for t in ["- '26741_*'","- 'handoff_payload_26741/**'",'.github/workflows/build-26741-superres-confidence-bright-neutrality.yml']:
 assert t in w,t
# Native owner changed intentionally; real NDK both-ABI checkpoint remains before patch proof/assemble exactly as 26740.
assert 'modified Super Res CPU fallback native owner compiled in both ABIs' in s
print('PASS 26741 infrastructure: exact successful 26740 nine-role mechanics hash-pinned; stage/toolchain/order unchanged; exact 26740 authority identity hash-pinned; exact prior-base + current-candidate shader compile; native both-ABI stage preserved; no backup/commit/push')
