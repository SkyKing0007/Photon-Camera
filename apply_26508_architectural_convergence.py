#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse

ROOT: Path

def fail(msg: str):
    raise SystemExit('ERROR: ' + msg)

def one(src: str, old: str, new: str, label: str) -> str:
    n = src.count(old)
    if n != 1:
        fail(f'{label}: expected one anchor, found {n}')
    return src.replace(old, new, 1)

def replace_span(src: str, start_token: str, end_token: str, replacement: str, label: str) -> str:
    a = src.find(start_token)
    if a < 0:
        fail(f'{label}: start token missing')
    if src.find(start_token, a + 1) >= 0:
        fail(f'{label}: start token not unique')
    b = src.find(end_token, a + len(start_token))
    if b < 0:
        fail(f'{label}: end token missing')
    return src[:a] + replacement.rstrip() + '\n' + src[b:]

def edit(rel: str, fn):
    p = ROOT / rel
    if not p.is_file():
        fail('missing ' + rel)
    before = p.read_text()
    after = fn(before)
    if after == before:
        fail(rel + ': no change')
    p.write_text(after)
    print('CHANGED', rel)

def add(rel: str, text: str):
    p = ROOT / rel
    if p.exists():
        fail('new file already exists ' + rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    print('ADDED', rel)

# -----------------------------------------------------------------------------
# Capture ownership: retain Short/Long one-shot ownership and add one geometry-only
# nearest-Normal bridge slot. It is opportunistic and never waits at shutter time.
# -----------------------------------------------------------------------------
GEOMETRY_BRIDGE_CLASS = r'''    /* IRIS_26508_NEAREST_NORMAL_GEOMETRY_BRIDGE_OWNER
     * One copied NORMAL RAW may survive the capture-time early-close solely as a
     * geometry bridge for Short-A. It is never inserted into MotionBatch.frames and
     * never becomes a pixel/RGB contributor. Before Short timestamp identity exists,
     * newest wins; afterwards the closest timestamp wins deterministically.
     */
    public static final class GeometryBridgeSlot {
        private ImageFrame frame;
        private boolean sealed = false;
        public synchronized boolean offerNearest(ImageFrame candidate,long shortTimestampNs) {
            if (candidate == null) return false;
            if (sealed || candidate.motionV2FrameRole != ImageFrame.MotionV2FrameRole.NORMAL) {
                try { candidate.close(); } catch (Throwable ignored) {}
                return false;
            }
            boolean replace = frame == null;
            if (!replace) {
                if (shortTimestampNs > 0L) {
                    long oldDistance = Math.abs(frame.timestamp - shortTimestampNs);
                    long newDistance = Math.abs(candidate.timestamp - shortTimestampNs);
                    replace = newDistance < oldDistance
                            || (newDistance == oldDistance && candidate.timestamp > frame.timestamp);
                } else {
                    replace = candidate.timestamp > frame.timestamp;
                }
            }
            if (!replace) {
                try { candidate.close(); } catch (Throwable ignored) {}
                return false;
            }
            if (frame != null) try { frame.close(); } catch (Throwable ignored) {}
            frame = candidate;
            notifyAll();
            return true;
        }
        public synchronized ImageFrame peek() { return frame; }
        public synchronized boolean hasFrame() { return frame != null; }
        public synchronized long timestamp() { return frame == null ? 0L : frame.timestamp; }
        public synchronized void seal() { sealed = true; notifyAll(); }
        public synchronized boolean isSealed() { return sealed; }
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
            notifyAll();
        }
    }

'''

def motion_batch(src: str) -> str:
    if 'IRIS_26508_NEAREST_NORMAL_GEOMETRY_BRIDGE_OWNER' in src:
        fail('MotionBatch already contains 26508 bridge owner')
    if 'IRIS_26507_IMMUTABLE_AUX_FREEZE' not in src:
        fail('MotionBatch is not exact reconstructed 26507')
    anchor = '    public static final class ShadowAuxSlot {\n'
    src = one(src, anchor, GEOMETRY_BRIDGE_CLASS + anchor, 'geometry bridge class')
    src = one(src,
              '    public static final class ShortHighlightSlot {\n        public final ShadowAuxSlot shadowAuxSlot = new ShadowAuxSlot();\n',
              '    public static final class ShortHighlightSlot {\n        public final ShadowAuxSlot shadowAuxSlot = new ShadowAuxSlot();\n        public final GeometryBridgeSlot geometryBridgeSlot = new GeometryBridgeSlot();\n',
              'Short slot owns geometry bridge')
    src = one(src,
              '            shadowAuxSlot.sealAndClose();\n',
              '            shadowAuxSlot.sealAndClose();\n            geometryBridgeSlot.sealAndClose();\n',
              'Short slot closes geometry bridge')
    return src

BRIDGE_CAPTURE_METHODS = r'''    /* IRIS_26508_CAPTURE_SIDE_GEOMETRY_BRIDGE
     * Preserve a nearer normal-exposure RAW that would otherwise be closed while
     * the intentional Short/Long requests are in flight. Exact Short and exact Long
     * ownership are checked earlier in the RAW callback and therefore can never be
     * reclassified as this bridge. Missing result metadata may be refreshed once at
     * the immutable processing boundary; final host validation rejects it otherwise.
     */
    private boolean stageMotion26508NormalGeometryBridge(
            Motion26486ShortTicket ticket, Image img) {
        if (ticket == null || img == null || !ticket.requested
                || ticket.slot == null || ticket.slot.geometryBridgeSlot.isSealed()
                || ticket.iris26508GenerationId != mMotionUnifiedGeneration) return false;
        final long ts = img.getTimestamp();
        final long shortTimestamp = ticket.expectedTimestampNs();
        if (shortTimestamp > 0L && ts == shortTimestamp) return false;
        Motion26505LongTicket longTicket = mMotion26505CaptureLongTicket;
        if (longTicket != null) {
            long longTimestamp = longTicket.expectedTimestampNs();
            if (longTimestamp > 0L && ts == longTimestamp) return false;
        }
        TotalCaptureResult exact;
        synchronized (mZslBufferLock) { exact = mZslResultMap.get(ts); }
        if (exact != null) {
            Long exp = exact.get(CaptureResult.SENSOR_EXPOSURE_TIME);
            Integer iso = exact.get(CaptureResult.SENSOR_SENSITIVITY);
            double baseline = ExposureIndex.time2sec(mMotionUnifiedExposureNs)
                    * Math.max(mMotionUnifiedIso, 0);
            if (exp == null || exp <= 0L || iso == null || iso <= 0) return false;
            double energy = ExposureIndex.time2sec(exp) * iso;
            if (baseline > 0.0) {
                double ratio = energy / baseline;
                if (ratio < 0.72 || ratio > 1.38) return false;
            }
        }
        ImageFrame copy;
        try {
            copy = copyMotion26505LongFrame(img, exact);
        } catch (Throwable t) {
            Log.w(TAG,"IRIS_26508_BRIDGE_COPY_SKIPPED timestamp="+ts
                    +" reason="+t.getClass().getSimpleName());
            return false;
        }
        if (copy == null) return false;
        copy.motionV2FrameRole = ImageFrame.MotionV2FrameRole.NORMAL;
        copy.motionV2ShortHighlightFrame = false;
        boolean accepted = ticket.slot.geometryBridgeSlot.offerNearest(copy, shortTimestamp);
        if (accepted) {
            Log.d(TAG,"IRIS_26508_BRIDGE_CANDIDATE_STAGED"
                    +" timestamp="+ts
                    +" shortTimestampKnown="+(shortTimestamp>0L)
                    +" exactMetadataNow="+(exact!=null)
                    +" generation="+ticket.iris26508GenerationId
                    +" geometryOnly=true pixelContributor=false");
        }
        return accepted;
    }

    private void freezeMotion26508GeometryBridgeMetadata(
            MotionBatch.ShortHighlightSlot slot) {
        if (slot == null) return;
        ImageFrame bridge = slot.geometryBridgeSlot.peek();
        if (bridge != null && (bridge.motionV2ActualExposureNs <= 0L
                || bridge.motionV2ActualIso <= 0)) {
            TotalCaptureResult exact;
            synchronized (mZslBufferLock) { exact = mZslResultMap.get(bridge.timestamp); }
            if (exact != null) populateMotion26480FrameMetadata(bridge, exact, false);
        }
        bridge = slot.geometryBridgeSlot.peek();
        slot.geometryBridgeSlot.seal();
        Log.i(TAG,"IRIS_26508_FROZEN_GEOMETRY_BRIDGE"
                +" present="+(bridge!=null)
                +" timestamp="+(bridge==null?0L:bridge.timestamp)
                +" actualExposureNs="+(bridge==null?0L:bridge.motionV2ActualExposureNs)
                +" actualIso="+(bridge==null?0:bridge.motionV2ActualIso)
                +" role="+(bridge==null?"NONE":bridge.motionV2FrameRole)
                +" immutable=true geometryOnly=true pixelContributor=false shutterWait=false");
    }

'''

def capture_controller(src: str) -> str:
    if 'IRIS_26508_CAPTURE_SIDE_GEOMETRY_BRIDGE' in src:
        fail('CaptureController already contains 26508 bridge')
    if 'IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY' not in src:
        fail('CaptureController is not exact reconstructed 26507')
    method_anchor = '    /* IRIS_26486_NONBLOCKING_SHORT_HIGHLIGHT_TICKET\n'
    src = one(src, method_anchor, BRIDGE_CAPTURE_METHODS + method_anchor,
              'bridge methods before Short ticket methods')

    ticket_start = src.find('    private static final class Motion26486ShortTicket {')
    if ticket_start < 0:
        fail('Short ticket class missing')
    request_anchor = '        volatile boolean requested = false;\n'
    request_at = src.find(request_anchor, ticket_start)
    if request_at < 0:
        fail('Short ticket requested field missing')
    insert = '        volatile long iris26508GenerationId = -1L;\n'
    src = src[:request_at] + insert + src[request_at:]

    trigger = '''        final Motion26486ShortTicket iris26486ShortTicket = new Motion26486ShortTicket();
        mMotion26486CaptureShortTicket = iris26486ShortTicket;
'''
    src = one(src, trigger,
              '''        final Motion26486ShortTicket iris26486ShortTicket = new Motion26486ShortTicket();
        iris26486ShortTicket.iris26508GenerationId = mMotionUnifiedGeneration;
        mMotion26486CaptureShortTicket = iris26486ShortTicket;
''', 'Short ticket generation ownership')

    early_close = '                if (mZslCapturing && !mMotionTopUpActive) {\n'
    bridge_stage = '''                boolean iris26508BridgeCandidateCopied =
                        stageMotion26508NormalGeometryBridge(iris26489ShortTicket, img);
                if (iris26508BridgeCandidateCopied) {
                    Log.d(TAG,"IRIS_26508_BRIDGE_SURVIVED_CAPTURE_EARLY_CLOSE timestamp="
                            +img.getTimestamp());
                }
'''
    src = one(src, early_close, bridge_stage + early_close,
              'stage bridge before capture early close')

    freeze_anchor = '''        iris26486ShortSlot.freezeExpectedAuxiliaries(
                iris26507ShortExpected, iris26507LongExpected, 80L);
'''
    src = one(src, freeze_anchor,
              freeze_anchor + '''        freezeMotion26508GeometryBridgeMetadata(iris26486ShortSlot);
''', 'freeze bridge after expected aux wait')
    return src

# -----------------------------------------------------------------------------
# Short candidate: no old direct reference-neighborhood correspondence authority.
# The bridge is used only for geometry/radiometric sanity; its pixels never become
# output. Final MGC + GPU region topology decides Short contribution.
# -----------------------------------------------------------------------------
SHORT_RECOVERY_SHADER = r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;

uniform highp sampler2D normalCfa;
uniform highp sampler2D bridgeCfa;
uniform highp sampler2D shortCfa;
uniform highp sampler2D bridgeFlowTexture;
uniform highp sampler2D composedFlowTexture;
layout(rgba32f, binding = 0) uniform highp writeonly image2D outCfa;
layout(r32f, binding = 1) uniform highp writeonly image2D outProvenance;
layout(std430, binding = 2) buffer ShortDiagBuf { uint shortDiag[]; };
uniform ivec2 packedSize;
uniform float referenceExposureScale;
uniform float bridgeToNormalScale;
uniform float shortToNormalScale;
uniform float physicalClipThreshold;
uniform float shortClipThreshold;
uniform float minimumBridgeConfidence;
uniform int bridgeAvailable;

const float PROVENANCE_NORMAL=0.0;
const float PROVENANCE_CENSORED=1.0;
const float PROVENANCE_SHORT_CANDIDATE=2.0;
const uint D_TOTAL_CLIPPED=0u;
const uint D_SHORT_SAFE=1u;
const uint D_SHORT_CLIPPED=2u;
const uint D_NO_BRIDGE=3u;
const uint D_BRIDGE_GEOMETRY_REJECT=4u;
const uint D_RADIOMETRY_REJECT=5u;
const uint D_RECOVERED=6u;
const uint D_UNRECOVERABLE=7u;
const uint D_MGC_REJECT=13u;
const uint D_TOPOLOGY_REJECT=14u;
const uint D_CANDIDATE=15u;
const uint P_TOTAL=16u;
const uint P_RECOVERED=20u;
const uint P_SHORT_CLIPPED=24u;
const uint P_NO_BRIDGE=28u;
const uint P_BRIDGE_GEOMETRY=32u;
const uint P_RADIOMETRY=36u;
const uint P_UNRECOVERABLE=40u;
const uint P_MGC_REJECT=44u;
const uint P_TOPOLOGY_REJECT=48u;
const uint P_CANDIDATE=52u;

float sum4(vec4 v){return dot(v,vec4(1.0));}
float encodePhaseStates(vec4 s){return dot(s,vec4(1.0,3.0,9.0,27.0));}
void addMask(uint totalIndex,uint phaseBase,vec4 mask){
    for(int i=0;i<4;++i)if(mask[i]>0.5){atomicAdd(shortDiag[totalIndex],1u);atomicAdd(shortDiag[phaseBase+uint(i)],1u);}
}
void addTotalOnly(uint index,vec4 mask){for(int i=0;i<4;++i)if(mask[i]>0.5)atomicAdd(shortDiag[index],1u);}
vec4 samplePhaseSafe(highp sampler2D tex,vec2 packedCenter){
    vec2 p=packedCenter-vec2(0.5);ivec2 lo=ivec2(floor(p));vec2 f=fract(p);ivec2 mx=packedSize-ivec2(1);
    ivec2 p00=clamp(lo,ivec2(0),mx),p10=clamp(lo+ivec2(1,0),ivec2(0),mx);
    ivec2 p01=clamp(lo+ivec2(0,1),ivec2(0),mx),p11=clamp(lo+ivec2(1,1),ivec2(0),mx);
    vec4 a=texelFetch(tex,p00,0),b=texelFetch(tex,p10,0),c=texelFetch(tex,p01,0),d=texelFetch(tex,p11,0);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
vec4 shortSafe(vec4 v){return vec4(1.0)-step(vec4(shortClipThreshold),v);}
void storeState(ivec2 p,vec4 cfa,vec4 state){imageStore(outCfa,p,cfa);imageStore(outProvenance,p,vec4(encodePhaseStates(state),0.0,0.0,0.0));}

/* IRIS_26508_SHORT_TO_NEAREST_NORMAL_BRIDGE_AUTHORITY
 * The old 26497 direct reference-ring support-count / best-vs-second-best proof is
 * intentionally gone. Wronski supplies reference->bridge and bridge->Short flow;
 * this shader only checks that composed geometry is finite/coherent and, where a
 * bridge phase is physically observable, that exposure-normalized bridge and Short
 * agree. A fully clipped bridge center is not rejected merely for lacking normal
 * reference pixels. The bridge is geometry-only and is never copied into output.
 */
/* IRIS_26508_BRIDGE_GEOMETRY_ONLY_NEVER_CONTRIBUTES_RGB */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,packedSize)))return;
    vec4 normal=texelFetch(normalCfa,p,0);
    vec4 normalSensor=normal/max(referenceExposureScale,1.0e-6);
    vec4 clipMask=step(vec4(physicalClipThreshold),normalSensor);
    if(sum4(clipMask)<0.5){storeState(p,normal,vec4(PROVENANCE_NORMAL));return;}
    addMask(D_TOTAL_CLIPPED,P_TOTAL,clipMask);
    if(bridgeAvailable==0){
        addMask(D_NO_BRIDGE,P_NO_BRIDGE,clipMask);
        addMask(D_UNRECOVERABLE,P_UNRECOVERABLE,clipMask);
        storeState(p,normal,clipMask);return;
    }
    vec2 uv=(vec2(p)+vec2(0.5))/vec2(packedSize);
    vec4 rb=texture(bridgeFlowTexture,uv);
    vec4 rs=texture(composedFlowTexture,uv);
    vec2 bridgeCenter=vec2(p)+vec2(0.5)+rb.xy;
    vec2 shortCenter=vec2(p)+vec2(0.5)+rs.xy;
    bool finiteGeometry=all(lessThan(abs(vec4(rb.xy,rs.xy)),vec4(65504.0)));
    bool inBounds=bridgeCenter.x>=0.0&&bridgeCenter.y>=0.0&&shortCenter.x>=0.0&&shortCenter.y>=0.0
            &&bridgeCenter.x<float(packedSize.x)&&bridgeCenter.y<float(packedSize.y)
            &&shortCenter.x<float(packedSize.x)&&shortCenter.y<float(packedSize.y);
    float flowConfidence=exp(-80.0*max(max(rb.z,0.0),max(rs.z,0.0)));
    if(!finiteGeometry||!inBounds||flowConfidence<minimumBridgeConfidence){
        addMask(D_BRIDGE_GEOMETRY_REJECT,P_BRIDGE_GEOMETRY,clipMask);
        storeState(p,normal,clipMask);return;
    }
    vec4 bridgePhysical=samplePhaseSafe(bridgeCfa,bridgeCenter);
    vec4 shortPhysical=samplePhaseSafe(shortCfa,shortCenter);
    vec4 recoverMask=clipMask*shortSafe(shortPhysical);
    vec4 shortClippedMask=clipMask-recoverMask;
    addTotalOnly(D_SHORT_SAFE,recoverMask);
    addMask(D_SHORT_CLIPPED,P_SHORT_CLIPPED,shortClippedMask);
    if(sum4(recoverMask)<0.5){storeState(p,normal,clipMask);return;}

    vec4 bridgeEquivalent=bridgePhysical*bridgeToNormalScale*referenceExposureScale;
    vec4 shortEquivalent=shortPhysical*shortToNormalScale*referenceExposureScale;
    vec4 bridgeObservable=(vec4(1.0)-step(vec4(0.90),bridgePhysical))*shortSafe(shortPhysical)
            *step(vec4(0.010001),bridgePhysical);
    float observable=sum4(bridgeObservable);
    if(observable>0.5){
        vec4 rel=abs(bridgeEquivalent-shortEquivalent)/max(bridgeEquivalent,vec4(0.04));
        float meanRel=dot(rel,bridgeObservable)/observable;
        if(meanRel>0.20){
            addMask(D_BRIDGE_GEOMETRY_REJECT,P_BRIDGE_GEOMETRY,recoverMask);
            storeState(p,normal,clipMask);return;
        }
    }

    float requiredScale=1.0;
    for(int i=0;i<4;++i)if(recoverMask[i]>0.5)
        requiredScale=max(requiredScale,normal[i]/max(shortEquivalent[i],1.0e-6));
    if(requiredScale>1.25){
        addMask(D_RADIOMETRY_REJECT,P_RADIOMETRY,recoverMask);
        storeState(p,normal,clipMask);return;
    }
    shortEquivalent*=requiredScale;
    vec4 candidate=normal;vec4 state=clipMask;
    for(int i=0;i<4;++i)if(recoverMask[i]>0.5){
        float blend=smoothstep(physicalClipThreshold,1.0,normalSensor[i]);
        candidate[i]=mix(normal[i],shortEquivalent[i],blend);
        state[i]=PROVENANCE_SHORT_CANDIDATE;
    }
    addMask(D_CANDIDATE,P_CANDIDATE,recoverMask);
    storeState(p,candidate,state);
}
'''

BRIDGE_FLOW_SHADER = r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;
uniform highp sampler2D referenceToBridgeFlow;
uniform highp sampler2D bridgeToShortFlow;
uniform ivec2 packedSize;
layout(rgba16f,binding=0) uniform highp writeonly image2D outFlow;
/* IRIS_26508_WRONSKI_BRIDGE_FLOW_COMPOSITION
 * Compose reference->nearest-Normal and nearest-Normal->Short Wronski flows.
 * No bridge radiance enters this texture; it carries geometry/variation only.
 */
void main(){
 ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,packedSize)))return;
 vec4 a=texelFetch(referenceToBridgeFlow,p,0);
 vec2 bridgeCenter=vec2(p)+vec2(0.5)+a.xy;
 if(bridgeCenter.x<0.0||bridgeCenter.y<0.0||bridgeCenter.x>=float(packedSize.x)||bridgeCenter.y>=float(packedSize.y)){
  imageStore(outFlow,p,vec4(0.0,0.0,1.0,1.0));return;
 }
 vec2 uv=bridgeCenter/vec2(packedSize);
 vec4 b=texture(bridgeToShortFlow,clamp(uv,vec2(0.0),vec2(1.0)));
 imageStore(outFlow,p,vec4(a.xy+b.xy,max(max(a.z,0.0),max(b.z,0.0)),max(a.w,b.w)));
}
'''

REGION_SEED_SHADER = r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;
uniform highp sampler2D candidateProvenance;
uniform highp sampler2D mgcWeight;
uniform ivec2 packedSize;
layout(r32f,binding=0) uniform highp writeonly image2D outRegion;
layout(std430,binding=2) buffer ShortDiagBuf{uint shortDiag[];};
const uint D_MGC_REJECT=13u;const uint P_MGC_REJECT=44u;
float divv(int q){return q==0?1.0:(q==1?3.0:(q==2?9.0:27.0));}
float stateAt(ivec2 p,int q){p=clamp(p,ivec2(0),packedSize-ivec2(1));float c=texelFetch(candidateProvenance,p,0).r;return mod(floor(c/divv(q)),3.0);}
bool candidate(ivec2 p){for(int q=0;q<4;++q)if(abs(stateAt(p,q)-2.0)<0.25)return true;return false;}
bool measuredNormal(ivec2 p){for(int q=0;q<4;++q)if(abs(stateAt(p,q))<0.25)return true;return false;}
void main(){
 ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,packedSize)))return;
 bool c=candidate(p);vec2 uv=(vec2(p)+vec2(0.5))/vec2(packedSize);float w=clamp(texture(mgcWeight,uv).r,0.0,1.0);
 if(c&&w<=0.04){for(int q=0;q<4;++q)if(abs(stateAt(p,q)-2.0)<0.25){atomicAdd(shortDiag[D_MGC_REJECT],1u);atomicAdd(shortDiag[P_MGC_REJECT+uint(q)],1u);}}
 float candidateNeighbors=0.0,normalNeighbors=0.0;
 for(int oy=-1;oy<=1;++oy)for(int ox=-1;ox<=1;++ox){if(ox==0&&oy==0)continue;ivec2 n=p+ivec2(ox,oy);if(any(lessThan(n,ivec2(0)))||any(greaterThanEqual(n,packedSize)))continue;if(candidate(n))candidateNeighbors+=1.0;if(measuredNormal(n))normalNeighbors+=1.0;}
 /* IRIS_26508_GPU_REGION_BOUNDARY_SEED: a measured in-pack phase or a normal
  * neighboring boundary anchors the object; fully clipped interiors are reached
  * only by subsequent constrained 8-connected propagation. */
 bool seed=c&&w>0.20&&(measuredNormal(p)||(normalNeighbors>=1.0&&candidateNeighbors>=1.0));
 imageStore(outRegion,p,vec4(seed?1.0:0.0,0.0,0.0,1.0));
}
'''

REGION_PROPAGATE_SHADER = r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;
uniform highp sampler2D candidateProvenance;
uniform highp sampler2D mgcWeight;
uniform highp sampler2D regionIn;
uniform ivec2 packedSize;
layout(r32f,binding=0) uniform highp writeonly image2D outRegion;
shared uint iris26508Active[64];
shared uint iris26508Valid[64];
float divv(int q){return q==0?1.0:(q==1?3.0:(q==2?9.0:27.0));}
float stateAt(ivec2 p,int q){p=clamp(p,ivec2(0),packedSize-ivec2(1));float c=texelFetch(candidateProvenance,p,0).r;return mod(floor(c/divv(q)),3.0);}
bool candidate(ivec2 p){for(int q=0;q<4;++q)if(abs(stateAt(p,q)-2.0)<0.25)return true;return false;}
bool globalActiveNeighbor(ivec2 p){for(int oy=-1;oy<=1;++oy)for(int ox=-1;ox<=1;++ox){if(ox==0&&oy==0)continue;ivec2 n=p+ivec2(ox,oy);if(any(lessThan(n,ivec2(0)))||any(greaterThanEqual(n,packedSize)))continue;if(texelFetch(regionIn,n,0).r>0.5)return true;}return false;}
/* IRIS_26508_GPU_8_CONNECTED_REGION_PROPAGATION
 * One dispatch imports activity across workgroup boundaries, then floods each
 * 8x8 tile in shared memory. Four host passes therefore propagate coherent region
 * ownership across multiple tiles without any CPU/full-frame readback.
 */
void main(){
 ivec2 p=ivec2(gl_GlobalInvocationID.xy);ivec2 l=ivec2(gl_LocalInvocationID.xy);int li=int(gl_LocalInvocationIndex);
 bool inside=all(lessThan(p,packedSize));bool valid=false;bool active=false;
 if(inside){vec2 uv=(vec2(p)+vec2(0.5))/vec2(packedSize);valid=candidate(p)&&texture(mgcWeight,uv).r>0.04;active=valid&&(texelFetch(regionIn,p,0).r>0.5||globalActiveNeighbor(p));}
 iris26508Valid[li]=valid?1u:0u;iris26508Active[li]=active?1u:0u;barrier();
 for(int iter=0;iter<8;++iter){
  uint next=iris26508Active[li];
  if(next==0u&&iris26508Valid[li]!=0u){for(int oy=-1;oy<=1;++oy)for(int ox=-1;ox<=1;++ox){if(ox==0&&oy==0)continue;int nx=l.x+ox,ny=l.y+oy;if(nx<0||ny<0||nx>=8||ny>=8)continue;int ni=ny*8+nx;if(iris26508Active[ni]!=0u)next=1u;}}
  barrier();iris26508Active[li]=next;barrier();
 }
 if(inside)imageStore(outRegion,p,vec4(iris26508Active[li]!=0u?1.0:0.0,0.0,0.0,1.0));
}
'''

REGION_FINALIZE_SHADER = r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;
uniform highp sampler2D normalCfa;
uniform highp sampler2D candidateCfa;
uniform highp sampler2D candidateProvenance;
uniform highp sampler2D mgcWeight;
uniform highp sampler2D regionTexture;
uniform ivec2 packedSize;
layout(rgba32f,binding=0) uniform highp writeonly image2D outCfa;
layout(r32f,binding=1) uniform highp writeonly image2D outProvenance;
layout(std430,binding=2) buffer ShortDiagBuf{uint shortDiag[];};
const uint D_RECOVERED=6u,D_UNRECOVERABLE=7u,D_TOPOLOGY_REJECT=14u;
const uint P_RECOVERED=20u,P_UNRECOVERABLE=40u,P_TOPOLOGY_REJECT=48u;
float divv(int q){return q==0?1.0:(q==1?3.0:(q==2?9.0:27.0));}
float component(vec4 v,int q){return q==0?v.r:(q==1?v.g:(q==2?v.b:v.a));}
void setComponent(inout vec4 v,int q,float x){if(q==0)v.r=x;else if(q==1)v.g=x;else if(q==2)v.b=x;else v.a=x;}
float stateFrom(float code,int q){return mod(floor(code/divv(q)),3.0);}
float encode(vec4 s){return dot(s,vec4(1.0,3.0,9.0,27.0));}
/* IRIS_26508_REGION_TO_FINAL_PROVENANCE_AUTHORITY */
void main(){
 ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,packedSize)))return;
 vec4 normal=texelFetch(normalCfa,p,0),candidateRgb=texelFetch(candidateCfa,p,0);float code=texelFetch(candidateProvenance,p,0).r;
 vec4 outv=normal,state=vec4(0.0);vec2 uv=(vec2(p)+vec2(0.5))/vec2(packedSize);float mgc=clamp(texture(mgcWeight,uv).r,0.0,1.0);bool region=texelFetch(regionTexture,p,0).r>0.5;
 for(int q=0;q<4;++q){float s=stateFrom(code,q);if(abs(s-2.0)<0.25){if(region&&mgc>0.04){setComponent(outv,q,component(candidateRgb,q));state[q]=2.0;atomicAdd(shortDiag[D_RECOVERED],1u);atomicAdd(shortDiag[P_RECOVERED+uint(q)],1u);}else{state[q]=1.0;if(mgc>0.04){atomicAdd(shortDiag[D_TOPOLOGY_REJECT],1u);atomicAdd(shortDiag[P_TOPOLOGY_REJECT+uint(q)],1u);}atomicAdd(shortDiag[D_UNRECOVERABLE],1u);atomicAdd(shortDiag[P_UNRECOVERABLE+uint(q)],1u);}}else{state[q]=s;if(abs(s-1.0)<0.25){atomicAdd(shortDiag[D_UNRECOVERABLE],1u);atomicAdd(shortDiag[P_UNRECOVERABLE+uint(q)],1u);}}}
 imageStore(outCfa,p,outv);imageStore(outProvenance,p,vec4(encode(state),0.0,0.0,0.0));
}
'''

SHORT_WEIGHT_SHADER = r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
precision highp image2D;
uniform highp sampler2D highlightProvenance;
uniform ivec2 packedSize;
layout(rgba32f,binding=0) uniform highp writeonly image2D outWeight;
float divv(int q){return q==0?1.0:(q==1?3.0:(q==2?9.0:27.0));}
/* IRIS_26508_REGION_FINAL_SHORT_PHASE_WEIGHT
 * Region membership has already finalized provenance. This pass contains no local
 * topology heuristic; each physically retained SHORT_VALIDATED phase gets unit
 * semantic permission and MGC remains the independent frame-weight authority.
 */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,packedSize)))return;float code=texelFetch(highlightProvenance,p,0).r;vec4 w=vec4(0.0);for(int q=0;q<4;++q){float s=mod(floor(code/divv(q)),3.0);w[q]=abs(s-2.0)<0.25?1.0:0.0;}imageStore(outWeight,p,w);}
'''

AUX_DECL_OLD = '''            GLTexture iris26480ShortWbCfa=null,iris26480Recovered=null;MotionV2Alignment.Result iris26480ShortAlignment=null;
            GLTexture irisV13ShadowRaw=null,irisV13ShadowCfa=null,irisV13ShadowWbCfa=null,irisV13ShadowRecovered=null;
            GLTexture iris26501ShadowWeight=null,iris26501ShadowCov=null;
            GLTexture iris26501ShortWeight=null,iris26501ShortCov=null;
            MotionV2Alignment.Result irisV13ShadowAlignment=null; GLBuffer irisV13ShadowDiag=null;
'''
AUX_DECL_NEW = '''            GLTexture iris26480ShortWbCfa=null,iris26480Recovered=null;MotionV2Alignment.Result iris26480ShortAlignment=null;
            GLTexture irisV13ShadowRaw=null,irisV13ShadowCfa=null,irisV13ShadowWbCfa=null,irisV13ShadowRecovered=null;
            GLTexture iris26501ShadowWeight=null,iris26501ShadowCov=null;
            GLTexture iris26501ShortWeight=null,iris26501ShortCov=null;
            MotionV2Alignment.Result irisV13ShadowAlignment=null; GLBuffer irisV13ShadowDiag=null;
            /* IRIS_26508_AUX_MGC_LIFETIME_OWNER: dedicated resources survive both Long and Short. */
            GLTexture iris26508AuxGuide=null,iris26508AuxUnblocker=null,iris26508AuxRejectA=null,iris26508AuxRejectB=null,iris26508AuxRejectC=null;
            GLTexture iris26508AuxSmallLuma=null,iris26508AuxSmallRaw=null,iris26508AuxSmallFiltered=null,iris26508AuxFinalWeight=null;
            GLTexture iris26508BridgeRaw=null,iris26508BridgeCfa=null,iris26508BridgeWbCfa=null,iris26508ComposedFlow=null;
            GLTexture iris26508ShortCandidateCfa=null,iris26508ShortCandidateProvenance=null,iris26508RegionA=null,iris26508RegionB=null;
            MotionV2Alignment.Result iris26508ReferenceToBridgeAlignment=null,iris26508BridgeToShortAlignment=null;
'''

AUX_MGC_ALLOC = r'''                        if(iris26508AuxGuide==null)iris26508AuxGuide=new GLTexture(iris26487GuideSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                        if(iris26508AuxUnblocker==null)iris26508AuxUnblocker=new GLTexture(iris26487UnblockerSize,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                        if(iris26508AuxRejectA==null)iris26508AuxRejectA=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                        if(iris26508AuxRejectB==null)iris26508AuxRejectB=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        if(iris26508AuxRejectC==null)iris26508AuxRejectC=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                        if(iris26508AuxSmallLuma==null)iris26508AuxSmallLuma=new GLTexture(iris26487RejectSmallSize,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        if(iris26508AuxSmallRaw==null)iris26508AuxSmallRaw=new GLTexture(iris26487RejectSmallSize,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        if(iris26508AuxSmallFiltered==null)iris26508AuxSmallFiltered=new GLTexture(iris26487RejectSmallSize,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                        if(iris26508AuxFinalWeight==null)iris26508AuxFinalWeight=new GLTexture(iris26487MergeWeightSize,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
'''

LONG_BLOCK = r'''                /* IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER
                 * Long-A keeps exact physical capture identity and Wronski alignment, but the
                 * separate shadow_aux_bayer_fuse semantic authority is retired. Exposure-normalized
                 * Long now receives the same MGC rejection chain and writes directly into the same
                 * persistent additive Spatial-RGB accumulators as Normal. One normalization remains.
                 */
                if(directBayer&&irisV13ShadowAuxFrame!=null&&irisV13ShadowAuxFrame.buffer!=null
                        &&referenceFrame!=null&&referenceFrame.motionV2ExposureEnergy>0.0
                        &&irisV13ShadowAuxFrame.motionV2ExposureEnergy>referenceFrame.motionV2ExposureEnergy
                        &&wronskiPreparedAlignment!=null&&currentDirectFrameSupport!=null){
                    float irisV13ShadowToNormal=(float)(referenceFrame.motionV2ExposureEnergy/irisV13ShadowAuxFrame.motionV2ExposureEnergy);
                    if(irisV13ShadowToNormal>=0.15f&&irisV13ShadowToNormal<=0.84f){
                        long irisV13AlignStart=System.nanoTime();
                        irisV13ShadowRaw=new GLTexture(raw,new GLFormat(GLFormat.DataType.UNSIGNED_16,1),irisV13ShadowAuxFrame.buffer,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        irisV13ShadowCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        float[] shadowBlack=irisV13ShadowAuxFrame.motionV2BlackLevelValid?irisV13ShadowAuxFrame.motionV2BlackLevel:blackLevel;
                        float shadowWhite=irisV13ShadowAuxFrame.motionV2WhiteLevelValid?irisV13ShadowAuxFrame.motionV2WhiteLevel:(float)parameters.whiteLevel;
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/raw_to_cfa",true);glProg.setVar("whiteLevel",shadowWhite);glProg.setVar("blackLevel",shadowBlack);glProg.setVar("exposure",1.0f);glProg.setTexture("inTexture",irisV13ShadowRaw);glProg.setTextureCompute("outTexture",irisV13ShadowCfa,true);glProg.computeAutoDeferred(rawHalf,1);
                        float rr=directSensorGains[0]/Math.max(directSensorGains[1],1e-6f),bb=directSensorGains[2]/Math.max(directSensorGains[1],1e-6f);
                        float alignmentScale=irisV13ShadowToNormal*iris26487ReferenceExposureScale;
                        irisV13ShadowWbCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_wb_cfa",true);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("wbR",rr*alignmentScale);glProg.setVar("wbG",alignmentScale);glProg.setVar("wbB",bb*alignmentScale);glProg.setTextureCompute("inputCfa",irisV13ShadowCfa,false);glProg.setTextureCompute("outputCfa",irisV13ShadowWbCfa,true);glProg.computeAutoDeferred(rawHalf,1);
                        irisV13ShadowAlignment=MotionV2WronskiAlignment.alignPrepared(wronskiPreparedAlignment,glProg,irisV13ShadowWbCfa);
                        irisV13ShadowAlignDispatchMs=(System.nanoTime()-irisV13AlignStart)/1000000L;
                        Iris26487Noise iris26501ShadowSensorNoise=iris26487FrameNoise(irisV13ShadowAuxFrame,noiseS,noiseO);
                        float[] iris26501ShadowWbNoise=iris26487WbNoiseRgb(iris26501ShadowSensorNoise,(int)parameters.cfaPattern,alignmentScale,rr,bb);
                        iris26501ShadowCov=new GLTexture(iris26487GuideSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                        iris26501RenderRgbCovariance(glProg,raw,rawHalf,iris26487GuideSize,irisV13ShadowRaw,iris26501ShadowCov,(int)parameters.cfaPattern,shadowBlack,shadowWhite,alignmentScale,rr,bb,iris26501ShadowWbNoise[1],iris26501ShadowWbNoise[4]);
                        iris26501RenderChromaGuide(glProg,raw,irisV13ShadowRaw,iris26501ChromaGuideScratch,(int)parameters.cfaPattern,shadowBlack,shadowWhite,alignmentScale,rr,bb);
''' + AUX_MGC_ALLOC + r'''                        long irisV13FuseStart=System.nanoTime();
                        float[] iris26508LongGreenPhysicalNoise=iris26487GreenPhysicalNoise(iris26501ShadowSensorNoise,(int)parameters.cfaPattern);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_guide",true);glProg.setVar("rawSize",raw);glProg.setVar("guideSize",iris26487GuideSize);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("blackLevel",shadowBlack);glProg.setVar("whiteLevel",shadowWhite);glProg.setVar("exposureScale",alignmentScale);glProg.setVar("wbR",rr);glProg.setVar("wbB",bb);glProg.setVar("noiseShot",new float[]{iris26501ShadowWbNoise[0],iris26501ShadowWbNoise[1],iris26501ShadowWbNoise[2]});glProg.setVar("noiseRead",new float[]{iris26501ShadowWbNoise[3],iris26501ShadowWbNoise[4],iris26501ShadowWbNoise[5]});glProg.setTexture("rawTexture",irisV13ShadowRaw);glProg.setTextureCompute("outputGuide",iris26508AuxGuide,true);glProg.computeAutoDeferred(iris26487GuideSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_unblocker",true);glProg.setVar("rawHalf",rawHalf);glProg.setVar("unblockerSize",iris26487UnblockerSize);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("physicalExposureScale",alignmentScale);glProg.setVar("greenShot",iris26508LongGreenPhysicalNoise[0]);glProg.setVar("greenRead",iris26508LongGreenPhysicalNoise[1]);glProg.setTexture("physicalCfa",irisV13ShadowCfa);glProg.setTextureCompute("outUnblocker",iris26508AuxUnblocker,true);glProg.computeAutoDeferred(iris26487UnblockerSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_base",true);glProg.setVar("rawHalf",rawHalf);glProg.setVar("guideSize",iris26487GuideSize);glProg.setVar("referenceNoiseShot",new float[]{iris26487ReferenceWbNoise[0],iris26487ReferenceWbNoise[1],iris26487ReferenceWbNoise[2]});glProg.setVar("referenceNoiseRead",new float[]{iris26487ReferenceWbNoise[3],iris26487ReferenceWbNoise[4],iris26487ReferenceWbNoise[5]});glProg.setVar("currentNoiseShot",new float[]{iris26501ShadowWbNoise[0],iris26501ShadowWbNoise[1],iris26501ShadowWbNoise[2]});glProg.setVar("currentNoiseRead",new float[]{iris26501ShadowWbNoise[3],iris26501ShadowWbNoise[4],iris26501ShadowWbNoise[5]});glProg.setVar("flowVariationThreshold",iris26507FlowVariationThreshold);glProg.setTexture("referenceGuide",wronskiReferenceGuide);glProg.setTexture("currentGuide",iris26508AuxGuide);glProg.setTexture("flowTexture",irisV13ShadowAlignment.flowTexture);glProg.setTexture("unblockerTexture",iris26508AuxUnblocker);glProg.setTextureCompute("outReverseWeight",iris26508AuxRejectA,true);glProg.setTextureCompute("outPixelDifference",iris26508AuxRejectB,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_h",true);glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",iris26508AuxRejectB);glProg.setTextureCompute("outEvidence",iris26508AuxRejectC,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_v",true);glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",iris26508AuxRejectC);glProg.setTextureCompute("outEvidence",iris26508AuxRejectB,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_reduce4",true);glProg.setVar("inputSize",rawHalf);glProg.setVar("outputSize",iris26487RejectSmallSize);glProg.setTexture("referenceGray",iris26488ReferenceGray);glProg.setTexture("inputRejection",iris26508AuxRejectA);glProg.setTextureCompute("outLuma",iris26508AuxSmallLuma,true);glProg.setTextureCompute("outRejection",iris26508AuxSmallRaw,true);glProg.computeAutoDeferred(iris26487RejectSmallSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_bilateral",true);glProg.setVar("smallSize",iris26487RejectSmallSize);glProg.setTexture("inputLuma",iris26508AuxSmallLuma);glProg.setTexture("inputRejection",iris26508AuxSmallRaw);glProg.setTextureCompute("outFiltered",iris26508AuxSmallFiltered,true);glProg.computeAutoDeferred(iris26487RejectSmallSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_postprocess",true);glProg.setVar("fullSize",rawHalf);glProg.setVar("smallSize",iris26487RejectSmallSize);glProg.setTexture("originalRejection",iris26508AuxRejectA);glProg.setTexture("filteredRejection",iris26508AuxSmallFiltered);glProg.setTexture("pixelDifference",iris26508AuxRejectB);glProg.setTextureCompute("outRejection",iris26508AuxRejectC,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_dilate",true);glProg.setVar("inputSize",rawHalf);glProg.setVar("outputSize",iris26487MergeWeightSize);glProg.setTexture("inputRejection",iris26508AuxRejectC);glProg.setTextureCompute("outWeight",iris26508AuxFinalWeight,true);glProg.computeAutoDeferred(iris26487MergeWeightSize,1);
                        iris26501ContributeRgbFrame(glProg,iris26501RgbFramebuffer,raw,rawHalf,irisV13ShadowRaw,iris26501ChromaGuideScratch,irisV13ShadowAlignment.flowTexture,iris26508AuxFinalWeight,iris26501ShadowCov,iris26508AuxFinalWeight,(int)parameters.cfaPattern,shadowBlack,shadowWhite,alignmentScale,rr,bb,iris26501ShadowWbNoise[1],iris26501ShadowWbNoise[4],false,true,false);
                        iris26501SemanticHdrContributedFrames++;
                        irisV13ShadowFuseDispatchMs=(System.nanoTime()-irisV13FuseStart)/1000000L;
                        Log.i(TAG,"IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER"
                                +" longActualEnergy="+irisV13ShadowAuxFrame.motionV2ExposureEnergy
                                +" referenceEnergy="+referenceFrame.motionV2ExposureEnergy
                                +" exposureScale="+alignmentScale
                                +" longAlignMs="+irisV13ShadowAlignDispatchMs
                                +" longSharedFusionMs="+irisV13ShadowFuseDispatchMs
                                +" samePersistentRgbAccumulator=true oneFinalNormalization=true"
                                +" postHocShadowSemanticFuse=false helperBayerMutation=false");
                    }
                }
'''

SHORT_BLOCK = r'''                if(directBayer&&shortHighlightFrame!=null&&shortHighlightFrame.buffer!=null&&referenceFrame!=null
                        &&referenceFrame.motionV2ExposureEnergy>0.0&&shortHighlightFrame.motionV2ExposureEnergy>0.0
                        &&shortHighlightFrame.motionV2ExposureEnergy<referenceFrame.motionV2ExposureEnergy
                        &&wronskiPreparedAlignment!=null){
                    float shortToNormalScale=(float)Math.max(1.0,Math.min(8.0,referenceFrame.motionV2ExposureEnergy/shortHighlightFrame.motionV2ExposureEnergy));
                    iris26480ShortRaw=new GLTexture(raw,new GLFormat(GLFormat.DataType.UNSIGNED_16,1),shortHighlightFrame.buffer,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    iris26480ShortCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    float[] iris26490ShortBlack=shortHighlightFrame.motionV2BlackLevelValid?shortHighlightFrame.motionV2BlackLevel:blackLevel;
                    float iris26490ShortWhite=shortHighlightFrame.motionV2WhiteLevelValid?shortHighlightFrame.motionV2WhiteLevel:(float)parameters.whiteLevel;
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/raw_to_cfa",true);glProg.setVar("whiteLevel",iris26490ShortWhite);glProg.setVar("blackLevel",iris26490ShortBlack);glProg.setVar("exposure",1.0f);glProg.setTexture("inTexture",iris26480ShortRaw);glProg.setTextureCompute("outTexture",iris26480ShortCfa,true);glProg.computeAutoDeferred(rawHalf,1);
                    float r=directSensorGains[0]/Math.max(directSensorGains[1],1e-6f),b=directSensorGains[2]/Math.max(directSensorGains[1],1e-6f);
                    float iris26490ShortAlignmentScale=shortToNormalScale*iris26487ReferenceExposureScale;
                    iris26480ShortWbCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_wb_cfa",true);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("wbR",r*iris26490ShortAlignmentScale);glProg.setVar("wbG",iris26490ShortAlignmentScale);glProg.setVar("wbB",b*iris26490ShortAlignmentScale);glProg.setTextureCompute("inputCfa",iris26480ShortCfa,false);glProg.setTextureCompute("outputCfa",iris26480ShortWbCfa,true);glProg.computeAutoDeferred(rawHalf,1);

                    boolean iris26508BridgeUsable=iris26508GeometryBridgeFrame!=null
                            &&iris26508GeometryBridgeFrame.buffer!=null
                            &&iris26508GeometryBridgeFrame.motionV2FrameRole==ImageFrame.MotionV2FrameRole.NORMAL
                            &&iris26508GeometryBridgeFrame.motionV2ActualExposureNs>0L
                            &&iris26508GeometryBridgeFrame.motionV2ActualIso>0
                            &&iris26508GeometryBridgeFrame.motionV2ExposureEnergy>0.0;
                    double iris26508BridgeEnergyRatio=iris26508BridgeUsable?iris26508GeometryBridgeFrame.motionV2ExposureEnergy/referenceFrame.motionV2ExposureEnergy:0.0;
                    long iris26508ReferenceToShortDeltaNs=Math.abs(shortHighlightFrame.timestamp-referenceFrame.timestamp);
                    long iris26508BridgeToShortDeltaNs=iris26508BridgeUsable?Math.abs(shortHighlightFrame.timestamp-iris26508GeometryBridgeFrame.timestamp):Long.MAX_VALUE;
                    iris26508BridgeUsable=iris26508BridgeUsable&&iris26508BridgeEnergyRatio>=0.80&&iris26508BridgeEnergyRatio<=1.25
                            &&iris26508BridgeToShortDeltaNs<iris26508ReferenceToShortDeltaNs;
                    float iris26508BridgeToNormalScale=iris26508BridgeUsable?(float)(referenceFrame.motionV2ExposureEnergy/iris26508GeometryBridgeFrame.motionV2ExposureEnergy):1.0f;
                    Log.i(TAG,"IRIS_26508_NEAREST_NORMAL_BRIDGE_SELECTION"
                            +" finalReferenceTimestamp="+referenceFrame.timestamp
                            +" bridgeTimestamp="+(iris26508GeometryBridgeFrame==null?0L:iris26508GeometryBridgeFrame.timestamp)
                            +" shortTimestamp="+shortHighlightFrame.timestamp
                            +" referenceToShortDeltaMs="+(iris26508ReferenceToShortDeltaNs/1000000.0)
                            +" bridgeToShortDeltaMs="+(iris26508BridgeToShortDeltaNs==Long.MAX_VALUE?-1.0:iris26508BridgeToShortDeltaNs/1000000.0)
                            +" bridgeEnergyRatio="+iris26508BridgeEnergyRatio
                            +" bridgeUsable="+iris26508BridgeUsable
                            +" sameGenerationCaptureOwner=true nearestWithinFrozenCandidates=true"
                            +" geometryOnly=true pixelContributor=false unrelatedFallback=false");

                    if(iris26508BridgeUsable){
                        iris26508BridgeRaw=new GLTexture(raw,new GLFormat(GLFormat.DataType.UNSIGNED_16,1),iris26508GeometryBridgeFrame.buffer,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        iris26508BridgeCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        float[] bridgeBlack=iris26508GeometryBridgeFrame.motionV2BlackLevelValid?iris26508GeometryBridgeFrame.motionV2BlackLevel:blackLevel;
                        float bridgeWhite=iris26508GeometryBridgeFrame.motionV2WhiteLevelValid?iris26508GeometryBridgeFrame.motionV2WhiteLevel:(float)parameters.whiteLevel;
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/raw_to_cfa",true);glProg.setVar("whiteLevel",bridgeWhite);glProg.setVar("blackLevel",bridgeBlack);glProg.setVar("exposure",1.0f);glProg.setTexture("inTexture",iris26508BridgeRaw);glProg.setTextureCompute("outTexture",iris26508BridgeCfa,true);glProg.computeAutoDeferred(rawHalf,1);
                        iris26508BridgeWbCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        float bridgeAlignmentScale=iris26508BridgeToNormalScale*iris26487ReferenceExposureScale;
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_wb_cfa",true);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("wbR",r*bridgeAlignmentScale);glProg.setVar("wbG",bridgeAlignmentScale);glProg.setVar("wbB",b*bridgeAlignmentScale);glProg.setTextureCompute("inputCfa",iris26508BridgeCfa,false);glProg.setTextureCompute("outputCfa",iris26508BridgeWbCfa,true);glProg.computeAutoDeferred(rawHalf,1);
                        iris26508ReferenceToBridgeAlignment=MotionV2WronskiAlignment.alignPrepared(wronskiPreparedAlignment,glProg,iris26508BridgeWbCfa);
                        MotionV2WronskiAlignment.PreparedReference iris26508BridgePrepared=null;
                        try{
                            iris26508BridgePrepared=MotionV2WronskiAlignment.prepareReference(rawHalf,parameters.cfaPattern,canonicalGain,mfsrSnr,glProg,iris26508BridgeWbCfa);
                            iris26508BridgeToShortAlignment=MotionV2WronskiAlignment.alignPrepared(iris26508BridgePrepared,glProg,iris26480ShortWbCfa);
                        }finally{if(iris26508BridgePrepared!=null)iris26508BridgePrepared.close();}
                        iris26508ComposedFlow=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bridge_flow_compose_26508",true);glProg.setVar("packedSize",rawHalf);glProg.setTexture("referenceToBridgeFlow",iris26508ReferenceToBridgeAlignment.flowTexture);glProg.setTexture("bridgeToShortFlow",iris26508BridgeToShortAlignment.flowTexture);glProg.setTextureCompute("outFlow",iris26508ComposedFlow,true);glProg.computeAutoDeferred(rawHalf,1);
                    }

                    Iris26487Noise iris26501ShortSensorNoise=iris26487FrameNoise(shortHighlightFrame,noiseS,noiseO);
                    float[] iris26501ShortWbNoise=iris26487WbNoiseRgb(iris26501ShortSensorNoise,(int)parameters.cfaPattern,iris26490ShortAlignmentScale,r,b);
                    iris26501ShortCov=new GLTexture(iris26487GuideSize,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_LINEAR,GL_CLAMP_TO_EDGE);
                    iris26501RenderRgbCovariance(glProg,raw,rawHalf,iris26487GuideSize,iris26480ShortRaw,iris26501ShortCov,(int)parameters.cfaPattern,iris26490ShortBlack,iris26490ShortWhite,iris26490ShortAlignmentScale,r,b,iris26501ShortWbNoise[1],iris26501ShortWbNoise[4]);
                    iris26501RenderChromaGuide(glProg,raw,iris26480ShortRaw,iris26501ChromaGuideScratch,(int)parameters.cfaPattern,iris26490ShortBlack,iris26490ShortWhite,iris26490ShortAlignmentScale,r,b);

                    iris26508ShortCandidateCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    iris26508ShortCandidateProvenance=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    iris26496ShortDiag=new GLBuffer(64,new GLFormat(GLFormat.DataType.UNSIGNED_32));iris26496ShortDiag.uploadBuffer(new int[64],64);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/short_highlight_bayer_recover",true);glProg.setVar("packedSize",rawHalf);glProg.setVar("shortToNormalScale",shortToNormalScale);glProg.setVar("bridgeToNormalScale",iris26508BridgeToNormalScale);glProg.setVar("physicalClipThreshold",IRIS26487_CLIP_THRESHOLD);glProg.setVar("shortClipThreshold",IRIS26487_CLIP_THRESHOLD);glProg.setVar("minimumBridgeConfidence",0.30f);glProg.setVar("referenceExposureScale",iris26487ReferenceExposureScale);glProg.setVar("bridgeAvailable",iris26508BridgeUsable?1:0);glProg.setTexture("normalCfa",imageOutput);glProg.setTexture("bridgeCfa",iris26508BridgeUsable?iris26508BridgeCfa:imageOutput);glProg.setTexture("shortCfa",iris26480ShortCfa);glProg.setTexture("bridgeFlowTexture",iris26508BridgeUsable?iris26508ReferenceToBridgeAlignment.flowTexture:imageOutput);glProg.setTexture("composedFlowTexture",iris26508BridgeUsable?iris26508ComposedFlow:imageOutput);glProg.setTextureCompute("outCfa",iris26508ShortCandidateCfa,true);glProg.setTextureCompute("outProvenance",iris26508ShortCandidateProvenance,true);glProg.setBufferCompute("ShortDiagBuf",iris26496ShortDiag);glProg.computeAutoDeferred(rawHalf,1);

                    if(iris26508BridgeUsable){
''' + AUX_MGC_ALLOC + r'''                        float[] iris26508ShortGreenPhysicalNoise=iris26487GreenPhysicalNoise(iris26501ShortSensorNoise,(int)parameters.cfaPattern);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_guide",true);glProg.setVar("rawSize",raw);glProg.setVar("guideSize",iris26487GuideSize);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("blackLevel",iris26490ShortBlack);glProg.setVar("whiteLevel",iris26490ShortWhite);glProg.setVar("exposureScale",iris26490ShortAlignmentScale);glProg.setVar("wbR",r);glProg.setVar("wbB",b);glProg.setVar("noiseShot",new float[]{iris26501ShortWbNoise[0],iris26501ShortWbNoise[1],iris26501ShortWbNoise[2]});glProg.setVar("noiseRead",new float[]{iris26501ShortWbNoise[3],iris26501ShortWbNoise[4],iris26501ShortWbNoise[5]});glProg.setTexture("rawTexture",iris26480ShortRaw);glProg.setTextureCompute("outputGuide",iris26508AuxGuide,true);glProg.computeAutoDeferred(iris26487GuideSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_unblocker",true);glProg.setVar("rawHalf",rawHalf);glProg.setVar("unblockerSize",iris26487UnblockerSize);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);glProg.setVar("physicalExposureScale",iris26490ShortAlignmentScale);glProg.setVar("greenShot",iris26508ShortGreenPhysicalNoise[0]);glProg.setVar("greenRead",iris26508ShortGreenPhysicalNoise[1]);glProg.setTexture("physicalCfa",iris26480ShortCfa);glProg.setTextureCompute("outUnblocker",iris26508AuxUnblocker,true);glProg.computeAutoDeferred(iris26487UnblockerSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_base",true);glProg.setVar("rawHalf",rawHalf);glProg.setVar("guideSize",iris26487GuideSize);glProg.setVar("referenceNoiseShot",new float[]{iris26487ReferenceWbNoise[0],iris26487ReferenceWbNoise[1],iris26487ReferenceWbNoise[2]});glProg.setVar("referenceNoiseRead",new float[]{iris26487ReferenceWbNoise[3],iris26487ReferenceWbNoise[4],iris26487ReferenceWbNoise[5]});glProg.setVar("currentNoiseShot",new float[]{iris26501ShortWbNoise[0],iris26501ShortWbNoise[1],iris26501ShortWbNoise[2]});glProg.setVar("currentNoiseRead",new float[]{iris26501ShortWbNoise[3],iris26501ShortWbNoise[4],iris26501ShortWbNoise[5]});glProg.setVar("flowVariationThreshold",iris26507FlowVariationThreshold);glProg.setTexture("referenceGuide",wronskiReferenceGuide);glProg.setTexture("currentGuide",iris26508AuxGuide);glProg.setTexture("flowTexture",iris26508ComposedFlow);glProg.setTexture("unblockerTexture",iris26508AuxUnblocker);glProg.setTextureCompute("outReverseWeight",iris26508AuxRejectA,true);glProg.setTextureCompute("outPixelDifference",iris26508AuxRejectB,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_h",true);glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",iris26508AuxRejectB);glProg.setTextureCompute("outEvidence",iris26508AuxRejectC,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_v",true);glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",iris26508AuxRejectC);glProg.setTextureCompute("outEvidence",iris26508AuxRejectB,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_reduce4",true);glProg.setVar("inputSize",rawHalf);glProg.setVar("outputSize",iris26487RejectSmallSize);glProg.setTexture("referenceGray",iris26488ReferenceGray);glProg.setTexture("inputRejection",iris26508AuxRejectA);glProg.setTextureCompute("outLuma",iris26508AuxSmallLuma,true);glProg.setTextureCompute("outRejection",iris26508AuxSmallRaw,true);glProg.computeAutoDeferred(iris26487RejectSmallSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_bilateral",true);glProg.setVar("smallSize",iris26487RejectSmallSize);glProg.setTexture("inputLuma",iris26508AuxSmallLuma);glProg.setTexture("inputRejection",iris26508AuxSmallRaw);glProg.setTextureCompute("outFiltered",iris26508AuxSmallFiltered,true);glProg.computeAutoDeferred(iris26487RejectSmallSize,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_postprocess",true);glProg.setVar("fullSize",rawHalf);glProg.setVar("smallSize",iris26487RejectSmallSize);glProg.setTexture("originalRejection",iris26508AuxRejectA);glProg.setTexture("filteredRejection",iris26508AuxSmallFiltered);glProg.setTexture("pixelDifference",iris26508AuxRejectB);glProg.setTextureCompute("outRejection",iris26508AuxRejectC,true);glProg.computeAutoDeferred(rawHalf,1);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_dilate",true);glProg.setVar("inputSize",rawHalf);glProg.setVar("outputSize",iris26487MergeWeightSize);glProg.setTexture("inputRejection",iris26508AuxRejectC);glProg.setTextureCompute("outWeight",iris26508AuxFinalWeight,true);glProg.computeAutoDeferred(iris26487MergeWeightSize,1);

                        iris26508RegionA=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);iris26508RegionB=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_short_region_seed_26508",true);glProg.setVar("packedSize",rawHalf);glProg.setTexture("candidateProvenance",iris26508ShortCandidateProvenance);glProg.setTexture("mgcWeight",iris26508AuxFinalWeight);glProg.setTextureCompute("outRegion",iris26508RegionA,true);glProg.setBufferCompute("ShortDiagBuf",iris26496ShortDiag);glProg.computeAutoDeferred(rawHalf,1);
                        GLTexture iris26508RegionRead=iris26508RegionA,iris26508RegionWrite=iris26508RegionB;
                        for(int iris26508RegionPass=0;iris26508RegionPass<4;++iris26508RegionPass){glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_short_region_propagate_26508",true);glProg.setVar("packedSize",rawHalf);glProg.setTexture("candidateProvenance",iris26508ShortCandidateProvenance);glProg.setTexture("mgcWeight",iris26508AuxFinalWeight);glProg.setTexture("regionIn",iris26508RegionRead);glProg.setTextureCompute("outRegion",iris26508RegionWrite,true);glProg.computeAutoDeferred(rawHalf,1);GLTexture iris26508Swap=iris26508RegionRead;iris26508RegionRead=iris26508RegionWrite;iris26508RegionWrite=iris26508Swap;}
                        iris26480Recovered=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);iris26492RecoveredProvenance=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_short_region_finalize_26508",true);glProg.setVar("packedSize",rawHalf);glProg.setTexture("normalCfa",imageOutput);glProg.setTexture("candidateCfa",iris26508ShortCandidateCfa);glProg.setTexture("candidateProvenance",iris26508ShortCandidateProvenance);glProg.setTexture("mgcWeight",iris26508AuxFinalWeight);glProg.setTexture("regionTexture",iris26508RegionRead);glProg.setTextureCompute("outCfa",iris26480Recovered,true);glProg.setTextureCompute("outProvenance",iris26492RecoveredProvenance,true);glProg.setBufferCompute("ShortDiagBuf",iris26496ShortDiag);glProg.computeAutoDeferred(rawHalf,1);
                        iris26501ShortWeight=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_spatial_rgb_short_weight_26501",true);glProg.setVar("packedSize",rawHalf);glProg.setTexture("highlightProvenance",iris26492RecoveredProvenance);glProg.setTextureCompute("outWeight",iris26501ShortWeight,true);glProg.computeAutoDeferred(rawHalf,1);
                        iris26501ContributeRgbFrame(glProg,iris26501RgbFramebuffer,raw,rawHalf,iris26480ShortRaw,iris26501ChromaGuideScratch,iris26508ComposedFlow,iris26508AuxFinalWeight,iris26501ShortCov,iris26501ShortWeight,(int)parameters.cfaPattern,iris26490ShortBlack,iris26490ShortWhite,iris26490ShortAlignmentScale,r,b,iris26501ShortWbNoise[1],iris26501ShortWbNoise[4],false,true,true);
                        iris26501SemanticHdrContributedFrames++;
                        iris26480ReadbackOutput=iris26480Recovered;iris26492ReadbackProvenance=iris26492RecoveredProvenance;parameters.motionV2ShortHighlightRecoveryExecuted=true;
                        Log.i(TAG,"IRIS_26508_SHORT_BRIDGE_MGC_REGION_OWNER bridge=true composedWronski=true mgc=true gpuRegionPasses=4 regionTileFlood=8x8 bridgePixelContributor=false oneFinalRgbOwner=true");
                    }else{
                        iris26480ReadbackOutput=iris26508ShortCandidateCfa;iris26492ReadbackProvenance=iris26508ShortCandidateProvenance;parameters.motionV2ShortHighlightRecoveryExecuted=false;
                        Log.w(TAG,"IRIS_26508_SHORT_BRIDGE_UNAVAILABLE noDirectReferenceFallback=true recoveryIntentionallyCensored=true");
                    }
                }
'''

DIAG_BLOCK = r'''                if (iris26496ShortDiag != null) {
                    try {
                        int[] d=iris26496ShortDiag.readBufferIntegers(false);
                        if(d!=null&&d.length>=56){
                            long total=Integer.toUnsignedLong(d[0]),safe=Integer.toUnsignedLong(d[1]),shortClipped=Integer.toUnsignedLong(d[2]);
                            long noBridge=Integer.toUnsignedLong(d[3]),bridgeRejected=Integer.toUnsignedLong(d[4]),radiometryRejected=Integer.toUnsignedLong(d[5]);
                            long recovered=Integer.toUnsignedLong(d[6]),unrecoverable=Integer.toUnsignedLong(d[7]);
                            long mgcRejected=Integer.toUnsignedLong(d[13]),topologyRejected=Integer.toUnsignedLong(d[14]),candidate=Integer.toUnsignedLong(d[15]);
                            float denom=Math.max(total,1L);
                            Log.i(TAG,"IRIS_26508_SHORT_ARCHITECTURAL_RESULT"
                                    +" totalNormalClipped="+total
                                    +" shortPhysicallyAvailable="+safe+" shortPhysicallyAvailablePct="+(100.0f*safe/denom)
                                    +" shortPhysicallyClipped="+shortClipped+" shortPhysicallyClippedPct="+(100.0f*shortClipped/denom)
                                    +" noBridge="+noBridge+" noBridgePct="+(100.0f*noBridge/denom)
                                    +" bridgeGeometryRejected="+bridgeRejected+" bridgeGeometryRejectedPct="+(100.0f*bridgeRejected/denom)
                                    +" mgcRejected="+mgcRejected+" mgcRejectedPct="+(100.0f*mgcRejected/denom)
                                    +" regionTopologyRejected="+topologyRejected+" regionTopologyRejectedPct="+(100.0f*topologyRejected/denom)
                                    +" radiometryRejected="+radiometryRejected+" radiometryRejectedPct="+(100.0f*radiometryRejected/denom)
                                    +" physicalCandidates="+candidate+" candidatePct="+(100.0f*candidate/denom)
                                    +" recovered="+recovered+" recoveredPct="+(100.0f*recovered/denom)
                                    +" intentionallyUnrecoverableOrDisoccluded="+unrecoverable+" unrecoverablePct="+(100.0f*unrecoverable/denom)
                                    +" clippedByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(d,16,20))
                                    +" recoveredByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(d,20,24))
                                    +" shortClippedByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(d,24,28))
                                    +" noBridgeByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(d,28,32))
                                    +" bridgeRejectedByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(d,32,36))
                                    +" radiometryRejectedByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(d,36,40))
                                    +" unrecoverableByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(d,40,44))
                                    +" mgcRejectedByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(d,44,48))
                                    +" topologyRejectedByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(d,48,52))
                                    +" candidateByPhase="+java.util.Arrays.toString(java.util.Arrays.copyOfRange(d,52,56))
                                    +" oneGpuDrain=true");
                            if(total!=recovered+unrecoverable)Log.w(TAG,"IRIS_26508_SHORT_ACCOUNTING_MISMATCH total="+total+" recoveredPlusUnrecoverable="+(recovered+unrecoverable));
                            try{com.particlesdevs.photoncamera.util.MotionTrace.processingState("IRIS_26508_SHORT_ARCHITECTURAL_RESULT","total="+total+" recovered="+recovered+" unrecoverable="+unrecoverable+" noBridge="+noBridge+" bridgeRejected="+bridgeRejected+" mgcRejected="+mgcRejected+" topologyRejected="+topologyRejected);}catch(Throwable ignored){}
                        }
                    }catch(Throwable shortDiagError){Log.w(TAG,"IRIS_26508_SHORT_DIAGNOSTIC_READBACK_SKIPPED",shortDiagError);}
                }
'''


def cfa_host(src: str) -> str:
    if 'IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER' in src:
        fail('CFA host already contains 26508')
    for marker in ('IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY','IRIS_26507_SHORT_A_SHARED_MGC_PRECHROMA_GATE','IRIS_26507_LONG_A_SHARED_MGC_PRECHROMA_GATE'):
        if marker not in src:
            fail('CFA host missing reconstructed 26507 marker '+marker)

    take_short = '''            ImageFrame shortHighlightFrame = shortHighlightSlot == null
                    ? null : shortHighlightSlot.takeAndSeal();
'''
    src = one(src, take_short, take_short + '''            ImageFrame iris26508GeometryBridgeFrame = shortHighlightSlot == null
                    ? null : shortHighlightSlot.geometryBridgeSlot.takeAndSeal();
''', 'take immutable geometry bridge')
    src = one(src, AUX_DECL_OLD, AUX_DECL_NEW, 'aux ownership declarations')

    long_start = '                /* IRIS_26498_V13_SHADOW_AUX_REFERENCE_OWNED_ALIGNMENT\n'
    short_start = '                if(directBayer&&shortHighlightFrame!=null&&shortHighlightFrame.buffer!=null&&referenceFrame!=null\n'
    src = replace_span(src, long_start, short_start, LONG_BLOCK, 'replace Long semantic authority')

    final_norm = '''                if (directBayer) {
                    /* IRIS_26501_PROPER_SPATIAL_RGB_FINAL_NORMALIZATION
'''
    src = replace_span(src, short_start, final_norm, SHORT_BLOCK, 'replace old direct Short correspondence authority')

    diag_start = '                if (iris26496ShortDiag != null) {\n'
    provenance_start = '                if (directBayer && iris26492ReadbackProvenance != null) {\n'
    src = replace_span(src, diag_start, provenance_start, DIAG_BLOCK, 'replace Short diagnostics')

    cleanup_anchor = '''                if(irisV13ShadowRecovered!=null)irisV13ShadowRecovered.close();if(irisV13ShadowDiag!=null)irisV13ShadowDiag.close();
                /* IRIS_26498_V13_TAKEN_AUX_CPU_BUFFER_LIFETIME_FIX */
'''
    cleanup_new = '''                if(irisV13ShadowRecovered!=null)irisV13ShadowRecovered.close();if(irisV13ShadowDiag!=null)irisV13ShadowDiag.close();
                if(iris26508ReferenceToBridgeAlignment!=null)iris26508ReferenceToBridgeAlignment.close();if(iris26508BridgeToShortAlignment!=null)iris26508BridgeToShortAlignment.close();
                if(iris26508BridgeWbCfa!=null)iris26508BridgeWbCfa.close();if(iris26508BridgeCfa!=null)iris26508BridgeCfa.close();if(iris26508BridgeRaw!=null)iris26508BridgeRaw.close();if(iris26508ComposedFlow!=null)iris26508ComposedFlow.close();
                if(iris26508ShortCandidateCfa!=null)iris26508ShortCandidateCfa.close();if(iris26508ShortCandidateProvenance!=null)iris26508ShortCandidateProvenance.close();if(iris26508RegionA!=null)iris26508RegionA.close();if(iris26508RegionB!=null)iris26508RegionB.close();
                if(iris26508AuxFinalWeight!=null)iris26508AuxFinalWeight.close();if(iris26508AuxSmallFiltered!=null)iris26508AuxSmallFiltered.close();if(iris26508AuxSmallRaw!=null)iris26508AuxSmallRaw.close();if(iris26508AuxSmallLuma!=null)iris26508AuxSmallLuma.close();
                if(iris26508AuxRejectC!=null)iris26508AuxRejectC.close();if(iris26508AuxRejectB!=null)iris26508AuxRejectB.close();if(iris26508AuxRejectA!=null)iris26508AuxRejectA.close();if(iris26508AuxUnblocker!=null)iris26508AuxUnblocker.close();if(iris26508AuxGuide!=null)iris26508AuxGuide.close();
                /* IRIS_26498_V13_TAKEN_AUX_CPU_BUFFER_LIFETIME_FIX */
'''
    src = one(src, cleanup_anchor, cleanup_new, '26508 GPU cleanup')
    src = one(src,
              '                if(irisV13ShadowAuxFrame!=null)try{irisV13ShadowAuxFrame.close();}catch(Throwable ignored){}\n',
              '                if(irisV13ShadowAuxFrame!=null)try{irisV13ShadowAuxFrame.close();}catch(Throwable ignored){}\n                if(iris26508GeometryBridgeFrame!=null)try{iris26508GeometryBridgeFrame.close();}catch(Throwable ignored){}\n',
              'geometry bridge CPU lifetime')
    return src


def short_recovery(_src: str) -> str:
    if 'IRIS_26497_SHORT_CORRESPONDENCE_REFINEMENT' not in _src:
        fail('old Short correspondence marker missing before replacement')
    if 'IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY' not in _src:
        fail('old boundary Short authority missing before replacement')
    return SHORT_RECOVERY_SHADER

def short_weight(_src: str) -> str:
    if 'IRIS_26507_GPU_LOCAL_8_CONNECTED_SHORT_TOPOLOGY' not in _src:
        fail('26507 local topology marker missing before replacement')
    return SHORT_WEIGHT_SHADER


def main():
    global ROOT
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    args=ap.parse_args();ROOT=args.root.resolve()
    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',motion_batch)
    edit('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',capture_controller)
    edit('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',cfa_host)
    edit('app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',short_recovery)
    edit('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',short_weight)
    add('app/src/main/assets/shaders/motionv2/mfsr_bridge_flow_compose_26508.glsl',BRIDGE_FLOW_SHADER)
    add('app/src/main/assets/shaders/motionv2/mfsr_short_region_seed_26508.glsl',REGION_SEED_SHADER)
    add('app/src/main/assets/shaders/motionv2/mfsr_short_region_propagate_26508.glsl',REGION_PROPAGATE_SHADER)
    add('app/src/main/assets/shaders/motionv2/mfsr_short_region_finalize_26508.glsl',REGION_FINALIZE_SHADER)
    print('PASS: 26508 architectural convergence transform applied')

if __name__=='__main__':
    main()
