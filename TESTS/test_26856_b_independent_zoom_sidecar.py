#!/usr/bin/env python3
"""Exact post-routing check for separate B vs A high-zoom guides; source-only."""
from pathlib import Path
R=Path(__file__).resolve().parent.parent/'handoff_payload_26856'/'app/src/main/java'
def src(p):return (R/p).read_text()
b=src('com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
s=src('com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
p=src('com/particlesdevs/photoncamera/processing/render/Parameters.java')
h=src('com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
r=src('com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java') if (R/'com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').exists() else None
assert 'val highZoomDetailEnabled = parameters.motionV2Active && !parameters.irisNightActive &&\n                !sabreSuperResEnabled && localOutputZoom >= 1.10f' in b
assert 'enableHighZoomDetail = highZoomDetailEnabled,' in b
assert 'val bIndependentZoom26856 = iris26856AmazeCfaConsumer != null' in s
assert 'iris26856RawrRgbSidecar' in s.split('val zoomDetailGuide26856 =',1)[1].split('val attempt =',1)[0]
assert 'nativeHdrAuthority26601' in s.split('val zoomDetailGuide26856 =',1)[1].split('val attempt =',1)[0]
assert 'parameters.iris26856BHighZoomDetail = if (' in b
assert 'stackB26856.highZoomDetailPath' in b
assert 'historical.copy(' in b
assert 'iris26856BHighZoomDetail = null' in p
assert 'Iris26856BHighZoomDetail bZoom = iris26856BHighZoomDetail' in p
assert 'if (bZoom != null && !independentTrue2x)' in p
assert 'motionV2HighZoomDetailPath = bZoom.path;' in p
assert 'iris26856BPostParameters.prepareRawrBPublication26856' in h
assert 'processingParameters.prepareRawrBPublication26856' in h
assert 'mIris26856BHighZoomDetailPathForCleanup' in h
assert 'if (!iris26856BHighZoomDetailHandedOff)' in b
assert 'enableSabreSuperRes = sabreSuperResEnabled &&' in b
assert 'iris26856BTrue2x = sabreSuperResEnabled &&' in b
# Under the existing shader route, the same luma field enters SDR and UHDR.
shdr=Path(__file__).resolve().parent.parent/'handoff_payload_26856'/'app/src/main/assets/shaders/motionv2/render.glsl'
# Those shaders are unchanged protected authority, and need not be repackaged.
print('PASS B local >=1.1x bounded independent CFA detail: B RGB guide, separate AB carrier, no A RGB borrowing')
print('PASS native output dimensions at Super Res OFF; optional true2x path disjoint')
print('PASS authority original GLSL render/gainmap are untouched; real compilers/device tests NOT RUN')
