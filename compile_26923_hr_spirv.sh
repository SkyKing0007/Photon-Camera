#!/usr/bin/env bash
# Real pinned Vulkan 1.1 compiler/optimizer/validator gate for the new 26923
# B Super Res ON-only Wronski finalize shader. No alternate native compiler.
set -euo pipefail
cd "$(dirname "$0")"
python3 -S build_26923_incremental.py regress
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED: missing pinned glslang 16.5.0'; exit 4; }
"$COMPILER" --version > photon_26923_outputs/26923_HR_GLSLANG_VERSION.txt
# Prevent accidentally using a different unpinned compiler, including the
# historically incorrect 26904 V1 SPIR-V optimizer/compiler handoff.
grep -F '16.5.0' photon_26923_outputs/26923_HR_GLSLANG_VERSION.txt >/dev/null
command -v spirv-opt >/dev/null || { echo 'BLOCKED: spirv-opt unavailable'; exit 4; }
command -v spirv-val >/dev/null || { echo 'BLOCKED: spirv-val unavailable'; exit 4; }
python3 -S - <<'END_26923_STATIC_SHADER_CONTRACT'
from pathlib import Path
s=Path('app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp').read_text()
assert s.startswith('#version 450')
assert s.count('IRIS_26923_B_SR_ON_NINE_BOUNDED_HR_UPDATES')==1
assert s.count('for (int t = 0; t < 3; ++t)')==1
assert s.count('for (int step = 0; step < 3; ++step)')==1
assert 'imageLoad(sumI,z)' in s and 'imageLoad(weightI,z)' in s
assert 'const ivec2 extent = imageSize' not in s
assert 'const float baselineY = dot(' not in s
c=Path('app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake').read_text()
assert c.count('Iris26923WronskiFinalize.comp')==1
assert '"${IRIS26887_VENDOR_SHADOW}/multiframe/merge_wronski/shaders/a11_finalize.comp" COPYONLY' in c
print('PASS 26923 CMake build shadow overlays only B Wronski native finalize, vendor source unchanged')
END_26923_STATIC_SHADER_CONTRACT
OUT="$PWD/photon_26923_outputs"
DIR="$TOOLS/26923_hr_shaders"
mkdir -p "$DIR"
SRC=app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp
"$COMPILER" -V --target-env vulkan1.1 -S comp -o "$DIR/a11_finalize_26923.spv" "$SRC"
spirv-val --target-env vulkan1.1 "$DIR/a11_finalize_26923.spv"
spirv-opt --target-env=vulkan1.1 -O "$DIR/a11_finalize_26923.spv" -o "$DIR/a11_finalize_26923.opt.spv"
spirv-val --target-env vulkan1.1 "$DIR/a11_finalize_26923.opt.spv"
{
  echo 'PASS real pinned glslang 16.5.0 Vulkan 1.1 Wronski 26923 finalize GLSL/SPIR-V compile, optimization and dual validation'
  cat "$OUT/26923_HR_GLSLANG_VERSION.txt"
  sha256sum "$SRC" "$DIR/a11_finalize_26923.spv" "$DIR/a11_finalize_26923.opt.spv"
  spirv-val --version
  spirv-opt --version
} > "$OUT/26923_WRONSKI_HR_SPIRV_REAL_COMPILER.txt"
