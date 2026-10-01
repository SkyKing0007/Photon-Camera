#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26742_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
# Exact successful 26741 nine-role mechanics authority must remain byte-identical in the live repository.
auth=load('26742_SEALED_26741_INFRASTRUCTURE_AUTHORITY.sha256'); assert len(auth)==9
for p,h in auth.items():
 q=Path(p); assert q.exists(),('missing sealed 26741 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26741 mechanics authority drift',p)
for t in [
 'ROOT_ACTIONS_AUTHORITY_COMMIT="4541f7e0f86661623231b99aec19d6c88f58f4e7"',
 'ROOT_ARTIFACT_NAME="photon-26741-superres-confidence-bright-neutrality"',
 'ROOT_ARTIFACT_SHA="0020dc73a48bc6fa02a78a37a090f46a80c7f7525dc2760e74cdeb4ceb328ba1"',
 'ROOT_TAR_SHA="0374850b5de2175785f4ab4f7dccd5ea04356980ccff37e7f4398c742723eb46"',
 'VERSION_NAME="0.9726742"','VERSION_BUILD="26742"','GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26742_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:
 assert t in s,t
# Same 26741 authority lookup mechanic: exact name + exact successful head SHA + archive + candidate TAR hashes.
for t in ['actions/artifacts?name=${ROOT_ARTIFACT_NAME}&per_page=100','head_sha','expected exactly one artifact matching exact 26741 archive SHA','26742_EXACT_26741_CANDIDATE_AUTHORITY.sha256','pass "exact successful 26741 Actions compiled candidate authority reconstructed directly from exact archive/tar hashes"']:
 assert t in s,t
marker='# IRIS_26742_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26741_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26742 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26742 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26741 stage order drift',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26742_source_valid_highlight_chroma.sh']:
 assert t in s+w,t
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
# Exact prior-base compiler replay + current candidate compiler validation, same ordering as 26741.
assert 'IRIS_26742_CURRENT_AUTHORITY_BASE_SHADER_REPLAY' in s
assert 'python3 -S verify_26741_shaders.py "$ROOT" "$BASE" "$BASE" --compiler "$IRIS26742_GLSLANG"' in s
assert 'python3 -S verify_26742_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26742_GLSLANG"' in s
assert r'compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"' in s
assert '"$(find handoff_payload_26742 -type f|wc -l)" -eq 4' in s
for t in ["- '26742_*'","- 'handoff_payload_26742/**'",'.github/workflows/build-26742-source-valid-highlight-chroma.yml']:
 assert t in w,t
# Native owner changes intentionally; both ABI compilation stays before patch proof/assemble exactly as 26741.
assert 'modified source-valid Super Res CPU fallback native owner compiled in both ABIs' in s
print('PASS 26742 infrastructure: exact successful 26741 nine-role mechanics hash-pinned; stage/toolchain/order unchanged; exact 26741 authority identity hash-pinned; exact prior-base + current-candidate shader compile; native both-ABI stage preserved; no backup/commit/push')
