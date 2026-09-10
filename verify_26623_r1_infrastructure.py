#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26623_r1_infrastructure.py BUILD WORKFLOW [--success-26622-script P --success-26622-workflow P --success-26622-transform P]')
bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text(); root=bp.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for token in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'RUNTIME_AUTHORITY_COMMIT="cc10ef3db2271526a8411ba4dac0c1287a1aa0c2"',
'HANDOFF_PARENT_COMMIT="cc10ef3db2271526a8411ba4dac0c1287a1aa0c2"',
'BASE_RUN_ID="34489649812"','BASE_ARTIFACT_ID="10157342883"',
'BASE_ARTIFACT_NAME="photon-26622-r1-local-laplacian-telemetry-lifetime-repair"',
'BASE_ARTIFACT_SHA="662f2e6648572524ba36204b3ad3e469d212d1fa5a63b36349221406019c7269"',
'BASE_TAR_SHA="8fd668bb6b9b55097aa226256e7d12728312a6ec9c8a0295da944edb787c8b0f"',
'VERSION_NAME="0.9726623"; VERSION_BUILD="26623"','GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'SUCCESS_26622_BUILD_BLOB="2b03cca0151dec633d3305c8a670841548814c16"',
'SUCCESS_26622_WORKFLOW_BLOB="319842cbc1b30fef74aa8b913de55ca41bc1f789"',
'SUCCESS_26622_TRANSFORM_BLOB="a73440052d40ca84e6496bd6c45d9538cbf82dd0"']:
    assert token in b,f'missing authority/mechanics pin: {token}'
for token in ['runtime allowlist must be 7','1706','802','778','4 modified runtime-expanded variants']:
    assert token in b,f'missing 26623 scope/count pin: {token}'
workflow_pins=['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']
for t in workflow_pins: assert t in w,t
assert 'IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-adaptive-upper-tone-short-telemetry-debug.apk' in b
assert 'IrisCamera-0.9726623-26623-r1-adaptive-upper-tone-short-telemetry-debug.apk' in w
push=w.split('workflow_dispatch:',1)[0]
for forbidden in ['26614_','26615_','26616_','26617_','26618_','26619_','26620_','26621_','26622_','handoff_payload_26622']:
    assert forbidden not in push,f'historical trigger overlap {forbidden}'
for required in ["'26623_R1_README_UPLOAD.txt'","'REGRESSION_R1_26623_*'","'R1_26623_*'","'build_26623_r1_adaptive_upper_tone_short_telemetry.sh'","'transform_26623_r1.py'","'validate_26623_r1.py'","'verify_26623_r1_*.py'","'handoff_payload_26623_r1/**'","'.github/workflows/build-26623-r1-adaptive-upper-tone-short-telemetry.yml'"]:
    assert required in push,required
t=(root/'transform_26623_r1.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]: assert tok in t,tok
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev','git push --force','adb install']:
    assert forbidden not in b,forbidden
# Exact successful-26622 core order remains unchanged.
seq=[
'python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"',
'rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"',
'snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','expected exactly one Gradle debug APK',
'snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"','POST-BUILD INVARIANCE','candidate_app_source.tar.gz']
pos=-1
for tok in seq:
    n=b.find(tok,pos+1); assert n>pos,f'missing/out-of-order successful-26622 mechanic: {tok}'; pos=n
top=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n']; pos=-1
for tok in top:
    n=b.find(tok,pos+1); assert n>pos,f'missing/out-of-order packaged gate: {tok.strip()}'; pos=n
shader=b.find('python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"')
ia=b.find('python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" --success-26622-script')
sw=b.find('rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"')
assert shader < ia < sw,'source-write ordering changed'
args=sys.argv[3:]
if '--success-26622-script' in args:
    p=Path(args[args.index('--success-26622-script')+1]); assert sha(p)=='cc1e6391a684a9c531170e0cea49dee16050f6051640deee7dab7545623d08ae','successful 26622 build raw SHA mismatch'
    prev=p.read_text(); pp=-1
    for tok in seq:
        n=prev.find(tok,pp+1); assert n>pp,f'exact successful 26622 mechanic missing: {tok}'; pp=n
if '--success-26622-workflow' in args:
    p=Path(args[args.index('--success-26622-workflow')+1]); assert sha(p)=='87f3b88a615fa5da3093630ea8acc90afee3864198fa61400e0de52b6d5dfc02','successful 26622 workflow raw SHA mismatch'
    pw=p.read_text()
    for tok in workflow_pins: assert tok in pw and tok in w,tok
if '--success-26622-transform' in args:
    p=Path(args[args.index('--success-26622-transform')+1]); assert sha(p)=='b207539176931d5b86547bc400719530128d5a6f59b3d56b5bfd65f26fc4e117','successful 26622 transform raw SHA mismatch'
    pt=p.read_text()
    for tok in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]: assert tok in pt and tok in t,tok
print('PASS 26623 infrastructure: exact successful-26622 ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; only 26623 identity, direct-26622 authority, 7-path upper-tone/telemetry scope, and applicable validators differ')
