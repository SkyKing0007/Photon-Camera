#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26751_infrastructure.py BUILD_SCRIPT WORKFLOW [--package-only]')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); package_only=(len(sys.argv)==4 and sys.argv[3]=='--package-only')
s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
# Exact successful 26750 infrastructure bytes are the verification-mechanics authority.
auth={}
for l in (pkg/'26751_SEALED_26750_INFRASTRUCTURE_AUTHORITY.sha256').read_text().splitlines():
 if l.strip(): h,p=l.split(None,1); auth[p.strip()]=h
assert len(auth)==9
if not package_only:
 for p,h in auth.items():
  q=Path(p); assert q.exists(),('missing exact successful 26750 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26750 mechanics authority drift',p)
for t in [
 'RUNTIME_AUTHORITY_COMMIT="2202d37797d0feb6c40d58d1eea4deaeab3110c8"',
 'ROOT_ARTIFACT_NAME="photon-26750-source-proven-fine-color"',
 'ROOT_ARTIFACT_SHA="99e8ea824460986aa0fe732b25358b295c423cd8d00a85970262400ba6282f5d"',
 'ROOT_TAR_SHA="fa69d7b12b12c48d6ce381e5015a01a11cb7f124b0c4ab00b2afc6fc79a9a502"',
 'MECHANICS_AUTHORITY_COMMIT="2202d37797d0feb6c40d58d1eea4deaeab3110c8"',
 'MECHANICS_ACTIONS_RUN="37039400846"','MECHANICS_ARTIFACT_ID="11242915354"',
 'MECHANICS_ARTIFACT_SHA="99e8ea824460986aa0fe732b25358b295c423cd8d00a85970262400ba6282f5d"',
 'VERSION_NAME="0.9726751"','VERSION_BUILD="26751"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
 assert t in s,t
marker='# IRIS_26751_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26750_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26751 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26751 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26750 stage order drift',t); pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26751_frozen_reciprocal_fine_color.sh']:
 assert t in s+w,t
compile_block=s[s.index('compile_modified_runtime_shaders(){'):s.index('compile_spektra_raw_shader(){')]
assert 'verify_26751_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26751_GLSLANG"' in compile_block
for bad in ['verify_26750_shaders.py "$ROOT" "$BASE" "$AFTER"','HIST26747_BASE','HIST26746_BASE','HIST26745_BASE','HIST26743_BASE']:
 assert bad not in compile_block,bad
# Permanent post-assemble slash/sed failure class remains fixed.
assert "sed -i 's#APK JNI CONTRACT:.*#APK JNI CONTRACT: PASS (full assemble APK present; 26750 native Sabre/VGN color owner preserved; 26751 frozen fine-color consensus feeds shared VGN color; Super Res direct CFA remains luma/detail-only)#'" in s
assert "sed -i 's/APK JNI CONTRACT:" not in s
assert not re.search(r"sed\s+-i\s+'s/[^']*Sabre/VGN",s)
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
assert '"$(find handoff_payload_26751 -type f|wc -l)" -eq 2' in s
assert '"$(wc -l < 26751_RUNTIME_CHANGED_PATHS.txt)" -eq 2' in s
assert "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" in s
assert '13 base / 14 candidate runtime-expanded variants' in s
sv=(pkg/'verify_26751_shaders.py').read_text(); assert '26751_BASE_26750_RUNTIME_EXPANDED.sha256' in sv and "changed=={'universal_adaptive_color.comp'}" in sv and "added=={'fine_color_apply_26751.comp'}" in sv
for t in [
 'name: Build 26751 Frozen Reciprocal Fine Color','branches: [experimental-clean-photon-rebuild]',
 "- '26751_README_UPLOAD.txt'", "- '26751_*'", "- 'handoff_payload_26751/**'",
 'permissions:\n  contents: read\n  actions: read','name: photon-26751-frozen-reciprocal-fine-color',
 'IrisCamera-0.9726751-26751-frozen-reciprocal-fine-color-debug.apk']:
 assert t in w,t
print('PASS 26751 infrastructure: exact successful-26750 mechanics byte-pinned; stage/toolchain/order unchanged; exact successful 26750 candidate is runtime authority; safe Sabre/VGN sed; 2-file runtime payload; both-ABI native stage; no backup/commit/push'+(' (package-only authority-byte check deferred to repository)' if package_only else ''))
