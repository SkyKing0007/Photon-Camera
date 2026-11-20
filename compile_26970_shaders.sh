#!/usr/bin/env bash
# 26970 current compiled shader proof: exact successful 26968 toolchain, mandatory GLSL/SPIR-V tool gates.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26970_source.py --live
python3 -S test_26970_ae.py --live
python3 -S test_26970_noise.py --live
# Run required V2 native/GLSL ownership and reserved-name checks before querying optional local compiler tools.
python3 -S test_26970_glsl_preflight.py --live
OUT="$PWD/photon_26970_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26970_real_current_source_shader_compile"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit 2>/dev/null || true)"
[ -x "$COMPILER" ] || { echo '26970 BLOCKED: real pinned glslang 16.5.0 missing' >&2; exit 4; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null || { echo '26970 BLOCKED: SPIR-V validator missing'; exit 4; }
command -v spirv-opt >/dev/null || { echo '26970 BLOCKED: SPIR-V optimizer missing'; exit 4; }
python3 -S - <<'PYSHADER'
from pathlib import Path
import textwrap,re
O=Path('photon_26970_outputs')
for name in ('render','gainmap'):
 s=(Path('app/src/main/assets/shaders/motionv2')/(name+'.glsl')).read_text()
 if '#version' in s or s.count('void main()')!=1 or s.count('uniform int iris26954BOffNight26940Sdr;')!=1:
  raise SystemExit('26970 BLOCKED malformed current '+name)
 for version in ('300','310'):(O/f'26970_{name}_es{version}.frag').write_text('#version '+version+' es\n#line 1\n'+s)
s=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt').read_text()
if s.count('"""#version 300 es')!=1 or s.count('""".trimIndent()')!=1:raise SystemExit('26970 BLOCKED LKR median shader missing')
med=textwrap.dedent('#version 300 es'+s.split('"""#version 300 es',1)[1].split('""".trimIndent()',1)[0])
if med.count('void main()')!=1:raise SystemExit('26970 BLOCKED LKR median entry missing')
for version in ('300','310'):(O/f'26970_lkr_median_es{version}.frag').write_text(med.replace('#version 300 es','#version '+version+' es',1))
for path in ['Iris26887BOffHdrqMerge.comp','Iris26887BOffHdrqDeconvolute.comp','Iris26970BOffGrainEven.comp']:
 s=(Path('app/src/main/cpp/iris26864/bridge')/path).read_text()
 assert s.startswith('#version 450'),path
 code=re.sub(r'/\*.*?\*/|//[^\n]*',' ',s,flags=re.S)
 bad=re.search(r'\b(?:float|int|uint|vec[234]|mat[234]|bool|const)\s+(?:coherent|flat|in|out|varying|attribute|uniform|buffer|precision|shared|layout|sample|switch|class|atomic_uint)\s*[=;,\[]',code)
 if bad:raise SystemExit('26970 BLOCKED reserved GLSL identifier '+path+' '+bad.group())
 if code.count('void main()')!=1:raise SystemExit('26970 BLOCKED GLSL main '+path)
 if re.search(r'\b(?:isfinite)\s*\(',code):raise SystemExit('26970 BLOCKED unsupported GLSL intrinsic '+path)
PYSHADER
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26970 actual real shader compile FAILED $rc" >&3;tail -n 180 "$OUT/26970_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
 "$COMPILER" --version
 spirv-val --version;spirv-opt --version
 for shader in render gainmap lkr_median; do
  if [ "$shader" = lkr_median ]; then sha256sum app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt
  else sha256sum "app/src/main/assets/shaders/motionv2/${shader}.glsl"; fi
  "$COMPILER" -S frag "$OUT/26970_${shader}_es300.frag"
  "$COMPILER" -S frag "$OUT/26970_${shader}_es310.frag"
  "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${shader}.spv" "$OUT/26970_${shader}_es310.frag"
  spirv-val --target-env opengl4.5 "$DIR/${shader}.spv"
  spirv-opt --target-env=opengl4.5 -O "$DIR/${shader}.spv" -o "$DIR/${shader}.opt.spv"
  spirv-val --target-env opengl4.5 "$DIR/${shader}.opt.spv"
  sha256sum "$DIR/${shader}.spv" "$DIR/${shader}.opt.spv"
 done
 src='app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag';sha256sum "$src"
 "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/b_fused_final_p3_gain.spv" "$src"
 spirv-val --target-env opengl4.5 "$DIR/b_fused_final_p3_gain.spv"
 spirv-opt --target-env=opengl4.5 -O "$DIR/b_fused_final_p3_gain.spv" -o "$DIR/b_fused_final_p3_gain.opt.spv"
 spirv-val --target-env opengl4.5 "$DIR/b_fused_final_p3_gain.opt.spv"
 for name in Iris26887BOffHdrqMerge.comp Iris26887BOffHdrqDeconvolute.comp Iris26970BOffGrainEven.comp Iris26887BOffHdrqMismatchNorm.comp Iris26943BOffHdrqBorder.comp; do
  src="app/src/main/cpp/iris26864/bridge/$name"
  sha256sum "$src"
  "$COMPILER" -V --target-env vulkan1.1 -S comp -o "$DIR/${name}.spv" "$src"
  spirv-val --target-env vulkan1.1 "$DIR/${name}.spv"
  spirv-opt --target-env=vulkan1.1 -O "$DIR/${name}.spv" -o "$DIR/${name}.opt.spv"
  spirv-val --target-env vulkan1.1 "$DIR/${name}.opt.spv"
  sha256sum "$DIR/${name}.spv" "$DIR/${name}.opt.spv"
 done
 sha256sum app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
 echo 'PASS actual 26970 current ESSL300/310 + Vulkan 1.1, SPIR-V opt/val'
} > "$OUT/26970_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR;exec 3>&-
