#!/usr/bin/env python3
from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")

CAP = root / "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
COLOR_JAVA = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java"
COLOR_GLSL = root / "app/src/main/assets/shaders/motionv2/color_transform.glsl"
RECON = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
VER = root / "app/version.properties"

for p in (CAP, COLOR_JAVA, COLOR_GLSL, RECON, VER):
    if not p.exists():
        raise SystemExit("26481 missing path: " + str(p))

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: anchor count={n}")
    return text.replace(old, new, 1)

def regex_once(text, pattern, repl, label, flags=re.S):
    out, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"{label}: regex count={n}")
    return out

# 1. Exact Camera2 timestamp ownership.
t = CAP.read_text()

old_method = r'''    private TotalCaptureResult findNearestZslResult(long timestamp) {
        synchronized (mZslBufferLock) {
            TotalCaptureResult exact = mZslResultMap.get(timestamp);
            if (exact != null) return exact;
            long bestDelta = Long.MAX_VALUE;
            TotalCaptureResult best = null;
            for (Map.Entry<Long, TotalCaptureResult> entry : mZslResultMap.entrySet()) {
                long delta = Math.abs(entry.getKey() - timestamp);
                if (delta < bestDelta) {
                    bestDelta = delta;
                    best = entry.getValue();
                }
            }
            return bestDelta <= 40_000_000L ? best : null;
        }
    }
'''
new_method = r'''    /*
     * IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP
     *
     * Camera2 RAW Image timestamps are capture identities. A neighboring result
     * must never be substituted merely because it is within one frame interval.
     */
    private TotalCaptureResult findNearestZslResult(long timestamp) {
        synchronized (mZslBufferLock) {
            TotalCaptureResult exact = mZslResultMap.get(timestamp);
            if (exact == null) {
                Log.w(TAG, "IRIS_26481_EXACT_TIMESTAMP_MISS"
                        + " rawTimestamp=" + timestamp
                        + " neighborFallback=false");
            }
            return exact;
        }
    }
'''
if old_method in t:
    t = t.replace(old_method, new_method, 1)
else:
    t = regex_once(
        t,
        r'''    private TotalCaptureResult findNearestZslResult\(long timestamp\) \{.*?
            return bestDelta <= 40_000_000L \? best : null;\s*
        \}\s*
    \}''',
        new_method.rstrip(),
        "exact timestamp method",
        flags=re.S | re.X,
    )

field_anchor = "    private static final long MOTION_26480_SHORT_WAIT_MS = 650L;\n"
field_new = field_anchor + (
    "    private static final long MOTION_26481_TIMESTAMP_MATCH_TOLERANCE_NS = 2_000_000L;\n"
)
t = replace_once(t, field_anchor, field_new, "26481 timestamp tolerance field")

count_40 = t.count("<= 40_000_000L")
if count_40 != 2:
    raise SystemExit(f"expected exactly 2 remaining 40ms short-frame matches, found {count_40}")
t = t.replace(
    "<= 40_000_000L",
    "<= MOTION_26481_TIMESTAMP_MATCH_TOLERANCE_NS",
)

t = replace_once(
    t,
    '                    + " normalWronskiStillAvailable=true");',
    '                    + " timestampToleranceNs=" + MOTION_26481_TIMESTAMP_MATCH_TOLERANCE_NS\n'
    '                    + " normalWronskiStillAvailable=true");',
    "short timeout timestamp proof",
)
t = replace_once(
    t,
    '                        + " excludedFromNormalExposureGroup=true");',
    '                        + " timestampToleranceNs=" + MOTION_26481_TIMESTAMP_MATCH_TOLERANCE_NS\n'
    '                        + " excludedFromNormalExposureGroup=true");',
    "short transported timestamp proof",
)
CAP.write_text(t)

# 2. Domain-correct clipping immediately before Camera2 WB/matrix.
COLOR_JAVA.write_text(r'''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26481_BJZHOU_DOMAIN_CORRECT_HIGHLIGHT_COLOR
 *
 * Camera2 WB/matrix remains the color authority. Sensor clipping is handled
 * immediately before WB because clipped camera-RGB values no longer contain a
 * trustworthy channel ratio. WB gains are calculation-only for the repair.
 */
public final class MotionV2ColorTransform extends Node {
    public MotionV2ColorTransform() { super("", "MotionV2ColorTransform"); }
    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException("MotionV2ColorTransform outside Motion V2");
        }
        if (!basePipeline.mParameters.motionV2DirectColorValid) {
            throw new IllegalStateException(
                    "Motion V2 requires direct Camera2 COLOR_CORRECTION_GAINS + TRANSFORM");
        }

        float[] g = basePipeline.mParameters.motionV2ColorGains;
        float[] m = basePipeline.mParameters.motionV2ColorTransform;
        if (g == null || g.length != 4 || m == null || m.length != 9) {
            throw new IllegalStateException("Invalid Motion V2 direct color metadata dimensions");
        }

        float greenGain = 0.5f * (g[1] + g[2]);
        float sensorClipLevel = Math.max(
                1.0f, basePipeline.mParameters.motionCanonicalExposureGain);

        glProg.useAssetProgram("motionv2/color_transform");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("sensorGains", new float[]{g[0], greenGain, g[3]});
        glProg.setVar("sensorClipLevel", sensorClipLevel);
        glProg.setVar("colorRow0", new float[]{m[0],m[1],m[2]});
        glProg.setVar("colorRow1", new float[]{m[3],m[4],m[5]});
        glProg.setVar("colorRow2", new float[]{m[6],m[7],m[8]});

        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26481_BJZHOU_DOMAIN_CORRECT_HIGHLIGHT_COLOR"
                + " gainsRGeGoB=" + java.util.Arrays.toString(g)
                + " greenMean=" + greenGain
                + " matrixRowMajor=" + java.util.Arrays.toString(m)
                + " sensorClipLevel=" + sensorClipLevel
                + " camera2ColorAuthority=true"
                + " repairBeforeWbMatrix=true"
                + " wbCalculationOnly=true"
                + " fullClipHueAuthority=false"
                + " partialRepairRequiresReliablePair=true"
                + " spatialHueDonor=false"
                + " broadDesaturation=false"
                + " maxRgbToneGuideAlready26480=true");
    }
}
''')

COLOR_GLSL.write_text(r'''precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform vec3 sensorGains;
uniform float sensorClipLevel;
uniform vec3 colorRow0;
uniform vec3 colorRow1;
uniform vec3 colorRow2;
out vec3 Output;

float max3(vec3 v) { return max(v.r, max(v.g, v.b)); }
float min3(vec3 v) { return min(v.r, min(v.g, v.b)); }

/*
 * IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR
 *
 * Ordinary pixels:
 *   camera RGB -> Camera2 WB -> Camera2 3x3
 *
 * Near physical sensor clipping:
 *   camera RGB -> temporary WB-balanced calculation domain
 *   -> repair only lost sensor-channel evidence
 *   -> Camera2 3x3
 *
 * There is no neighborhood hue import and no generic highlight desaturation.
 */
void main() {
    ivec2 xy = ivec2(gl_FragCoord.xy);
    vec3 cameraRgb = max(texelFetch(InputBuffer, xy, 0).rgb, vec3(0.0));

    vec3 gains = max(sensorGains, vec3(1.0e-6));
    float clip = max(sensorClipLevel, 1.0e-6);
    vec3 sensorRelative = cameraRgb / clip;

    vec3 channelLoss = smoothstep(vec3(0.940), vec3(0.995), sensorRelative);
    vec3 reliable = vec3(1.0) - channelLoss;
    float reliableSupport = reliable.r + reliable.g + reliable.b;

    // White balance is used only as a calculation domain.
    vec3 balancedMeasured = cameraRgb * gains;
    float reliableMean = dot(balancedMeasured, reliable)
            / max(reliableSupport, 1.0e-6);

    // Partial repair requires at least two reliable channels that agree.
    vec3 reliableDeviation =
            abs(balancedMeasured - vec3(reliableMean)) * reliable;
    float reliableSpread = max3(reliableDeviation)
            / max(reliableMean, 1.0e-6);
    float reliablePair = smoothstep(1.35, 1.90, reliableSupport);
    float neutralPairAgreement =
            1.0 - smoothstep(0.08, 0.28, reliableSpread);

    float allChannelsNearClip =
            smoothstep(0.970, 0.997, min3(sensorRelative));
    float partialRepairGate =
            reliablePair * neutralPairAgreement * (1.0 - allChannelsNearClip);

    vec3 repairedBalanced = mix(
            balancedMeasured,
            vec3(reliableMean),
            channelLoss * partialRepairGate);

    // Once all physical channels clip, hue is not observable.
    float terminalNeutral = max3(balancedMeasured);
    repairedBalanced = mix(
            repairedBalanced,
            vec3(terminalNeutral),
            allChannelsNearClip);

    vec3 linearSrgb = vec3(
            dot(colorRow0, repairedBalanced),
            dot(colorRow1, repairedBalanced),
            dot(colorRow2, repairedBalanced));

    Output = max(linearSrgb, vec3(0.0));
}
''')

# 3. Total Wronski wall timing; detailed 26468 per-frame timing stays intact.
t = RECON.read_text()
sig_pattern = r'''(public static MotionV2Merger\.Result reconstruct\(
\s*Point size,
\s*List<ImageFrame> inputImages,
\s*long referenceTimestamp,
\s*Parameters parameters,
\s*ImageFrame shortHighlightFrame\) \{)'''
m = re.search(sig_pattern, t)
if not m:
    raise SystemExit("26481 reconstruction signature anchor missing")
t = t[:m.end()] + '''
        final long iris26481ReconstructStartMs = System.currentTimeMillis();
''' + t[m.end():]

return_anchor = '''            return new MotionV2Merger.Result(
                    script.output,
                    referenceTimestamp,
                    ordered.size(),
                    script.effectiveSupport);
'''
return_new = '''            Log.d(TAG, "IRIS_26481_WRONSKI_TOTAL_TIMING"
                    + " elapsedMs="
                    + (System.currentTimeMillis() - iris26481ReconstructStartMs)
                    + " normalFrames=" + ordered.size()
                    + " shortFramePresent=" + (shortHighlightFrame != null)
                    + " detailedPerFrameTiming=IRIS_26468_STAGE_TIMING"
                    + " equationsChanged=false");
''' + return_anchor
t = replace_once(t, return_anchor, return_new, "26481 total timing return")
RECON.write_text(t)

# 4. Version.
v = VER.read_text()
v = replace_once(v, "VERSION_NAME=0.9726480", "VERSION_NAME=0.9726481", "version name")
v = replace_once(v, "VERSION_BUILD=26480", "VERSION_BUILD=26481", "version build")
VER.write_text(v)

# Hard validation.
cap = CAP.read_text()
cj = COLOR_JAVA.read_text()
cg = COLOR_GLSL.read_text()
recon = RECON.read_text()
ver = VER.read_text()

for marker in (
    "IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP",
    "MOTION_26481_TIMESTAMP_MATCH_TOLERANCE_NS",
    "neighborFallback=false",
):
    if marker not in cap:
        raise SystemExit("CaptureController missing " + marker)

for marker in (
    "IRIS_26481_BJZHOU_DOMAIN_CORRECT_HIGHLIGHT_COLOR",
    "sensorClipLevel",
    "repairBeforeWbMatrix=true",
):
    if marker not in cj:
        raise SystemExit("ColorJava missing " + marker)

for marker in (
    "IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR",
    "allChannelsNearClip",
    "partialRepairGate",
    "terminalNeutral",
):
    if marker not in cg:
        raise SystemExit("ColorGLSL missing " + marker)

for marker in ("IRIS_26481_WRONSKI_TOTAL_TIMING", "IRIS_26468_STAGE_TIMING"):
    if marker not in recon:
        raise SystemExit("Recon missing " + marker)

if "40_000_000L" in cap:
    raise SystemExit("stale 40ms timestamp fallback survived")
if "neighborhoodRisk" in cg:
    raise SystemExit("old spatial highlight-risk path reintroduced")
if "VERSION_NAME=0.9726481" not in ver or "VERSION_BUILD=26481" not in ver:
    raise SystemExit("26481 version proof failed")

print("26481 candidate/source validation PASS")
