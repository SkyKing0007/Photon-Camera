#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3:raise SystemExit('usage: validate_26703.py BASE26702 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root):return {str(p.relative_to(root)):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(root,rel):return (root/rel).read_text()
def method(text,sig):
 i=text.index(sig);brace=text.index('{',i);d=0
 for j in range(brace,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[i:j+1]
 raise AssertionError(sig)
B=files(b);C=files(c);assert len(B)==len(C)==1823,(len(B),len(C))
changed={k for k in set(B)|set(C) if B.get(k)!=C.get(k)}
expected={
 'app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt',
 'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt',
 'app/version.properties',
}
assert changed==expected,changed
# Version/build only.
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726703' in v and 'VERSION_BUILD=26703' in v
bv=txt(b,'app/version.properties');assert v==bv.replace('VERSION_NAME=0.9726702','VERSION_NAME=0.9726703').replace('VERSION_BUILD=26702','VERSION_BUILD=26703')
# Full-frame saved-still factory must be the only FrameGeometrySnapshot change.
rel='app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt';bg=txt(b,rel);cg=txt(c,rel)
factory='''        /* IRIS_26703_SPEKTRA_FULL_FRAME_STILL_GEOMETRY\n         * Saved still geometry is sensor-active-array owned. It must never inherit the\n         * viewfinder/UI viewport aspect, because CameraActivity can remain portrait-locked\n         * while the physical capture transform is landscape. */\n        fun createFullFrameStill(\n            sensor: SensorMetadata,\n            output: RawOutput,\n            transform: CaptureTransform,\n        ): FrameGeometrySnapshot {\n            val pixelArray = requireNotNull(sensor.pixelArray(output.maximumResolutionMode)) {\n                "Sensor pixel array is unavailable"\n            }\n            val activeArray = requireNotNull(sensor.activeArray(output.maximumResolutionMode)) {\n                "Sensor active array is unavailable"\n            }\n            validateActiveArray(activeArray, pixelArray)\n            val mappedActive = mapActiveArray(activeArray, pixelArray, output.size)\n            val normalizedActive = mappedActive.normalized(output.size)\n            val rawOutputSize = Size2d(mappedActive.width, mappedActive.height)\n            val orientedOutput = transform.outputSize(rawOutputSize)\n            return FrameGeometrySnapshot(\n                sourceSize = output.size,\n                activeArray = normalizedActive,\n                sourceCrop = normalizedActive,\n                cropPixels = mappedActive,\n                transform = transform,\n                targetViewport = orientedOutput,\n                outputSize = orientedOutput,\n            )\n        }\n\n'''
assert cg.count(factory)==1
assert cg.replace(factory,'')==bg
fm=method(cg,'        fun createFullFrameStill(')
assert 'centerCrop(' not in fm and 'targetViewport:' not in fm and 'processingLimit' not in fm
for token in ['val mappedActive = mapActiveArray(activeArray, pixelArray, output.size)','sourceCrop = normalizedActive','cropPixels = mappedActive','val orientedOutput = transform.outputSize(rawOutputSize)','targetViewport = orientedOutput','outputSize = orientedOutput']:
 assert token in fm,token
# Existing viewport-driven create path and mapping helpers are byte-identical.
for sig in ['        fun create(','        private fun validateActiveArray(','        private fun mapActiveArray(','        private fun centerCrop(','        private fun fitWithin(']:assert method(bg,sig)==method(cg,sig),sig
# Active capture owner changes only its still-geometry construction; preview path remains byte-identical.
rel='app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt';br=txt(b,rel);cr=txt(c,rel)
bcap=method(br,'    fun captureStill(): Boolean = synchronized(lock) {');ccap=method(cr,'    fun captureStill(): Boolean = synchronized(lock) {')
assert br.replace(bcap,'<CAPTURE_STILL>')==cr.replace(ccap,'<CAPTURE_STILL>')
old='''            val geometry = FrameGeometrySnapshot.create(\n                owner.camera.sensorMetadata,\n                captureOutput,\n                transform,\n                requireNotNull(viewportSize) { "Viewfinder dimensions are unavailable" },\n            )\n'''
new='''            val geometry = FrameGeometrySnapshot.createFullFrameStill(\n                owner.camera.sensorMetadata,\n                captureOutput,\n                transform,\n            )\n            Log.i(\n                TAG,\n                "IRIS_26703_SPEKTRA_FULL_FRAME_STILL_GEOMETRY " +\n                    "raw=${captureOutput.size.width}x${captureOutput.size.height} " +\n                    "activeCrop=${geometry.cropPixels.width}x${geometry.cropPixels.height}" +\n                    "@${geometry.cropPixels.left},${geometry.cropPixels.top} " +\n                    "physicalRotation=${transform.orientationDegrees} " +\n                    "output=${geometry.outputSize.width}x${geometry.outputSize.height} " +\n                    "viewportIgnoredForStill=true",\n            )\n'''
assert bcap.count(old)==1 and ccap.count(new)==1
assert ccap.replace(new,old)==bcap
for token in ['PhotonCamera.getGravity().getCameraRotation(sensorOrientation)','owner.camera.facing == LensFacing.FRONT','IRIS_26702_SPEKTRA_ACTIVE_CAPTURE_ORIENTATION']:
 assert token in ccap,token
assert 'displayRotationDegrees()' not in ccap and 'viewportSize' not in ccap
assert 'FrameGeometrySnapshot.createFullFrameStill(' in ccap
assert cr.count('FrameGeometrySnapshot.createFullFrameStill(')==1
assert cr.count('FrameGeometrySnapshot.create(')==1
# Preview must still be display/viewport owned exactly as 26702.
assert 'CaptureGeometry.transform(\n                    owner.camera.sensorMetadata.orientationDegrees,\n                    displayRotationDegrees(),' in cr
assert 'requireNotNull(viewportSize) { "Viewfinder dimensions are unavailable" },\n                owner.plan.processingSize,' in cr
# Exact regression math for the observed 4:3 full-active source contract.
def out(w,h,rot):return (h,w) if rot in (90,270) else (w,h)
assert out(4096,3072,0)==(4096,3072)
assert out(4096,3072,180)==(4096,3072)
assert out(4096,3072,90)==(3072,4096)
assert out(4096,3072,270)==(3072,4096)
# No viewfinder aspect participates in the saved-still factory/capture call.
for viewport in [(1440,1920),(1920,1440),(1000,1000),(1080,2400)]:
 assert out(4096,3072,0)==(4096,3072),viewport
print('PASS validate 26703: exact 3-file scope; Spektra still uses full mapped active array independent of portrait-locked viewport; 26702 physical orientation and preview geometry preserved')
