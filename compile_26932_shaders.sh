#!/usr/bin/env bash
# Exact 26932 active shader source, mandatory pinned original 16.5.0 GLSL,
# ESSL300/310, REAL OpenGL SPIR-V optimizer+validator, no mocks/bypass.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26932_shader_contract.py --live
OUT="$PWD/photon_26932_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26932_current_real_gles"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED pinned original glslang16.5 executable missing'; exit 4; }
"$COMPILER" --version > "$OUT/26932_GLSLANG_VERSION.txt"
grep -F 16.5.0 "$OUT/26932_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S test_26932_shader_contract.py --live --extract
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26932 actual GLSL/SPIRV compilation failed $rc" >&3;tail -n 95 "$OUT/26932_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
  echo 'PASS current real shader compile glslang16.5 + ESSL300/310 + glslang -G + spirv-opt + spirv-val source matched'
  cat "$OUT/26932_GLSLANG_VERSION.txt"
  for kind in raw_lens_median lkr_smooth_white motion_render motion_gainmap b_native_final; do
    SRC310="$OUT/26932_${kind}_es310.frag"
    if [ "$kind" != b_native_final ]; then
      SRC300="$OUT/26932_${kind}_es300.frag"
      sha256sum "$SRC300"
      "$COMPILER" -S frag "$SRC300"
    fi
    sha256sum "$SRC310"
    "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${kind}.spv" "$SRC310"
    spirv-val --target-env opengl4.5 "$DIR/${kind}.spv"
    spirv-opt --target-env=opengl4.5 -O "$DIR/${kind}.spv" -o "$DIR/${kind}.opt.spv"
    spirv-val --target-env opengl4.5 "$DIR/${kind}.opt.spv"
    sha256sum "$DIR/${kind}.spv" "$DIR/${kind}.opt.spv"
  done
  spirv-val --version
  spirv-opt --version
} > "$OUT/26932_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR;exec 3>&-
