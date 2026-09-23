#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26690.py BASE CANDIDATE')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); root=Path(__file__).resolve().parent
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}
def manifest(name):
 d={}
 for line in (root/name).read_text().splitlines():
  if line.strip(): h,p=line.split('  ',1); d[p]=h
 return d
b=H(base); c=H(cand); changed=sorted(p for p in set(b)|set(c) if b.get(p)!=c.get(p))
allowed=sorted(x.strip() for x in (root/'R1_26690_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip())
assert len(b)==1819 and len(c)==1820
assert changed==allowed, (len(changed), sorted(set(changed)^set(allowed))[:10])
assert sum(p not in b for p in changed)==1 and sum(p in b and p in c for p in changed)==2 and not any(p not in c for p in changed)
for a,bn in [('R1_26690_PROTECTED_UNCHANGED_BASE.sha256','R1_26690_PROTECTED_UNCHANGED_CANDIDATE.sha256'),('R1_26690_NATIVE_PROTECTED_BASE.sha256','R1_26690_NATIVE_PROTECTED_CANDIDATE.sha256'),('R1_26690_VENDOR_PROTECTED_BASE.sha256','R1_26690_VENDOR_PROTECTED_CANDIDATE.sha256'),('R1_26690_DNG_BASE.sha256','R1_26690_DNG_CANDIDATE.sha256'),('R1_26690_ASSET_SHADER_UNIVERSE_BASE.sha256','R1_26690_ASSET_SHADER_UNIVERSE_CANDIDATE.sha256')]:
 assert (root/a).read_bytes()==(root/bn).read_bytes(), f'invariance manifest mismatch {a}'
# Exact version/build.
v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726690' in v and 'VERSION_BUILD=26690' in v
# Exact successful-26689 native provenance remains byte-identical.
so=cand/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so'
assert so.stat().st_size==18174352
assert hashlib.sha256(so.read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
# Device-crash JNI_OnLoad contract recovered from exact 1.1.2 binary.
raw=so.read_bytes()
assert raw.count(b'com/unspektrawesome/diagnostics/InternalLogRecorder')==1
assert b'recordNative' in raw
assert raw.count(b'(ILjava/lang/String;Ljava/lang/String;)V')==1
log=(cand/'app/src/main/java/com/unspektrawesome/diagnostics/InternalLogRecorder.java').read_text()
assert 'package com.unspektrawesome.diagnostics;' in log
assert log.count('@Keep')>=2
assert re.search(r'public\s+static\s+void\s+recordNative\s*\(\s*int\s+priority\s*,\s*String\s+tag\s*,\s*String\s+message\s*\)', log)
assert 'Log.println(priority' in log
# Startup containment: normal Iris construction/binding must not instantiate the native owner.
mode=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java').read_text()
assert 'IRIS_26690_SPEKTRA_LAZY_NATIVE_OWNER' in mode
ctor=mode[mode.index('public SpektraModeController('):mode.index('public synchronized void bindPreviewSurface')]
bind=mode[mode.index('public synchronized void bindPreviewSurface'):mode.index('private synchronized RawVulkanPreviewController ensureControllerForActivation')]
ensure=mode[mode.index('private synchronized RawVulkanPreviewController ensureControllerForActivation'):mode.index('private void failActivation')]
assert 'new RawVulkanPreviewController' not in ctor
assert 'new RawVulkanPreviewController' not in bind
assert mode.count('new RawVulkanPreviewController')==1
assert ensure.count('new RawVulkanPreviewController')==1
assert 'if (controller != null) previewView.bind(controller, owner);' in bind
assert 'ensureControllerForActivation()' in mode
assert 'catch (RuntimeException | LinkageError error)' in mode
# Existing successful 26689 hosted ownership remains intact.
assert 'SpektraCameraOwner' not in mode and 'SpektraRawCpuOwner' not in mode and 'SpektraRawVulkanOwner' not in mode
ctrl=(cand/'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt').read_text()
vr=(cand/'app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt').read_text()
assert 'private val renderer = VulkanRenderer(context.applicationContext)' in ctrl
assert 'System.loadLibrary("unspektrawesome_vulkan")' in vr
assert '.warmUp(' not in ctrl
print('PASS 26690 semantic/ownership validation: exact 3-path JNI startup containment over successful 26689 R1.2')
