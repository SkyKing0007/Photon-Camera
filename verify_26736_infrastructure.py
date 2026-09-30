#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26736_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
AUTH='271f52be81d8222e5f04fdfd0e9085a55bbd5e2c'
AUTH_FILES={
'.github/workflows/build-26735-neutral-chroma-digital-luma-retry.yml':'7080a4699e6f81906f842e826c0620f087ac71be4ddeedc902493a8417b25434',
'build_26735_neutral_chroma_digital_luma_retry.sh':'79559e5c3160f19aed015cb59de65d701c23dcbc1169bc6a30b3292f1c180542',
'transform_26735.py':'4fa57aabac511692b138469ff46fd9400eaf7712ac9102fc7d277d200ea4fb47',
'validate_26735.py':'c33b88e97b5a5f2cf69f91cfd2a3029c2e257358a542cbaaa2bbd9e5db43a51a',
'verify_26735_authority.py':'8e968f462fc7141bae6f002df9376369ffc78222eb7320f323686afefa60871f',
'verify_26735_infrastructure.py':'768c47b23ea36c4c131f8079e4e8629703f712b5eb79f03fb6f7e4b94160f948',
'verify_26735_patches.py':'9c8a1fb56b61f43cf045210dc39d5aa2292f62d622e5f6f395134c004efbc569',
'verify_26735_regressions.py':'d58f4b948103b6296c7892ba7f1ce18b0da116a3aa1195157659883220c0f73f',
'verify_26735_shaders.py':'3df25820f8f19355f4eced101642b23c967f13f5b6c570f445cb96fe6fcf6b8e',
}
if Path('.git').exists():
 for path,h in AUTH_FILES.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}']); assert hashlib.sha256(data).hexdigest()==h,('successful 26735 infrastructure authority drift',path)
for t in [f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"',f'MECHANICS_AUTHORITY_COMMIT="{AUTH}"','BASE_RUN_ID="36637337435"','BASE_ARTIFACT_ID="11064304462"','BASE_ARTIFACT_NAME="photon-26735-neutral-chroma-digital-luma-retry"','BASE_ARTIFACT_SHA="37b6ef1cf0735403765291f15fe7b639d67d1ff406a54617b639e97221bbf8bd"','BASE_TAR_SHA="8159fbf01e8e02d8d4a0480dd2bc53348f2e57938f63111db7fd69a6ac76ba0a"','VERSION_NAME="0.9726736"','VERSION_BUILD="26736"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"','EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26736_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"']:
 assert t in s,t
marker='# IRIS_26736_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26735_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26736 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26736 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('successful-26735 stage order drift',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26736_wronski_phase_integrity.sh']:
 assert t in s+w,t
assert 'git commit' not in main and 'git push' not in main and 'backup' not in main.lower()
# Permanent failed-26734 regression: current verifier compiles exact base and exact candidate; no obsolete fixed manifest is applied to changed shader bytes.
assert 'IRIS_26736_CURRENT_AUTHORITY_BASE_SHADER_REPLAY' in s
assert 'python3 -S verify_26736_shaders.py "$ROOT" "$BASE" "$BASE" --base-only --compiler "$IRIS26736_GLSLANG"' in s
assert 'python3 -S verify_26736_shaders.py "$ROOT" "$BASE" "$AFTER" --compiler "$IRIS26736_GLSLANG"' in s
compile_body=s[s.index('compile_modified_runtime_shaders(){'):s.index('compile_spektra_raw_shader(){')]
assert 'verify_26735_shaders.py' not in compile_body and 'verify_26727_shaders.py' not in compile_body
assert 'compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -o -type l -name glslangValidator -print -quit)"' in s
assert '"$(find handoff_payload_26736 -type f|wc -l)" -eq 3' in s and '"$(wc -l < 26736_RUNTIME_CHANGED_PATHS.txt)" -eq 3' in s
# Workflow is uniquely scoped so uploading 26736 stage-1 files does not match 26735 workflow path prefixes.
assert "- '26736_*'" in w and "- 'handoff_payload_26736/**'" in w and '.github/workflows/build-26736-wronski-phase-integrity.yml' in w
print('PASS 26736 infrastructure: exact successful 26735 nine-role authority hash-pinned; compiler/build stage order unchanged; current-authority base + exact candidate shader compilation prevents stale-manifest recurrence; no backup/commit/push')
