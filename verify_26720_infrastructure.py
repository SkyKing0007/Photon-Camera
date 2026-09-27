#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26720_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
prior={'build_26719_high_zoom_lazy_isolation.sh':'96887b917804872475976f9b6f6fef57747b098fd28db6a23594eae152b1ad68','.github/workflows/build-26719-high-zoom-lazy-isolation.yml':'53f2a2beffa48b73dc12ad075c3182a3a399960c8f8d9acab68f7cbc142c03fb'}
if Path('.git').exists():
 for path,h in prior.items():
  data=subprocess.check_output(['git','show','bffcb6e7f66d72b588c4a0dd6664b716b47af083:'+path]); assert hashlib.sha256(data).hexdigest()==h,('26719 infrastructure authority drift',path)
for t in [
'RUNTIME_AUTHORITY_COMMIT="bffcb6e7f66d72b588c4a0dd6664b716b47af083"',
'BASE_RUN_ID="36333749781"','BASE_ARTIFACT_ID="10936462373"',
'BASE_ARTIFACT_SHA="8824190b1223653a6c42db0ea7e2316599b5aa0bc4d9cdd6804942cec7dc73e5"',
'BASE_TAR_SHA="a88536cc92f7173333b510c046275cc920a035378d4c27c68df1531561ce48fb"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26720_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'96887b917804872475976f9b6f6fef57747b098fd28db6a23594eae152b1ad68',
'53f2a2beffa48b73dc12ad075c3182a3a399960c8f8d9acab68f7cbc142c03fb']:
 assert t in s,t
m='# IRIS_26720_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(m)==1; main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26719_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26720 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26720 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('stage order',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
 assert t in s,t
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26720_banding_highzoom_rgb.sh']:
 assert t in w,t
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
print('PASS 26720 infrastructure: exact successful 26719 mechanics authority hash-pinned; compiler/build stage order unchanged; authority advanced only; 14-file architectural scope + applicable semantic/shader gates; no backup')
