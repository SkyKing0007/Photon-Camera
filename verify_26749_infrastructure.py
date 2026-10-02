#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv) not in (3,4): raise SystemExit('usage: verify_26749_infrastructure.py BUILD_SCRIPT WORKFLOW [--package-only]')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); package_only=(len(sys.argv)==4 and sys.argv[3]=='--package-only')
s=build.read_text(); w=workflow.read_text(); pkg=Path(__file__).resolve().parent
# Exact successful 26748 infrastructure bytes are authority, pinned by successful 26748 SHA-256 handoff proof.
auth={}
for l in (pkg/'26749_SEALED_26748_INFRASTRUCTURE_AUTHORITY.sha256').read_text().splitlines():
 if l.strip(): h,p=l.split(None,1); auth[p.strip()]=h
assert len(auth)==9
if not package_only:
 for p,h in auth.items():
  q=Path(p); assert q.exists(),('missing exact successful 26748 mechanics authority',p); assert hashlib.sha256(q.read_bytes()).hexdigest()==h,('26748 mechanics authority drift',p)
for t in [
 'ROOT_ACTIONS_AUTHORITY_COMMIT="7f7d8a807b801575d80f2f3966146eae259562c2"',
 'ROOT_ARTIFACT_NAME="photon-26748-temporal-raw-chroma-provenance"',
 'ROOT_ARTIFACT_SHA="ffe3074fc9de1bf45c773cd64d32c54c926187fda905ebe76103edf9061b1908"',
 'ROOT_TAR_SHA="c432714d2c7f49d9c2d8d2c3db0815699a1201db10edddc7bc67d39c12344630"',
 'HIST26747_ACTIONS_AUTHORITY_COMMIT="c2523a14725a92e1ff85d153578cb4bf9e6fdce2"',
 'HIST26746_ACTIONS_AUTHORITY_COMMIT="58dfdb0d423cad988afcbd4918e673fbac8d2558"',
 'HIST26745_ACTIONS_AUTHORITY_COMMIT="a8473f519a8d77926510a8a01a5658942dcf9645"',
 'HIST26743_ACTIONS_AUTHORITY_COMMIT="c927843ea78f58f632082758142ee061a1c05166"',
 'VERSION_NAME="0.9726749"','VERSION_BUILD="26749"','GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
 assert t in s,t
marker='# IRIS_26749_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26748_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26749 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26749 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('26748 stage order drift',t); pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26749_bounded_resolvesabre_cfa_reference.sh']:
 assert t in s+w,t
compile_block=s[s.index('compile_modified_runtime_shaders(){'):s.index('compile_spektra_raw_shader(){')]
roles=[
 'verify_26743_shaders.py "$ROOT" "$HIST26743_BASE" "$HIST26743_BASE" --compiler "$IRIS26749_GLSLANG"',
 'verify_26745_shaders.py "$ROOT" "$HIST26743_BASE" "$HIST26745_BASE" --compiler "$IRIS26749_GLSLANG"',
 'verify_26746_shaders.py "$ROOT" "$HIST26745_BASE" "$HIST26746_BASE" --compiler "$IRIS26749_GLSLANG"',
 'verify_26747_shaders.py "$ROOT" "$HIST26746_BASE" "$HIST26747_BASE" --compiler "$IRIS26749_GLSLANG"',
 'verify_26748_shaders.py "$ROOT" "$HIST26747_BASE" "$BASE" --compiler "$IRIS26749_GLSLANG"',
 'verify_26749_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26749_GLSLANG"']
for t in roles: assert t in compile_block,t
assert [compile_block.index(t) for t in roles]==sorted(compile_block.index(t) for t in roles)
for bad in [
 'verify_26747_shaders.py "$ROOT" "$BASE" "$BASE"',
 'verify_26748_shaders.py "$ROOT" "$BASE" "$BASE"',
 'verify_26748_shaders.py "$ROOT" "$BASE" "$AFTER"',
 'verify_26749_shaders.py "$ROOT" "$HIST26747_BASE" "$AFTER"']:
 assert bad not in compile_block,('wrong-role inherited shader replay survived',bad)
# 26746 slash-containing sed regression remains permanent.
assert "sed -i 's#APK JNI CONTRACT:.*#APK JNI CONTRACT: PASS (full assemble APK present; Super Res remains shared Sabre/VGN chroma owner; true2x native publication compiled in both ABIs)#'" in s
assert "sed -i 's/APK JNI CONTRACT:" not in s
assert not re.search(r"sed\s+-i\s+'s/[^']*Sabre/VGN",s)
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
assert '"$(find handoff_payload_26749 -type f|wc -l)" -eq 4' in s
assert '"$(wc -l < 26749_RUNTIME_CHANGED_PATHS.txt)" -eq 4' in s
assert "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" in s
assert '18 candidate runtime-expanded variants' in s
sv=(pkg/'verify_26749_shaders.py').read_text(); assert '26749_BASE_26748_RUNTIME_EXPANDED.sha256' in sv and 'resolvesabre_compatibility_input_26749.frag' in sv and 'wronski_resolvesabre_reconcile_float_26749.frag' in sv
# New workflow is only the next-build authority/name/scope advance of successful 26748 trigger/toolchain mechanics.
for t in [
 'name: Build 26749 Bounded ResolveSabre CFA Reference',
 'branches: [experimental-clean-photon-rebuild]',
 "- '26749_README_UPLOAD.txt'", "- '26749_*'", "- 'handoff_payload_26749/**'",
 'permissions:\n  contents: read\n  actions: read',
 'name: photon-26749-bounded-resolvesabre-cfa-reference',
 'IrisCamera-0.9726749-26749-bounded-resolvesabre-cfa-reference-debug.apk']:
 assert t in w,t
print('PASS 26749 infrastructure: exact successful-26748 mechanics byte-pinned; stage/toolchain/order preserved; historical shader roles locked 26743->26745->26746->26747->26748->26749; safe Sabre/VGN sed; 4-file runtime payload; both-ABI native stage; no backup/commit/push; procedural delta zero'+(' (package-only authority-byte check deferred to repository)' if package_only else ''))
