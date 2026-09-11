#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26629_r1_infrastructure.py BUILD WORKFLOW [--successful-26628-build P --successful-26628-workflow P --successful-26628-transform P]')
bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text(); root=bp.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for t in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','RUNTIME_AUTHORITY_COMMIT="feeced352582866975009edc6b113d6151418c98"','HANDOFF_PARENT_COMMIT="feeced352582866975009edc6b113d6151418c98"',
'SUCCESS_26628_COMMIT="feeced352582866975009edc6b113d6151418c98"','BASE_RUN_ID="34643414499"','BASE_ARTIFACT_ID="10281080928"',
'BASE_ARTIFACT_NAME="photon-26628-r3-bjzhou-color-motion-night-superres-lens-ui"','BASE_ARTIFACT_SHA="5934180f54b51f947d61580344dc74c9e396174a475a70570e2e73be1cce8d12"',
'BASE_TAR_SHA="464890911b315f262f1173d2e25e7df96c2d55b369461553f31e09a49b4993ca"','VERSION_NAME="0.9726629"; VERSION_BUILD="26629"','GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','runtime allowlist must be 5','1708','802','778','7 DNG','3 modified runtime-expanded variants',
'NO NEW BACKUP (user directed)']:
    if t not in b: raise SystemExit(f'FAIL infrastructure pin missing: {t}')
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    if t not in w: raise SystemExit(f'FAIL workflow pin {t}')
if 'bash build_26629_r1_color_uhdr.sh\n' not in w: raise SystemExit('FAIL direct Actions build invocation missing')
if '--local-prebuild' in w: raise SystemExit('FAIL preparation-only mode referenced by Actions workflow')
for forbidden in ['git replace','--graft','git push','adb install']:
    if forbidden in w: raise SystemExit(f'FAIL workflow forbidden mechanism: {forbidden}')
push=w.split('workflow_dispatch:',1)[0]
for required in ["'26629_R1_README_UPLOAD.txt'","'REGRESSION_R1_26629_*'","'R1_26629_*'","'build_26629_r1_color_uhdr.sh'","'transform_26629_r1.py'","'validate_26629_r1.py'","'verify_26629_r1_*.py'","'handoff_payload_26629_r1/**'","'.github/workflows/build-26629-r1-color-uhdr.yml'"]:
    if required not in push: raise SystemExit(f'FAIL workflow trigger missing {required}')
for forbidden in ['26628_R3_','handoff_payload_26628_r3','build-26628-r3']:
    if forbidden in push: raise SystemExit(f'FAIL historical trigger overlap {forbidden}')
# Preserve exact successful R3 compiler/build order. Runtime-specific validators may differ; core mechanics do not.
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
    if n<=pos: raise SystemExit(f'FAIL missing/out-of-order successful-26628 mechanic: {tok}')
    pos=n
shader=b.find(seq[0]); infra=b.find('verify_successful_26628_mechanics'); source=b.find(seq[1])
if not (shader < infra < source): raise SystemExit('FAIL prewrite compiler/infrastructure ordering')
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26628_mechanics']
pos=-1
main=b[b.rfind('\nverify_package\n'):]
for tok in order:
    n=main.find(tok,pos+1)
    if n<=pos: raise SystemExit(f'FAIL top-level packaged order {tok}')
    pos=n
t=(root/'transform_26629_r1.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"'git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"'git','apply','--check"]:
    if tok not in t: raise SystemExit(f'FAIL transform isolation token {tok}')
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev','git push --force','adb install','git replace --graft']:
    if forbidden in b: raise SystemExit(f'FAIL build-script forbidden operation {forbidden}')
# Exact successful 26628 R3 implementation is the mechanics authority when supplied (Actions and final replay).
args=sys.argv[3:]
checks={
'--successful-26628-build':('05f2a3547f02091bdb3c43fe8759a7cdd9e9672301004b4e423f800e25279d4c',seq),
'--successful-26628-workflow':('199172e97e8be8a32ac7f8db07a620cebc853694168b3ea5844c39a954f52251',None),
'--successful-26628-transform':('c8f55b38ae167731249065cd206d2d3fa9afa2fba5df2ab29638fb8e88d8be83',None),
}
for flag,(expected,sseq) in checks.items():
    if flag in args:
        p=Path(args[args.index(flag)+1])
        if sha(p)!=expected: raise SystemExit(f'FAIL exact successful-26628-R3 SHA {flag}: {sha(p)}')
        if sseq:
            text=p.read_text(); pp=-1
            # R3 uses same core mechanics, but old helper name is successful_26627; only search core tokens.
            for tok in sseq:
                if tok.startswith('python3 -S "$SHADERVERIFY"') or tok.startswith('rm -rf "$ROOT/app/src"') or tok.startswith('snapshot_candidate_from_authority') or tok.startswith('./gradlew') or tok in ['verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','expected exactly one Gradle debug APK','POST-BUILD INVARIANCE','candidate_app_source.tar.gz']:
                    nn=text.find(tok,pp+1)
                    if nn<=pp: raise SystemExit(f'FAIL exact successful-26628-R3 core mechanic absent/out-of-order: {tok}')
                    pp=nn
print('PASS 26629 infrastructure: exact successful-26628-R3 direct ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; authority/identity/5-path color-UHDR validators only')
