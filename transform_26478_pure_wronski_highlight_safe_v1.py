from pathlib import Path
import hashlib
import sys

root = Path(sys.argv[1])

capture = root / "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
recon = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
direct_init = root / "app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl"
direct_acc = root / "app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"
ref_add = root / "app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl"
finalize = root / "app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl"
color = root / "app/src/main/assets/shaders/motionv2/color_transform.glsl"
version = root / "app/version.properties"

for p in [capture, recon, direct_init, direct_acc, ref_add, finalize, color, version]:
    if not p.exists():
        raise SystemExit("26478 missing candidate source: " + str(p))

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

expected_shader_sha = {
    direct_init: "f5c6936faeb218f1d355cdb8544ec89fdded3936a329d033f7e862aae3ea8017",
    direct_acc: "4173840a7df096a3a797ce08816369a31c10ae679a1eb762a4e93c6e6e036e62",
    ref_add: "7b20e19ab32fde6805656b6a0c21e87de6c0d74e6b06ea80f169df92f88ac197",
    finalize: "e55c5bd1874c9403e05fb898f520918b428fb352ad8279dfa549f34bbac05de1",
    color: "e7c520622d504e0246f3a3427d45bca48f7520a526ca0793621541c9db73da65",
}
for p, expected in expected_shader_sha.items():
    actual = sha256(p)
    if actual != expected:
        raise SystemExit(
            "26478 exact-26477 shader hash mismatch "
            + str(p) + " actual=" + actual + " expected=" + expected)

# Capture-side Google-style highlight-safe equal-exposure burst adaptation.
t = capture.read_text()

field_anchor = '''    /* IRIS_26382_CAPTURE_STATE_HANDOFF */
    private volatile long mMotion26382LastOpportunityCeilingNs = 0L;
    private volatile float mMotion26382LastRawNeed = 0.0f;
'''
field_insert = '''    /* IRIS_26382_CAPTURE_STATE_HANDOFF */
    private volatile long mMotion26382LastOpportunityCeilingNs = 0L;
    private volatile float mMotion26382LastRawNeed = 0.0f;

    /*
     * IRIS_26478_GOOGLE_STYLE_HIGHLIGHT_SAFE_EQUAL_EXPOSURE_BURST
     *
     * Photon-specific acquisition adaptation, not claimed as unpublished
     * Google production code. The published HDR+ principle is an equal-
     * exposure RAW burst exposed low enough to retain highlights.
     *
     * Use the existing 0.2% sparse-RAW highlight onset and request one stop
     * less AE exposure only AFTER shutter press. Old prebuffer frames are
     * cleared so reconstruction receives one actual exposure group.
     */
    private static final float MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER = 0.002f;
    private static final float MOTION_26478_HIGHLIGHT_PROTECTION_EV = 1.0f;
    private boolean mMotion26478HighlightSafeBiasApplied = false;
    private int mMotion26478HighlightSafeBaseSteps = 0;
    private int mMotion26478HighlightSafeTargetSteps = 0;
'''
if t.count(field_anchor) != 1:
    raise SystemExit("26478 CaptureController field anchor count=" + str(t.count(field_anchor)))
t = t.replace(field_anchor, field_insert, 1)

trigger_anchor = '''    private void triggerZslCapture() {'''
helper = r'''    /*
     * IRIS_26478_GOOGLE_STYLE_HIGHLIGHT_SAFE_EQUAL_EXPOSURE_BURST
     * Shutter-time only; the continuous preview RAW-AE loop stays dormant.
     */
    private boolean applyMotion26478HighlightSafeBurstBiasIfNeeded() {
        if (!isZslMode()
                || mPreviewRequestBuilder == null
                || mCaptureSession == null
                || mCameraCharacteristics == null
                || mPreviewCaptureResult == null
                || mMotion26380RawSampleCount < 64
                || Float.isNaN(mMotion26380RawHighlightFraction)) {
            return false;
        }

        Long previewTimestamp =
                mPreviewCaptureResult.get(CaptureResult.SENSOR_TIMESTAMP);
        long rawAgeNs =
                previewTimestamp == null
                                || mMotion26380RawSignalTimestampNs <= 0L
                        ? Long.MAX_VALUE
                        : Math.abs(
                                previewTimestamp
                                        - mMotion26380RawSignalTimestampNs);
        boolean rawFresh = rawAgeNs <= 180_000_000L;
        if (!rawFresh
                || mMotion26380RawHighlightFraction
                        < MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER) {
            return false;
        }

        android.util.Range<Integer> range =
                mCameraCharacteristics.get(
                        CameraCharacteristics.CONTROL_AE_COMPENSATION_RANGE);
        android.util.Rational step =
                mCameraCharacteristics.get(
                        CameraCharacteristics.CONTROL_AE_COMPENSATION_STEP);
        if (range == null || step == null || step.floatValue() <= 0.0f) {
            Log.w(TAG,
                    "IRIS_26478_HIGHLIGHT_SAFE_CAPTURE unavailable"
                            + " reason=noAeCompensationRange");
            return false;
        }

        Integer current =
                mPreviewRequestBuilder.get(
                        CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION);
        int baseSteps = current != null ? current : 0;
        baseSteps =
                Math.max(
                        range.getLower(),
                        Math.min(range.getUpper(), baseSteps));

        int protectionSteps =
                Math.max(
                        1,
                        Math.round(
                                MOTION_26478_HIGHLIGHT_PROTECTION_EV
                                        / step.floatValue()));
        int targetSteps =
                Math.max(
                        range.getLower(),
                        Math.min(
                                range.getUpper(),
                                baseSteps - protectionSteps));
        if (targetSteps >= baseSteps) {
            return false;
        }

        try {
            mPreviewRequestBuilder.set(
                    CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION,
                    targetSteps);

            mMotion26478HighlightSafeBiasApplied = true;
            mMotion26478HighlightSafeBaseSteps = baseSteps;
            mMotion26478HighlightSafeTargetSteps = targetSteps;

            clearMotionUnifiedBuffer();
            rebuildPreviewBuilder();

            Log.i(TAG,
                    "IRIS_26478_HIGHLIGHT_SAFE_CAPTURE_APPLIED"
                            + " rawHighlightFraction="
                            + mMotion26380RawHighlightFraction
                            + " trigger="
                            + MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER
                            + " rawAgeNs=" + rawAgeNs
                            + " requestedProtectionEv="
                            + MOTION_26478_HIGHLIGHT_PROTECTION_EV
                            + " aeStepEv=" + step.floatValue()
                            + " baseSteps=" + baseSteps
                            + " targetSteps=" + targetSteps
                            + " halAeRemainsOn=true"
                            + " prebufferCleared=true"
                            + " equalExposureGroupRequired=true");
            return true;
        } catch (IllegalArgumentException | IllegalStateException error) {
            mMotion26478HighlightSafeBiasApplied = false;
            Log.w(TAG,
                    "IRIS_26478_HIGHLIGHT_SAFE_CAPTURE skipped "
                            + error.getClass().getSimpleName());
            return false;
        }
    }

    private void restoreMotion26478HighlightSafeBurstBias() {
        if (!mMotion26478HighlightSafeBiasApplied
                || mPreviewRequestBuilder == null
                || mCaptureSession == null) {
            mMotion26478HighlightSafeBiasApplied = false;
            return;
        }

        int restoreSteps = mMotion26478HighlightSafeBaseSteps;
        int usedSteps = mMotion26478HighlightSafeTargetSteps;
        try {
            mPreviewRequestBuilder.set(
                    CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION,
                    restoreSteps);
            rebuildPreviewBuilder();
            Log.i(TAG,
                    "IRIS_26478_HIGHLIGHT_SAFE_CAPTURE_RESTORED"
                            + " usedSteps=" + usedSteps
                            + " restoredSteps=" + restoreSteps
                            + " halAeRemainsOn=true");
        } catch (IllegalArgumentException | IllegalStateException error) {
            Log.w(TAG,
                    "IRIS_26478_HIGHLIGHT_SAFE_CAPTURE_RESTORE skipped "
                            + error.getClass().getSimpleName());
        } finally {
            mMotion26478HighlightSafeBiasApplied = false;
        }
    }

'''
if t.count(trigger_anchor) != 1:
    raise SystemExit("26478 trigger insertion anchor count=" + str(t.count(trigger_anchor)))
t = t.replace(trigger_anchor, helper + trigger_anchor, 1)

old_trigger = '''        mZslCapturing = true;
        burst = false;
        mMotionTopUpActive = true;
        mMotionTopUpStartMs = android.os.SystemClock.elapsedRealtime();
'''
new_trigger = '''        mZslCapturing = true;
        burst = false;
        mMotionTopUpActive = true;

        final boolean iris26478HighlightSafeBurst =
                applyMotion26478HighlightSafeBurstBiasIfNeeded();

        mMotionTopUpStartMs = android.os.SystemClock.elapsedRealtime();
'''
if t.count(old_trigger) != 1:
    raise SystemExit("26478 trigger body anchor count=" + str(t.count(old_trigger)))
t = t.replace(old_trigger, new_trigger, 1)

trace_anchor = '''                        + " minimum=" + mMotionTopUpMinimumFrames
                        + " timeoutMs=" + MOTION_TOP_UP_TIMEOUT_MS);'''
trace_new = '''                        + " minimum=" + mMotionTopUpMinimumFrames
                        + " timeoutMs=" + MOTION_TOP_UP_TIMEOUT_MS
                        + " iris26478HighlightSafeBurst="
                        + iris26478HighlightSafeBurst
                        + " iris26478RawHighlightFraction="
                        + mMotion26380RawHighlightFraction
                        + " iris26478AeTargetSteps="
                        + mMotion26478HighlightSafeTargetSteps);'''
if t.count(trace_anchor) != 1:
    raise SystemExit("26478 TOP_UP_BEGIN trace anchor count=" + str(t.count(trace_anchor)))
t = t.replace(trace_anchor, trace_new, 1)

recover_anchor = '''    private void recoverMotionCaptureAfterEarlyExit(
            @NonNull String traceResult,
            @NonNull String userMessage) {
        mMotionTopUpActive = false;
'''
recover_new = '''    private void recoverMotionCaptureAfterEarlyExit(
            @NonNull String traceResult,
            @NonNull String userMessage) {
        mMotionTopUpActive = false;
        restoreMotion26478HighlightSafeBurstBias();
'''
if t.count(recover_anchor) != 1:
    raise SystemExit("26478 recovery restore anchor count=" + str(t.count(recover_anchor)))
t = t.replace(recover_anchor, recover_new, 1)

finalize_anchor = '''    private void finalizeMotionZslCapture() {
        int frameCount = mMotionTopUpTargetFrames > 0'''
finalize_new = '''    private void finalizeMotionZslCapture() {
        /*
         * Top-up is stopped before this method; restoring live preview AE
         * cannot alter the already-buffered equal-exposure RAW group.
         */
        restoreMotion26478HighlightSafeBurstBias();

        int frameCount = mMotionTopUpTargetFrames > 0'''
if t.count(finalize_anchor) != 1:
    raise SystemExit("26478 finalize restore anchor count=" + str(t.count(finalize_anchor)))
t = t.replace(finalize_anchor, finalize_new, 1)

capture.write_text(t)

# Truthful reconstruction logging; image math remains shader-owned.
r = recon.read_text()
old_log = '''IRIS_26472_WRONSKI_REFERENCE_MERGE accumulatedRobustnessThreshold=2 referenceRadiusLowSupport=2 referenceRadiusNormal=1 covarianceMultiplierLowSupport=8 referenceOverwriteLowSupport=true referenceAddNormal=true clippedEvidenceSemantics26469Preserved=true'''
new_log = '''IRIS_26478_WRONSKI_REFERENCE_ADD_ONCE ipolAccumulatedRobustnessDenoiser=false referenceRadius=1 covarianceMultiplier=1 referenceOverwrite=false referenceAddOnce=true saturationValidity=false'''
if r.count(old_log) != 1:
    raise SystemExit("26478 reconstruction reference log anchor count=" + str(r.count(old_log)))
r = r.replace(old_log, new_log, 1)

replacements = {
    "IRIS_26471_LOW_SUPPORT_COHERENT_RECONSTRUCTION":
        "IRIS_26478_PURE_WRONSKI_DIRECT_RGB",
    "censoredHighlightDualEvidence=true":
        "censoredHighlightDualEvidence=false",
    "sharedSpatialClipCoherence=true":
        "sharedSpatialClipCoherence=false",
    "clippedBrightnessPreserved=true":
        "clippedSamplesOrdinaryObservations=true",
}
for old, new in replacements.items():
    if r.count(old) != 1:
        raise SystemExit("26478 reconstruction log replacement count "
                         + old + "=" + str(r.count(old)))
    r = r.replace(old, new, 1)
recon.write_text(r)

# Shader replacements.
direct_init.write_text(r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba32f,binding=1) uniform highp readonly image2D referenceCov;
layout(rgba32f,binding=2) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=3) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=4) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float clipR;
uniform float clipG;
uniform float clipB;

/* IRIS_26478_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR_NO_SATURATION_SIDECHANNEL */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,rawSize))) return;
    imageStore(outNumerator,p,vec4(0.0));
    imageStore(outDenominator,p,vec4(0.0));
    imageStore(outFrameSupport,p,vec4(0.0));
}
''')

direct_acc.write_text(r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D flowTexture;
uniform highp sampler2D robustnessTexture;
uniform highp sampler2D previousNumerator;
uniform highp sampler2D previousDenominator;
uniform highp sampler2D previousFrameSupport;
layout(rgba16f,binding=0) uniform highp readonly image2D alterCfa;
layout(rgba32f,binding=1) uniform highp readonly image2D alterCov;
layout(rgba32f,binding=2) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=3) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=4) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float maximumSupport;
uniform float clipR;
uniform float clipG;
uniform float clipB;

int componentIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int componentColor(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
float cfaAt(ivec2 p){
    p=clamp(p,ivec2(0),rawSize-ivec2(1));
    vec4 v=imageLoad(alterCfa,p>>1);
    int c=componentIndex(p);
    return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));
}
mat2 covAt(ivec2 p){
    p=clamp(p,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(alterCov,p);
    return mat2(v.x,v.y,v.z,v.w);
}
mat2 interpolateCov(vec2 gp){
    ivec2 fl=ivec2(max(floor(gp),vec2(0.0)));
    ivec2 ce=min(fl+ivec2(1),rawHalf-ivec2(1));
    vec2 f=fract(gp);
    mat2 c00=covAt(fl);
    mat2 c01=covAt(ivec2(ce.x,fl.y));
    mat2 c10=covAt(ivec2(fl.x,ce.y));
    mat2 c11=covAt(ce);
    return c00*((1.0-f.x)*(1.0-f.y))
         + c01*(f.x*(1.0-f.y))
         + c10*((1.0-f.x)*f.y)
         + c11*(f.x*f.y);
}
mat2 invertCov(mat2 m){
    float d=m[0][0]*m[1][1]-m[0][1]*m[1][0];
    if(abs(d)<=1e-10) return mat2(1,0,0,1);
    return mat2(m[1][1],-m[0][1],-m[1][0],m[0][0])/d;
}

/* IRIS_26478_WRONSKI_PUBLIC_AUX_ACCUMULATION_NO_SATURATION_SIDECHANNEL */
void main(){
    ivec2 outP=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(outP,rawSize))) return;

    vec2 uv=(vec2(outP)+0.5)/vec2(rawSize);
    vec2 rawFlow=2.0*texture(flowTexture,uv).xy;
    vec2 lr=vec2(outP)+0.5;
    vec2 lrMov=lr+rawFlow;
    if(lrMov.x<0.0||lrMov.y<0.0||lrMov.x>=float(rawSize.x)||lrMov.y>=float(rawSize.y)) return;

    ivec2 robustP=clamp(ivec2(lr),ivec2(0),rawSize-ivec2(1));
    float R=clamp(texelFetch(robustnessTexture,robustP,0).r,0.0,1.0);
    vec2 kmap=lrMov/2.0-0.5;
    mat2 invCov=invertCov(interpolateCov(kmap));

    ivec2 center=ivec2(lrMov);
    vec2 movTarget=lrMov-0.5;
    vec3 addNum=vec3(0.0),addDen=vec3(0.0);
    for(int iy=-1;iy<=1;iy++)for(int ix=-1;ix<=1;ix++){
        ivec2 p=center+ivec2(ix,iy);
        if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,rawSize))) continue;
        int c=componentColor(componentIndex(p));
        vec2 d=vec2(p)-movTarget;
        float z=max(dot(d,invCov*d),0.0);
        float w=exp(-0.5*z)*R;
        float cfaSample=cfaAt(p);
        addNum[c]+=w*cfaSample;
        addDen[c]+=w;
    }

    vec4 n=texelFetch(previousNumerator,outP,0);
    n.rgb+=addNum;
    imageStore(outNumerator,outP,n);

    vec4 d=texelFetch(previousDenominator,outP,0);
    d.rgb+=addDen;
    imageStore(outDenominator,outP,d);

    vec4 fs=texelFetch(previousFrameSupport,outP,0);
    fs.r=min(max(maximumSupport-1.0,0.0),max(fs.r,0.0)+R);
    fs.gba=vec3(0.0);
    imageStore(outFrameSupport,outP,fs);
}
''')

ref_add.write_text(r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba32f,binding=1) uniform highp readonly image2D referenceCov;
layout(rgba32f,binding=2) uniform highp readonly image2D currentNumerator;
layout(rgba32f,binding=3) uniform highp readonly image2D currentDenominator;
layout(rgba32f,binding=4) uniform highp readonly image2D currentFrameSupport;
layout(rgba32f,binding=5) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=6) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=7) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float clipR;
uniform float clipG;
uniform float clipB;

/*
 * IRIS_26478_WRONSKI_REFERENCE_ADD_ONCE_NO_IPOL_ACCUMULATED_DENOISER
 * IPOL's public default config disables accumulated_robustness_denoiser.merge.
 * Always add the immutable reference with the ordinary radius-1 kernel.
 */
int componentIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int componentColor(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
float cfaAt(ivec2 p){
    p=clamp(p,ivec2(0),rawSize-ivec2(1));
    vec4 v=imageLoad(referenceCfa,p>>1);
    int c=componentIndex(p);
    return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));
}
mat2 covAt(ivec2 p){
    p=clamp(p,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(referenceCov,p);
    return mat2(v.x,v.y,v.z,v.w);
}
mat2 interpolateCov(vec2 gp){
    ivec2 fl=ivec2(max(floor(gp),vec2(0.0)));
    ivec2 ce=min(fl+ivec2(1),rawHalf-ivec2(1));
    vec2 f=fract(gp);
    mat2 c00=covAt(fl);
    mat2 c01=covAt(ivec2(ce.x,fl.y));
    mat2 c10=covAt(ivec2(fl.x,ce.y));
    mat2 c11=covAt(ce);
    return c00*((1.0-f.x)*(1.0-f.y))
         + c01*(f.x*(1.0-f.y))
         + c10*((1.0-f.x)*f.y)
         + c11*(f.x*f.y);
}
mat2 invertCov(mat2 m){
    float d=m[0][0]*m[1][1]-m[0][1]*m[1][0];
    if(abs(d)<=1e-10) return mat2(1,0,0,1);
    return mat2(m[1][1],-m[0][1],-m[1][0],m[0][0])/d;
}

void main(){
    ivec2 outP=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(outP,rawSize))) return;

    vec4 oldNum=imageLoad(currentNumerator,outP);
    vec4 oldDen=imageLoad(currentDenominator,outP);
    vec4 fs=imageLoad(currentFrameSupport,outP);

    vec2 coarse=vec2(outP);
    vec2 greyPos=(coarse-vec2(0.5))/2.0;
    mat2 invCov=invertCov(interpolateCov(greyPos));
    ivec2 center=ivec2(round(coarse));
    vec3 refNum=vec3(0.0),refDen=vec3(0.0);

    const int RAD=1;
    for(int iy=-RAD;iy<=RAD;iy++) for(int ix=-RAD;ix<=RAD;ix++){
        ivec2 p=center+ivec2(ix,iy);
        if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,rawSize))) continue;
        int c=componentColor(componentIndex(p));
        vec2 delta=vec2(p)-coarse;
        float z=max(dot(delta,invCov*delta),0.0);
        float w=exp(-0.5*z);
        float sample=cfaAt(p);
        refNum[c]+=sample*w;
        refDen[c]+=w;
    }

    imageStore(outNumerator,outP,vec4(oldNum.rgb+refNum,0.0));
    imageStore(outDenominator,outP,vec4(oldDen.rgb+refDen,1.0));
    // fs.r remains auxiliary robustness; finalizer adds the reference once.
    imageStore(outFrameSupport,outP,vec4(max(fs.r,0.0),0.0,0.0,0.0));
}
''')

finalize.write_text(r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba32f,binding=0) uniform highp readonly image2D currentNumerator;
layout(rgba32f,binding=1) uniform highp readonly image2D currentDenominator;
layout(rgba32f,binding=2) uniform highp readonly image2D currentFrameSupport;
layout(rgba32f,binding=3) uniform highp writeonly image2D outRgb;
uniform float wbR;
uniform float wbG;
uniform float wbB;

/* IRIS_26478_WRONSKI_PURE_DIVIDE_ONCE_FINALIZER */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,imageSize(outRgb)))) return;

    vec3 num=imageLoad(currentNumerator,p).rgb;
    vec3 den=max(imageLoad(currentDenominator,p).rgb,vec3(1e-12));
    vec3 wbRgb=num/den;
    vec3 sensorRgb=wbRgb/vec3(
            max(wbR,1e-6),
            max(wbG,1e-6),
            max(wbB,1e-6));

    float auxiliaryRobustness=
            max(imageLoad(currentFrameSupport,p).r,0.0);
    float frameSupport=1.0+auxiliaryRobustness;

    imageStore(outRgb,p,vec4(max(sensorRgb,vec3(0.0)),frameSupport));
}
''')

color.write_text(r'''precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform vec3 sensorGains;
uniform float sensorClipLevel;
uniform vec3 colorRow0;
uniform vec3 colorRow1;
uniform vec3 colorRow2;
out vec3 Output;

/* IRIS_26478_CAMERA2_COLOR_ONLY_NO_HIGHLIGHT_CHROMA_REPAIR */
void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 cameraRgb=max(texelFetch(InputBuffer,xy,0).rgb,vec3(0.0));
    vec3 balanced=cameraRgb*max(sensorGains,vec3(1.0e-6));
    vec3 linearSrgb=vec3(
            dot(colorRow0,balanced),
            dot(colorRow1,balanced),
            dot(colorRow2,balanced));
    Output=max(linearSrgb,vec3(0.0));
}
''')

v = version.read_text()
if v.count("VERSION_NAME=0.9726477") != 1 or v.count("VERSION_BUILD=26477") != 1:
    raise SystemExit("26478 exact 26477 version anchors not unique")
v = v.replace("VERSION_NAME=0.9726477", "VERSION_NAME=0.9726478", 1)
v = v.replace("VERSION_BUILD=26477", "VERSION_BUILD=26478", 1)
version.write_text(v)

ct = capture.read_text()
rt = recon.read_text()
di = direct_init.read_text()
da = direct_acc.read_text()
ra = ref_add.read_text()
fi = finalize.read_text()
co = color.read_text()

required = [
    ("capture marker", "IRIS_26478_GOOGLE_STYLE_HIGHLIGHT_SAFE_EQUAL_EXPOSURE_BURST" in ct),
    ("shutter-only capture call", "applyMotion26478HighlightSafeBurstBiasIfNeeded()" in ct),
    ("restore path", "restoreMotion26478HighlightSafeBurstBias();" in ct),
    ("one-stop protection", "MOTION_26478_HIGHLIGHT_PROTECTION_EV = 1.0f" in ct),
    ("existing trigger", "MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER = 0.002f" in ct),
    ("reference log", "IRIS_26478_WRONSKI_REFERENCE_ADD_ONCE" in rt),
    ("zero accumulator", "IRIS_26478_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR_NO_SATURATION_SIDECHANNEL" in di),
    ("aux recurrence", "IRIS_26478_WRONSKI_PUBLIC_AUX_ACCUMULATION_NO_SATURATION_SIDECHANNEL" in da),
    ("reference add", "IRIS_26478_WRONSKI_REFERENCE_ADD_ONCE_NO_IPOL_ACCUMULATED_DENOISER" in ra),
    ("pure finalizer", "IRIS_26478_WRONSKI_PURE_DIVIDE_ONCE_FINALIZER" in fi),
    ("Camera2 color only", "IRIS_26478_CAMERA2_COLOR_ONLY_NO_HIGHLIGHT_CHROMA_REPAIR" in co),
    ("version", "VERSION_NAME=0.9726478" in version.read_text()),
    ("build", "VERSION_BUILD=26478" in version.read_text()),
]
for name, ok in required:
    if not ok:
        raise SystemExit("26478 candidate validation failed: " + name)

for forbidden, text, where in [
    ("sampleValidity(", di, "direct_rgb_init"),
    ("sampleValidity(", da, "direct_rgb_accumulate"),
    ("sampleValidity(", ra, "reference_add"),
    ("unsupportedAll", fi, "mfsr_finalize"),
    ("channelLoss", co, "color_transform"),
    ("neighborhoodRisk", co, "color_transform"),
    ("chromaCompression", co, "color_transform"),
    ("referenceOwns", ra, "reference_add"),
    ("MAX_FRAME_COUNT", ra, "reference_add"),
    ("MAX_MULTIPLIER", ra, "reference_add"),
]:
    if forbidden in text:
        raise SystemExit("26478 forbidden logic survived in " + where + ": " + forbidden)

for invariant in [
    "vec2 lr=vec2(outP)+0.5;",
    "vec2 lrMov=lr+rawFlow;",
    "vec2 kmap=lrMov/2.0-0.5;",
    "float w=exp(-0.5*z)*R;",
    "n.rgb+=addNum;",
    "d.rgb+=addDen;",
]:
    if invariant not in da:
        raise SystemExit("26478 Wronski aux invariant missing: " + invariant)

for invariant in ["oldNum.rgb+refNum", "oldDen.rgb+refDen", "const int RAD=1;"]:
    if invariant not in ra:
        raise SystemExit("26478 Wronski reference invariant missing: " + invariant)

for p in [capture, recon]:
    s = p.read_text()
    if s.count("{") != s.count("}"):
        raise SystemExit("26478 Java brace mismatch: " + str(p))
for p in [direct_init, direct_acc, ref_add, finalize, color]:
    s = p.read_text()
    if s.count("{") != s.count("}") or "void main()" not in s:
        raise SystemExit("26478 GLSL structural validation failed: " + str(p))

print("26478 candidate/source validation PASS")
print("26478 Temporary-copy validation: PASS")
