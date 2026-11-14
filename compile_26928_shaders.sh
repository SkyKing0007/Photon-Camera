#!/usr/bin/env bash
# 26928: exact successful 26926 real pinned 26906 compiler and current ESSL GLSL sources.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S build_26928_incremental.py regress
python3 -S test_26928_shader_contract.py --live
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
assert orig.count(old)==1
for token in ('"$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag','spirv-val --target-env opengl4.5','spirv-opt --target-env=opengl4.5 -O','spirv-opt --version',"'motionv2/render.glsl:render' 'motionv2/gainmap.glsl:gainmap' 'iris26876/b_fused_final_p3_gain.frag:b_final_50mp'"):
 assert token in orig,token
patched=orig.replace(old,new,1);assert patched.replace(new,old,1)==orig
Path('.photon_26928_inherited_tone_glsl.sh').write_text(patched)
print('PASS unchanged inherited 26906 pinned ESSL + SPIR-V compiler contract; only historical 26922 tone assertion retained')
PY
trap 'rm -f .photon_26928_inherited_tone_glsl.sh' EXIT
bash .photon_26928_inherited_tone_glsl.sh
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26928_live_gles";OUT="$PWD/photon_26928_outputs"
mkdir -p "$DIR" "$OUT"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED missing pinned glslang16.5'; exit 4; }
"$COMPILER" --version > "$OUT/26928_GLSLANG_VERSION.txt"
grep -F 16.5.0 "$OUT/26928_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null;command -v spirv-opt >/dev/null
python3 -S - <<'PY'
from pathlib import Path
import re,textwrap
root=Path('app/src/main/java/com/hinnka/mycamera/processor');out=Path('photon_26928_outputs')
for file,values in [('GlesIris26870PostAmazeChroma.kt',[('val shader','chroma')]),('GlesIris26856RawrFalseColor.kt',[('val medianChroma','fcc_median'),('val reconstructChroma','fcc_reconstruct')])]:
 s=(root/file).read_text()
 for marker,key in values:
  matches=list(re.finditer(re.escape(marker)+r'\s*=\s*"""',s));assert len(matches)==1,(file,key)
  body=textwrap.dedent(s[matches[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
  assert body.startswith('#version 300 es')
  for v in ('uniform int uIris26924BOff;','uniform int uIris26924ClipPresent;','uniform sampler2D uIris26924SensorClip;'):assert body.count(v)==1,v
  if key=='chroma':assert 'bOffMaterialOutlier' in body and 'uIris26926ShotByRgb' in body and 'if(uIris26924BOff!=0)' in body
  if key=='fcc_median':assert 'chromaticBoundary' in body
  if key=='fcc_reconstruct':assert 'w*=1.0-smoothstep(0.14,0.38,length(c0-c1));' in body
  (out/f'26928_current_{key}_es300.frag').write_text(body)
  (out/f'26928_current_{key}_es310.frag').write_text(body.replace('#version 300 es','#version 310 es',1))
print('PASS three true 26928 runtime-expanded ESSL300 and 310 source bodies')
PY
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26928 real GLSL/SPIRV failure $rc" >&3;tail -n 100 "$OUT/26928_CURRENT_GLSL_SPIRV_REAL_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
 echo 'PASS real pinned glslang 16.5.0, original 26906 GLSL and all 26928 GLES ESSL300/310 shaders with SPIR-V optimizer'
 cat "$OUT/26928_GLSLANG_VERSION.txt"
 for key in chroma fcc_median fcc_reconstruct;do
  "$COMPILER" -S frag "$OUT/26928_current_${key}_es300.frag"
  "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${key}.spv" "$OUT/26928_current_${key}_es310.frag"
  spirv-val --target-env opengl4.5 "$DIR/${key}.spv"
  spirv-opt --target-env=opengl4.5 -O "$DIR/${key}.spv" -o "$DIR/${key}.opt.spv"
  spirv-val --target-env opengl4.5 "$DIR/${key}.opt.spv"
  sha256sum "$OUT/26928_current_${key}_es300.frag" "$DIR/${key}.spv" "$DIR/${key}.opt.spv"
 done
 spirv-opt --version;spirv-val --version
} > "$OUT/26928_CURRENT_GLSL_SPIRV_REAL_COMPILER.txt" 2>&1
trap - ERR;exec 3>&-
