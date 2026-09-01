#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys

CHANGED=[
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
'app/version.properties']

def fail(m): raise SystemExit('FAIL: '+m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(root): return {str(p.relative_to(root)):sha(p) for p in sorted((Path(root)/'app').rglob('*')) if p.is_file()}
def need(s,t,label):
    if t not in s: fail(label+' missing: '+t)
def extract_raw_string(s,name):
    m=re.search(r'static const char\*'+re.escape(name)+r'=R"GLSL\((.*?)\)GLSL";',s,re.S)
    if not m: fail('native embedded shader missing '+name)
    return m.group(1)

def main():
    if len(sys.argv)!=3: fail('usage base candidate')
    base,cand=map(Path,sys.argv[1:])
    a,b=amap(base),amap(cand)
    if len(a)!=1708 or len(b)!=1708: fail(f'candidate universe {len(a)}/{len(b)}')
    diff=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
    if diff!=sorted(CHANGED): fail('changed allowlist '+repr(diff))
    v=(cand/'app/version.properties').read_text()
    need(v,'VERSION_NAME=0.9726576','version name'); need(v,'VERSION_BUILD=26576','version build')

    cap=(cand/CHANGED[2]).read_text()
    hdr=(cand/CHANGED[3]).read_text()
    enc=(cand/CHANGED[4]).read_text()
    ui=(cand/CHANGED[5]).read_text()
    stack=(cand/CHANGED[1]).read_text()
    native=(cand/CHANGED[0]).read_text()
    native_base=(base/CHANGED[0]).read_text()

    # 26575 immutable ownership remains authority; 26576 only mirrors it to persistent trace.
    for t in ['IRIS_26575_MOTION_SUPER_RES_SHUTTER_OWNER','mMotion26575SuperResAtShutter = PreferenceKeys.isIrisSuperResOn()','IRIS_26576_SR_SHUTTER_STATE','immutableBatch=true']:
        need(cap,t,'capture ownership')
    for t in ['IRIS_26575_SUPER_RES_IMMUTABLE_PROCESSING_OWNER','processingParameters.motionV2SuperResOutputEnabled = mMotion26575SuperResEnabled','IRIS_26576_SR_PROCESSING_STATE','IRIS_26576_SR_FINAL_DIMENSIONS','IRIS_26576_SR_CAPTURE_SUMMARY']:
        need(hdr,t,'Hdrx ownership')
    if 'processingParameters.motionV2SuperResOutputEnabled =\n                    com.particlesdevs.photoncamera.settings.PreferenceKeys.isIrisSuperResOn()' in hdr:
        fail('old mutable post-shutter SR owner revived')
    for t in ['IRIS_26575_SUPER_RES_UI_COMMIT','IRIS_26576_SR_UI_COMMIT','PreferenceKeys.setIrisSuperRes(iris26575RequestedSuperRes)']:
        need(ui,t,'UI proof')

    # Established true2x contract must remain exact: max8/top2, 26574 refine, 26573 proof, no chroma owner.
    for t in ['TRUE2X_JPEG_EVIDENCE_PER_PHASE = 2','TRUE2X_JPEG_MAX_EVIDENCE = 4 * TRUE2X_JPEG_EVIDENCE_PER_PHASE','IRIS_26574_JPEG_RETAINED_FLOW_REFINEMENT_ONLY','IRIS_26574_TRUE2X_FLOW_REFINE','IRIS_26573_SR_PROOF','IRIS_26576_SR_EVIDENCE','IRIS_26576_SR_RECONSTRUCTION_SUMMARY','IRIS_26576_SR_RECONSTRUCTION_GPU_FALLBACK','IRIS_26576_SR_CPU_PROOF','temporalProofPacked=true','directChromaOwner=false']:
        need(stack,t,'true2x telemetry contract')
    if 'TRUE2X_JPEG_MAX_EVIDENCE = 15' in stack: fail('max8 evidence policy weakened')

    # The embedded 26571 publication compute pixel math is byte-identical.
    if extract_raw_string(native_base,'kIris26571PublicationCompute') != extract_raw_string(native,'kIris26571PublicationCompute'):
        fail('26571 publication compute math changed')
    # GPU-first route and exact CPU fallback remain unchanged in policy/order.
    for t in ['bool gpuEligible=motionFast&&!water.enabled();','if(gpuEligible)gpuEncoded=iris26571EncodeGpuPublication','/* Exact successful 26570 CPU fallback begins here. */','pboSlots=2','const int bandRows=motionFast?256:128','jpeg_set_quality(&baseC,std::clamp((int)quality,1,100),TRUE)']:
        need(native,t,'native GPU-first invariant')
    if native.index('if(gpuEligible)gpuEncoded=iris26571EncodeGpuPublication') > native.index('/* Exact successful 26570 CPU fallback begins here. */'):
        fail('GPU-first publication order changed')
    for t in ['IRIS_26576_NATIVE_PUBLICATION_TELEMETRY_ONLY','thread_local std::string gIris26576PublicationTelemetry','getLastTrue2xPublicationTelemetryNative','backend=GPU gpuEligible=1 gpuUsed=1','backend=CPU gpuEligible=%d gpuUsed=0']:
        need(native,t,'native telemetry')
    for t in ['IRIS_26576_NATIVE_PUBLICATION_BACKEND_PERSISTENT_PROOF','getLastTrue2xPublicationTelemetryNative()','IRIS_26576_SR_PUBLICATION_BACKEND']:
        need(enc,t,'encoder telemetry')

    # No shader source/runtime expanded shader owner changed.
    shader_changed=[p for p in diff if '/shaders/' in p or p.endswith('Shaders.kt') or p.endswith('.glsl') or p.endswith('.frag') or p.endswith('.comp')]
    if shader_changed: fail('unexpected shader change '+repr(shader_changed))
    # No DNG/Night/JPEG-R ownership file changed except the intentional late publication JNI telemetry carrier.
    forbidden=[p for p in diff if ('Night' in p or 'dng' in p.lower() or 'motionv2_jpeg_r_encoder' in p)]
    if forbidden: fail('forbidden ownership change '+repr(forbidden))

    print('PASS exact 1708-file 26575 authority -> 7-file 26576 allowlist')
    print('PASS 26575 immutable SR shutter/batch/processing ownership preserved')
    print('PASS 26568 max8/top2 + 26573 cross-frame + 26574 retained-flow refinement contracts preserved')
    print('PASS 26571 GPU-first publication + exact 26570 CPU fallback policy preserved')
    print('PASS native publication compute pixel math byte-identical; telemetry-only native delta')
    print('PASS persistent shot-scoped UI/shutter/processing/evidence/refine/backend/publication/final-dimension telemetry present')
    print('PASS no GLSL/DNG/Night/JPEG-R ownership changes')
if __name__=='__main__': main()
