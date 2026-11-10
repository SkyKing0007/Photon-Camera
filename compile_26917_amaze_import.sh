#!/usr/bin/env bash
# Real 26917 B-OFF-only AMaZE import shader compile. This is ADDITIVE to every
# inherited successful 26916 GLSL, SPIR-V, CMake and Android build gate.
set -euo pipefail
cd "$(dirname "$0")"
SRC="$PWD/app/src/main/cpp/iris26856/amaze/shaders"
DST="$PWD/app/src/main/assets/iris26856/rawr/amaze/spv/amaze_import.spv"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
OUT="$PWD/photon_26917_outputs"
TARGET="$TOOLS/26917_amaze_import"
mkdir -p "$OUT" "$TARGET"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -n "$COMPILER" ] || { echo '26917 BLOCKED pinned glslang 16.5.0 missing'; exit 4; }
"$COMPILER" --version > "$TARGET/pinned_glslang_version.txt"
grep -F '16.5.0' "$TARGET/pinned_glslang_version.txt" >/dev/null
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
# Verify exact source import and expand with same non-destructive 26904 method;
# source the runtime actually loads, not a similar standalone shader.
python3 -S - <<'PY'
from pathlib import Path
src=Path('app/src/main/cpp/iris26856/amaze/shaders')
body=(src/'amaze_import.comp').read_text()
header=(src/'amaze_tile.glsl').read_text()
assert body.startswith('#version 450\n') and body.count('#include "amaze_tile.glsl"')==1
assert 'iris26917ReflectPhysicalBayer' in body and 'if (tile.reserved > 0.5)' in body
assert 'uint srcOriginX' in header and 'float inputMode, inputWidth, pattern, reserved;' in header
expanded=body.replace('#include "amaze_tile.glsl"', '#line 1 20\n'+header+'\n#line 6 21')
Path('.photon_26904_incremental_work/real_shader_tools/26917_amaze_import/amaze_import_expanded.comp').write_text(expanded)
print('PASS exact runtime AMaZE import source/header expansion')
PY
"$COMPILER" -V --target-env vulkan1.1 -S comp -o "$TARGET/amaze_import.spv" "$TARGET/amaze_import_expanded.comp"
spirv-val --target-env vulkan1.1 "$TARGET/amaze_import.spv"
spirv-opt --target-env=vulkan1.1 -O "$TARGET/amaze_import.spv" -o "$TARGET/amaze_import.opt.spv"
spirv-val --target-env vulkan1.1 "$TARGET/amaze_import.opt.spv"
test "$(od -An -tx1 -N4 "$TARGET/amaze_import.spv" | tr -d ' \n')" = '03022307'
# The existing native C++ loader consumes exactly this unoptimized compiled
# SPV, matching the successful 26904 export SPV packaging contract.
cp "$TARGET/amaze_import.spv" "$DST"
cmp --silent "$TARGET/amaze_import.spv" "$DST"
{
  echo 'REAL PINNED GLSL COMPILE: PASS 26917 B OFF AMaZE import runtime source'
  echo 'REAL Vulkan 1.1 glslang 16.5.0 compile: PASS'
  cat "$TARGET/pinned_glslang_version.txt"
  sha256sum "$TARGET/amaze_import_expanded.comp" "$TARGET/amaze_import.spv" "$DST"
} > "$OUT/26917_AMAZE_IMPORT_SHADER_REAL_COMPILER.txt"
{
  echo 'REAL SPIR-V VALIDATION: PASS vulkan1.1 pre/post optimization'
  echo 'spirv-val --target-env vulkan1.1: PASS on original and optimized shader'
  echo 'spirv-opt --target-env=vulkan1.1 -O: PASS on compiled shader'
  spirv-val --version
  spirv-opt --version
  sha256sum "$TARGET/amaze_import.spv" "$TARGET/amaze_import.opt.spv"
} > "$OUT/26917_AMAZE_IMPORT_SPIRV_VALIDATED.txt"
echo 'PASS 26917 B OFF import full pinned glslang/SPIR-V compile, val, opt, val, source equality'
