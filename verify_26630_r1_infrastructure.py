#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26630_r1_infrastructure.py BUILD WORKFLOW [--successful-26629-build P --successful-26629-workflow P --successful-26629-transform P]')
bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text(); root=bp.parent
def gitblob(p):
    data=Path(p).read_bytes(); return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
for t in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','RUNTIME_AUTHORITY_COMMIT="fe1b6953fa1546f19a23c67bce55e49de15c7ac6"','HANDOFF_PARENT_COMMIT="fe1b6953fa1546f19a23c67bce55e49de15c7ac6"',
'SUCCESS_26629_COMMIT="fe1b6953fa1546f19a23c67bce55e49de15c7ac6"','BASE_RUN_ID="34659969391"','BASE_ARTIFACT_ID="10287765040"',
'BASE_ARTIFACT_NAME="photon-26629-r1-luminance-locked-color-uhdr"','BASE_ARTIFACT_SHA="8b1ba27471689621bfe0e5b26b9c252e0c27d1697660fcab65263209c7580830"',
'BASE_TAR_SHA="51d61d1c8e13ef624939da053ff0fb41203dc5903bb21de143a69e1035d739fe"','VERSION_NAME="0.9726630"; VERSION_BUILD="26630"','GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','runtime allowlist must be 13','1700','802','778','7 DNG','3 modified runtime-expanded variants','NO NEW BACKUP']:
    if t not in b: raise SystemExit(f'FAIL infrastructure pin missing: {t}')
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    if t not in w: raise SystemExit(f'FAIL workflow pin {t}')
if 'bash build_26630_r1_adaptive_color_fixed_policy_uhdr.sh\n' not in w: raise SystemExit('FAIL direct Actions build invocation missing')
if '--local-prebuild' in w: raise SystemExit('FAIL preparation-only mode referenced by Actions workflow')
for forbidden in ['git replace','--graft','git push','adb install']:
    if forbidden in w: raise SystemExit(f'FAIL workflow forbidden mechanism: {forbidden}')
push=w.split('workflow_dispatch:',1)[0]
for required in ["'26630_R1_README_UPLOAD.txt'","'REGRESSION_R1_26630_*'","'R1_26630_*'","'build_26630_r1_adaptive_color_fixed_policy_uhdr.sh'","'transform_26630_r1.py'","'validate_26630_r1.py'","'verify_26630_r1_*.py'","'handoff_payload_26630_r1/**'","'.github/workflows/build-26630-r1-adaptive-color-fixed-policy-uhdr.yml'"]:
    if required not in push: raise SystemExit(f'FAIL workflow trigger missing {required}')
for forbidden in ['26629_R1_','handoff_payload_26629_r1','build-26629-r1']:
    if forbidden in push: raise SystemExit(f'FAIL historical trigger overlap {forbidden}')
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
    n=b.find(tok,pos+1)
    if n<=pos: raise SystemExit(f'FAIL missing/out-of-order successful-26629 mechanic: {tok}')
    pos=n
shader=b.find(seq[0]); infra=b.find('verify_successful_26629_mechanics'); source=b.find(seq[1])
if not (shader < infra < source): raise SystemExit('FAIL prewrite compiler/infrastructure ordering')
main=b[b.rfind('\nverify_package\n'):]; order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26629_mechanics']; pos=-1
for tok in order:
    n=main.find(tok,pos+1)
    if n<=pos: raise SystemExit(f'FAIL top-level packaged order {tok}')
    pos=n
t=(root/'transform_26630_r1.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"'git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"'git','apply','--check"]:
    if tok not in t: raise SystemExit(f'FAIL transform isolation token {tok}')
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev','git push --force','adb install','git replace --graft']:
    if forbidden in b: raise SystemExit(f'FAIL build-script forbidden operation {forbidden}')
# Exact successful 26629 files are the verification-mechanics authority when supplied by Actions.
args=sys.argv[3:]
checks={
'--successful-26629-build':('14f1fb28c9c8ecdeef32dde65ada1fc7bea1c29e',seq),
'--successful-26629-workflow':('8e83af054493729f0cf27f056d8de4fd0ed27367',None),
'--successful-26629-transform':('9d77f5e04854b2614e7902f503189c5162bee55e',None),
}
for flag,(expected,sseq) in checks.items():
    if flag in args:
        p=Path(args[args.index(flag)+1]); got=gitblob(p)
        if got!=expected: raise SystemExit(f'FAIL exact successful-26629-R1 Git blob {flag}: {got}')
        if sseq:
            text=p.read_text(); pp=-1
            for tok in sseq:
                nn=text.find(tok,pp+1)
                if nn<=pp: raise SystemExit(f'FAIL exact successful-26629-R1 core mechanic absent/out-of-order: {tok}')
                pp=nn
print('PASS 26630 infrastructure: exact successful-26629-R1 ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; authority/identity/13-path semantic validators only')
