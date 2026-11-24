#!/usr/bin/env bash
set -eEuo pipefail
cd "$(dirname "$0")"
OUT="$PWD/photon_26983_outputs"
INPUT="$OUT/26983_CON_EXTRACTED_GLSL"
LOG="$OUT/26983_CON_REAL_GLSL_SPIRV_COMPILER.txt"
rm -rf "$INPUT"
python3 -S verify_26983_con_glsl.py --emit "$INPUT"
TOOLS="$PWD/.photon_26904_incremental_work/real_shader_tools"
COMPILER="$(find "$TOOLS/glslang" -type f \( -name glslang -o -name glslangValidator \) -print -quit 2>/dev/null || true)"
[ -x "$COMPILER" ]
"$COMPILER" --version | grep -F '16.5.0'
command -v spirv-val >/dev/null
command -v spirv-opt >/dev/null
mapfile -t SOURCES < <(find "$INPUT" -maxdepth 1 -type f \( -name '*.vert' -o -name '*.frag' -o -name '*.comp' \) | LC_ALL=C sort)
COUNT=13
[ "${#SOURCES[@]}" -eq "$COUNT" ]
WORK="$PWD/.photon_26983_work/26983_con_shader_spirv"
mkdir -p "$WORK"
# V9 Step 60 correction: preserve every real compiler/optimizer/validator gate.
# Emit the EXACT failing phase, shader name, and originating Kotlin file to
# GitHub Actions immediately. Report ALL failures in this one run and fail
# closed after the full inventory. Do not hide diagnostics in a redirected brace.
printf '%s\n' \
  '26983 ACTUAL STATIC GLSL/SPIR-V COMPILATION BEGIN' \
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
 raise SystemExit('26983 BLOCKED: shader metadata missing or ambiguous '+sys.argv[2])
print(matching[0]['location'])
PYMETA
}
run_checked_phase() {
 # Does NOT treat a failing compiler as success; only captures its evidence.
 local source_name="$1" origin="$2" phase="$3"
 shift 3
 local command_log="$WORK/26983_v9_last_phase.log" code=0
 printf 'RUN shader=%s origin=%s phase=%s command=' "$source_name" "$origin" "$phase" >> "$LOG"
 printf '%q ' "$@" >> "$LOG"
 printf '\n' >> "$LOG"
 if "$@" > "$command_log" 2>&1; then
   cat "$command_log" >> "$LOG"
   return 0
 else
   code=$?
   printf 'FAIL 26983 shader=%s origin=%s phase=%s exit=%d\n' \
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
printf '26983 CURRENT SHADER RESULT: pass=%d fail=%d total=%d\n' \
  "$PASSED" "$FAILED" "$COUNT" | tee -a "$LOG"
if [ "$FAILED" -ne 0 ] || [ "$PASSED" -ne "$COUNT" ]; then
  printf 'BLOCKED: %d actual shader toolchain failures; see complete phase diagnostics in this Actions log\n' "$FAILED" | tee -a "$LOG" >&2
  exit 2
fi
printf 'PASS 26983 physical current %d/%d static C ON ESSL GLSL + SPIR-V opt/val; independently pinned source inventory\n' "$COUNT" "$COUNT" >> "$LOG"
printf '%s\n' 'NOT RUN/NOT PROVEN: dynamic Kotlin-assembled donor shader compile on physical Android GPU (cannot honestly substitute static template validation)' >> "$LOG"

printf "%s\n" "PASS 26983 C ON 13/13 static shader stages real GLSL/SPIR-V opt/val" >> "$LOG"
