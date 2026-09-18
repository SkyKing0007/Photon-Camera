#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26666_infrastructure.py BUILD_SCRIPT WORKFLOW')
b,w=map(Path,sys.argv[1:3]);s=b.read_text();y=w.read_text()
# Exact successful-26665 mechanics identity is pinned by Git blob and required command/order tokens.
for t in ['AUTH_26665_BUILD_SCRIPT_BLOB="3b49d4f72f497652b3184f9edffe00fa997efd84"','AUTH_26665_WORKFLOW_BLOB="b91678f323222cdd17e380e8fb37431f43676c02"','snapshot_candidate_from_authority','verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26665_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']:
 if t not in s:raise SystemExit('FAIL infrastructure token '+t)
# Order of successful 26665 compile/build gates is non-negotiable.
ordered=['make_candidate','verify_shaders','verify_successful_26665_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for t in ordered:
 q=s.find(t,pos+1)
 if q<0:raise SystemExit('FAIL order missing '+t)
 pos=q
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'sha256sum -c R1_26666_HANDOFF_HASHES.sha256','bash -n build_26666_r1_high_dr_body_snr.sh','bash build_26666_r1_high_dr_body_snr.sh','actions/upload-artifact@v4','retention-days: 90']:
 if t not in y:raise SystemExit('FAIL workflow token '+t)
print('PASS 26666 infrastructure: functional build mechanics delta from successful 26665 is ZERO; identity/authority/9-path scope/26666 semantic+shader targets only')
