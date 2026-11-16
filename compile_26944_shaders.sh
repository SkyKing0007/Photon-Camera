#!/usr/bin/env bash
# Mandatory real current 26944 shader compile; inherited 26904-26943 compilers also run.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26944_shader_contract.py --live
OUT="$PWD/photon_26944_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26944_current_real_gpu"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED missing pinned real glslang 16.5' >&2; exit 4; }
"$COMPILER" --version > "$OUT/26944_GLSLANG_VERSION.txt"
grep -F '16.5.0' "$OUT/26944_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null; command -v spirv-opt >/dev/null
python3 -S - <<'PY'
from pathlib import Path
r=Path('app/src/main/assets/shaders/motionv2/render.glsl').read_text()
if '#version' in r or r.count('void main()')!=1:raise SystemExit('wrong current Night/Photo render source')
o=Path('photon_26944_outputs')
(o/'26944_motion_render_es300.frag').write_text('#version 300 es\n#line 1\n'+r)
(o/'26944_motion_render_es310.frag').write_text('#version 310 es\n#line 1\n'+r)
PY
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26944 actual GLSL/SPIR-V compiler failed $rc" >&3;tail -n 100 "$OUT/26944_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
 echo 'BEGIN 26944 pinned glslang 16.5 actual Night matched SDR and private motion Vulkan source'
 cat "$OUT/26944_GLSLANG_VERSION.txt"
 for p in "$OUT/26944_motion_render_es300.frag" "$OUT/26944_motion_render_es310.frag"; do
   sha256sum "$p"
 done
 "$COMPILER" -S frag "$OUT/26944_motion_render_es300.frag"
 "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/26944_motion_render.spv" "$OUT/26944_motion_render_es310.frag"
 spirv-val --target-env opengl4.5 "$DIR/26944_motion_render.spv"
 spirv-opt --target-env=opengl4.5 -O "$DIR/26944_motion_render.spv" -o "$DIR/26944_motion_render.opt.spv"
 spirv-val --target-env opengl4.5 "$DIR/26944_motion_render.opt.spv"
 sha256sum "$DIR/26944_motion_render.spv" "$DIR/26944_motion_render.opt.spv"
 for shader in Iris26888BOffHdrqMismatch Iris26887BOffHdrqMerge; do
   src="app/src/main/cpp/iris26864/bridge/${shader}.comp"
   sha256sum "$src"
   "$COMPILER" -V --target-env vulkan1.1 -S comp -o "$DIR/${shader}.spv" "$src"
   spirv-val --target-env vulkan1.1 "$DIR/${shader}.spv"
   spirv-opt --target-env=vulkan1.1 -O "$DIR/${shader}.spv" -o "$DIR/${shader}.opt.spv"
   spirv-val --target-env vulkan1.1 "$DIR/${shader}.opt.spv"
   sha256sum "$DIR/${shader}.spv" "$DIR/${shader}.opt.spv"
 done
 spirv-opt --version;spirv-val --version
 echo 'PASS 26944 real pinned shader and SPIR-V GLSL300/310 Night, Vulkan 1.1 B HDRq mismatch/merge'
} > "$OUT/26944_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR; exec 3>&-
