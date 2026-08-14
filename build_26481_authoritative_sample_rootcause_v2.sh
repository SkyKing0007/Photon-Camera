#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
SUCCESS_26479="028c77b6970801d2d360d45917f811286b6aaa39"
BACKUP="backup-26480-success-before-26481-sample-rootcause"

PATCH_26479="26479_successful_source.patch"
PATCH_26479_SHA="996aac3986f658663d23b53d698f4657f0c01c65c3f725de3fc362fde88ab417"
HASHES_26479="26479_successful_after.sha256"
HASHES_26479_SHA="900729d32ddc3d621bd51f21ff6afde74d0e34a5531d9593a2c6bc8ecaa193e7"
TRANSFORM_26480="transform_26480_bjzhou_short_highlight_v1.py"
TRANSFORM_26480_SHA="62f4716e402a5525416ae869c378342465d9b78cc5d3bea3b516096e86cd03aa"
TRANSFORM_26481="transform_26481_sample_rootcause_v1.py"
TRANSFORM_26481_SHA="e912d743dbba989ca3f466436ecbe22a567b47a71ae8cb0b801cea5bd0916672"

NEW_VERSION="0.9726481"
NEW_BUILD="26481"
OUTDIR="$ROOT/26481_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-sample-rootcause-highlight-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26481_source_audit.txt"
REPORT="$OUTDIR/26481_build_report.txt"
PREPATCH="$OUTDIR/26481_pre_edit_exact_26480_binary.patch"
PREHASH="$OUTDIR/26480_pre_26481.sha256"
AFTERHASH="$OUTDIR/26481_after.sha256"
CHANGED="$OUTDIR/26481_changed_files.txt"
SOURCEPATCH="$OUTDIR/26481_source.patch"

exec > >(tee "$AUDIT") 2>&1

echo "=== 26481 AUTHORITATIVE SAMPLE ROOT-CAUSE BUILD V2 ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "dev is protected"

# Infrastructure commits may exist after 26480, but committed app source must remain the
# verified clean base because source changes are generated only inside this guarded build.
git cat-file -e "$APP_BASE^{commit}" || fail "verified app base unavailable"
git diff --quiet "$APP_BASE" -- app/src/main app/version.properties || \
  fail "committed app source differs from verified clean base before guarded replay"
pass "experimental branch + untouched committed app source gate"

# Mandatory pre-change backup already exists from the user's vscode.dev flow.
# Verify it; never overwrite or move it from the Action.
git fetch --no-tags origin \
  "refs/heads/$BACKUP:refs/remotes/origin/$BACKUP" >/dev/null 2>&1 || \
  fail "required backup branch missing: $BACKUP"
git diff --quiet "$APP_BASE" "refs/remotes/origin/$BACKUP" -- \
  app/src/main app/version.properties || \
  fail "backup branch app source is not the verified clean pre-26481 state"
pass "required pre-26481 backup branch verified without moving it"

for f in "$PATCH_26479" "$HASHES_26479" "$TRANSFORM_26480" "$TRANSFORM_26481"; do
  [[ -f "$f" ]] || fail "missing authoritative input $f"
done

[[ "$(sha256sum "$PATCH_26479" | awk '{print $1}')" == "$PATCH_26479_SHA" ]] || \
  fail "26479 replay patch hash mismatch"
[[ "$(sha256sum "$HASHES_26479" | awk '{print $1}')" == "$HASHES_26479_SHA" ]] || \
  fail "26479 replay hash-manifest mismatch"
[[ "$(sha256sum "$TRANSFORM_26480" | awk '{print $1}')" == "$TRANSFORM_26480_SHA" ]] || \
  fail "26480 transform hash mismatch"
[[ "$(sha256sum "$TRANSFORM_26481" | awk '{print $1}')" == "$TRANSFORM_26481_SHA" ]] || \
  fail "26481 transform hash mismatch"

python3 -m py_compile "$TRANSFORM_26480"
python3 -m py_compile "$TRANSFORM_26481"
pass "authoritative replay inputs + transform syntax/integrity PASS"

TMP="$(mktemp -d)"
trap 'git worktree remove --force "$TMP/candidate" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
CAND="$TMP/candidate"
PRE26481="$TMP/exact26480"
git worktree add --detach "$CAND" "$APP_BASE" >/dev/null

# ----------------------------------------------------------------------
# Exact successful 26479 reconstruction.
# ----------------------------------------------------------------------
(
  cd "$CAND"
  git apply --check "$ROOT/$PATCH_26479" || exit 31
  git apply "$ROOT/$PATCH_26479"
  sha256sum -c "$ROOT/$HASHES_26479" >/dev/null
  grep -q '^VERSION_NAME=0\.9726479$' app/version.properties
  grep -q '^VERSION_BUILD=26479$' app/version.properties
  grep -q 'IRIS_26478_WRONSKI_PURE_DIVIDE_ONCE_FINALIZER' \
    app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl
  grep -q 'IRIS_26479_ADRENO_GLSL_SAMPLE_KEYWORD_PORTABILITY' \
    app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
) || fail "exact successful 26479 reconstruction failed"
pass "exact successful 26479 V10 source reproduced"

# ----------------------------------------------------------------------
# Exact authoritative 26480 transform in temporary source first.
# ----------------------------------------------------------------------
python3 "$ROOT/$TRANSFORM_26480" "$CAND"

(
  cd "$CAND"
  grep -q '^VERSION_NAME=0\.9726480$' app/version.properties
  grep -q '^VERSION_BUILD=26480$' app/version.properties
  grep -q 'IRIS_26480_ALIGNED_SHORT_SENSOR_HIGHLIGHT_RECOVERY_SHADER_V1' \
    app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl
  grep -q 'normalRingPreserved=true' \
    app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  grep -q 'guide=max(luma,max3(rgb))' \
    app/src/main/assets/shaders/motionv2/render.glsl
  grep -q 'vec3 wbRgb=num/den;' \
    app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl
  ! grep -q 'sampleValidity' \
    app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
) || fail "exact authoritative 26480 reconstruction failed"
pass "exact successful 26480 source reconstructed in temporary worktree"

# Save exact 26480 state before any 26481 source modification.
mkdir -p "$PRE26481"
cp -a "$CAND/app" "$PRE26481/app"

(
  cd "$CAND"
  git diff --binary "$APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
  find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$PREHASH"
  sha256sum app/version.properties >> "$PREHASH"
)
[[ -s "$PREPATCH" ]] || fail "26481 pre-edit exact-26480 patch is empty"
pass "TRUE exact-26480 pre-edit binary patch created before 26481 modification"

# ----------------------------------------------------------------------
# Generate and validate 26481 ONLY in temporary candidate.
# ----------------------------------------------------------------------
python3 "$ROOT/$TRANSFORM_26481" "$CAND"

(
  cd "$CAND"
  grep -q '^VERSION_NAME=0\.9726481$' app/version.properties
  grep -q '^VERSION_BUILD=26481$' app/version.properties
  grep -q 'IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP' \
    app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  grep -q 'MOTION_26481_TIMESTAMP_MATCH_TOLERANCE_NS = 2_000_000L' \
    app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  ! grep -q '40_000_000L' \
    app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java

  grep -q 'IRIS_26481_BJZHOU_DOMAIN_CORRECT_HIGHLIGHT_COLOR' \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
  grep -q 'IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR' \
    app/src/main/assets/shaders/motionv2/color_transform.glsl
  grep -q 'partialRepairGate' \
    app/src/main/assets/shaders/motionv2/color_transform.glsl
  grep -q 'allChannelsNearClip' \
    app/src/main/assets/shaders/motionv2/color_transform.glsl
  ! grep -q 'neighborhoodRisk' \
    app/src/main/assets/shaders/motionv2/color_transform.glsl

  grep -q 'IRIS_26481_WRONSKI_TOTAL_TIMING' \
    app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java

  # Proven 26480/26479 behavior must survive.
  grep -q 'guide=max(luma,max3(rgb))' \
    app/src/main/assets/shaders/motionv2/render.glsl
  grep -q 'vec3 wbRgb=num/den;' \
    app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl
  ! grep -q 'sampleValidity' \
    app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
  grep -q 'float cfaSample=cfaAt(p);' \
    app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
  grep -q 'normalRingPreserved=true' \
    app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
)
pass "candidate/source validation PASS"

# Exact five-file allowlist relative to reconstructed 26480.
(
  cd "$CAND"
  find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$AFTERHASH"
  sha256sum app/version.properties >> "$AFTERHASH"
)
python3 - "$PREHASH" "$AFTERHASH" "$CHANGED" <<'PY'
from pathlib import Path
import sys

def load(path):
    out={}
    for line in Path(path).read_text().splitlines():
        if not line.strip(): continue
        h,p=line.split(None,1)
        out[p.strip()]=h
    return out

a=load(sys.argv[1]); b=load(sys.argv[2])
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
Path(sys.argv[3]).write_text("\n".join(changed)+"\n")
expected=sorted([
 "app/src/main/assets/shaders/motionv2/color_transform.glsl",
 "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java",
 "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java",
 "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
 "app/version.properties",
])
if changed != expected:
    raise SystemExit("26481 changed-file allowlist mismatch:\n"+"\n".join(changed))
print("26481 exact changed-file allowlist PASS")
PY

# Scoped whitespace check: only the NEW 26481 deltas are judged.
for rel in \
  app/src/main/assets/shaders/motionv2/color_transform.glsl \
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java \
  app/version.properties; do
  git diff --no-index --check \
    "$PRE26481/$rel" "$CAND/$rel" >/dev/null || \
    fail "26481 scoped whitespace validation failed: $rel"
done
pass "26481 scoped whitespace validation PASS"

# Static Java/GLSL structure guards that are reproducible before Gradle.
python3 - "$CAND" <<'PY'
from pathlib import Path
import sys
r=Path(sys.argv[1])
java=[
 r/"app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java",
 r/"app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java",
 r/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
]
for p in java:
    s=p.read_text()
    if s.count("{") != s.count("}"):
        raise SystemExit(f"brace mismatch: {p}")
    if "\t" in s:
        raise SystemExit(f"tab introduced in guarded source: {p}")
shader=(r/"app/src/main/assets/shaders/motionv2/color_transform.glsl").read_text()
if shader.count("{") != shader.count("}"):
    raise SystemExit("GLSL brace mismatch")
if "readonly image2D tex" in shader:
    raise SystemExit("known Adreno-risk image2D function parameter introduced")
if "layout(" in shader and "image2D" in shader:
    raise SystemExit("26481 color shader unexpectedly introduced image load/store")
print("26481 Java/GLSL static structure PASS")
PY

echo "Temporary-copy validation: PASS"

# ----------------------------------------------------------------------
# Only after temporary-copy PASS, apply the already-validated candidate to live
# source. No app source commit or push is performed.
# ----------------------------------------------------------------------
git checkout "$APP_BASE" -- app/src/main app/version.properties
git apply "$PATCH_26479"
sha256sum -c "$HASHES_26479" >/dev/null || fail "live 26479 replay hash mismatch"
python3 "$TRANSFORM_26480" .

while IFS= read -r rel; do
  [[ -n "$rel" ]] || continue
  mkdir -p "$(dirname "$rel")"
  cp "$CAND/$rel" "$rel"
  cmp -s "$rel" "$CAND/$rel" || fail "candidate/live mismatch: $rel"
done < "$CHANGED"

# Re-prove every non-allowlisted app file stayed byte-identical to exact 26480.
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$OUTDIR/26481_live.sha256"
sha256sum app/version.properties >> "$OUTDIR/26481_live.sha256"
cmp -s "$AFTERHASH" "$OUTDIR/26481_live.sha256" || \
  fail "live source does not exactly equal validated 26481 candidate"
pass "protected-file hashes + candidate/live equivalence PASS"

# Final hard source invariants before Gradle.
grep -q '^VERSION_NAME=0\.9726481$' app/version.properties || fail "wrong version"
grep -q '^VERSION_BUILD=26481$' app/version.properties || fail "wrong build"
grep -q 'IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP' \
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java || fail "timestamp fix missing"
grep -q 'IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR' \
  app/src/main/assets/shaders/motionv2/color_transform.glsl || fail "highlight domain fix missing"
grep -q 'guide=max(luma,max3(rgb))' \
  app/src/main/assets/shaders/motionv2/render.glsl || fail "26480 max-RGB guide lost"
grep -q 'vec3 wbRgb=num/den;' \
  app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl || fail "Wronski divide-once finalizer changed"
! grep -q 'sampleValidity' \
  app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl || fail "old sampleValidity reintroduced"

git diff --binary "$APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"
[[ -s "$SOURCEPATCH" ]] || fail "26481 source patch empty"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"

# Build/version are deliberately part of this same guarded command script.
rm -f ./*.apk
./gradlew assembleDebug --no-daemon 2>&1 | tee "$OUTDIR/build_26481.log"
grep -q 'BUILD SUCCESSFUL' "$OUTDIR/build_26481.log" || fail "literal BUILD SUCCESSFUL missing"

mapfile -t APKS < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || {
  printf 'Found APKs:\n'; printf '%s\n' "${APKS[@]:-none}"
  fail "expected exactly one APK"
}
cp "${APKS[0]}" "$APK_NAME"
APK_SHA="$(sha256sum "$APK_NAME" | awk '{print $1}')"

cat > "$REPORT" <<EOF
26481 AUTHORITATIVE SAMPLE ROOT-CAUSE V2
Version=$NEW_VERSION
Build=$NEW_BUILD
Branch=$EXPECTED_BRANCH
AppBase=$APP_BASE
Successful26479=$SUCCESS_26479
Backup=$BACKUP
ReplayPatchSHA256=$PATCH_26479_SHA
ReplayHashesSHA256=$HASHES_26479_SHA
Transform26480SHA256=$TRANSFORM_26480_SHA
Transform26481SHA256=$TRANSFORM_26481_SHA
APK=$APK_NAME
APK_SHA256=$APK_SHA

ExactTimestampMetadataOwnership=true
ShortTimestampToleranceNs=2000000
ShortWaitMsUnchanged=650
BjzhouCalculationDomainPrinciple=true
FullClipHueAuthority=false
PartialRepairRequiresReliablePair=true
MaxRgbToneGuidePreserved=true
NormalWronskiEquationsChanged=false
ZslRingPreserved=true
EOF

echo "APK=$APK_NAME"
echo "SHA256=$APK_SHA"
echo "26481 BUILD SUCCESS"
echo "No app source commit was created and no app source branch was pushed."
