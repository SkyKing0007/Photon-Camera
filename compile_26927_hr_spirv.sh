#!/usr/bin/env bash
# Native Wronski source unchanged from real successful 26926; compile all prod/trace variants again, no mock.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S build_26927_incremental.py regress
python3 -S test_26927_shader_contract.py --live
python3 -S test_26927_shader_shadow.py --live
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools";OUT="$PWD/photon_26927_outputs";DIR="$TOOLS/26927_current_vulkan"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED pinned glslang16.5.0 unavailable'; exit 4; }
"$COMPILER" --version > "$OUT/26927_WRONSKI_GLSLANG_VERSION.txt"
grep -F 16.5.0 "$OUT/26927_WRONSKI_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null;command -v spirv-opt >/dev/null
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26927 real Vulkan shader failure $rc" >&3;tail -n 100 "$OUT/26927_WRONSKI_SPIRV_REAL_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
 echo 'PASS real pinned glslang 16.5.0 Vulkan1.1 Wronski 3 native shaders, production and trace real SPIR-V optimize/validate'
 cat "$OUT/26927_WRONSKI_GLSLANG_VERSION.txt"
 for label in Iris26923WronskiFinalize Iris26885WronskiChromaGuide Iris26880WaveletCopy;do
  if [ "$label" = Iris26923WronskiFinalize ];then SRC="app/src/main/cpp/iris26864/bridge/${label}.comp";else SRC="app/src/main/cpp/iris26864/${label}.comp";fi
  [ -f "$SRC" ] || { echo "BLOCKED missing native shader $SRC";exit 4; }
  sha256sum "$SRC"
  for variant in prod trace;do
   args=();if [ "$variant" = trace ];then args+=('-DRAWR_PARITY_TRACE=1');fi
   "$COMPILER" -V --target-env vulkan1.1 -S comp "${args[@]}" -o "$DIR/${label}_${variant}.spv" "$SRC"
   spirv-val --target-env vulkan1.1 "$DIR/${label}_${variant}.spv"
   spirv-opt --target-env=vulkan1.1 -O "$DIR/${label}_${variant}.spv" -o "$DIR/${label}_${variant}.opt.spv"
   spirv-val --target-env vulkan1.1 "$DIR/${label}_${variant}.opt.spv"
   sha256sum "$DIR/${label}_${variant}.spv" "$DIR/${label}_${variant}.opt.spv"
  done
 done
 spirv-opt --version;spirv-val --version
} > "$OUT/26927_WRONSKI_SPIRV_REAL_COMPILER.txt" 2>&1
trap - ERR;exec 3>&-
