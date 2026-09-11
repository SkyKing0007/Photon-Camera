#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26625_r1_infrastructure.py BUILD WORKFLOW [--success-26624-script P --success-26624-workflow P --success-26624-transform P]')
bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text(); root=bp.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for token in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'RUNTIME_AUTHORITY_COMMIT="d0d48ab26006a868baa8525a0b81aad65939fac3"',
'HANDOFF_PARENT_COMMIT="d0d48ab26006a868baa8525a0b81aad65939fac3"',
'BASE_RUN_ID="34525392337"','BASE_ARTIFACT_ID="10171452870"',
'BASE_ARTIFACT_NAME="photon-26624-r1-component-owned-short-recovery"',
'BASE_ARTIFACT_SHA="d4f45ff32259ccb7d75f28e53189298ff325ecfa3beddf4e1440b7009693dac5"',
'BASE_TAR_SHA="99b7860aa385c4dc9256e1ea9c1ec0abe434c58c302d5ede24c4cbd28b8c0f30"',
'VERSION_NAME="0.9726625"; VERSION_BUILD="26625"','GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'SUCCESS_26624_BUILD_BLOB="9a3d9f8447c5fae733d16066b3b473181a21ab0c"',
'SUCCESS_26624_WORKFLOW_BLOB="02dfaf0f46334d8eb726705fe46100eee9e666a3"',
'SUCCESS_26624_TRANSFORM_BLOB="58faecfbd58cec802323a7c1c375274b15885a21"']:
    assert token in b,f'missing authority/mechanics pin: {token}'
for token in ['runtime allowlist must be 3','1710','802','778','2 modified runtime-expanded variants']:
    assert token in b,f'missing 26625 scope/count pin: {token}'
workflow_pins=['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']
for t in workflow_pins: assert t in w,t
assert 'IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-robust-short-fallback-geometry-debug.apk' in b
assert 'IrisCamera-0.9726625-26625-r1-robust-short-fallback-geometry-debug.apk' in w
push=w.split('workflow_dispatch:',1)[0]
for forbidden in ['26614_','26615_','26616_','26617_','26618_','26619_','26620_','26621_','26622_','26623_','26624_','handoff_payload_26624']:
    assert forbidden not in push,f'historical trigger overlap {forbidden}'
for required in ["'26625_R1_README_UPLOAD.txt'","'REGRESSION_R1_26625_*'","'R1_26625_*'","'build_26625_r1_robust_short_fallback_geometry.sh'","'transform_26625_r1.py'","'validate_26625_r1.py'","'verify_26625_r1_*.py'","'handoff_payload_26625_r1/**'","'.github/workflows/build-26625-r1-robust-short-fallback-geometry.yml'"]:
    assert required in push,required
t=(root/'transform_26625_r1.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]: assert tok in t,tok
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev','git push --force','adb install']:
    assert forbidden not in b,forbidden
# Exact successful-26624 core order is immutable.
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
    n=b.find(tok,pos+1); assert n>pos,f'missing/out-of-order successful-26624 mechanic: {tok}'; pos=n
top=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders']; pos=-1
for tok in top:
    n=b.find(tok,pos+1); assert n>pos,f'missing/out-of-order packaged gate: {tok.strip()}'; pos=n
shader_pos=b.find('python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"')
ia=b.find('python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" --success-26624-script')
sw=b.find('rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"')
assert shader_pos < ia < sw,'source-write ordering changed'
# Permanent 26624 provenance-report regression: target build must print exact 26624 authority, not stale 26622/26623 ids.
line='PASS (successful 26624 R1 commit d0d48ab26006a868baa8525a0b81aad65939fac3/run 34525392337/artifact 10171452870/exact compiled candidate TAR)'
assert line in b
for stale in ['successful 26624 R1 commit cc10ef3d/run 34489649812/artifact 10157342883']:
    assert stale not in b
args=sys.argv[3:]
if '--success-26624-script' in args:
    p=Path(args[args.index('--success-26624-script')+1]); assert sha(p)=='b215085cc5d2d6b9786ba580165e6842a7cf50c215f13ef0be4dc52f254d2db6','successful 26624 build raw SHA mismatch'
    prev=p.read_text(); pp=-1
    for tok in seq:
        n=prev.find(tok,pp+1); assert n>pp,f'exact successful 26624 mechanic missing: {tok}'; pp=n
if '--success-26624-workflow' in args:
    p=Path(args[args.index('--success-26624-workflow')+1]); assert sha(p)=='19189db53efa0e8384a6b671abbf93290544ef9dedcc0e9f4caab044ed92b061','successful 26624 workflow raw SHA mismatch'
    pw=p.read_text()
    for tok in workflow_pins: assert tok in pw and tok in w,tok
if '--success-26624-transform' in args:
    p=Path(args[args.index('--success-26624-transform')+1]); assert sha(p)=='f1300f65acbca3910c53c17b84edc8d0b751cab91ecff3b335d237231f93db29','successful 26624 transform raw SHA mismatch'
    pt=p.read_text()
    for tok in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]: assert tok in pt and tok in t,tok
print('PASS 26625 infrastructure: exact successful-26624 ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; only 26625 identity, direct-26624 authority, exact 3-path robust-SHORT-fallback scope, provenance-report regression, and applicable validators differ')
