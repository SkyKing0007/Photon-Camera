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

def method_bounds_containing(src: str, marker: str):
    pos=src.find(marker)
    if pos<0: return None
    # Diagnostic helpers are private/static void in the current source. Choose the nearest
    # preceding void method whose balanced body contains the marker.
    candidates=[]
    for m in re.finditer(r'(?m)^\s*(?:private\s+|public\s+|protected\s+)?(?:static\s+)?void\s+[A-Za-z_]\w*\s*\(', src[:pos]):
        candidates.append(m.start())
    for start in reversed(candidates):
        brace=src.find('{',start)
        if brace<0 or brace>pos: continue
        depth=0
        for i in range(brace,len(src)):
            if src[i]=='{': depth+=1
            elif src[i]=='}':
                depth-=1
                if depth==0:
                    if i>pos: return start,brace,i
                    break
    return None

def _brace_pairs(src: str):
    """Return balanced Java brace pairs while ignoring comments and quoted literals."""
    stack=[]; pairs=[]
    in_str=False; in_char=False; esc=False; in_line=False; in_block=False
    i=0
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
        elif in_char:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=="'": in_char=False
        else:
            if ch=='/' and nxt=='/': in_line=True; i+=1
            elif ch=='/' and nxt=='*': in_block=True; i+=1
            elif ch=='"': in_str=True
            elif ch=="'": in_char=True
            elif ch=='{': stack.append(i)
            elif ch=='}':
                if not stack: fail('Java brace parser saw unmatched closing brace')
                pairs.append((stack.pop(),i))
        i+=1
    if stack: fail('Java brace parser saw unmatched opening brace')
    return pairs

def _diagnostic_only(body: str) -> bool:
    # Positive proof: a GPU->CPU readback plus its diagnostic texture/buffer owner.
    if 'BufferLoad' not in body or ('textureBuffer' not in body and 'TextureBuffer' not in body):
        return False
    # Negative proof: never suppress GPU image production, ownership, cleanup or metrics
    # that the renderer consumes. Logging/math around a BufferLoad is okay; dispatch is not.
    forbidden=(
        'computeAuto', 'drawBlocks', 'setTextureCompute', 'glProg.draw',
        'glProg.useProgram', 'glProg.close', 'currentSupport.BufferLoad()',
        'MotionMetrics.publishV2Support(', 'return current', 'return output',
    )
    return not any(x in body for x in forbidden)

def disable_diag_method(src: str, marker: str, disable_marker: str) -> tuple[str,bool]:
    """Disable the smallest provably readback-only lexical scope containing marker.

    26492-26502 diagnostics moved between helper methods and inline scoped blocks over
    several builds.  Search smallest-first instead of assuming one historical method
    shape.  This avoids both a fragile anchor failure and, more importantly, ever
    disabling the enclosing reconstruction method when that method also dispatches GPU
    image math.
    """
    pos=src.find(marker)
    if pos<0: return src,False
    candidates=sorted(
        ((a,b) for a,b in _brace_pairs(src) if a<pos<b),
        key=lambda ab: ab[1]-ab[0])
    for brace,end in candidates:
        body=src[brace+1:end]
        if not _diagnostic_only(body):
            continue
        indent=re.search(r'(?m)^(\s*)[^\n]*$',src[:brace].split('\n')[-1] if False else '')
        # Keep the original lexical scope and declarations intact; the constant-false
        # child scope makes the diagnostic unreachable without perturbing surrounding code.
        wrapped=(
            '\n        /* '+disable_marker+'\n'
            '         * Proven diagnostic-only GPU readback disabled; image math and the\n'
            '         * functional currentSupport/MotionMetrics path remain untouched. */\n'
            '        if (false) {'+body+'\n        }\n    ')
        return src[:brace+1]+wrapped+src[end:],True
    return src,False

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
     * targets.  The selected reference CaptureResult is already the frozen shutter-time
     * HAL/preview exposure state.  Its actual aperture/exposure/ISO creates a one-way
     * scene key: no value here is fed back to Camera2 or live AE.
     *
     * Very-low-EV scenes are allowed to remain dark.  Bright high-dynamic-range scenes
     * whose median is mostly interior/shadow receive additional shadow-dominance
     * protection so a dark car cabin cannot force the whole frame several stops brighter.
     * Normally exposed scenes converge to the proven 26502 histogram targets.
     */
    public static float computeReferenceGain(
            ByteBuffer buffer,
            int width,
            int height,
            Parameters parameters) {
        if (buffer == null || width <= 0 || height <= 0 || parameters == null) {
            return 1.0f;
        }

        ByteBuffer src = buffer.duplicate().order(ByteOrder.nativeOrder());
        int samples = Math.min(width * height, src.capacity() / 2);
        if (samples <= 0) return 1.0f;

        final int bins = 1024;
        long[] histogram = new long[bins];
        long total = 0L;
        float white = Math.max(parameters.whiteLevel, 1.0f);
        float[] black = parameters.blackLevel != null && parameters.blackLevel.length >= 4
                ? parameters.blackLevel : new float[]{0f,0f,0f,0f};

        /* Sample the physical RAW directly.  Four-pixel stride keeps the estimator cheap
         * while preserving the same scene statistics across Bayer phases. */
        for (int index = 0; index < samples; index += 4) {
            int x = index % width;
            int y = index / width;
            int phase = ((y & 1) << 1) | (x & 1);
            float b = black[Math.max(0, Math.min(3, phase))];
            float value = Short.toUnsignedInt(src.getShort(index * 2));
            float normalized = Math.max(0.0f, value - b) / Math.max(white - b, 1.0f);
            int bin = Math.max(0, Math.min(bins - 1, Math.round(normalized * (bins - 1))));
            histogram[bin]++;
            total++;
        }
        if (total <= 0L) return 1.0f;

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
        float ev100 = 6.0f; // invalid metadata falls back to the proven normal-scene policy
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

        /* High EV + tiny median relative to p99 describes a bright scene whose frame is
         * dominated by dark foreground (the car test). Preserve that intended contrast
         * instead of asking the median to look like an ordinary evenly-lit photograph. */
        float medianToHighlight = p50 / Math.max(p99, 0.0020f);
        float brightScene = frozenCaptureValid ? smoothstep(6.0f, 10.0f, ev100) : 0.0f;
        float shadowDominance = 1.0f - smoothstep(0.060f, 0.200f, medianToHighlight);
        float hdrShadowProtection = clamp01(brightScene * shadowDominance);
        targetP50 *= mix(1.0f, 0.35f, hdrShadowProtection);
        targetP90 *= mix(1.0f, 0.65f, hdrShadowProtection);

        float gain50 = targetP50 / Math.max(p50, 1.0e-5f);
        float gain90 = targetP90 / Math.max(p90, 1.0e-5f);
        float sceneGain = (float) Math.sqrt(
                Math.max(1.0f, gain50) * Math.max(1.0f, gain90));
        sceneGain = Math.max(1.0f, Math.min(16.0f, sceneGain));

        /* Keep 26502's highlight occupancy veto.  This veto can only lower the global
         * display gain; it cannot brighten shadows or change live exposure. */
        float predictedNearClip = fractionAbove(
                histogram, total, Math.min(1.0f, 0.985f / Math.max(sceneGain, 1.0f)));
        float occupancyPressure = smoothstep(0.015f, 0.18f, predictedNearClip);
        float occupancyLimitedGain = mix(sceneGain, 1.0f, occupancyPressure);
        float gain = Math.max(1.0f, Math.min(16.0f, occupancyLimitedGain));

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
                + " globalExposureOwner=true"
                + " liveAeFeedback=false"
                + " frozenReferenceCaptureState=true");
        return gain;
    }'''
    return replace_function(src,'    public static float computeReferenceGain(',replacement,'MotionV2Merger.computeReferenceGain')

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

    marker='IRIS_26426_DIRECT_RGB_CHANNEL_SUPPORT_TELEMETRY'
    pos=src.find(marker)
    if pos<0: fail('CFA: direct RGB diagnostic marker missing')
    cond='if (directBayer && currentDirectSupport != null) {'
    ci=src.find(cond,pos)
    if ci<0 or ci-pos>1600: fail('CFA: direct support readback condition not found near marker')
    src=src[:ci]+'''if (false && /* IRIS_26503_DISABLE_HEAVY_DIRECT_RGB_SUPPORT_READBACK */\n                    (directBayer && currentDirectSupport != null)) {'''+src[ci+len(cond):]

    # The per-phase provenance diagnostic was invaluable during 26492-26502 but the logs
    # show it can stall seconds after RGB is already complete. Disable the diagnostic-only
    # method as a whole only when the reconstructed source proves it is readback-only.
    provenance_markers=[
        'IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE',
        'IRIS_26492_EXPLICIT_HIGHLIGHT_PROVENANCE',
    ]
    disabled=False
    for pm in provenance_markers:
        if pm in src:
            candidate,ok=disable_diag_method(src,pm,'IRIS_26503_DISABLE_HEAVY_PROVENANCE_READBACK')
            if ok:
                src=candidate; disabled=True; break
    if not disabled:
        fail('CFA: heavy provenance marker exists but no diagnostic-only readback scope could be proven; refusing unsafe speed edit')
    return src

# EXIF truthfulness; no image math.
def parse_exif(src: str) -> str:
    old='''        Integer iso = result.get(SENSOR_SENSITIVITY);\n        int isonum = 100;\n        if (iso != null) isonum = (int) (iso * IsoExpoSelector.getMPY());'''
    new='''        Integer iso = result.get(SENSOR_SENSITIVITY);\n        int isonum = 100;\n        /* IRIS_26503_ACTUAL_CAPTURE_RESULT_ISO_EXIF\n         * SENSOR_SENSITIVITY is already the actual Camera2 ISO for this frame.\n         * Do not multiply it by Photon's historical minimum-ISO normalization. */\n        if (iso != null) isonum = iso;'''
    return one(src,old,new,'EXIF actual ISO')


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
    edit('app/src/main/java/com/particlesdevs/photoncamera/api/ParseExif.java',parse_exif)
    print('PASS: 26503 V2 deterministic A/B/E/performance/EXIF transforms applied')

if __name__=='__main__': main()
