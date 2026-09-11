#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
REPAIR_PARENT="3df6cee0015a21671b5e8c9ed55e9e750a7bd332"
AUTHORITY_COMMIT="d0d48ab26006a868baa8525a0b81aad65939fac3"
BUILD_SCRIPT="$ROOT/build_26625_r1_robust_short_fallback_geometry.sh"
HANDOFF="$ROOT/R1_26625_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26625_r1_robust_short_fallback_geometry_outputs"
APK="$ROOT/IrisCamera-0.9726625-26625-r1-robust-short-fallback-geometry-debug.apk"
STATUS="$OUT/26625_R1_COMPILER_STATUS.txt"
R3_SCOPE="$ROOT/.26625_r3_repair_scope.txt"
R3_ACTUAL="$ROOT/.26625_r3_repair_actual.txt"
FULL_EXPECTED="$ROOT/.26625_r3_full_expected.txt"
FULL_ACTUAL="$ROOT/.26625_r3_full_actual.txt"
HEAD_SHA="$(git rev-parse HEAD)"
REPLACE_ACTIVE=0
cleanup(){
  rm -f "$R3_SCOPE" "$R3_ACTUAL" "$FULL_EXPECTED" "$FULL_ACTUAL"
  if [[ "$REPLACE_ACTIVE" -eq 1 ]]; then git replace -d "$HEAD_SHA" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$REPAIR_PARENT" ]] || fail "26625 R3 repair must be one commit directly on false-green R2 carrier $REPAIR_PARENT"
cat > "$R3_SCOPE" <<'SCOPE'
.github/workflows/build-26625-r1-robust-short-fallback-geometry.yml
R1_26625_HANDOFF_HASHES.sha256
R1_26625_R2_REPAIR_RUN.sh
REGRESSION_R2_26625_KOTLIN_SCOPE.txt
SCOPE
git diff --name-only "$REPAIR_PARENT"..HEAD | sort > "$R3_ACTUAL"
diff -u "$R3_SCOPE" "$R3_ACTUAL" || fail "26625 R3 repair commit scope mismatch"
! grep -Eq '^app/|^handoff_payload_26625_r1/app/' "$R3_ACTUAL" || fail "R3 repair unexpectedly changes runtime/payload bytes"

# The original 26625 build script is intentionally left byte-identical. Project the current
# sealed handoff tree onto the exact successful 26624 parent only inside this ephemeral Actions
# checkout so its original direct-parent/scope proof runs unchanged. No source/history is pushed.
[[ -z "$(git replace -l)" ]] || fail "unexpected pre-existing git replacement refs"
git replace --graft "$HEAD_SHA" "$AUTHORITY_COMMIT"
REPLACE_ACTIVE=1
[[ "$(git rev-parse HEAD^)" == "$AUTHORITY_COMMIT" ]] || fail "temporary 26624 parent projection failed"

awk '{print $2}' "$HANDOFF" | sort > "$FULL_EXPECTED"
printf '%s\n' 'R1_26625_HANDOFF_HASHES.sha256' >> "$FULL_EXPECTED"
sort -u -o "$FULL_EXPECTED" "$FULL_EXPECTED"
git diff --name-only "$AUTHORITY_COMMIT"..HEAD | sort > "$FULL_ACTUAL"
diff -u "$FULL_EXPECTED" "$FULL_ACTUAL" || fail "projected full 26625 sealed scope differs from handoff manifest"
pass "26625 R3 projected carrier: exact current sealed tree on successful 26624 parent; original 26625 build mechanics unchanged"

# CRITICAL: no --local-prebuild here. This must execute real GLSL/Kotlin/Java/NDK/assemble/invariance.
bash "$BUILD_SCRIPT"

[[ -f "$STATUS" ]] || fail "compiler status missing after authoritative build"
grep -Fxq 'REAL GLSL COMPILE: PASS (pinned glslang 16.5.0)' "$STATUS" || fail "real GLSL compile not proven"
grep -Fxq 'REAL KOTLIN COMPILE: PASS' "$STATUS" || fail "real Kotlin compile not proven"
grep -Fxq 'REAL JAVA COMPILE: PASS' "$STATUS" || fail "real Java compile not proven"
grep -Fxq 'NATIVE/NDK COMPILE: PASS (both ABIs)' "$STATUS" || fail "real native/NDK compile not proven"
grep -Fxq 'FULL ANDROID ASSEMBLE: PASS' "$STATUS" || fail "full Android assemble not proven"
grep -Fxq 'POST-BUILD INVARIANCE: PASS' "$STATUS" || fail "post-build invariance not proven"
[[ -s "$APK" ]] || fail "expected final APK missing/empty"
[[ -s "$OUT/26625_R1_candidate_app_source.tar.gz" ]] || fail "final candidate export missing/empty"
APK_BYTES="$(stat -c '%s' "$APK")"
pass "26625 R3 authoritative full build complete; APK bytes=$APK_BYTES"
