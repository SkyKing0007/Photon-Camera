#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26717_infrastructure.py BUILD_SCRIPT WORKFLOW')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
# Exact committed 26716 procedural authority must still be present and byte-exact.
up={
'build_26716_native_iris_log_storage.sh':'4821562a7d5a5423a3abb72df399b3c7645e990853cb741a8232de45828bb708',
'.github/workflows/build-26716-native-iris-log-storage.yml':'279d346dea849ea291588ea28453893cb6dbb18525ed9171ad4916bcf85d583c',
'transform_26716.py':'181a36e6db93a3f877ba3f41e5e521bede2ecb331d2802e829feadba436bd06c',
'validate_26716.py':'33d25f8b6408a2cdbd48399a86d094d9e116ca7b01db3e9b48cec89d91c3d35e',
'verify_26716_authority.py':'f28dc4f7cabaf793dbe2d46797fc9c65e27822c57dee689d39ad1eb8f973dc17',
'verify_26716_infrastructure.py':'4507bcc9e6380bf1ff38105f302ff549e3e09e820c15f6e3c7ab075eb964fe20',
'verify_26716_patches.py':'6e6b08a03d9b96773e9b3e71bbf376b55f928f83a9df682082d010c92889fb9b',
'verify_26716_regressions.py':'5b020a7ed4cd750d021b61711cbf98f5e4fdd7d108835ba74362acb8626abf8b',
'verify_26716_shaders.py':'be41771a97ab2449c2487554bebb34e4114133de8779e17b0b1122df735ec485'}
# The exact 26716 SHA-256 values are immutable procedural authority. The current 26717
# files are normalized below and must reproduce those bytes exactly; no live repository lookup
# is required for clean-extract replay.

# Prove the non-storage mechanics are byte-identical to 26716 after identifier normalization.
normalized={
 'transform_26717.py':('transform_26716.py','181a36e6db93a3f877ba3f41e5e521bede2ecb331d2802e829feadba436bd06c'),
 'validate_26717.py':('validate_26716.py','33d25f8b6408a2cdbd48399a86d094d9e116ca7b01db3e9b48cec89d91c3d35e'),
 'verify_26717_authority.py':('verify_26716_authority.py','f28dc4f7cabaf793dbe2d46797fc9c65e27822c57dee689d39ad1eb8f973dc17'),
 'verify_26717_patches.py':('verify_26716_patches.py','6e6b08a03d9b96773e9b3e71bbf376b55f928f83a9df682082d010c92889fb9b'),
 'verify_26717_shaders.py':('verify_26716_shaders.py','be41771a97ab2449c2487554bebb34e4114133de8779e17b0b1122df735ec485')}
for new,(old,h) in normalized.items():
 data=Path(new).read_text().replace('26717','26716').encode()
 assert hashlib.sha256(data).hexdigest()==h,('normalized 26716 mechanics drift',new)
# The 26717 build script mechanically back-transforms to the exact 26716 build bytes.
back=s.replace('26717','26716').replace('downloads_iris_log_storage','native_iris_log_storage').replace('downloads-iris-log-storage','native-iris-log-storage').replace('0.9726717','0.9726716')
back=back.replace('# IRIS_26716_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- identical 26716 ordering and exact successful-26715 compiler/build mechanics','# IRIS_26716_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- identical successful-26715 ordering')
assert hashlib.sha256(back.encode()).hexdigest()==up['build_26716_native_iris_log_storage.sh']
# The workflow likewise back-transforms exactly after restoring the two descriptive step titles.
backw=w.replace('26717','26716').replace('Downloads Iris Log Storage','Native Iris Log Storage').replace('downloads_iris_log_storage','native_iris_log_storage').replace('downloads-iris-log-storage','native-iris-log-storage').replace('0.9726717','0.9726716')
backw=backw.replace('Verify sealed 26716 handoff and exact 26716 procedure inheritance','Verify sealed 26716 handoff and exact successful 26715 mechanics')
backw=backw.replace('Build exact 26716 candidate with 26716 procedure from successful 26715 compiled authority','Build exact 26716 candidate from successful 26715 compiled authority')
assert hashlib.sha256(backw.encode()).hexdigest()==up['.github/workflows/build-26716-native-iris-log-storage.yml']
for t in [
'RUNTIME_AUTHORITY_COMMIT="86ac112cf76f28f317c8ecdba9c16a1e788dbb4c"',
'BASE_RUN_ID="36282010855"','BASE_ARTIFACT_ID="10919491403"',
'BASE_ARTIFACT_SHA="7729bda8f55dcf2b83c46e15517143a78e541c583c2aa11e0bd3202d7af3c1b5"',
'BASE_TAR_SHA="1dd96bc7046d288e09050447d589652728a71fedf14098bfa394ad69462c84a0"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26717_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'f08b3f9ed5804655d21ad97f095977a8d3d750b44e7e64b3d9a1261fe1742b42',
'31a0b517712473305ba5992b0847197fe2aaa63112f9479e76060b2f060fa115']:
 assert t in s,t
m='# IRIS_26717_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(m)==1;main=s[s.index(m):]
# Exact 26716 execution ordering; only build-number/output names change.
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26715_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26717 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26717 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1);assert n>pos,('stage order',t);pos=n
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26717_downloads_iris_log_storage.sh']:
 assert t in w,t
assert 'python3 -S verify_26717_infrastructure.py build_26717_downloads_iris_log_storage.sh .github/workflows/build-26717-downloads-iris-log-storage.yml' in w
assert 'from successful 26715 compiled authority' in w
assert 'backup' not in s.lower()
print('PASS 26717 infrastructure: exact 26716 procedure authority hash-pinned; identical 26716 Actions stage order retained; successful 26715 compiled authority and compiler/build sequence unchanged; no backup')
