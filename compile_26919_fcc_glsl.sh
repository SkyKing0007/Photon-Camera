#!/usr/bin/env bash
# 26919 ADDITIVE compiler gate; retain original successful 26918 full gates.
# Compile BOTH exact Kotlin runtime FCC ESSL300 shaders and separate ESSL310
# SPIR-V validation versions, without replacing the ESSL300 runtime sources.
set -euo pipefail
cd "$(dirname "$0")"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
TARGET="$TOOLS/26919_fcc"
OUT="$PWD/photon_26919_outputs"
mkdir -p "$TARGET" "$OUT"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -n "$COMPILER" ] || { echo '26919 BLOCKED pinned glslang 16.5.0 missing'; exit 4; }
"$COMPILER" --version > "$TARGET/pinned_glslang_version.txt"
grep -F '16.5.0' "$TARGET/pinned_glslang_version.txt" >/dev/null
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
python3 -S - <<'PY'
from pathlib import Path
p=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt')
s=p.read_text()
folder=Path('.photon_26904_incremental_work/real_shader_tools/26919_fcc')
for key in ('medianChroma','reconstructChroma'):
    start='val '+key+' = """';end='""".trimIndent()'
    assert s.count(start)==1 and s.count(end)==2, '26919 FCC shader string anchor drift: '+key
    lines=s.split(start,1)[1].split(end,1)[0].splitlines()
    while lines and not lines[0].strip():lines.pop(0)
    while lines and not lines[-1].strip():lines.pop()
    prefix=min(len(l)-len(l.lstrip(' \t')) for l in lines if l.strip())
    shader='\n'.join(l[prefix:] for l in lines)
    assert shader.startswith('#version 300 es\n') and 'uClipAwareBOff26919' in shader
    assert 'uOriginalSensorClip26919' in shader
    (folder/(key+'_exact_300.frag')).write_text(shader+'\n')
    (folder/(key+'_310.frag')).write_text(shader.replace('#version 300 es','#version 310 es',1)+'\n')
print('PASS source-equal Kotlin FCC median/reconstruct runtime ESSL300 expansion')
PY
for key in medianChroma reconstructChroma; do
  "$COMPILER" -S frag -l "$TARGET/${key}_exact_300.frag" > "$TARGET/${key}_essl300_compile.log" 2>&1 || {
    cat "$TARGET/${key}_essl300_compile.log"; exit 1;
  }
  "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag \
    -o "$TARGET/${key}.spv" "$TARGET/${key}_310.frag"
  spirv-val --target-env opengl4.5 "$TARGET/${key}.spv"
  spirv-opt --target-env=opengl4.5 -O "$TARGET/${key}.spv" -o "$TARGET/${key}.opt.spv"
  spirv-val --target-env opengl4.5 "$TARGET/${key}.opt.spv"
done
{
  echo 'REAL PINNED GLSL COMPILE: PASS exact 26919 median/reconstruct ESSL300 runtime and ESSL310 equivalent SPIR-V'
  cat "$TARGET/pinned_glslang_version.txt"
  for key in medianChroma reconstructChroma; do
    sha256sum "$TARGET/${key}_exact_300.frag" "$TARGET/${key}_310.frag"
  done
} > "$OUT/26919_FCC_SHADER_REAL_COMPILER.txt"
{
  echo 'REAL SPIR-V VALIDATION: PASS real val/opt/val for BOTH 26919 FCC shaders, OpenGL4.5 SPIR-V'
  spirv-val --version
  spirv-opt --version
  echo 'spirv-opt --target-env=opengl4.5 -O both FCC shaders: PASS'
  for key in medianChroma reconstructChroma; do
    sha256sum "$TARGET/${key}.spv" "$TARGET/${key}.opt.spv"
  done
} > "$OUT/26919_FCC_SHADER_SPIRV_VALIDATED.txt"
echo 'PASS 26919 real pinned FCCx2 ESSL300 and SPIR-V before/after optimizer'
