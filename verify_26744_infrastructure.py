#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26744_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
def load(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
# Exact successful 26743 nine-role mechanics authority must remain byte-identical in live repository.
auth=load('26744_SEALED_26743_INFRASTRUCTURE_AUTHORITY.sha256'); assert len(auth)==9
for p,h in auth.items():
 q=Path(p); assert q.exists(),('missing sealed 26743 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26743 mechanics authority drift',p)
for t in [
 'ROOT_ACTIONS_AUTHORITY_COMMIT="c927843ea78f58f632082758142ee061a1c05166"',
 'ROOT_ARTIFACT_NAME="photon-26743-visible-highlight-neutrality"',
 'ROOT_ARTIFACT_SHA="051fd7ef96e46f176e9e9e72cb55ecf14fa670177075aab6f3d39b60da75119f"',
 'ROOT_TAR_SHA="7d7fe097d3a978813a78da8bfcbc883bbf2f2855f729b88d376b532b14f4f5c7"',
 'VERSION_NAME="0.9726744"','VERSION_BUILD="26744"','GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26744_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:
 assert t in s,t
for t in ['actions/artifacts?name=${ROOT_ARTIFACT_NAME}&per_page=100','head_sha','expected exactly one artifact matching exact 26743 archive SHA','26744_EXACT_26743_CANDIDATE_AUTHORITY.sha256','pass "exact successful 26743 Actions compiled candidate authority reconstructed directly from exact archive/tar hashes"','build_26743_visible_highlight_neutrality_outputs/26743_candidate_app_source.tar.gz']:
 assert t in s,t
marker='# IRIS_26744_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26743_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26744 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26744 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26743 stage order drift',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26744_normal_master_long_shadow_visible_neutrality.sh']:
 assert t in s+w,t
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
assert 'IRIS_26744_CURRENT_AUTHORITY_BASE_SHADER_REPLAY' in s
assert 'python3 -S verify_26743_shaders.py "$ROOT" "$BASE" "$BASE" --compiler "$IRIS26744_GLSLANG"' in s
assert 'python3 -S verify_26744_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26744_GLSLANG"' in s
assert '"$(find handoff_payload_26744 -type f|wc -l)" -eq 4' in s
for t in ["- '26744_*'","- 'handoff_payload_26744/**'",'.github/workflows/build-26744-normal-master-long-shadow-visible-neutrality.yml']:
 assert t in w,t
print('PASS 26744 infrastructure: exact successful 26743 nine-role mechanics hash-pinned; stage/toolchain/order unchanged; exact 26743 authority identity pinned; prior-base + current-candidate shader compile; NDK both-ABI/full assemble preserved; no backup/commit/push')
