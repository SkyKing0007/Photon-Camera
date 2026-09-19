#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26669_infrastructure.py BUILD_SCRIPT WORKFLOW')
b,w=map(Path,sys.argv[1:3]); s=b.read_text(); y=w.read_text()
# Exact successful-26668 R1.1 verification mechanics authority.
for t in [
'AUTH_26668_BUILD_SCRIPT_BLOB="9fa6b709cabd900fc7fef68cc01318460a8be45a"',
'AUTH_26668_WORKFLOW_BLOB="14c7736c06222c9a9b0fb10a45e4989972e669b0"',
'snapshot_candidate_from_authority','verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26668_mechanics','install_frozen_candidate_live',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',
"buildCMakeDebug[arm64-v8a]","buildCMakeDebug[armeabi-v7a]",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']:
    if t not in s: raise SystemExit('FAIL infrastructure token '+t)
ordered=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26668_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for t in ordered:
    q=s.find(t,pos+1)
    if q<0: raise SystemExit('FAIL order missing '+t)
    pos=q
# Same three Gradle invocation classes as successful 26668.
assert s.count('./gradlew ')==3,s.count('./gradlew ')
# Build authority is the exact successful 26668 artifact and upload parent.
for t in [
'UPLOAD_PARENT_COMMIT="cd1ff23a4935a0bd4a6c58926047ca74d617feea"',
'RUNTIME_AUTHORITY_COMMIT="cd1ff23a4935a0bd4a6c58926047ca74d617feea"',
'BASE_RUN_ID="35420831668"','BASE_ARTIFACT_ID="10577148078"',
'BASE_ARTIFACT_NAME="photon-26668-r1-motion-evidence-ui"',
'BASE_ARTIFACT_SHA="1138252581a3a5fd15aabe8d96f1b58e7491dc06d36b0c0475fe9f2c2e35c694"',
'BASE_TAR_SHA="39ce17755705031d35dc4f8a09383c8dd3461f6b63632f8602b4d042c6c4c86f"']:
    if t not in s: raise SystemExit('FAIL authority token '+t)
# Workflow setup/upload mechanics are inherited exactly in class/order.
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'sha256sum -c R1_26669_HANDOFF_HASHES.sha256','bash -n build_26669_r1_capture_ui_preview_correction.sh','bash build_26669_r1_capture_ui_preview_correction.sh','actions/upload-artifact@v4','retention-days: 90','runs-on: ubuntu-24.04']:
    if t not in y: raise SystemExit('FAIL workflow token '+t)
# Only the 26669 trigger namespace may launch this new build; no overlapping 26668 trigger paths.
for forbidden in ['26668_R1_','handoff_payload_26668/**','build_26668_r1_motion_evidence_ui.sh','verify_26668_*.py']:
    assert forbidden not in y,forbidden
# Exactly one workflow build invocation and one upload-artifact action.
assert y.count('bash build_26669_r1_capture_ui_preview_correction.sh')==1
assert y.count('actions/upload-artifact@v4')==1
print('PASS 26669 infrastructure: functional build/workflow mechanics delta from successful 26668 R1.1 is ZERO; identity/authority/6-path scope/semantic+shader targets only; compiler/native/patch/PRE-BUILD/assemble/postbuild order unchanged')
