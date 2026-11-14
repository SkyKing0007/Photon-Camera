#!/usr/bin/env bash
# Mandatory REAL original pinned 26930 GLSL16.5 + ESSL300, ESSL310 OpenGL SPIR-V
# optimizer/validator for ALL THREE newly ACTIVE LKR->Iris GL shader contracts.
# No mock compiler, no generated source substitutes, no mutation of Kotlin input.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26931_shader_contract.py --live
OUT="$PWD/photon_26931_outputs"; TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26931_lkr_real_gles"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED missing original pinned glslang 16.5.0'; exit 4; }
"$COMPILER" --version > "$OUT/26931_LKR_GLSLANG_VERSION.txt"
grep -F 16.5.0 "$OUT/26931_LKR_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null;command -v spirv-opt >/dev/null
python3 -S test_26931_shader_contract.py --extract
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26931 real LKR GL shader failure $rc" >&3;tail -n 90 "$OUT/26931_LKR_GLES_SPIRV_REAL_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
 echo 'PASS real pinned glslang 16.5.0; all LKR active GLES source ESSL300 + 310 with SPIR-V validation/optimization (OpenGL4.5)'
 cat "$OUT/26931_LKR_GLSLANG_VERSION.txt"
 for label in lkr_temporary_wb lkr_physical_lsc lkr_2x_guide; do
  SRC="$OUT/26931_${label}_es300.frag"
  SRC310="$OUT/26931_${label}_es310.frag"
  sha256sum "$SRC" "$SRC310"
  "$COMPILER" -S frag "$SRC"
  "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${label}.spv" "$SRC310"
  spirv-val --target-env opengl4.5 "$DIR/${label}.spv"
  spirv-opt --target-env=opengl4.5 -O "$DIR/${label}.spv" -o "$DIR/${label}.opt.spv"
  spirv-val --target-env opengl4.5 "$DIR/${label}.opt.spv"
  sha256sum "$DIR/${label}.spv" "$DIR/${label}.opt.spv"
 done
 spirv-opt --version; spirv-val --version
} > "$OUT/26931_LKR_GLES_SPIRV_REAL_COMPILER.txt" 2>&1
trap - ERR;exec 3>&-
