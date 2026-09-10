#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26618_r1_infrastructure.py BUILD WORKFLOW [--success-26614-script P --success-26614-workflow P]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
# Exact user-frozen successful 26614 R1 runtime authority and immutable toolchain pins.
for token in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'RUNTIME_AUTHORITY_COMMIT="11d7f8ee4b240f0299b27a674130ddaafbfb0be6"',
'BASE_RUN_ID="34297133575"','BASE_ARTIFACT_ID="10083632654"',
'BASE_ARTIFACT_NAME="photon-26614-r1-canonical-appearance-cfa-validity"',
'BASE_ARTIFACT_SHA="65ea5649bfcd11c45dfd01cd9f33b1326580e781201dbc08f7ee7d226435a25c"',
'BASE_TAR_SHA="2dafe644c1c09a25ebce7759e47fe13451fa5c6b74a18086424ed381d25f0efa"',
'VERSION_NAME="0.9726618"; VERSION_BUILD="26618"',
'GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
    assert token in b,f'missing authority/pin: {token}'
for token in ['runs-on: ubuntu-24.04','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    assert token in w,f'workflow pin changed: {token}'
assert 'IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-guided-base-detail-ltm-debug.apk' in b
assert 'IrisCamera-0.9726618-26618-r1-guided-base-detail-ltm-debug.apk' in w
# One-build trigger isolation: no 26614/15/16/17 path can launch this workflow.
push=w.split('workflow_dispatch:',1)[0]
for forbidden in ['26614_','26615_','26616_','26617_','handoff_payload_26614','handoff_payload_26615','handoff_payload_26616','handoff_payload_26617']:
    assert forbidden not in push,f'historical trigger overlap: {forbidden}'
for required in ["'R1_26618_*'","'verify_26618_r1_*.py'","'handoff_payload_26618/**'","'build_26618_r1_guided_base_detail_ltm.sh'"]:
    assert required in push,required
# Permanent successful 26614 R1 nested-worktree isolation must be inherited unchanged.
t=Path(Path(sys.argv[1]).parent/'transform_26618_r1.py').read_text()
for token in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]:
    assert token in t,f'missing 26614 R1 isolation mechanic: {token}'
# No build-script backup/write-to-dev mechanics.
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev']:
    assert forbidden not in b
# Exact successful 26614 core verification/build ordering.
seq=[
'python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"',
'rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches',
'PRE-BUILD SAFETY PROOF PASSED',
'./gradlew :app:assembleDebug --stacktrace',
'snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"']
pos=-1
for token in seq:
    n=b.find(token,pos+1); assert n>pos,f'missing/out-of-order 26614 core mechanic: {token}'; pos=n
# Exact top-level packaged gate order.
top=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n']
pos=-1
for token in top:
    n=b.find(token,pos+1); assert n>pos,f'missing/out-of-order packaged gate: {token.strip()}'; pos=n
args=sys.argv[3:]
if '--success-26614-script' in args:
    prev=Path(args[args.index('--success-26614-script')+1]).read_text()
    prevseq=[
    'python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"',
    'rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"',
    './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
    "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
    'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"']
    pp=-1
    for token in prevseq:
        n=prev.find(token,pp+1); assert n>pp,f'successful 26614 mechanic missing: {token}'; pp=n
    assert prevseq==seq
if '--success-26614-workflow' in args:
    pw=Path(args[args.index('--success-26614-workflow')+1]).read_text()
    for token in ['runs-on: ubuntu-24.04','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
        assert token in pw and token in w,f'workflow mechanics pin changed: {token}'
print('PASS 26618 infrastructure: exact successful-26614-R1 ordering/isolation/compiler/NDK/patch/assemble/invariance mechanics preserved; only identity/authority/count/algorithm validators adapted')
