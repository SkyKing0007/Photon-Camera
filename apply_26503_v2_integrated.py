#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, re, sys


def fail(msg: str):
    raise SystemExit('ERROR: '+msg)

def one(src: str, old: str, new: str, label: str) -> str:
    n=src.count(old)
    if n!=1: fail(f'{label}: expected one anchor, found {n}')
    return src.replace(old,new,1)

def replace_function(src: str, signature_token: str, replacement: str, label: str) -> str:
    start=src.find(signature_token)
    if start<0: fail(f'{label}: signature token not found: {signature_token}')
    if src.find(signature_token,start+1)>=0: fail(f'{label}: signature token is not unique')
    brace=src.find('{',start)
    if brace<0: fail(f'{label}: opening brace not found')
    depth=0
    in_str=False; esc=False; in_line=False; in_block=False
    i=brace
    while i<len(src):
        ch=src[i]; nxt=src[i+1] if i+1<len(src) else ''
        if in_line:
            if ch=='\n': in_line=False
        elif in_block:
            if ch=='*' and nxt=='/': in_block=False; i+=1
        elif in_str:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': in_str=False
        else:
            if ch=='/' and nxt=='/': in_line=True; i+=1
            elif ch=='/' and nxt=='*': in_block=True; i+=1
            elif ch=='"': in_str=True
            elif ch=='{': depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:
                    return src[:start]+replacement.rstrip()+src[i+1:]
        i+=1
    fail(f'{label}: closing brace not found')

ROOT=None

def edit(rel: str, fn):
    p=ROOT/rel
    if not p.is_file(): fail(f'missing {rel}')
    before=p.read_text()
    after=fn(before)
    if after==before: fail(f'{rel}: transform made no change')
    p.write_text(after)
    print('CHANGED',rel)

# A — frozen capture scene-key display exposure owner.
def motion_merger(src: str) -> str:
    replacement=r'''    /* IRIS_26503_FROZEN_CAPTURE_SCENE_KEY_GAIN
     * The large Motion display multiplier remains a single downstream rendering
     * authority, but darkness is no longer interpreted as an error by fixed p50/p90
     * targets. The selected reference CaptureResult is already the frozen shutter-time
     * HAL/preview exposure state. Its actual aperture/exposure/ISO creates a one-way
     * scene key: no value here is fed back to Camera2 or live AE.
     *
     * Keep the proven 26502 sparse RAW histogram sampling so exposure estimation stays
     * cheap. Very-low-EV scenes are allowed to remain dark. Bright HDR scenes whose
     * median is mostly interior/shadow receive additional shadow-dominance protection.
     */
    public static float computeDisplayGain(
            ByteBuffer raw, int width, int height, Parameters parameters,
            double referenceExposureEnergy) {
        if (raw == null || width <= 0 || height <= 0
                || parameters == null || parameters.whiteLevel <= 0
                || parameters.blackLevel == null || parameters.blackLevel.length < 4) {
            return 1.0f;
        }

        /* IRIS_26503_KEEP_26502_SPARSE_GAIN_SAMPLING
         * Preserve the proven ~256x192 estimator footprint instead of scanning millions
         * of RAW pixels on the CPU. This change must not become a processing-time regression. */
        final int bins = 2048;
        final int[] histogram = new int[bins];
        long total = 0L;
        ByteBuffer view = raw.duplicate().order(ByteOrder.nativeOrder());
        view.clear();
        ShortBuffer shorts = view.asShortBuffer();
        int sx = Math.max(1, width / 256);
        int sy = Math.max(1, height / 192);
        float white = parameters.whiteLevel;

        for (int y = sy / 2; y < height; y += sy) {
            for (int x = sx / 2; x < width; x += sx) {
                int index = y * width + x;
                if (index < 0 || index >= shorts.limit()) continue;
                int rawValue = Short.toUnsignedInt(shorts.get(index));
                int phase = ((y & 1) << 1) | (x & 1);
                float black = parameters.blackLevel[phase];
                float span = Math.max(1.0f, white - black);
                float normalized = (rawValue - black) / span;
                float measured = Math.max(0.0f, Math.min(1.0f, normalized));
                int bin = Math.min(bins - 1,
                        Math.max(0, (int)(measured * (bins - 1))));
                histogram[bin]++;
                total++;
            }
        }
        if (total < 64L) return 1.0f;

        float p50 = quantile(histogram, total, 0.50f);
        float p90 = quantile(histogram, total, 0.90f);
        float p99 = quantile(histogram, total, 0.99f);

        double exposureSeconds = parameters.exposureTime;
        float iso = Math.max(1.0f, (float) parameters.iso);
        float aperture = parameters.aperture;
        boolean frozenCaptureValid = Double.isFinite(exposureSeconds)
                && exposureSeconds > 0.0 && exposureSeconds < 30.0
                && Float.isFinite(iso) && iso > 0.0f
                && Float.isFinite(aperture) && aperture > 0.1f;
        float ev100 = 6.0f;
        if (frozenCaptureValid) {
            double ev = Math.log((aperture * aperture) / exposureSeconds) / Math.log(2.0)
                    - Math.log(iso / 100.0) / Math.log(2.0);
            if (Double.isFinite(ev)) ev100 = (float) ev;
            else frozenCaptureValid = false;
        }

        float darknessSceneKey = frozenCaptureValid
                ? smoothstep(1.5f, 5.5f, ev100) : 1.0f;
        float targetP50 = mix(0.0020f, 0.050f, darknessSceneKey);
        float targetP90 = mix(0.0120f, 0.180f, darknessSceneKey);

        float medianToHighlight = p50 / Math.max(p99, 0.0020f);
        float brightScene = frozenCaptureValid ? smoothstep(6.0f, 10.0f, ev100) : 0.0f;
        float shadowDominance = 1.0f - smoothstep(0.060f, 0.200f, medianToHighlight);
        float hdrShadowProtection = clamp01(brightScene * shadowDominance);
        targetP50 *= mix(1.0f, 0.35f, hdrShadowProtection);
        targetP90 *= mix(1.0f, 0.65f, hdrShadowProtection);

        float gain50 = targetP50 / Math.max(p50, 1.0e-5f);
        float gain90 = targetP90 / Math.max(p90, 1.0e-5f);
        float sceneGain = (float)Math.sqrt(
                Math.max(1.0f, gain50) * Math.max(1.0f, gain90));
        sceneGain = Math.max(1.0f, Math.min(16.0f, sceneGain));

        /* Highlight occupancy is a one-way veto only. It can lower display lift, never
         * increase it and never feed Camera2/live AE. */
        float predictedNearClip = fractionAbove(
                histogram, total, Math.min(1.0f, 0.985f / Math.max(sceneGain, 1.0f)));
        float occupancyPressure = smoothstep(0.015f, 0.18f, predictedNearClip);
        float gain = Math.max(1.0f,
                Math.min(16.0f, mix(sceneGain, 1.0f, occupancyPressure)));
        if (!Float.isFinite(gain)) gain = 1.0f;
        if (gain < 1.02f) gain = 1.0f;

        Log.d(TAG, "IRIS_26503_FROZEN_CAPTURE_SCENE_KEY_GAIN"
                + " rawP50=" + p50
                + " rawP90=" + p90
                + " rawP99=" + p99
                + " aperture=" + aperture
                + " exposureSeconds=" + exposureSeconds
                + " iso=" + iso
                + " frozenCaptureValid=" + frozenCaptureValid
                + " ev100=" + ev100
                + " darknessSceneKey=" + darknessSceneKey
                + " medianToHighlight=" + medianToHighlight
                + " hdrShadowProtection=" + hdrShadowProtection
                + " targetP50=" + targetP50
                + " targetP90=" + targetP90
                + " unconstrainedGain=" + sceneGain
                + " predictedNearClip=" + predictedNearClip
                + " displayGain=" + gain
                + " referenceExposureEnergyDiagnosticOnly=" + referenceExposureEnergy
                + " globalExposureOwner=true"
                + " liveAeFeedback=false"
                + " frozenReferenceCaptureState=true");
        return gain;
    }'''
    return replace_function(
            src,
            '    public static float computeDisplayGain(',
            replacement,
            'MotionV2Merger.computeDisplayGain')

# B/E — carry true local frame-equivalent support in RGB alpha without changing RGB math.
def normalizer(src: str) -> str:
    src=one(src,
        'uniform highp sampler2D lensShadingMap;\n',
        'uniform highp sampler2D lensShadingMap;\n'
        'uniform highp sampler2D frameSupportTexture;\n',
        'normalizer frame support uniform')
    old='''    calculationRgb*=lensShadingRgb(p);\n    vec3 cameraRgb=calculationRgb*cameraDomainScale;\n    Output=vec4(max(cameraRgb,vec3(0.0)),min(gWeight,65504.0));'''
    new='''    calculationRgb*=lensShadingRgb(p);\n    vec3 cameraRgb=calculationRgb*cameraDomainScale;\n\n    /* IRIS_26503_LOCAL_FRAME_EQUIVALENT_SUPPORT_CARRIER\n     * RGB above is byte-for-byte the 26502 calculation. Alpha is telemetry/permission\n     * only: the proven Wronski frame-equivalent support carrier's .r component.\n     * MotionV2DisplayExposure consumes it once before the vec3 post graph discards alpha. */\n    float localFrameSupport=max(texelFetch(frameSupportTexture,p,0).r,1.0);\n    Output=vec4(max(cameraRgb,vec3(0.0)),min(localFrameSupport,65504.0));'''
    return one(src,old,new,'normalizer alpha carrier')

# B/E local shadow recovery consumes local alpha; old seed already installed global safe shadow logic.
def display_shader(src: str) -> str:
    src=one(src,'uniform float shadowFloorStop;\n','uniform float shadowFloorStop;\nuniform float retainedFrames;\n','display retained uniform')
    replacement=r'''vec3 recoverSupportedShadow(
        vec3 displayed, vec3 sensorRgb, float localFrameSupport) {
    displayed = max(displayed, vec3(0.0));
    sensorRgb = max(sensorRgb, vec3(0.0));
    float sensorY = max(luminance(sensorRgb), 0.0);
    float displayedY = max(luminance(displayed), 0.0);
    if (sensorY <= 1.0e-8 || shadowRecoveryStrength <= 0.0) return displayed;

    /* Floor ownership stays in the pre-display sensor-linear domain. */
    float floorWidth = max(0.006, 1.5 * shadowFloorStop);
    float floorGate = smoothstep(shadowFloorStop, shadowFloorStop + floorWidth, sensorY);
    float shadowGate = 1.0 - smoothstep(0.12, 0.30, displayedY);

    /* IRIS_26503_PIXEL_LOCAL_EFFECTIVE_STACK_PERMISSION
     * Alpha carries 1 reference + accepted auxiliary frame equivalents. A 3-frame
     * shadow cannot receive the same opening as a 12-14 frame shadow even when the
     * global frame count says 15. The factor is scalar and therefore hue preserving. */
    float frameDenom = max(retainedFrames - 1.0, 1.0);
    float localRatio = clamp((max(localFrameSupport,1.0) - 1.0) / frameDenom, 0.0, 1.0);
    float localDepth = smoothstep(1.5, 8.0, max(localFrameSupport,1.0));
    float localPermission = localRatio * (0.30 + 0.70 * localDepth);
    float scale = 1.0 + clamp(shadowRecoveryStrength, 0.0, 0.10)
            * floorGate * shadowGate * localPermission;
    return displayed * scale;
}'''
    src=replace_function(src,'vec3 recoverSupportedShadow(',replacement,'display recoverSupportedShadow')
    old='''    ivec2 p = ivec2(gl_FragCoord.xy);\n    vec3 c = max(texelFetch(InputBuffer, p, 0).rgb, vec3(0.0));\n    vec3 displayed = c * max(displayGain, 1.0);\n    Output = recoverSupportedShadow(displayed, c);'''
    new='''    ivec2 p = ivec2(gl_FragCoord.xy);\n    vec4 carrier = max(texelFetch(InputBuffer, p, 0), vec4(0.0));\n    vec3 c = carrier.rgb;\n    vec3 displayed = c * max(displayGain, 1.0);\n    Output = recoverSupportedShadow(displayed, c, carrier.a);'''
    return one(src,old,new,'display main local support')

def display_java(src: str) -> str:
    src=one(src,
        '        glProg.setVar("shadowFloorStop", shadowFloorStop);\n',
        '        glProg.setVar("shadowFloorStop", shadowFloorStop);\n'
        '        glProg.setVar("retainedFrames", retainedFrames);\n',
        'display host retainedFrames binding')
    src=one(src,
        '+ " localHueScaleOnly=true"\n',
        '+ " localHueScaleOnly=true"\n'
        '                + " pixelLocalSupportFromCarrierAlpha=true"\n',
        'display host local support telemetry')
    return src

# E/performance — bind local support and remove only proven diagnostic-only readbacks.
def cfa_host(src: str) -> str:
    src=one(src,
        '                    glProg.setTexture("lensShadingMap", iris26501LensShading);\n',
        '                    glProg.setTexture("lensShadingMap", iris26501LensShading);\n'
        '                    /* IRIS_26503_LOCAL_FRAME_SUPPORT_TO_DISPLAY */\n'
        '                    glProg.setTexture("frameSupportTexture", currentDirectFrameSupport);\n',
        'CFA normalizer local support binding')

    # 26502 already disabled the obsolete full direct-support readback. Freeze that
    # proven state instead of trying to re-disable it with a stale historical anchor.
    already_disabled = (
        'if (false && /* IRIS_26480_DISABLE_DIRECT_SUPPORT_GPU_READBACK_V2 */ '
        'directBayer && currentDirectSupport != null) {'
    )
    if already_disabled not in src:
        fail('CFA: canonical 26502 direct-support diagnostic-disable invariant missing')

    # The remaining full provenance readback is post-normalization telemetry only for
    # standard Bayer/direct-RGB. PostPipeline explicitly discards this CPU carrier for
    # direct RGB because provenance has already been consumed GPU-side by the normalizer.
    provenance_condition = 'if (directBayer && iris26492ReadbackProvenance != null) {'
    provenance_disabled = (
        'if (false && /* IRIS_26503_DISABLE_HEAVY_PROVENANCE_READBACK */ '
        'directBayer && iris26492ReadbackProvenance != null) {'
    )
    src = one(
        src,
        provenance_condition,
        provenance_disabled,
        'CFA direct-RGB provenance diagnostic readback disable')
    return src

def main():
    global ROOT
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path,help='candidate root containing app/')
    a=ap.parse_args(); ROOT=a.root
    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',motion_merger)
    edit('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',normalizer)
    edit('app/src/main/assets/shaders/motionv2/display_exposure.glsl',display_shader)
    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',display_java)
    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',cfa_host)
    print('PASS: 26503 V2 deterministic A/B/E/performance transforms applied; Photon ISO100-normalized EXIF preserved')

if __name__=='__main__': main()
