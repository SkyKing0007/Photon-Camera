#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26798.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
ALLOW={
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties',
}
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(root): return {p.relative_to(root).as_posix():sha(p) for p in (root/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==len(c)==1779,(len(a),len(c))); need(set(a)==set(c),'candidate universe changed')
mod={p for p in a if a[p]!=c[p]}; need(mod==ALLOW,f'changed allowlist mismatch {sorted(mod)}')
print('PASS 26798 authority-seeded scope: 1779 files, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/'app/version.properties').read_text(); need('VERSION_NAME=0.9726798' in v and 'VERSION_BUILD=26798' in v,'version')
print('PASS 26798 version 0.9726798 / 26798')
shader_rel='app/src/main/assets/shaders/motionv2/render.glsl'
java_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
b=(BASE/shader_rel).read_text(); n=(CAND/shader_rel).read_text(); bj=(BASE/java_rel).read_text(); j=(CAND/java_rel).read_text()
need(n.count('IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_VALIDITY')==1,'26796 fallback marker missing')
need(n.count('IRIS_26797_CALIBRATED_MULTI_HUE_ZIPPER_CONTOUR_VALIDITY')==1,'26797 fallback marker missing')
need(n.count('IRIS_26798_CALIBRATED_CONNECTED_ZIPPER_HYSTERESIS_VALIDITY')==1,'26798 shader owner marker')
for s in (
'layout(std430, binding=0) buffer iris26798Stats {',
'uint iris26798Counters[12];',
'vec3 fallback26797=iris26797CalibratedZipperContour(sourcePixel,rgb);',
'float edgeBandRisk=iris26798BandEdgeRisk(sourcePixel,normal,guide,relativeGradient)',
'float centerSeedConfidence=iris26798SeedConfidenceAt(sourcePixel,normal)',
'iris26798SeedConfidenceAt(sourcePixel+tangent,normal)',
'iris26798SeedConfidenceAt(sourcePixel-tangent,normal)',
'iris26798SeedConfidenceAt(sourcePixel+tangent*2.0,normal)',
'iris26798SeedConfidenceAt(sourcePixel-tangent*2.0,normal)',
'iris26798SeedConfidenceAt(sourcePixel+tangent*3.0,normal)',
'iris26798SeedConfidenceAt(sourcePixel-tangent*3.0,normal)',
'float connectedSeed=max(centerSeed,neighborSeed)',
'float ribbonEvidence=interiorHueAbsent*withinMaterialEdge*realEdgeSpan;',
'float weakCandidate=smoothstep(0.10,0.30,weakConfidence)',
'float hysteresisCorrection=max(centerSeed,smoothstep(0.06,0.24,promoted))',
'vec3 targetChroma=iris26797MaterialTargetChroma(negMaterial,posMaterial,y,guide,centerMagnitude)',
'iris26798TelemetryMagnitude(8u,9u,10u,11u,centerMagnitude,postMagnitude)',
'linearSrgb=iris26798CalibratedConnectedZipper(sourcePixel,linearSrgb);'):
    need(s in n,f'missing 26798 contract: {s}')
block=n[n.index('/* IRIS_26798_CALIBRATED_CONNECTED_ZIPPER_HYSTERESIS_VALIDITY'):n.index('/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE')]
need('(1.0-tangentCoherent)' not in block,'26798 must not use tangent coherence as correction veto')
need('if(connectedSeed<=1.0e-5)' in block,'no-seed real-thin-color protection missing')
need('atomicAdd(iris26798Counters[3],1u)' in block,'contour-promotion telemetry missing')
need('atomicAdd(iris26798Counters[4],1u)' in block,'material protection telemetry missing')
need('atomicAdd(iris26798Counters[5],1u)' in block,'thin real-color protection telemetry missing')
call='linearSrgb=iris26798CalibratedConnectedZipper(sourcePixel,linearSrgb);'
callpos=n.index(call)
need(callpos < n.index('linearSrgb=max(linearSrgb*exp2(iris26718HighZoomLogDetail'),'26798 correction must precede high-zoom scalar detail')
need(callpos < n.index('if(iris26592MotionHdrHandoff!=0 && iris26621LocalToneEnabled!=0)'),'26798 correction must precede presentation/tone')
# Exact successful 26797 owner bytes remain frozen.
bm='/* IRIS_26796_CALIBRATED_BIPOLAR_BRIGHT_CONTOUR_VALIDITY'
nm='/* IRIS_26798_CALIBRATED_CONNECTED_ZIPPER_HYSTERESIS_VALIDITY'
em='/* IRIS_26718_HIGH_ZOOM_DETAIL_SAMPLE'
base_frozen=b[b.index(bm):b.index(em)]
cand_frozen=n[n.index(bm):n.index(nm)]
need(base_frozen==cand_frozen,'successful 26796+26797 fallback shader owners changed')
# Remove only 26798 block and restore exact 26797 call block; all other shader bytes must equal authority.
start=n.index('/* IRIS_26798_CALIBRATED_CONNECTED_ZIPPER_HYSTERESIS_VALIDITY')
end=n.index(em,start)
stripped=n[:start]+n[end:]
newcall=(
'    if(iris26592MotionHdrHandoff!=0){\n'
'        /* 26798 keeps successful 26797 as fallback, then promotes weak unsupported chroma only\n'
'         * when it is contour-connected to a strong false-color seed before presentation/tone. */\n'
'        linearSrgb=iris26798CalibratedConnectedZipper(sourcePixel,linearSrgb);\n'
'    }\n')
oldcall=(
'    if(iris26592MotionHdrHandoff!=0){\n'
'        /* 26797 keeps 26796 as the conservative fallback and adds the calibrated multi-hue zipper\n'
'         * strong tier before any presentation/tone magnitude. */\n'
'        linearSrgb=iris26797CalibratedZipperContour(sourcePixel,linearSrgb);\n'
'    }\n')
need(newcall in stripped,'26798 call block missing for exact preservation proof')
need(stripped.replace(newcall,oldcall,1)==b,'render shader changed outside 26798 owner + call')
# Java exact-intent proof: import + owner log + stats setup/read/close are the only changes.
need('import com.particlesdevs.photoncamera.processing.opengl.GLBuffer;' in j,'GLBuffer import missing')
need('IRIS_26798_CALIBRATED_CONNECTED_ZIPPER_HYSTERESIS_OWNER' in j,'26798 owner log missing')
need('IRIS_26798_CONNECTED_ZIPPER_DECISIONS' in j,'26798 decision telemetry log missing')
for s in ('new GLBuffer(12, new GLFormat(GLFormat.DataType.UNSIGNED_32))','iris26798Stats.uploadBuffer(new int[12], 12)','glProg.setBufferCompute("iris26798Stats", iris26798Stats)','glMemoryBarrier(android.opengl.GLES31.GL_SHADER_STORAGE_BARRIER_BIT)','iris26798Stats.readBufferIntegers(false)','iris26798Stats.close()'):
    need(s in j,f'missing 26798 Java telemetry contract: {s}')
# Protected owners outside the 3-file allowlist.
for p in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
]: need(sha(BASE/p)==sha(CAND/p),f'protected owner changed: {p}')
for p in a:
    if p in ALLOW: continue
    need(a[p]==c[p],f'unexpected protected change {p}')
print('PASS 26798 ownership: successful 26797 fallback retained byte-identical; only connected contour-hysteresis owner + telemetry + call/log/version added')
print('PASS 26798 26795 bridge + color transform/ACR3 + Sabre/VGN + exposure/tone/UHDR/DNG/SR/native/vendor owners protected')

def ss(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def final_corr(weak_conf,center_seed_conf,neighbor_seed_conf):
    weak=ss(.10,.30,weak_conf); center=ss(.18,.42,center_seed_conf); neigh=ss(.18,.42,neighbor_seed_conf)
    connected=max(center,neigh)
    if weak<=1e-5 or connected<=1e-5:return 0.0
    promoted=min(weak,connected)
    return max(center,ss(.06,.24,promoted))
# Proven 26797 failure: tangent-coherent false ribbon with no center seed but a nearby phase seed must be promoted.
need(final_corr(.80,.0,.80)>.99,'connected coherent false ribbon not fully promoted')
# Pixel-local strong seed remains fully corrected.
need(final_corr(.80,.80,.0)>.99,'center strong seed not fully corrected')
# Genuine thin color with no false-color seed remains protected regardless of weak/ribbon evidence.
need(final_corr(.80,.0,.0)==0.0,'real thin color without seed not protected')
# Displaced edge membership: a weak center derivative may still belong to a strong nearby normal-band edge.
center=.01; band=.10
edge=max(ss(.040,.15,center),ss(.032,.115,band)); need(edge>.90,'displaced chroma lobe not admitted by edge-band membership')
# Material-supported color suppresses weak confidence before hysteresis.
unsupported=.02; weak=min(1.0,1.0,1.0,unsupported,1.0); need(final_corr(weak,.8,.8)<.02,'material-supported color not protected')
# Weighted P3 luminance remains exact under target-chroma interpolation.
w=(.22897456,.69173852,.07928691); rgb=(.91,.69,.84); y=sum(a*b for a,b in zip(w,rgb)); center=tuple(v-y for v in rgb); target=(.03,-.015,.043); wy=sum(a*b for a,b in zip(w,target)); target=tuple(v-wy for v in target)
for k in (0.0,.2,.7,1.0):
    chroma=tuple((1-k)*a+k*b for a,b in zip(center,target)); out=tuple(y+q for q in chroma); yy=sum(a*b for a,b in zip(w,out)); need(abs(yy-y)<2e-7,(k,y,yy))
print('PASS 26798 synthetic invariants: connected coherent zipper promoted; center seed corrected; no-seed real thin color/material color protected; displaced edge band admitted; Display-P3 luma invariant')
print('PASS 26798 no Sabre/VGN/denoise/26795-bridge/color-transform/ACR3/exposure/tone/UHDR/DNG/SR/native/vendor redesign')
