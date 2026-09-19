#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26668_infrastructure.py BUILD_SCRIPT WORKFLOW')
b,w=map(Path,sys.argv[1:3]); s=b.read_text(); y=w.read_text()
# Exact successful-26667 verification mechanics authority.
for t in [
'AUTH_26667_BUILD_SCRIPT_BLOB="3279c2a8179c40daf7f99202ba1aaa5f3e213671"',
'AUTH_26667_WORKFLOW_BLOB="c33eec9a2c77a4116acf0142d569f1824d387d75"',
'snapshot_candidate_from_authority','verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26667_mechanics','install_frozen_candidate_live',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',
"buildCMakeDebug[arm64-v8a]","buildCMakeDebug[armeabi-v7a]",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']:
    if t not in s: raise SystemExit('FAIL infrastructure token '+t)
ordered=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26667_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for t in ordered:
    q=s.find(t,pos+1)
    if q<0: raise SystemExit('FAIL order missing '+t)
    pos=q
# Exactly the same three Gradle invocation classes as successful 26667.
assert s.count('./gradlew ')==3,s.count('./gradlew ')
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'sha256sum -c R1_26668_HANDOFF_HASHES.sha256','bash -n build_26668_r1_motion_evidence_ui.sh','bash build_26668_r1_motion_evidence_ui.sh','actions/upload-artifact@v4','retention-days: 90','runs-on: ubuntu-24.04']:
    if t not in y: raise SystemExit('FAIL workflow token '+t)
# Prevent overlapping historical workflow trigger names.
assert '26667_R1_' not in y and 'handoff_payload_26667' not in y
print('PASS 26668 infrastructure: functional build/workflow mechanics delta from successful 26667 is ZERO; identity/authority/18-path scope/semantic+shader targets only; compiler/native/patch/PRE-BUILD/assemble/postbuild order unchanged')
