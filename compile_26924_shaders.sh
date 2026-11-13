#!/usr/bin/env bash
# Exact successful 26923 V4 glslang16.5 ESSL/GLSL/SPIRV gates plus changed
# current 26924 clip-aware shaders. Missing tools MUST fail, not mock PASS.
set -euo pipefail
cd "$(dirname "$0")"
python3 -S build_26924_incremental.py regress
python3 -S - <<'PY'
from pathlib import Path
orig=Path('compile_26906_tone_glsl.sh').read_text()
old="assert 'float iris26906BVisualTone(float y)' in s and '0.330*toeGate' in s\nassert s.count('float iris26906BVisualTone(float y)')==1\n"
new=("if sys.argv[2]=='b_final_50mp':\n"
     "    assert 'IRIS_26922_B_SR_ON_TONE_RESTORE' in s\n"
     "    assert 'iris26906BVisualTone(' not in s\n"
     "    assert 'IRIS_26922_B_SRON_MATCHED_HDR_SDR_QUOTIENT' in s\n"
     "else:\n"
     "    assert 'float iris26906BVisualTone(float y)' in s and '0.330*toeGate' in s\n"
     "    assert s.count('float iris26906BVisualTone(float y)')==1\n")
assert orig.count(old)==1,'successful old ESSL preflight drift'
for cmd in ('"$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag','spirv-val --target-env opengl4.5','spirv-opt --target-env=opengl4.5 -O','spirv-opt --version',"'motionv2/render.glsl:render' 'motionv2/gainmap.glsl:gainmap' 'iris26876/b_fused_final_p3_gain.frag:b_final_50mp'"):
 assert cmd in orig, '26906 real compiler procedure changed '+cmd
transformed=orig.replace(old,new,1)
assert transformed.replace(new,old,1)==orig
Path('.photon_26924_tone_compile_full.sh').write_text(transformed)
print('PASS exactly inherited 26906 actual pinned shader compilation; B ON source-era assertion only')
PY
trap 'rm -f .photon_26924_tone_compile_full.sh' EXIT
bash .photon_26924_tone_compile_full.sh
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26924_current_shaders"
OUT="$PWD/photon_26924_outputs"
mkdir -p "$DIR" "$OUT"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED: pinned glslang 16.5.0 missing'; exit 4; }
"$COMPILER" --version > "$OUT/26924_GLSLANG_VERSION.txt"
grep -F 16.5.0 "$OUT/26924_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S - <<'PY'
from pathlib import Path
import textwrap,re
r=Path('app/src/main/java/com/hinnka/mycamera/processor')
out=Path('photon_26924_outputs')
assert out.is_dir()
for filename,parts in [('GlesIris26870PostAmazeChroma.kt',[('val shader','chroma')]),('GlesIris26856RawrFalseColor.kt',[('val medianChroma','fcc_median'),('val reconstructChroma','fcc_reconstruct')])]:
 s=(r/filename).read_text()
 for marker,key in parts:
  m=list(re.finditer(re.escape(marker)+r'\s*=\s*"""',s))
  assert len(m)==1,(filename,marker,'nonunique shader owner')
  body=textwrap.dedent(s[m[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
  assert body.startswith('#version 300 es') and body.count('uniform int uIris26924BOff;')==1
  assert body.count('uniform int uIris26924ClipPresent;')==1 and body.count('uniform sampler2D uIris26924SensorClip;')==1
  if key=='chroma':
   assert body.count('uniform int uIris26922SrOn;')==1
  (out/('26924_current_'+key+'_es300.frag')).write_text(body)
  (out/('26924_current_'+key+'_es310.frag')).write_text(body.replace('#version 300 es','#version 310 es',1))
print('PASS 26924 three EXACT runtime-expanded Kotlin shaders, all new native uniforms and unchanged 26922 ABI')
PY
{
 echo 'PASS real inherited 26906 full ESSL/SPIR-V plus 26924 current post-AMaZE and both FCC stages'
 cat "$OUT/26924_GLSLANG_VERSION.txt"
 for label in chroma fcc_median fcc_reconstruct; do
  "$COMPILER" -S frag "$OUT/26924_current_${label}_es300.frag"
  "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${label}.spv" "$OUT/26924_current_${label}_es310.frag"
  spirv-val --target-env opengl4.5 "$DIR/${label}.spv"
  spirv-opt --target-env=opengl4.5 -O "$DIR/${label}.spv" -o "$DIR/${label}.opt.spv"
  spirv-val --target-env opengl4.5 "$DIR/${label}.opt.spv"
  sha256sum "$OUT/26924_current_${label}_es300.frag" "$DIR/${label}.spv" "$DIR/${label}.opt.spv"
 done
 spirv-opt --version
 spirv-val --version
} > "$OUT/26924_CURRENT_GLSL_SPIRV_REAL_COMPILER.txt"
