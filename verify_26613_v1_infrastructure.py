#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26613_v1_infrastructure.py BUILD WORKFLOW [--success-26612-script P --success-26612-workflow P]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
assert 'experimental-clean-photon-rebuild' in b and 'experimental-clean-photon-rebuild' in w
assert 'f0789b5e2d18ab1dcec3568e456effdc140e0b7d' in b
assert '34226567972' in b and '10056062883' in b
assert '0.9726613' in b and '26613' in b
assert 'GLSLANG_VERSION="16.5.0"' in b
assert 'b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657' in b
assert 'ubuntu-24.04' in w and "java-version: '17'" in w and "python-version: '3.12'" in w
assert 'build-26613-v1-fixed-domain-support-provenance.yml' in w
assert '26612_' not in '\n'.join(x for x in w.splitlines() if 'success' not in x.lower()), '26612 trigger/path overlap in 26613 workflow'
# No backup mechanics in this ordinary correction.
for forbidden in ['git branch backup-', 'create_branch', 'backup-26612', 'backup-26613']:
    assert forbidden not in b
# Required successful-26612 command ordering is exact at the compiler/build core.
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
    n=b.find(token,pos+1); assert n>pos, f'missing/out-of-order core mechanic {token}'; pos=n
# Optional exact previous mechanics audit supplied in Actions.
args=sys.argv[3:]
if '--success-26612-script' in args:
    p=Path(args[args.index('--success-26612-script')+1]).read_text()
    prev=[
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches',
'PRE-BUILD SAFETY PROOF PASSED',
'./gradlew :app:assembleDebug --stacktrace',
'snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"',
]
    pp=-1
    for token in prev:
        n=p.find(token,pp+1); assert n>pp, f'successful 26612 mechanic missing {token}'; pp=n
    assert prev==seq[2:], 'internal comparison sequence changed'
if '--success-26612-workflow' in args:
    pw=Path(args[args.index('--success-26612-workflow')+1]).read_text()
    for token in ['runs-on: ubuntu-24.04','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'"]:
        assert token in pw and token in w, f'workflow mechanics pin changed {token}'
print('PASS 26613 infrastructure: exact successful-26612 compiler/NDK/patch/PRE-BUILD/assemble/postbuild ordering preserved; identity/scope only; no backup')
