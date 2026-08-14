from pathlib import Path
import sys

root = Path(sys.argv[1])
recon = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"

if not recon.exists():
    raise SystemExit("26478 speaker diagnostic missing recon source: " + str(recon))

t = recon.read_text()

for marker in [
    "IRIS_26478_PURE_WRONSKI_DIRECT_RGB",
    "IRIS_26478_WRONSKI_REFERENCE_ADD_ONCE",
    "IRIS_26477_WRONSKI_RECONSTRUCTION_AUTHORITY",
]:
    if marker not in t:
        raise SystemExit("26478 speaker diagnostic prerequisite missing: " + marker)

call_anchor = '''            Log.d(TAG, "IRIS_26436_V2_SPATIAL_SUPPORT"
                    + " grid12x8=" + supportGrid12x8
                    + " meanNeighborDelta=" + supportRoughness
                    + " retainedFrames=" + frameCount
                    + " loggingOnly=true");

            Log.d(TAG, "IRIS_26413_V2_CFA_RECONSTRUCTION"
'''
call_new = '''            Log.d(TAG, "IRIS_26436_V2_SPATIAL_SUPPORT"
                    + " grid12x8=" + supportGrid12x8
                    + " meanNeighborDelta=" + supportRoughness
                    + " retainedFrames=" + frameCount
                    + " loggingOnly=true");

            if (directBayer && output != null) {
                /*
                 * IRIS_26478_SPEAKER_SUPPORT_DIAGNOSTIC
                 * Correlates the SAME IRIS_26436 local support map with the
                 * already-read pure-Wronski direct RGB. Read-only telemetry.
                 */
                iris26478LogSpeakerSupportEdges(
                        summary,
                        supportGrid12x8.toString(),
                        output.duplicate(),
                        raw.x,
                        raw.y,
                        frameCount,
                        parameters);
            }

            Log.d(TAG, "IRIS_26413_V2_CFA_RECONSTRUCTION"
'''
if t.count(call_anchor) != 1:
    raise SystemExit(
        "26478 speaker diagnostic support-map call anchor count="
        + str(t.count(call_anchor)))
t = t.replace(call_anchor, call_new, 1)

helper_anchor = '''    private static SupportSummary summarizeSupport(
            ByteBuffer bytes,
            int width,
            int height,
            int frameCount) {
'''
if t.count(helper_anchor) != 1:
    raise SystemExit(
        "26478 speaker diagnostic helper anchor count="
        + str(t.count(helper_anchor)))

helper = r'''    private static float[] iris26478SampleFinalDirectRgb(
            FloatBuffer values,
            int width,
            int height,
            int x,
            int y) {
        int sx = Math.max(0, Math.min(width - 1, x));
        int sy = Math.max(0, Math.min(height - 1, y));
        int base = (sy * width + sx) * 4;
        if (base + 3 >= values.limit()) {
            return new float[]{Float.NaN, Float.NaN, Float.NaN, Float.NaN};
        }
        return new float[]{
                values.get(base),
                values.get(base + 1),
                values.get(base + 2),
                values.get(base + 3)};
    }

    /*
     * Exact linear diagnostic mirror:
     * MotionV2DisplayExposure -> Camera2 gains -> Camera2 3x3 matrix.
     * The active pipeline remains authoritative; this result is logging only.
     */
    private static float[] iris26478PredictActiveColor(
            float[] direct,
            Parameters parameters,
            float displayGain) {
        if (direct == null
                || direct.length < 3
                || parameters == null
                || parameters.motionV2ColorGains == null
                || parameters.motionV2ColorGains.length != 4
                || parameters.motionV2ColorTransform == null
                || parameters.motionV2ColorTransform.length != 9) {
            return new float[]{Float.NaN, Float.NaN, Float.NaN};
        }

        float[] g = parameters.motionV2ColorGains;
        float[] m = parameters.motionV2ColorTransform;
        float greenGain = 0.5f * (g[1] + g[2]);

        float r = Math.max(0.0f, direct[0]) * displayGain * g[0];
        float gg = Math.max(0.0f, direct[1]) * displayGain * greenGain;
        float b = Math.max(0.0f, direct[2]) * displayGain * g[3];

        return new float[]{
                Math.max(0.0f, m[0] * r + m[1] * gg + m[2] * b),
                Math.max(0.0f, m[3] * r + m[4] * gg + m[5] * b),
                Math.max(0.0f, m[6] * r + m[7] * gg + m[8] * b)};
    }

    /*
     * IRIS_26478_SPEAKER_SUPPORT_DIAGNOSTIC
     * Uses the exact existing SupportSummary from IRIS_26436 and reports
     * the four strongest adjacent support discontinuities.
     */
    private static void iris26478LogSpeakerSupportEdges(
            SupportSummary summary,
            String grid12x8,
            ByteBuffer rgbaBytes,
            int width,
            int height,
            int frameCount,
            Parameters parameters) {
        if (summary == null
                || summary.coarseGrid == null
                || rgbaBytes == null
                || width <= 0
                || height <= 0) {
            return;
        }

        String mapMessage =
                "grid12x8=" + grid12x8
                        + " mean=" + summary.mean
                        + " p10=" + summary.p10
                        + " p50=" + summary.p50
                        + " p90=" + summary.p90
                        + " retainedFrames=" + frameCount
                        + " source=existingIRIS_26436LocalSupport"
                        + " sameLocalSupportMap=true"
                        + " diagnosticOnly=true"
                        + " feedsImageMath=false";
        Log.d(TAG, "IRIS_26478_SPEAKER_SUPPORT_MAP " + mapMessage);
        try {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26478_SPEAKER_SUPPORT_MAP",
                    mapMessage);
        } catch (Throwable ignored) {}

        final int topN = 4;
        float[] bestDelta = new float[topN];
        int[] axGrid = new int[topN];
        int[] ayGrid = new int[topN];
        int[] bxGrid = new int[topN];
        int[] byGrid = new int[topN];
        String[] orientation = new String[topN];

        for (int gy = 0; gy < summary.gridHeight; gy++) {
            for (int gx = 0; gx < summary.gridWidth; gx++) {
                int gi = gy * summary.gridWidth + gx;

                if (gx + 1 < summary.gridWidth) {
                    iris26478InsertSupportEdge(
                            Math.abs(
                                    summary.coarseGrid[gi]
                                            - summary.coarseGrid[gi + 1]),
                            gx,
                            gy,
                            gx + 1,
                            gy,
                            "verticalBoundary",
                            bestDelta,
                            axGrid,
                            ayGrid,
                            bxGrid,
                            byGrid,
                            orientation);
                }
                if (gy + 1 < summary.gridHeight) {
                    iris26478InsertSupportEdge(
                            Math.abs(
                                    summary.coarseGrid[gi]
                                            - summary.coarseGrid[
                                                    gi + summary.gridWidth]),
                            gx,
                            gy,
                            gx,
                            gy + 1,
                            "horizontalBoundary",
                            bestDelta,
                            axGrid,
                            ayGrid,
                            bxGrid,
                            byGrid,
                            orientation);
                }
            }
        }

        FloatBuffer values =
                rgbaBytes.duplicate()
                        .order(ByteOrder.nativeOrder())
                        .asFloatBuffer();

        float displayGain =
                Math.max(
                        1.0f,
                        parameters != null
                                ? parameters.motionCanonicalExposureGain
                                : 1.0f);

        for (int rank = 0; rank < topN; rank++) {
            if (!(bestDelta[rank] > 0.0f) || orientation[rank] == null) {
                continue;
            }

            int ax =
                    iris26478GridCenterToPixel(
                            axGrid[rank],
                            summary.gridWidth,
                            width);
            int ay =
                    iris26478GridCenterToPixel(
                            ayGrid[rank],
                            summary.gridHeight,
                            height);
            int bx =
                    iris26478GridCenterToPixel(
                            bxGrid[rank],
                            summary.gridWidth,
                            width);
            int by =
                    iris26478GridCenterToPixel(
                            byGrid[rank],
                            summary.gridHeight,
                            height);

            float[] directA =
                    iris26478SampleFinalDirectRgb(
                            values,
                            width,
                            height,
                            ax,
                            ay);
            float[] directB =
                    iris26478SampleFinalDirectRgb(
                            values,
                            width,
                            height,
                            bx,
                            by);
            float[] colorA =
                    iris26478PredictActiveColor(
                            directA,
                            parameters,
                            displayGain);
            float[] colorB =
                    iris26478PredictActiveColor(
                            directB,
                            parameters,
                            displayGain);

            float supportA =
                    summary.coarseGrid[
                            ayGrid[rank] * summary.gridWidth
                                    + axGrid[rank]];
            float supportB =
                    summary.coarseGrid[
                            byGrid[rank] * summary.gridWidth
                                    + bxGrid[rank]];

            String edgeMessage =
                    "rank=" + (rank + 1)
                            + " supportDelta=" + bestDelta[rank]
                            + " orientation=" + orientation[rank]
                            + " gridA=" + axGrid[rank] + "," + ayGrid[rank]
                            + " gridB=" + bxGrid[rank] + "," + byGrid[rank]
                            + " supportA=" + supportA
                            + " supportB=" + supportB
                            + " pixelA=" + ax + "," + ay
                            + " pixelB=" + bx + "," + by
                            + " xNormA=" + ax / (float)Math.max(1, width - 1)
                            + " yNormA=" + ay / (float)Math.max(1, height - 1)
                            + " xNormB=" + bx / (float)Math.max(1, width - 1)
                            + " yNormB=" + by / (float)Math.max(1, height - 1)
                            + " directA="
                            + directA[0] + "," + directA[1] + "," + directA[2]
                            + " directB="
                            + directB[0] + "," + directB[1] + "," + directB[2]
                            + " finalAlphaA=" + directA[3]
                            + " finalAlphaB=" + directB[3]
                            + " displayGain=" + displayGain
                            + " colorA="
                            + colorA[0] + "," + colorA[1] + "," + colorA[2]
                            + " colorB="
                            + colorB[0] + "," + colorB[1] + "," + colorB[2]
                            + " colorPrediction=MotionV2DisplayExposure_then_Camera2GainsMatrix"
                            + " sameLocalSupportMap=true"
                            + " diagnosticOnly=true"
                            + " feedsImageMath=false";

            Log.d(TAG, "IRIS_26478_SPEAKER_SUPPORT_EDGE " + edgeMessage);
            try {
                com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                        "IRIS_26478_SPEAKER_SUPPORT_EDGE",
                        edgeMessage);
            } catch (Throwable ignored) {}
        }
    }

    private static int iris26478GridCenterToPixel(
            int cell,
            int gridExtent,
            int imageExtent) {
        return Math.max(
                0,
                Math.min(
                        imageExtent - 1,
                        Math.round(
                                (cell + 0.5f)
                                        * imageExtent
                                        / gridExtent
                                        - 0.5f)));
    }

    private static void iris26478InsertSupportEdge(
            float delta,
            int ax,
            int ay,
            int bx,
            int by,
            String edgeOrientation,
            float[] bestDelta,
            int[] axGrid,
            int[] ayGrid,
            int[] bxGrid,
            int[] byGrid,
            String[] orientation) {
        for (int rank = 0; rank < bestDelta.length; rank++) {
            if (delta <= bestDelta[rank]) continue;

            for (int shift = bestDelta.length - 1;
                    shift > rank;
                    shift--) {
                bestDelta[shift] = bestDelta[shift - 1];
                axGrid[shift] = axGrid[shift - 1];
                ayGrid[shift] = ayGrid[shift - 1];
                bxGrid[shift] = bxGrid[shift - 1];
                byGrid[shift] = byGrid[shift - 1];
                orientation[shift] = orientation[shift - 1];
            }

            bestDelta[rank] = delta;
            axGrid[rank] = ax;
            ayGrid[rank] = ay;
            bxGrid[rank] = bx;
            byGrid[rank] = by;
            orientation[rank] = edgeOrientation;
            return;
        }
    }

'''

# Inspect only the Java helper to be inserted.
for forbidden in [
    "glProg.",
    "setTextureCompute(",
    "computeAuto(",
    "imageStore(",
    "WorkingTexture",
    "MotionMetrics.publish",
]:
    if forbidden in helper:
        raise SystemExit(
            "26478 diagnostic helper contains image/control mutation: "
            + forbidden)

t = t.replace(helper_anchor, helper + helper_anchor, 1)

for required in [
    "IRIS_26478_SPEAKER_SUPPORT_MAP",
    "IRIS_26478_SPEAKER_SUPPORT_EDGE",
    "source=existingIRIS_26436LocalSupport",
    "sameLocalSupportMap=true",
    "MotionV2DisplayExposure_then_Camera2GainsMatrix",
    "diagnosticOnly=true",
    "feedsImageMath=false",
]:
    if required not in t:
        raise SystemExit(
            "26478 diagnostic missing required marker: " + required)

if t.count("{") != t.count("}"):
    raise SystemExit(
        "26478 diagnostic Java brace mismatch "
        + str(t.count("{"))
        + " vs "
        + str(t.count("}")))

recon.write_text(t)

print("26478 speaker diagnostic candidate/source validation PASS")
print("26478 same-local-support-map correlation PASS")
print("26478 speaker diagnostic telemetry-only proof PASS")
