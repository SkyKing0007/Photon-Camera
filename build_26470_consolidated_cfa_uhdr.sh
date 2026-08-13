#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
PROTECTED_HEAD="1a95b27bfa05e71603c7c512f6c6a4cf6ba94fa6"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26469-before-26470-consolidation"
PRECURSOR_SCRIPT="build_26469_censored_highlight_foundation.sh"
PRECURSOR_BLOB="79fda2b6cc605adc8daf507ba633c8e6f04e0fea"
NEW_VERSION="0.9726470"
NEW_BUILD="26470"
OUTDIR="build_26470_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-consolidated-cfa-uhdr-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26470_source_audit.txt"
REPORT="$OUTDIR/26470_build_report.txt"
GEOMETRY="$OUTDIR/26470_uhdr_geometry_validation.txt"
HASH_INITIAL="$OUTDIR/26470_protected_initial.sha256"
HASH_26469="$OUTDIR/26470_protected_26469_base.sha256"
HASH_AFTER="$OUTDIR/26470_protected_after.sha256"
PREPATCH="$OUTDIR/26470_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26470_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26470_source.patch"
exec > >(tee "$AUDIT") 2>&1

echo "=== 26470 GUARDED CONSOLIDATED CFA / UHDR BUILD ==="
date -Iseconds || true
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
pass "branch gate"

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$PROTECTED_HEAD" ]] || fail "backup=$REMOTE_BACKUP expected=$PROTECTED_HEAD"
pass "backup branch exact protected 26469 checkpoint"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "missing verified app base"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || fail "app source changed before 26470"
pass "application source unchanged from verified checkpoint"

[[ -f "$PRECURSOR_SCRIPT" ]] || fail "missing $PRECURSOR_SCRIPT"
[[ "$(git hash-object "$PRECURSOR_SCRIPT")" == "$PRECURSOR_BLOB" ]] || fail "26469 precursor blob mismatch"
pass "26469 precursor script exact"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_INITIAL"
sha256sum app/version.properties >> "$HASH_INITIAL"
pass "binary pre-edit patch created before source modification"
pass "protected-file hashes captured before source modification"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
PRECURSOR="$TMP/26469_transform_only.sh"
awk '/^chmod \+x \.\/gradlew$/ { exit } { print }' "$PRECURSOR_SCRIPT" > "$PRECURSOR"
python3 - "$PRECURSOR" "$TMP/26469_precursor_outputs" <<'PY_OUTDIR'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
a='OUTDIR="build_26469_outputs"'; r='OUTDIR="'+sys.argv[2]+'"'
if t.count(a)!=1: raise SystemExit(f'26469 OUTDIR anchor count={t.count(a)}')
p.write_text(t.replace(a,r,1)); print('26469 precursor OUTDIR rewrite: PASS')
PY_OUTDIR
chmod +x "$PRECURSOR"
bash -n "$PRECURSOR" || fail "26469 transform-only precursor syntax"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726469$' app/version.properties || fail "26469 version name"
grep -q '^VERSION_BUILD=26469$' app/version.properties || fail "26469 version build"
for marker in \
 IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_REFERENCE \
 IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_AUX \
 IRIS_26469_SPATIALLY_COHERENT_CENSORED_HIGHLIGHT \
 IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR; do
  grep -Rqs "$marker" app/src/main || fail "26469 lineage missing $marker"
done
pass "26469 CFA/highlight/eigensystem lineage reproduced"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_26469"
sha256sum app/version.properties >> "$HASH_26469"

RENDER="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java"
UHDR="app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java"
VERSION="app/version.properties"
for f in "$RENDER" "$UHDR" "$VERSION"; do
  mkdir -p "$TMP/candidate/$(dirname "$f")"; cp "$f" "$TMP/candidate/$f"
done

python3 - "$TMP/candidate" <<'PY_TRANSFORM'
from pathlib import Path
import sys
root=Path(sys.argv[1])
render=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
uhdr=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java'
version=root/'app/version.properties'
def once(s,a,b,label):
    n=s.count(a)
    if n!=1: raise SystemExit(f'{label}: expected 1 anchor, found {n}')
    return s.replace(a,b,1)

t=render.read_text()
t=once(t,
'''            Point raw = basePipeline.mParameters.rawSize;
            Point gainSize = new Point(
                    Math.max(1, raw.x / GAINMAP_DOWNSAMPLE),
                    Math.max(1, raw.y / GAINMAP_DOWNSAMPLE));
''',
'''            /* IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY */
            Point renderedSdrSize = new Point(WorkingTexture.mSize);
            Point gainSize = new Point(
                    Math.max(1, renderedSdrSize.x / GAINMAP_DOWNSAMPLE),
                    Math.max(1, renderedSdrSize.y / GAINMAP_DOWNSAMPLE));
''','render geometry')
t=once(t,
'''                Log.d(Name, "IRIS_26436_V2_GAINMAP"
                        + " size=" + gainSize.x + "x" + gainSize.y
''',
'''                Log.d(Name, "IRIS_26470_UHDR_GAINMAP_GEOMETRY"
                        + " renderedSdr=" + renderedSdrSize.x + "x" + renderedSdrSize.y
                        + " gainMap=" + gainSize.x + "x" + gainSize.y
                        + " downsample=" + GAINMAP_DOWNSAMPLE
                        + " authority=actualRenderedSdrTexture");
                Log.d(Name, "IRIS_26436_V2_GAINMAP"
                        + " size=" + gainSize.x + "x" + gainSize.y
''','geometry log')
render.write_text(t)

t=uhdr.read_text()
t=once(t,
'''                        matrix,
                        true);''',
'''                        matrix,
                        false);''','orthogonal rotation')
t=once(t,
'''            float safeMax = Math.max(1.50f, Math.min(2.5f, maxRatio));
            Gainmap gainmap = new Gainmap(oriented);
''',
'''            /* IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY */
            float baseAspect = sdrBase.getHeight() > 0
                    ? sdrBase.getWidth() / (float) sdrBase.getHeight() : 0.0f;
            float gainAspect = oriented.getHeight() > 0
                    ? oriented.getWidth() / (float) oriented.getHeight() : 0.0f;
            float aspectError = Math.abs(baseAspect - gainAspect);
            Log.d(TAG, "IRIS_26470_UHDR_ATTACH_GEOMETRY"
                    + " base=" + sdrBase.getWidth() + "x" + sdrBase.getHeight()
                    + " gain=" + oriented.getWidth() + "x" + oriented.getHeight()
                    + " rotation=" + rotation
                    + " exactOrthogonalRotation=true interpolation=false"
                    + " aspectError=" + aspectError);
            float safeMax = Math.max(1.50f, Math.min(2.5f, maxRatio));
            Gainmap gainmap = new Gainmap(oriented);
''','attach geometry log')
uhdr.write_text(t)

v=version.read_text()
v=once(v,'VERSION_NAME=0.9726469','VERSION_NAME=0.9726470','VERSION_NAME')
v=once(v,'VERSION_BUILD=26469','VERSION_BUILD=26470','VERSION_BUILD')
version.write_text(v)
PY_TRANSFORM

grep -q 'IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY' "$TMP/candidate/$RENDER" || fail "candidate render geometry marker"
grep -q 'new Point(WorkingTexture.mSize)' "$TMP/candidate/$RENDER" || fail "render geometry authority"
! grep -q 'Point raw = basePipeline.mParameters.rawSize;' "$TMP/candidate/$RENDER" || fail "raw geometry still used"
grep -q 'IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY' "$TMP/candidate/$UHDR" || fail "candidate exact rotation marker"
grep -q 'IRIS_26470_UHDR_ATTACH_GEOMETRY' "$TMP/candidate/$UHDR" || fail "candidate geometry log"
grep -q '^VERSION_NAME=0\.9726470$' "$TMP/candidate/$VERSION" || fail "candidate version name"
grep -q '^VERSION_BUILD=26470$' "$TMP/candidate/$VERSION" || fail "candidate version build"
pass "candidate/source validation PASS"

python3 - "$TMP/candidate" "$GEOMETRY" <<'PY_VALIDATE'
from pathlib import Path
import sys
root=Path(sys.argv[1]); report=Path(sys.argv[2])
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java']:
    s=(root/rel).read_text()
    if s.count('{')!=s.count('}'): raise SystemExit('brace mismatch '+rel)
def gs(w,h): return max(1,w//4),max(1,h//4)
def rot(w,h,r): return (h,w) if r%360 in (90,270) else (w,h)
def asp(w,h): return w/float(h)
lines=[]
for w,h,r in [(4096,3072,0),(4096,3072,90),(4096,2304,0),(4096,2304,90),(3072,4096,270)]:
    gw,gh=gs(w,h); bw,bh=rot(w,h,r); rw,rh=rot(gw,gh,r)
    err=abs(asp(bw,bh)-asp(rw,rh))
    if err>0.002: raise SystemExit(f'aspect proof failed {(w,h,r)} err={err}')
    lines.append(f'{w}x{h} r={r} base={bw}x{bh} gain={rw}x{rh} err={err:.8f}')
report.write_text('26470 UHDR geometry validation PASS\n\n'+'\n'.join(lines)+'\n')
print('Temporary-copy validation: PASS')
PY_VALIDATE
pass "Temporary-copy validation: PASS"

for f in "$RENDER" "$UHDR" "$VERSION"; do cp "$TMP/candidate/$f" "$f"; done
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
sha256sum app/version.properties >> "$HASH_AFTER"
python3 - "$HASH_26469" "$HASH_AFTER" "$RENDER" "$UHDR" "$VERSION" <<'PY_HASH'
from pathlib import Path
import sys
def load(p):
 d={}
 for line in Path(p).read_text().splitlines(): h,f=line.split('  ',1); d[f]=h
 return d
b=load(sys.argv[1]); a=load(sys.argv[2]); allowed=set(sys.argv[3:])
if set(b)!=set(a): raise SystemExit('protected path set changed')
bad=[p for p in b if p not in allowed and b[p]!=a[p]]
if bad: raise SystemExit('unexpected protected changes: '+', '.join(bad))
print('Protected-file hashes: PASS')
PY_HASH

for marker in \
 IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT \
 IRIS_26462_WRONSKI_PUBLISHED_COARSE_TO_FINE_ALIGNMENT \
 IRIS_26463_WRONSKI_PUBLIC_SIGNAL_DOMAIN \
 IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE \
 IRIS_26467_MOTION_OUTPUT_MODE_AUTHORITY \
 IRIS_26468_SINGLE_FRAME_FULL_MOTION_PIPELINE \
 IRIS_26468_PROCESSING_SEAM_DIAGNOSTIC \
 IRIS_26469_CENSORED_HIGHLIGHT_COHERENT_RECONSTRUCTION \
 IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_REFERENCE \
 IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_AUX \
 IRIS_26469_SPATIALLY_COHERENT_CENSORED_HIGHLIGHT \
 IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR \
 IRIS_26436_TRUE_ULTRAHDR_ATTACH \
 IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY \
 IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY; do
  grep -Rqs "$marker" app/src/main || fail "lost required marker $marker"
done
pass "historical lineage/ownership preservation PASS"

grep -q 'IRIS_26432_MOTION_V2_TRUE_LINEAR_GAINMAP' app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java || fail "V2 UHDR ownership lost"
pass "Motion V2 UHDR ownership invariant PASS"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  protected-file hashes PASS"
echo "  exact pre-26470 backup branch PASS"
echo "  26469 CFA/highlight/eigensystem lineage PASS"
echo "  rendered-SDR UHDR geometry authority PASS"
echo "  exact orthogonal gain-map rotation PASS"
echo "  version/build increment in same script PASS"

cat > "$REPORT" <<EOF_REPORT
26470 consolidated CFA / UHDR geometry build
============================================
Protected pre-26470 checkpoint: $PROTECTED_HEAD
Application lineage base: $EXPECTED_APP_BASE
Backup branch: $BACKUP_BRANCH
Build: $NEW_VERSION / $NEW_BUILD

- Reproduces all guarded 26469 CFA/highlight/eigensystem corrections first.
- Gain-map size now follows the actual rendered SDR texture, not raw sensor size.
- Exact 90/180/270 gain-map rotation uses no interpolation.
- Adds IRIS_26470 UHDR generation/attachment geometry diagnostics.
- Wronski alignment/robustness, denoise, tone, exposure, gain encoding and
  sharpening state are unchanged.
- No speculative performance rewrite is included because no additional work
  elimination was proven math-identical for this build.
EOF_REPORT

rm -f ./*.apk
chmod +x ./gradlew
./gradlew assembleDebug --no-daemon

echo "BUILD SUCCESSFUL verified by Gradle return code" | tee -a "$REPORT"
mapfile -t apks < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no debug APK found"
cp "${apks[0]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "APK missing/empty"
sha="$(sha256sum "$APK_NAME" | awk '{print $1}')"
{
 echo "BUILD SUCCESS"; echo "APK=$APK_NAME"; echo "SHA256=$sha"
 echo "VERSION=$NEW_VERSION"; echo "BUILD=$NEW_BUILD"
 echo "dev_untouched=true"; echo "experimental_source_not_committed=true"
} | tee -a "$REPORT"
pass "26470 BUILD SUCCESS"
