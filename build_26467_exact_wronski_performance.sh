#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_BASE="67df2ede5084df503e941e3453409c6243950a10"
BACKUP_BRANCH="backup-26466-before-26467-exact-wronski"
OLD_VERSION="0.9726466"
OLD_BUILD="26466"
NEW_VERSION="0.9726467"
NEW_BUILD="26467"

OUTDIR="build_26467_outputs"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26467_source_audit.txt"
BUILDLOG="$OUTDIR/26467_build_report.txt"
PERF="$OUTDIR/26467_performance_changes.txt"
PATCH="$OUTDIR/26467_pre_edit_binary.patch"
HASH_BEFORE="$OUTDIR/26467_protected_before.sha256"
HASH_AFTER="$OUTDIR/26467_protected_after.sha256"

exec > >(tee "$AUDIT") 2>&1

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

echo "=== 26467 GUARDED EXACT WRONSKI / OUTPUT ROUTING / PERFORMANCE BUILD ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
pass "branch gate"

git cat-file -e "$EXPECTED_BASE^{commit}" || fail "missing expected base commit"
BASE_TREE="$(git rev-parse "$EXPECTED_BASE^{tree}")"
echo "base=$EXPECTED_BASE tree=$BASE_TREE"

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$EXPECTED_BASE" ]] || fail "backup branch mismatch: $REMOTE_BACKUP"
pass "backup branch exact 26466"

git diff --quiet "$EXPECTED_BASE" -- app/src/main app/version.properties \
  || fail "application source differs from exact 26466 before edit"
pass "application source exact 26466"

grep -q '^VERSION_NAME=0\.9726466$' app/version.properties || fail "VERSION_NAME gate"
grep -q '^VERSION_BUILD=26466$' app/version.properties || fail "VERSION_BUILD gate"
pass "version gate 0.9726466 / 26466"

ALIGN="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
VERSION="app/version.properties"

[[ "$(git hash-object "$ALIGN")" == "2e57b00c26d85f0fadf51a67cad2aa4c12289237" ]] || fail "alignment blob gate"
[[ "$(git hash-object "$RECON")" == "7627cc560254579bfd621f7db56c69eddbc28bd2" ]] || fail "reconstruction blob gate"
[[ "$(git hash-object "$HDRX")" == "e7178e444589164535c837a9297f92e3ae3b63ae" ]] || fail "HdrxProcessor blob gate"
[[ "$(git hash-object "$VERSION")" == "a51a104219a3dd384378802017abf52109c63f16" ]] || fail "version blob gate"
pass "exact critical blob gates"

for marker in \
  IRIS_26462_WRONSKI_PUBLISHED_COARSE_TO_FINE_ALIGNMENT \
  IRIS_26463_WRONSKI_PUBLIC_ROBUSTNESS_GEOMETRY \
  IRIS_26463_WRONSKI_PUBLIC_SIGNAL_DOMAIN \
  IRIS_26465_REFERENCE_CLIP_PROVENANCE \
  IRIS_26450_MOTION_V2_REFERENCE_DNG
do
  grep -Rqs "$marker" app/src/main || fail "missing lineage marker $marker"
done
pass "lineage/ownership markers"

git diff --binary "$EXPECTED_BASE" -- app/src/main app/version.properties > "$PATCH"
cp "$PATCH" "$OUTDIR/26467_pre_edit_binary_recovery.patch"
pass "binary pre-edit patch created"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_BEFORE"
pass "protected-file hashes captured"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/app/src/main/java/com/particlesdevs/photoncamera/processing/processor" "$TMP/app"
cp "$ALIGN" "$TMP/$ALIGN"
cp "$RECON" "$TMP/$RECON"
cp "$HDRX" "$TMP/$HDRX"
cp "$VERSION" "$TMP/$VERSION"

cat > "$TMP/$ALIGN" <<'JAVA'
package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.util.Log;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26462_WRONSKI_PUBLISHED_COARSE_TO_FINE_ALIGNMENT
 * IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE
 *
 * Same published Wronski/IPOL alignment math as 26466. 26467 changes execution
 * only: the immutable reference guide/pyramid is prepared once per burst and
 * reused for every auxiliary frame.
 */
public final class MotionV2WronskiAlignment {
    private static final String TAG = "MotionV2WronskiAlign";
    private MotionV2WronskiAlignment() {}

    private static Point divCeil(Point p, int d) {
        return new Point(
                Math.max(1, (p.x + d - 1) / d),
                Math.max(1, (p.y + d - 1) / d));
    }

    public static final class PreparedReference implements AutoCloseable {
        private final Point rawHalf;
        private final int cfaPattern;
        private final float signalScale;
        private final float snr;
        private GLTexture[] levels;

        private PreparedReference(
                Point rawHalf,
                int cfaPattern,
                float signalScale,
                float snr,
                GLTexture[] levels) {
            this.rawHalf = new Point(rawHalf);
            this.cfaPattern = cfaPattern;
            this.signalScale = signalScale;
            this.snr = snr;
            this.levels = levels;
        }

        @Override
        public void close() {
            if (levels == null) return;
            for (GLTexture t : levels) {
                if (t != null) t.close();
            }
            levels = null;
        }
    }

    private static GLTexture[] buildGuidePyramid(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            GLProg glProg,
            GLTexture cfa) {
        final int[] stepFactor = new int[] {1, 2, 4, 4};
        GLTexture[] guide = new GLTexture[4];
        try {
            guide[0] = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);

            glProg.setDefine("CFAPATTERN", cfaPattern);
            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/alignment_guide", true);
            glProg.setVar("guideScale", 1);
            glProg.setVar("signalScale", Math.max(signalScale,1.0e-6f));
            glProg.setTexture("InputCfa", cfa);
            glProg.setTextureCompute("OutputGuide", guide[0], true);
            glProg.computeAuto(rawHalf,1);

            Point prev = rawHalf;
            for (int l=1;l<4;l++) {
                Point levelSize = divCeil(prev, stepFactor[l]);
                guide[l] = new GLTexture(
                        levelSize,
                        new GLFormat(GLFormat.DataType.FLOAT_32,1),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_pyramid_down", true);
                glProg.setVar("factor", stepFactor[l]);
                glProg.setTexture("InputGuide", guide[l-1]);
                glProg.setTextureCompute("OutputGuide", guide[l], true);
                glProg.computeAuto(levelSize,1);
                prev = levelSize;
            }
            return guide;
        } catch (Throwable t) {
            for (GLTexture texture : guide) {
                if (texture != null) {
                    try { texture.close(); } catch (Throwable ignored) {}
                }
            }
            throw t;
        }
    }

    public static PreparedReference prepareReference(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            float snr,
            GLProg glProg,
            GLTexture referenceCfa) {
        long start = System.currentTimeMillis();
        GLTexture[] ref = buildGuidePyramid(
                rawHalf, cfaPattern, signalScale, glProg, referenceCfa);
        Log.d(TAG,
                "IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE"
                + " elapsedMs=" + (System.currentTimeMillis() - start)
                + " levels=4"
                + " reusedAcrossAuxiliaries=true");
        return new PreparedReference(
                rawHalf, cfaPattern, signalScale, snr, ref);
    }

    public static MotionV2Alignment.Result alignPrepared(
            PreparedReference prepared,
            GLProg glProg,
            GLTexture alterCfa) {
        if (prepared == null || prepared.levels == null) {
            throw new IllegalStateException("Wronski prepared reference is closed");
        }

        final Point rawHalf = prepared.rawHalf;
        final float snr = prepared.snr;
        final int baseTile = snr <= 14.0f ? 64 : (snr <= 22.0f ? 32 : 16);
        final int[] tile = new int[] {
                baseTile, baseTile, baseTile, Math.max(8, baseTile / 2)
        };
        final int[] radius = new int[] {1, 4, 4, 4};
        final int[] metric = new int[] {0, 1, 1, 1};
        final int[] stepFactor = new int[] {1, 2, 4, 4};

        GLTexture[] ref = prepared.levels;
        GLTexture[] alt = null;
        GLTexture previousFlow = null;
        GLTexture denseFlow = null;

        try {
            alt = buildGuidePyramid(
                    rawHalf,
                    prepared.cfaPattern,
                    prepared.signalScale,
                    glProg,
                    alterCfa);

            Point[] levelSize = new Point[4];
            levelSize[0] = rawHalf;
            for (int l=1;l<4;l++) {
                levelSize[l] = divCeil(levelSize[l-1], stepFactor[l]);
            }

            for (int l=3;l>=0;l--) {
                Point grid = new Point(
                        Math.max(1,(levelSize[l].x + tile[l]-1)/tile[l]),
                        Math.max(1,(levelSize[l].y + tile[l]-1)/tile[l]));

                GLTexture block = new GLTexture(
                        grid,
                        new GLFormat(GLFormat.DataType.FLOAT_16,4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                GLTexture refined = new GLTexture(
                        grid,
                        new GLFormat(GLFormat.DataType.FLOAT_16,4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_block_match", true);
                glProg.setVar("levelSize", levelSize[l]);
                glProg.setVar("tileSize", tile[l]);
                glProg.setVar("searchRadius", radius[l]);
                glProg.setVar("distanceMetric", metric[l]);
                glProg.setVar("hasPrevious", previousFlow != null ? 1 : 0);
                glProg.setVar(
                        "previousToCurrentScale",
                        l < 3 ? (float)stepFactor[l+1] : 1.0f);
                glProg.setTexture("ReferenceGuide", ref[l]);
                glProg.setTexture("MovingGuide", alt[l]);
                glProg.setTexture(
                        "PreviousFlow",
                        previousFlow != null ? previousFlow : ref[l]);
                glProg.setTextureCompute("OutputFlow", block, true);
                glProg.computeAuto(grid,1);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_ica_refine", true);
                glProg.setVar("levelSize", levelSize[l]);
                glProg.setVar("tileSize", tile[l]);
                glProg.setVar("iterations", 3);
                glProg.setTexture("ReferenceGuide", ref[l]);
                glProg.setTexture("MovingGuide", alt[l]);
                glProg.setTexture("BlockFlow", block);
                glProg.setTextureCompute("OutputFlow", refined, true);
                glProg.computeAuto(grid,1);

                block.close();
                if (previousFlow != null) previousFlow.close();
                previousFlow = refined;
            }

            denseFlow = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_16,4),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);

            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/mfsr_flow_expand", true);
            glProg.setVar("outputSize", rawHalf);
            glProg.setVar("tileSize", baseTile);
            glProg.setTexture("TileFlow", previousFlow);
            glProg.setTextureCompute("OutputFlow", denseFlow, true);
            glProg.computeAuto(rawHalf,1);

            Log.d(TAG,
                    "IRIS_26462_WRONSKI_PUBLISHED_ALIGNMENT"
                    + " snr=" + snr
                    + " baseTile=" + baseTile
                    + " factors=1,2,4,4"
                    + " radii=1,4,4,4"
                    + " metrics=L1,L2,L2,L2"
                    + " icaIterations=3"
                    + " flowUpscale=nearest"
                    + " subpixelFromICA=true"
                    + " referencePreparedOnce=true");

            GLTexture keep = denseFlow;
            denseFlow = null;
            return new MotionV2Alignment.Result(
                    keep,0.0f,0.0f,1.0f,0.0f);
        } finally {
            if (denseFlow != null) denseFlow.close();
            if (previousFlow != null) previousFlow.close();
            if (alt != null) {
                for (GLTexture t : alt) {
                    if (t != null) t.close();
                }
            }
        }
    }

    public static MotionV2Alignment.Result align(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            float snr,
            GLProg glProg,
            GLTexture referenceCfa,
            GLTexture alterCfa) {
        try (PreparedReference prepared = prepareReference(
                rawHalf, cfaPattern, signalScale, snr, glProg, referenceCfa)) {
            return alignPrepared(prepared, glProg, alterCfa);
        }
    }
}
JAVA

python3 - "$TMP" <<'PY'
from pathlib import Path
import sys

tmp = Path(sys.argv[1])
recon = tmp / "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
hdrx = tmp / "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
version = tmp / "app/version.properties"

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly 1 anchor, found {n}")
    return text.replace(old, new, 1)

t = hdrx.read_text()
old = '''            /*
             * IRIS_26450_MOTION_V2_REFERENCE_DNG
             * Save the true timestamp-owned Bayer reference while its original
             * RAW buffer is still alive. This is single-frame sensor RAW:
             * no multiframe NR, no demosaic, no V2 RGB processing.
             */
            ByteBuffer iris26450ReferenceDng =
                    images.get(0).buffer == null
                            ? null
                            : images.get(0).buffer.duplicate();
            if (iris26450ReferenceDng == null) {
                throw new IllegalStateException(
                        "Motion V2 reference DNG buffer is null");
            }
            iris26450ReferenceDng.position(0);
            boolean iris26450DngSaved =
                    ImageSaver.Util.saveStackedRaw(
                            dngFile,
                            iris26450ReferenceDng,
                            processingParameters);
            processingEventsListener.notifyImageSavedStatus(
                    iris26450DngSaved,
                    dngFile);
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26450_MOTION_V2_REFERENCE_DNG",
                    "saved=" + iris26450DngSaved
                            + " rawTimestamp=" + images.get(0).timestamp
                            + " source=timestampOwnedReferenceBayer"
                            + " multiframeNr=false"
                            + " bakedRgb=false");
'''
new = '''            /*
             * IRIS_26467_MOTION_OUTPUT_MODE_AUTHORITY
             * Motion obeys the same user JPG / RAW / JPG+RAW selection as
             * the rest of Photon. The 26450 timestamp-owned reference DNG is
             * preserved only when saveRAW requests RAW output.
             */
            if (saveRAW >= 1) {
                ByteBuffer iris26450ReferenceDng =
                        images.get(0).buffer == null
                                ? null
                                : images.get(0).buffer.duplicate();
                if (iris26450ReferenceDng == null) {
                    throw new IllegalStateException(
                            "Motion V2 reference DNG buffer is null");
                }
                iris26450ReferenceDng.position(0);
                boolean iris26450DngSaved =
                        ImageSaver.Util.saveStackedRaw(
                                dngFile,
                                iris26450ReferenceDng,
                                processingParameters);
                processingEventsListener.notifyImageSavedStatus(
                        iris26450DngSaved,
                        dngFile);
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26450_MOTION_V2_REFERENCE_DNG",
                        "saved=" + iris26450DngSaved
                                + " rawTimestamp=" + images.get(0).timestamp
                                + " source=timestampOwnedReferenceBayer"
                                + " multiframeNr=false"
                                + " bakedRgb=false"
                                + " userSaveRaw=" + saveRAW);

                if (saveRAW == 2) {
                    for (ImageFrame image : images) {
                        if (image != null) image.close();
                    }
                    processingEventsListener.onProcessingFinished(
                            "Motion RAW Processing Finished");
                    callback.onFinished();
                    return;
                }
            } else {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26467_MOTION_OUTPUT_MODE_AUTHORITY",
                        "userSaveRaw=0 referenceDngSaved=false jpegRequested=true");
            }
'''
t = replace_once(t, old, new, "Hdrx Motion DNG block")
hdrx.write_text(t)

t = recon.read_text()
t = replace_once(
    t,
    '''        GLTexture wronskiReferenceCfa = null;
        GLTexture wronskiReferenceCov = null;
''',
    '''        GLTexture wronskiReferenceCfa = null;
        GLTexture wronskiReferenceCov = null;
        MotionV2WronskiAlignment.PreparedReference wronskiPreparedAlignment = null;
''',
    "prepared reference declaration")

t = replace_once(
    t,
    '''            mergedA = new GLTexture(
''',
    '''            if (directBayer) {
                /*
                 * IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE
                 * Reference geometry is immutable for this burst. Prepare its
                 * guide/pyramid once instead of rebuilding it for every
                 * auxiliary frame.
                 */
                wronskiPreparedAlignment =
                        MotionV2WronskiAlignment.prepareReference(
                                rawHalf,
                                parameters.cfaPattern,
                                canonicalGain,
                                mfsrSnr,
                                glProg,
                                wronskiReferenceCfa);
            }

            mergedA = new GLTexture(
''',
    "prepared reference initialization")

old_align = '''                        long alignmentStart = System.currentTimeMillis();
                        ownedAlignment =
                                directBayer
                                        ? MotionV2WronskiAlignment.align(
                                                rawHalf,
                                                parameters.cfaPattern,
                                                canonicalGain,
                                                mfsrSnr,
                                                glProg,
                                                wronskiReferenceCfa,
                                                wronskiAlterCfa)
                                        : MotionV2Alignment.align(
                                                rawHalf,
                                                parameters.cfaPattern,
                                                canonicalGain,
                                                glProg,
                                                referenceCfa,
                                                alterCfa);
'''
new_align = '''                        long frameProcessingStart = System.currentTimeMillis();
                        long alignmentOnlyStart = System.currentTimeMillis();
                        ownedAlignment =
                                directBayer
                                        ? MotionV2WronskiAlignment.alignPrepared(
                                                wronskiPreparedAlignment,
                                                glProg,
                                                wronskiAlterCfa)
                                        : MotionV2Alignment.align(
                                                rawHalf,
                                                parameters.cfaPattern,
                                                canonicalGain,
                                                glProg,
                                                referenceCfa,
                                                alterCfa);
                        long alignmentOnlyMs =
                                System.currentTimeMillis() - alignmentOnlyStart;
'''
t = replace_once(t, old_align, new_align, "alignment call")

t = replace_once(
    t,
    '''                                + (System.currentTimeMillis()-alignmentStart)
                                + " globalDxPacked="
''',
    '''                                + (System.currentTimeMillis()-frameProcessingStart)
                                + " alignmentOnlyMs=" + alignmentOnlyMs
                                + " referencePreparedOnce=" + directBayer
                                + " globalDxPacked="
''',
    "frame timing log")

t = replace_once(
    t,
    '''            if (wronskiReferenceCov != null) wronskiReferenceCov.close();
            if (wronskiReferenceCfa != null) wronskiReferenceCfa.close();
''',
    '''            if (wronskiReferenceCov != null) wronskiReferenceCov.close();
            if (wronskiPreparedAlignment != null) wronskiPreparedAlignment.close();
            if (wronskiReferenceCfa != null) wronskiReferenceCfa.close();
''',
    "prepared reference cleanup")

recon.write_text(t)

v = version.read_text()
v = replace_once(v, "VERSION_NAME=0.9726466", "VERSION_NAME=0.9726467", "VERSION_NAME")
v = replace_once(v, "VERSION_BUILD=26466", "VERSION_BUILD=26467", "VERSION_BUILD")
version.write_text(v)
PY

grep -q 'IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE' "$TMP/$ALIGN" || fail "candidate alignment marker"
grep -q 'class PreparedReference' "$TMP/$ALIGN" || fail "candidate PreparedReference"
grep -q 'alignPrepared' "$TMP/$ALIGN" || fail "candidate alignPrepared"
grep -q 'IRIS_26467_MOTION_OUTPUT_MODE_AUTHORITY' "$TMP/$HDRX" || fail "candidate output authority"
grep -q 'if (saveRAW >= 1)' "$TMP/$HDRX" || fail "candidate RAW gate"
grep -q 'MotionV2WronskiAlignment.prepareReference' "$TMP/$RECON" || fail "candidate reference prepare call"
grep -q 'MotionV2WronskiAlignment.alignPrepared' "$TMP/$RECON" || fail "candidate prepared align call"
grep -q '^VERSION_NAME=0\.9726467$' "$TMP/$VERSION" || fail "candidate version name"
grep -q '^VERSION_BUILD=26467$' "$TMP/$VERSION" || fail "candidate version build"
pass "candidate/source validation PASS"

python3 - "$TMP" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
files=[
root/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java",
root/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
root/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java",
]
for p in files:
    s=p.read_text()
    if s.count("{") != s.count("}"):
        raise SystemExit(f"brace count mismatch in {p}: {s.count('{')} vs {s.count('}')}")
print("Temporary-copy validation: PASS")
PY
pass "Temporary-copy validation: PASS"

cp "$TMP/$ALIGN" "$ALIGN"
cp "$TMP/$RECON" "$RECON"
cp "$TMP/$HDRX" "$HDRX"
cp "$TMP/$VERSION" "$VERSION"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
python3 - "$HASH_BEFORE" "$HASH_AFTER" "$ALIGN" "$RECON" "$HDRX" <<'PY'
from pathlib import Path
import sys

before, after = map(Path, sys.argv[1:3])
changed = {str(Path(x)) for x in sys.argv[3:]}

def load(path):
    d={}
    for line in path.read_text().splitlines():
        h,p=line.split("  ",1)
        d[p]=h
    return d

b=load(before); a=load(after)
if set(b) != set(a):
    raise SystemExit("protected-file path set changed unexpectedly")
bad=[]
for p,h in b.items():
    if p in changed:
        continue
    if a[p] != h:
        bad.append(p)
if bad:
    raise SystemExit("protected-file hash mismatch: "+", ".join(bad))
print("Protected-file hashes: PASS")
PY

for marker in \
  IRIS_26465_REFERENCE_CLIP_PROVENANCE \
  IRIS_26463_WRONSKI_PUBLIC_SIGNAL_DOMAIN \
  IRIS_26462_WRONSKI_PUBLISHED_COARSE_TO_FINE_ALIGNMENT \
  IRIS_26450_MOTION_V2_REFERENCE_DNG \
  IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT
do
  grep -Rqs "$marker" app/src/main || fail "post-edit lost marker $marker"
done
pass "historical behavior/lineage preservation PASS"

grep -q 'if (saveRAW >= 1)' "$HDRX" || fail "Motion RAW save gate absent"
grep -q 'if (saveRAW == 2)' "$HDRX" || fail "Motion RAW-only stop absent"
grep -q 'referencePreparedOnce=true' "$ALIGN" || fail "reference cache telemetry absent"
grep -q 'alignmentOnlyMs=' "$RECON" || fail "stage timing telemetry absent"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  protected-file hashes PASS"
echo "  exact backup branch PASS"
echo "  version/build increment in same script PASS"

cat > "$PERF" <<EOF
26467 performance / portability changes
=======================================
Base: $EXPECTED_BASE
Build: $NEW_VERSION / $NEW_BUILD

1. Wronski immutable reference guide+pyramid is prepared once per burst.
   26466 rebuilt the same reference guide and 3 downsample levels for every
   auxiliary frame. 26467 retains identical Wronski factors/radii/metrics/ICA
   math but reuses the immutable reference side.

2. Auxiliary guide+pyramid remains per-frame because each auxiliary RAW differs.

3. No Wronski robustness equation, direct-RGB accumulation equation, CFA
   saturation validity math, tone, denoise or sharpening parameter is changed.

4. Per-frame telemetry separates alignmentOnlyMs from total frame elapsedMs.

5. Motion output selection obeys saveRAW:
   saveRAW=0 -> JPEG only, no reference DNG.
   saveRAW=1 -> JPEG + timestamp-owned reference DNG.
   saveRAW=2 -> timestamp-owned reference DNG only, exits before Wronski/JPEG.
EOF

chmod +x ./gradlew
set +e
./gradlew assembleDebug --stacktrace 2>&1 | tee "$BUILDLOG"
GRADLE_STATUS=${PIPESTATUS[0]}
set -e
[[ "$GRADLE_STATUS" -eq 0 ]] || fail "Gradle build failed; see $BUILDLOG"

grep -q 'BUILD SUCCESSFUL' "$BUILDLOG" || fail "BUILD SUCCESSFUL marker missing"

APK="$(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | head -n 1)"
[[ -n "$APK" && -f "$APK" ]] || fail "debug APK not found"

OUTAPK="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-exact-wronski-reference-cache-debug.apk"
cp "$APK" "$OUTAPK"
cp "$OUTAPK" "$OUTDIR/$OUTAPK"

git diff --binary "$EXPECTED_BASE" -- app/src/main app/version.properties \
  > "$OUTDIR/26467_exact_source_changes.patch"

{
  echo
  echo "BUILD SUCCESS"
  echo "APK=$OUTAPK"
  echo "SHA256=$(sha256sum "$OUTAPK" | awk '{print $1}')"
  echo "VERSION=$NEW_VERSION"
  echo "BUILD=$NEW_BUILD"
  echo "dev_untouched=true"
  echo "experimental_source_not_committed=true"
} | tee -a "$BUILDLOG"

pass "26467 BUILD SUCCESS"
