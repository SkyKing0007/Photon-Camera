#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv) < 3:
    raise SystemExit('usage: verify_26622_r1_infrastructure.py BUILD WORKFLOW [--success-26621-script P --success-26621-workflow P --success-26621-transform P]')
bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text(); root=bp.parent
def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for token in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'RUNTIME_AUTHORITY_COMMIT="13073d0f358e9098e4288e60b3920bc208e8838b"',
'HANDOFF_PARENT_COMMIT="13073d0f358e9098e4288e60b3920bc208e8838b"',
'BASE_RUN_ID="34476774939"',
'BASE_ARTIFACT_ID="10151935955"',
'BASE_ARTIFACT_NAME="photon-26621-r1-new-simplified-local-laplacian"',
'BASE_ARTIFACT_SHA="ecd9c7ac803f484297bafabb3ffd8bff1e14cbdfbfe0b1d2b13c1a60cbff4097"',
'BASE_TAR_SHA="d5554aa30bd763ce725bec5eea1dc8165e9e898cc698f00061ea2aaa563176ae"',
'VERSION_NAME="0.9726622"; VERSION_BUILD="26622"',
'GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'SUCCESS_26621_BUILD_BLOB="b4825f5fe87aae6bd08a788416e1fbdf74d199dc"',
'SUCCESS_26621_WORKFLOW_BLOB="8a81be426691a4a9a90512985ea3cc411cc4a556"',
'SUCCESS_26621_TRANSFORM_BLOB="e2c7cbab74dd7ccf0c7521f9416402378b8f4767"',
]:
    assert token in b,f'missing 26621 authority/mechanics pin: {token}'
for token in ['runtime allowlist must be 2','1713','1711','802','778','0 modified runtime-expanded variants']:
    assert token in b,f'missing 26622 frozen-scope/count pin: {token}'
workflow_pins=['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']
for token in workflow_pins: assert token in w,f'workflow pin missing: {token}'
assert 'IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-local-laplacian-telemetry-lifetime-repair-debug.apk' in b
assert 'IrisCamera-0.9726622-26622-r1-local-laplacian-telemetry-lifetime-repair-debug.apk' in w
push=w.split('workflow_dispatch:',1)[0]
for forbidden in ['26614_','26615_','26616_','26617_','26618_','26619_','26620_','26621_','handoff_payload_26621']:
    assert forbidden not in push,f'historical trigger overlap: {forbidden}'
for required in [
"'26622_R1_README_UPLOAD.txt'","'REGRESSION_R1_26622_*'","'R1_26622_*'",
"'build_26622_r1_local_laplacian_telemetry_lifetime_repair.sh'","'transform_26622_r1.py'",
"'validate_26622_r1.py'","'verify_26622_r1_*.py'","'handoff_payload_26622_r1/**'",
"'.github/workflows/build-26622-r1-local-laplacian-telemetry-lifetime-repair.yml'"]:
    assert required in push,f'missing intended trigger: {required}'
t=(root/'transform_26622_r1.py').read_text()
for token in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]:
    assert token in t,f'missing nested-candidate isolation mechanic: {token}'
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev','git push --force','adb install']:
    assert forbidden not in b,f'forbidden build behavior: {forbidden}'
seq=[
'python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"',
'rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"',
'snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches',
'PRE-BUILD SAFETY PROOF PASSED',
'./gradlew :app:assembleDebug --stacktrace',
'expected exactly one Gradle debug APK',
'snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"',
'POST-BUILD INVARIANCE',
'candidate_app_source.tar.gz']
pos=-1
for token in seq:
    n=b.find(token,pos+1); assert n>pos,f'missing/out-of-order successful-26621 core mechanic: {token}'; pos=n
top=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n']
pos=-1
for token in top:
    n=b.find(token,pos+1); assert n>pos,f'missing/out-of-order packaged gate: {token.strip()}'; pos=n
shader=b.find('python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"')
ia=b.find('python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" --success-26621-script')
sw=b.find('rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"')
assert shader < ia < sw,'source write ordering changed'
args=sys.argv[3:]
if '--success-26621-script' in args:
    p=Path(args[args.index('--success-26621-script')+1])
    assert sha256(p)=='0ff53b29c8f849c1a8c5af98abf3edb4982627d24472eccf4f551a0ed0745877','successful 26621 build raw SHA mismatch'
    prev=p.read_text(); pp=-1
    for token in seq:
        n=prev.find(token,pp+1); assert n>pp,f'exact successful 26621 mechanic missing: {token}'; pp=n
if '--success-26621-workflow' in args:
    p=Path(args[args.index('--success-26621-workflow')+1])
    assert sha256(p)=='c84b03adc1c205f468d675f33b5db887a57e99682921b932eea5e93c24bd2ef1','successful 26621 workflow raw SHA mismatch'
    pw=p.read_text()
    for token in workflow_pins: assert token in pw and token in w,f'workflow mechanics changed: {token}'
if '--success-26621-transform' in args:
    p=Path(args[args.index('--success-26621-transform')+1])
    assert sha256(p)=='17009ab99a3fb4f6881741a23b4aee68d8e87e8b0f761f111b9f59e0e54c683b','successful 26621 transform raw SHA mismatch'
    pt=p.read_text()
    for token in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]:
        assert token in pt and token in t,f'transform isolation mechanic changed: {token}'
print('PASS 26622 infrastructure: exact successful-26621 ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; only 26622 identity, direct-26621 authority, 2-path crash repair scope, and device-lifetime regression differ')
