#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26627_r1_infrastructure.py BUILD WORKFLOW [--successful-26626-build P --successful-26626-workflow P --successful-26626-transform P]')
bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text(); root=bp.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for t in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','RUNTIME_AUTHORITY_COMMIT="8c6754f06ba0c8c36002c17372d7be1eab6daa43"','HANDOFF_PARENT_COMMIT="8c6754f06ba0c8c36002c17372d7be1eab6daa43"',
'SUCCESS_26626_COMMIT="8c6754f06ba0c8c36002c17372d7be1eab6daa43"','BASE_RUN_ID="34599600068"','BASE_ARTIFACT_ID="10262774952"',
'BASE_ARTIFACT_NAME="photon-26626-r1-bounded-source-structure-short-proof"','BASE_ARTIFACT_SHA="153ce6abb195f25bd42c459cbc447597f71faf349911f3be3f587759961f44d8"',
'BASE_TAR_SHA="0d587fc5ba3d239b4496be72979ad4d9bc7dfeca1c4a248c137a14087ffff712"','VERSION_NAME="0.9726627"; VERSION_BUILD="26627"','GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','runtime allowlist must be 4','1709','802','778','7 DNG','2 modified runtime-expanded variants']:
    if t not in b: raise SystemExit(f'FAIL infrastructure pin missing: {t}')
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    if t not in w: raise SystemExit(f'FAIL workflow pin {t}')
if 'bash build_26627_r1_adaptive_color_ui.sh\n' not in w: raise SystemExit('FAIL direct Actions build invocation missing')
if '--local-prebuild' in w: raise SystemExit('FAIL preparation-only mode referenced by Actions workflow')
for forbidden in ['git replace','--graft','R2_REPAIR_RUN','R3_REPAIR_RUN','backup-','git push','adb install']:
    if forbidden in w: raise SystemExit(f'FAIL workflow forbidden mechanism: {forbidden}')
push=w.split('workflow_dispatch:',1)[0]
for required in ["'26627_R1_README_UPLOAD.txt'","'REGRESSION_R1_26627_*'","'R1_26627_*'","'build_26627_r1_adaptive_color_ui.sh'","'transform_26627_r1.py'","'validate_26627_r1.py'","'verify_26627_r1_*.py'","'handoff_payload_26627_r1/**'","'.github/workflows/build-26627-r1-adaptive-color-ui.yml'"]:
    if required not in push: raise SystemExit(f'FAIL workflow trigger missing {required}')
for forbidden in ['26626_','handoff_payload_26626']:
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
    if n<=pos: raise SystemExit(f'FAIL missing/out-of-order successful-26626 mechanic: {tok}')
    pos=n
shader=b.find(seq[0]); infra=b.find('verify_successful_26626_mechanics'); source=b.find(seq[1])
if not (shader < infra < source): raise SystemExit('FAIL prewrite compiler/infrastructure ordering')
t=(root/'transform_26627_r1.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]:
    if tok not in t: raise SystemExit(f'FAIL transform isolation token {tok}')
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev','git push --force','adb install','git replace --graft']:
    if forbidden in b: raise SystemExit(f'FAIL build-script forbidden operation {forbidden}')
args=sys.argv[3:]
checks={
'--successful-26626-build':('c5cb59aa475e77eef513277a444ed07df2ff12e200328f91a1efc45f9bc473cf',seq),
'--successful-26626-workflow':('3f30210e306ad9139a9bb963598e2f899cd09a8568b0e8874e66f0775b69454c',None),
'--successful-26626-transform':('96bebf1bf930b06f3006eb8bc7dc8ec9f84c6892d9bd9b65ba9a3e2cf0b4f5ee',None),
}
for flag,(expected,sseq) in checks.items():
    if flag in args:
        p=Path(args[args.index(flag)+1])
        if sha(p)!=expected: raise SystemExit(f'FAIL exact successful-26626 SHA {flag}')
        if sseq:
            text=p.read_text(); pp=-1
            for tok in sseq:
                # Identity-specific tokens in successful build differ, but core compiler/build tokens are byte-stable.
                if tok.startswith('python3 -S "$SHADERVERIFY"') or tok.startswith('rm -rf "$ROOT/app/src"') or tok.startswith('snapshot_candidate_from_authority') or tok.startswith('./gradlew') or tok in ['verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','expected exactly one Gradle debug APK','POST-BUILD INVARIANCE','candidate_app_source.tar.gz']:
                    nn=text.find(tok,pp+1)
                    if nn<=pp: raise SystemExit(f'FAIL exact successful-26626 core mechanic absent/out-of-order: {tok}')
                    pp=nn
print('PASS 26627 infrastructure: exact successful-26626 direct ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; identity/authority/4-path validators only')
