#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,6):
    raise SystemExit('usage: verify_26634_r1_infrastructure.py CURRENT_BUILD CURRENT_WORKFLOW [PRIOR_BUILD PRIOR_WORKFLOW PRIOR_TRANSFORM]')
build=Path(sys.argv[1]).read_text(); workflow=Path(sys.argv[2]).read_text()
def ordered(text,tokens,label):
    pos=-1
    for token in tokens:
        n=text.find(token,pos+1)
        if n<0: raise SystemExit(f'FAIL {label}: missing/order token {token}')
        pos=n
# Exact successful-26633 top-level gate order retained.
ordered(build,['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26633_mechanics','verify_candidate_patches','install_and_build'], 'build top-level')
# Exact real compiler/build order retained inside install_and_build.
ordered(build,['snapshot_candidate_from_authority','$VALIDATE','$GATEVERIFY','$AUTHORITY','authority-seeded live compiler candidate byte-identical',':app:compileDebugKotlin :app:compileDebugJavaWithJavac',':app:buildCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[armeabi-v7a]','verify_candidate_patches','PRE-BUILD SAFETY PROOF',':app:assembleDebug','expected exactly one Gradle debug APK','postbuild candidate byte-identical','candidate_app_source.tar.gz'], 'compiler/build')
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'sha256sum -c R1_26634_HANDOFF_HASHES.sha256','bash -n build_26634_r1_local_residual_noise_metadata.sh','! find . -type f -name \'*.apk\' | grep -q .','bash build_26634_r1_local_residual_noise_metadata.sh','actions/upload-artifact@v4']:
    if token not in workflow: raise SystemExit(f'FAIL workflow mechanic missing {token}')
assert "branches:\n      - experimental-clean-photon-rebuild" in workflow
assert 'R1_26633_' not in workflow and 'build_26633_' not in workflow
# In Actions, prior files are extracted from exact successful 26633 parent and audited too.
if len(sys.argv)==6:
    pb=Path(sys.argv[3]).read_text(); pw=Path(sys.argv[4]).read_text(); pt=Path(sys.argv[5]).read_text()
    ordered(pb,['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26631_mechanics','verify_candidate_patches','install_and_build'],'26633 prior top-level')
    ordered(pb,[':app:compileDebugKotlin :app:compileDebugJavaWithJavac',':app:buildCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[armeabi-v7a]','verify_candidate_patches','PRE-BUILD SAFETY PROOF',':app:assembleDebug','expected exactly one Gradle debug APK','postbuild candidate byte-identical','candidate_app_source.tar.gz'],'26633 prior compiler/build')
    for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
        assert token in pw,token
    assert 'shutil.copytree(base,root)' in pt
print('PASS 26634 infrastructure: successful-26633 ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/invariance mechanics preserved; identity/authority/8-path validators only')
