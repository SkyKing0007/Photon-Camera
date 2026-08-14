from pathlib import Path
import re, sys

root=Path(sys.argv[1])

param=root/"app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
hdrx=root/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
recon=root/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
post=root/"app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
display_java=root/"app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java"
display_glsl=root/"app/src/main/assets/shaders/motionv2/display_exposure.glsl"
version=root/"app/version.properties"

# Parameters: non-tunable strict Motion sensor authority.
t=param.read_text()
anchor='''    public boolean motionV2DirectColorValid = false;
    public float tonemapStrength = 1.4f;'''
replacement='''    public boolean motionV2DirectColorValid = false;

    /*
     * IRIS_26477_STRICT_WRONSKI_SENSOR_AUTHORITY
     * Non-tunable Motion-only sensor contract populated directly from
     * timestamp-owned Camera2 metadata after generic Photon tunable injection.
     */
    public boolean motionV2StrictWronskiSensorValid = false;
    public float motionV2WronskiNoiseS = Float.NaN;
    public float motionV2WronskiNoiseO = Float.NaN;

    public float tonemapStrength = 1.4f;'''
if t.count(anchor)!=1:
    raise SystemExit("Parameters anchor count="+str(t.count(anchor)))
param.write_text(t.replace(anchor,replacement,1))

# Hdrx: install strict Camera2 authority after generic Parameters fill.
t=hdrx.read_text()
anchor='''        processingParameters.FillDynamicParameters(captureResult, captureRequest,ISO);
        processingParameters.cameraRotation = cameraRotation;'''
replacement='''        processingParameters.FillDynamicParameters(captureResult, captureRequest,ISO);
        if (cameraMode == CameraMode.MOTION) {
            configureStrictWronskiSensorAuthority(processingParameters);
        }
        processingParameters.cameraRotation = cameraRotation;'''
if t.count(anchor)!=1:
    raise SystemExit("Hdrx call anchor count="+str(t.count(anchor)))
t=t.replace(anchor,replacement,1)

helper_anchor='''    /*
     * IRIS_26394 canonical exposure estimator.'''
helper='''    /*
     * IRIS_26477_STRICT_WRONSKI_SENSOR_AUTHORITY
     * Hard boundary between Photon settings and Wronski reconstruction.
     */
    private void configureStrictWronskiSensorAuthority(Parameters p) {
        if (p == null || characteristics == null || captureResult == null) {
            throw new IllegalStateException(
                    "26477 strict Wronski requires Camera2 characteristics + timestamp result");
        }

        Integer cfa = characteristics.get(
                CameraCharacteristics.SENSOR_INFO_COLOR_FILTER_ARRANGEMENT);
        if (cfa == null || cfa < 0 || cfa > 3) {
            throw new IllegalStateException(
                    "26477 strict Wronski requires standard Camera2 Bayer CFA; cfa=" + cfa);
        }

        android.hardware.camera2.params.BlackLevelPattern staticBlack =
                characteristics.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);
        if (staticBlack == null) {
            throw new IllegalStateException(
                    "26477 strict Wronski missing SENSOR_BLACK_LEVEL_PATTERN");
        }
        int[] staticBl = new int[4];
        staticBlack.copyTo(staticBl, 0);
        float[] strictBl = new float[] {
                staticBl[0], staticBl[1], staticBl[2], staticBl[3]
        };
        float[] dynamicBl =
                captureResult.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL);
        if (dynamicBl != null && dynamicBl.length >= 4) {
            boolean finite = true;
            for (int i = 0; i < 4; i++) {
                finite &= Float.isFinite(dynamicBl[i]) && dynamicBl[i] >= 0.0f;
            }
            if (finite) {
                System.arraycopy(dynamicBl, 0, strictBl, 0, 4);
            }
        }

        Integer strictWhite =
                captureResult.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL);
        if (strictWhite == null || strictWhite <= 0) {
            strictWhite = characteristics.get(
                    CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL);
        }
        if (strictWhite == null || strictWhite <= 0) {
            throw new IllegalStateException(
                    "26477 strict Wronski missing sensor white level");
        }

        android.util.Pair<Double, Double>[] profile =
                captureResult.get(CaptureResult.SENSOR_NOISE_PROFILE);
        if (profile == null || profile.length == 0) {
            throw new IllegalStateException(
                    "26477 strict Wronski missing SENSOR_NOISE_PROFILE; Photon fallback forbidden");
        }

        double strictS;
        double strictO;
        if (profile.length >= 4) {
            strictS = (
                    profile[0].first
                            + 0.5 * (profile[1].first + profile[2].first)
                            + profile[3].first) / 3.0;
            strictO = (
                    profile[0].second
                            + 0.5 * (profile[1].second + profile[2].second)
                            + profile[3].second) / 3.0;
        } else if (profile.length >= 3) {
            strictS = (
                    profile[0].first + profile[1].first + profile[2].first) / 3.0;
            strictO = (
                    profile[0].second + profile[1].second + profile[2].second) / 3.0;
        } else {
            strictS = profile[0].first;
            strictO = profile[0].second;
        }

        if (!Double.isFinite(strictS) || !Double.isFinite(strictO)
                || strictS <= 0.0 || strictO < 0.0) {
            throw new IllegalStateException(
                    "26477 invalid Camera2 noise profile S=" + strictS + " O=" + strictO);
        }

        // Overwrite reconstruction-critical fields after TunableInjector.
        p.blackLevel = strictBl;
        p.whiteLevel = strictWhite;
        p.cfaPattern = (byte)(int)cfa;
        p.motionV2WronskiNoiseS = (float)strictS;
        p.motionV2WronskiNoiseO = (float)strictO;
        p.motionV2StrictWronskiSensorValid = true;

        String authority =
                "IRIS_26477_STRICT_WRONSKI_SENSOR_AUTHORITY"
                        + " cfaSource=CameraCharacteristics"
                        + " blackSource=Camera2"
                        + " whiteSource=Camera2"
                        + " noiseSource=CaptureResult.SENSOR_NOISE_PROFILE"
                        + " photonAdaptiveNoise=false"
                        + " photonNoiseModeler=false"
                        + " dynamicNoiseStore=false"
                        + " blackLevelOverride=false"
                        + " whiteLevelOverride=false"
                        + " cfaOverride=false"
                        + " noiseS=" + p.motionV2WronskiNoiseS
                        + " noiseO=" + p.motionV2WronskiNoiseO
                        + " whiteLevel=" + p.whiteLevel
                        + " cfa=" + p.cfaPattern;
        Log.d(TAG, authority);
        com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                "MOTION_WRONSKI_SENSOR_AUTHORITY", authority);
    }

'''
if t.count(helper_anchor)!=1:
    raise SystemExit("Hdrx helper anchor count="+str(t.count(helper_anchor)))
t=t.replace(helper_anchor,helper+helper_anchor,1)

old='''        processingParameters.noiseModeler.computeStackingNoiseModel(
                cameraMode == CameraMode.MOTION
                        ? Math.max(
                                1,
                                Math.round(
                                        processingParameters.motionV2EffectiveSupport))
                        : images.size());'''
new='''        if (cameraMode != CameraMode.MOTION) {
            processingParameters.noiseModeler.computeStackingNoiseModel(images.size());
        } else {
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26477_PHOTON_STACK_NOISE_BYPASS",
                    "noiseModeler.computeStackingNoiseModel=false"
                            + " wronskiNoiseOwner=Camera2_IPOL"
                            + " effectiveSupport="
                            + processingParameters.motionV2EffectiveSupport);
        }'''
if t.count(old)!=1:
    raise SystemExit("Hdrx stack-noise anchor count="+str(t.count(old)))
hdrx.write_text(t.replace(old,new,1))

# Reconstructor: remove Photon noise source and pre-merge hot-pixel mutation.
t=recon.read_text()
imp="import com.particlesdevs.photoncamera.processing.render.NoiseModeler;\n"
if t.count(imp)!=1:
    raise SystemExit("NoiseModeler import count="+str(t.count(imp)))
t=t.replace(imp,"",1)

hot='''        int mappedHotPixelsCorrected = 0;
        for (ImageFrame ownedFrame : ordered) {
            if (ownedFrame != null && ownedFrame.buffer != null) {
                mappedHotPixelsCorrected += correctKnownHotPixels(
                        ownedFrame.buffer,
                        size.x,
                        size.y,
                        parameters);
            }
        }
        Log.d(TAG, "IRIS_26423_KNOWN_HOT_PIXEL_SANITIZE"
                + " corrected=" + mappedHotPixelsCorrected
                + " frames=" + ordered.size()
                + " beforeAlignment=true"
                + " sameCfaNeighbors=true");'''
hot_new='''        /*
         * IRIS_26477_STRICT_WRONSKI_NO_PHOTON_PREMERGE_REPAIR
         * No Photon/Iris RAW mutation before Wronski reconstruction.
         */
        int mappedHotPixelsCorrected = 0;
        Log.d(TAG, "IRIS_26477_STRICT_WRONSKI_NO_PHOTON_PREMERGE_REPAIR"
                + " mappedHotPixelMutation=false"
                + " corrected=0"
                + " frames=" + ordered.size());'''
if t.count(hot)!=1:
    raise SystemExit("hot-pixel block count="+str(t.count(hot)))
t=t.replace(hot,hot_new,1)

gain='''        final float canonicalGain =
                Math.max(1.0f, parameters.motionCanonicalExposureGain);'''
gain_new='''        /*
         * IRIS_26477_WRONSKI_CANONICAL_SENSOR_DOMAIN
         * Display normalization is downstream of Wronski.
         */
        final float canonicalGain = 1.0f;'''
if t.count(gain)!=1:
    raise SystemExit("canonical gain anchor count="+str(t.count(gain)))
t=t.replace(gain,gain_new,1)

start=t.index("        float noiseS = 1.0e-6f;")
end_marker="        final float mfsrSnr = Math.max("
end=t.index(end_marker,start)
noise_new='''        if (!parameters.motionV2StrictWronskiSensorValid) {
            throw new IllegalStateException(
                    "26477 Wronski missing strict Camera2 sensor authority");
        }
        float noiseS = Math.max(parameters.motionV2WronskiNoiseS, 1.0e-7f);
        float noiseO = Math.max(parameters.motionV2WronskiNoiseO, 1.0e-8f);
        Log.d(TAG, "IRIS_26477_WRONSKI_NOISE_AUTHORITY"
                + " source=CaptureResult.SENSOR_NOISE_PROFILE"
                + " photonNoiseModeler=false"
                + " dynamicNoiseStore=false"
                + " adaptiveNoiseTunable=false"
                + " noiseRstr=false"
                + " displayGainInsideWronski=false"
                + " noiseS=" + noiseS
                + " noiseO=" + noiseO);

'''
t=t[:start]+noise_new+t[end:]

snr='''        final int mfsrTileSize =
                mfsrSnr <= 14.0f ? 64 : (mfsrSnr <= 22.0f ? 32 : 16);'''
snr_new=snr+'''

        Log.d(TAG, "IRIS_26477_WRONSKI_RECONSTRUCTION_AUTHORITY"
                + " reconstructionOwner=Wronski_IPOL"
                + " sensorDomainGain=1.0"
                + " displayGain=" + parameters.motionCanonicalExposureGain
                + " legacyPyramidAlignment=false"
                + " legacyPyramidMerge=false"
                + " photonAdaptiveNoise=false"
                + " photonNoiseRstr=false"
                + " photonHotPixelPremerge=false"
                + " mfsrSnr=" + mfsrSnr
                + " kDetail=" + mfsrKDetail
                + " kDenoise=" + mfsrKDenoise
                + " Dth=" + mfsrDth
                + " Dtr=" + mfsrDtr);'''
if t.count(snr)!=1:
    raise SystemExit("SNR log anchor count="+str(t.count(snr)))
recon.write_text(t.replace(snr,snr_new,1))

# PostPipeline: no Photon noiseRstr/NoiseModeler for Motion; no residual denoise.
t=post.read_text()
start=t.index("        NoiseModeler modeler = mParameters.noiseModeler;")
end_marker="        Point rawSliced = parameters.rawSize;"
end=t.index(end_marker,start)
new_noise='''        if (mParameters.motionV2Active) {
            /*
             * IRIS_26477_NO_PHOTON_POST_NOISE_STATE
             * Active Motion V2 nodes do not consume generic Photon noise state.
             */
            noiseS = 0.0f;
            noiseO = 0.0f;
            Log.d("PostPipeline",
                    "IRIS_26477_NO_PHOTON_POST_NOISE_STATE"
                            + " noiseModeler=false"
                            + " noiseRstr=false"
                            + " esd=false"
                            + " residualSpatialDenoise=false");
        } else {
            NoiseModeler modeler = mParameters.noiseModeler;
            noiseS = modeler.computeModel[0].first.floatValue() +
                    modeler.computeModel[1].first.floatValue() +
                    modeler.computeModel[2].first.floatValue();
            noiseO = modeler.computeModel[0].second.floatValue() +
                    modeler.computeModel[1].second.floatValue() +
                    modeler.computeModel[2].second.floatValue();
            noiseS /= 3.f;
            noiseO /= 3.f;
            double noisempy = Math.pow(2.0, mSettings.noiseRstr + constShift);
            Log.d("PostPipeline", "noisempy:" + noisempy);
            noiseS *= noisempy;
            noiseO *= noisempy;
            noiseO = Math.max(noiseO, 1.0f/4096.0f);
            noiseS = Math.max(noiseS, Float.MIN_NORMAL);
        }
'''
t=t[:start]+new_noise+t[end:]

old='''            add(new MotionV2ColorTransform());
            add(new MotionV2Denoise());

            add(new StageTelemetry("V2_POST_LUMA_CHROMA_RECONSTRUCTION"));'''
new='''            /*
             * IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY
             * Wronski is complete before scene/display exposure is applied.
             */
            add(new MotionV2DisplayExposure());
            add(new StageTelemetry("V2_POST_DISPLAY_EXPOSURE_AFTER_WRONSKI"));
            add(new MotionV2ColorTransform());

            /*
             * IRIS_26477_WRONSKI_PRIMARY_DENOISE_ONLY
             * Pure comparison build: no residual spatial denoise after Wronski.
             */
            add(new StageTelemetry("V2_POST_WRONSKI_PRIMARY_DENOISE_ONLY"));'''
if t.count(old)!=1:
    raise SystemExit("V2 color/denoise anchor count="+str(t.count(old)))
t=t.replace(old,new,1)

oldlog='''                    "nodes=MotionV2CfaInput,DirectRGB-or-CFAFallback,TrueLocalSupportDenoise,MotionV2ColorTransform,MotionV2Denoise,MotionV2Render,RotateWatermark"
                            + " directMultiframeRgb=" + directBayer
                            + " exposureFusion=false esd=false ablc=false"
                            + " initial=false autoExposure=false"
                            + " captureSharpening=false correctingFlow=false sharpen2=false");'''
newlog='''                    "nodes=MotionV2CfaInput,DirectRGB-or-CFAFallback,MotionV2DisplayExposure,MotionV2ColorTransform,MotionV2Render,RotateWatermark"
                            + " directMultiframeRgb=" + directBayer
                            + " strictWronskiAuthority26477=true"
                            + " displayExposureAfterWronski=true"
                            + " residualSpatialDenoise=false"
                            + " photonNoiseState=false"
                            + " exposureFusion=false esd=false ablc=false"
                            + " initial=false autoExposure=false"
                            + " captureSharpening=false correctingFlow=false sharpen2=false");'''
if t.count(oldlog)!=1:
    raise SystemExit("V2 authority log anchor count="+str(t.count(oldlog)))
post.write_text(t.replace(oldlog,newlog,1))

display_java.write_text('''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY
 * Applies the existing scalar display normalization only after Wronski.
 * This stage is intentionally non-tunable.
 */
public final class MotionV2DisplayExposure extends Node {
    public MotionV2DisplayExposure() {
        super("", "MotionV2DisplayExposure");
    }

    @Override public void Compile() {}

    @Override
    public void Run() {
        if (!basePipeline.mParameters.motionV2Active) {
            throw new IllegalStateException(
                    "MotionV2DisplayExposure used outside Motion V2");
        }

        float gain = Math.max(
                1.0f,
                basePipeline.mParameters.motionCanonicalExposureGain);

        glProg.useAssetProgram("motionv2/display_exposure");
        glProg.setTexture("InputBuffer", previousNode.WorkingTexture);
        glProg.setVar("displayGain", gain);
        WorkingTexture = basePipeline.getMain();
        glProg.drawBlocks(WorkingTexture);
        glProg.closed = true;

        Log.d(Name, "IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY"
                + " displayGain=" + gain
                + " insideWronski=false"
                + " photonAutoExposure=false"
                + " photonExposureFusion=false"
                + " tunable=false");
    }
}
''')

display_glsl.write_text('''precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
out vec3 Output;

/* IRIS_26477_POST_WRONSKI_DISPLAY_BOUNDARY */
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec3 c = max(texelFetch(InputBuffer, p, 0).rgb, vec3(0.0));
    Output = c * max(displayGain, 1.0);
}
''')

v=version.read_text()
if v.count("VERSION_NAME=0.9726476")!=1 or v.count("VERSION_BUILD=26476")!=1:
    raise SystemExit("version anchors not unique")
v=v.replace("VERSION_NAME=0.9726476","VERSION_NAME=0.9726477",1)
v=v.replace("VERSION_BUILD=26476","VERSION_BUILD=26477",1)
version.write_text(v)

# Candidate validation.
for p in [param,hdrx,recon,post,display_java,display_glsl,version]:
    if not p.exists():
        raise SystemExit("missing transformed file "+str(p))

rt=recon.read_text()
pt=post.read_text()
ht=hdrx.read_text()
assert "NoiseModeler modeler = parameters.noiseModeler" not in rt
assert "final float canonicalGain = 1.0f;" in rt
assert "CaptureResult.SENSOR_NOISE_PROFILE" in ht
assert "add(new MotionV2DisplayExposure());" in pt
assert "add(new MotionV2Denoise());" not in pt
assert "VERSION_NAME=0.9726477" in version.read_text()
assert "VERSION_BUILD=26477" in version.read_text()

for p in [param,hdrx,recon,post,display_java]:
    s=p.read_text()
    if s.count("{") != s.count("}"):
        raise SystemExit("brace mismatch "+str(p))

print("candidate/source validation PASS")
print("Temporary-copy validation: PASS")
