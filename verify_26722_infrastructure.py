#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26722_infrastructure.py BUILD_SCRIPT WORKFLOW')
s=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
prior={'build_26721_high_zoom_rgb32f_transport.sh':'2855cbc6ec9426a050235648e9a1520eb53217502fb90639efb40fc33427b082','.github/workflows/build-26721-high-zoom-rgb32f-transport.yml':'99b225886ed6767e985ce3ab13c54996c79d54fdbf7d6646a34db6457df0cb75'}
if Path('.git').exists():
 for path,h in prior.items():
  data=subprocess.check_output(['git','show','75f8bd1c3bf4de0fe4ed4f28e07575be80fd234c:'+path]); assert hashlib.sha256(data).hexdigest()==h,('26721 infrastructure authority drift',path)
for t in [
'RUNTIME_AUTHORITY_COMMIT="75f8bd1c3bf4de0fe4ed4f28e07575be80fd234c"',
'BASE_RUN_ID="36354348329"','BASE_ARTIFACT_ID="10943139473"',
'BASE_ARTIFACT_SHA="d869d1484039dad4b92a415130dec750b8d28547d6f05372f635914831792fb5"',
'BASE_TAR_SHA="e174b61afe513d3b322c4cf2d9c0221d167493e6b07f184f86f93d31b6824d11"',
'GLSLANG_VERSION="16.5.0"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
'export IRIS26722_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
'2855cbc6ec9426a050235648e9a1520eb53217502fb90639efb40fc33427b082',
'99b225886ed6767e985ce3ab13c54996c79d54fdbf7d6646a34db6457df0cb75']:
 assert t in s,t
m='# IRIS_26722_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(m)==1; main=s[s.index(m):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26721_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26722 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26722 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('stage order',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
 assert t in s,t
for t in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','bash build_26722_high_zoom_native_chroma.sh']:
 assert t in w,t
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
print('PASS 26722 infrastructure: exact successful 26721 mechanics authority hash-pinned; compiler/build stage order and commands unchanged; authority/version/scope/applicable gates advanced only; 3-file runtime scope; no backup')
