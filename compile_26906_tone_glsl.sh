#!/usr/bin/env bash
# Real pinned 16.5.0 glslang/SPIRV compile for every 26906 changed runtime fragment shader.
set -euo pipefail
cd "$(dirname "$0")"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
OUTPUT="$PWD/photon_26906_outputs"
mkdir -p "$OUTPUT" "$TOOLS/26906_tone_compiler"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -n "$COMPILER" ] || { echo 'BLOCKED pinned glslang16.5 missing'; exit 4; }
"$COMPILER" --version > "$OUTPUT/26906_TONE_GLSLANG_VERSION.txt"
grep -F '16.5.0' "$OUTPUT/26906_TONE_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
for ENTRY in 'motionv2/render.glsl:render' 'motionv2/gainmap.glsl:gainmap' 'iris26876/b_fused_final_p3_gain.frag:b_final_50mp'; do
  SOURCE="${ENTRY%%:*}"
  NAME="${ENTRY##*:}"
  python3 -S - "$SOURCE" "$NAME" <<'PY'
from pathlib import Path
import sys
src=Path('app/src/main/assets/shaders')/sys.argv[1]
out=Path('.photon_26904_incremental_work/real_shader_tools/26906_tone_compiler')/(sys.argv[2]+'.frag')
s=src.read_text()
assert 'float iris26906BVisualTone(float y)' in s and '0.330*toeGate' in s
assert s.count('float iris26906BVisualTone(float y)')==1
if s.startswith('#version 310 es'):
    out.write_text(s)
else:
    assert not s.lstrip().startswith('#version')
    out.write_text('#version 310 es\n#line 1\n'+s)
print('PASS exact 26906 runtime GL shader expansion',src,out)
PY
  FILE="$TOOLS/26906_tone_compiler/${NAME}.frag"
  "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$TOOLS/26906_tone_compiler/${NAME}.spv" "$FILE"
  spirv-val --target-env opengl4.5 "$TOOLS/26906_tone_compiler/${NAME}.spv"
  spirv-opt --target-env=opengl4.5 -O "$TOOLS/26906_tone_compiler/${NAME}.spv" -o "$TOOLS/26906_tone_compiler/${NAME}.opt.spv"
  spirv-val --target-env opengl4.5 "$TOOLS/26906_tone_compiler/${NAME}.opt.spv"
  echo "PASS pinned 16.5.0 glslang ESSL310 + spirv-val + spirv-opt 26906 $NAME"
done | tee "$OUTPUT/26906_TONE_SHADER_FULL_REAL_COMPILER.log"
{
 echo 'PASS real pinned GLSL ESSL310 three 26906 changed final shaders compiled with glslang 16.5.0'
 echo 'PASS real spirv-val opengl4.5 each shader before and after spirv-opt --target-env=opengl4.5 -O'
 cat "$OUTPUT/26906_TONE_GLSLANG_VERSION.txt"
} > "$OUTPUT/26906_TONE_SHADER_REAL_COMPILER.txt"
{
 echo 'PASS three 26906 final fragment shaders spirv-val/spirv-opt opengl4.5'
 spirv-val --version
 spirv-opt --version
} > "$OUTPUT/26906_TONE_SHADER_SPIRV_VALIDATED.txt"
