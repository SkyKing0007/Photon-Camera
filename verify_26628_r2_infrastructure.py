#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26628_r2_infrastructure.py BUILD WORKFLOW [--successful-26627-build P --successful-26627-workflow P --successful-26627-transform P]')
bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text(); root=bp.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for t in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','RUNTIME_AUTHORITY_COMMIT="77ad63a80827ac103714be303678be1b47ad30d4"','HANDOFF_PARENT_COMMIT="d01b9beaa590b7a0f6ea35572efd9beaf24f4c6b"',
'SUCCESS_26627_COMMIT="77ad63a80827ac103714be303678be1b47ad30d4"','BASE_RUN_ID="34627218884"','BASE_ARTIFACT_ID="10275365416"',
'BASE_ARTIFACT_NAME="photon-26627-r1-adaptive-color-ui"','BASE_ARTIFACT_SHA="63ed3147750de19744c04762ed9f42e6a29ef6642a4f01860525fdc47d8c38f7"',
'BASE_TAR_SHA="0dcbe9210ff1c46a59469bfc7ae3faf5bc3342afb66685de070d73b49240d4da"','VERSION_NAME="0.9726628"; VERSION_BUILD="26628"','GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','runtime allowlist must be 11','1702','802','778','7 DNG','6 modified runtime-expanded variants',
'backup-26627-pre-bjzhou-color-motion-night-superres @ 77ad63a80827ac103714be303678be1b47ad30d4']:
    if t not in b: raise SystemExit(f'FAIL infrastructure pin missing: {t}')
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    if t not in w: raise SystemExit(f'FAIL workflow pin {t}')
if 'bash build_26628_r2_bjzhou_color_motion_night_superres.sh\n' not in w: raise SystemExit('FAIL direct Actions build invocation missing')
if '--local-prebuild' in w: raise SystemExit('FAIL preparation-only mode referenced by Actions workflow')
for forbidden in ['git replace','--graft','R2_REPAIR_RUN','R3_REPAIR_RUN','git push','adb install']:
    if forbidden in w: raise SystemExit(f'FAIL workflow forbidden mechanism: {forbidden}')
push=w.split('workflow_dispatch:',1)[0]
for required in ["'26628_R2_README_UPLOAD.txt'","'REGRESSION_R2_26628_*'","'R2_26628_*'","'build_26628_r2_bjzhou_color_motion_night_superres.sh'","'transform_26628_r2.py'","'validate_26628_r2.py'","'verify_26628_r2_*.py'","'handoff_payload_26628_r2/**'","'.github/workflows/build-26628-r2-bjzhou-color-motion-night-superres.yml'"]:
    if required not in push: raise SystemExit(f'FAIL workflow trigger missing {required}')
for forbidden in ['26627_','handoff_payload_26627']:
    if forbidden in push: raise SystemExit(f'FAIL historical trigger overlap {forbidden}')
# Same successful 26627 direct compiler/build sequence and order. No wrapper/graft/local-prebuild path in Actions.
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
    if n<=pos: raise SystemExit(f'FAIL missing/out-of-order successful-26627 mechanic: {tok}')
    pos=n
shader=b.find(seq[0]); infra=b.find('verify_successful_26627_mechanics'); source=b.find(seq[1])
if not (shader < infra < source): raise SystemExit('FAIL prewrite compiler/infrastructure ordering')
# Top-level packaged execution order is inherited unchanged.
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26627_mechanics']
pos=-1
main=b[b.rfind('\nverify_package\n'):]
for tok in order:
    n=main.find(tok,pos+1)
    if n<=pos: raise SystemExit(f'FAIL top-level packaged order {tok}')
    pos=n
t=(root/'transform_26628_r2.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]:
    if tok not in t: raise SystemExit(f'FAIL transform isolation token {tok}')
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev','git push --force','adb install','git replace --graft']:
    if forbidden in b: raise SystemExit(f'FAIL build-script forbidden operation {forbidden}')
args=sys.argv[3:]
checks={
'--successful-26627-build':('d91a730a8ca691a3a8e979d8f23ad9d99518b59ee56affcfe62cebc147e2b218',seq),
'--successful-26627-workflow':('f9e4aafae7f5a99213d5f50168aa58c3a9d4d79c1790c01a38a0e2170a719b08',None),
'--successful-26627-transform':('921045889a4f65af9e3d8bbb661ee2856bb6e95de39b7b7da5f3cc7a8d6eea2c',None),
}
for flag,(expected,sseq) in checks.items():
    if flag in args:
        p=Path(args[args.index(flag)+1])
        if sha(p)!=expected: raise SystemExit(f'FAIL exact successful-26627 SHA {flag}')
        if sseq:
            text=p.read_text(); pp=-1
            for tok in sseq:
                if tok.startswith('python3 -S "$SHADERVERIFY"') or tok.startswith('rm -rf "$ROOT/app/src"') or tok.startswith('snapshot_candidate_from_authority') or tok.startswith('./gradlew') or tok in ['verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','expected exactly one Gradle debug APK','POST-BUILD INVARIANCE','candidate_app_source.tar.gz']:
                    nn=text.find(tok,pp+1)
                    if nn<=pp: raise SystemExit(f'FAIL exact successful-26627 core mechanic absent/out-of-order: {tok}')
                    pp=nn
print('PASS 26628 infrastructure: exact successful-26627 direct ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; authority/identity/11-path color/UI/native-regression validators only')
