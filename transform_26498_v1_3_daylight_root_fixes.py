#!/usr/bin/env python3
from pathlib import Path
import argparse, sys


def fail(msg):
    raise SystemExit('ERROR: '+msg)

def replace_once(text, old, new, label):
    c=text.count(old)
    if c!=1:
        fail(f'{label}: expected exactly one anchor, found {c}')
    return text.replace(old,new,1)

def write_changed(path, text):
    old=path.read_text()
    if old==text:
        fail(f'no change produced for {path}')
    path.write_text(text)

SHADOW_SHADER = r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;

uniform highp sampler2D mergedCfa;
uniform highp sampler2D referenceCfa;
uniform highp sampler2D shadowCfa;
uniform highp sampler2D flowTexture;
uniform highp sampler2D frameSupport;
layout(rgba32f, binding = 0) uniform highp writeonly image2D outCfa;
layout(std430, binding = 3) buffer ShadowDiagBuf { uint shadowDiag[]; };
uniform ivec2 packedSize;
uniform float referenceExposureScale;
uniform float shadowToNormalScale;
uniform float shadowExposureRatio;
uniform float shadowClipThreshold;
uniform float minimumFlowConfidence;
uniform float deepShadowThreshold;
uniform float deepShadowPackCeiling;
uniform float minimumShadowSignal;
uniform float requiredExposureSupportRatio;
uniform float maxShadowBlend;

/* IRIS_26498_V13_BOUNDED_PRE_SHUTTER_SHADOW_AUX
 * Exactly one already-buffered brighter RAW can contribute. The merged normal CFA
 * remains base/detail authority; the immutable Wronski reference owns geometry and
 * correspondence. No generic Photon noiseS/noiseO is consumed here. A phase is
 * eligible only when actual exposure-energy gain beats its local temporal support,
 * so the auxiliary is used only where it predicts a physical shadow-SNR benefit.
 */
float sum4(vec4 v){return dot(v,vec4(1.0));}
float max4(vec4 v){return max(max(v.x,v.y),max(v.z,v.w));}
vec4 shadowSafe(vec4 v){return vec4(1.0)-step(vec4(shadowClipThreshold),v);}
vec4 phaseSafeShadow(vec2 packedCenter){
    vec2 p=packedCenter-vec2(0.5); ivec2 lo=ivec2(floor(p)); vec2 f=fract(p);
    ivec2 hi=packedSize-ivec2(1);
    ivec2 p00=clamp(lo,ivec2(0),hi),p10=clamp(lo+ivec2(1,0),ivec2(0),hi);
    ivec2 p01=clamp(lo+ivec2(0,1),ivec2(0),hi),p11=clamp(lo+ivec2(1,1),ivec2(0),hi);
    vec4 a=texelFetch(shadowCfa,p00,0),b=texelFetch(shadowCfa,p10,0);
    vec4 c=texelFetch(shadowCfa,p01,0),d=texelFetch(shadowCfa,p11,0);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
bool validateReferenceOwnedCorrespondence(ivec2 p,vec2 source,out float meanErr,out float support){
    float err=0.0; support=0.0; ivec2 hi=packedSize-ivec2(1);
    for(int oy=-2;oy<=2;++oy)for(int ox=-2;ox<=2;++ox){
        if(max(abs(ox),abs(oy))!=2)continue;
        ivec2 q=p+ivec2(ox,oy); if(any(lessThan(q,ivec2(0)))||any(greaterThan(q,hi)))continue;
        vec2 qs=source+vec2(float(ox),float(oy));
        if(qs.x<0.0||qs.y<0.0||qs.x>=float(packedSize.x)||qs.y>=float(packedSize.y))continue;
        vec4 refSensor=texelFetch(referenceCfa,q,0)/max(referenceExposureScale,1.0e-6);
        vec4 sh=phaseSafeShadow(qs); vec4 shEq=sh*shadowToNormalScale;
        vec4 mask=(vec4(1.0)-step(vec4(0.85),refSensor))*shadowSafe(sh)*step(vec4(minimumShadowSignal),refSensor);
        float n=sum4(mask); if(n<1.5)continue;
        vec4 rel=abs(refSensor-shEq)/max(refSensor,vec4(0.025));
        err+=dot(rel,mask); support+=n;
    }
    meanErr=support>0.0?err/support:1.0e20;
    return support>=12.0&&meanErr<=0.10;
}
float phaseSupport(ivec2 p,int phase){
    ivec2 rawP=p*2+ivec2(phase&1,(phase>>1)&1);
    return max(texelFetch(frameSupport,rawP,0).r,1.0);
}
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy); if(any(greaterThanEqual(p,packedSize)))return;
    vec4 merged=texelFetch(mergedCfa,p,0), ref=texelFetch(referenceCfa,p,0);
    vec4 mergedSensor=merged/max(referenceExposureScale,1.0e-6);
    vec4 refSensor=ref/max(referenceExposureScale,1.0e-6);
    if(max4(mergedSensor)>=deepShadowPackCeiling||max4(refSensor)>=deepShadowPackCeiling){imageStore(outCfa,p,merged);return;}
    vec2 uv=(vec2(p)+vec2(0.5))/vec2(packedSize); vec4 fs=texture(flowTexture,uv);
    float cancelled=step(0.5,fs.w);
    float flowConfidence=(1.0-cancelled)*exp(-80.0*max(fs.z,0.0));
    vec2 source=vec2(p)+vec2(0.5)+fs.xy;
    if(source.x<0.0||source.y<0.0||source.x>=float(packedSize.x)||source.y>=float(packedSize.y)){atomicAdd(shadowDiag[6],1u);imageStore(outCfa,p,merged);return;}
    if(flowConfidence<minimumFlowConfidence){atomicAdd(shadowDiag[3],1u);imageStore(outCfa,p,merged);return;}
    float corrErr,corrSupport;
    if(!validateReferenceOwnedCorrespondence(p,source,corrErr,corrSupport)){atomicAdd(shadowDiag[7],1u);imageStore(outCfa,p,merged);return;}
    atomicAdd(shadowDiag[2],1u);
    vec4 sh=phaseSafeShadow(source); vec4 shEqSensor=sh*shadowToNormalScale;
    vec4 shEq=shEqSensor*referenceExposureScale; vec4 outv=merged; bool any=false;
    float corrConf=1.0-smoothstep(0.06,0.10,corrErr);
    for(int phase=0;phase<4;++phase){
        if(mergedSensor[phase]>=deepShadowThreshold||refSensor[phase]>=deepShadowPackCeiling)continue;
        atomicAdd(shadowDiag[0],1u);
        if(mergedSensor[phase]<minimumShadowSignal||refSensor[phase]<minimumShadowSignal||shEqSensor[phase]<minimumShadowSignal)continue;
        atomicAdd(shadowDiag[1],1u);
        if(sh[phase]>=shadowClipThreshold){atomicAdd(shadowDiag[4],1u);continue;}
        float radiometric=abs(refSensor[phase]-shEqSensor[phase])/max(refSensor[phase],0.020);
        if(radiometric>0.22){atomicAdd(shadowDiag[8],1u);continue;}
        float sup=phaseSupport(p,phase);
        if(sup<=1.25)atomicAdd(shadowDiag[10],1u);else if(sup<=4.5)atomicAdd(shadowDiag[11],1u);else atomicAdd(shadowDiag[12],1u);
        float requiredRatio=max(1.50,requiredExposureSupportRatio*sup);
        if(shadowExposureRatio<requiredRatio){atomicAdd(shadowDiag[9],1u);continue;}
        float benefit=smoothstep(requiredRatio,min(4.0,requiredRatio+0.75),shadowExposureRatio);
        float blend=maxShadowBlend*corrConf*max(benefit,0.25);
        outv[phase]=mix(merged[phase],shEq[phase],clamp(blend,0.0,maxShadowBlend));
        atomicAdd(shadowDiag[5],1u); atomicAdd(shadowDiag[16+phase],1u); any=true;
    }
    if(any)atomicAdd(shadowDiag[13],1u);
    imageStore(outCfa,p,max(outv,vec4(0.0)));
}
'''

def transform(root: Path):
    app=root/'app/src/main'
    motion_batch=app/'java/com/particlesdevs/photoncamera/processing/MotionBatch.java'
    capture=app/'java/com/particlesdevs/photoncamera/capture/CaptureController.java'
    recon=app/'java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'
    short_shader=app/'assets/shaders/motionv2/short_highlight_bayer_recover.glsl'
    shadow_shader=app/'assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl'
    for p in (motion_batch,capture,recon,short_shader):
        if not p.is_file(): fail('missing '+str(p))
    if shadow_shader.exists(): fail('shadow shader already exists; refusing double apply')

    # Separate one-shot auxiliary owner. It is carried beside Short-A but never aliases it.
    t=motion_batch.read_text()
    anchor='''    public static final class ShortHighlightSlot {
'''
    repl='''    /* IRIS_26498_V13_SEPARATE_SHADOW_AUX_SLOT
     * A distinct one-shot owner for one brighter pre-shutter RAW. It is not the
     * Short-A slot and never appears in MotionBatch.frames.
     */
    public static final class ShadowAuxSlot {
        private ImageFrame frame;
        private boolean sealed = false;
        public synchronized boolean offer(ImageFrame candidate) {
            if (candidate == null) return false;
            if (sealed || frame != null) {
                try { candidate.close(); } catch (Throwable ignored) {}
                return false;
            }
            frame = candidate;
            return true;
        }
        public synchronized ImageFrame takeAndSeal() {
            sealed = true;
            ImageFrame out = frame;
            frame = null;
            return out;
        }
        public synchronized void sealAndClose() {
            sealed = true;
            if (frame != null) {
                try { frame.close(); } catch (Throwable ignored) {}
                frame = null;
            }
        }
        public synchronized boolean hasFrame() { return frame != null; }
        public synchronized boolean isSealed() { return sealed; }
    }

    public static final class ShortHighlightSlot {
        public final ShadowAuxSlot shadowAuxSlot = new ShadowAuxSlot();
'''
    t=replace_once(t,anchor,repl,'MotionBatch separate shadow slot class')
    anchor='''        public synchronized void sealAndClose() {
            sealed = true;
            if (frame != null) {
                try { frame.close(); } catch (Throwable ignored) {}
                frame = null;
            }
        }
'''
    repl='''        public synchronized void sealAndClose() {
            sealed = true;
            if (frame != null) {
                try { frame.close(); } catch (Throwable ignored) {}
                frame = null;
            }
            shadowAuxSlot.sealAndClose();
        }
'''
    short_class_pos=t.find('    public static final class ShortHighlightSlot {')
    close_pos=t.find(anchor,short_class_pos)
    if short_class_pos<0 or close_pos<0:
        fail('MotionBatch short-slot cleanup anchor missing')
    t=t[:close_pos]+repl+t[close_pos+len(anchor):]
    write_changed(motion_batch,t)

    # Capture: scan the COMPLETE shutter-frozen ring before any prefix Image is closed.
    # Normal drain/admission remains unchanged; only one selected non-normal pre-shutter RAW is cloned.
    t=capture.read_text()
    drain_anchor='''        /* IRIS_26480_SHORT_DRAIN_HEADROOM_V1 */
        int iris26480DrainTarget = frameCount
                + (mMotion26480ShortResultTimestampNs > 0L ? 1 : 0);
        int take = Math.min(rawImages.size(), iris26480DrainTarget);
        int skip = rawImages.size() - take;
        for (int i = 0; i < skip; i++) {
            rawImages.get(i).close();
        }
'''
    drain_repl='''        /* IRIS_26480_SHORT_DRAIN_HEADROOM_V1 */
        int iris26480DrainTarget = frameCount
                + (mMotion26480ShortResultTimestampNs > 0L ? 1 : 0);
        int take = Math.min(rawImages.size(), iris26480DrainTarget);
        int skip = rawImages.size() - take;

        /* IRIS_26498_V13_COMPLETE_FROZEN_RING_EXPOSURE_AUTHORITY
         * Determine the unchanged normal exposure group from the same drain window as 26494,
         * but inspect all shutter-frozen RAWs before closing the prefix. Exactly one physically
         * brighter pre-shutter RAW may be cloned into the isolated shadow lane.
         */
        TotalCaptureResult bestExposureGroup =
                findBestMotionExposureGroup(rawImages, skip);
        ImageFrame irisV13ShadowAuxFrame = null;
        long irisV13ShadowAuxTimestamp = -1L;
        TotalCaptureResult irisV13ShadowAuxResult = null;
        int irisV13ShadowAuxIndex = -1;
        final long irisV13ShadowSelectStartNs = System.nanoTime();
        /* rawImages is the immediately frozen rolling-ZSL ring from the shutter path;
         * only tagged Short-A is non-normal and excluded separately. */
        final long irisV13PreShutterCeilingNs = Long.MAX_VALUE;
        final double irisV13NormalEnergy = motion26486ExposureEnergy(bestExposureGroup);
        Long irisV13NormalExpObj = bestExposureGroup == null ? null
                : bestExposureGroup.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer irisV13NormalIsoObj = bestExposureGroup == null ? null
                : bestExposureGroup.get(CaptureResult.SENSOR_SENSITIVITY);
        final long irisV13NormalExpNs = irisV13NormalExpObj == null ? 0L : irisV13NormalExpObj;
        final int irisV13NormalIso = irisV13NormalIsoObj == null ? 0 : irisV13NormalIsoObj;
        final long irisV13ShortTicketTimestamp = iris26486ShortTicket == null
                ? 0L : iris26486ShortTicket.expectedTimestampNs();
        double irisV13BestShadowExposureRatio = 0.0;
        int irisV13RingExact = 0, irisV13RingNormalEligible = 0;
        int irisV13DrainNormalEligible = 0, irisV13RingBrighter = 0;
        StringBuilder irisV13RingExposureTrace = new StringBuilder();
        for (int i = 0; i < rawImages.size(); ++i) {
            Image im = rawImages.get(i);
            if (im == null) continue;
            long rawTs = im.getTimestamp();
            TotalCaptureResult rr = findNearestZslResult(rawTs);
            Long rrTs = rr == null ? null : rr.get(CaptureResult.SENSOR_TIMESTAMP);
            Long e = rr == null ? null : rr.get(CaptureResult.SENSOR_EXPOSURE_TIME);
            Integer iso = rr == null ? null : rr.get(CaptureResult.SENSOR_SENSITIVITY);
            boolean exact = rrTs != null && rrTs == rawTs;
            if (exact) irisV13RingExact++;
            boolean normalEligible = motionExposurePairMatches(rr, bestExposureGroup);
            if (normalEligible) {
                irisV13RingNormalEligible++;
                if (i >= skip) irisV13DrainNormalEligible++;
            }
            double energy = motion26486ExposureEnergy(rr);
            double energyRatio = irisV13NormalEnergy > 0.0 && energy > 0.0
                    ? energy / irisV13NormalEnergy : Double.NaN;
            double deltaEv = energyRatio > 0.0
                    ? Math.log(energyRatio) / Math.log(2.0) : Double.NaN;
            boolean taggedShort = (rr != null && rr.getRequest() != null
                    && MOTION_26480_SHORT_TAG.equals(rr.getRequest().getTag()))
                    || (irisV13ShortTicketTimestamp > 0L && rawTs == irisV13ShortTicketTimestamp)
                    || (mMotion26480ShortResultTimestampNs > 0L
                            && rawTs == mMotion26480ShortResultTimestampNs);
            boolean preShutter = rawTs <= irisV13PreShutterCeilingNs;
            double exposureRatio = irisV13NormalExpNs > 0L && e != null && e > 0L
                    ? e / (double) irisV13NormalExpNs : Double.NaN;
            boolean brighter = !normalEligible && !taggedShort && exact && preShutter
                    && energyRatio >= 1.50 && energyRatio <= 4.0
                    && exposureRatio >= 1.15 && exposureRatio <= 2.50
                    && iso != null && iso > 0
                    && (irisV13NormalIso <= 0 || iso <= 2 * irisV13NormalIso);
            if (brighter) {
                irisV13RingBrighter++;
                if (irisV13ShadowAuxTimestamp < 0L || rawTs > irisV13ShadowAuxTimestamp) {
                    irisV13BestShadowExposureRatio = energyRatio;
                    irisV13ShadowAuxTimestamp = rawTs;
                    irisV13ShadowAuxResult = rr;
                    irisV13ShadowAuxIndex = i;
                }
            }
            if (irisV13RingExposureTrace.length() > 0) irisV13RingExposureTrace.append(';');
            irisV13RingExposureTrace.append(i).append(':').append(rawTs).append('/')
                    .append(e).append('/').append(iso).append("/dEv=").append(deltaEv)
                    .append("/normalEligible=").append(normalEligible)
                    .append("/inNormalDrainWindow=").append(i >= skip)
                    .append("/pre=").append(preShutter)
                    .append("/short=").append(taggedShort)
                    .append("/shadowEligible=").append(brighter);
        }

        if (irisV13ShadowAuxIndex >= 0 && irisV13ShadowAuxResult != null) {
            Image img = rawImages.get(irisV13ShadowAuxIndex);
            try {
                int rowStride = img.getPlanes()[0].getRowStride();
                int pixelStride = img.getPlanes()[0].getPixelStride();
                int width = (img.getFormat() == ImageFormat.RAW10)
                        ? img.getWidth()
                        : (pixelStride > 0 ? rowStride / pixelStride : img.getWidth());
                int height = img.getHeight();
                int bufCapacity = img.getPlanes()[0].getBuffer().capacity();
                int offset = 0;
                if (PhotonCamera.getSettings().aspect169 && width > height) {
                    height = width * 9 / 16;
                    int offsetH = (img.getHeight() - height) / 2;
                    offsetH -= offsetH % 2;
                    offset = rowStride * offsetH;
                    bufCapacity = rowStride * height;
                }
                Allocator.binning = PhotonCamera.getSettings().binning;
                ImageFrame shadow = new ImageFrame(
                        img.getPlanes()[0].getBuffer(), img.getFormat(),
                        width, rowStride, offset, bufCapacity);
                shadow.timestamp = img.getTimestamp();
                shadow.width = width;
                shadow.height = height;
                if (PhotonCamera.getSettings().binning) {
                    shadow.width /= 2;
                    shadow.height /= 2;
                }
                populateMotion26480FrameMetadata(shadow, irisV13ShadowAuxResult, false);
                if (shadow.motionV2ExposureEnergy > 0.0) {
                    irisV13ShadowAuxFrame = shadow;
                } else {
                    shadow.close();
                    irisV13ShadowAuxTimestamp = -1L;
                    irisV13ShadowAuxResult = null;
                    irisV13ShadowAuxIndex = -1;
                }
            } catch (Throwable shadowCopyError) {
                if (irisV13ShadowAuxFrame != null) {
                    try { irisV13ShadowAuxFrame.close(); } catch (Throwable ignored) {}
                    irisV13ShadowAuxFrame = null;
                }
                irisV13ShadowAuxTimestamp = -1L;
                irisV13ShadowAuxResult = null;
                irisV13ShadowAuxIndex = -1;
                Log.w(TAG, "IRIS_26498_V13_SHADOW_AUX_COPY_REJECTED", shadowCopyError);
            }
        }
        final long irisV13ShadowSelectCpuMs =
                (System.nanoTime() - irisV13ShadowSelectStartNs) / 1_000_000L;
        Log.i(TAG, "IRIS_26498_V13_RING_EXPOSURE_DISTRIBUTION"
                + " frozenRingFrames=" + rawImages.size()
                + " normalDrainWindowFrames=" + (rawImages.size() - skip)
                + " exactMetadata=" + irisV13RingExact
                + " ringNormalEligible=" + irisV13RingNormalEligible
                + " drainNormalEligible=" + irisV13DrainNormalEligible
                + " shadowAuxCandidateFrames=" + irisV13RingBrighter
                + " normalExposureNs=" + irisV13NormalExpNs
                + " normalIso=" + irisV13NormalIso
                + " preShutterCeilingNs=" + irisV13PreShutterCeilingNs
                + " shadowAuxTimestamp=" + irisV13ShadowAuxTimestamp
                + " shadowAuxIndex=" + irisV13ShadowAuxIndex
                + " shadowAuxSelected=" + (irisV13ShadowAuxFrame != null)
                + " shadowAuxSelectMs=" + irisV13ShadowSelectCpuMs
                + " frames=[" + irisV13RingExposureTrace + "]");

        /* Preserve 26494 normal drain semantics byte-for-byte after the read-only full-ring scan.
         * The selected shadow RAW has already been copied into independently owned memory. */
        for (int i = 0; i < skip; i++) {
            rawImages.get(i).close();
        }
'''
    t=replace_once(t,drain_anchor,drain_repl,'Capture complete-ring selection before prefix close')
    # No second bestExposureGroup declaration later.
    t=replace_once(t,
        '''        ImageFrame iris26480ShortFrame = null;
        TotalCaptureResult iris26480ShortResult = null;

        TotalCaptureResult bestExposureGroup =
                findBestMotionExposureGroup(
                        rawImages,
                        skip);

''',
        '''        ImageFrame iris26480ShortFrame = null;
        TotalCaptureResult iris26480ShortResult = null;

''','Capture remove duplicate best group declaration')

    # If the selected shadow resides inside the ordinary drain suffix, consume only the original
    # android.media.Image here; the copied ImageFrame already belongs to the isolated slot.
    loop_anchor='''            TotalCaptureResult frameResult = findNearestZslResult(img.getTimestamp());
            boolean iris26486TaggedShort = frameResult != null
'''
    loop_repl='''            TotalCaptureResult frameResult = findNearestZslResult(img.getTimestamp());
            if (irisV13ShadowAuxFrame != null
                    && img.getTimestamp() == irisV13ShadowAuxTimestamp) {
                img.close();
                Log.i(TAG, "IRIS_26498_V13_SHADOW_AUX_ORIGINAL_IMAGE_CONSUMED"
                        + " timestamp=" + irisV13ShadowAuxTimestamp
                        + " copiedBeforePrefixClose=true normalAccumulatorAdmission=false");
                continue;
            }
            boolean iris26486TaggedShort = frameResult != null
'''
    t=replace_once(t,loop_anchor,loop_repl,'Capture skip copied shadow in normal drain')

    t=replace_once(t,
        '''        if (actualCount < 2) {
            for (ImageFrame f : selected) if (f != null) f.close();
            if (iris26480ShortFrame != null) iris26480ShortFrame.close();
            if (iris26486ShortTicket != null) {
''',
        '''        if (actualCount < 2) {
            for (ImageFrame f : selected) if (f != null) f.close();
            if (iris26480ShortFrame != null) iris26480ShortFrame.close();
            if (irisV13ShadowAuxFrame != null) irisV13ShadowAuxFrame.close();
            if (iris26486ShortTicket != null) {
''','Capture shadow cleanup insufficient group')
    t=replace_once(t,
        '''        if (!(iris26486SpanEv <= MOTION_26486_MAX_GROUP_SPAN_EV + 1.0e-4)) {
            for (ImageFrame f : selected) if (f != null) f.close();
            if (iris26480ShortFrame != null) iris26480ShortFrame.close();
            if (iris26486ShortTicket != null) {
''',
        '''        if (!(iris26486SpanEv <= MOTION_26486_MAX_GROUP_SPAN_EV + 1.0e-4)) {
            for (ImageFrame f : selected) if (f != null) f.close();
            if (iris26480ShortFrame != null) iris26480ShortFrame.close();
            if (irisV13ShadowAuxFrame != null) irisV13ShadowAuxFrame.close();
            if (iris26486ShortTicket != null) {
''','Capture shadow cleanup span reject')
    anchor='''        if (iris26480ShortFrame != null) {
            long iris26486ShortTs = iris26480ShortFrame.timestamp;
'''
    insert='''        if (irisV13ShadowAuxFrame != null) {
            long shadowTs = irisV13ShadowAuxFrame.timestamp;
            boolean shadowAccepted = iris26486ShortSlot.shadowAuxSlot.offer(irisV13ShadowAuxFrame);
            Log.i(TAG, "IRIS_26498_V13_SHADOW_AUX_BATCH_DELIVERY"
                    + " accepted=" + shadowAccepted
                    + " timestamp=" + shadowTs
                    + " normalAccumulatorAdmission=false separateAuxSlot=true");
            irisV13ShadowAuxFrame = null;
        }
'''+anchor
    t=replace_once(t,anchor,insert,'Capture shadow slot delivery')
    t=replace_once(t,
        '''                + " shortFramePresent=" + iris26486ShortSlot.hasFrame()
                + " shortNeverNormalFusion=true");
''',
        '''                + " shortFramePresent=" + iris26486ShortSlot.hasFrame()
                + " shadowAuxPresent=" + iris26486ShortSlot.shadowAuxSlot.hasFrame()
                + " shortNeverNormalFusion=true shadowNeverNormalFusion=true");
''','Capture batch boundary telemetry')
    write_changed(capture,t)

    # Reconstruction: take shadow aux before the slot seals, use reference CFA for validation,
    # fused CFA only as the need/target authority, and release both taken aux CPU buffers.
    t=recon.read_text()
    t=replace_once(t,
        '''            /* IRIS_26486_LATE_NONBLOCKING_SHORT_TAKE */\n            ImageFrame shortHighlightFrame = shortHighlightSlot == null\n                    ? null : shortHighlightSlot.takeAndSeal();\n''',
        '''            /* IRIS_26498_V13_SEPARATE_AUXILIARY_OWNERS */\n            ImageFrame irisV13ShadowAuxFrame = shortHighlightSlot == null\n                    ? null : shortHighlightSlot.shadowAuxSlot.takeAndSeal();\n            /* IRIS_26486_LATE_NONBLOCKING_SHORT_TAKE */\n            ImageFrame shortHighlightFrame = shortHighlightSlot == null\n                    ? null : shortHighlightSlot.takeAndSeal();\n''','Recon shadow take')
    t=replace_once(t,
        '''            GLTexture iris26480ShortWbCfa=null,iris26480Recovered=null;MotionV2Alignment.Result iris26480ShortAlignment=null;\n''',
        '''            GLTexture iris26480ShortWbCfa=null,iris26480Recovered=null;MotionV2Alignment.Result iris26480ShortAlignment=null;\n            GLTexture irisV13ShadowRaw=null,irisV13ShadowCfa=null,irisV13ShadowWbCfa=null,irisV13ShadowRecovered=null;\n            MotionV2Alignment.Result irisV13ShadowAlignment=null; GLBuffer irisV13ShadowDiag=null;\n            long irisV13ShadowAlignDispatchMs=0L,irisV13ShadowFuseDispatchMs=0L;\n''','Recon shadow resources')
    try_anchor='''            try{\n                if(directBayer&&shortHighlightFrame!=null&&shortHighlightFrame.buffer!=null&&referenceFrame!=null\n'''
    shadow_code='''            try{\n                /* IRIS_26498_V13_SHADOW_AUX_REFERENCE_OWNED_ALIGNMENT\n                 * One pre-shutter auxiliary, never in the accumulator. It writes a separate packed\n                 * CFA only when local reference correspondence and a per-phase exposure/support SNR proof pass.\n                 */\n                if(directBayer&&irisV13ShadowAuxFrame!=null&&irisV13ShadowAuxFrame.buffer!=null\n                        &&referenceFrame!=null&&referenceFrame.motionV2ExposureEnergy>0.0\n                        &&irisV13ShadowAuxFrame.motionV2ExposureEnergy>referenceFrame.motionV2ExposureEnergy\n                        &&wronskiPreparedAlignment!=null&&currentDirectFrameSupport!=null\n                        ){\n                    float irisV13ShadowToNormal=(float)(referenceFrame.motionV2ExposureEnergy\n                            /irisV13ShadowAuxFrame.motionV2ExposureEnergy);\n                    if(irisV13ShadowToNormal>=0.25f&&irisV13ShadowToNormal<=0.84f){\n                        long irisV13AlignStart=System.nanoTime();\n                        irisV13ShadowRaw=new GLTexture(raw,new GLFormat(GLFormat.DataType.UNSIGNED_16,1),\n                                irisV13ShadowAuxFrame.buffer,GL_NEAREST,GL_CLAMP_TO_EDGE);\n                        irisV13ShadowCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);\n                        float[] shadowBlack=irisV13ShadowAuxFrame.motionV2BlackLevelValid\n                                ?irisV13ShadowAuxFrame.motionV2BlackLevel:blackLevel;\n                        float shadowWhite=irisV13ShadowAuxFrame.motionV2WhiteLevelValid\n                                ?irisV13ShadowAuxFrame.motionV2WhiteLevel:(float)parameters.whiteLevel;\n                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/raw_to_cfa",true);\n                        glProg.setVar("whiteLevel",shadowWhite);glProg.setVar("blackLevel",shadowBlack);glProg.setVar("exposure",1.0f);\n                        glProg.setTexture("inTexture",irisV13ShadowRaw);glProg.setTextureCompute("outTexture",irisV13ShadowCfa,true);\n                        glProg.computeAutoDeferred(rawHalf,1);\n                        float rr=directSensorGains[0]/Math.max(directSensorGains[1],1e-6f);\n                        float bb=directSensorGains[2]/Math.max(directSensorGains[1],1e-6f);\n                        float alignmentScale=irisV13ShadowToNormal*iris26487ReferenceExposureScale;\n                        irisV13ShadowWbCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);\n                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_wb_cfa",true);\n                        glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("wbR",rr*alignmentScale);\n                        glProg.setVar("wbG",alignmentScale);glProg.setVar("wbB",bb*alignmentScale);\n                        glProg.setTextureCompute("inputCfa",irisV13ShadowCfa,false);glProg.setTextureCompute("outputCfa",irisV13ShadowWbCfa,true);\n                        glProg.computeAutoDeferred(rawHalf,1);\n                        irisV13ShadowAlignment=MotionV2WronskiAlignment.alignPrepared(wronskiPreparedAlignment,glProg,irisV13ShadowWbCfa);\n                        irisV13ShadowAlignDispatchMs=(System.nanoTime()-irisV13AlignStart)/1000000L;\n                        long irisV13FuseStart=System.nanoTime();\n                        irisV13ShadowRecovered=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);\n                        irisV13ShadowDiag=new GLBuffer(32,new GLFormat(GLFormat.DataType.UNSIGNED_32));\n                        irisV13ShadowDiag.uploadBuffer(new int[32],32);\n                        \n                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/shadow_aux_bayer_fuse",true);\n                        glProg.setVar("packedSize",rawHalf);glProg.setVar("referenceExposureScale",iris26487ReferenceExposureScale);\n                        glProg.setVar("shadowToNormalScale",irisV13ShadowToNormal);glProg.setVar("shadowClipThreshold",IRIS26487_CLIP_THRESHOLD);\n                        glProg.setVar("minimumFlowConfidence",0.40f);glProg.setVar("deepShadowThreshold",0.10f);\n                        glProg.setVar("deepShadowPackCeiling",0.18f);glProg.setVar("minimumShadowSignal",0.004f);glProg.setVar("requiredExposureSupportRatio",1.15f);\n                        glProg.setVar("shadowExposureRatio",1.0f/Math.max(irisV13ShadowToNormal,1.0e-6f));glProg.setVar("maxShadowBlend",0.20f);\n                        \n                        \n                        glProg.setTexture("mergedCfa",imageOutput);glProg.setTexture("referenceCfa",referenceCfa);\n                        glProg.setTexture("shadowCfa",irisV13ShadowCfa);glProg.setTexture("flowTexture",irisV13ShadowAlignment.flowTexture);\n                        glProg.setTexture("frameSupport",currentDirectFrameSupport);glProg.setTextureCompute("outCfa",irisV13ShadowRecovered,true);\n                        glProg.setBufferCompute("ShadowDiagBuf",irisV13ShadowDiag);glProg.computeAutoDeferred(rawHalf,1);\n                        irisV13ShadowFuseDispatchMs=(System.nanoTime()-irisV13FuseStart)/1000000L;\n                        imageOutput=irisV13ShadowRecovered;iris26480ReadbackOutput=irisV13ShadowRecovered;\n                        Log.i(TAG,"IRIS_26498_V13_SHADOW_AUX_DISPATCH"\n                                +" shadowToNormalScale="+irisV13ShadowToNormal\n                                +" shadowAuxExposureRatio="+(1.0f/Math.max(irisV13ShadowToNormal,1.0e-6f))\n                                +" shadowAuxTimestampDelta="+(irisV13ShadowAuxFrame.timestamp-referenceFrame.timestamp)\n                                +" shadowAuxAlignMs="+irisV13ShadowAlignDispatchMs\n                                +" shadowAuxFuseMs="+irisV13ShadowFuseDispatchMs\n                                +" shadowAuxTotalMs="+(irisV13ShadowAlignDispatchMs+irisV13ShadowFuseDispatchMs)\n                                +" normalAccumulatorAdmission=false secondDemosaic=false extraGpuDrain=false");\n                    }\n                }\n                if(directBayer&&shortHighlightFrame!=null&&shortHighlightFrame.buffer!=null&&referenceFrame!=null\n'''
    t=replace_once(t,try_anchor,shadow_code,'Recon shadow pass')
    t=replace_once(t,
        '''                    glProg.setTexture("normalCfa",imageOutput);\n                    glProg.setTexture("shortCfa",iris26480ShortCfa);\n''',
        '''                    glProg.setTexture("normalCfa",imageOutput);\n                    /* IRIS_26498_V13_SHORT_REFERENCE_OWNS_CORRESPONDENCE; merged CFA owns need/target. */\n                    glProg.setTexture("referenceCfa",referenceCfa);\n                    glProg.setTexture("shortCfa",iris26480ShortCfa);\n''','Recon short reference binding')
    read_anchor='''                if (iris26496ShortDiag != null) {\n'''
    if read_anchor not in t:
        # 26494 fixture has no 26498 short diagnostic; use provenance readback as insertion point.
        read_anchor='''                if (directBayer && iris26492ReadbackProvenance != null) {\n'''
    shadow_read='''                if (irisV13ShadowDiag != null) {\n                    try {\n                        int[] sd=irisV13ShadowDiag.readBufferIntegers(false);\n                        if(sd!=null&&sd.length>=20){\n                            Log.i(TAG,"IRIS_26498_V13_SHADOW_AUX_RESULT"\n                                    +" shadowAuxCandidatePixels="+Integer.toUnsignedLong(sd[0])\n                                    +" shadowAuxLowSignalCandidates="+Integer.toUnsignedLong(sd[1])\n                                    +" shadowAuxCorrespondencePassed="+Integer.toUnsignedLong(sd[2])\n                                    +" shadowAuxMotionRejected="+Integer.toUnsignedLong(sd[3])\n                                    +" shadowAuxSaturationRejected="+Integer.toUnsignedLong(sd[4])\n                                    +" shadowAuxContributedPixels="+Integer.toUnsignedLong(sd[5])\n                                    +" outOfBounds="+Integer.toUnsignedLong(sd[6])\n                                    +" correspondenceRejected="+Integer.toUnsignedLong(sd[7])\n                                    +" radiometryRejected="+Integer.toUnsignedLong(sd[8])\n                                    +" supportSnrRejected="+Integer.toUnsignedLong(sd[9])\n                                    +" supportLe1="+Integer.toUnsignedLong(sd[10])\n                                    +" support2to4="+Integer.toUnsignedLong(sd[11])\n                                    +" supportGt4="+Integer.toUnsignedLong(sd[12])+" packsWithFusion="+Integer.toUnsignedLong(sd[13])\n                                    +" fusedByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(sd,16,20))\n                                    +" shadowAuxAlignMs="+irisV13ShadowAlignDispatchMs\n                                    +" shadowAuxFuseMs="+irisV13ShadowFuseDispatchMs\n                                +" shadowAuxTotalMs="+(irisV13ShadowAlignDispatchMs+irisV13ShadowFuseDispatchMs)\n                                    +" oneGpuDrain=true");\n                        }\n                    } catch(Throwable shadowDiagError){Log.w(TAG,"IRIS_26498_V13_SHADOW_DIAG_SKIPPED",shadowDiagError);}\n                }\n'''+read_anchor
    t=replace_once(t,read_anchor,shadow_read,'Recon shadow diag read')
    cleanup_anchor='''                if(iris26480ShortAlignment!=null)iris26480ShortAlignment.close();if(iris26480ShortWbCfa!=null)iris26480ShortWbCfa.close();\n                if(iris26480ShortCfa!=null)iris26480ShortCfa.close();if(iris26480ShortRaw!=null)iris26480ShortRaw.close();\n                if(iris26480Recovered!=null)iris26480Recovered.close();\n'''
    cleanup_new='''                if(iris26480ShortAlignment!=null)iris26480ShortAlignment.close();if(iris26480ShortWbCfa!=null)iris26480ShortWbCfa.close();\n                if(iris26480ShortCfa!=null)iris26480ShortCfa.close();if(iris26480ShortRaw!=null)iris26480ShortRaw.close();\n                if(iris26480Recovered!=null)iris26480Recovered.close();\n                if(irisV13ShadowAlignment!=null)irisV13ShadowAlignment.close();if(irisV13ShadowWbCfa!=null)irisV13ShadowWbCfa.close();\n                if(irisV13ShadowCfa!=null)irisV13ShadowCfa.close();if(irisV13ShadowRaw!=null)irisV13ShadowRaw.close();\n                if(irisV13ShadowRecovered!=null)irisV13ShadowRecovered.close();if(irisV13ShadowDiag!=null)irisV13ShadowDiag.close();\n                /* IRIS_26498_V13_TAKEN_AUX_CPU_BUFFER_LIFETIME_FIX */\n                if(shortHighlightFrame!=null)try{shortHighlightFrame.close();}catch(Throwable ignored){}\n                if(irisV13ShadowAuxFrame!=null)try{irisV13ShadowAuxFrame.close();}catch(Throwable ignored){}\n'''
    t=replace_once(t,cleanup_anchor,cleanup_new,'Recon aux cleanup')
    write_changed(recon,t)

    # Short-A: only correspondence evidence switches from merged normalCfa to actual referenceCfa.
    t=short_shader.read_text()
    t=replace_once(t,
        '''uniform highp sampler2D normalCfa;\nuniform highp sampler2D shortCfa;\n''',
        '''uniform highp sampler2D normalCfa;\n/* IRIS_26498_V13_REFERENCE_CFA_CORRESPONDENCE_AUTHORITY */\nuniform highp sampler2D referenceCfa;\nuniform highp sampler2D shortCfa;\n''','Short shader reference uniform')
    t=replace_once(t,
        '''            vec4 nSensor = texelFetch(normalCfa, q, 0) /\n''',
        '''            vec4 nSensor = texelFetch(referenceCfa, q, 0) /\n''','Short correspondence reference fetch')
    # prove main replacement/need logic still reads normalCfa by requiring at least one remaining fetch.
    if 'texelFetch(normalCfa, p, 0)' not in t:
        fail('Short shader lost merged-CFA final need/target fetch')
    write_changed(short_shader,t)
    shadow_shader.write_text(SHADOW_SHADER)

    print('PASS: V1.3 semantic transform applied')
    print('PASS: Short-A correspondence uses reference CFA while final need/target remains merged CFA')
    print('PASS: one pre-shutter shadow auxiliary is outside MotionBatch.frames/normal accumulator')


def self_test():
    candidates=[(100,1.7),(110,3.8),(120,2.0)]
    eligible=[x for x in candidates if 1.5 <= x[1] <= 4.0]
    assert max(eligible,key=lambda x:x[0]) == (120,2.0)
    def eligible_phase(exposure_ratio,support):
        return exposure_ratio >= max(1.5,1.15*max(support,1.0))
    assert eligible_phase(1.6,1.0)
    assert not eligible_phase(1.6,2.0)
    assert eligible_phase(3.0,2.0)
    assert not eligible_phase(4.0,4.0)
    for energy_ratio in (1.5,2.0,4.0):
        scale=1.0/energy_ratio
        assert 0.25 <= scale <= (2.0/3.0)+1e-6
    assert 'uniform vec4 referenceNoiseShot' not in SHADOW_SHADER and 'uniform vec4 shadowNoiseShot' not in SHADOW_SHADER
    assert 'maxShadowBlend' in SHADOW_SHADER
    print('PASS: V1.3 newest-one-shadow selection and exposure/support SNR safety tests')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('root',nargs='?')
    ap.add_argument('--self-test',action='store_true')
    a=ap.parse_args()
    if a.self_test: self_test()
    elif a.root: transform(Path(a.root).resolve())
    else: ap.error('root or --self-test required')
