#!/usr/bin/env bash
# Compile and validate BOTH prod + parity trace B-only RAW-reprojection shaders.
# Actual CMake copies compile again for both Android ABIs with the exact pinned toolchain.
set -euo pipefail
cd "$(dirname "$0")"
python3 -S build_26925_incremental.py regress
python3 -S test_26925_shader_shadow.py --live
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26925_raw_projection"
OUT="$PWD/photon_26925_outputs"
mkdir -p "$DIR" "$OUT"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED pinned glslang 16.5.0 missing'; exit 4; }
"$COMPILER" --version > "$OUT/26925_RAW_PROJECTION_GLSLANG_VERSION.txt"
grep -F '16.5.0' "$OUT/26925_RAW_PROJECTION_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-opt >/dev/null
command -v spirv-val >/dev/null
{
 echo 'PASS real pinned glslang 16.5.0 Vulkan1.1 original RAW projection, exact build-shadow shaders, both prod and trace, SPIR-V validation and optimization'
 cat "$OUT/26925_RAW_PROJECTION_GLSLANG_VERSION.txt"
 for shader in Iris26924_raw_residual Iris26924_raw_adjoint Iris26924_raw_update Iris26924_reference_model Iris26925_raw_cfa_weight Iris26925_support_finish; do
  SRC="app/src/main/cpp/iris26864/bridge/${shader}.comp"
  [ -f "$SRC" ] || { echo 'BLOCKED: source absent' "$SRC"; exit 4; }
  sha256sum "$SRC"
  for variant in prod trace; do
   ARGS=()
   if [ "$variant" = trace ];then ARGS+=('-DRAWR_PARITY_TRACE=1');fi
   "$COMPILER" -V --target-env vulkan1.1 -S comp "${ARGS[@]}" -o "$DIR/${shader}_${variant}.spv" "$SRC"
   spirv-val --target-env vulkan1.1 "$DIR/${shader}_${variant}.spv"
   spirv-opt --target-env=vulkan1.1 -O "$DIR/${shader}_${variant}.spv" -o "$DIR/${shader}_${variant}.opt.spv"
   spirv-val --target-env vulkan1.1 "$DIR/${shader}_${variant}.opt.spv"
   sha256sum "$DIR/${shader}_${variant}.spv" "$DIR/${shader}_${variant}.opt.spv"
  done
 done
 SRC=app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp
 sha256sum "$SRC"
 for variant in prod trace;do
  ARGS=()
  if [ "$variant" = trace ];then ARGS+=('-DRAWR_PARITY_TRACE=1');fi
  "$COMPILER" -V --target-env vulkan1.1 -S comp "${ARGS[@]}" -o "$DIR/Iris26885WronskiChromaGuide_${variant}.spv" "$SRC"
  spirv-val --target-env vulkan1.1 "$DIR/Iris26885WronskiChromaGuide_${variant}.spv"
  spirv-opt --target-env=vulkan1.1 -O "$DIR/Iris26885WronskiChromaGuide_${variant}.spv" -o "$DIR/Iris26885WronskiChromaGuide_${variant}.opt.spv"
  spirv-val --target-env vulkan1.1 "$DIR/Iris26885WronskiChromaGuide_${variant}.opt.spv"
  sha256sum "$DIR/Iris26885WronskiChromaGuide_${variant}.spv" "$DIR/Iris26885WronskiChromaGuide_${variant}.opt.spv"
 done
 spirv-val --version
 spirv-opt --version
} > "$OUT/26925_ORIGINAL_RAW_SPIRV_REAL_COMPILER.txt"
