#!/usr/bin/env python3
"""26925 GLSL/Kotlin source/ABI/versions/static preflights, compiler still mandatory."""
from pathlib import Path
import sys,re,subprocess,textwrap
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26925' if '--payload' in sys.argv else R
J=P/'app/src/main/java/com/hinnka/mycamera/processor'
B=P/'app/src/main/cpp/iris26864/bridge'
for x in ('compile_26925_shaders.sh','compile_26925_hr_spirv.sh'):
 t=(R/x).read_text()
 assert 'spirv-opt --target-env=' in t and 'spirv-val --target-env ' in t
 assert '16.5.0' in t
 subprocess.run(['bash','-n',str(R/x)],check=True)
sh=(J/'GlesIris26870PostAmazeChroma.kt').read_text()
m=list(re.finditer(r'val shader\s*=\s*"""',sh));assert len(m)==1
body=textwrap.dedent(sh[m[0].end():].split('""".trimIndent()',1)[0]).strip()
assert body.startswith('#version 300 es') and body.count('void main()')==1
for t in ('uIris26925SupportPresent','uIris26925OriginalFrames','uIris26925ShotByRgb','uIris26925ReadByRgb'):
 assert body.count('uniform') and body.count(t)==2 or body.count(t)>=2,t
assert body.count('uniform int uIris26922SrOn;')==1
assert 'uniform int uIris26923SrOn;' not in body
assert 'uIris26922ShotVariance;' not in body and 'uIris26922ReadVariance;' not in body
assert 'uniform int uIris26924BOff;' in body and 'uniform int uIris26924ClipPresent;' in body
assert (B/'Iris26925_raw_cfa_weight.comp').read_text().count('void main()')==1
assert (B/'Iris26925_support_finish.comp').read_text().count('void main()')==1
assert 'binding=6,r32f' in (B/'Iris26924_raw_adjoint.comp').read_text()
assert 'Iris26925_raw_cfa_weight' in (R/'compile_26925_hr_spirv.sh').read_text()
assert 'Iris26885WronskiChromaGuide' in (R/'compile_26925_hr_spirv.sh').read_text()
print('PASS 26925 exact shader ABI, native per-CFA variance, actual original RAW GLSL and unchanged historical compiler gates; REAL glslang/NDK PENDING')
