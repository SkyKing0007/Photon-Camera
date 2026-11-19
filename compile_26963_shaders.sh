#!/usr/bin/env bash
# Preserve successful 26962 pinned glslang 16.5 ESSL300/310, Vulkan SPIR-V val/opt; no skipped stages.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26963_source.py --live
python3 -S test_26963_motion_math.py --live
python3 -S test_26963_shader_abi.py --live
python3 -S test_26963_rawr051_parity.py --live
OUT="$PWD/photon_26963_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26963_real_current_source_shader_compile"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo '26963 BLOCKED actual pinned glslang 16.5 missing' >&2; exit 4; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S - <<'PYSHADER'
from pathlib import Path
import textwrap,re
O=Path('photon_26963_outputs')
for name in ('render','gainmap'):
 s=(Path('app/src/main/assets/shaders/motionv2')/(name+'.glsl')).read_text()
 if '#version' in s or s.count('void main()')!=1 or s.count('uniform int iris26954BOffNight26940Sdr;')!=1:raise SystemExit('malformed current '+name)
 # Complete runtime-expanded reserved identifier scan, not just source-only scan.
 code=re.sub(r'/\*.*?\*/|//[^\n]*',' ',s,flags=re.S)
 if re.search(r'\b(?:float|int|uint|vec[234]|mat[234]|bool|const)\s+(?:coherent|flat|in|out|varying|attribute|uniform|buffer|precision|shared|layout|sample|switch|class|atomic_uint)\s*[=;,\[]',code):raise SystemExit('GLSL reserved identifier in current '+name)
 for version in ('300','310'):
  (O/f'26963_{name}_es{version}.frag').write_text('#version '+version+' es\n#line 1\n'+s)
s=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt').read_text()
if s.count('"""#version 300 es')!=1 or s.count('""".trimIndent()')!=1:raise SystemExit('LKR median fragment missing')
med=textwrap.dedent('#version 300 es'+s.split('"""#version 300 es',1)[1].split('""".trimIndent()',1)[0])
if med.count('void main()')!=1:raise SystemExit('LKR median entry missing')
for version in ('300','310'):(O/f'26963_lkr_median_es{version}.frag').write_text(med.replace('#version 300 es','#version '+version+' es',1))
PYSHADER
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26963 real compiler FAILED $rc" >&3;tail -n 180 "$OUT/26963_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
 "$COMPILER" --version
 for shader in render gainmap lkr_median; do
  if [ "$shader" = lkr_median ]; then
   sha256sum app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt
  else
   sha256sum "app/src/main/assets/shaders/motionv2/${shader}.glsl"
  fi
  "$COMPILER" -S frag "$OUT/26963_${shader}_es300.frag"
  "$COMPILER" -S frag "$OUT/26963_${shader}_es310.frag"
  "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${shader}.spv" "$OUT/26963_${shader}_es310.frag"
  spirv-val --target-env opengl4.5 "$DIR/${shader}.spv"
  spirv-opt --target-env=opengl4.5 -O "$DIR/${shader}.spv" -o "$DIR/${shader}.opt.spv"
  spirv-val --target-env opengl4.5 "$DIR/${shader}.opt.spv"
  sha256sum "$DIR/${shader}.spv" "$DIR/${shader}.opt.spv"
 done
 src='app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag'
 sha256sum "$src"
 "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/b_fused_final_p3_gain.spv" "$src"
 spirv-val --target-env opengl4.5 "$DIR/b_fused_final_p3_gain.spv"
 spirv-opt --target-env=opengl4.5 -O "$DIR/b_fused_final_p3_gain.spv" -o "$DIR/b_fused_final_p3_gain.opt.spv"
 spirv-val --target-env opengl4.5 "$DIR/b_fused_final_p3_gain.opt.spv"
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
 echo 'PASS actual 26963 current ESSL300/310 + Vulkan 1.1, SPIR-V opt/val'
} > "$OUT/26963_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR;exec 3>&-
