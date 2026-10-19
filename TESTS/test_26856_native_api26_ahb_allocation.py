#!/usr/bin/env python3
"""Permanent actual 39328271520 Actions NDK API-26 regression.
Real NDK build is still mandatory and NOT replaced by this structural test.
"""
from pathlib import Path
import re
root = Path(__file__).resolve().parent.parent
native = root / 'handoff_payload_26856/app/src/main/cpp/iris26856/amaze'
src = (native/'src/AmazeGlVulkanJni.cpp').read_text()
cmake = (root/'handoff_payload_26856/app/src/main/cpp/CMakeLists.txt').read_text()
# Fail on API29 calls when :app builds native code for API26; do not silently raise app minSDK.
assert 'AHardwareBuffer_isSupported(' not in re.sub(r'//[^\n]*','',src), '39328271520 API29 native call returned'
assert 'AHardwareBuffer_getId(' not in src
assert 'AHardwareBuffer_lockAndGetInfo(' not in src
assert src.count('if (android_get_device_api_level() < 29)') == 1, 'established API29 feature gate changed'
assert src.count('AHardwareBuffer_allocate(&desc, &owned.buffer)') == 1, 'single API26 allocation changed'
assert src.index('ScopedAHB owned;') < src.index('AHardwareBuffer_allocate(&desc, &owned.buffer)')
assert 'if (AHardwareBuffer_allocate(&desc, &owned.buffer) != 0 || !owned.buffer)' in src
assert 'AHARDWAREBUFFER_FORMAT_R16G16B16A16_FLOAT' in src
assert 'AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE' in src
assert 'AHARDWAREBUFFER_USAGE_GPU_COLOR_OUTPUT' in src
assert 'AHARDWAREBUFFER_USAGE_GPU_DATA_BUFFER' in src
assert 'AHardwareBuffer_release(buffer)' in src
assert 'target_link_libraries(iris26856amaze PRIVATE iris26856-rawr-amaze android EGL GLESv3 vulkan log)' in cmake
for p in (native/'src').glob('*.cpp'):
 t = re.sub(r'//[^\n]*','',p.read_text())
 for forbidden in ('AHardwareBuffer_isSupported(', 'AHardwareBuffer_lockAndGetInfo(', 'AHardwareBuffer_getId('):
  assert forbidden not in t,(p.name,forbidden)
print('PASS 26856 Android NDK API26 AHB allocator/native safety regression: exact failure 39328271520 blocked')
print('Real Android NDK compiler: NOT RUN')
