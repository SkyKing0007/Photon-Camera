#!/usr/bin/env bash
# Full real successful 26951 native and SDR shader compilers, then CURRENT 26952
# new LKR two-radius median GLSL and SDR: pinned ESSL300/310, SPIR-V validator and optimizer.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26952_source.py --live
python3 -S test_26952_chroma.py --live
python3 -S test_26952_halo.py --live
OUT="$PWD/photon_26952_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26952_live_shader_compiles"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED 26952: real pinned GLSLang 16.5 missing' >&2; exit 4; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
# Preserve original entire real 26951 compiler command body, replacing ONLY its
# now-obsolete old-live SHA/test entry points with sealed historical tests and
# the current 26952 source check. Any other original 26951 alteration is fatal.
python3 -S - <<'PY'
from pathlib import Path
import hashlib
root=Path.cwd()
originals={
 'compile_26951_shaders.sh':('c3793466b278fd0fc8d8281a6dc5a13eb5faac7315559e1007b44996595aa938',{
   'python3 -S test_26951_source.py --live':'python3 -S test_26952_source.py --live',
   'python3 -S test_26951_descriptor_abi.py --live':'python3 -S test_26951_descriptor_abi.py --payload'}),
 'compile_26951_sdr_shaders.sh':('d9e7aa939c1d3ffbb687d716e6536b7d324b061fbc4df23597ad04b8c4f08060',{
   'python3 -S test_26951_highlight.py --live':'python3 -S test_26951_highlight.py --payload'})
}
for name,(expected,repl) in originals.items():
 src=(root/name).read_bytes()
 if hashlib.sha256(src).hexdigest()!=expected:raise SystemExit('BLOCKED: original 26951 real compiler changed '+name)
 source=src.decode()
 for before,after in repl.items():
  if source.count(before)!=1 or after in source:raise SystemExit('BLOCKED: 26951 historical live preflight unexpected '+name)
 out=source
 for before,after in repl.items():out=out.replace(before,after,1)
 # Original compile bodies remain EXACTLY the same: only preflights are rerouted.
 check=out
 for before,after in reversed(list(repl.items())):check=check.replace(after,before,1)
 if check!=source:raise SystemExit('BLOCKED: historical compiler body modified '+name)
 path=root/'photon_26952_outputs'/('26952_replay_'+name)
 path.write_text(out)
PY
# Execute with bash -c and original shell-script path as $0 so the original
# `cd "$(dirname "$0")"` operates from project root UNMODIFIED.
for name in compile_26951_shaders.sh compile_26951_sdr_shaders.sh; do
  bash -c "$(cat "$OUT/26952_replay_${name}")" "$PWD/$name"
done
# Both original compilers must have produced genuine compiler/optimizer receipts.
grep -F 'PASS 26951 real Vulkan 1.1 four RAWR shaders with SPIR-V optimizer' photon_26951_outputs/26951_REAL_GLSL_SPIRV_COMPILER.txt
grep -F 'PASS 26951 real ESSL300/310 SDR/gain shader compilation, SPIR-V val/opt' photon_26951_outputs/26951_REAL_SDR_GLSL_SPIRV_COMPILER.txt
python3 -S - <<'PY'
from pathlib import Path
import re, textwrap
out=Path('photon_26952_outputs')
raw=Path('app/src/main/assets/shaders/motionv2/render.glsl').read_text()
if '#version' in raw or raw.count('void main()')!=1:raise SystemExit('BLOCKED new 26952 B render shader syntax input')
for es in ('300','310'):
 (out/f'26952_render_es{es}.frag').write_text(f'#version {es} es\n#line 1\n'+raw)
kt=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt').read_text()
if kt.count('"""#version 300 es')!=1 or kt.count('""".trimIndent()')!=1:raise SystemExit('BLOCKED: cannot extract exactly ONE active LKR GLSL shader')
shader='#version 300 es'+kt.split('"""#version 300 es',1)[1].split('""".trimIndent()',1)[0]
shader=textwrap.dedent(shader)
if shader.count('void main()')!=1:raise SystemExit('BLOCKED: LKR fragment main missing')
for es in ('300','310'):
 (out/f'26952_lkr_median_es{es}.frag').write_text(shader.replace('#version 300 es','#version '+es+' es',1))
PY
exec 3>&1
trap 'rc=$?; trap - ERR; tail -n 140 "$OUT/26952_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :; exit "$rc"' ERR
{
 "$COMPILER" --version
 for name in render lkr_median; do
   if [ "$name" = render ]; then sha256sum app/src/main/assets/shaders/motionv2/render.glsl; else sha256sum app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt; fi
   "$COMPILER" -S frag "$OUT/26952_${name}_es300.frag"
   "$COMPILER" -S frag "$OUT/26952_${name}_es310.frag"
   "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${name}.spv" "$OUT/26952_${name}_es310.frag"
   spirv-val --target-env opengl4.5 "$DIR/${name}.spv"
   spirv-opt --target-env=opengl4.5 -O "$DIR/${name}.spv" -o "$DIR/${name}.opt.spv"
   spirv-val --target-env opengl4.5 "$DIR/${name}.opt.spv"
   sha256sum "$DIR/${name}.spv" "$DIR/${name}.opt.spv"
 done
 spirv-val --version; spirv-opt --version
 echo 'PASS 26952 real ESSL300/310 medians and B render, SPIR-V validator/optimizer'
} > "$OUT/26952_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR; exec 3>&-
