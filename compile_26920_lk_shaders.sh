#!/usr/bin/env bash
# Additive strict prebuild compile of the ACTUAL Vulkan 26920 active shaders,
# both production and trace variants. Successful 26919 verification gates and actual 26917 runtime preserved.
set -euo pipefail
cd "$(dirname "$0")"
TOOLROOT="$PWD/.photon_26904_incremental_work/real_shader_tools"
COMPILER="$(find "$TOOLROOT/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED: pinned glslang 16.5.0 absent'; exit 3; }
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
OUT="$PWD/photon_26920_outputs/26920_lk_shaders"
mkdir -p "$OUT"
"$COMPILER" --version > "$OUT/glslang-version.txt"
grep -F '16.5.0' "$OUT/glslang-version.txt" >/dev/null || { echo 'BLOCKED: wrong glslang'; exit 4; }
python3 -S test_26920_source.py --live
python3 -S test_26920_vulkan_abi.py --live
{
  for variant in prod trace; do
    for shader in lk_refine robust_photometric; do
      if [ "$shader" = lk_refine ]; then
        SRC="app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/alignment/shaders/lk_refine.comp"
      else
        SRC="app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/robust_photometric.comp"
      fi
      ARG=()
      if [ "$variant" = prod ] && [ "$shader" = robust_photometric ]; then ARG+=('-DRAWR_MIN_GATE=1'); fi
      if [ "$variant" = trace ]; then ARG+=('-DRAWR_PARITY_TRACE=1'); fi
      "$COMPILER" -V --target-env vulkan1.1 -S comp "${ARG[@]}" -o "$OUT/${shader}_${variant}.spv" "$SRC"
      spirv-val --target-env vulkan1.1 "$OUT/${shader}_${variant}.spv"
      spirv-opt --target-env=vulkan1.1 -O "$OUT/${shader}_${variant}.spv" -o "$OUT/${shader}_${variant}.opt.spv"
      spirv-val --target-env vulkan1.1 "$OUT/${shader}_${variant}.opt.spv"
      sha256sum "$SRC" "$OUT/${shader}_${variant}.spv" "$OUT/${shader}_${variant}.opt.spv"
    done
  done
  cat "$OUT/glslang-version.txt"
  spirv-opt --version
  spirv-val --version
} > "$PWD/photon_26920_outputs/26920_LK_GLSL_SPIRV_REAL_COMPILER.txt"
python3 -S test_26920_vulkan_abi.py --live --compiled | tee "$PWD/photon_26920_outputs/26920_VULKAN_DESCRIPTOR_ABI_PROOF.txt"
grep -F 'lk_refine.comp' "$PWD/photon_26920_outputs/26920_LK_GLSL_SPIRV_REAL_COMPILER.txt" >/dev/null
grep -F 'robust_photometric.comp' "$PWD/photon_26920_outputs/26920_LK_GLSL_SPIRV_REAL_COMPILER.txt" >/dev/null
