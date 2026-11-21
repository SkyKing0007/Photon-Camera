#!/usr/bin/env bash
# Exact successful 26971 pinned toolchain and V1/V2/V3 regression mechanics.
# Compile the exact source-pinned current 26972-C 24 GLES shaders, NOT stale templates.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26972_source.py --live
OUT="$PWD/photon_26972_outputs"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
DIR="$TOOLS/26972_real_current_source_shader_compile"
SHADERS="$PWD/26972_EXACT_EXPANDED_C_SHADERS"
mkdir -p "$OUT" "$DIR"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit 2>/dev/null || true)"
[ -x "$COMPILER" ] || { echo '26972 BLOCKED: exact pinned glslang 16.5.0 missing' >&2; exit 4; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null || { echo '26972 BLOCKED: SPIR-V validator missing' >&2; exit 4; }
command -v spirv-opt >/dev/null || { echo '26972 BLOCKED: SPIR-V optimizer missing' >&2; exit 4; }
(cd "$SHADERS" && sha256sum -c ../26972_EXPANDED_SHADER_HASHES.sha256)
python3 -S - <<'PYSHADER'
from pathlib import Path
import re
root=Path('26972_EXACT_EXPANDED_C_SHADERS')
files=sorted(root.glob('*.frag'))
if len(files)!=24:raise SystemExit('26972 BLOCKED 24 current C source shader count')
reserved=set('''attribute varying precision highp mediump lowp in out inout uniform buffer shared coherent volatile restrict readonly writeonly const invariant layout flat smooth noperspective patch sample centroid subroutine common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output filter sizeof cast namespace using row_major switch default case struct while do for if else continue break return discard true false void int uint float double bool atomic_uint'''.split())
reserved.update(('gl_FragColor','gl_FragData','gl_FragCoord','gl_VertexID','gl_Position'))
qualifier=r'(?:\b(?:highp|mediump|lowp|readonly|writeonly|flat|smooth|centroid)\s+)*'
datatype=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|isampler2D|usampler2D|sampler3D|sampler2DArray)'
var=re.compile(r'\b(?:uniform|in|out|const)?\s*'+qualifier+r'\b'+datatype+r'\s+(\w+)\s*(?=[;=,\[])')
versions={'300':0,'310':0}
for file in files:
 s=file.read_text()
 if not (s.startswith('#version 300 es\n') or s.startswith('#version 310 es\n')) or s.count('void main()')!=1:raise SystemExit('26972 BLOCKED incorrect C shader '+file.name)
 versions[s.split(' ',2)[1]]+=1
 code=re.sub(r'//[^\n]*|/\*.*?\*/','',s,flags=re.S)
 for match in var.finditer(code):
  name=match.group(1)
  if name in reserved or name.startswith('gl_'):raise SystemExit('26972 BLOCKED GLSL reserved declaration '+file.name+' '+name)
if versions!={'300':19,'310':5}:raise SystemExit('26972 BLOCKED unexpected 19 ES300 / 5 ES310 C shader versions '+str(versions))
print('PASS 26972 physical reserved GLSL declaration scan: 19 ES300, 5 ES310')
PYSHADER
exec 3>&1
trap 'rc=$?;trap - ERR;echo "26972 real shader compile FAILED $rc" >&3;tail -n 150 "$OUT/26972_REAL_GLSL_SPIRV_COMPILER.txt" >&3 || :;exit "$rc"' ERR
{
  "$COMPILER" --version
  spirv-val --version
  spirv-opt --version
  for src in "$SHADERS"/*.frag; do
    name="$(basename "$src")"
    sha256sum "$src" | sed "s@  .*@  $name@"
    "$COMPILER" -S frag "$src"
    # ES310 is required by five donor arithmetic/format shaders; do not require ES300 for those.
    if grep -q '^#version 300 es$' "$src"; then
      sed '1s/#version 300 es/#version 310 es/' "$src" > "$DIR/${name%.frag}.es310.frag"
    else
      cp "$src" "$DIR/${name%.frag}.es310.frag"
    fi
    "$COMPILER" -S frag "$DIR/${name%.frag}.es310.frag"
    "$COMPILER" -G --auto-map-locations --auto-map-bindings -S frag -o "$DIR/${name%.frag}.spv" "$DIR/${name%.frag}.es310.frag"
    spirv-val --target-env opengl4.5 "$DIR/${name%.frag}.spv"
    spirv-opt --target-env=opengl4.5 -O "$DIR/${name%.frag}.spv" -o "$DIR/${name%.frag}.opt.spv"
    spirv-val --target-env opengl4.5 "$DIR/${name%.frag}.opt.spv"
    sha256sum "$DIR/${name%.frag}.spv" "$DIR/${name%.frag}.opt.spv"
  done
  echo 'PASS actual 26972 24/24 C GLES (19 ESSL300+310; 5 ESSL310-only) + OpenGL SPIR-V opt/val'
} > "$OUT/26972_REAL_GLSL_SPIRV_COMPILER.txt" 2>&1
trap - ERR
exec 3>&-
