#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26624_r1_infrastructure.py BUILD WORKFLOW [--success-26623-script P --success-26623-workflow P --success-26623-transform P]')
bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text(); root=bp.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for token in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'RUNTIME_AUTHORITY_COMMIT="1a4f4bd99b785617ca6c18a232477953ab429b65"',
'HANDOFF_PARENT_COMMIT="1a4f4bd99b785617ca6c18a232477953ab429b65"',
'BASE_RUN_ID="34507995081"','BASE_ARTIFACT_ID="10164738775"',
'BASE_ARTIFACT_NAME="photon-26623-r1-adaptive-upper-tone-short-telemetry"',
'BASE_ARTIFACT_SHA="746c6c4058ec1f5d5b7ad3341bc6cd834222516bdd142430ea0d779f67fef718"',
'BASE_TAR_SHA="c8ea95e0fea592753fc4cfb2a5a3e49a522e6e4b54b504db208807a890a55762"',
'VERSION_NAME="0.9726624"; VERSION_BUILD="26624"','GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'SUCCESS_26623_BUILD_BLOB="6527e146aa8ac30382713351af914be011bc699f"',
'SUCCESS_26623_WORKFLOW_BLOB="2d13af1570bfcf5ba7335f379f3d0f865d93d894"',
'SUCCESS_26623_TRANSFORM_BLOB="6d72e93f94dbeb3ddd6427f976e3d6792201d663"']:
    assert token in b,f'missing authority/mechanics pin: {token}'
for token in ['runtime allowlist must be 3','1710','802','778','2 modified runtime-expanded variants']:
    assert token in b,f'missing 26624 scope/count pin: {token}'
workflow_pins=['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']
for t in workflow_pins: assert t in w,t
assert 'IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-component-owned-short-recovery-debug.apk' in b
assert 'IrisCamera-0.9726624-26624-r1-component-owned-short-recovery-debug.apk' in w
push=w.split('workflow_dispatch:',1)[0]
for forbidden in ['26614_','26615_','26616_','26617_','26618_','26619_','26620_','26621_','26622_','26623_','handoff_payload_26623']:
    assert forbidden not in push,f'historical trigger overlap {forbidden}'
for required in ["'26624_R1_README_UPLOAD.txt'","'REGRESSION_R1_26624_*'","'R1_26624_*'","'build_26624_r1_component_owned_short_recovery.sh'","'transform_26624_r1.py'","'validate_26624_r1.py'","'verify_26624_r1_*.py'","'handoff_payload_26624_r1/**'","'.github/workflows/build-26624-r1-component-owned-short-recovery.yml'"]:
    assert required in push,required
t=(root/'transform_26624_r1.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]: assert tok in t,tok
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev','git push --force','adb install']:
    assert forbidden not in b,forbidden
# Exact successful-26623 core order remains unchanged.
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
    n=b.find(tok,pos+1); assert n>pos,f'missing/out-of-order successful-26623 mechanic: {tok}'; pos=n
top=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n']; pos=-1
for tok in top:
    n=b.find(tok,pos+1); assert n>pos,f'missing/out-of-order packaged gate: {tok.strip()}'; pos=n
shader=b.find('python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"')
ia=b.find('python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" --success-26623-script')
sw=b.find('rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"')
assert shader < ia < sw,'source-write ordering changed'
args=sys.argv[3:]
if '--success-26623-script' in args:
    p=Path(args[args.index('--success-26623-script')+1]); assert sha(p)=='7ae1ad308f16a2e7a9ea97f2b729c972ff6f1c5b53a5b002de1413e7405574f9','successful 26623 build raw SHA mismatch'
    prev=p.read_text(); pp=-1
    for tok in seq:
        n=prev.find(tok,pp+1); assert n>pp,f'exact successful 26623 mechanic missing: {tok}'; pp=n
if '--success-26623-workflow' in args:
    p=Path(args[args.index('--success-26623-workflow')+1]); assert sha(p)=='89f8ba692af10bc860df79aba15be15a95a8331df3276a40aa86ffe91e7bd953','successful 26623 workflow raw SHA mismatch'
    pw=p.read_text()
    for tok in workflow_pins: assert tok in pw and tok in w,tok
if '--success-26623-transform' in args:
    p=Path(args[args.index('--success-26623-transform')+1]); assert sha(p)=='e7e79ee49038852224fa9125fec63e3620c7e287f9a32df278373edb4dc9cd54','successful 26623 transform raw SHA mismatch'
    pt=p.read_text()
    for tok in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]: assert tok in pt and tok in t,tok
print('PASS 26624 infrastructure: exact successful-26623 ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; only 26624 identity, direct-26623 authority, 3-path component-owned-SHORT scope, and applicable validators differ')
