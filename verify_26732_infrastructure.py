#!/usr/bin/env python3
from pathlib import Path
import hashlib, subprocess, sys, re
if len(sys.argv)!=3:
    raise SystemExit('usage: verify_26732_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2])
s=build.read_text(); w=workflow.read_text()
sv=Path('verify_26732_shaders.py').read_text(); rv=Path('verify_26732_regressions.py').read_text()
AUTH='67d01c2ac10ba7784d934b4dc48cb584513c5b23'
AUTH_FILES={
'.github/workflows/build-26731-frozen-material-chroma-transport.yml':'54ff7ca8df9f884f7d85c1fe2ba1df288a5357f9131577a452d47961e55d5956',
'build_26731_frozen_material_chroma_transport.sh':'58540951bb0dd0e6d928e9b7db2c92fcb1cc1c755626a1b318e95b2d229515cd',
'transform_26731.py':'43fa4d4b2839dbc3d6aa482d7461b68f8320f1d26dd8935fe4900c8d3ba52ce8',
'validate_26731.py':'18f7876a267b0ae43ba11bb1ab15f39fcde865669e94cd24dd7425ec3012d0a8',
'verify_26731_authority.py':'b3538f7af39193d4e6c6082c57ffc4dd2e22fc8a93a3f58444d5da5df9206684',
'verify_26731_infrastructure.py':'ad43b160da70e72faa16c2711094efede2a48b1e99b4675908f03eb7b6371688',
'verify_26731_patches.py':'16e0f0c6db3d13b80746bcee6eda3e176b20242104422c416df754709ecc9219',
'verify_26731_regressions.py':'b90f5330669a28c31bb1a6fb8d5e60b06f0f39ff277162197b1d9ccff6d589d3',
'verify_26731_shaders.py':'cd01dd9a995a5e6fadb2229b0640848af286d4ce5fba9c99d830fc3cd8140b30'}
# Synthetic fixtures are insufficient for handoff mechanics: on Actions, pin every
# successful-26731 infrastructure role against the actual successful commit.
if Path('.git').exists():
    for path,h in AUTH_FILES.items():
        data=subprocess.check_output(['git','show',f'{AUTH}:{path}'])
        assert hashlib.sha256(data).hexdigest()==h,('successful 26731 infrastructure authority drift',path)
for t in [
    f'RUNTIME_AUTHORITY_COMMIT="{AUTH}"', f'MECHANICS_AUTHORITY_COMMIT="{AUTH}"',
    'BASE_RUN_ID="36517535564"','BASE_ARTIFACT_ID="11012335104"',
    'BASE_ARTIFACT_NAME="photon-26731-frozen-material-chroma-transport"',
    'BASE_ARTIFACT_SHA="ec1d4104091b35911508e4d9811bea5583830316e05c589f4b8e63d5abe715b1"',
    'BASE_TAR_SHA="7a3a91d8c9da26a3f76dd83e15c4545b3dcaf0e85648427a5024606e275232e1"',
    'VERSION_NAME="0.9726732"','VERSION_BUILD="26732"','GLSLANG_VERSION="16.5.0"',
    'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
    'EXPECTED_BRANCH="experimental-clean-photon-rebuild"',
    'export IRIS26732_GLSLANG="$compiler"','export IRIS26681_SPEKTRA_GLSLANG="$compiler"',
    AUTH_FILES['build_26731_frozen_material_chroma_transport.sh'],
    AUTH_FILES['.github/workflows/build-26731-frozen-material-chroma-transport.yml'],
    AUTH_FILES['verify_26731_shaders.py']]:
    assert t in s,t
marker='# IRIS_26732_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
# Exact successful-26731 execution order; names advance only with the build number.
order=[
 'verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26731_mechanics',
 'prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 'JNI callback/motion ABI compiler checkpoint','after_language_compiler_snapshot',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches','26732 PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace',
 'postbuild_proof','26732 ACTIONS BUILD COMPLETE']
pos=-1
for t in order:
    n=main.find(t,pos+1); assert n>pos,('successful-26731 stage order drift',t); pos=n
for t in [
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 './gradlew :app:assembleDebug --stacktrace','runs-on: ubuntu-24.04','actions/checkout@v5','fetch-depth: 0',
 'actions/setup-java@v5','distribution: temurin',"java-version: '17'",'cache: gradle',
 'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','retention-days: 90',
 'bash build_26732_chroma_integrity_high_zoom.sh']:
    assert t in (s+'\n'+w),t
assert "branches: [experimental-clean-photon-rebuild]" in w
assert '.github/workflows/build-26732-chroma-integrity-high-zoom.yml' in w
# Workflow job/step sequence is the successful-26731 sequence.
w_order=['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5',
 'Verify sealed 26732 handoff','Build exact 26732 candidate','Verify exact 26732 APK exists','actions/upload-artifact@v4']
pos=-1
for t in w_order:
    n=w.find(t,pos+1); assert n>pos,('successful-26731 workflow step order drift',t); pos=n
# Permanent 26729 R1/R2 failures and 26731 runtime-lazy-anchor failure are pre-compiler gates.
for t in ['IRIS_26732_INHERIT_26729_R1_EXACT_KOTLIN_RUNTIME_SHADER_EXPANSION',
          "raw=raw.replace('$common',common)","assert '$' not in expanded",
          'highZoomFlowRefine26724','highZoomRgbProtect26724']:
    assert t in sv,t
assert 'textwrap.dedent' not in sv
assert 'setInitial\\(\\s*SCOPE_GLOBAL' in rv
for t in ['IRIS_26732_DIRECT_HIGH_ZOOM_FLOW_RUNTIME_OWNER','IRIS_26732_DIRECT_HIGH_ZOOM_RGB_RUNTIME_OWNER',
          'IRIS_26732_HIGH_ZOOM_FAIL_CLOSED_NATIVE_FALLBACK','NATIVE_SABRE_VGN_NO_DETAIL']:
    assert t in rv,t
# No backups or repository writes may appear in the guarded build script.
assert 'backup-' not in s.lower() and 'git branch backup' not in s.lower()
assert not re.search(r'\bgit\s+(commit|push)\b',s)
for t in ['compare_app "$AFTER" "$AFTER2"','compare_app "$AFTER" "$LIVE_CANON"',
          'expected one Gradle APK','one intended root APK','post-build candidate/protected/native/vendor/DNG invariance']:
    assert t in s,t
# Scope/package mechanics advance only counts/names, never weakening exact allowlist behavior.
assert 'payload count' in s and 'changed count' in s and 'fail additions' in s
assert "! git diff --name-only \"$RUNTIME_AUTHORITY_COMMIT\"..HEAD|grep -Eq '^app/'" in s
print('PASS 26732 infrastructure: exact successful 26731 nine-role implementation hash-pinned; compiler/build/workflow ordering unchanged; 26729 R1/R2 + 26731 runtime-anchor failures permanently preflighted; MECHANICS DELTA ZERO; no backup/commit/push')
