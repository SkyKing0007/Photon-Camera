#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26750_infrastructure.py BUILD_SCRIPT WORKFLOW [--package-only]')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); package_only=(len(sys.argv)==4 and sys.argv[3]=='--package-only')
s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
# Exact successful 26749 infrastructure bytes are the verification-mechanics authority.
auth={}
for l in (pkg/'26750_SEALED_26749_INFRASTRUCTURE_AUTHORITY.sha256').read_text().splitlines():
 if l.strip(): h,p=l.split(None,1); auth[p.strip()]=h
assert len(auth)==9
if not package_only:
 for p,h in auth.items():
  q=Path(p); assert q.exists(),('missing exact successful 26749 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26749 mechanics authority drift',p)
for t in [
 'RUNTIME_AUTHORITY_COMMIT="5d0482abd0b99979f5f8b800bf55b7a39ef40dab"',
 'ROOT_ARTIFACT_NAME="photon-26728-physically-supported-chroma"',
 'ROOT_ARTIFACT_SHA="c8a63a217be8c47f226976972afdc5edb0b8a68521cf045e4578ffce7aee384b"',
 'ROOT_TAR_SHA="fc1dea853e131f48decbe56d1138fe9d7c5a4148ed50b80fb2ccf0820a2fefe8"',
 'MECHANICS_AUTHORITY_COMMIT="3dadcf34afcad2def978f3ae8c05f3ae5132c5bd"',
 'MECHANICS_ACTIONS_RUN="37013817352"','MECHANICS_ARTIFACT_ID="11229062652"',
 'MECHANICS_ARTIFACT_SHA="c031353209ce75388742dace75a6a2540526c4e2cf01d525f963f944dffdfeda"',
 'VERSION_NAME="0.9726750"','VERSION_BUILD="26750"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
 assert t in s,t
marker='# IRIS_26750_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26749_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26750 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26750 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26749 stage order drift',t); pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26750_source_proven_fine_color.sh']:
 assert t in s+w,t
# Intentional reset changes only the runtime authority inputs and applicable shader replay. Compiler/toolchain/order remain successful-26749 mechanics.
compile_block=s[s.index('compile_modified_runtime_shaders(){'):s.index('compile_spektra_raw_shader(){')]
assert 'verify_26750_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26750_GLSLANG"' in compile_block
for bad in ['verify_26749_shaders.py','HIST26747_BASE','HIST26746_BASE','HIST26745_BASE','HIST26743_BASE']:
 assert bad not in compile_block,bad
# Permanent post-assemble slash/sed failure class remains fixed.
assert "sed -i 's#APK JNI CONTRACT:.*#APK JNI CONTRACT: PASS (full assemble APK present; 26728 native Sabre/VGN color owner preserved; Super Res shares corrected VGN chroma and direct CFA remains luma/detail-only)#'" in s
assert "sed -i 's/APK JNI CONTRACT:" not in s
assert not re.search(r"sed\s+-i\s+'s/[^']*Sabre/VGN",s)
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
assert '"$(find handoff_payload_26750 -type f|wc -l)" -eq 2' in s
assert '"$(wc -l < 26750_RUNTIME_CHANGED_PATHS.txt)" -eq 2' in s
assert "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" in s
assert '13 base / 13 candidate runtime-expanded variants' in s
sv=(pkg/'verify_26750_shaders.py').read_text(); assert '26750_BASE_26728_RUNTIME_EXPANDED.sha256' in sv and "changed=={'universal_adaptive_color.comp'}" in sv
for t in [
 'name: Build 26750 Source-Proven Fine Color','branches: [experimental-clean-photon-rebuild]',
 "- '26750_README_UPLOAD.txt'", "- '26750_*'", "- 'handoff_payload_26750/**'",
 'permissions:\n  contents: read\n  actions: read','name: photon-26750-source-proven-fine-color',
 'IrisCamera-0.9726750-26750-source-proven-fine-color-debug.apk']:
 assert t in w,t
print('PASS 26750 infrastructure: exact successful-26749 mechanics byte-pinned; stage/toolchain/order preserved; intentional runtime authority reset to exact successful 26728; applicable real shader compile is exact 26728 base -> 26750 candidate; safe Sabre/VGN sed; 2-file runtime payload; both-ABI native stage; no backup/commit/push'+(' (package-only authority-byte check deferred to repository)' if package_only else ''))
