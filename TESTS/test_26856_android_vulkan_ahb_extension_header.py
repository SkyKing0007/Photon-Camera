#!/usr/bin/env python3
"""Exact NDK compile-regression condition from Actions run 39322097818.
Does NOT substitute for the native compiler or full :app:assembleDebug.
"""
from pathlib import Path
root = Path(__file__).resolve().parent.parent / 'handoff_payload_26856/app/src/main/cpp/iris26856/amaze'
p = (root / 'src/VulkanDeviceOwner.cpp').read_text()
header = '#include <vulkan/vulkan_android.h>'
needle = 'VK_ANDROID_EXTERNAL_MEMORY_ANDROID_HARDWARE_BUFFER_EXTENSION_NAME'
assert p.count(header) == 1
assert p.count(needle) == 1
assert p.index(header) < p.index(needle)
assert 'VK_KHR_EXTERNAL_SEMAPHORE_FD_EXTENSION_NAME' in p
assert 'VK_EXT_QUEUE_FAMILY_FOREIGN_EXTENSION_NAME' in p
assert 'if (!containsExtension(exts, ext)) ok = false;' in p
assert 'd.ppEnabledExtensionNames = required;' in p
assert '#include <vulkan/vulkan_android.h>' in (root/'include/amaze/HardwareBufferImport.hpp').read_text()
print('PASS 26856 native Vulkan AHB extension header and unchanged strict device-extension requirements')
print('Real Android NDK compile: NOT RUN')
