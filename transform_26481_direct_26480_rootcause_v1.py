#!/usr/bin/env python3
from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
CAP = root / "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
CJ = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java"
CG = root / "app/src/main/assets/shaders/motionv2/color_transform.glsl"
for p in (CAP, CJ, CG):
    if not p.is_file(): raise SystemExit(f"26481 missing required 26480 source path: {p}")

def once(t, old, new, label):
    n=t.count(old)
    if n != 1: raise SystemExit(f"26481 {label}: anchor count={n}, expected 1")
    return t.replace(old,new,1)

# ------------------------------------------------------------------
# 1) Camera2 metadata/short-frame role: timestamp is an identity.
# ------------------------------------------------------------------
t=CAP.read_text()
for marker in ["IRIS_26480_SHORT_RING_HEADROOM_V1", "IRIS_26480_SHORT_DRAIN_HEADROOM_V1",
               "IRIS_26480_SHORT_FRAME_TRANSPORTED", "MOTION_26480_SHORT_WAIT_MS = 300L"]:
    if marker not in t: raise SystemExit(f"26481 exact-successful-26480 capture marker missing: {marker}")
old='''    private TotalCaptureResult findNearestZslResult(long timestamp) {
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
new='''    /* IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP
     * RAW Image SENSOR_TIMESTAMP is frame identity. Never borrow Camera2
     * metadata from an adjacent ~33 ms frame: that makes exposure/noise/role
     * metadata belong to the wrong physical observation.
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
t=once(t,old,new,"exact timestamp metadata method")
field='    private static final long MOTION_26480_SHORT_WAIT_MS = 300L;\n'
t=once(t,field,field+'    private static final long MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS = 2_000_000L;\n',"short timestamp tolerance field")
# After the nearest-metadata fallback is removed, exact successful 26480 must
# have exactly two 40 ms comparisons, both short-role association gates.
matches=list(re.finditer(r'<=\s*40_000_000L',t))
if len(matches)!=2:
    raise SystemExit(f"26481 expected exactly 2 remaining 40ms short-role comparisons, found {len(matches)}")
t=re.sub(r'<=\s*40_000_000L','<= MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS',t)
if '40_000_000L' in t:
    raise SystemExit('26481 stale 40ms timestamp-role fallback remains')
if t.count('MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS') != 3:
    raise SystemExit('26481 short timestamp tolerance producer/consumer count mismatch')
CAP.write_text(t)

# ------------------------------------------------------------------
# 2) Normal-stack highlight color: repair lost sensor-channel authority
#    before Camera2 WB/matrix, following bjzhou's calculation-only-WB rule.
# ------------------------------------------------------------------
g=CG.read_text()
if 'IRIS_26478_CAMERA2_COLOR_ONLY_NO_HIGHLIGHT_CHROMA_REPAIR' not in g:
    raise SystemExit('26481 exact successful 26480 Camera2-only color baseline marker missing')
for forbidden in ['IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR','neighborhoodRisk','chromaCompression']:
    if forbidden in g: raise SystemExit(f'26481 color baseline unexpectedly already contains {forbidden}')
CG.write_text(r'''precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform vec3 sensorGains;
uniform float sensorClipLevel;
uniform vec3 colorRow0;
uniform vec3 colorRow1;
uniform vec3 colorRow2;
out vec3 Output;

float max3(vec3 v){return max(v.r,max(v.g,v.b));}
float min3(vec3 v){return min(v.r,min(v.g,v.b));}

/* IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR
 * Ordinary camera RGB is untouched. Only channels proven near the physical
 * sensor ceiling lose hue authority. WB gains are used temporarily to judge
 * neutral-channel agreement, then removed again so the externally visible
 * value remains camera RGB before the one authoritative Camera2 WB+matrix.
 * No spatial hue donor, no blanket desaturation, no Wronski intervention.
 */
void main(){
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 cameraRgb=max(texelFetch(InputBuffer,xy,0).rgb,vec3(0.0));
    vec3 gains=max(sensorGains,vec3(1.0e-6));
    float clip=max(sensorClipLevel,1.0e-6);
    vec3 sensorRelative=cameraRgb/clip;

    vec3 channelLoss=smoothstep(vec3(0.940),vec3(0.995),sensorRelative);
    vec3 reliable=vec3(1.0)-channelLoss;
    float reliableSupport=reliable.r+reliable.g+reliable.b;

    vec3 calcBalanced=cameraRgb*gains;
    float reliableMean=dot(calcBalanced,reliable)/max(reliableSupport,1.0e-6);
    vec3 reliableDev=abs(calcBalanced-vec3(reliableMean))*reliable;
    float reliableSpread=max3(reliableDev)/max(reliableMean,1.0e-6);
    float reliablePair=smoothstep(1.35,1.90,reliableSupport);
    float pairAgreement=1.0-smoothstep(0.08,0.28,reliableSpread);
    float allClipped=smoothstep(0.970,0.997,min3(sensorRelative));
    float partialGate=reliablePair*pairAgreement*(1.0-allClipped);

    vec3 repairedBalanced=mix(
            calcBalanced,vec3(reliableMean),channelLoss*partialGate);
    float neutralTerminal=max3(calcBalanced);
    repairedBalanced=mix(repairedBalanced,vec3(neutralTerminal),allClipped);

    /* Calculation-only WB is explicitly removed before the normal color path. */
    vec3 repairedCameraRgb=repairedBalanced/gains;
    vec3 balanced=repairedCameraRgb*gains;
    vec3 linearSrgb=vec3(
            dot(colorRow0,balanced),
            dot(colorRow1,balanced),
            dot(colorRow2,balanced));
    Output=max(linearSrgb,vec3(0.0));
}
''')

# Keep Java bindings unchanged; update only telemetry so future logs describe
# the active shader instead of the stale 26430 intervention flags.
j=CJ.read_text()
if 'glProg.setVar("sensorClipLevel", sensorClipLevel);' not in j:
    raise SystemExit('26481 sensorClipLevel binding missing from exact 26480 Java color owner')
pat=re.compile(r'''        Log\.d\(Name, "IRIS_26430_V2_COLOR".*?\n\s*\+ " explicitDotRows=true"\);''',re.S)
repl='''        Log.d(Name, "IRIS_26481_BJZHOU_DOMAIN_CORRECT_HIGHLIGHT_COLOR"
                + " gainsRGeGoB=" + java.util.Arrays.toString(g)
                + " greenMean=" + greenGain
                + " matrixRowMajor=" + java.util.Arrays.toString(m)
                + " sensorClipLevel=" + sensorClipLevel
                + " camera2ColorAuthority=true"
                + " repairBeforeWbMatrix=true"
                + " wbCalculationOnlyAndRemoved=true"
                + " fullClipHueAuthority=false"
                + " partialRepairRequiresReliablePair=true"
                + " spatialHueDonor=false"
                + " broadDesaturation=false"
                + " wronskiMathChanged=false");'''
j,n=pat.subn(repl,j,count=1)
if n!=1: raise SystemExit(f'26481 color telemetry block count={n}, expected 1')
CJ.write_text(j)

# Final transform-only semantic proof. Version is intentionally NOT changed here;
# the guarded builder increments it only after the transformed candidate compiles.
assert 'IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP' in CAP.read_text()
assert CAP.read_text().count('MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS') == 3
assert 'IRIS_26481_BJZHOU_CALCULATION_DOMAIN_HIGHLIGHT_REPAIR' in CG.read_text()
assert 'repairedCameraRgb=repairedBalanced/gains;' in CG.read_text()
assert 'IRIS_26481_BJZHOU_DOMAIN_CORRECT_HIGHLIGHT_COLOR' in CJ.read_text()
print('26481 transform dry-run/source assumptions PASS')
print('26481 exact timestamp ownership PASS')
print('26481 2ms short-role association PASS')
print('26481 bjzhou calculation-only WB repair PASS')
print('26481 Wronski math untouched by transform PASS')
