#!/usr/bin/env bash
# Exact same pinned real GLSLang/SPIRV-tools compilation from successful 26952 V4.
# First the historical successful-26952 source shaders were ALL compiled in earlier workflow step.
# NOW compile EVERY changed current-26953 SDR and gainmap shader, unchanged LKR, and unchanged
# RAWR Vulkan shaders using their actual compiled-source bytes. No simulated compilation.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26953_source.py --live
python3 -S test_26953_tone_math.py --live
OUT="$PWD/photon_26953_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26953_real_current_source_shader_compile"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo '26953 BLOCKED missing exact 26904 V3 pinned actual GLSLang 16.5' >&2; exit 4; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S - <<'PY'
from pathlib import Path
import textwrap
O=Path('photon_26953_outputs')
for name in ('render','gainmap'):
 path=Path('app/src/main/assets/shaders/motionv2')/(name+'.glsl')
 shader=path.read_text()
 if '#version' in shader or shader.count('void main()')!=1 or shader.count('uniform int iris26953BOffNightSdrEnabled;')!=1:
  raise SystemExit('26953 actual GLSL runtime source malformed: '+name)
 for ver in ('300','310'):
  (O/('26953_'+name+'_es'+ver+'.frag')).write_text('#version '+ver+' es\n#line 1\n'+shader)
source=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt').read_text()
if source.count('"""#version 300 es')!=1 or source.count('""".trimIndent()')!=1:
 raise SystemExit('unchanged original released LKR median shader cannot extract')
median='#version 300 es'+source.split('"""#version 300 es',1)[1].split('""".trimIndent()',1)[0]
median=textwrap.dedent(median)
if median.count('void main()')!=1:raise SystemExit('inherited LKR median source has no real fragment main')
for ver in ('300','310'):(O/('26953_lkr_median_es'+ver+'.frag')).write_text(median.replace('#version 300 es','#version '+ver+' es',1))
PY
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26953 REAL shader compilation FAILED $rc" >&3;tail -n 160 "$OUT/26953_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
 "$COMPILER" --version
 for shader in render gainmap lkr_median; do
  if [ "$shader" != lkr_median ]; then
   sha256sum "app/src/main/assets/shaders/motionv2/${shader}.glsl"
  else
   sha256sum app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt
  fi
  "$COMPILER" -S frag "$OUT/26953_${shader}_es300.frag"
  "$COMPILER" -S frag "$OUT/26953_${shader}_es310.frag"
  "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${shader}.spv" "$OUT/26953_${shader}_es310.frag"
  spirv-val --target-env opengl4.5 "$DIR/${shader}.spv"
  spirv-opt --target-env=opengl4.5 -O "$DIR/${shader}.spv" -o "$DIR/${shader}.opt.spv"
  spirv-val --target-env opengl4.5 "$DIR/${shader}.opt.spv"
  sha256sum "$DIR/${shader}.spv" "$DIR/${shader}.opt.spv"
 done
 # Protected non-SDR fragment: still compile the actual 26952 B SR ON source as an exact regression.
 src='app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag'
 sha256sum "$src"
 "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/b_fused_final_p3_gain.spv" "$src"
 spirv-val --target-env opengl4.5 "$DIR/b_fused_final_p3_gain.spv"
 spirv-opt --target-env=opengl4.5 -O "$DIR/b_fused_final_p3_gain.spv" -o "$DIR/b_fused_final_p3_gain.opt.spv"
 spirv-val --target-env opengl4.5 "$DIR/b_fused_final_p3_gain.opt.spv"
 # Four exact original RAWR HDR+ Higher Quality Vulkan shaders, 26951 strength 11 protected.
 for name in Iris26887BOffHdrqMerge.comp Iris26888BOffHdrqMismatch.comp Iris26887BOffHdrqMismatchNorm.comp Iris26943BOffHdrqBorder.comp; do
  src="app/src/main/cpp/iris26864/bridge/$name"
  sha256sum "$src"
  "$COMPILER" -V --target-env vulkan1.1 -S comp -o "$DIR/${name}.spv" "$src"
  spirv-val --target-env vulkan1.1 "$DIR/${name}.spv"
  spirv-opt --target-env=vulkan1.1 -O "$DIR/${name}.spv" -o "$DIR/${name}.opt.spv"
  spirv-val --target-env vulkan1.1 "$DIR/${name}.opt.spv"
  sha256sum "$DIR/${name}.spv" "$DIR/${name}.opt.spv"
 done
 spirv-opt --version
 spirv-val --version
 echo 'PASS actual 26953 current ESSL300/310 + Vulkan 1.1, SPIR-V opt/val'
} > "$OUT/26953_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR;exec 3>&-
