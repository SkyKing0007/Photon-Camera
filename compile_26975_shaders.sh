#!/usr/bin/env bash
# 26975 V6: mandatory exact successful 26974 V3 24 physical shaders PLUS
# all 178 independently extracted, SHA-pinned static Kotlin donor/Iris C GLSL.
# Never rely only on 26974's stale expanded shader snapshot. Dynamic Kotlin
# assembled shaders are explicitly audited but cannot be compile-proven offline.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26975_source.py --live
python3 -S verify_26975_v6_current_glsl.py --selftest
python3 -S verify_26975_v6_current_glsl.py --audit
ORIGINAL=compile_26974_shaders.sh
[ -f "$ORIGINAL" ] || { echo '26975 BLOCKED: original 26974 shader compiler missing' >&2; exit 7; }
EXPECTED_GIT_BLOB=7f31528bc83ba4867476e358c68aee8558201478
[ "$(git hash-object "$ORIGINAL")" = "$EXPECTED_GIT_BLOB" ] || { echo '26975 BLOCKED: actual successful 26974 shader compiler changed' >&2; exit 7; }
TMP=$(mktemp "$PWD/.photon_26975_compile_24.XXXXXXXX.sh")
trap 'rm -f -- "$TMP"' EXIT
python3 -S - "$ORIGINAL" "$TMP" <<'PY'
from pathlib import Path
import sys
original=Path(sys.argv[1]).read_bytes()
old=b'python3 -S test_26974_source.py --live'
new=b'python3 -S test_26975_source.py --live'
if original.count(old)!=1: raise SystemExit('26975 BLOCKED: original 26974 source guard unexpected')
Path(sys.argv[2]).write_bytes(original.replace(old,new))
PY
# Historical 24/24 GLSL/SPIR-V validation, unchanged physical source inputs.
bash "$TMP"
mkdir -p photon_26975_outputs
cp photon_26974_outputs/26974_REAL_GLSL_SPIRV_COMPILER.txt photon_26975_outputs/26975_REAL_GLSL_SPIRV_COMPILER.txt
grep -F 'PASS actual 26974 24/24 C GLES (19 ESSL300+310; 5 ESSL310-only) + OpenGL SPIR-V opt/val' photon_26975_outputs/26975_REAL_GLSL_SPIRV_COMPILER.txt

# NEW: extract current, exact C donor/Kotlin shader strings, instead of
# revalidating only the old snapshot. Inventory source hashes are frozen in
# the stage-one handoff seal and checked against the exact assembled app tree.
python3 -S verify_26975_v6_current_glsl.py --emit
OUT="$PWD/photon_26975_outputs"
INPUT="$OUT/26975_V6_CURRENT_EXTRACTED_GLSL"
LOG="$OUT/26975_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit 2>/dev/null || true)"
[ -x "$COMPILER" ] || { echo '26975 V6 BLOCKED: pinned glslang 16.5.0 missing' >&2; exit 7; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null || { echo '26975 V6 BLOCKED: SPIR-V validator missing' >&2; exit 7; }
command -v spirv-opt >/dev/null || { echo '26975 V6 BLOCKED: SPIR-V optimizer missing' >&2; exit 7; }
mapfile -t SOURCES < <(find "$INPUT" -maxdepth 1 -type f \( -name '*.vert' -o -name '*.frag' -o -name '*.comp' \) | LC_ALL=C sort)
COUNT="$(python3 -S - <<'PY'
import json
v=json.load(open('26975_V6_CURRENT_SHADER_INVENTORY.json'))
assert v['static_count'] == 178 and v['source_count'] == v['static_count'] + v['dynamic_count']
print(v['static_count'])
PY
)"
[ "${#SOURCES[@]}" -eq "$COUNT" ] || { echo "26975 V6 BLOCKED: only ${#SOURCES[@]} of $COUNT current static shaders extracted" >&2; exit 7; }
WORK="$PWD/.photon_26975_work/26975_v6_shader_spirv"
mkdir -p "$WORK"
# Always report actual failure, never substitute an old receipt.
trap 'rc=$?; echo "26975 V6 physical current GLSL compile FAILED $rc" >&2; [ -f "$LOG" ] && tail -n 75 "$LOG" >&2 || :; exit "$rc"' ERR
{
 "$COMPILER" --version
 spirv-val --version
 spirv-opt --version
 sha256sum "$INPUT"/*.{frag,comp,vert} 2>/dev/null || :
 for SRC in "${SOURCES[@]}"; do
   BASE="$(basename "$SRC")"
   TYPE="${BASE##*.}"
   case "$TYPE" in frag|vert|comp) ;; *) echo 'invalid source stage' >&2; exit 8;; esac
   echo "VERIFY CURRENT C GLSL $BASE stage=$TYPE"
   # Actual ESSL 300/310 parser and semantic checks, not just regex.
   "$COMPILER" -S "$TYPE" "$SRC"
   # Historical 26974 SPIR-V mechanics require ESSL >= 310 for -G.
   CONVERTED="$WORK/$BASE"
   if grep -q '^#version 300 es$' "$SRC"; then
     sed '1s/#version 300 es/#version 310 es/' "$SRC" > "$CONVERTED"
   else
     cp "$SRC" "$CONVERTED"
   fi
   "$COMPILER" -S "$TYPE" "$CONVERTED"
   "$COMPILER" -G --auto-map-locations --auto-map-bindings -S "$TYPE" -o "$WORK/$BASE.spv" "$CONVERTED"
   spirv-val --target-env opengl4.5 "$WORK/$BASE.spv"
   spirv-opt --target-env=opengl4.5 -O "$WORK/$BASE.spv" -o "$WORK/$BASE.opt.spv"
   spirv-val --target-env opengl4.5 "$WORK/$BASE.opt.spv"
   sha256sum "$WORK/$BASE.spv" "$WORK/$BASE.opt.spv"
 done
 echo "PASS 26975 V6 physical current $COUNT/$COUNT static donor/Iris C ESSL GLSL + SPIR-V opt/val; independently pinned source inventory"
 echo 'NOT RUN/NOT PROVEN: dynamic Kotlin-assembled donor shader compile on physical Android GPU (cannot honestly substitute static template validation)'
} > "$LOG" 2>&1
trap - ERR
cp "$LOG" "$OUT/26975_V6_STATIC_GLSL_SPIRV_RECEIPT.txt"
printf '%s\n' "PASS inherited historical 24/24 and actual current $COUNT/$COUNT V6 donor/Iris C shader compilation with pinned glslang/SPIR-V toolchain; dynamic runtime GLSL still needs device" >> "$OUT/26975_REAL_GLSL_SPIRV_COMPILER.txt"
