#!/usr/bin/env bash
# Current actual real 26934 FIVE GLES shaders: no mock, real ES300/310 and
# pinned glslang 16.5.0 + spirv-opt + spirv-val; no previous APK build.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26934_shader_contract.py --live --extract
python3 -S test_26934_highlight_math.py --live
OUT="$PWD/photon_26934_outputs";TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26934_current_real_gles";mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED missing successful pinned glslang 16.5.0'; exit 4; }
"$COMPILER" --version > "$OUT/26934_GLSLANG_VERSION.txt"
grep -F 16.5.0 "$OUT/26934_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null;command -v spirv-opt >/dev/null
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26934 actual shader compilation failed $rc" >&3;tail -n 110 "$OUT/26934_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
  echo 'PASS actual 26934 inline ESSL 300 310 pinned glslang 16.5.0 all five shaders; SPIR-V optimized and validated from current source'
  cat "$OUT/26934_GLSLANG_VERSION.txt"
  for kind in raw_lens_median lkr_smooth_white motion_render motion_gainmap b_native_final;do
    if [ "$kind" != b_native_final ];then
      s="$OUT/26934_${kind}_es300.frag"
      sha256sum "$s";"$COMPILER" -S frag "$s"
    fi
    s="$OUT/26934_${kind}_es310.frag"
    sha256sum "$s"
    "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${kind}.spv" "$s"
    spirv-val --target-env opengl4.5 "$DIR/${kind}.spv"
    spirv-opt --target-env=opengl4.5 -O "$DIR/${kind}.spv" -o "$DIR/${kind}.opt.spv"
    spirv-val --target-env opengl4.5 "$DIR/${kind}.opt.spv"
    sha256sum "$DIR/${kind}.spv" "$DIR/${kind}.opt.spv"
  done
  spirv-opt --version;spirv-val --version
} > "$OUT/26934_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR;exec 3>&-
