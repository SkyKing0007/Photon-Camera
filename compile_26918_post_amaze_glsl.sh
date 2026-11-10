#!/usr/bin/env bash
# 26918 additional compiler gate only: preserve every actual 26917 shader/NDK
# gate and compile the exact Kotlin-embedded ESSL300 runtime source directly.
set -euo pipefail
cd "$(dirname "$0")"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
TARGET="$TOOLS/26918_chroma"
OUT="$PWD/photon_26918_outputs"
mkdir -p "$TARGET" "$OUT"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -n "$COMPILER" ] || { echo '26918 BLOCKED pinned glslang 16.5.0 missing'; exit 4; }
"$COMPILER" --version > "$TARGET/pinned_glslang_version.txt"
grep -F '16.5.0' "$TARGET/pinned_glslang_version.txt" >/dev/null
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S - <<'PY'
from pathlib import Path
p=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt')
s=p.read_text();start='val shader="""';end='""".trimIndent()'
assert s.count(start)==s.count(end)==1,'26918 GLSL string ownership drift'
lines=s.split(start,1)[1].split(end,1)[0].splitlines()
while lines and not lines[0].strip():lines.pop(0)
while lines and not lines[-1].strip():lines.pop()
minimum=min(len(line)-len(line.lstrip(' \t')) for line in lines if line.strip())
shader='\n'.join(line[minimum:] for line in lines)
assert shader.startswith('#version 300 es\n'),'actual runtime shader lost ESSL300'
assert shader.count('uniform int uIris26918BypassSpatialChroma;')==1
assert 'vec4(rawrHighlightOff(raw.rgb),raw.a);' in shader
assert 'if(uIris26918BypassSpatialChroma!=0)' in shader
p=Path('.photon_26904_incremental_work/real_shader_tools/26918_chroma')
(p/'post_amaze_exact_300.frag').write_text(shader+'\n')
# Only the testing target has its GLSL version raised: the compiled ESSL300
# source itself remains byte-identical to the Kotlin runtime source.
(p/'post_amaze_310.frag').write_text(shader.replace('#version 300 es','#version 310 es',1)+'\n')
print('PASS captured exact Kotlin-embedded post-AMaZE ESSL300 runtime shader')
PY
# First compile/link the EXACT runtime ESSL300 text with the pinned compiler.
"$COMPILER" -S frag -l "$TARGET/post_amaze_exact_300.frag" > "$TARGET/essl300_compile.log" 2>&1 || { cat "$TARGET/essl300_compile.log"; exit 1; }
# Real SPIR-V tools cannot represent ESSL300 directly. Validate identical
# semantics as ESSL310 separately, without shipping that transformed shader.
"$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag \
  -o "$TARGET/post_amaze_310.spv" "$TARGET/post_amaze_310.frag"
spirv-val --target-env opengl4.5 "$TARGET/post_amaze_310.spv"
spirv-opt --target-env=opengl4.5 -O "$TARGET/post_amaze_310.spv" \
  -o "$TARGET/post_amaze_310.opt.spv"
spirv-val --target-env opengl4.5 "$TARGET/post_amaze_310.opt.spv"
{
  echo 'REAL PINNED GLSL COMPILE: PASS actual 26918 post-AMaZE runtime ESSL300 text'
  echo 'REAL PINNED 16.5.0: PASS ESSL300 syntax/link plus ESSL310 SPIR-V compilation'
  cat "$TARGET/pinned_glslang_version.txt"
  sha256sum "$TARGET/post_amaze_exact_300.frag" "$TARGET/post_amaze_310.frag"
} > "$OUT/26918_CHROMA_SHADER_REAL_COMPILER.txt"
{
  echo 'REAL SPIR-V VALIDATION: PASS exact-logic ESSL310 test, glslang + spirv-val/spirv-opt/spirv-val opengl4.5'
  spirv-val --version
  spirv-opt --version
  sha256sum "$TARGET/post_amaze_310.spv" "$TARGET/post_amaze_310.opt.spv"
} > "$OUT/26918_CHROMA_SHADER_SPIRV_VALIDATED.txt"
echo 'PASS 26918 exact runtime ESSL300 plus equivalent ESSL310 SPIR-V/optimizer verified; no runtime shader swap'
