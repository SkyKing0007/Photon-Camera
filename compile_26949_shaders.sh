#!/usr/bin/env bash
# 26949 actual B OFF runtime-expanded Kotlin GLSL source; new real pinned compiler gate.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26949_restore.py --live
OUT="$PWD/photon_26949_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26949_b_off_exact_rawr_amaze_fcc"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED 26949: missing 16.5.0 PINNED REAL GLSL compiler' >&2; exit 4; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S - <<'PY'
from pathlib import Path
import re
s=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
assert s.count('val shader="""')==1
src=s.split('val shader="""',1)[1].split('""".trimIndent()',1)[0]
# Kotlin trimIndent(): nonblank leading/trailing lines, minimum indent (first
# #version line has none) removed; there are no interpolation tokens.
assert not ('$' in src)
lines=src.splitlines()
while lines and not lines[-1].strip():lines.pop()
while lines and not lines[0].strip():lines.pop(0)
indent=min(len(x)-len(x.lstrip()) for x in lines if x.strip())
real='\n'.join(x[indent:] if x.strip() else '' for x in lines)+'\n'
if not real.startswith('#version 300 es\n') or real.count('void main()')!=1 or real.count('oPostWbCameraRgb')<5:raise SystemExit('26949 runtime GL shader extraction failed')
if real.count('if(uIris26924BOff!=0){\n            oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);')!=1:raise SystemExit('26949 restore early branch missing')
# Bounded GLSL ES reserved-identifier check on *actual* compiled runtime source.
for word in ('input','output','namespace','packed','sample','subroutine','goto','coherent','volatile','restrict','readonly','writeonly','filter','common','partition','active'):
 if re.search(r'\b(?:uniform|float|int|vec[234]|bool|sampler2D|ivec2)\s+'+word+r'\b',real):raise SystemExit('reserved GLSL identifier '+word)
out=Path('photon_26949_outputs')
(out/'26949_B_off_post_amaze_runtime_es300.frag').write_text(real)
(out/'26949_B_off_post_amaze_mirror_es310.frag').write_text(real.replace('#version 300 es','#version 310 es',1))
print('PASS extract exact runtime-expanded GLES300, reserved names, original highlight OFF')
PY
exec 3>&1
trap 'rc=$?; trap - ERR; echo "26949 REAL compiler gate FAILED rc=$rc" >&3; tail -n 100 "$OUT/26949_REAL_GLSL_COMPILER.txt" >&3 || :; exit "$rc"' ERR
{
 echo 'BEGIN 26949 REAL PINNED GLSL compile + SPIR-V supplementary mirror proof'
 "$COMPILER" --version
 sha256sum app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt \
  "$OUT/26949_B_off_post_amaze_runtime_es300.frag"
 "$COMPILER" -S frag "$OUT/26949_B_off_post_amaze_runtime_es300.frag"
 "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/26949_b_off_post_amaze.spv" "$OUT/26949_B_off_post_amaze_mirror_es310.frag"
 spirv-val --target-env opengl4.5 "$DIR/26949_b_off_post_amaze.spv"
 spirv-opt --target-env=opengl4.5 -O "$DIR/26949_b_off_post_amaze.spv" -o "$DIR/26949_b_off_post_amaze.opt.spv"
 spirv-val --target-env opengl4.5 "$DIR/26949_b_off_post_amaze.opt.spv"
 sha256sum "$DIR/26949_b_off_post_amaze.spv" "$DIR/26949_b_off_post_amaze.opt.spv"
 spirv-val --version; spirv-opt --version
 echo 'PASS 26949 real pinned runtime-expanded GLES300 post-AMaZE shader'
} > "$OUT/26949_REAL_GLSL_COMPILER.txt" 2>&1
trap - ERR; exec 3>&-
