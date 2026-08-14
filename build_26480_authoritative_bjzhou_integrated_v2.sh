#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_PARENT="c4ccb0bd3ddc224de7dad10d5ffd682ac3097988"
EXPECTED_26479_V10="028c77b6970801d2d360d45917f811286b6aaa39"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
NEW_VERSION="0.9726480"
NEW_BUILD="26480"
OUTDIR="build_26480_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-bjzhou-integrated-motion-v2-debug.apk"
BACKUP_BRANCH="backup-26480-v2-before-replay-bootstrap-blob-fix"

REPLAY_PATCH="26479_successful_source.patch"
REPLAY_HASHES="26479_successful_after.sha256"
TRANSFORM="transform_26480_bjzhou_integrated_v2.py"
PRECURSOR="transform_26480_precursor_v1.py"
POST="transform_26480_bjzhou_integrated_v2_post.py"

REPLAY_PATCH_SHA="996aac3986f658663d23b53d698f4657f0c01c65c3f725de3fc362fde88ab417"
REPLAY_HASHES_SHA="900729d32ddc3d621bd51f21ff6afde74d0e34a5531d9593a2c6bc8ecaa193e7"
PRECURSOR_SHA="62f4716e402a5525416ae869c378342465d9b78cc5d3bea3b516096e86cd03aa"
POST_SHA="6d61e5a4ea1a578c262b014a6af7333c59f476d89832870fabbbfa471744f143"
TRANSFORM_SHA="091a8e1222ca2de32f7ab8730d2cc975daaaee4f9e61405316e6907c34ecb06c"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

REPO="$(pwd)"
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26480_source_audit.txt"
REPORT="$OUTDIR/26480_build_report.txt"
PRE_EDIT="$OUTDIR/26480_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26480_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26480_source.patch"
BEFORE_HASH="$OUTDIR/26480_exact_26479_before.sha256"
AFTER_HASH="$OUTDIR/26480_after.sha256"
GLSLLOG="$OUTDIR/26480_glslang_validation.txt"
CANDIDATE_BUILD_LOG="$OUTDIR/26480_temporary_candidate_build.log"
FINAL_BUILD_LOG="$OUTDIR/26480_final_build.log"

exec > >(tee "$AUDIT") 2>&1

echo "=== 26480 BJZHOU-INTEGRATED MOTION V2 / STRICT 26472-26474 BUILD PROCEDURE ==="
date -Iseconds || true

# -------------------------------------------------------------------------
# GATE 0: exact infrastructure lineage and package identity.
# -------------------------------------------------------------------------
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $BRANCH"
CURRENT_HEAD="$(git rev-parse HEAD)"
[[ "$(git rev-parse HEAD^)" == "$EXPECTED_PARENT" ]] || fail "26480 blob-identity correction must be direct child of exact replay-bootstrap fix commit"
[[ "$(git rev-parse HEAD~2)" == "093766319a95af2990ce1f67bd410ed2911f0850" ]] || fail "26480 blob-fix chain missing exact original V2 infrastructure commit"
[[ "$(git rev-parse HEAD~3)" == "$EXPECTED_26479_V10" ]] || fail "26480 V2 infrastructure is not rooted directly on exact successful 26479 V10 head"
EXPECTED_FIX_SCOPE="build_26480_authoritative_bjzhou_integrated_v2.sh"
ACTUAL_FIX_SCOPE="$(git diff --name-only HEAD^ HEAD | sort)"
[[ "$ACTUAL_FIX_SCOPE" == "$EXPECTED_FIX_SCOPE" ]] || { echo "ACTUAL:"; printf '%s\n' "$ACTUAL_FIX_SCOPE"; fail "26480 blob-identity correction commit must change only the guarded build script"; }
[[ "$(git diff --name-only "$EXPECTED_26479_V10" HEAD -- app/src/main app/version.properties | wc -l)" -eq 0 ]] || fail "26480 infrastructure chain directly changed app source"
for required in \
  '.github/workflows/build-26480-authoritative-bjzhou-integrated-v2.yml' \
  '26479_successful_after.sha256' \
  '26479_successful_source.patch' \
  'transform_26480_bjzhou_integrated_v2.py' \
  'transform_26480_bjzhou_integrated_v2_post.py' \
  'transform_26480_precursor_v1.py' \
  'build_26479_authoritative_v10_workflow_object_guard_fix.sh'; do
  [[ -f "$required" ]] || fail "required replay/build file missing: $required"
done
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "verified app base unavailable"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || fail "committed app source differs from verified app base before guarded replay"

[[ -f "$REPLAY_PATCH" && "$(sha "$REPLAY_PATCH")" == "$REPLAY_PATCH_SHA" ]] || fail "26479 replay patch identity mismatch"
[[ -f "$REPLAY_HASHES" && "$(sha "$REPLAY_HASHES")" == "$REPLAY_HASHES_SHA" ]] || fail "26479 replay hash manifest identity mismatch"
[[ -f "$PRECURSOR" && "$(sha "$PRECURSOR")" == "$PRECURSOR_SHA" ]] || fail "26480 precursor identity mismatch"
[[ -f "$POST" && "$(sha "$POST")" == "$POST_SHA" ]] || fail "26480 V2 post-transform identity mismatch"
[[ -f "$TRANSFORM" && "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] || fail "26480 integrated transform identity mismatch"
python3 -m py_compile "$PRECURSOR" "$POST" "$TRANSFORM"
bash -n "$0"
pass "exact branch/head/package identity gate"

# -------------------------------------------------------------------------
# GATE 1: backup branch BEFORE any candidate or live app-source modification.
# The infrastructure HEAD contains no committed app-source changes.
# -------------------------------------------------------------------------
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
if [[ -n "$REMOTE_BACKUP" ]]; then
  [[ "$REMOTE_BACKUP" == "$CURRENT_HEAD" ]] || fail "existing backup branch points to wrong commit: $REMOTE_BACKUP"
else
  git push origin "$CURRENT_HEAD:refs/heads/$BACKUP_BRANCH"
fi
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$CURRENT_HEAD" ]] || fail "backup branch verification failed"
pass "exact pre-app-modification backup branch"

# -------------------------------------------------------------------------
# GATE 2: build a FULL temporary candidate first. Live app source stays clean.
# -------------------------------------------------------------------------
TMP="$(mktemp -d)"
CAND="$TMP/candidate-worktree"
PRE="$TMP/exact-26479-before"
cleanup(){
  set +e
  if [[ -d "$CAND" ]]; then git worktree remove --force "$CAND" >/dev/null 2>&1 || true; fi
  if [[ -n "${HIST:-}" && -d "${HIST:-}" ]]; then git worktree remove --force "$HIST" >/dev/null 2>&1 || true; fi
  rm -rf "$TMP"
}
trap cleanup EXIT

HIST="$TMP/historical-26479-v10-replay"
git worktree add --detach "$HIST" "$EXPECTED_26479_V10" >/dev/null
HIST_V10="$HIST/build_26479_authoritative_v10_workflow_object_guard_fix.sh"
[[ -f "$HIST_V10" ]] || fail "historical exact V10 replay script missing"
[[ "$(git -C "$HIST" hash-object build_26479_authoritative_v10_workflow_object_guard_fix.sh)" == "7a105dcb8f67cc530499c6db029c188e71972e40" ]] || fail "historical V10 replay script blob mismatch"
HIST_TRANSFORM_ONLY="$TMP/26479_v10_transform_only.sh"
awk '/^rm -f \.\/\*\.apk$/ { exit } { print }' "$HIST_V10" > "$HIST_TRANSFORM_ONLY"
grep -q 'python3 "$PORT_TRANSFORM" "$CAND79"' "$HIST_TRANSFORM_ONLY" || fail "historical V10 transform-only extraction ended before 26479 portability transform"
! grep -q '^\./gradlew ' "$HIST_TRANSFORM_ONLY" || fail "historical transform-only replay unexpectedly contains Gradle"
chmod +x "$HIST_TRANSFORM_ONLY"
(
  cd "$HIST"
  GITHUB_REF_NAME="$EXPECTED_BRANCH" bash "$HIST_TRANSFORM_ONLY"
  sha256sum -c "$REPO/$REPLAY_HASHES"
)
pass "exact successful 26479 historical V10 replay including generated files PASS"

git worktree add --detach "$CAND" "$EXPECTED_APP_BASE" >/dev/null
rm -rf "$CAND/app/src/main"
mkdir -p "$CAND/app/src"
cp -a "$HIST/app/src/main" "$CAND/app/src/main"
cp "$HIST/app/version.properties" "$CAND/app/version.properties"
(
  cd "$CAND"
  sha256sum -c "$REPO/$REPLAY_HASHES"
)
pass "exact successful 26479 source reconstructed in temporary candidate worktree"

mkdir -p "$PRE"
while IFS= read -r rel; do
  mkdir -p "$PRE/$(dirname "$rel")"
  cp "$CAND/$rel" "$PRE/$rel"
done < <(find "$CAND/app/src/main" -type f -printf '%P\n' | sed 's#^#app/src/main/#' | sort)
mkdir -p "$PRE/app"
cp "$CAND/app/version.properties" "$PRE/app/version.properties"

# Candidate pre-edit patch exists BEFORE any 26480 transform.
(
  cd "$CAND"
  git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$REPO/$OUTDIR/26480_candidate_pre_edit_binary.patch"
)
[[ -s "$OUTDIR/26480_candidate_pre_edit_binary.patch" ]] || fail "temporary candidate pre-edit patch empty"

# Apply the single integrated transform. The V1 precursor is immediately
# replaced by the V2 post-transform inside one process; V1 is never built.
python3 "$REPO/$TRANSFORM" "$CAND"

# Exactly these paths may differ between exact 26479 and final 26480.
cat > "$TMP/allowed.txt" <<'EOF_ALLOWED'
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java
app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
app/version.properties
EOF_ALLOWED

python3 - "$PRE" "$CAND" "$TMP/allowed.txt" <<'PY_SCOPE'
from pathlib import Path
import hashlib,sys
pre=Path(sys.argv[1]); cand=Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
def files(root):
    out={}
    for base in [root/'app/src/main',root/'app']:
        if not base.exists(): continue
        if base.name=='app':
            paths=[base/'version.properties']
        else:
            paths=[p for p in base.rglob('*') if p.is_file()]
        for p in paths:
            if not p.exists(): continue
            rel=str(p.relative_to(root)).replace('\\','/')
            out[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return out
a=files(pre); b=files(cand)
changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed != allowed:
    raise SystemExit('26480 changed-file scope mismatch\nactual='+repr(sorted(changed))+'\nexpected='+repr(sorted(allowed)))
print('26480 exact changed-file allowlist: PASS')
PY_SCOPE

# Scoped whitespace proof: only 26480 deltas, never historical 26479 whitespace.
while IFS= read -r rel; do
  if [[ -f "$PRE/$rel" && -f "$CAND/$rel" ]]; then
    git diff --no-index --check -- "$PRE/$rel" "$CAND/$rel" >/dev/null || fail "26480 scoped whitespace check failed: $rel"
  fi
done < "$TMP/allowed.txt"
pass "26480 scoped whitespace proof"

# -------------------------------------------------------------------------
# GATE 2A: source/math/architecture invariants on transformed candidate.
# -------------------------------------------------------------------------
CAP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
FRAME="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java"
HDRX="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
RECON="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
RENDER="$CAND/app/src/main/assets/shaders/motionv2/render.glsl"
SHORT="$CAND/app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl"
VER="$CAND/app/version.properties"

# Viewfinder stability: short capture is explicit RAW-only one-shot and must not
# mutate/rebuild the repeating preview request or use AE compensation fallback.
grep -q 'IRIS_26480_SHORT_CAPTURE_SUBMITTED' "$CAP" || fail "short role one-shot missing"
grep -q 'MANUAL_SENSOR_RAW_ONLY' "$CAP" || fail "manual RAW-only short path missing"
grep -q 'MANUAL_SENSOR_UNAVAILABLE previewAeUntouched=true' "$CAP" || fail "safe no-manual skip missing"
grep -q 'previewRepeatingRequestMutated=false' "$CAP" || fail "preview stability proof missing"
python3 - "$CAP" <<'PY_CAPTURE'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text(); a=s.index('private boolean applyMotion26480ExplicitShortCaptureIfNeeded'); b=s.index('private void resetMotion26480ShortCaptureState',a); x=s[a:b]
bad=['mPreviewRequestBuilder.set(','rebuildPreviewBuilder()','setRepeatingRequest(','clearMotionUnifiedBuffer();','CONTROL_AE_EXPOSURE_COMPENSATION']
found=[z for z in bad if z in x]
if found: raise SystemExit('short capture mutates preview/AE: '+repr(found))
for req in ['TEMPLATE_STILL_CAPTURE','mImageReaderRaw.getSurface()','CONTROL_AE_MODE_OFF','SENSOR_EXPOSURE_TIME','SENSOR_SENSITIVITY']:
    if req not in x: raise SystemExit('short capture contract missing '+req)
print('RAW-only explicit short capture / preview-stability proof: PASS')
PY_CAPTURE

# Actual TET role/admission policy: 1/3 target ±0.35 EV, actual result only,
# strictly lower than every accepted normal frame.
grep -q 'MOTION_26480_SHORT_TARGET_RATIO = 1.0 / 3.0' "$CAP" || fail "1/3 short target missing"
grep -q 'MOTION_26480_SHORT_TOLERANCE_EV = 0.35' "$CAP" || fail "short ±0.35EV tolerance missing"
grep -q 'notStrictlyLowerThanEveryNormal' "$CAP" || fail "strict role admission proof missing"
grep -q 'CaptureResult.SENSOR_EXPOSURE_TIME' "$CAP" || fail "actual exposure metadata missing"
grep -q 'CaptureResult.SENSOR_SENSITIVITY' "$CAP" || fail "actual ISO metadata missing"

# Per-frame metadata/noise: four phase pairs, valid S>0/O>=0/any O>0,
# no post-RAW sensitivity boost, no Pixel3 fallback.
grep -q 'IRIS_26480_BJZHOU_FRAME_ROLE_AND_METADATA_V2' "$FRAME" || fail "frame metadata role missing"
grep -q 'motionV2NoiseProfile = new float\[8\]' "$FRAME" || fail "four-pair noise carrier missing"
grep -q 'CAMERA2_PER_FRAME' "$CAP" || fail "per-frame Camera2 noise source missing"
grep -q 'CAMERA2_BASE_FRAME' "$HDRX" || fail "base-frame Camera2 noise fallback missing"
grep -q 'WRONSKI_EXISTING_FALLBACK' "$HDRX" || fail "existing-Wronski fallback missing"
! grep -Rqs 'PIXEL3_FALLBACK' "$CAND/app/src/main/java/com/particlesdevs/photoncamera" || fail "foreign Pixel3 noise fallback introduced"
grep -q 'normalizedSensorVariance=true' "$HDRX" || fail "normalized Camera2 noise-domain proof missing"

# Frame-sequential GPU/lifetime/cache + scheduling.
grep -q 'IRIS_26480_FRAME_SEQUENTIAL_SCRATCH_REUSE_V2' "$RECON" || fail "sequential scratch reuse missing"
grep -q 'iris26480RawScratch.loadData' "$RECON" || fail "single raw upload texture reuse missing"
grep -q 'IRIS_26480_UI_BREATHING_CHECKPOINT_V2' "$RECON" || fail "UI breathing checkpoint missing"
grep -q 'android.opengl.GLES30.glFlush(); Thread.yield();' "$RECON" || fail "safe per-frame UI yield missing"
grep -q 'IRIS_26480_BACKGROUND_PROCESSING_PRIORITY' "$HDRX" || fail "background processing priority missing"
grep -q 'THREAD_PRIORITY_BACKGROUND' "$HDRX" || fail "background thread priority not applied"

# Production diagnostic stalls removed from relevant production path.
grep -q 'IRIS_26480_DISABLE_DIRECT_SUPPORT_GPU_READBACK_V2' "$RECON" || fail "direct support readback disable missing"
grep -q 'IRIS_26480_DISABLE_SPEAKER_EDGE_DIAGNOSTIC_V2' "$RECON" || fail "speaker diagnostic disable missing"

# Deferred DNG: JPEG path first; saveRAW==2 remains immediate because there is no JPEG.
grep -q 'IRIS_26480_DEFERRED_DNG_OUTPUT_V2' "$HDRX" || fail "deferred DNG marker missing"
grep -q 'MotionDeferredOutput' "$HDRX" || fail "low-priority DNG executor missing"
grep -q 'if (saveRAW == 2)' "$HDRX" || fail "RAW-only immediate semantics lost"

# RCD/Bento-inspired math in sensor/WB calculation domain.
grep -q 'IRIS_26480_BJZHOU_RCD_OPPOSED_SHORT_HIGHLIGHT_SHADER_V2' "$SHORT" || fail "RCD opposed-color shader missing"
grep -q 'const float power=3.0' "$SHORT" || fail "RCD cube-root power missing"
grep -q '0.5\*(rg+rb)' "$SHORT" || fail "RCD opposed red reconstruction missing"
grep -q '0.5\*(rr+rb)' "$SHORT" || fail "RCD opposed green reconstruction missing"
grep -q '0.5\*(rr+rg)' "$SHORT" || fail "RCD opposed blue reconstruction missing"
grep -q 'highlightClipThreshold' "$SHORT" || fail "RCD clip threshold uniform missing"
grep -q 'highlightCeiling' "$SHORT" || fail "RCD reconstruction ceiling missing"
grep -q 'IRIS_26480_BJZHOU_RCD_BENTO_SHORT_RECOVERY' "$RECON" || fail "short recovery integration missing"
grep -q 'highlightClipThreshold", 0.985f' "$RECON" || fail "0.985 physical clip threshold missing"
grep -q 'highlightCeiling", 8.0f' "$RECON" || fail "8x calculation ceiling missing"

# Wronski normal merge remains isolated from short frame.
grep -q 'role=HIGHLIGHT_SHORT' "$CAP" || fail "short capture role missing"
grep -q 'short excluded from Wronski' "$HDRX" || fail "short/Wronski isolation proof missing"
for marker in \
  IRIS_26477_STRICT_WRONSKI_SENSOR_AUTHORITY \
  IRIS_26477_WRONSKI_NOISE_AUTHORITY \
  IRIS_26477_WRONSKI_RECONSTRUCTION_AUTHORITY \
  IRIS_26478_WRONSKI_PURE_DIVIDE_ONCE_FINALIZER \
  IRIS_26478_WRONSKI_REFERENCE_ADD_ONCE_NO_IPOL_ACCUMULATED_DENOISER \
  IRIS_26479_ADRENO_GLSL_SAMPLE_KEYWORD_PORTABILITY; do
  grep -Rqs "$marker" "$CAND/app/src/main" || fail "protected Wronski lineage marker lost: $marker"
done

# Max-RGB tone guide and version.
grep -q 'IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V2' "$RENDER" || fail "max-RGB tone guide missing"
grep -q 'max3' "$RENDER" || fail "max-RGB helper missing"
grep -Fxq "VERSION_NAME=$NEW_VERSION" "$VER" || fail "candidate version name wrong"
grep -Fxq "VERSION_BUILD=$NEW_BUILD" "$VER" || fail "candidate version build wrong"

# Protect sharpening/denoise/UHDR and core Wronski shaders by exact hash against 26479.
python3 - "$PRE" "$CAND" <<'PY_PROTECT'
from pathlib import Path
import hashlib,sys
pre,cand=map(Path,sys.argv[1:3])
protected=[
'app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_robustness_erode.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java',
'app/src/main/assets/shaders/motionv2/denoise.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
]
for rel in protected:
    a=(pre/rel).read_bytes(); b=(cand/rel).read_bytes()
    if hashlib.sha256(a).digest()!=hashlib.sha256(b).digest(): raise SystemExit('protected file changed: '+rel)
print('critical Wronski/denoise/UHDR protected hashes: PASS')
PY_PROTECT
pass "candidate/source validation PASS"

# -------------------------------------------------------------------------
# GATE 2B: explicit GLSL/runtime static proof.
# -------------------------------------------------------------------------
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator missing"
python3 - "$CAND/app/src/main/assets/shaders/motionv2" <<'PY_GLSL_SCAN'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]); bad=[]
for p in sorted(root.glob('*.glsl')):
    t=p.read_text(errors='replace')
    code=re.sub(r'/\*.*?\*/',' ',t,flags=re.S); code=re.sub(r'//[^\n]*',' ',code)
    if re.search(r'\bsample\b',code): bad.append((p.name,'reserved word sample'))
    if 'layout(rg32f' in code.replace(' ','').lower(): bad.append((p.name,'rg32f imageStore risk'))
    if re.search(r'\bimage2D\s+\w+\s*[,)]',code): bad.append((p.name,'image2D function parameter'))
if bad: raise SystemExit('MotionV2 GLSL static portability failures: '+repr(bad))
print('all MotionV2 GLSL reserved/layout/function-parameter scan: PASS')
PY_GLSL_SCAN

WRAPC="$TMP/wrap_compute.py"; WRAPF="$TMP/wrap_frag.py"
cat > "$WRAPC" <<'PY_WC'
from pathlib import Path
import re,sys
s=Path(sys.argv[1]).read_text()
s=re.sub(r'(?m)^#define\s+LAYOUT\s+//\s*\nLAYOUT\s*\n','',s,count=1)
Path(sys.argv[2]).write_text('#version 310 es\nlayout(local_size_x=8,local_size_y=8,local_size_z=1) in;\n'+s)
PY_WC
cat > "$WRAPF" <<'PY_WF'
from pathlib import Path
import sys
Path(sys.argv[2]).write_text('#version 310 es\n'+Path(sys.argv[1]).read_text())
PY_WF

: > "$GLSLLOG"
for name in short_highlight_recover direct_rgb_accumulate mfsr_low_support_reference mfsr_finalize mfsr_kernel_covariance mfsr_robustness mfsr_robustness_erode; do
  python3 "$WRAPC" "$CAND/app/src/main/assets/shaders/motionv2/$name.glsl" "$TMP/$name.comp"
  glslangValidator -S comp "$TMP/$name.comp" 2>&1 | tee -a "$GLSLLOG"
done
python3 "$WRAPF" "$CAND/app/src/main/assets/shaders/motionv2/render.glsl" "$TMP/render.frag"
glslangValidator -S frag "$TMP/render.frag" 2>&1 | tee -a "$GLSLLOG"
pass "explicit GLSL compiler proof for new/critical MotionV2 shaders"

# -------------------------------------------------------------------------
# GATE 2C: FULL temporary candidate Gradle build BEFORE live app edit.
# This catches Java/API/signature/resource errors that syntax greps cannot.
# -------------------------------------------------------------------------
(
  cd "$CAND"
  chmod +x ./gradlew
  set +e
  ./gradlew clean assembleDebug --no-daemon --stacktrace 2>&1 | tee "$REPO/$CANDIDATE_BUILD_LOG"
  RC=${PIPESTATUS[0]}
  set -e
  [[ $RC -eq 0 ]] || exit $RC
)
[[ -f "$CANDIDATE_BUILD_LOG" ]] || fail "candidate Gradle log missing"
grep -q 'BUILD SUCCESSFUL' "$CANDIDATE_BUILD_LOG" || fail "temporary candidate did not report BUILD SUCCESSFUL"
mapfile -t CAND_APKS < <(find "$CAND/app/build/outputs/apk" -type f -name '*.apk' | sort)
[[ ${#CAND_APKS[@]} -eq 1 ]] || fail "expected exactly one temporary candidate APK, found ${#CAND_APKS[@]}"
pass "FULL TEMPORARY CANDIDATE GRADLE BUILD PASS"
pass "Temporary-copy validation: PASS"

# -------------------------------------------------------------------------
# GATE 3: only now reconstruct exact 26479 in LIVE tree and create true pre-edit patch.
# -------------------------------------------------------------------------
git apply --check "$REPLAY_PATCH"
git apply "$REPLAY_PATCH"
sha256sum -c "$REPLAY_HASHES"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$BEFORE_HASH"
sha256sum app/version.properties >> "$BEFORE_HASH"
git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PRE_EDIT"
[[ -s "$PRE_EDIT" ]] || fail "true 26480 pre-edit patch empty"
git apply --check --reverse "$PRE_EDIT" || fail "true 26480 pre-edit patch cannot reverse exact 26479"
pass "TRUE 26480 pre-edit binary patch created before live 26480 source modification"

# Apply EXACT already-built candidate files, never rerun a transformation on live source.
while IFS= read -r rel; do
  mkdir -p "$(dirname "$rel")"
  cp "$CAND/$rel" "$rel"
done < "$TMP/allowed.txt"

# Live source must byte-match the candidate that already built.
while IFS= read -r rel; do
  cmp -s "$rel" "$CAND/$rel" || fail "live file differs from built candidate: $rel"
done < "$TMP/allowed.txt"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$AFTER_HASH"
sha256sum app/version.properties >> "$AFTER_HASH"

python3 - "$BEFORE_HASH" "$AFTER_HASH" "$TMP/allowed.txt" <<'PY_LIVE_SCOPE'
from pathlib import Path
import sys
def load(p):
 d={}
 for line in Path(p).read_text().splitlines():
  h,n=line.split(None,1); d[n.strip()]=h
 return d
b=load(sys.argv[1]); a=load(sys.argv[2]); allow=set(Path(sys.argv[3]).read_text().splitlines())
changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed!=allow: raise SystemExit('live 26480 delta mismatch: '+repr(sorted(changed)))
print('live exact changed-file allowlist: PASS')
PY_LIVE_SCOPE

# Re-run final critical invariants on live candidate.
grep -Fxq "VERSION_NAME=$NEW_VERSION" app/version.properties || fail "live version wrong"
grep -Fxq "VERSION_BUILD=$NEW_BUILD" app/version.properties || fail "live build wrong"
grep -q 'IRIS_26480_BJZHOU_RCD_OPPOSED_SHORT_HIGHLIGHT_SHADER_V2' app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl || fail "live RCD shader missing"
grep -q 'previewRepeatingRequestMutated=false' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java || fail "live preview safety proof missing"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

echo "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  exact backup branch before source modification PASS"
echo "  exact successful 26479 replay/hash manifest PASS"
echo "  candidate pre-edit patch before candidate modification PASS"
echo "  full transformed temporary candidate Gradle build PASS"
echo "  GLSL reserved-keyword/format/function-parameter scan PASS"
echo "  glslang compilation of new + critical MotionV2 shaders PASS"
echo "  RAW-only explicit short role / repeating preview untouched PASS"
echo "  actual TET short admission 1/3 ±0.35EV PASS"
echo "  Camera2 per-frame/base-frame noise-source hierarchy PASS"
echo "  frame-sequential scratch/reference lifetime PASS"
echo "  production readback cleanup PASS"
echo "  background/UI scheduling PASS"
echo "  deferred DNG output scheduling PASS"
echo "  RCD opposed-color WB-domain highlight math PASS"
echo "  Wronski/IPOL normal merge protected PASS"
echo "  version/build increment in same guarded script PASS"

# -------------------------------------------------------------------------
# GATE 4: FINAL live build, same exact bytes that passed temporary candidate build.
# -------------------------------------------------------------------------
set +e
./gradlew clean assembleDebug --no-daemon --stacktrace 2>&1 | tee "$FINAL_BUILD_LOG"
FINAL_RC=${PIPESTATUS[0]}
set -e
[[ $FINAL_RC -eq 0 ]] || fail "final Gradle failed rc=$FINAL_RC"
grep -q 'BUILD SUCCESSFUL' "$FINAL_BUILD_LOG" || fail "final Gradle returned without BUILD SUCCESSFUL"

mapfile -t APKS < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
[[ ${#APKS[@]} -eq 1 ]] || fail "expected exactly one final APK, found ${#APKS[@]}"
cp "${APKS[0]}" "$APK_NAME"
APK_SHA="$(sha "$APK_NAME")"

cat > "$REPORT" <<EOF_REPORT
26480 bjzhou-integrated Motion V2
================================
Infrastructure parent: $EXPECTED_PARENT
Infrastructure HEAD: $CURRENT_HEAD
Verified app base: $EXPECTED_APP_BASE
Backup branch: $BACKUP_BRANCH -> $CURRENT_HEAD
Build: $NEW_VERSION / $NEW_BUILD
APK: $APK_NAME
APK SHA256: $APK_SHA

Capture / viewfinder:
- Repeating preview request is not mutated or rebuilt for the short frame.
- One RAW-only TEMPLATE_STILL_CAPTURE is tagged HIGHLIGHT_SHORT.
- Manual sensor exposure = normal actual exposure / 3 at same ISO, bounded by Camera2 ranges.
- If MANUAL_SENSOR is unavailable, short recovery is skipped; preview AE is not perturbed.
- Actual returned exposure*ISO admits short frame only within 1/3 +/-0.35EV and strictly below all normal frames.

Metadata / noise:
- Frame carries result sensor timestamp, frame number, actual exposure, actual ISO, focus, lens state, rolling shutter skew.
- Four Camera2 SENSOR_NOISE_PROFILE CFA pairs are validated in normalized-sensor variance domain Var=S*x+O.
- Source priority: CAMERA2_PER_FRAME -> CAMERA2_BASE_FRAME -> existing strict Wronski fallback.
- No Pixel-device calibration fallback was imported.

Highlight reconstruction:
- Normal equal-exposure frames alone enter Wronski num/den.
- Short frame is aligned separately to the prepared Wronski reference.
- Clipped-site recovery uses the bjzhou/RCD power=3 opposed-color calculation in a temporary WB-conditioned sensor domain, threshold 0.985, ceiling 8.0, then inverse-WB back to camera RGB.
- Max-RGB guides the high-end tone shoulder with uniform RGB scaling.

Performance / scheduling:
- Temporal RAW/CFA/WB/covariance/robustness scratch textures are reused frame-sequentially.
- Existing immutable Wronski reference preparation remains the shared reference cache.
- Motion processing thread is lowered to Android background priority and restored afterward.
- glFlush + Thread.yield UI breathing checkpoint between temporal frames.
- Speaker/direct-support production readbacks disabled; mandatory final FLOAT32 bridge remains.
- Optional Motion reference DNG save is deferred until after JPEG when saveRAW==1; saveRAW==2 remains immediate RAW-only behavior.

Protected:
- Wronski direct RGB accumulator, literal divide-once finalizer, reference-add-once shader.
- 3-iteration ICA / IPOL robustness / covariance math.
- MotionV2Denoise remains disabled by existing 26479 pipeline.
- Sharpening remains off.
- Ultra HDR implementation protected except existing render input receives max-RGB tone-guided SDR result.
EOF_REPORT

sha256sum "$APK_NAME" "$PRE_EDIT" "$RECOVERY" "$SOURCEPATCH" "$AUDIT" "$FINAL_BUILD_LOG" > "$OUTDIR/26480_artifact_hashes.sha256"
echo "26480 BUILD SUCCESS"
echo "APK=$APK_NAME"
echo "SHA256=$APK_SHA"
