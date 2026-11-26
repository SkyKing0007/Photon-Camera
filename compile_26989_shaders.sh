#!/usr/bin/env bash
# 26989 V6: mandatory exact successful 26974 V3 24 physical shaders PLUS
# all 299 remaining SHA-pinned current 26989 Experiment C Kotlin GLSL (8 excluded preview shaders are physically gone).
# Never rely only on 26974's stale expanded shader snapshot. Dynamic Kotlin
# assembled shaders are explicitly audited but cannot be compile-proven offline.
set -eEuo pipefail
cd "$(dirname "$0")"
python3 -S test_26989_source.py --live
python3 -S verify_26989_v6_current_glsl.py --selftest
python3 -S verify_26989_v6_current_glsl.py --audit
ORIGINAL=compile_26974_shaders.sh
[ -f "$ORIGINAL" ] || { echo '26989 BLOCKED: original 26974 shader compiler missing' >&2; exit 7; }
EXPECTED_GIT_BLOB=7f31528bc83ba4867476e358c68aee8558201478
[ "$(git hash-object "$ORIGINAL")" = "$EXPECTED_GIT_BLOB" ] || { echo '26989 BLOCKED: actual successful 26974 shader compiler changed' >&2; exit 7; }
TMP=$(mktemp "$PWD/.photon_26989_compile_24.XXXXXXXX.sh")
trap 'rm -f -- "$TMP"' EXIT
python3 -S - "$ORIGINAL" "$TMP" <<'PY'
from pathlib import Path
import sys
original=Path(sys.argv[1]).read_bytes()
old=b'python3 -S test_26974_source.py --live'
new=b'python3 -S test_26989_source.py --live'
if original.count(old)!=1: raise SystemExit('26989 BLOCKED: original 26974 source guard unexpected')
Path(sys.argv[2]).write_bytes(original.replace(old,new))
PY
# Historical 24/24 GLSL/SPIR-V validation, unchanged physical source inputs.
bash "$TMP"
mkdir -p photon_26989_outputs
cp photon_26974_outputs/26974_REAL_GLSL_SPIRV_COMPILER.txt photon_26989_outputs/26989_REAL_GLSL_SPIRV_COMPILER.txt
grep -F 'PASS actual 26974 24/24 C GLES (19 ESSL300+310; 5 ESSL310-only) + OpenGL SPIR-V opt/val' photon_26989_outputs/26989_REAL_GLSL_SPIRV_COMPILER.txt

# NEW: extract current, exact C donor/Kotlin shader strings, instead of
# revalidating only the old snapshot. Inventory source hashes are frozen in
# the stage-one handoff seal and checked against the exact assembled app tree.
python3 -S verify_26989_v6_current_glsl.py --emit
OUT="$PWD/photon_26989_outputs"
INPUT="$OUT/26989_V6_CURRENT_EXTRACTED_GLSL"
LOG="$OUT/26989_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit 2>/dev/null || true)"
[ -x "$COMPILER" ] || { echo '26989 V6 BLOCKED: pinned glslang 16.5.0 missing' >&2; exit 7; }
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null || { echo '26989 V6 BLOCKED: SPIR-V validator missing' >&2; exit 7; }
command -v spirv-opt >/dev/null || { echo '26989 V6 BLOCKED: SPIR-V optimizer missing' >&2; exit 7; }
mapfile -t SOURCES < <(find "$INPUT" -maxdepth 1 -type f \( -name '*.vert' -o -name '*.frag' -o -name '*.comp' \) | LC_ALL=C sort)
COUNT="$(python3 -S - <<'PY'
import json
v=json.load(open('26989_V6_CURRENT_SHADER_INVENTORY.json'))
assert v['static_count'] == 299 and v['dynamic_count'] == 92 and v['source_count'] == v['static_count'] + v['dynamic_count']
print(v['static_count'])
PY
)"
[ "${#SOURCES[@]}" -eq "$COUNT" ] || { echo "26989 V6 BLOCKED: only ${#SOURCES[@]} of $COUNT current static shaders extracted" >&2; exit 7; }
WORK="$PWD/.photon_26989_work/26989_v6_shader_spirv"
mkdir -p "$WORK"
# V9 Step 60 correction: preserve every real compiler/optimizer/validator gate.
# Emit the EXACT failing phase, shader name, and originating Kotlin file to
# GitHub Actions immediately. Report ALL failures in this one run and fail
# closed after the full inventory. Do not hide diagnostics in a redirected brace.
printf '%s\n' \
  '26989 ACTUAL STATIC GLSL/SPIR-V COMPILATION BEGIN' \
  "static_shader_count=$COUNT" > "$LOG"
"$COMPILER" --version >> "$LOG" 2>&1
spirv-val --version >> "$LOG" 2>&1
spirv-opt --version >> "$LOG" 2>&1
sha256sum "${SOURCES[@]}" >> "$LOG"

shader_origin() {
 python3 -S - "$INPUT/COMPILATION_METADATA.json" "$1" <<'PYMETA'
import json,sys
records=json.load(open(sys.argv[1],encoding='utf8'))
matching=[x for x in records if x['file']==sys.argv[2]]
if len(matching)!=1:
 raise SystemExit('26989 BLOCKED: shader metadata missing or ambiguous '+sys.argv[2])
print(matching[0]['location'])
PYMETA
}
run_checked_phase() {
 # Does NOT treat a failing compiler as success; only captures its evidence.
 local source_name="$1" origin="$2" phase="$3"
 shift 3
 local command_log="$WORK/26989_v9_last_phase.log" code=0
 printf 'RUN shader=%s origin=%s phase=%s command=' "$source_name" "$origin" "$phase" >> "$LOG"
 printf '%q ' "$@" >> "$LOG"
 printf '\n' >> "$LOG"
 if "$@" > "$command_log" 2>&1; then
   cat "$command_log" >> "$LOG"
   return 0
 else
   code=$?
   printf 'FAIL 26989 shader=%s origin=%s phase=%s exit=%d\n' \
     "$source_name" "$origin" "$phase" "$code" | tee -a "$LOG" >&2
   printf 'FAILING COMMAND: ' | tee -a "$LOG" >&2
   printf '%q ' "$@" | tee -a "$LOG" >&2
   printf '\n' | tee -a "$LOG" >&2
   cat "$command_log" | tee -a "$LOG" >&2
   return 1
 fi
}
FAILED=0
PASSED=0
for SRC in "${SOURCES[@]}"; do
  BASE="$(basename "$SRC")"
  TYPE="${BASE##*.}"
  case "$TYPE" in frag|vert|comp) ;; *) echo "BLOCKED invalid source stage: $BASE" >&2; exit 8;; esac
  ORIGIN="$(shader_origin "$BASE")"
  CONVERTED="$WORK/$BASE"
  if grep -q '^#version 300 es$' "$SRC"; then
    sed '1s/#version 300 es/#version 310 es/' "$SRC" > "$CONVERTED"
  else
    cp "$SRC" "$CONVERTED"
  fi
  printf 'VERIFY CURRENT C GLSL %s stage=%s origin=%s\n' "$BASE" "$TYPE" "$ORIGIN" >> "$LOG"
  if ! run_checked_phase "$BASE" "$ORIGIN" 'original-ESSL-parse' "$COMPILER" -S "$TYPE" "$SRC"; then
    FAILED=$((FAILED+1)); continue
  fi
  if ! run_checked_phase "$BASE" "$ORIGIN" 'ESSL310-conversion-parse' "$COMPILER" -S "$TYPE" "$CONVERTED"; then
    FAILED=$((FAILED+1)); continue
  fi
  if ! run_checked_phase "$BASE" "$ORIGIN" 'OpenGL-SPIRV-generate' "$COMPILER" -G --auto-map-locations --auto-map-bindings -S "$TYPE" -o "$WORK/$BASE.spv" "$CONVERTED"; then
    FAILED=$((FAILED+1)); continue
  fi
  if ! run_checked_phase "$BASE" "$ORIGIN" 'SPIRV-original-validate' spirv-val --target-env opengl4.5 "$WORK/$BASE.spv"; then
    FAILED=$((FAILED+1)); continue
  fi
  if ! run_checked_phase "$BASE" "$ORIGIN" 'SPIRV-optimize-O' spirv-opt --target-env=opengl4.5 -O "$WORK/$BASE.spv" -o "$WORK/$BASE.opt.spv"; then
    FAILED=$((FAILED+1)); continue
  fi
  if ! run_checked_phase "$BASE" "$ORIGIN" 'SPIRV-optimized-validate' spirv-val --target-env opengl4.5 "$WORK/$BASE.opt.spv"; then
    FAILED=$((FAILED+1)); continue
  fi
  sha256sum "$WORK/$BASE.spv" "$WORK/$BASE.opt.spv" >> "$LOG"
  PASSED=$((PASSED+1))
done
printf '26989 CURRENT SHADER RESULT: pass=%d fail=%d total=%d\n' \
  "$PASSED" "$FAILED" "$COUNT" | tee -a "$LOG"
if [ "$FAILED" -ne 0 ] || [ "$PASSED" -ne "$COUNT" ]; then
  printf 'BLOCKED: %d actual shader toolchain failures; see complete phase diagnostics in this Actions log\n' "$FAILED" | tee -a "$LOG" >&2
  exit 2
fi
printf 'PASS 26989 physical current %d/%d static donor/Iris C ESSL GLSL + SPIR-V opt/val; independently pinned source inventory\n' "$COUNT" "$COUNT" >> "$LOG"
printf '%s\n' 'NOT RUN/NOT PROVEN: dynamic Kotlin-assembled donor shader compile on physical Android GPU (cannot honestly substitute static template validation)' >> "$LOG"
cp "$LOG" "$OUT/26989_V6_STATIC_GLSL_SPIRV_RECEIPT.txt"
printf '%s\n' "PASS inherited historical 24/24 and actual current $COUNT/$COUNT 26989 donor/Iris C shader compilation with pinned glslang/SPIR-V toolchain; dynamic runtime GLSL still needs device" >> "$OUT/26989_REAL_GLSL_SPIRV_COMPILER.txt"
