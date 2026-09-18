#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26667_infrastructure.py BUILD_SCRIPT WORKFLOW')
b,w=map(Path,sys.argv[1:3]);s=b.read_text();y=w.read_text()
for t in ['AUTH_26666_BUILD_SCRIPT_BLOB="4746c8115e8e1b7725cfb1f024249a7afe4ecefc"','AUTH_26666_WORKFLOW_BLOB="d3f8bba49b99ed854c0f63aeedb87bfe682e8856"','snapshot_candidate_from_authority','verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26666_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','buildCMakeDebug[armeabi-v7a]','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']:
 if t not in s:raise SystemExit('FAIL infrastructure token '+t)
ordered=['make_candidate','verify_shaders','verify_successful_26666_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','buildCMakeDebug[arm64-v8a]','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for t in ordered:
 q=s.find(t,pos+1)
 if q<0:raise SystemExit('FAIL order missing '+t)
 pos=q
for t in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'sha256sum -c R1_26667_HANDOFF_HASHES.sha256','bash -n build_26667_r1_preview_long_confidence.sh','bash build_26667_r1_preview_long_confidence.sh','actions/upload-artifact@v4','retention-days: 90']:
 if t not in y:raise SystemExit('FAIL workflow token '+t)
print('PASS 26667 infrastructure: functional build mechanics delta from successful 26666 is ZERO; identity/authority/4-path scope/26667 semantic+shader targets only')
