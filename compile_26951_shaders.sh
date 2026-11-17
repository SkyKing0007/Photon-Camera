#!/usr/bin/env bash
# Exact 26949 Actions compiler mechanics, broadened to the four changed RAWR Vulkan shaders.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26951_source.py --live
python3 -S test_26951_descriptor_abi.py --live
python3 -S test_26951_math.py --live
OUT="$PWD/photon_26951_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26951_real_rawr_hdrq"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED 26951: pinned real glslang missing' >&2; exit 4; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
exec 3>&1
trap 'rc=$?; trap - ERR; tail -n 120 "$OUT/26951_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :; exit "$rc"' ERR
{
 "$COMPILER" --version
 for name in Iris26887BOffHdrqMerge.comp Iris26888BOffHdrqMismatch.comp Iris26887BOffHdrqMismatchNorm.comp Iris26943BOffHdrqBorder.comp; do
   p="app/src/main/cpp/iris26864/bridge/$name"
   sha256sum "$p"
   "$COMPILER" -V --target-env vulkan1.1 -S comp -o "$DIR/${name}.spv" "$p"
   spirv-val --target-env vulkan1.1 "$DIR/${name}.spv"
   spirv-opt --target-env=vulkan1.1 -O "$DIR/${name}.spv" -o "$DIR/${name}.opt.spv"
   spirv-val --target-env vulkan1.1 "$DIR/${name}.opt.spv"
   sha256sum "$DIR/${name}.spv" "$DIR/${name}.opt.spv"
 done
 spirv-opt --version; spirv-val --version
 echo 'PASS 26951 real Vulkan 1.1 four RAWR shaders with SPIR-V optimizer'
} > "$OUT/26951_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR; exec 3>&-
