#!/usr/bin/env bash
# Standalone, pinned real compiler for exactly the 26904 changed runtime shader domains.
# GitHub Actions ubuntu-24.04: requires pinned glslang 16.5.0 and actual spirv-tools.
set -euo pipefail
cd "$(dirname "$0")"
OUT="$PWD/photon_26904_incremental_outputs"
SRC="$PWD/app/src/main"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
mkdir -p "$OUT" "$TOOLS"
ARCHIVE="$TOOLS/glslang-16.5.0-linux-x86_64-release.tar.gz"
URL='https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz'
PIN='b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657'
curl --fail --location --retry 3 --silent --show-error "$URL" -o "$ARCHIVE"
printf '%s  %s\n' "$PIN" "$ARCHIVE" | sha256sum --check --status
mkdir -p "$TOOLS/glslang"
tar -xzf "$ARCHIVE" -C "$TOOLS/glslang"
COMPILER="$(find "$TOOLS/glslang" -type f -name glslang -print -quit)"
if [ -z "$COMPILER" ]; then COMPILER="$(find "$TOOLS/glslang" -name glslangValidator -print -quit)"; fi
[ -n "$COMPILER" ] && chmod +x "$COMPILER"
"$COMPILER" --version | tee "$OUT/26904_GLSLANG_VERSION.txt"
grep -F '16.5.0' "$OUT/26904_GLSLANG_VERSION.txt" >/dev/null
if ! command -v spirv-val >/dev/null || ! command -v spirv-opt >/dev/null; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq spirv-tools
fi
command -v spirv-val >/dev/null && command -v spirv-opt >/dev/null
spirv-val --version > "$OUT/26904_SPIRV_TOOLS_VERSION.txt"
spirv-opt --version >> "$OUT/26904_SPIRV_TOOLS_VERSION.txt"
python3 -S - <<'PY'
from pathlib import Path
src=Path('app/src/main')
expanded=Path('.photon_26904_incremental_work/real_shader_tools')
rot=(src/'assets/shaders/addwatermark_rotate.glsl').read_text()
interp=(src/'assets/shaders/utils/import_interpolation.glsl').read_text()
assert rot.count('#import interpolation')==1
assert rot.count('#define WATERMARK 1')==1
assert '#version' not in rot.splitlines()[0]
# GLProg's shader runtime adds ESSL310 and replaces this one interpolation import.
for flag in ['1','0']:
    body=rot.replace('#define WATERMARK 1','#define WATERMARK '+flag)
    body=body.replace('#import interpolation', '#line 1 10\n'+interp+'\n#line 1 11')
    (expanded/('26904_actual_rotation_wm'+flag+'.frag')).write_text('#version 310 es\n'+body)
# Native shader uses one pre-existing source include. Expand it exactly, leaving
# source #version and descriptor ABI untouched (glslang includes need extension).
native=(src/'cpp/iris26856/amaze/shaders/amaze_export.comp').read_text()
header=(src/'cpp/iris26856/amaze/shaders/amaze_tile.glsl').read_text()
assert native.count('#include "amaze_tile.glsl"')==1
assert native.startswith('#version 450\n')
(expanded/'26904_amaze_export_expanded.comp').write_text(native.replace('#include "amaze_tile.glsl"', '#line 1 20\n'+header+'\n#line 6 21'))
print('PASS runtime source import expansion exact anchors')
PY
{
  for flag in 1 0; do
    SRC_FRAG="$TOOLS/26904_actual_rotation_wm${flag}.frag"
    "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$TOOLS/rotation_wm${flag}.spv" "$SRC_FRAG"
    spirv-val --target-env opengl4.5 "$TOOLS/rotation_wm${flag}.spv"
    spirv-opt --target-env=opengl4.5 -O "$TOOLS/rotation_wm${flag}.spv" -o "$TOOLS/rotation_wm${flag}_opt.spv"
    spirv-val --target-env opengl4.5 "$TOOLS/rotation_wm${flag}_opt.spv"
    echo "PASS real ESSL310 rotation WATERMARK=$flag glslang 16.5.0 SPIR-V validation"
  done
  "$COMPILER" -V --target-env vulkan1.1 -S comp -o "$TOOLS/amaze_export_26904.spv" "$TOOLS/26904_amaze_export_expanded.comp"
  spirv-val --target-env vulkan1.1 "$TOOLS/amaze_export_26904.spv"
  spirv-opt --target-env=vulkan1.1 -O "$TOOLS/amaze_export_26904.spv" -o "$TOOLS/amaze_export_26904_opt.spv"
  spirv-val --target-env vulkan1.1 "$TOOLS/amaze_export_26904_opt.spv"
  echo 'PASS real Vulkan 1.1 AMaZE export glslang 16.5.0 SPIR-V validator/optimizer'
} | tee "$OUT/26904_SHADER_COMPILER_VERBOSE.log"
# The actual APK native loader reads exactly this pinned SPV asset.
ASSET="$SRC/assets/iris26856/rawr/amaze/spv/amaze_export.spv"
cp "$TOOLS/amaze_export_26904.spv" "$ASSET"
[ "$(od -An -tx1 -N4 "$ASSET" | tr -d ' \n')" = '03022307' ]
sha256sum "$ASSET" > "$OUT/26904_GENERATED_SPV_COMPILER_RECEIPT.sha256"
{
  echo 'REAL GLSL COMPILE: PASS pinned glslang 16.5.0 native AMaZE and both runtime ESSL310 watermark variants'
  echo 'AMAZE EXPORT SPV ASSET: REGENERATED FROM MODIFIED RUNTIME SOURCE'
  cat "$OUT/26904_GLSLANG_VERSION.txt"
} > "$OUT/26904_GLSL_REAL_COMPILER.txt"
{
  echo 'REAL SPIR-V VALIDATION: PASS spirv-val pre/post spirv-opt native vulkan1.1 and ESSL310'
  cat "$OUT/26904_SPIRV_TOOLS_VERSION.txt"
} > "$OUT/26904_SPIRV_VALIDATED.txt"
