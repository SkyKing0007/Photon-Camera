#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26743_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
# Exact successful 26742 nine-role mechanics authority must remain byte-identical in live repository.
auth=load('26743_SEALED_26742_INFRASTRUCTURE_AUTHORITY.sha256'); assert len(auth)==9
for p,h in auth.items():
 q=Path(p); assert q.exists(),('missing sealed 26742 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26742 mechanics authority drift',p)
for t in [
 'ROOT_ACTIONS_AUTHORITY_COMMIT="ce17f4e3f70ba60a7130a6f2fa2f1d90e60b6638"',
 'ROOT_ARTIFACT_NAME="photon-26742-source-valid-highlight-chroma"',
 'ROOT_ARTIFACT_SHA="30ebd0c2bc0f48e9b7ddc3f73b88bc8934578089f8f69bc2f9308c7be26201f7"',
 'ROOT_TAR_SHA="bdb364a553ee77bf6d1f636abccbb7a34adc2314e1d2ac7cbfe1f573cc7ed391"',
 'VERSION_NAME="0.9726743"','VERSION_BUILD="26743"','GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26743_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:
 assert t in s,t
for t in ['actions/artifacts?name=${ROOT_ARTIFACT_NAME}&per_page=100','head_sha','expected exactly one artifact matching exact 26742 archive SHA','26743_EXACT_26742_CANDIDATE_AUTHORITY.sha256','pass "exact successful 26742 Actions compiled candidate authority reconstructed directly from exact archive/tar hashes"','build_26742_source_valid_highlight_chroma_outputs/26742_candidate_app_source.tar.gz']:
 assert t in s,t
marker='# IRIS_26743_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26742_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26743 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26743 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26742 stage order drift',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26743_visible_highlight_neutrality.sh']:
 assert t in s+w,t
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
assert 'IRIS_26743_CURRENT_AUTHORITY_BASE_SHADER_REPLAY' in s
assert 'python3 -S verify_26742_shaders.py "$ROOT" "$BASE" "$BASE" --compiler "$IRIS26743_GLSLANG"' in s
assert 'python3 -S verify_26743_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26743_GLSLANG"' in s
assert r'compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"' in s
assert '"$(find handoff_payload_26743 -type f|wc -l)" -eq 5' in s
for t in ["- '26743_*'","- 'handoff_payload_26743/**'",'.github/workflows/build-26743-visible-highlight-neutrality.yml']:
 assert t in w,t
assert 'restored 26741 Super Res CPU fallback native owner compiled in both ABIs' in s
print('PASS 26743 infrastructure: exact successful 26742 nine-role mechanics hash-pinned; stage/toolchain/order unchanged; exact 26742 authority identity hash-pinned; exact prior-base + current-candidate shader compile; native both-ABI stage preserved; no backup/commit/push')
