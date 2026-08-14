#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
SUCCESSFUL_26480_HEAD="20289467277241039413bb9f0daf5fc9ae855fd8"
BACKUP_BRANCH="backup-26480-successful-before-26481-direct-v1"
BASE_PATCH="26480_successful_source.patch"
BASE_PATCH_SHA="e9f2b9987a84075160f2e6aad62a9983d5b9920b065b77febc83e705aa859975"
BASE_HASHES="26480_successful_after.sha256"
BASE_HASHES_SHA="b34a13173d3ddd37d5b3ef94241fb3e4d068766e9e7893396b76a097f2b06ebb"
# The successful 26480 build report is provenance only. It is intentionally
# NOT a runtime dependency. Exact source authority is the source patch plus
# the complete 822-file SHA-256 manifest from the successful GitHub artifact.
TRANSFORM="transform_26481_direct_26480_rootcause_v1.py"
TRANSFORM_SHA="fb9cc02f8a8af64c531a383055d3a2b254a4517fb78fdbfcc68089ede54ac560"
NEW_VERSION="0.9726481"
NEW_BUILD="26481"
OUTDIR="build_26481_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-direct-26480-rootcause-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

REPO="$(pwd)"
rm -rf "$OUTDIR"; mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26481_source_audit.txt"
CANDLOG="$OUTDIR/26481_temporary_candidate_build.log"
FINALLOG="$OUTDIR/26481_final_build.log"
SHADERLOG="$OUTDIR/26481_shader_validation.txt"
REPORT="$OUTDIR/26481_build_report.txt"
PREPATCH="$OUTDIR/26481_pre_edit_exact_26480_binary.patch"
DELTAPATCH="$OUTDIR/26481_source.patch"
AFTERHASH="$OUTDIR/26481_after.sha256"
exec > >(tee "$AUDIT") 2>&1

echo "=== 26481 DIRECT FROM SUCCESSFUL GITHUB 26480 ARTIFACT ==="
date -Iseconds || true

# GATE 0 — package identity. No historical replay is allowed.
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" != "dev" ]] || fail "dev is protected"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $BRANCH"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "verified app-base commit unavailable"
git cat-file -e "$SUCCESSFUL_26480_HEAD^{commit}" || fail "successful 26480 infrastructure HEAD unavailable"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || \
  fail "committed app source is not the unchanged verified base; refuse to overwrite"
[[ -f "$BASE_PATCH" && "$(sha "$BASE_PATCH")" == "$BASE_PATCH_SHA" ]] || fail "successful 26480 source patch identity mismatch"
[[ -f "$BASE_HASHES" && "$(sha "$BASE_HASHES")" == "$BASE_HASHES_SHA" ]] || fail "successful 26480 hash manifest identity mismatch"
[[ -f "$TRANSFORM" && "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] || fail "26481 transform identity mismatch"
python3 -m py_compile "$TRANSFORM" || fail "26481 transform Python syntax"
bash -n "$0" || fail "26481 build script syntax"
[[ "$BASE_PATCH" == "26480_successful_source.patch" ]] || fail "direct baseline patch name changed"
[[ "$BASE_HASHES" == "26480_successful_after.sha256" ]] || fail "direct baseline manifest name changed"
pass "successful-26480 direct-baseline package identity"

# GATE 1 — backup exact known-good 26480 infrastructure state before modification.
remote="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
if [[ -n "$remote" ]]; then
  [[ "$remote" == "$SUCCESSFUL_26480_HEAD" ]] || fail "existing 26480 backup branch points to wrong SHA: $remote"
else
  git push origin "$SUCCESSFUL_26480_HEAD:refs/heads/$BACKUP_BRANCH"
fi
[[ "$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')" == "$SUCCESSFUL_26480_HEAD" ]] || fail "backup verification"
pass "backup branch exact successful 26480 GitHub checkpoint"

TMP="$(mktemp -d)"
BASE="$TMP/exact-successful-26480"
CAND="$TMP/candidate-26481"
PRETREE="$TMP/pre26481"
cleanup(){ set +e; git worktree remove --force "$BASE" >/dev/null 2>&1 || true; git worktree remove --force "$CAND" >/dev/null 2>&1 || true; rm -rf "$TMP"; }
trap cleanup EXIT

reconstruct_26480(){
  local dst="$1"
  git worktree add --detach "$dst" "$EXPECTED_APP_BASE" >/dev/null || fail "create clean base worktree"
  ( cd "$dst" && git apply --check --binary "$REPO/$BASE_PATCH" ) || fail "successful 26480 patch does not apply cleanly to verified app base"
  ( cd "$dst" && git apply --binary "$REPO/$BASE_PATCH" ) || fail "successful 26480 patch apply"
  ( cd "$dst" && sha256sum -c "$REPO/$BASE_HASHES" ) || fail "successful 26480 full manifest verification"
  grep -q '^VERSION_NAME=0\.9726480$' "$dst/app/version.properties" || fail "reconstructed baseline version is not 26480"
  grep -q '^VERSION_BUILD=26480$' "$dst/app/version.properties" || fail "reconstructed baseline build is not 26480"
  [[ -f "$dst/app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl" ]] || fail "successful 26480 baseline missing generated Wronski shader"
  [[ -f "$dst/app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl" ]] || fail "successful 26480 baseline missing short-highlight shader"
}

# GATE 2 — exact successful 26480 is reconstructed directly from its artifact.
reconstruct_26480 "$BASE"
pass "baseline source PASS — exact successful 26480 artifact reconstructed"
mkdir -p "$PRETREE/app/src" "$PRETREE/app"
cp -a "$BASE/app/src/main" "$PRETREE/app/src/main"
cp "$BASE/app/version.properties" "$PRETREE/app/version.properties"
( cd "$BASE" && git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties ) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "26481 pre-edit exact-26480 patch is empty"
pass "binary pre-edit patch created before 26481 modification"

# Build a second immutable candidate from the SAME successful 26480 artifact.
reconstruct_26480 "$CAND"
python3 "$REPO/$TRANSFORM" "$CAND" || fail "26481 transform dry-run/application"
pass "transform dry-run PASS"

cat > "$TMP/allowed-functional.txt" <<'EOF'
app/src/main/assets/shaders/motionv2/color_transform.glsl
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
EOF
python3 - "$PRETREE" "$CAND" "$TMP/allowed-functional.txt" <<'PY'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
def h(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): out[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 v=root/'app/version.properties'; out['app/version.properties']=hashlib.sha256(v.read_bytes()).hexdigest()
 return out
a,b=h(A),h(B); changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed != allowed: raise SystemExit('changed-file allowlist mismatch\nactual='+repr(sorted(changed))+'\nexpected='+repr(sorted(allowed)))
print('changed-file allowlist PASS')
PY
pass "candidate changed-file allowlist PASS"

# All non-allowed app files must still equal the successful 26480 manifest.
python3 - "$REPO/$BASE_HASHES" "$CAND" "$TMP/allowed-functional.txt" <<'PY'
from pathlib import Path
import hashlib,sys
manifest=Path(sys.argv[1]); root=Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
for line in manifest.read_text().splitlines():
 if not line.strip(): continue
 expected,path=line.split(None,1); path=path.strip()
 if path in allowed: continue
 p=root/path
 if not p.is_file(): raise SystemExit('protected file missing: '+path)
 actual=hashlib.sha256(p.read_bytes()).hexdigest()
 if actual!=expected: raise SystemExit('protected hash changed: '+path)
print('protected successful-26480 hashes PASS')
PY

# Structural/ownership gates.
CAP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
CJ="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java"
CG="$CAND/app/src/main/assets/shaders/motionv2/color_transform.glsl"
grep -q 'IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP' "$CAP" || fail "exact metadata ownership marker"
grep -q 'MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS = 2_000_000L' "$CAP" || fail "2ms short timestamp tolerance"
[[ "$(grep -o 'MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS' "$CAP" | wc -l)" -eq 3 ]] || fail "2ms timestamp producer/consumer count"
! grep -q '40_000_000L' "$CAP" || fail "stale 40ms timestamp association remains"
grep -q 'MOTION_26480_SHORT_WAIT_MS = 300L' "$CAP" || fail "26480 short wait policy changed"
grep -q 'IRIS_26480_SHORT_CAPTURE_SUBMITTED' "$CAP" || fail "26480 explicit short capture lost"
grep -q 'IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR' "$CG" || fail "26481 highlight-domain repair missing"
grep -q 'repairedCameraRgb=repairedBalanced/gains;' "$CG" || fail "calculation-only WB is not removed before normal WB"
grep -q 'IRIS_26481_BJZHOU_DOMAIN_CORRECT_HIGHLIGHT_COLOR' "$CJ" || fail "color telemetry marker missing"
grep -q 'glProg.setVar("sensorClipLevel", sensorClipLevel);' "$CJ" || fail "sensor clip binding lost"
! grep -q 'neighborhoodRisk\|chromaCompression' "$CG" || fail "broad/spatial chroma repair reintroduced"
# Existing 26480 max-RGB render guide must remain byte protected.
grep -q 'IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V2' "$CAND/app/src/main/assets/shaders/motionv2/render.glsl" || fail "26480 max-RGB tone guide lost"
# Wronski and denoise/sharpening invariants remain.
grep -q 'vec3 wbRgb=num/den;' "$CAND/app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl" || fail "Wronski divide-once finalizer changed"
! grep -q 'add(new MotionV2Denoise());' "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java" || fail "MotionV2Denoise re-enabled"
pass "source structural/ownership PASS"

# Runtime shader smoke validation. First lexical/brace checks, then glslang when installed.
python3 - "$CG" > "$SHADERLOG" <<'PY'
from pathlib import Path
import sys,re
p=Path(sys.argv[1]); t=p.read_text()
if t.count('{')!=t.count('}'): raise SystemExit('shader brace mismatch')
for bad in ['readonly image2D tex','\x00']:
 if bad in t: raise SystemExit('forbidden shader construct: '+bad)
if not re.search(r'void\s+main\s*\(',t): raise SystemExit('shader main missing')
print('26481 color shader lexical/structure PASS')
PY
if command -v glslangValidator >/dev/null 2>&1; then
  { echo '#version 300 es'; cat "$CG"; } > "$TMP/26481_color.frag"
  glslangValidator -S frag "$TMP/26481_color.frag" >> "$SHADERLOG" 2>&1 || { cat "$SHADERLOG"; fail "glslang color shader compilation"; }
  echo "glslang color shader compilation PASS" >> "$SHADERLOG"
else
  fail "glslangValidator unavailable; workflow must install glslang-tools"
fi
cat "$SHADERLOG"
pass "shader asset/reference PASS"

# CRITICAL SOP STEP: compile the FULL transformed candidate BEFORE live source is touched.
(
  cd "$CAND"
  chmod +x ./gradlew
  ./gradlew clean assembleDebug --no-daemon
) 2>&1 | tee "$CANDLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "full temporary candidate Gradle build"
grep -q 'BUILD SUCCESSFUL' "$CANDLOG" || fail "temporary candidate did not report BUILD SUCCESSFUL"
pass "Gradle compile PASS — full temporary candidate"

# CMake intentionally downloads these build-time native headers into app/src/main/cpp/deps.
# They are NOT canonical successful-26480 source: they are absent from the 822-file
# manifest and absent from the direct 26480 source patch. Treat them as generated
# build inputs, never as 26481 source changes. Candidate and final builds must use
# byte-identical generated copies within this run.
cat > "$TMP/generated-native-deps.txt" <<'EOF'
app/src/main/cpp/deps/archive.h
app/src/main/cpp/deps/archive_entry.h
app/src/main/cpp/deps/technicallyflac.h
app/src/main/cpp/deps/tiny_dng_writer.h
EOF

while IFS= read -r rel; do
  ! grep -Fq "  $rel" "$BASE_HASHES" || fail "generated native dep unexpectedly entered canonical 26480 manifest: $rel"
  [[ ! -e "$PRETREE/$rel" ]] || fail "generated native dep unexpectedly exists in canonical 26480 tree: $rel"
  [[ -f "$CAND/$rel" ]] || fail "candidate Gradle build did not materialize expected native dep: $rel"
done < "$TMP/generated-native-deps.txt"

python3 - "$REPO/$BASE_HASHES" "$CAND" "$TMP/allowed-functional.txt" <<'PY'
from pathlib import Path
import hashlib,sys
manifest=Path(sys.argv[1]); root=Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
for line in manifest.read_text().splitlines():
    if not line.strip():
        continue
    expected,path=line.split(None,1); path=path.strip()
    if path in allowed:
        continue
    p=root/path
    if not p.is_file():
        raise SystemExit('post-candidate protected canonical file missing: '+path)
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit('post-candidate protected canonical hash changed: '+path)
print('post-candidate canonical source hashes PASS')
PY

while IFS= read -r rel; do
  sha256sum "$CAND/$rel"
done < "$TMP/generated-native-deps.txt" > "$OUTDIR/26481_candidate_generated_native_deps.sha256"
pass "candidate generated native dependency identity captured"
pass "Temporary-copy validation: PASS"

# Only now may the ephemeral live Actions workspace be reconstructed from exact 26480.
git apply --check --binary "$BASE_PATCH" || fail "live successful-26480 baseline apply check"
git apply --binary "$BASE_PATCH" || fail "live successful-26480 baseline apply"
sha256sum -c "$BASE_HASHES" || fail "live successful-26480 baseline manifest"
pass "live exact successful 26480 baseline PASS"

# Copy only the already-compiled candidate functional files.
while IFS= read -r rel; do cp "$CAND/$rel" "$rel"; done < "$TMP/allowed-functional.txt"
# Byte equality between compiled candidate and live files.
while IFS= read -r rel; do cmp -s "$CAND/$rel" "$rel" || fail "candidate/live mismatch: $rel"; done < "$TMP/allowed-functional.txt"
pass "candidate/source validation PASS"

# Final pre-version checks: only three functional files differ from exact 26480.
python3 - "$PRETREE" "$REPO" "$TMP/allowed-functional.txt" <<'PY'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
def h(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): out[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 v=root/'app/version.properties'; out['app/version.properties']=hashlib.sha256(v.read_bytes()).hexdigest()
 return out
a,b=h(A),h(B); changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed!=allowed: raise SystemExit('live pre-version scope mismatch: '+repr(sorted(changed)))
print('live pre-version exact functional scope PASS')
PY

pass "PRE-BUILD SAFETY PROOF PASSED"
echo "  baseline source PASS — successful 26480 artifact only"
echo "  binary pre-edit patch before 26481 modification PASS"
echo "  transform dry-run PASS"
echo "  changed-file allowlist PASS"
echo "  protected successful-26480 hashes PASS"
echo "  shader asset/reference + glslang PASS"
echo "  source structural PASS"
echo "  Gradle compile PASS on full temporary candidate"
echo "  Temporary-copy validation: PASS"
echo "  candidate/source byte equality PASS"
echo "  Wronski/IPOL normal fusion untouched PASS"
echo "  26480 short capture/ZSL architecture preserved PASS"
echo "  MotionV2Denoise remains disabled PASS"
echo "  max-RGB render/UHDR path protected PASS"
echo "  version/build increment is last and shares the final Gradle command block PASS"

# VERSION IS LAST. It is changed in the same guarded block as the final Gradle build.
(
python3 - <<'PY'
from pathlib import Path
p=Path('app/version.properties'); t=p.read_text()
if t.count('VERSION_NAME=0.9726480')!=1 or t.count('VERSION_BUILD=26480')!=1:
    raise SystemExit('version baseline anchors are not exact 26480')
t=t.replace('VERSION_NAME=0.9726480','VERSION_NAME=0.9726481',1)
t=t.replace('VERSION_BUILD=26480','VERSION_BUILD=26481',1)
p.write_text(t)
print('version/build incremented to 0.9726481 / 26481')
PY
./gradlew clean assembleDebug --no-daemon
) 2>&1 | tee "$FINALLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "final 26481 Gradle build"
grep -q 'BUILD SUCCESSFUL' "$FINALLOG" || fail "final Gradle did not report BUILD SUCCESSFUL"
pass "final APK Gradle build PASS"

# Prove final native configure used the same generated dependency bytes as the
# already-compiled temporary candidate. Then remove these generated files from
# the source tree before source-delta/next-baseline packaging. The APK remains
# the already-built binary; cleanup only restores canonical source cleanliness.
python3 - "$CAND" "$REPO" "$TMP/generated-native-deps.txt" <<'PY'
from pathlib import Path
import hashlib,sys
cand,live=Path(sys.argv[1]),Path(sys.argv[2])
paths=[x for x in Path(sys.argv[3]).read_text().splitlines() if x]
for rel in paths:
    a,b=cand/rel,live/rel
    if not a.is_file() or not b.is_file():
        raise SystemExit('generated native dependency missing after final build: '+rel)
    ha=hashlib.sha256(a.read_bytes()).hexdigest()
    hb=hashlib.sha256(b.read_bytes()).hexdigest()
    if ha != hb:
        raise SystemExit(f'candidate/final generated native dependency mismatch: {rel} candidate={ha} final={hb}')
    print(f'generated native dependency byte equality PASS: {rel} {ha}')
PY

while IFS= read -r rel; do
  rm -f "$rel"
  [[ ! -e "$rel" ]] || fail "generated native dependency cleanup failed: $rel"
done < "$TMP/generated-native-deps.txt"
pass "generated native build inputs removed before canonical source delta"

python3 - "$REPO/$BASE_HASHES" "$REPO" "$TMP/allowed-functional.txt" <<'PY'
from pathlib import Path
import hashlib,sys
manifest=Path(sys.argv[1]); root=Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
for line in manifest.read_text().splitlines():
    if not line.strip():
        continue
    expected,path=line.split(None,1); path=path.strip()
    if path in allowed:
        continue
    p=root/path
    if not p.is_file():
        raise SystemExit('post-final protected canonical file missing: '+path)
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit('post-final protected canonical hash changed: '+path)
print('post-final canonical source hashes PASS')
PY

# Final exact four-file delta and recovery artifacts for 26482 baseline.
cat > "$TMP/allowed-final.txt" <<'EOF'
app/src/main/assets/shaders/motionv2/color_transform.glsl
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
app/version.properties
EOF
python3 - "$PRETREE" "$REPO" "$TMP/allowed-final.txt" <<'PY'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
def h(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): out[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 v=root/'app/version.properties'; out['app/version.properties']=hashlib.sha256(v.read_bytes()).hexdigest()
 return out
a,b=h(A),h(B); changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed!=allowed: raise SystemExit('final 26481 delta mismatch: '+repr(sorted(changed)))
print('final exact four-file 26480->26481 delta PASS')
PY

# Build a true direct 26480->26481 patch using a temporary local baseline commit; never pushed.
(
  cd "$BASE"
  git -c user.name=Photon26481 -c user.email=local@invalid add app/src/main app/version.properties
  git -c user.name=Photon26481 -c user.email=local@invalid commit -q -m 'temporary exact successful 26480 artifact baseline'
  while IFS= read -r rel; do cp "$REPO/$rel" "$rel"; done < "$TMP/allowed-final.txt"
  git diff --binary HEAD -- app/src/main app/version.properties
) > "$DELTAPATCH"
[[ -s "$DELTAPATCH" ]] || fail "direct 26480->26481 source patch empty"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$AFTERHASH"
sha256sum app/version.properties >> "$AFTERHASH"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one final debug APK, found ${#APKS[@]}"
rm -f ./*.apk
cp "${APKS[0]}" "$APK_NAME"
APK_SHA="$(sha "$APK_NAME")"

cat > "$REPORT" <<EOF
26481 DIRECT SUCCESSFUL-26480 ROOT-CAUSE BUILD
==============================================
Version=$NEW_VERSION
Build=$NEW_BUILD
Successful26480Head=$SUCCESSFUL_26480_HEAD
Successful26480ArtifactPatchSHA256=$BASE_PATCH_SHA
Successful26480ArtifactManifestSHA256=$BASE_HASHES_SHA
TransformSHA256=$TRANSFORM_SHA
BackupBranch=$BACKUP_BRANCH
BaselineReplay=NONE_OLDER_THAN_26480
Historical26479Replay=false
TemporaryCandidateFullGradleBuild=true
GeneratedNativeDepsCandidateFinalByteEqual=true
GeneratedNativeDepsExcludedFromCanonicalSource=true
ExactMetadataTimestampOwnership=true
ShortRoleTimestampToleranceNs=2000000
ShortWaitMsPreserved=300
BjzhouCalculationOnlyWbRepair=true
RepairBeforeCamera2WbMatrix=true
SpatialHueDonor=false
BroadDesaturation=false
WronskiMathChanged=false
MotionV2Denoise=false
Sharpening=false
UltraHdrProtected=true
APK=$APK_NAME
APK_SHA256=$APK_SHA
EOF

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$TRANSFORM" "$OUTDIR/next_baseline_inputs/"
cp "$0" "$OUTDIR/next_baseline_inputs/build_26481_direct_successful_26480_v1_2.sh"
if [[ -f .github/workflows/build-26481-direct-successful-26480-v1_2.yml ]]; then
  cp .github/workflows/build-26481-direct-successful-26480-v1_2.yml "$OUTDIR/next_baseline_inputs/"
fi
cp "$DELTAPATCH" "$OUTDIR/next_baseline_inputs/26481_source.patch"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26481_after.sha256"
sha256sum "$PREPATCH" "$DELTAPATCH" "$AFTERHASH" "$REPORT" "$CANDLOG" "$FINALLOG" "$SHADERLOG" > "$OUTDIR/26481_artifact_hashes.sha256"
echo "APK=$APK_NAME"
echo "SHA256=$APK_SHA"
echo "26481 BUILD SUCCESS"
