#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26706_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
required=[
'MECHANICS_AUTHORITY_COMMIT="9523e5d8a72e687385ba7fe9000072cb915404a1"',
'AUTH_26704_BUILD_SCRIPT_BLOB="02e9b9fc9ed02c30f01ca76af18cf7c67817174b"',
'AUTH_26704_WORKFLOW_BLOB="e7678fff1c3256d79ead17f8450bf67797dd3dc1"',
'AUTH_26705_R1_COMMIT="e6223da276e1eb439b572f17e0d4c2e959bf31f8"',
'AUTH_26705_R1_BUILD_SCRIPT_BLOB="df0004317fa1387c44209f6225d02b6d39697c53"',
'AUTH_26705_R1_WORKFLOW_BLOB="e01028079c65bdbbb67e34824526a6f5379d3350"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'build_26704_short_fusion_body_tone.sh','.github/workflows/build-26704-short-fusion-body-tone.yml',
'build_26705_normal_ae_short_headroom.sh','.github/workflows/build-26705-normal-ae-short-headroom.yml']
for t in required:assert t in s,t
# Permanent 26704 Actions regression: one pinned compiler, both aliases, before any Gradle/CMake stage.
assert s.count('export IRIS26706_GLSLANG="$compiler"')==1
assert s.count('export IRIS26681_SPEKTRA_GLSLANG="$compiler"')==1
prep=s[s.index('prepare_glslang(){'):s.index('compile_modified_runtime_shaders(){')]
for t in ['export IRIS26706_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:assert t in prep
# Permanent 26705 R1 regression: body-tone runtime owner stays inherited from 26704.
assert s.count("b'iris26704BodyToneStrength'")==1
assert s.count("b'iris26706BodyToneStrength'")==1  # explicit rejection assertion only
assert "assert not any(b'iris26706BodyToneStrength'" in s
marker='# IRIS_26706_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26704_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','verify_compiled_jni_callback','verify_compiled_motion_jni','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26706 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','verify_apk_jni_contract','postbuild_proof','26706 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
# Static shader scan must occur during candidate construction before real compiler stage.
assert s.index('python3 -S "$SHADERVERIFY" "$ROOT" "$BASE" "$AFTER" | tee') < s.index('prepare_glslang(){')
# Exact 26705 authority and successful wrapper blobs must be verified before candidate build continues.
for t in ['AUTH_26705_R1_BUILD_SCRIPT_BLOB','AUTH_26705_R1_WORKFLOW_BLOB','successful 26705 R1 build-script blob changed','successful 26705 R1 workflow blob changed']:assert t in s
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:assert t in w,t
wo=['Verify sealed 26706 handoff and exact successful 26704 mechanics + 26705 R1 regression','Build exact 26706 candidate from successful 26705 R1 compiled authority','Verify exact 26706 APK exists before artifact upload','Upload 26706 proof and APK']
pos=-1
for t in wo:
 n=w.find(t,pos+1);assert n>pos,('workflow order',t);pos=n
push=w.split('workflow_dispatch:',1)[0]
assert '26705_*' not in push and 'handoff_payload_26705' not in push
assert '26706_*' in push and 'handoff_payload_26706/**' in push
print('PASS 26706 infrastructure audit: exact successful 26704 compiler/build ordering + dual glslang handoff retained; successful 26705 R1 marker-verifier regression retained; only 26706 identity/scope/shader-count adaptations added')
