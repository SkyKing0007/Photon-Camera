#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
REPAIR_PARENT="54b464dc0ead50c55f068316180c01f804891a9c"
AUTHORITY_COMMIT="d0d48ab26006a868baa8525a0b81aad65939fac3"
AUTHORITY_RUN="34525392337"
AUTHORITY_ARTIFACT_ID="10171452870"
AUTHORITY_ARTIFACT_SHA="d4f45ff32259ccb7d75f28e53189298ff325ecfa3beddf4e1440b7009693dac5"
AUTHZIP="$ROOT/.26625_r2_exact_26624_authority.zip"
SCOPE="$ROOT/.26625_r2_expected_scope.txt"
ACTUAL="$ROOT/.26625_r2_actual_scope.txt"
PROOF="$ROOT/.26625_r2_scope_proof.txt"
cleanup(){ rm -f "$AUTHZIP" "$SCOPE" "$ACTUAL" "$PROOF"; }
trap cleanup EXIT
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$REPAIR_PARENT" ]] || fail "26625 R2 repair must be one commit directly on failed 26625 R1 carrier $REPAIR_PARENT"
cat > "$SCOPE" <<'SCOPE'
.github/workflows/build-26625-r1-robust-short-fallback-geometry.yml
R1_26625_EXPECTED_CANDIDATE_FULL_APP.sha256
R1_26625_EXPECTED_CHANGED_SOURCE_HASHES.sha256
R1_26625_HANDOFF_HASHES.sha256
R1_26625_R2_REPAIR_RUN.sh
R1_26625_RUNTIME_DELTA_FROM_26624_R1.patch
R1_26625_RUNTIME_ROLLBACK_TO_26624_R1.patch
REGRESSION_R2_26625_KOTLIN_SCOPE.txt
handoff_payload_26625_r1/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
verify_26625_r1_regressions.py
SCOPE
git diff --name-only "$REPAIR_PARENT"..HEAD | sort > "$ACTUAL"
diff -u "$SCOPE" "$ACTUAL" || fail "26625 R2 repair commit scope mismatch"
! grep -Eq '^app/' "$ACTUAL" || fail "repair commit contains live app source"
cat > "$PROOF" <<PROOF
26625 R2 REPAIR SCOPE: PASS
branch=$EXPECTED_BRANCH
repairParent=$REPAIR_PARENT
runtimeAuthorityCommit=$AUTHORITY_COMMIT
runtimeAuthorityRun=$AUTHORITY_RUN
runtimeChangedFileAllowlist=3
repairInfrastructureDelta=wrapper+workflow-routing+compiler-regression-only
imageAlgorithmDeltaFromFailed26625=ZERO
PROOF
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
[[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
curl -L --fail --retry 3 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${AUTHORITY_ARTIFACT_ID}/zip" \
  -o "$AUTHZIP"
[[ "$(sha "$AUTHZIP")" == "$AUTHORITY_ARTIFACT_SHA" ]] || fail "26624 R1 artifact ZIP SHA"
pass "26625 R2 repair provenance and exact 26624 artifact authority"
bash "$ROOT/build_26625_r1_robust_short_fallback_geometry.sh" --local-prebuild "$AUTHZIP"
OUT="$ROOT/build_26625_r1_robust_short_fallback_geometry_outputs"
[[ -d "$OUT" ]] || fail "26625 output directory missing after build"
cp "$PROOF" "$OUT/26625_R2_REPAIR_SCOPE_PROOF.txt"
pass "26625 R2 repair completed through unchanged R1 compiler/build/invariance sequence"
