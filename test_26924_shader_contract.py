#!/usr/bin/env python3
"""26924 current pre-compiler GLES shader and shader ABI/fail-closed preflights.
This is additional to real pinned ESSL, Vulkan SPIR-V, NDK and APK gates.
"""
from pathlib import Path
import sys,re,subprocess,textwrap
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26924' if '--payload' in sys.argv else R
J=P/'app/src/main/java/com/hinnka/mycamera/processor'
W=(R/'compile_26924_shaders.sh').read_text()
F=(R/'compile_26924_hr_spirv.sh').read_text()
assert W.count('spirv-opt --target-env=opengl4.5 -O')>=1
assert W.count('spirv-val --target-env opengl4.5')>=1
assert 'compile_26906_tone_glsl.sh' in W
assert 'build_26924_incremental.py regress' in W
assert 'Iris26924_raw_residual' in F and 'Iris26924_reference_model' in F and '${shader}.comp' in F
assert 'spirv-val --target-env vulkan1.1' in F and 'spirv-opt --target-env=vulkan1.1 -O' in F
assert 'compile_26923_hr_spirv.sh' not in F
for p in [R/'compile_26924_shaders.sh',R/'compile_26924_hr_spirv.sh']:
 subprocess.run(['bash','-n',str(p)],check=True)
for filename,parts in [('GlesIris26870PostAmazeChroma.kt',('val shader',)),('GlesIris26856RawrFalseColor.kt',('val medianChroma','val reconstructChroma'))]:
 s=(J/filename).read_text()
 for key in parts:
  m=list(re.finditer(re.escape(key)+r'\s*=\s*"""',s))
  if len(m)!=1:raise AssertionError('wrong Kotlin inline shader extraction '+filename+' '+key)
  body=textwrap.dedent(s[m[0].end():].split('""".trimIndent()',1)[0]).strip()
  assert body.startswith('#version 300 es')
  assert 'uniform sampler2D uIris26924SensorClip;' in body
  assert 'uniform int uIris26924ClipPresent;' in body
  assert 'uniform int uIris26924BOff;' in body
  assert body.count('void main()')==1
chroma=(J/'GlesIris26870PostAmazeChroma.kt').read_text()
assert chroma.count('uniform int uIris26922SrOn;')==1,'26923 V3 wrong uniform ABI regression'
assert 'uniform int uIris26923SrOn;' not in chroma
assert 'IRIS_26922_SR_ON_UNCERTAINTY_AWARE_CHROMA' in chroma
final=(P/'app/src/main/cpp/iris26864/bridge/Iris26924WronskiFinalize.comp').read_text()
assert final.startswith('#version 450') and 'IRIS_26923_B_SR_ON_NINE_BOUNDED_HR_UPDATES' not in final
print('PASS 26924 exact extracted GLES shader ABI, 26923 V3 uniform regression, pinned GLSL and Vulkan compiler arguments; shell syntax')
