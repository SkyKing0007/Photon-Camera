#!/usr/bin/env bash
# 26923: inherit full 26906 real shader compilation + pinned GLSL/SPIR-V validation.
# Only the 26906 source assertion for B ON 50MP is version-scoped; every compiler,
# glslang/SPIR-V optimizer/validator invocation is preserved exactly.
set -euo pipefail
cd "$(dirname "$0")"
python3 -S build_26923_incremental.py regress
python3 -S - <<'PY'
from pathlib import Path
orig=Path('compile_26906_tone_glsl.sh').read_text()
old="assert 'float iris26906BVisualTone(float y)' in s and '0.330*toeGate' in s\nassert s.count('float iris26906BVisualTone(float y)')==1\n"
new=("if sys.argv[2]=='b_final_50mp':\n"
     "    assert 'IRIS_26922_B_SR_ON_TONE_RESTORE' in s\n"
     "    assert 'iris26906BVisualTone(' not in s\n"
     "    assert 'IRIS_26922_B_SRON_MATCHED_HDR_SDR_QUOTIENT' in s\n"
     "else:\n"
     "    assert 'float iris26906BVisualTone(float y)' in s and '0.330*toeGate' in s\n"
     "    assert s.count('float iris26906BVisualTone(float y)')==1\n")
assert orig.count(old)==1, '26906 original source assertion not uniquely recognized'
for x in ('"$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag',
          'spirv-val --target-env opengl4.5',
          'spirv-opt --target-env=opengl4.5 -O',
          'spirv-opt --version',
          "'motionv2/render.glsl:render' 'motionv2/gainmap.glsl:gainmap' 'iris26876/b_fused_final_p3_gain.frag:b_final_50mp'"):
    assert x in orig, 'historical 26906 compiler gate changed '+x
patched=orig.replace(old,new,1)
assert patched.replace(new,old,1)==orig,'changed compilation procedure'
Path('.photon_26923_tone_compile_full.sh').write_text(patched)
print('PASS inherited 26906 pinned shader compiler invocation byte-identical except 26923 50MP removed-tone source assertion')
PY
trap 'rm -f .photon_26923_tone_compile_full.sh' EXIT
bash .photon_26923_tone_compile_full.sh
# Additional real pinned compiler for exact 26870 inlined Kotlin ES300 shader;
# compile actual ES300 first, and additionally ESSL310 SPIR-V with identical body.
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
OUT="$PWD/photon_26923_outputs"
DIR="$TOOLS/26923_sr_shaders"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit)"
[ -x "$COMPILER" ] || { echo 'BLOCKED: missing pinned GLSL 16.5.0'; exit 4; }
"$COMPILER" --version > "$OUT/26923_GLSLANG_VERSION.txt"
grep -F '16.5.0' "$OUT/26923_GLSLANG_VERSION.txt" >/dev/null
command -v spirv-opt >/dev/null
command -v spirv-val >/dev/null
python3 -S - <<'PY'
from pathlib import Path
import textwrap,re,hashlib
r=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt')
s=r.read_text()
assert s.count('val shader="""')==1
src=s.split('val shader="""',1)[1].split('""".trimIndent()',1)[0]
assert src.lstrip().startswith('#version 300 es')
src=textwrap.dedent(src).strip()+'\n'
# 26923 V4: exact successful 26922 inline shader ABI keeps its 26922 uniform.
assert src.count('uniform int uIris26922SrOn;')==1 and 'IRIS_26922_SR_ON_UNCERTAINTY_AWARE_CHROMA' in src
out=Path('.photon_26904_incremental_work/real_shader_tools/26923_sr_shaders')
(out/'chroma_es300.frag').write_text(src)
(out/'chroma_es310.frag').write_text(src.replace('#version 300 es','#version 310 es',1))
sh=Path('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag')
assert sh.read_text().startswith('#version 310 es') and 'iris26906BVisualTone(' not in sh.read_text()
assert 'IRIS_26922_B_SRON_MATCHED_HDR_SDR_QUOTIENT' in sh.read_text()
print('PASS exact runtime Kotlin shader extracted verbatim, ESSL300 native syntax and ESSL310 SPIRV body; 50MP B ON source exact')
PY
"$COMPILER" -S frag "$DIR/chroma_es300.frag"
"$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/chroma_es310.spv" "$DIR/chroma_es310.frag"
spirv-val --target-env opengl4.5 "$DIR/chroma_es310.spv"
spirv-opt --target-env=opengl4.5 -O "$DIR/chroma_es310.spv" -o "$DIR/chroma_es310.opt.spv"
spirv-val --target-env opengl4.5 "$DIR/chroma_es310.opt.spv"
"$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/b_final_50mp.spv" app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag
spirv-val --target-env opengl4.5 "$DIR/b_final_50mp.spv"
spirv-opt --target-env=opengl4.5 -O "$DIR/b_final_50mp.spv" -o "$DIR/b_final_50mp.opt.spv"
spirv-val --target-env opengl4.5 "$DIR/b_final_50mp.opt.spv"
{
  echo 'PASS real pinned glslang 16.5.0 ES300+ES310 Kotlin inline SR shadow shader, 50MP B final, unchanged 26906 complete inherited GLSL/SPIR-V compilers'
  cat "$OUT/26923_GLSLANG_VERSION.txt"
  sha256sum app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag
  for f in "$DIR"/*.spv; do sha256sum "$f"; done
  spirv-val --version
  spirv-opt --version
} > "$OUT/26923_SHADER_REAL_COMPILER.txt"
