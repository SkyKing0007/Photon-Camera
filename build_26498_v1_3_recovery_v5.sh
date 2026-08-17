#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

V4="build_26498_v1_3_recovery_v4.sh"
V5_VERIFY="verify_26498_v1_3_recovery_v5_source_integrity.py"
EXPECTED_V4="71411c724c504fa2504158d409152e693ef97bf728f3bf3965415b5b784beb27"
EXPECTED_VERIFY="1e5d7f84115bc3f928334961675d984eecf718506cba3f72feb66994020ed1b5"

fail(){ echo "ERROR: $*" >&2; exit 1; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

[[ "$(git branch --show-current)" == "experimental-clean-photon-rebuild" ]] || fail "wrong branch"
[[ "$(git branch --show-current)" != "dev" ]] || fail "refusing dev"
[[ -f "$V4" ]] || fail "missing proven V4 source script"
[[ "$(sha "$V4")" == "$EXPECTED_V4" ]] || fail "V4 source script identity mismatch"
[[ "$(sha "$V5_VERIFY")" == "$EXPECTED_VERIFY" ]] || fail "V5 verifier identity mismatch"
python3 -m py_compile "$V5_VERIFY"
python3 "$V5_VERIFY" self-test

EFFECTIVE="$(mktemp)"
cleanup(){ rm -f "$EFFECTIVE"; }
trap cleanup EXIT

python3 - "$V4" "$EFFECTIVE" <<'PY'
from pathlib import Path
import sys

src = Path(sys.argv[1]).read_text()
dst = Path(sys.argv[2])

def once(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"ERROR: V5 transform anchor {label!r} count={n}, expected=1")
    src = src.replace(old, new, 1)

once(
'OUT="$ROOT/build_26498_v1_3_recovery_v4_outputs"\n'
'LOG="$OUT/26498_v1_3_recovery_v4_build.log"',
'OUT="$ROOT/build_26498_v1_3_recovery_v5_outputs"\n'
'LOG="$OUT/26498_v1_3_recovery_v5_build.log"',
"output directory"
)

old_build = r'''# Build in the SAME guarded script/command block. Record source-only hashes first so Gradle
# is also proven not to rewrite runtime source.
find app -type f \
  ! -path 'app/build/*' ! -path 'app/.cxx/*' ! -path 'app/.externalNativeBuild/*' \
  -print0 | sort -z | xargs -0 sha256sum > "$OUT/26498_v1_3_pre_gradle_source.sha256"
chmod +x ./gradlew
# Explicitly require the Android application module.  A root-level assembleDebug may
# otherwise report BUILD SUCCESSFUL after assembling only circularbarlib if the app
# module shell is ever missing or misconfigured.
./gradlew clean :app:assembleDebug --stacktrace
find app -type f \
  ! -path 'app/build/*' ! -path 'app/.cxx/*' ! -path 'app/.externalNativeBuild/*' \
  -print0 | sort -z | xargs -0 sha256sum > "$OUT/26498_v1_3_post_gradle_source.sha256"
diff -u "$OUT/26498_v1_3_pre_gradle_source.sha256" "$OUT/26498_v1_3_post_gradle_source.sha256" \
  > "$OUT/26498_v1_3_post_build_source_diff.txt" || fail "Gradle mutated runtime source"
echo "PASS: Gradle did not mutate runtime source"'''

new_build = r'''# Build in the SAME guarded script/command block.
# The exact candidate-owned runtime set is 865 files. Gradle is allowed to download
# only its four gitignored native dependency headers; every pre-existing app file
# remains hash-protected.
CAND_OWNED_COUNT="$(
  { find "$CAND/app/src/main" -type f -print; echo "$CAND/app/version.properties"; } | wc -l
)"
[[ "$CAND_OWNED_COUNT" -eq 865 ]] || fail "pre-Gradle candidate-owned file count=$CAND_OWNED_COUNT expected=865"
python3 "$ROOT/verify_26498_v1_3_recovery_v5_source_integrity.py" snapshot \
  "$ROOT/app" "$OUT/26498_v1_3_pre_gradle_app_manifest.json"
chmod +x ./gradlew
# Explicitly require the Android application module. A root-level assembleDebug may
# otherwise report BUILD SUCCESSFUL after assembling only circularbarlib.
./gradlew clean :app:assembleDebug --stacktrace
python3 "$ROOT/verify_26498_v1_3_recovery_v5_source_integrity.py" verify \
  "$ROOT/app" "$OUT/26498_v1_3_pre_gradle_app_manifest.json" \
  | tee "$OUT/26498_v1_3_post_gradle_integrity.txt"
echo "PASS: Gradle preserved all pre-existing app files; only expected ignored native deps were generated"'''

once(old_build, new_build, "Gradle integrity block")

old_archive = r'''# Emit exact successful SOURCE bundle/manifest (never Gradle/CMake generated outputs).
# Keep the established canonical-baseline contract: runtime source only, exactly
# app/src/main + app/version.properties.  Never archive module Gradle scaffolding as
# part of the canonical runtime-source baseline.
( cd "$ROOT" && \
  tar --sort=name --mtime='UTC 2026-08-17 00:00:00' --owner=0 --group=0 --numeric-owner \
      -czf "$OUT/26498_v1_3_successful_app_source.tar.gz" app/src/main app/version.properties )
( { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | \
  while read -r f; do sha256sum "$f"; done ) > "$OUT/26498_v1_3_successful_after.sha256"
[[ "$(wc -l < "$OUT/26498_v1_3_successful_after.sha256")" -eq 865 ]] || \
  fail "successful canonical runtime-source manifest must contain exactly 865 files"
( cd "$BASE" && git diff --no-index --binary -- app "$ROOT/app" || [[ $? -eq 1 ]] ) > "$OUT/26498_v1_3_complete_binary_delta_from_26494.patch"'''

new_archive = r'''# Emit exact successful SOURCE bundle/manifest from the preserved CLEAN candidate,
# never from the Gradle-augmented checkout. This guarantees generated cpp/deps headers
# cannot leak into the next canonical source baseline.
( cd "$CAND" && \
  tar --sort=name --mtime='UTC 2026-08-17 00:00:00' --owner=0 --group=0 --numeric-owner \
      -czf "$OUT/26498_v1_3_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$CAND" && \
  { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | \
  while read -r f; do sha256sum "$f"; done ) > "$OUT/26498_v1_3_successful_after.sha256"
[[ "$(wc -l < "$OUT/26498_v1_3_successful_after.sha256")" -eq 865 ]] || \
  fail "successful canonical runtime-source manifest must contain exactly 865 files"
for generated in archive.h archive_entry.h technicallyflac.h tiny_dng_writer.h; do
  ! tar -tzf "$OUT/26498_v1_3_successful_app_source.tar.gz" | \
    grep -qx "app/src/main/cpp/deps/$generated" || \
    fail "generated dependency leaked into successful source archive: $generated"
done
( cd "$BASE" && git diff --no-index --binary -- app "$CAND/app" || [[ $? -eq 1 ]] ) > "$OUT/26498_v1_3_complete_binary_delta_from_26494.patch"'''

once(old_archive, new_archive, "canonical archive block")
once(
'echo "PASS: 26498 V1.3 RECOVERY V4 BUILD COMPLETE: $FINAL"',
'echo "PASS: 26498 V1.3 RECOVERY V5 BUILD COMPLETE: $FINAL"',
"final marker"
)

for forbidden in [
    'rm -rf "$ROOT/app"',
    'build_26498_v1_3_recovery_v4_outputs',
    'Gradle mutated runtime source',
]:
    if forbidden in src:
        raise SystemExit(f"ERROR: forbidden V4 regression survived V5 transform: {forbidden}")

required = [
    'verify_26498_v1_3_recovery_v5_source_integrity.py" verify',
    'CAND_OWNED_COUNT',
    'expected=865',
    'cd "$CAND"',
    ':app:assembleDebug',
    'RECOVERY V5 BUILD COMPLETE',
]
for token in required:
    if token not in src:
        raise SystemExit(f"ERROR: V5 required token missing after transform: {token}")

dst.write_text(src)
PY

bash -n "$EFFECTIVE"
grep -q 'CAND_OWNED_COUNT' "$EFFECTIVE"
grep -q 'verify_26498_v1_3_recovery_v5_source_integrity.py" verify' "$EFFECTIVE"
grep -q 'cd "$CAND"' "$EFFECTIVE"
grep -q './gradlew clean :app:assembleDebug --stacktrace' "$EFFECTIVE"
! grep -q 'rm -rf "$ROOT/app"' "$EFFECTIVE"
! grep -q 'Gradle mutated runtime source' "$EFFECTIVE"

chmod +x "$EFFECTIVE"
"$EFFECTIVE"

cp "$EFFECTIVE" "$ROOT/build_26498_v1_3_recovery_v5_outputs/26498_v1_3_recovery_v5_effective.sh"
sha256sum "$ROOT/build_26498_v1_3_recovery_v5_outputs/26498_v1_3_recovery_v5_effective.sh" \
  > "$ROOT/build_26498_v1_3_recovery_v5_outputs/26498_v1_3_recovery_v5_effective.sh.sha256"
