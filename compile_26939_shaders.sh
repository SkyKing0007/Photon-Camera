#!/usr/bin/env bash
# Same pinned real 26938 glslang 16.5 / SPIR-V optimizer/validator, on CURRENT 26939 expanded GLSL.
# 26938 V1 failed GLSL compilation due to max(a,b,c); retain fixed-arity regression.
# Never bypass or replace real compiler with local regex/mock tests.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26939_shader_contract.py --live --extract
python3 -S test_26939_highlight_math.py --live
OUT="$PWD/photon_26939_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26939_current_real_gles"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED missing successful pinned glslang 16.5.0' >&2; exit 4; }
"$COMPILER" --version > "$OUT/26939_GLSLANG_VERSION.txt"
grep -F 16.5.0 "$OUT/26939_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null;command -v spirv-opt >/dev/null
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26939 pinned real shader compiler FAILED $rc" >&3;tail -n 120 "$OUT/26939_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
 echo 'BEGIN actual 26939 inline ESSL 300 310 pinned glslang 16.5.0 five current shaders; SPIR-V optimizer and validator remain mandatory'
 cat "$OUT/26939_GLSLANG_VERSION.txt"
 for kind in raw_lens_median lkr_smooth_white motion_render motion_gainmap b_native_final; do
   if [ "$kind" != b_native_final ]; then
     s="$OUT/26939_${kind}_es300.frag"
     sha256sum "$s";"$COMPILER" -S frag "$s"
   fi
   s="$OUT/26939_${kind}_es310.frag"
   sha256sum "$s"
   "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${kind}.spv" "$s"
   spirv-val --target-env opengl4.5 "$DIR/${kind}.spv"
   spirv-opt --target-env=opengl4.5 -O "$DIR/${kind}.spv" -o "$DIR/${kind}.opt.spv"
   spirv-val --target-env opengl4.5 "$DIR/${kind}.opt.spv"
   sha256sum "$DIR/${kind}.spv" "$DIR/${kind}.opt.spv"
 done
 spirv-opt --version; spirv-val --version
 echo 'PASS actual 26939 inline ESSL 300 310 pinned glslang 16.5.0 five current shaders; SPIR-V optimized and validated'
} > "$OUT/26939_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR;exec 3>&-
