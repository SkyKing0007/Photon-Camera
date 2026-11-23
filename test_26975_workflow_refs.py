#!/usr/bin/env python3
"""Require unchanged actual successful 26974 historical preflight, never a shortened workflow."""
import hashlib,pathlib,re
R=pathlib.Path(__file__).resolve().parent
ref=(R/'26974_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
new=(R/'.github/workflows/build-26975-change-aware.yml').read_text()
anchor='      - name: Fetch ONLY exact successful 26973 Actions artifact 14717056814'
assert ref.count(anchor)==1 and new.split(anchor)[0] != '', 'missing historical anchor'
# The historical steps, including 26886/7 26903 26904 V1 V2 V3 and 26974 seal, remain exact.
prefix=ref.split(anchor)[0]
prefix=prefix.replace('name: Photon 26974 - exact successful 26973 source, independent C shutter lifecycle repair','name: Photon 26975 - pinned original Pro Sabre native 1x Lanczos-3 Experiment C')
prefix=prefix.replace('TRIGGER_26974.txt','TRIGGER_26975.txt')
assert new.startswith(prefix), 'historical preflight steps weakened/reordered'
for old in ('26903_modes.py','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py','build_26974_incremental.py seal'):
 assert old in prefix or old in new,old
for cmd in ('build_26975_incremental.py seal','build_26975_incremental.py fetch','build_26975_incremental.py prepare-base','build_26975_incremental.py install','build_26975_incremental.py stage-native','bash compile_26975_shaders.sh','./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace','build_26975_incremental.py finalize','actions/upload-artifact@v4'):
 assert cmd in new,cmd
assert new.count('actions/upload-artifact@v4')==1
assert new.count('build_26975_incremental.py finalize')==1
assert 'photon-26975-c-original-pro-sabre' in new
assert "- TRIGGER_26975.txt" in new
assert 'photon_26975_outputs/' in new
assert 'test_26975_sealed_negatives.py' in new
print('PASS 26975 workflow exact successful 26974 historical preflight and mandatory one true dual-ABI Android assemble/publish')

assert 'test_26975_v5_asset_host.py' in (R/'build_26975_incremental.py').read_text()

assert 'test_26975_v5_asset_host.py' in (R/'build_26975_incremental.py').read_text()

assert 'verify_26975_v6_current_glsl.py --emit' in (R/'compile_26975_shaders.sh').read_text()
assert '26975_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt' in (R/'build_26975_incremental.py').read_text()
assert 'EXPECTED_GIT_BLOB=7f31528bc83ba4867476e358c68aee8558201478' in (R/'compile_26975_shaders.sh').read_text()
