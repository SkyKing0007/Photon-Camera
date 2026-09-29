#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26734r1_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
AUTH='2f0ab8637816acd91a3a4ee331de910a47cad147'
AUTH_FILES={
'.github/workflows/build-26733-highlight-safe-color-integrity.yml':'6fa86f4d0b829f577a3517dd55ad8e9b78495b8c92739257c5ca37aad7e6b485',
'build_26733_highlight_safe_color_integrity.sh':'173b0fa6be81abe91aca5a6241224c84474468c059563337c9866139d3a70529',
'transform_26733.py':'f4784df0a5456f0a18ca5bdc321e3e0ccf1fb490928a87cfd751517268912d52',
'validate_26733.py':'1eb25ed25829c7e80108a2da90b6199e56a8a6ee6a0a17f07c11c26e77a2f102',
'verify_26733_authority.py':'90db29328ed10a92b2b07a442f8ff8c57f340eb532b7b4e3d5a55ec2901a746d',
'verify_26733_infrastructure.py':'62326bb00db882764f895b14e16ad638e2a64b4c44f44f40dd137cba235d590b',
'verify_26733_patches.py':'5916d5cedbbc93ac6a014ec5e5ba6a61048abaf2a1d9f003f25b6ce8e513a3a2',
'verify_26733_regressions.py':'f8d1568e22b15b722fa0a1fa8b0f4590cd980ed1301f7124e70144b401d42ed1',
'verify_26733_shaders.py':'5d7fdd960f6d8f002b3d575e4321193491ab7e9cd396caa466e8bf7097830ac5'}
if Path('.git').exists():
 for path,h in AUTH_FILES.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}']); assert hashlib.sha256(data).hexdigest()==h,('successful 26733 infrastructure authority drift',path)
for t in [f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"',f'MECHANICS_AUTHORITY_COMMIT="{AUTH}"','BASE_RUN_ID="36569631787"','BASE_ARTIFACT_ID="11033487736"','BASE_ARTIFACT_NAME="photon-26733-highlight-safe-color-integrity"','BASE_ARTIFACT_SHA="d27333374b4ab1dea2ea4bdb2deed85eab603b44a4eea5a65e4e343665becb52"','BASE_TAR_SHA="6feaf5ef8718f2d60ba6448393b31872644f56407eb89e6aa847f43381a34009"','PRIOR_INHERITED_SHADER_VERIFIER_SHA="180fa8f0daed736bb5453dd1dbfda93f28aa34e0b6309f818a04be48e0f3b645"','VERSION_NAME="0.9726734"','VERSION_BUILD="26734"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26734R1_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:
 assert t in s,t
marker='# IRIS_26734R1_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26733_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26734 R1 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26734 R1 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('successful-26733 stage order drift',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26734r1_all_digital_zoom_achromatic_sr.sh']:
 assert t in s+w,t
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
# Exact failure regression: stale 26727 candidate manifest may not be applied to intentional 26734 SR shader bytes.
assert 'IRIS_26734R1_STALE_26727_MANIFEST_REPAIR' in s
assert 'verify_26727_shaders.py "$ROOT" "$BASE" "$BASE" --compiler "$IRIS26734R1_GLSLANG"' in s
assert 'verify_26727_shaders.py "$ROOT" "$BASE" "$AFTER"' not in s
assert 'verify_26734r1_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26734R1_GLSLANG"' in s
assert 'compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"' in s
assert 'sha256sum verify_26727_shaders.py | grep -F "$PRIOR_INHERITED_SHADER_VERIFIER_SHA"' in s
print('PASS 26734 R1 infrastructure: successful 26733 stage order/compiler/build mechanics exact; stale 26727 candidate-manifest misuse permanently blocked; inherited base gate retained; exact 26734 candidate shader gate retained; no backup/commit/push')
