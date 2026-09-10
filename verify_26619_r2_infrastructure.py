#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26619_r2_infrastructure.py BUILD WORKFLOW [--success-26618-script P --success-26618-workflow P --success-26618-transform P]')
bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text()
for token in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'RUNTIME_AUTHORITY_COMMIT="34dce306c8f1b333511db8e2fbdb58555e9e9bd2"',
'HANDOFF_PARENT_COMMIT="7a0532a9aa26ea0d92ab71c8d7c6965a9139524b"',
'BASE_RUN_ID="34426075869"','BASE_ARTIFACT_ID="10132769400"',
'BASE_ARTIFACT_NAME="photon-26618-r1-guided-base-detail-ltm"',
'BASE_ARTIFACT_SHA="3121977d6f6064e6cd2f41e3ad913572505df2f3a892671736af8ef0db1327f1"',
'BASE_TAR_SHA="150e70d4b044ae8c3caa35758f5dbbffa505dd31b80ec76c535864f55645e3ea"',
'VERSION_NAME="0.9726619"; VERSION_BUILD="26619"',
'GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
    assert token in b,f'missing authority/pin: {token}'
for token in ['runs-on: ubuntu-24.04','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    assert token in w,f'workflow pin changed: {token}'
assert 'IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r2-monotonic-guided-base-detail-debug.apk' in b
assert 'IrisCamera-0.9726619-26619-r2-monotonic-guided-base-detail-debug.apk' in w
push=w.split('workflow_dispatch:',1)[0]
for forbidden in ['26614_','26615_','26616_','26617_','26618_','handoff_payload_26618']:
    assert forbidden not in push,f'historical trigger overlap: {forbidden}'
for required in ["'R2_26619_*'","'verify_26619_r2_*.py'","'handoff_payload_26619_r2/**'","'build_26619_r2_monotonic_guided_base_detail_ltm.sh'"]:
    assert required in push,required
t=(bp.parent/'transform_26619_r2.py').read_text()
for token in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]:
    assert token in t,f'missing successful 26618 isolation mechanic: {token}'
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev']:
    assert forbidden not in b
# Exact successful 26618 core gate/build ordering is immutable.
seq=[
'python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"',
'rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"']
pos=-1
for token in seq:
    n=b.find(token,pos+1); assert n>pos,f'missing/out-of-order successful-26618 core mechanic: {token}'; pos=n
top=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n']
pos=-1
for token in top:
    n=b.find(token,pos+1); assert n>pos,f'missing/out-of-order packaged gate: {token.strip()}'; pos=n
args=sys.argv[3:]
def arg(name): return Path(args[args.index(name)+1]) if name in args else None
ps=arg('--success-26618-script'); pw=arg('--success-26618-workflow'); pt=arg('--success-26618-transform')
if ps:
    assert hashlib.sha256(ps.read_bytes()).hexdigest()=='8217bc2daf8cc3d5a48fe7a451c777291241ba043dc7c9a64e4f16e02b068775','successful 26618 build script hash'
    prev=ps.read_text(); pp=-1
    for token in seq:
        n=prev.find(token,pp+1); assert n>pp,f'successful 26618 mechanic missing: {token}'; pp=n
if pw:
    assert hashlib.sha256(pw.read_bytes()).hexdigest()=='eb9071c83eb469b29ca685cc05733cb3b6f8f5f626049ec4b3e24b2678121c07','successful 26618 workflow hash'
    prev=pw.read_text()
    for token in ['runs-on: ubuntu-24.04','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
        assert token in prev and token in w
if pt:
    assert hashlib.sha256(pt.read_bytes()).hexdigest()=='63dc96b362d4c501ab2b7b3cf3bb6b2623490e9a986315aac71f1c7f4fe2ed01','successful 26618 transform hash'
    prev=pt.read_text()
    for token in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]:
        assert token in prev and token in t
print('PASS 26619 R2 infrastructure: exact successful-26618 ordering/isolation/compiler/NDK/patch/assemble/invariance mechanics preserved; identity/authority/count/algorithm validators only')
