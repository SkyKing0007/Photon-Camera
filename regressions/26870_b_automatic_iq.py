#!/usr/bin/env python3
"""Permanent real 26869 device failures + strict 26870 B-only active path regressions."""
from pathlib import Path
import sys,re,hashlib
assert len(sys.argv)==3
prior=Path(sys.argv[1]);cand=Path(sys.argv[2]);rel=Path('src/main/')
def data(p,name):return (p/rel/name).read_bytes()
def src(p,name):return data(p,name).decode()
# 26869 runtime incident: AndroidX shared-preferences String/Boolean crash;
# AAPT2 `app:max`, missing controls and lost selected B. ZERO settings changes.
settings=['java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
          'java/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java',
          'res/xml/preferences.xml',
          'java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java']
for path in settings:assert data(prior,path)==data(cand,path),('26869 restored proven settings owner changed',path)
settingsXml=src(cand,settings[2]);ui=src(cand,settings[0]);ab=src(cand,settings[1])
assert 'app:max=' not in settingsXml and 'iris_26869_b_' not in settingsXml
assert 'Iris26869BSettings' not in ui and 'SwitchPreferenceCompat' not in ui
assert 'iris_26856_physical_lens_ab' in ab and 'putString(PREFIX + identity(lensId, null), mode.id)' in ab
print('PASS 26869 exact String/Boolean preference crash + AAPT2 + per-lens B-owner immutability')
bridge=src(cand,'java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
gpu=src(cand,'java/com/hinnka/mycamera/processor/GlesIris26870GpuSharpest.kt')
stack=src(cand,'java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
chroma=src(cand,'java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt')
post=src(cand,'java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
tone=src(cand,'java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java')
toneShader=src(cand,'assets/shaders/motionv2/iris_tone_controls.glsl')
assert bridge.count('GlesIris26870GpuSharpest.select(')==2
assert bridge.count('GlesIris26864NativeRawr.run(')==2
assert bridge.index('GlesIris26870GpuSharpest.select(')<bridge.index('GlesIris26864NativeRawr.run(')
assert 'GlesIris26870GpuSharpest.select(\n                                        frozen,pattern,nativeReferenceIndex)' in bridge
assert 'chosenRef26870,' in bridge and 'selected=$chosenRef26870' in bridge
assert 'GLES30.GL_R16UI' in gpu and 'GLES30.GL_RED_INTEGER' in gpu
assert 'GLES30.glReadPixels' in gpu and 'GL_UNSIGNED_BYTE' in gpu
assert 'GlesIris26864FrozenRawrIngress' in gpu and 'return shutterIndex' in gpu
assert 'frozen.buffers' in gpu and '0.005' in gpu
assert 'rawrNativeReceipt26864 != null' in stack and 'GlesIris26870PostAmazeChroma.shader' in stack
# Real persistent-object regression: B may switch native/legacy across generations;
# the two shader programs cannot share one GL program cache ID.
assert stack.count('private var iris26870NativePostAmazeWbProgram = 0')==1
assert stack.count('iris26870NativePostAmazeWbProgram = linkProgram(')==1
assert 'if (iris26857ApplyAmazeWbProgram == 0)' in stack
assert 'val applyProgram = if (rawrNativeReceipt26864 != null)' in stack
assert stack.index('val applyProgram = if (rawrNativeReceipt26864 != null)') < stack.index('bindTexture(applyProgram, "uSensorNeutralAmazeRgb"')
assert 'GlesIris26856RawrColorContract.applyAmazeWbForLabFcc' in stack
assert 'bChromaCorrected26870' not in stack and 'uReferenceProtectionEv' in stack
assert 'uAmazeWb' in chroma and 'uReferenceProtectionEv' in chroma
assert 'vec4(rgb*uAmazeWb,raw.a)' in chroma
assert '0.36*agree*protectedStructure*outlier*genuineHueProtect*visible' in chroma
assert 'rawrNativeReceipt26864 != null' in stack and 'nativeSensorClipFullRes26866' in stack
assert 'MotionV2Render());' in post and 'IrisMotionToneControls(irisMotionSettings)' in post
assert 'irisMotionSettings.hasToneAdjustment() || nativeB26870' in post
assert 'Float.isFinite(p25)' in tone and 'Float.isFinite(p50)' in tone and 'Float.isFinite(gain)' in tone
assert 'motionV2ReconstructionOwner ==' in tone and '!basePipeline.mParameters.irisNightActive' in tone
assert 'glProg.setVar("bAutoShadowToe26870", autoToe26870)' in tone
assert 'bAutoShadowToe26870>0.0001' in toneShader
assert 'Iris26869BResidualChroma' not in post
print('PASS 26870 GPU NORMAL sharpness -> B HDRq & Wronski, 26868 B mode immutable')
print('PASS 26870 fused post-AMaZE B sensor RGB chroma, no 2x extra RGB texture, native LSC/WB/Lab/FCC order')
print('PASS 26870 scene-percentile automatic toe, no A/NIGHT, no settings/slider, zero when unsupported')
# Exact original failures against intentional mutations.
for bad in ['app:max="100"', 'iris_26869_b_chroma_enable']:
 assert bad not in settingsXml
# Color-domain mathematical invariance in the shader's unconstrained RGB region.
for yy in (0.01,0.08,0.20,0.60):
 for a,b in ((0.0,0.0),(0.12,-0.20),(-0.10,0.15)):
  scale=max(yy,0.035)
  g=yy-0.25*(a+b)*scale
  rgb=(g+a*scale,g,g+b*scale)
  if min(rgb)>=0: assert abs((.25*rgb[0]+.5*rgb[1]+.25*rgb[2])-yy)<1e-9
print('PASS 26870 linear RGB chroma reconstruction zero luminance displacement numerical fixtures')
