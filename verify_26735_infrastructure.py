#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26735_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
AUTH='ff1eb4d7969c81070d86b8a2df1d2b8c42b2436e'
AUTH_FILES={
'.github/workflows/build-26734r1-all-digital-zoom-achromatic-sr.yml':'2591923eefd6c496bbafa0840945ec26331eb937d3e9a2a23cf44992c75fa1be',
'build_26734r1_all_digital_zoom_achromatic_sr.sh':'136d835fffaf8f0455787f773e375364008ea48dc191ee20538084a3f105bba2',
'transform_26734r1.py':'b0930a4e6da6b4f485afc3dbc9e61740bce5a5f81a3b076cacab43f23565b494',
'validate_26734r1.py':'4e62e1c8a55fd5142b84d41ce968b37c906c81c8920b138041756c1f754912c9',
'verify_26734r1_authority.py':'e728d690b1b95fe659b717fb1f47baa7de9d750d43839041899f1d8650cf028c',
'verify_26734r1_infrastructure.py':'d979ff87d967b5f1b8840759bbf881a5e5303f5b2c513218d13b153e527ebfe5',
'verify_26734r1_patches.py':'8b10b0264aaf4dbd8e71b77418a1c6ce413c8c998fcdd28308d0b10af9beb1e7',
'verify_26734r1_regressions.py':'0c9fe6e94fb8eeaa7d013e8aff3e8f55d51834622486b38a60468b98a6bc76d0',
'verify_26734r1_shaders.py':'ce036d5f1433974ab7d7af717bac340e105f45df5405c64903335f74b3766e90',
}
if Path('.git').exists():
 for path,h in AUTH_FILES.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}']); assert hashlib.sha256(data).hexdigest()==h,('successful 26734 R1 infrastructure authority drift',path)
for t in [f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"',f'MECHANICS_AUTHORITY_COMMIT="{AUTH}"','BASE_RUN_ID="36600235506"','BASE_ARTIFACT_ID="11049405399"','BASE_ARTIFACT_NAME="photon-26734-r1-all-digital-zoom-achromatic-sr"','BASE_ARTIFACT_SHA="378d7fc175f1d6f1c6015eef08eecd29310998f7528c1809208918e79d968a31"','BASE_TAR_SHA="5f9cec5009e6599d2566c7f86df78628e8551a4e5d1214ba1d93689809f7033c"','VERSION_NAME="0.9726735"','VERSION_BUILD="26735"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26735_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:
 assert t in s,t
marker='# IRIS_26735_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26734r1_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26735 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26735 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('successful-26734R1 stage order drift',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26735_neutral_chroma_digital_luma_retry.sh']:
 assert t in s+w,t
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
# Permanent failure regression: never apply obsolete 26727 fixed manifest to current R1 or 26735 shader bytes.
assert 'IRIS_26735_CURRENT_AUTHORITY_BASE_SHADER_REPLAY' in s
assert 'verify_26727_shaders.py' not in s
assert 'verify_26735_shaders.py "$ROOT" "$BASE" "$BASE" --base-only --compiler "$IRIS26735_GLSLANG"' in s
assert 'verify_26735_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26735_GLSLANG"' in s
assert 'compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"' in s
# Exact changed-file count and no source writes before deterministic candidate construction.
assert 'payload count' in s and 'changed count' in s and 'fail additions' in s
print('PASS 26735 infrastructure: exact successful 26734 R1 nine-role authority hash-pinned; stage order/compiler/build mechanics unchanged; current-authority base shader replay replaces stale 26727 manifest misuse; no backup/commit/push')
