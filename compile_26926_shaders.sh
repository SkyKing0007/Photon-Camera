#!/usr/bin/env bash
# 26926: inherited 26906 full pinned GLES/GLSL/SPIR-V contract plus current
# EXACT three inline Kotlin B-only shaders. No mocked/pass-through compilers.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S build_26926_incremental.py regress
python3 -S test_26926_shader_contract.py --live
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
assert orig.count(old)==1,'26906 original pinned compiler gate drift'
for cmd in ('"$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag','spirv-val --target-env opengl4.5','spirv-opt --target-env=opengl4.5 -O','spirv-opt --version',"'motionv2/render.glsl:render' 'motionv2/gainmap.glsl:gainmap' 'iris26876/b_fused_final_p3_gain.frag:b_final_50mp'"):
 assert cmd in orig,'historical real compiler changed '+cmd
patched=orig.replace(old,new,1)
assert patched.replace(new,old,1)==orig
Path('.photon_26926_inherited_tone_glsl.sh').write_text(patched)
print('PASS inherited exact 26906 pinned real GLSL procedure, only 26922 B ON 50MP no-tone assertion updated')
PY
trap 'rm -f .photon_26926_inherited_tone_glsl.sh' EXIT
bash .photon_26926_inherited_tone_glsl.sh
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26926_live_gles"
OUT="$PWD/photon_26926_outputs"
mkdir -p "$DIR" "$OUT"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED pinned glslang16.5 compiler unavailable'; exit 4; }
"$COMPILER" --version > "$OUT/26926_GLSLANG_VERSION.txt"
grep -F 16.5.0 "$OUT/26926_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S - <<'PY'
from pathlib import Path
import re,textwrap
r=Path('app/src/main/java/com/hinnka/mycamera/processor')
out=Path('photon_26926_outputs')
for fname,defs in [('GlesIris26870PostAmazeChroma.kt',[('val shader','chroma')]),('GlesIris26856RawrFalseColor.kt',[('val medianChroma','fcc_median'),('val reconstructChroma','fcc_reconstruct')])]:
 s=(r/fname).read_text()
 for marker,key in defs:
  m=list(re.finditer(re.escape(marker)+r'\s*=\s*"""',s)); assert len(m)==1,(fname,marker)
  body=textwrap.dedent(s[m[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
  assert body.startswith('#version 300 es')
  assert body.count('uniform int uIris26924BOff;')==1
  assert body.count('uniform int uIris26924ClipPresent;')==1
  assert body.count('uniform sampler2D uIris26924SensorClip;')==1
  if key=='chroma':
   for token in ('uIris26926BurstFrames','uIris26926ShotByRgb','uIris26926ReadByRgb','uIris26926LensShading','uIris26926RawSize','uIris26922SrOn'):
    assert body.count('uniform') and token in body,(key,token)
  (out/('26926_current_'+key+'_es300.frag')).write_text(body)
  (out/('26926_current_'+key+'_es310.frag')).write_text(body.replace('#version 300 es','#version 310 es',1))
print('PASS three exact runtime-expanded GLES 300 shaders, SPIRV GLSL ES310 shadows and original ABI')
PY
# 26925 V1 failed glslang yet hid stdout. Do not hide real failure again.
exec 3>&1
trap 'rc=$?; trap - ERR; echo "26926 BLOCKED real pinned GLSL (exit $rc)" >&3; if [ -f "$OUT/26926_CURRENT_GLSL_SPIRV_REAL_COMPILER.txt" ];then tail -n 160 "$OUT/26926_CURRENT_GLSL_SPIRV_REAL_COMPILER.txt" >&3;fi; exit "$rc"' ERR
{
 echo 'PASS real inherited 26906 full GLSL/SPIR-V plus current 26926 three GLES300/310 shaders'
 cat "$OUT/26926_GLSLANG_VERSION.txt"
 for key in chroma fcc_median fcc_reconstruct;do
  "$COMPILER" -S frag "$OUT/26926_current_${key}_es300.frag"
  "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${key}.spv" "$OUT/26926_current_${key}_es310.frag"
  spirv-val --target-env opengl4.5 "$DIR/${key}.spv"
  spirv-opt --target-env=opengl4.5 -O "$DIR/${key}.spv" -o "$DIR/${key}.opt.spv"
  spirv-val --target-env opengl4.5 "$DIR/${key}.opt.spv"
  sha256sum "$OUT/26926_current_${key}_es300.frag" "$DIR/${key}.spv" "$DIR/${key}.opt.spv"
 done
 spirv-opt --version
 spirv-val --version
} > "$OUT/26926_CURRENT_GLSL_SPIRV_REAL_COMPILER.txt" 2>&1
trap - ERR
exec 3>&-
