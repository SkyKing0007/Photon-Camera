#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

if len(sys.argv) < 3:
    raise SystemExit('usage: verify_26621_r1_infrastructure.py BUILD WORKFLOW [--success-26620-script P --success-26620-workflow P --success-26620-transform P]')

bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text()
root=bp.parent

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

# Exact successful 26620 compiled runtime authority + build mechanics pins.
for token in [
    'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
    'RUNTIME_AUTHORITY_COMMIT="a2ee879727707b293781868c13fd70102b9507c7"',
    'HANDOFF_PARENT_COMMIT="a2ee879727707b293781868c13fd70102b9507c7"',
    'BASE_RUN_ID="34437257967"',
    'BASE_ARTIFACT_ID="10136699847"',
    'BASE_ARTIFACT_NAME="photon-26620-r1-multiscale-local-laplacian"',
    'BASE_ARTIFACT_SHA="9c49984b4573a7f2d4e9518faa768baa6859ccad806468e77f651dc6e2daa3d6"',
    'BASE_TAR_SHA="7a51215a31287d5943be2453597645ad48cebf6c4954bfd77d0b605018ab0e89"',
    'VERSION_NAME="0.9726621"; VERSION_BUILD="26621"',
    'GLSLANG_VERSION="16.5.0"',
    'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
    'SUCCESS_26620_BUILD_BLOB="7ca1fbb32498abb30ce1b29a69cc356cf9394b76"',
    'SUCCESS_26620_WORKFLOW_BLOB="934e28afc93320cdbd70653e975c263c355f2f17"',
    'SUCCESS_26620_TRANSFORM_BLOB="8533d2d04d92b7bef52e72d3c780dd88cc967d4a"',
]:
    assert token in b, f'missing 26620 authority/mechanics pin: {token}'

# Exact changed-domain/count pins from frozen candidate.
for token in [
    'runtime allowlist must be 17',
    'existing/add count',
    '1711', '1713', '1699',
    '802', '778',
    '9 exact modified runtime-expanded variants',
]:
    assert token in b, f'missing 26621 frozen-scope/count pin: {token}'

# Successful 26620 workflow toolchain is preserved exactly.
workflow_pins=[
    'runs-on: ubuntu-24.04',
    'actions/checkout@v5',
    'actions/setup-java@v5',
    'distribution: temurin',
    "java-version: '17'",
    'actions/setup-python@v5',
    "python-version: '3.12'",
    'actions/upload-artifact@v4',
]
for token in workflow_pins:
    assert token in w, f'workflow pin changed/missing: {token}'
assert 'IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-r1-new-simplified-local-laplacian-debug.apk' in b
assert 'IrisCamera-0.9726621-26621-r1-new-simplified-local-laplacian-debug.apk' in w

# Trigger isolation: exactly the 26621 package launches this workflow; no historical overlap.
push=w.split('workflow_dispatch:',1)[0]
for forbidden in [
    '26614_','26615_','26616_','26617_','26618_','26619_','26620_',
    'handoff_payload_26614','handoff_payload_26615','handoff_payload_26616',
    'handoff_payload_26617','handoff_payload_26618','handoff_payload_26619','handoff_payload_26620',
]:
    assert forbidden not in push, f'historical workflow trigger overlap: {forbidden}'
for required in [
    "'26621_R1_README_UPLOAD.txt'",
    "'REGRESSION_R1_26621_*'",
    "'R1_26621_*'",
    "'build_26621_r1_new_simplified_local_laplacian.sh'",
    "'transform_26621_r1.py'",
    "'validate_26621_r1.py'",
    "'verify_26621_r1_*.py'",
    "'handoff_payload_26621_r1/**'",
    "'.github/workflows/build-26621-r1-new-simplified-local-laplacian.yml'",
]:
    assert required in push, f'missing intended workflow trigger: {required}'

# Nested candidate must remain isolated from carrier Git worktree, exactly as successful 26620.
t=(root/'transform_26621_r1.py').read_text()
isolation=[
    'GIT_CEILING_DIRECTORIES',
    "git','rev-parse','--show-toplevel'",
    'candidate transform unexpectedly discovered a parent Git worktree',
    "git','apply','--check",
]
for token in isolation:
    assert token in t, f'missing proven nested-candidate isolation mechanic: {token}'

# No backup/dev/push behavior is introduced.
for forbidden in [
    'git branch backup-', 'git checkout dev', 'git switch dev', 'git push origin dev',
    'git push --force', 'adb install',
]:
    assert forbidden not in b, f'forbidden build behavior: {forbidden}'

# Critical successful-26620 ordering must remain unchanged.
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
    'candidate_app_source.tar.gz',
]
pos=-1
for token in seq:
    n=b.find(token,pos+1)
    assert n>pos, f'missing/out-of-order successful-26620 core mechanic: {token}'
    pos=n

# Packaged gate ordering before source write is also preserved.
top=[
    'verify_package\n',
    'verify_scope\n',
    'obtain_authority\n',
    'make_candidate\n',
    'verify_shaders\n',
]
pos=-1
for token in top:
    n=b.find(token,pos+1)
    assert n>pos, f'missing/out-of-order packaged gate: {token.strip()}'
    pos=n

# Source is written only after real shader compile + infrastructure comparison in Actions path.
shader_compile_pos=b.find('python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --compiler "$compiler"')
infra_actions_pos=b.find('python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" --success-26620-script')
source_write_pos=b.find('rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"')
assert shader_compile_pos < infra_actions_pos < source_write_pos, 'source write ordering changed'

# If exact successful 26620 files are supplied, audit the real prior implementation rather than fixtures.
args=sys.argv[3:]
if '--success-26620-script' in args:
    p=Path(args[args.index('--success-26620-script')+1])
    assert sha256(p)=='ad541f78771b2b47872dc5908579e6bf456c28b6bfb62c15a044e0947c1e0161', 'successful 26620 build script raw SHA mismatch'
    prev=p.read_text(); pp=-1
    prev_seq=[
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
        'candidate_app_source.tar.gz',
    ]
    for token in prev_seq:
        n=prev.find(token,pp+1); assert n>pp, f'exact successful 26620 mechanic missing: {token}'; pp=n
if '--success-26620-workflow' in args:
    p=Path(args[args.index('--success-26620-workflow')+1])
    assert sha256(p)=='1fd37d6a060d114ae2f71848001bc0e9d1f3daea6ffbecc1ea46b94bed75f75e', 'successful 26620 workflow raw SHA mismatch'
    pw=p.read_text()
    for token in workflow_pins:
        assert token in pw and token in w, f'workflow mechanics pin changed: {token}'
if '--success-26620-transform' in args:
    p=Path(args[args.index('--success-26620-transform')+1])
    assert sha256(p)=='0b4e74aa7bc473950dda8d61e60bff3f42567d068cdd961afa9178c838d8a281', 'successful 26620 transform raw SHA mismatch'
    pt=p.read_text()
    for token in isolation:
        assert token in pt and token in t, f'transform isolation mechanic changed: {token}'

print('PASS 26621 infrastructure: exact successful-26620-R1 ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; only 26621 identity, direct-26620 authority, 17-path presentation scope, and new tone/Local-Laplacian validators differ')
