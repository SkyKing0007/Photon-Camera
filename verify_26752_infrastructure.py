#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26752_infrastructure.py BUILD_SCRIPT WORKFLOW [--package-only]')
build,workflow=Path(sys.argv[1]),Path(sys.argv[2]); package_only=(len(sys.argv)==4 and sys.argv[3]=='--package-only');s=build.read_text();w=workflow.read_text();pkg=Path(__file__).resolve().parent
auth={}
for l in (pkg/'26752_SEALED_26751_INFRASTRUCTURE_AUTHORITY.sha256').read_text().splitlines():
 if l.strip(): h,p=l.split(None,1);auth[p.strip()]=h
assert len(auth)==9
if not package_only:
 for p,h in auth.items():
  q=Path(p);assert q.exists(),('missing successful 26751 mechanics',p);assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26751 mechanics drift',p)
for t in ['RUNTIME_AUTHORITY_COMMIT="2f0ab8637816acd91a3a4ee331de910a47cad147"','ROOT_ARTIFACT_NAME="photon-26733-highlight-safe-color-integrity"','ROOT_ARTIFACT_SHA="d27333374b4ab1dea2ea4bdb2deed85eab603b44a4eea5a65e4e343665becb52"','ROOT_TAR_SHA="6feaf5ef8718f2d60ba6448393b31872644f56407eb89e6aa847f43381a34009"','MECHANICS_AUTHORITY_COMMIT="de4f3e6389b4e3d94b1e0d5cbaad100818402757"','MECHANICS_ACTIONS_RUN="37051394764"','MECHANICS_ARTIFACT_ID="11247011528"','MECHANICS_ARTIFACT_SHA="3ecf4b7d3a27e71e91af9461dd2eead77985f79b068d6ee3542c94161eb421fa"','VERSION_NAME="0.9726752"','VERSION_BUILD="26752"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
 assert t in s,t
marker='# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(marker)==1;main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26752 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26752 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order drift',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26752_ipol_plan_b_translational_sr.sh']:
 assert t in s+w,t
assert 'verify_26752_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26752_GLSLANG"' in s
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
assert '"$(find handoff_payload_26752 -type f|wc -l)" -eq 11' in s
assert '"$(wc -l < 26752_RUNTIME_CHANGED_PATHS.txt)" -eq 11' in s
assert "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" in s
for t in ['name: Build 26752 IPOL Plan B Translational SR','branches: [experimental-clean-photon-rebuild]',"- '26752_README_UPLOAD.txt'","- '26752_*'","- 'handoff_payload_26752/**'",'permissions:\n  contents: read\n  actions: read','name: photon-26752-ipol-plan-b-translational-sr','IrisCamera-0.9726752-26752-ipol-plan-b-translational-sr-debug.apk']:
 assert t in w,t
# Safe delimiter permanent regression.
assert "sed -i 's#APK JNI CONTRACT:.*#APK JNI CONTRACT:" in s and "sed -i 's/APK JNI CONTRACT:" not in s
print('PASS 26752 infrastructure: exact successful-26751 mechanics byte-pinned; stage/toolchain/order unchanged; exact successful 26733 compiled candidate is runtime/IQ authority; 11-file runtime payload; both-ABI native stage; no backup/commit/push'+(' (package-only prior-byte check deferred to repository)' if package_only else ''))
