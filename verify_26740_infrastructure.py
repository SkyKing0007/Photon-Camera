#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26740_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
# Exact successful 26739 nine-role mechanics authority must remain byte-identical in live repository.
auth=load('26740_SEALED_26739_INFRASTRUCTURE_AUTHORITY.sha256'); assert len(auth)==9
for p,h in auth.items():
 q=Path(p); assert q.exists(),('missing sealed 26739 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26739 mechanics authority drift',p)
for t in [
 'ROOT_ACTIONS_AUTHORITY_COMMIT="b39fe757ff41b1ca59925057f1c5b55ecc5b0611"',
 'ROOT_ARTIFACT_NAME="photon-26739-faithful-wronski-rgb-highlight-integrity"',
 'ROOT_ARTIFACT_SHA="2cbd161b610a38371aaf1bb7262f406e35fc8fd0f79faaa1c1f89dcac606c2bc"',
 'ROOT_TAR_SHA="3e8bfbc1bc12ab858f91687d36c6268a3e1034b238633d288ce189caa54d0524"',
 'VERSION_NAME="0.9726740"','VERSION_BUILD="26740"','GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26740_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:
 assert t in s,t
# 26740 authority is the exact successful 26739 artifact/candidate. Artifact lookup may resolve by exact name+head SHA,
# but identity is still pinned by full archive SHA and candidate TAR SHA; no source-tree substitution is allowed.
for t in ['actions/artifacts?name=${ROOT_ARTIFACT_NAME}&per_page=100','head_sha','expected exactly one artifact matching exact 26739 archive SHA','26740_EXACT_26739_CANDIDATE_AUTHORITY.sha256','pass "exact successful 26739 Actions compiled candidate authority reconstructed directly from exact archive/tar hashes"']:
 assert t in s,t
marker='# IRIS_26740_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26739_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26740 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26740 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26739 stage order drift',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26740_wronski_confidence_highlight_integrity.sh']:
 assert t in s+w,t
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
# Base compiler replay is the exact successful prior verifier; changed candidate has only current verifier.
assert 'IRIS_26740_CURRENT_AUTHORITY_BASE_SHADER_REPLAY' in s
assert 'python3 -S verify_26739_shaders.py "$ROOT" "$BASE" "$BASE" --compiler "$IRIS26740_GLSLANG"' in s
assert 'python3 -S verify_26740_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26740_GLSLANG"' in s
compile_body=s[s.index('compile_modified_runtime_shaders(){'):s.index('compile_spektra_raw_shader(){')]
for stale in ['verify_26735_shaders.py','verify_26736_shaders.py','verify_26737_shaders.py','verify_26738_shaders.py']:
 assert stale not in compile_body
assert 'compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" \\( -type f -o -type l \\) -name glslangValidator -print -quit)"' in s
assert '"$(find handoff_payload_26740 -type f|wc -l)" -eq 4' in s
for t in ["- '26740_*'","- 'handoff_payload_26740/**'",'.github/workflows/build-26740-wronski-confidence-highlight-integrity.yml']:
 assert t in w,t
print('PASS 26740 infrastructure: exact successful 26739 nine-role mechanics hash-pinned; stage/toolchain/order unchanged; exact 26739 authority identity hash-pinned; exact prior-base + current-candidate shader compile; no backup/commit/push')
