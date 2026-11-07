#!/usr/bin/env bash
# Mandatory full pinned 16.5.0 ESSL310/SPIR-V compile; no dropped compile gates.
set -euo pipefail
cd "$(dirname "$0")"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
OUTPUT="$PWD/photon_26907_outputs"
mkdir -p "$OUTPUT" "$TOOLS/26907_hue_compiler"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -n "$COMPILER" ] || { echo 'BLOCKED pinned glslang 16.5.0 missing'; exit 4; }
"$COMPILER" --version > "$OUTPUT/26907_HUE_GLSLANG_VERSION.txt"
grep -F '16.5.0' "$OUTPUT/26907_HUE_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S - <<'PY'
import re,ast
from pathlib import Path
runtime=Path('app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl')
s=runtime.read_text()
for part in ('uniform sampler2D HueDeltas','float delta=measuredDelta','oldY/newY','rgbToOklab','oklabToRgb'):
    assert part in s, 'missing dynamic hue shader contract: '+part
assert not s.lstrip().startswith('#version'), 'wrong shader version injection'
compileDir=Path('.photon_26904_incremental_work/real_shader_tools/26907_hue_compiler')
(compileDir/'hue.frag').write_text('#version 310 es\n#line 1\n'+s)
# The RGB probe is also a LIVE GPU fragment shader, assembled in Java from
# literal parts; compile precisely its Java literal bytes, not a mock-up.
java=Path('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PreviewHueMatch.java').read_text()
start=java.index('program.useProgram(')+len('program.useProgram(')
depth=1; inQuote=False; escaped=False; end=None
for i in range(start,len(java)):
    c=java[i]
    if inQuote:
        if escaped: escaped=False
        elif c=='\\': escaped=True
        elif c=='"': inQuote=False
    elif c=='"': inQuote=True
    elif c=='(': depth+=1
    elif c==')':
        depth-=1
        if depth==0: end=i; break
assert end is not None and java[end+1]==';', 'unterminated Java inline probe'
fragment=java[start:end]
parts=re.findall(r'"(?:\\.|[^"\\])*"',fragment)
assert len(parts)>=3 and not re.sub(r'"(?:\\.|[^"\\])*"','',fragment).strip(' \n\t+'), 'unexpected inline GPU source construction'
shader=''.join(ast.literal_eval(part) for part in parts)
assert shader.count('uniform sampler2D InputBuffer;')==1 and 'Output=texture(' in shader
(compileDir/'probe.frag').write_text('#version 310 es\n#line 1\n'+shader)
print('PASS exact 26907 runtime HueLUT and Java inline RGB probe expanded as ESSL310')
PY
FILE="$TOOLS/26907_hue_compiler/hue.frag"
"$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$TOOLS/26907_hue_compiler/hue.spv" "$FILE"
spirv-val --target-env opengl4.5 "$TOOLS/26907_hue_compiler/hue.spv"
spirv-opt --target-env=opengl4.5 -O "$TOOLS/26907_hue_compiler/hue.spv" -o "$TOOLS/26907_hue_compiler/hue.opt.spv"
spirv-val --target-env opengl4.5 "$TOOLS/26907_hue_compiler/hue.opt.spv"
"$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$TOOLS/26907_hue_compiler/probe.spv" "$TOOLS/26907_hue_compiler/probe.frag"
spirv-val --target-env opengl4.5 "$TOOLS/26907_hue_compiler/probe.spv"
spirv-opt --target-env=opengl4.5 -O "$TOOLS/26907_hue_compiler/probe.spv" -o "$TOOLS/26907_hue_compiler/probe.opt.spv"
spirv-val --target-env opengl4.5 "$TOOLS/26907_hue_compiler/probe.opt.spv"
{
  echo 'PASS real pinned GLSL ESSL310 both 26907 hue correction and exact inline camera RGB probe compiled with glslang 16.5.0'
  cat "$OUTPUT/26907_HUE_GLSLANG_VERSION.txt"
} > "$OUTPUT/26907_HUE_SHADER_REAL_COMPILER.txt"
{
  echo 'PASS 26907 new hue shader and exact inline probe spirv-val/spirv-opt opengl4.5'
  spirv-val --version
  spirv-opt --version
} > "$OUTPUT/26907_HUE_SHADER_SPIRV_VALIDATED.txt"
