#!/usr/bin/env bash
# 26935 real pinned ESSL300 / ESSL310 + SPIR-V optimizer/validator on exact current-source FIVE shaders.
# The 26934 visual-white/highlight shaders are SHA protected and unchanged, never replaced or stubbed.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26934_shader_contract.py --live --extract
python3 -S test_26934_highlight_math.py --live
OUT="$PWD/photon_26935_outputs"
SHADERS="$PWD/photon_26934_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26935_current_real_gles"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED missing pinned real glslang 16.5.0' >&2; exit 4; }
"$COMPILER" --version > "$OUT/26935_GLSLANG_VERSION.txt"
grep -F 16.5.0 "$OUT/26935_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26935 real shader compiler FAILED $rc" >&3;tail -n 120 "$OUT/26935_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
 echo 'PASS actual 26935 inline ESSL 300 310 pinned glslang 16.5.0 all five protected-current shaders; real SPIR-V optimized and validated'
 cat "$OUT/26935_GLSLANG_VERSION.txt"
 for kind in raw_lens_median lkr_smooth_white motion_render motion_gainmap b_native_final; do
   if [ "$kind" != b_native_final ]; then
     s="$SHADERS/26934_${kind}_es300.frag"
     sha256sum "$s"
     "$COMPILER" -S frag "$s"
   fi
   s="$SHADERS/26934_${kind}_es310.frag"
   sha256sum "$s"
   "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${kind}.spv" "$s"
   spirv-val --target-env opengl4.5 "$DIR/${kind}.spv"
   spirv-opt --target-env=opengl4.5 -O "$DIR/${kind}.spv" -o "$DIR/${kind}.opt.spv"
   spirv-val --target-env opengl4.5 "$DIR/${kind}.opt.spv"
   sha256sum "$DIR/${kind}.spv" "$DIR/${kind}.opt.spv"
 done
 spirv-opt --version
 spirv-val --version
} > "$OUT/26935_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR;exec 3>&-
