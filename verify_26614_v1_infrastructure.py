#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26614_v1_infrastructure.py BUILD WORKFLOW [--success-26613-v1-1-script P --success-26613-v1-1-workflow P]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
# Exact successful authority and immutable pins.
for token in [
    'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
    'BASE_SUCCESS_COMMIT="717d5e71a4179a188e6c2ab996a0af2329a90d9c"',
    'HANDOFF_PARENT_COMMIT="717d5e71a4179a188e6c2ab996a0af2329a90d9c"',
    'BASE_RUN_ID="34276782851"','BASE_ARTIFACT_ID="10076133721"',
    'BASE_ARTIFACT_NAME="photon-26613-v1-1-fixed-domain-support-provenance"',
    'BASE_ARTIFACT_SHA="70a1b6ff93591c591d4851ea6eacdadb05e56cb881138dff12730cd3cff72fac"',
    'BASE_TAR_SHA="f57b85a35277233dc22a71228809d4a3a27a46125680d12e496badeba2f567fa"',
    'VERSION_NAME="0.9726614"; VERSION_BUILD="26614"',
    'GLSLANG_VERSION="16.5.0"',
    'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
]: assert token in b, f'missing authority/pin: {token}'
for token in ['runs-on: ubuntu-24.04','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'"]:
    assert token in w, f'workflow pin changed: {token}'
assert 'IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-canonical-appearance-cfa-validity-debug.apk' in b
assert 'IrisCamera-0.9726614-26614-v1-canonical-appearance-cfa-validity-debug.apk' in w
# One-build trigger isolation: this workflow may only react to 26614-specific paths.
push_block=w.split('workflow_dispatch:',1)[0]
for forbidden in ['26613_', 'V1_1_26613', 'verify_26613', 'handoff_payload_26613', 'build_26613']:
    assert forbidden not in push_block, f'historical trigger overlap in 26614 workflow: {forbidden}'
for required in ["'V1_26614_*'","'verify_26614_v1_*.py'","'handoff_payload_26614_v1/**'","'build_26614_v1_canonical_appearance_cfa_validity.sh'"]:
    assert required in push_block
# No backup mechanics.
for forbidden in ['git branch backup-', 'create_branch', 'backup-26613', 'backup-26614']:
    assert forbidden not in b
# Exact successful V1.1 core verification/build ordering must remain unchanged.
seq=[
'python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"',
'rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches',
'PRE-BUILD SAFETY PROOF PASSED',
'./gradlew :app:assembleDebug --stacktrace',
'snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"',
]
pos=-1
for token in seq:
    n=b.find(token,pos+1); assert n>pos, f'missing/out-of-order successful V1.1 core mechanic: {token}'; pos=n
# Top-level packaged gate ordering is also frozen.
top=['verify_package\n','verify_scope\n','obtain_authority\n','make_candidate\n','verify_shaders\n']
pos=-1
for token in top:
    n=b.find(token,pos+1); assert n>pos, f'missing/out-of-order packaged gate {token.strip()}'; pos=n
args=sys.argv[3:]
if '--success-26613-v1-1-script' in args:
    prev=Path(args[args.index('--success-26613-v1-1-script')+1]).read_text()
    prev_seq=[
    'python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"',
    'rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"',
    './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
    "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
    'verify_candidate_patches',
    'PRE-BUILD SAFETY PROOF PASSED',
    './gradlew :app:assembleDebug --stacktrace',
    'snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"',
    ]
    pp=-1
    for token in prev_seq:
        n=prev.find(token,pp+1); assert n>pp, f'successful 26613 V1.1 mechanic missing: {token}'; pp=n
    assert prev_seq==seq
if '--success-26613-v1-1-workflow' in args:
    pw=Path(args[args.index('--success-26613-v1-1-workflow')+1]).read_text()
    for token in ['runs-on: ubuntu-24.04','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
        assert token in pw and token in w, f'workflow mechanics pin changed: {token}'
print('PASS 26614 infrastructure: exact successful 26613 V1.1 compiler/NDK/patch/PRE-BUILD/assemble/postbuild order and pins preserved; 26614-only trigger paths; no backup')
