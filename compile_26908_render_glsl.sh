#!/usr/bin/env bash
# Photon 26908: real pinned GLSL16.5 + SPIR-V compile of exact changed render.glsl.
# Historical 26904, 26906, 26907 GLSL compilers still run unchanged first.
set -euo pipefail
cd "$(dirname "$0")"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
OUTPUT="$PWD/photon_26908_outputs"
DIR="$TOOLS/26908_render_compiler"
mkdir -p "$OUTPUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -n "$COMPILER" ] || { echo 'BLOCKED: pinned glslang missing'; exit 4; }
"$COMPILER" --version > "$OUTPUT/26908_GLSLANG_VERSION.txt"
grep -F '16.5.0' "$OUTPUT/26908_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-val
command -v spirv-opt
python3 -S - <<'PYSHADER'
from pathlib import Path
s=Path('app/src/main/assets/shaders/motionv2/render.glsl').read_text()
assert s.count('uniform int iris26908NightPresentationLiftEnabled;')==1
assert s.count('vec3 iris26908NightPresentationLift(vec3 rgb)')==1
assert s.count('linearSrgb=iris26908NightPresentationLift(linearSrgb);')==1
assert 'float ev=0.75*shadowGate*highlightGate;' in s
assert 'linearSrgb=iris26638UserSaturation(linearSrgb,iris26630MotionSaturation);' in s
assert 'float iris26906BVisualTone(float y)' in s
assert '#version' not in s
Path('.photon_26904_incremental_work/real_shader_tools/26908_render_compiler/render.frag').write_text('#version 310 es\n#line 1\n'+s)
print('PASS source expanded from exact running GLSL shader')
PYSHADER
"$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/render.spv" "$DIR/render.frag"
spirv-val --target-env opengl4.5 "$DIR/render.spv"
spirv-opt --target-env=opengl4.5 -O "$DIR/render.spv" -o "$DIR/render.opt.spv"
spirv-val --target-env opengl4.5 "$DIR/render.opt.spv"
{ echo 'PASS real pinned 16.5.0 ESSL310 compile of EXACT 26908 Night render/shadow/highlight/saturation shader'; cat "$OUTPUT/26908_GLSLANG_VERSION.txt"; } > "$OUTPUT/26908_RENDER_SHADER_REAL_COMPILER.txt"
{ echo 'PASS spirv-val + spirv-opt --target-env=opengl4.5 -O of actual 26908 render'; spirv-val --version; spirv-opt --version; } > "$OUTPUT/26908_RENDER_SHADER_SPIRV_VALIDATED.txt"
