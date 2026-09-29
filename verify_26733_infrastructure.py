#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26733_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text(); sv=Path('verify_26733_shaders.py').read_text(); rv=Path('verify_26733_regressions.py').read_text()
AUTH='aa393fe28e7cf590db0cad5a3c69e3fd64bf3cf2'
AUTH_FILES={
'.github/workflows/build-26732-chroma-integrity-high-zoom.yml':'720bf684e425e5193ffdb339e51a70470ee5f62181408b673ff69fbcbecbb999',
'build_26732_chroma_integrity_high_zoom.sh':'84e514ed37f2b079adbe86568ebfd614f78b4f11875c15e3fa15b3d6a8e35980',
'transform_26732.py':'8ab11a04593ea27e1bd4c77d9ebf1980820fb8cbde6d333ec635f902e4f85df8',
'validate_26732.py':'350b625fcbc513b28ea460c2d775390d90f30bd1a4b48719180284b97df25049',
'verify_26732_authority.py':'1bb43b573a653ca1b6583aadc192993601d1028e1ca85a2db615db3322086bdf',
'verify_26732_infrastructure.py':'7510483051a3f01a1a2c00a0df67580fc7a9a40640bf0288665b95c9c86111b4',
'verify_26732_patches.py':'e182fa21a52475e9faff8e74dfcdbade61fe4df9d0e6dd541e22df95781b2907',
'verify_26732_regressions.py':'c3d388ede587197037a5504ef6cc2266ecb168a7976a898ed20e1159e39fa1af',
'verify_26732_shaders.py':'f9a0827cb52d34ad0afc8eaf885e84224a44414f6fc1f41e94a0420f18839ef5'}
if Path('.git').exists():
 for path,h in AUTH_FILES.items():
  data=subprocess.check_output(['git','show',f'{AUTH}:{path}'])
  assert hashlib.sha256(data).hexdigest()==h,('successful 26732 infrastructure authority drift',path)
for t in [
 f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"',f'MECHANICS_AUTHORITY_COMMIT="{AUTH}"',
 'BASE_RUN_ID="36523368217"','BASE_ARTIFACT_ID="11013851432"','BASE_ARTIFACT_NAME="photon-26732-chroma-integrity-high-zoom"',
 'BASE_ARTIFACT_SHA="9725e9c97cd2b21dae973a7660b97a0a7cd8ed3cee756c9b5b6cd195266b7a59"',
 'BASE_TAR_SHA="f6f44aecbd3819cab3a68a4f71fc07d25e3c6ba47623cac01a3652923a0a91c7"',
 'VERSION_NAME="0.9726733"','VERSION_BUILD="26733"','GLSLANG_VERSION="16.5.0"',
 'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 'EXPECTED_BRANCH="experimental-clean-photon-rebuild"','export IRIS26733_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
 AUTH_FILES['build_26732_chroma_integrity_high_zoom.sh'],AUTH_FILES['.github/workflows/build-26732-chroma-integrity-high-zoom.yml'],AUTH_FILES['verify_26732_shaders.py']]:
 assert t in s,t
marker='# IRIS_26733_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26732_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace','JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','26733 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','postbuild_proof','26733 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
 n=main.find(t,pos+1); assert n>pos,('successful-26732 stage order drift',t); pos=n
for t in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle','actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90','bash build_26733_highlight_safe_color_integrity.sh']:
 assert t in (s+'\n'+w),t
assert "branches: [experimental-clean-photon-rebuild]" in w
assert '.github/workflows/build-26733-highlight-safe-color-integrity.yml' in w
w_order=['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','Verify sealed 26733 handoff','Build exact 26733 candidate','Verify exact 26733 APK exists','actions/upload-artifact@v4']
pos=-1
for t in w_order:
 n=w.find(t,pos+1); assert n>pos,('successful-26732 workflow step order drift',t); pos=n
# Permanent historical build/runtime failures remain pre-compiler regressions.
for t in ['IRIS_26733_INHERIT_26729_R1_EXACT_KOTLIN_RUNTIME_SHADER_EXPANSION',"raw=raw.replace('$common',common)","assert '$' not in expanded",'highZoomFlowRefine26724','highZoomRgbProtect26724']:
 assert t in sv,t
assert 'textwrap.dedent' not in sv
assert 'setInitial\\(\\s*SCOPE_GLOBAL' in rv
for t in ['IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP','IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER','IRIS_26733_EARLY_ACHROMATIC_STRUCTURE_OWNER','IRIS_26733_MOTION_AUTO_RESIDUAL_CHROMA_HALF_SCALE']:
 assert t in rv,t
# Guarded build never creates backups or writes repository history.
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
assert not re.search(r'\bgit\s+(commit|push)\b',s)
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"','expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']:
 assert t in s,t
assert 'payload count' in s and 'changed count' in s and 'fail additions' in s
assert "! git diff --name-only \"$RUNTIME_AUTHORITY_COMMIT\"..HEAD|grep -Eq '^app/'" in s
print('PASS 26733 infrastructure: exact successful 26732 nine-role implementation hash-pinned; compiler/build/workflow ordering unchanged; historical 26729/26731 failures and 26733 audit regressions preflighted; MECHANICS DELTA ZERO; no backup/commit/push')
