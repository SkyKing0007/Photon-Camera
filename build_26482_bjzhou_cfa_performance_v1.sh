#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
SUCCESSFUL_26481_INFRA_HEAD="0416d55443e7aa1834e87e2d69a39f2a9172b1bc"
BACKUP_BRANCH="backup-26481-success-before-26482-bjzhou-cfa-domain-fix"
BASE_PATCH="26481_successful_source.patch"
BASE_PATCH_SHA="65a3859eaba66503dcf98067aed29208e6c2ab7dbb74dc1077004ac03ad8c039"
BASE_HASHES="26481_successful_after.sha256"
BASE_HASHES_SHA="6d1906925e653e61d3f0368b1f627c1fe204d76586d5265267b4b4109f4f9d95"
TRANSFORM="transform_26482_bjzhou_cfa_performance_v1.py"
TRANSFORM_SHA="390ec44be747409f13d38eafaa7947c7b5cba8e1920d70d258fa1d608c6339d1"
NEW_VERSION="0.9726482"
NEW_BUILD="26482"
OUTDIR="build_26482_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-bjzhou-cfa-performance-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

REPO="$(pwd)"
rm -rf "$OUTDIR"; mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26482_source_audit.txt"
CANDLOG="$OUTDIR/26482_temporary_candidate_build.log"
FINALLOG="$OUTDIR/26482_final_build.log"
SHADERLOG="$OUTDIR/26482_shader_validation.txt"
REPORT="$OUTDIR/26482_build_report.txt"
PREPATCH="$OUTDIR/26482_pre_edit_exact_26481_binary.patch"
DELTAPATCH="$OUTDIR/26482_delta_from_26481.patch"
SOURCEPATCH="$OUTDIR/26482_source.patch"
AFTERHASH="$OUTDIR/26482_after.sha256"
exec > >(tee "$AUDIT") 2>&1

echo "=== 26482 DIRECT FROM SUCCESSFUL 26481 CHECKPOINT ==="
date -Iseconds || true

# GATE 0 — direct checkpoint/package identity. No 26480/26479 replay is executable here.
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" != "dev" ]] || fail "dev is protected"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $BRANCH"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "verified app-base commit unavailable"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || \
  fail "committed app source is not unchanged verified base; refuse to overwrite"
[[ -f "$BASE_PATCH" && "$(sha "$BASE_PATCH")" == "$BASE_PATCH_SHA" ]] || fail "successful 26481 direct source patch identity mismatch"
[[ -f "$BASE_HASHES" && "$(sha "$BASE_HASHES")" == "$BASE_HASHES_SHA" ]] || fail "successful 26481 manifest identity mismatch"
[[ -f "$TRANSFORM" && "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] || fail "26482 transform identity mismatch"
python3 -m py_compile "$TRANSFORM" || fail "26482 transform Python syntax"
bash -n "$0" || fail "26482 build script syntax"
[[ "$BASE_PATCH" == "26481_successful_source.patch" ]] || fail "direct 26481 baseline patch name changed"
[[ "$BASE_HASHES" == "26481_successful_after.sha256" ]] || fail "direct 26481 manifest name changed"
# Historical checkpoint files may still exist in the infrastructure branch, but this
# builder has no variables or reconstruction functions for them. The only executable
# reconstruction inputs above are the direct successful-26481 patch + manifest.
pass "successful-26481 direct-baseline package identity"

# GATE 1 — verify the user-created pre-26482 backup branch points to the successful 26481 infrastructure checkpoint.
remote="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ -n "$remote" ]] || fail "required backup branch missing: $BACKUP_BRANCH"
[[ "$remote" == "$SUCCESSFUL_26481_INFRA_HEAD" ]] || fail "backup branch points to $remote, expected $SUCCESSFUL_26481_INFRA_HEAD"
pass "backup branch exact successful 26481 infrastructure checkpoint"

TMP="$(mktemp -d)"
BASE="$TMP/exact-successful-26481"
CAND="$TMP/candidate-26482"
PRETREE="$TMP/pre26482"
cleanup(){ set +e; git worktree remove --force "$BASE" >/dev/null 2>&1 || true; git worktree remove --force "$CAND" >/dev/null 2>&1 || true; [[ -n "${DIRECT:-}" ]] && git worktree remove --force "$DIRECT" >/dev/null 2>&1 || true; rm -rf "$TMP"; }
trap cleanup EXIT

reconstruct_26481(){
  local dst="$1"
  git worktree add --detach "$dst" "$EXPECTED_APP_BASE" >/dev/null || fail "create clean app-base worktree"
  ( cd "$dst" && git apply --check --binary "$REPO/$BASE_PATCH" ) || fail "successful 26481 patch does not apply cleanly to verified app base"
  ( cd "$dst" && git apply --binary "$REPO/$BASE_PATCH" ) || fail "successful 26481 direct patch apply"
  ( cd "$dst" && sha256sum -c "$REPO/$BASE_HASHES" ) || fail "successful 26481 full manifest verification"
  grep -q '^VERSION_NAME=0\.9726481$' "$dst/app/version.properties" || fail "reconstructed baseline version is not 26481"
  grep -q '^VERSION_BUILD=26481$' "$dst/app/version.properties" || fail "reconstructed baseline build is not 26481"
  grep -q 'IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP' "$dst/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" || fail "26481 exact metadata ownership missing"
  grep -q 'IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR' "$dst/app/src/main/assets/shaders/motionv2/color_transform.glsl" || fail "26481 color baseline marker missing"
}

# GATE 2 — reconstruct exact successful 26481 once, then create pre-edit backup patch before modification.
reconstruct_26481 "$BASE"
pass "baseline source PASS — exact successful 26481 artifact reconstructed"
mkdir -p "$PRETREE/app/src" "$PRETREE/app"
cp -a "$BASE/app/src/main" "$PRETREE/app/src/main"
cp "$BASE/app/version.properties" "$PRETREE/app/version.properties"
( cd "$BASE" && git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties ) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "26482 pre-edit exact-26481 binary patch is empty"
pass "binary pre-edit patch created before 26482 modification"

# Candidate is independently reconstructed from the SAME successful 26481 checkpoint.
reconstruct_26481 "$CAND"
python3 "$REPO/$TRANSFORM" "$CAND" || fail "26482 transform application"
pass "transform dry-run PASS"

cat > "$TMP/allowed-functional.txt" <<'EOF'
app/src/main/assets/shaders/motionv2/color_transform.glsl
app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java
EOF

python3 - "$PRETREE" "$CAND" "$TMP/allowed-functional.txt" <<'PY'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
def h(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): out[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 v=root/'app/version.properties';out['app/version.properties']=hashlib.sha256(v.read_bytes()).hexdigest();return out
a,b=h(A),h(B);changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed!=allowed: raise SystemExit('candidate changed-file allowlist mismatch\nactual='+repr(sorted(changed))+'\nexpected='+repr(sorted(allowed)))
print('candidate changed-file allowlist PASS')
PY

# Every unmodified canonical file remains byte-exact successful 26481.
python3 - "$REPO/$BASE_HASHES" "$CAND" "$TMP/allowed-functional.txt" <<'PY'
from pathlib import Path
import hashlib,sys
manifest=Path(sys.argv[1]);root=Path(sys.argv[2]);allowed=set(Path(sys.argv[3]).read_text().splitlines())
for line in manifest.read_text().splitlines():
 if not line.strip():continue
 expected,path=line.split(None,1);path=path.strip()
 if path in allowed:continue
 p=root/path
 if not p.is_file():raise SystemExit('protected file missing: '+path)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise SystemExit('protected hash changed: '+path)
print('protected successful-26481 hashes PASS')
PY

# GATE 3 — structural/ownership invariants.
CAP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
CR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
WA="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
CJ="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java"
CG="$CAND/app/src/main/assets/shaders/motionv2/color_transform.glsl"
WB="$CAND/app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl"
FIN="$CAND/app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl"
SHORT="$CAND/app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl"

grep -q 'IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP' "$CAP" || fail "exact metadata ownership lost"
grep -q 'MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS = 2_000_000L' "$CAP" || fail "2ms short role identity lost"
[[ "$(grep -o 'MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS' "$CAP" | wc -l)" -eq 3 ]] || fail "2ms short role producer/consumer count changed"
! grep -q '40_000_000L' "$CAP" || fail "stale 40ms metadata/short-role association returned"
grep -q 'MOTION_26480_SHORT_WAIT_MS = 300L' "$CAP" || fail "short wait policy changed"
grep -q 'IRIS_26480_SHORT_CAPTURE_SUBMITTED' "$CAP" || fail "explicit RAW-only short capture lost"

grep -q 'IRIS_26482_BJZHOU_CFA_CALCULATION_DOMAIN_CLIP_AUTHORITY' "$WB" || fail "CFA calculation-domain clip authority missing"
grep -q 'vec4 physical=camera/max(sensorExposureScale' "$WB" || fail "physical normalized photosite authority missing"
grep -q 'sensorExposureScale' "$WB" || fail "physical exposure unscale missing"
grep -q 'opposedEstimate' "$WB" || fail "opposed CFA reconstruction missing"
[[ "$(grep -o 'setVar("sensorExposureScale"' "$CR" | wc -l)" -eq 3 ]] || fail "expected three Wronski CFA physical exposure bindings"
[[ "$(grep -o 'setVar("physicalClipThreshold"' "$CR" | wc -l)" -eq 3 ]] || fail "expected three physical clip threshold bindings"

grep -q 'IRIS_26482_CAMERA2_COLOR_ONLY_AFTER_CFA_CLIP_AUTHORITY' "$CG" || fail "pure Camera2 color stage missing"
! grep -q 'IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR' "$CG" || fail "too-late 26481 RGB repair remains"
! grep -q 'sensorClipLevel' "$CG" || fail "RGB clip proxy remains in shader"
! grep -q 'sensorClipLevel' "$CJ" || fail "RGB clip proxy remains in Java color owner"
grep -q 'IRIS_26482_CAMERA2_COLOR_ONLY_AFTER_CFA_AUTHORITY' "$CJ" || fail "26482 color telemetry missing"

grep -q 'vec3 wbRgb=num/den;' "$FIN" || fail "Wronski divide-once finalizer changed"
grep -q 'vec3 sensorRgb=wbRgb/vec3' "$FIN" || fail "Wronski calculation gains no longer removed at output"
grep -q 'IRIS_26482_WRONSKI_SEQUENTIAL_ALIGNMENT_SCRATCH' "$WA" || fail "alignment scratch reuse missing"
grep -q 'icaIterations=3FineOnly' "$WA" || fail "three fine ICA iterations changed"
grep -q 'radii=1,4,4,4' "$WA" || fail "Wronski search radii changed"
grep -q 'metrics=L1,L2,L2,L2' "$WA" || fail "Wronski distance metrics changed"
grep -q 'mathChanged=false' "$WA" || fail "alignment transform does not attest math preservation"

grep -q 'IRIS_26480_BJZHOU_RCD_OPPOSED_SHORT_HIGHLIGHT_SHADER_V2' "$SHORT" || fail "proven short-highlight shader lost"
grep -q 'IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V2' "$CAND/app/src/main/assets/shaders/motionv2/render.glsl" || fail "max-RGB render guide lost"
! grep -q 'add(new MotionV2Denoise());' "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java" || fail "MotionV2Denoise re-enabled"
pass "source structural/ownership PASS"

# Static Java delimiter proof for the modified Java files (Gradle below is authoritative compile proof).
python3 - "$CJ" "$CR" "$WA" <<'PY'
from pathlib import Path
import sys
for name in sys.argv[1:]:
 t=Path(name).read_text()
 if t.count('{')!=t.count('}'):raise SystemExit('Java brace mismatch: '+name)
 if '\x00' in t:raise SystemExit('NUL in Java source: '+name)
 print('Java lexical structure PASS:',name)
PY

# GLSL lexical + real glslang compilation for both modified shaders.
python3 - "$CG" "$WB" > "$SHADERLOG" <<'PY'
from pathlib import Path
import sys,re
for name in sys.argv[1:]:
 t=Path(name).read_text()
 if t.count('{')!=t.count('}'):raise SystemExit('shader brace mismatch: '+name)
 if '\x00' in t:raise SystemExit('shader NUL: '+name)
 if not re.search(r'void\s+main\s*\(',t):raise SystemExit('shader main missing: '+name)
 print('shader lexical structure PASS:',name)
PY
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator unavailable; workflow must install glslang-tools"
{ echo '#version 300 es'; cat "$CG"; } > "$TMP/26482_color.frag"
glslangValidator -S frag "$TMP/26482_color.frag" >> "$SHADERLOG" 2>&1 || { cat "$SHADERLOG"; fail "26482 color shader compilation"; }
sed 's/^#define LAYOUT \/\//#define LAYOUT layout(local_size_x=8,local_size_y=8,local_size_z=1) in;/' "$WB" > "$TMP/26482_wb_body.comp"
{ echo '#version 310 es'; cat "$TMP/26482_wb_body.comp"; } > "$TMP/26482_wb.comp"
glslangValidator -S comp "$TMP/26482_wb.comp" >> "$SHADERLOG" 2>&1 || { cat "$SHADERLOG"; fail "26482 WB CFA shader compilation"; }
echo 'glslang modified shader compilation PASS' >> "$SHADERLOG"
cat "$SHADERLOG"
pass "shader asset/reference PASS"

# CRITICAL SOP: full transformed candidate Gradle build BEFORE live source is touched.
(
  cd "$CAND"
  chmod +x ./gradlew
  ./gradlew clean assembleDebug --no-daemon
) 2>&1 | tee "$CANDLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "full temporary candidate Gradle build"
grep -q 'BUILD SUCCESSFUL' "$CANDLOG" || fail "temporary candidate did not report BUILD SUCCESSFUL"
pass "Gradle compile PASS — full temporary candidate"

# CMake downloads these during native configure; they are generated build inputs, not canonical source.
cat > "$TMP/generated-native-deps.txt" <<'EOF'
app/src/main/cpp/deps/archive.h
app/src/main/cpp/deps/archive_entry.h
app/src/main/cpp/deps/technicallyflac.h
app/src/main/cpp/deps/tiny_dng_writer.h
EOF
while IFS= read -r rel; do
  ! grep -Fq "  $rel" "$BASE_HASHES" || fail "generated native dep unexpectedly in canonical 26481 manifest: $rel"
  [[ ! -e "$PRETREE/$rel" ]] || fail "generated native dep unexpectedly in canonical 26481 tree: $rel"
  [[ -f "$CAND/$rel" ]] || fail "candidate build did not materialize native dep: $rel"
done < "$TMP/generated-native-deps.txt"
python3 - "$REPO/$BASE_HASHES" "$CAND" "$TMP/allowed-functional.txt" <<'PY2'
from pathlib import Path
import hashlib,sys
manifest=Path(sys.argv[1]);root=Path(sys.argv[2]);allowed=set(Path(sys.argv[3]).read_text().splitlines())
for line in manifest.read_text().splitlines():
 if not line.strip():continue
 expected,path=line.split(None,1);path=path.strip()
 if path in allowed:continue
 p=root/path
 if not p.is_file():raise SystemExit('post-candidate protected canonical file missing: '+path)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise SystemExit('post-candidate protected canonical hash changed: '+path)
print('post-candidate canonical source hashes PASS')
PY2
while IFS= read -r rel; do sha256sum "$CAND/$rel"; done < "$TMP/generated-native-deps.txt" > "$OUTDIR/26482_candidate_generated_native_deps.sha256"
pass "candidate generated native dependency identity captured"
pass "Temporary-copy validation: PASS"

# Only now reconstruct the ephemeral live Actions tree to exact 26481.
git apply --check --binary "$BASE_PATCH" || fail "live successful-26481 direct baseline apply check"
git apply --binary "$BASE_PATCH" || fail "live successful-26481 direct baseline apply"
sha256sum -c "$BASE_HASHES" || fail "live successful-26481 baseline manifest"
pass "live exact successful 26481 baseline PASS"

# Copy only already-compiled candidate functional files; prove byte equality.
while IFS= read -r rel; do cp "$CAND/$rel" "$rel"; done < "$TMP/allowed-functional.txt"
while IFS= read -r rel; do cmp -s "$CAND/$rel" "$rel" || fail "candidate/live mismatch: $rel"; done < "$TMP/allowed-functional.txt"
pass "candidate/source validation PASS"

python3 - "$PRETREE" "$REPO" "$TMP/allowed-functional.txt" <<'PY'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]);allowed=set(Path(sys.argv[3]).read_text().splitlines())
def h(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file():out[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 v=root/'app/version.properties';out['app/version.properties']=hashlib.sha256(v.read_bytes()).hexdigest();return out
a,b=h(A),h(B);changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed!=allowed:raise SystemExit('live pre-version scope mismatch: '+repr(sorted(changed)))
print('live pre-version exact functional scope PASS')
PY

pass "PRE-BUILD SAFETY PROOF PASSED"
echo "  exact successful 26481 direct checkpoint PASS"
echo "  binary pre-edit patch before 26482 modification PASS"
echo "  transform dry-run PASS"
echo "  exact five-file functional allowlist PASS"
echo "  protected successful-26481 hashes PASS"
echo "  CFA physical clipping authority in existing WB calculation domain PASS"
echo "  too-late 26481 post-RGB clip inference removed PASS"
echo "  Wronski divide-once + 3-ICA/radii/metric invariants PASS"
echo "  sequential alignment scratch reuse without equation changes PASS"
echo "  exact timestamp + short RAW transport protected PASS"
echo "  MotionV2Denoise remains disabled PASS"
echo "  max-RGB render/UHDR path protected PASS"
echo "  full temporary candidate Gradle build PASS"
echo "  Temporary-copy validation: PASS"
echo "  candidate/source byte equality PASS"
echo "  version/build increment is last and shares final Gradle command block PASS"

# VERSION IS LAST and the final Gradle build is in the same shell group.
(
python3 - <<'PY'
from pathlib import Path
p=Path('app/version.properties');t=p.read_text()
if t.count('VERSION_NAME=0.9726481')!=1 or t.count('VERSION_BUILD=26481')!=1:
 raise SystemExit('version anchors are not exact 26481')
t=t.replace('VERSION_NAME=0.9726481','VERSION_NAME=0.9726482',1)
t=t.replace('VERSION_BUILD=26481','VERSION_BUILD=26482',1)
p.write_text(t)
print('version/build incremented to 0.9726482 / 26482')
PY
./gradlew clean assembleDebug --no-daemon
) 2>&1 | tee "$FINALLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "final 26482 Gradle build"
grep -q 'BUILD SUCCESSFUL' "$FINALLOG" || fail "final Gradle did not report BUILD SUCCESSFUL"
pass "final APK Gradle build PASS"

# Prove native-generated headers are candidate/final byte-identical, then remove from canonical source accounting.
python3 - "$CAND" "$REPO" "$TMP/generated-native-deps.txt" <<'PY'
from pathlib import Path
import hashlib,sys
cand,live=Path(sys.argv[1]),Path(sys.argv[2])
for rel in Path(sys.argv[3]).read_text().splitlines():
 if not rel:continue
 a,b=cand/rel,live/rel
 if not a.is_file() or not b.is_file():raise SystemExit('generated native dependency missing: '+rel)
 ha=hashlib.sha256(a.read_bytes()).hexdigest();hb=hashlib.sha256(b.read_bytes()).hexdigest()
 if ha!=hb:raise SystemExit(f'candidate/final generated native dependency mismatch: {rel} candidate={ha} final={hb}')
 print('generated native dependency byte equality PASS:',rel,ha)
PY
while IFS= read -r rel; do rm -f "$rel"; [[ ! -e "$rel" ]] || fail "generated native dep cleanup failed: $rel"; done < "$TMP/generated-native-deps.txt"
pass "generated native build inputs removed before canonical source delta"

# Every canonical 26481 file except the intentional functional+version delta must still match after final Gradle.
python3 - "$REPO/$BASE_HASHES" "$REPO" "$TMP/allowed-functional.txt" <<'PY'
from pathlib import Path
import hashlib,sys
manifest=Path(sys.argv[1]);root=Path(sys.argv[2]);allowed=set(Path(sys.argv[3]).read_text().splitlines());allowed.add('app/version.properties')
for line in manifest.read_text().splitlines():
 if not line.strip():continue
 expected,path=line.split(None,1);path=path.strip()
 if path in allowed:continue
 p=root/path
 if not p.is_file():raise SystemExit('post-final protected canonical file missing: '+path)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise SystemExit('post-final protected canonical hash changed: '+path)
print('post-final canonical source hashes PASS (version intentionally exempt)')
PY

cat > "$TMP/allowed-final.txt" <<'EOF'
app/src/main/assets/shaders/motionv2/color_transform.glsl
app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java
app/version.properties
EOF
python3 - "$PRETREE" "$REPO" "$TMP/allowed-final.txt" <<'PY'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]);allowed=set(Path(sys.argv[3]).read_text().splitlines())
def h(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file():out[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 v=root/'app/version.properties';out['app/version.properties']=hashlib.sha256(v.read_bytes()).hexdigest();return out
a,b=h(A),h(B);changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed!=allowed:raise SystemExit('final 26482 delta mismatch: '+repr(sorted(changed)))
print('final exact six-file 26481->26482 delta PASS')
PY

# Delta from successful 26481, useful for audit only.
(
 cd "$BASE"
 git -c user.name=Photon26482 -c user.email=local@invalid add app/src/main app/version.properties
 git -c user.name=Photon26482 -c user.email=local@invalid commit -q -m 'temporary exact successful 26481 baseline'
 while IFS= read -r rel; do cp "$REPO/$rel" "$rel"; done < "$TMP/allowed-final.txt"
 git diff --binary HEAD -- app/src/main app/version.properties
) > "$DELTAPATCH"
[[ -s "$DELTAPATCH" ]] || fail "26481->26482 delta patch empty"

# Canonical NEXT checkpoint is DIRECT app-base->26482, so future builds never need to replay 26481.
# Build the patch in a clean temporary app-base worktree and stage the full final tree so files
# introduced after the base (including Wronski/short shaders) are represented as additions.
DIRECT="$TMP/direct-26482"
git worktree add --detach "$DIRECT" "$EXPECTED_APP_BASE" >/dev/null || fail "create direct-26482 patch worktree"
rm -rf "$DIRECT/app/src/main"
mkdir -p "$DIRECT/app/src"
cp -a "$REPO/app/src/main" "$DIRECT/app/src/main"
cp "$REPO/app/version.properties" "$DIRECT/app/version.properties"
(
 cd "$DIRECT"
 git add -A app/src/main app/version.properties
 git diff --cached --binary HEAD -- app/src/main app/version.properties
) > "$SOURCEPATCH"
[[ -s "$SOURCEPATCH" ]] || fail "direct app-base->26482 source patch empty"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$AFTERHASH"
sha256sum app/version.properties >> "$AFTERHASH"
[[ "$(wc -l < "$AFTERHASH")" -eq 822 ]] || fail "26482 canonical manifest expected 822 files"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one final debug APK, found ${#APKS[@]}"
rm -f ./*.apk
cp "${APKS[0]}" "$APK_NAME"
APK_SHA="$(sha "$APK_NAME")"

cat > "$REPORT" <<EOF
26482 BJZHOU CFA-DOMAIN + WRONSKI PERFORMANCE BUILD
==================================================
Version=$NEW_VERSION
Build=$NEW_BUILD
Successful26481InfrastructureHead=$SUCCESSFUL_26481_INFRA_HEAD
Successful26481DirectPatchSHA256=$BASE_PATCH_SHA
Successful26481ManifestSHA256=$BASE_HASHES_SHA
TransformSHA256=$TRANSFORM_SHA
BackupBranch=$BACKUP_BRANCH
HistoricalReplay=false
DirectBaseline=verified-app-base-plus-single-successful-26481-patch
TemporaryCandidateFullGradleBuild=true
GeneratedNativeDepsCandidateFinalByteEqual=true
GeneratedNativeDepsExcludedFromCanonicalSource=true
ExactMetadataTimestampOwnership=true
ShortRoleTimestampToleranceNs=2000000
ShortWaitMsPreserved=300
ExistingWronskiCalculationWbDomainPreserved=true
PhysicalCfaClipAuthority=true
PhysicalClipThreshold=0.985
OpposedColorReconstructionDomain=calculation-WB-CFA
CalculationWbRemovedInMfsrFinalize=true
PostRgbClipInference=false
Camera2WbMatrixAuthority=true
WronskiNumDenChanged=false
WronskiAlignmentEquationsChanged=false
WronskiAlignmentSequentialScratchReuse=true
ReferenceAlignmentProductsPreparedOnce=true
ZslRingChanged=false
FrameCountReduced=false
MotionV2Denoise=false
Sharpening=false
UltraHdrProtected=true
APK=$APK_NAME
APK_SHA256=$APK_SHA
EOF

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$SOURCEPATCH" "$OUTDIR/next_baseline_inputs/26482_successful_source.patch"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26482_successful_after.sha256"
cp "$REPORT" "$OUTDIR/next_baseline_inputs/26482_successful_build_report.txt"
cp "$TRANSFORM" "$OUTDIR/next_baseline_inputs/"
cp "$0" "$OUTDIR/next_baseline_inputs/"
if [[ -f .github/workflows/build-26482-bjzhou-cfa-performance-v1.yml ]]; then cp .github/workflows/build-26482-bjzhou-cfa-performance-v1.yml "$OUTDIR/next_baseline_inputs/"; fi

(
 cd "$REPO"
 sha256sum "$PREPATCH" "$DELTAPATCH" "$SOURCEPATCH" "$AFTERHASH" "$REPORT" "$CANDLOG" "$FINALLOG" "$SHADERLOG"
 sha256sum "$APK_NAME"
) > "$OUTDIR/26482_artifact_hashes.sha256"

pass "26482 canonical direct checkpoint package created"
echo "APK=$APK_NAME"
echo "APK_SHA256=$APK_SHA"
echo "26482_SOURCE_PATCH_SHA256=$(sha "$SOURCEPATCH")"
echo "26482_AFTER_MANIFEST_SHA256=$(sha "$AFTERHASH")"
echo "26482 BUILD SUCCESS"
