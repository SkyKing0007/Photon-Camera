#!/usr/bin/env bash
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26951_highlight.py --live
OUT="$PWD/photon_26951_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26951_sdr_real_gpu"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED: missing pinned glslang' >&2; exit 4; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S - <<'PYGLSL'
from pathlib import Path
out=Path('photon_26951_outputs')
for name in ('render','gainmap'):
 src=Path('app/src/main/assets/shaders/motionv2/'+name+'.glsl').read_text()
 if '#version' in src or src.count('void main()')!=1:raise SystemExit('bad 26951 B GLSL input '+name)
 for ver in ('300','310'):
  (out/f'26951_{name}_es{ver}.frag').write_text(f'#version {ver} es\n#line 1\n'+src)
PYGLSL
exec 3>&1
trap 'rc=$?; trap - ERR; tail -n 100 "$OUT/26951_REAL_SDR_GLSL_SPIRV_COMPILER.txt" >&3 || :; exit "$rc"' ERR
{
 "$COMPILER" --version
 for name in render gainmap; do
  sha256sum "app/src/main/assets/shaders/motionv2/${name}.glsl"
  "$COMPILER" -S frag "$OUT/26951_${name}_es300.frag"
  "$COMPILER" -S frag "$OUT/26951_${name}_es310.frag"
  "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${name}.spv" "$OUT/26951_${name}_es310.frag"
  spirv-val --target-env opengl4.5 "$DIR/${name}.spv"
  spirv-opt --target-env=opengl4.5 -O "$DIR/${name}.spv" -o "$DIR/${name}.opt.spv"
  spirv-val --target-env opengl4.5 "$DIR/${name}.opt.spv"
  sha256sum "$DIR/${name}.spv" "$DIR/${name}.opt.spv"
 done
 spirv-val --version; spirv-opt --version
 echo 'PASS 26951 real ESSL300/310 SDR/gain shader compilation, SPIR-V val/opt'
} > "$OUT/26951_REAL_SDR_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR; exec 3>&-
