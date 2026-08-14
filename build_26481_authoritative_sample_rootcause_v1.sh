#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

NEW_VERSION="0.9726481"
NEW_BUILD="26481"
APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
PATCH_26479="26479_successful_source.patch"
TRANSFORM_26480="transform_26480_bjzhou_short_highlight_v1.py"
TRANSFORM_26481="transform_26481_sample_rootcause_v1.py"
OUTDIR="$ROOT/26481_outputs"
BACKUP="backup-26480-success-before-26481-sample-rootcause"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

mkdir -p "$OUTDIR"
BRANCH="$(git branch --show-current)"
HEAD="$(git rev-parse HEAD)"

[[ "$BRANCH" != "dev" ]] || fail "dev is protected"
git diff --quiet -- app/src/main app/version.properties ||   fail "tracked app source dirty before 26481"

for f in "$PATCH_26479" "$TRANSFORM_26480" "$TRANSFORM_26481"; do
  [[ -f "$f" ]] || fail "missing $f"
done

[[ "$(sha256sum "$PATCH_26479" | awk '{print $1}')" ==   "996aac3986f658663d23b53d698f4657f0c01c65c3f725de3fc362fde88ab417" ]] ||   fail "26479 replay patch hash mismatch"
[[ "$(sha256sum "$TRANSFORM_26480" | awk '{print $1}')" ==   "62f4716e402a5525416ae869c378342465d9b78cc5d3bea3b516096e86cd03aa" ]] ||   fail "26480 transform hash mismatch"
[[ "$(sha256sum "$TRANSFORM_26481" | awk '{print $1}')" ==   "e912d743dbba989ca3f466436ecbe22a567b47a71ae8cb0b801cea5bd0916672" ]] || fail "26481 transform hash mismatch"

# Mandatory backup branch before live source modification.
if git show-ref --verify --quiet "refs/heads/$BACKUP"; then
  [[ "$(git rev-parse "$BACKUP")" == "$HEAD" ]] || \
    fail "backup branch exists at a different commit"
else
  git branch "$BACKUP" "$HEAD"
fi
pass "backup branch created: $BACKUP -> $HEAD"

# Persist only the required backup branch. Never dev; no source branch push.
if git remote get-url origin >/dev/null 2>&1; then
  git push origin "refs/heads/$BACKUP:refs/heads/$BACKUP" >/dev/null
  pass "backup branch pushed"
fi

TMP="$(mktemp -d)"
trap 'git worktree remove --force "$TMP/candidate" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
git worktree add --detach "$TMP/candidate" "$APP_BASE" >/dev/null

# Reconstruct exact 26480 in candidate only.
(
  cd "$TMP/candidate"
  git apply --binary "$ROOT/$PATCH_26479"
  python3 "$ROOT/$TRANSFORM_26480" .
  grep -q '^VERSION_NAME=0\.9726480$' app/version.properties
  grep -q '^VERSION_BUILD=26480$' app/version.properties
  grep -q 'IRIS_26480_ALIGNED_SHORT_SENSOR_HIGHLIGHT_RECOVERY_SHADER_V1' \
    app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl
  grep -q 'guide=max(luma,max3(rgb))' \
    app/src/main/assets/shaders/motionv2/render.glsl
)

# Exact 26480 pre-edit recovery patch.
(
  cd "$TMP/candidate"
  git diff --binary "$APP_BASE" -- app/src/main app/version.properties \
    > "$OUTDIR/26481_pre_edit_exact_26480_binary.patch"
)
[[ -s "$OUTDIR/26481_pre_edit_exact_26480_binary.patch" ]] || \
  fail "pre-edit binary patch empty"
pass "binary pre-edit patch created"

# Hash exact 26480 before 26481.
(
  cd "$TMP/candidate"
  find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum
  sha256sum app/version.properties
) > "$OUTDIR/26480_pre_26481.sha256"

# Apply 26481 to temp candidate first.
python3 "$ROOT/$TRANSFORM_26481" "$TMP/candidate"

(
  cd "$TMP/candidate"
  grep -q '^VERSION_NAME=0\.9726481$' app/version.properties
  grep -q '^VERSION_BUILD=26481$' app/version.properties
  grep -q 'IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP' \
    app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  grep -q 'IRIS_26481_BJZHOU_DOMAIN_CORRECT_HIGHLIGHT_COLOR' \
    app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
  grep -q 'IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR' \
    app/src/main/assets/shaders/motionv2/color_transform.glsl
  grep -q 'IRIS_26481_WRONSKI_TOTAL_TIMING' \
    app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java

  # Preserve 26480 max-RGB guide and Wronski core.
  grep -q 'guide=max(luma,max3(rgb))' app/src/main/assets/shaders/motionv2/render.glsl
  grep -q 'vec3 wbRgb=num/den;' app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl
  ! grep -q 'sampleValidity' app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
  grep -q 'float cfaSample=cfaAt(p);' \
    app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
)
echo "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"

python3 - "$OUTDIR/26480_pre_26481.sha256" "$TMP/candidate" <<'PY'
from pathlib import Path
import hashlib, sys
manifest=Path(sys.argv[1]).read_text().splitlines()
root=Path(sys.argv[2])
before={}
for line in manifest:
    if not line.strip(): continue
    h,p=line.split(None,1)
    before[p.strip()]=h
after={}
for p in sorted((root/"app/src/main").rglob("*")):
    if p.is_file():
        rel=str(p.relative_to(root))
        after[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
vp=root/"app/version.properties"
after["app/version.properties"]=hashlib.sha256(vp.read_bytes()).hexdigest()

changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
expected=sorted([
 "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java",
 "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java",
 "app/src/main/assets/shaders/motionv2/color_transform.glsl",
 "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
 "app/version.properties",
])
if changed != expected:
    raise SystemExit("26481 changed-file allowlist mismatch:\n" + "\n".join(changed))
print("26481 changed-file allowlist PASS")
print("protected-file hashes PASS")
PY

# Only now modify live source by reconstructing exact 26480 then copying the
# already-validated 26481 candidate files.
git checkout "$APP_BASE" -- app/src/main app/version.properties
git apply --binary "$PATCH_26479"
python3 "$TRANSFORM_26480" .

for rel in \
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java \
  app/src/main/assets/shaders/motionv2/color_transform.glsl \
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java \
  app/version.properties; do
  cp "$TMP/candidate/$rel" "$rel"
  cmp -s "$rel" "$TMP/candidate/$rel" || fail "candidate/live mismatch $rel"
done

git diff --check -- app/src/main app/version.properties

python3 - <<'PY'
from pathlib import Path
for p in [
 Path("app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"),
 Path("app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java"),
 Path("app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"),
]:
    s=p.read_text()
    if s.count("{") != s.count("}"):
        raise SystemExit(f"brace mismatch: {p}")
s=Path("app/src/main/assets/shaders/motionv2/color_transform.glsl").read_text()
if s.count("{") != s.count("}"):
    raise SystemExit("GLSL brace mismatch")
print("PRE-BUILD SAFETY PROOF PASSED")
PY

echo "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"

# Version bump and build are in this same command block.
[[ "$(grep '^VERSION_NAME=' app/version.properties)" == "VERSION_NAME=$NEW_VERSION" ]]
[[ "$(grep '^VERSION_BUILD=' app/version.properties)" == "VERSION_BUILD=$NEW_BUILD" ]]

./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUTDIR/build_26481.log"
grep -q 'BUILD SUCCESSFUL' "$OUTDIR/build_26481.log" || fail "BUILD SUCCESSFUL missing"

APK="$(find app/build/outputs/apk -type f -name '*.apk' -printf '%T@ %p\n' \
  | sort -nr | head -1 | cut -d' ' -f2-)"
[[ -n "$APK" && -f "$APK" ]] || fail "APK not found"

DEST="$ROOT/IrisCamera-0.9726481-26481-sample-rootcause-highlight-debug.apk"
cp "$APK" "$DEST"
sha256sum "$DEST" | tee "$OUTDIR/26481_apk.sha256"

cat > "$OUTDIR/26481_summary.txt" <<EOF
26481 SAMPLE ROOT-CAUSE BUILD
Version: 0.9726481 / 26481
Starting branch: $BRANCH
Starting HEAD: $HEAD
Backup branch: $BACKUP

- exact RAW/result timestamp ownership; no ~33-ms neighbor fallback
- short RAW/result tolerance 2 ms; 650-ms timeout unchanged
- bjzhou-informed calculation-domain clipping correction before Camera2 WB/matrix
- fully clipped RGB has no hue authority and is neutral-balanced
- partial repair requires two reliable balanced channels that agree
- no spatial hue donor; no broad desaturation
- 26480 max-RGB guide preserved
- Wronski equations preserved
- existing detailed timing preserved; total Wronski timing added
EOF

echo "26481 BUILD SUCCESS"
echo "APK: $DEST"
echo "No source commit was created and no source branch was pushed."
