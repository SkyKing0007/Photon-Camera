#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26626_r1_infrastructure.py BUILD WORKFLOW [--successful-26624-build P --successful-26624-workflow P --successful-26624-transform P]')
bp=Path(sys.argv[1]); wp=Path(sys.argv[2]); b=bp.read_text(); w=wp.read_text(); root=bp.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# New identity/authority pins.
for t in [
'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'RUNTIME_AUTHORITY_COMMIT="50764653ecd67e62b303ab0bf27325dd82ac4239"',
'HANDOFF_PARENT_COMMIT="50764653ecd67e62b303ab0bf27325dd82ac4239"',
'BASE_RUN_ID="34552875046"','BASE_ARTIFACT_ID="10181524325"',
'BASE_ARTIFACT_NAME="photon-26625-r1-robust-short-fallback-geometry"',
'BASE_ARTIFACT_SHA="8f339d2ed9c95f02b1e0d964b041e38147c3411307e1759a3624888d73fe14ac"',
'BASE_TAR_SHA="d1ead1c9d881b784d8c57b1db9bd935f24562be3a0879c07b7df0d23365e7903"',
'VERSION_NAME="0.9726626"; VERSION_BUILD="26626"','GLSLANG_VERSION="16.5.0"',
'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
'runtime allowlist must be 5','1708','802','778','7 DNG','4 modified runtime-expanded variants',
]:
    if t not in b: raise SystemExit(f'FAIL infrastructure pin missing: {t}')
# Workflow must be the successful-26624 direct shape: setup -> sealed verify -> one direct build -> upload.
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    if t not in w: raise SystemExit(f'FAIL workflow pin {t}')
if 'bash build_26626_r1_bounded_source_structure_short_proof.sh\n' not in w: raise SystemExit('FAIL direct Actions build invocation missing')
if '--local-prebuild' in w: raise SystemExit('FAIL preparation-only mode referenced by Actions workflow')
for forbidden in ['git replace','--graft','R2_REPAIR_RUN','R3_REPAIR_RUN','backup-','git push','adb install']:
    if forbidden in w: raise SystemExit(f'FAIL workflow forbidden mechanism: {forbidden}')
# No historical workflow trigger overlap.
push=w.split('workflow_dispatch:',1)[0]
for required in ["'26626_R1_README_UPLOAD.txt'","'REGRESSION_R1_26626_*'","'R1_26626_*'","'build_26626_r1_bounded_source_structure_short_proof.sh'","'transform_26626_r1.py'","'validate_26626_r1.py'","'verify_26626_r1_*.py'","'handoff_payload_26626_r1/**'","'.github/workflows/build-26626-r1-bounded-source-structure-short-proof.yml'"]:
    if required not in push: raise SystemExit(f'FAIL workflow trigger missing {required}')
for forbidden in ['26624_','26625_','handoff_payload_26624','handoff_payload_26625']:
    if forbidden in push: raise SystemExit(f'FAIL historical trigger overlap {forbidden}')
# Preserve successful-26624 core execution order exactly in spirit and token ordering.
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
    if n<=pos: raise SystemExit(f'FAIL missing/out-of-order successful-26624 mechanic: {tok}')
    pos=n
# Source writes must occur after real shader compile and full candidate/infra validation.
shader=b.find(seq[0]); infra=b.find('verify_successful_26624_mechanics'); source=b.find(seq[1])
if not (shader < infra < source): raise SystemExit('FAIL prewrite compiler/infrastructure ordering')
# Candidate transform isolation inherited from successful 26624.
t=(root/'transform_26626_r1.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"git','rev-parse','--show-toplevel'",'candidate transform unexpectedly discovered a parent Git worktree',"git','apply','--check"]:
    if tok not in t: raise SystemExit(f'FAIL transform isolation token {tok}')
for forbidden in ['git branch backup-','git checkout dev','git switch dev','git push origin dev','git push --force','adb install','git replace --graft']:
    if forbidden in b: raise SystemExit(f'FAIL build-script forbidden operation {forbidden}')
# When real successful-26624 files are supplied in Actions, pin their exact packaged SHA256 and verify the same core sequence.
args=sys.argv[3:]
checks={
'--successful-26624-build':('b215085cc5d2d6b9786ba580165e6842a7cf50c215f13ef0be4dc52f254d2db6',seq),
'--successful-26624-workflow':('19189db53efa0e8384a6b671abbf93290544ef9dedcc0e9f4caab044ed92b061',None),
'--successful-26624-transform':('f1300f65acbca3910c53c17b84edc8d0b751cab91ecff3b335d237231f93db29',None),
}
for flag,(expected,sseq) in checks.items():
    if flag in args:
        p=Path(args[args.index(flag)+1])
        if sha(p)!=expected: raise SystemExit(f'FAIL exact successful-26624 SHA {flag}')
        if sseq:
            text=p.read_text(); pp=-1
            for tok in sseq:
                nn=text.find(tok,pp+1)
                if nn<=pp: raise SystemExit(f'FAIL exact successful-26624 core mechanic absent/out-of-order: {tok}')
                pp=nn
print('PASS 26626 infrastructure: exact successful-26624 direct ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; no 26625 wrapper/graft/preparation-only Actions path')
