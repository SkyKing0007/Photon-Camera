#!/usr/bin/env bash
# Mandatory real NEW changed GLSL, three shaders; Android Vulkan/OpenGL SPIR-V.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26948_sdr_hdr_math.py --live
OUT="$PWD/photon_26948_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26948_B_sdr_flicker_real_compiler"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED: missing pinned real glslang 16.5 compiler' >&2; exit 4; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S - <<'PY'
from pathlib import Path
p=Path('photon_26948_outputs')
for name in ('render','gainmap'):
 raw=Path('app/src/main/assets/shaders/motionv2/'+name+'.glsl').read_text()
 if '#version' in raw or raw.count('void main()')!=1:raise SystemExit('invalid active B render/gain GLSL')
 for version in ('300','310'):
  (p/f'26948_motionv2_{name}_es{version}.frag').write_text(f'#version {version} es\n#line 1\n'+raw)
fused=Path('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag').read_text()
if not fused.startswith('#version 310 es') or fused.count('void main()')!=1:raise SystemExit('invalid B ON true2x shader')
# Also prove live embedded 2x CFA GLSL without string-interpolation/template changes.
s=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856True2xCfa.kt').read_text()
a=s.index('    val accumulate = """')+len('    val accumulate = """');b=s.index('""".trimIndent()',a)
acc=s[a:b];acc='\n'.join(x.strip() for x in acc.splitlines() if x.strip())+'\n'
if not acc.startswith('#version 300 es') or 'float iris26948BRowGain(' not in acc:raise SystemExit('2x embedded shader not extracted')
(p/'26948_B_true2x_accumulate.frag').write_text(acc)
s=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
a=s.index('    val normalCfaTemporalAccumulate26852 = """')+len('    val normalCfaTemporalAccumulate26852 = """');b=s.index('""".trimIndent()',a)
acc=s[a:b];acc='\n'.join(x.strip() for x in acc.splitlines() if x.strip())+'\n'
if not acc.startswith('#version 300 es') or 'float iris26948BRowCorrect(' not in acc:raise SystemExit('B OFF embedded shader not extracted')
(p/'26948_B_off_temporal_accumulate.frag').write_text(acc)
PY
exec 3>&1
trap 'rc=$?; trap - ERR; echo "26948 real GLSL/SPIR-V failed rc=$rc" >&3; tail -n 130 "$OUT/26948_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :; exit "$rc"' ERR
{
 echo 'BEGIN 26948 actual edited B GLSL glslang 16.5, SPIR-V optimizer and val'
 "$COMPILER" --version
 for source in app/src/main/assets/shaders/motionv2/render.glsl app/src/main/assets/shaders/motionv2/gainmap.glsl app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag; do
   sha256sum "$source"
 done
 for target in "$OUT/26948_motionv2_render_es300.frag" "$OUT/26948_motionv2_gainmap_es300.frag" "$OUT/26948_B_true2x_accumulate.frag" "$OUT/26948_B_off_temporal_accumulate.frag" app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag; do
   sha256sum "$target"
   "$COMPILER" -S frag "$target"
 done
 for file in "$OUT/26948_motionv2_render_es310.frag" "$OUT/26948_motionv2_gainmap_es310.frag" app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag; do
   stem="$(basename "$file" | sed 's/\.frag$//')"
   "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${stem}.spv" "$file"
   spirv-val --target-env opengl4.5 "$DIR/${stem}.spv"
   spirv-opt --target-env=opengl4.5 -O "$DIR/${stem}.spv" -o "$DIR/${stem}.opt.spv"
   spirv-val --target-env opengl4.5 "$DIR/${stem}.opt.spv"
   sha256sum "$DIR/${stem}.spv" "$DIR/${stem}.opt.spv"
 done
 spirv-opt --version; spirv-val --version
 echo 'PASS 26948 real pinned GLES/SPIR-V current three shader sources'
} > "$OUT/26948_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR; exec 3>&-
