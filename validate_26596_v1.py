#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=[x for x in """app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java
app/version.properties""".splitlines() if x]
def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c: fail(m)
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def embedded(src,name):
 m=re.search(r'(?m)^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',src); req(m is not None,'missing '+name)
 a=m.end(); z=src.find('""".trimIndent()',a); req(z>=0,'end '+name); return src[a:z]
if len(sys.argv)!=3: fail('usage base candidate')
b,c=map(Path,sys.argv[1:])
bp={str(p.relative_to(b)):H(p) for p in sorted((b/'app').rglob('*')) if p.is_file()}
cp={str(p.relative_to(c)):H(p) for p in sorted((c/'app').rglob('*')) if p.is_file()}
req(set(bp)==set(cp) and len(bp)==1708,'full app universe')
changed=[r for r in bp if bp[r]!=cp[r]]; req(changed==CHANGED,'exact changed allowlist '+repr(changed))
s=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
k=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
r=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
p=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
u=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text()
e=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
n=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text();v=(c/'app/version.properties').read_text()
# Phase-complete exact sensor loss: one or more clipped phases, every clipped phase must be explained by SHORT.
mask=s[s.index('val shortRestoreMask26596'):s.index('val shortRestoreMaskProbe26590')]
for t in ['IRIS_26596_PHASE_COMPLETE_SENSOR_LOSS_SHORT_MASK','sensorClippedPhaseCount(referenceP) >= 1','everyClippedReferencePhaseExplained(referenceQuad, shortNormalized)','if (shortNormalized[phase] < 0.90) return false','if (samePhasePeak(support) >= uShortHeadroomThreshold) return false','flow.w > uFlowVariationPixelsThreshold','oMask = everyClippedReferencePhaseExplained(referenceQuad, shortNormalized) ? 1.0 : 0.0']:
 req(t in s+mask,'phase-complete SHORT contract '+t)
for banned in ['uShortWeight','uUnblocker','uShortWeightThreshold','uUnblockerThreshold']:
 req(banned not in mask,'photometric/unblocker final veto revived '+banned)
# Near-clip path remains 26595 connected boundary radiometry, and full mask proof remains.
for t in ['val shortRegionSeed26595','boundaryRadiometry=subpixelSameCfaPhase','clipPhasesMin=1 clippedPhaseShortProof=true','countSabreShortRestoreMaskFull26595','fullActive=$fullActiveText26595','sabrePhotometricGate=false','unblockerGate=false']:
 req(t in s+k,'SHORT carry/final proof '+t)
# Motion UHDR body unity + actual encoded peak owns display capacity.
for t in ['IRIS_26596_UHDR_BODY_UNITY','HDR_EXPOSURE_SCALE = OUTPUT_EXPOSURE_SCALE','peakCode = Math.max(peakCode, code)','actualPeakContentRatio = (float)Math.pow','motionV2GainMapFullHdrDisplayRatio = fullHdrDisplayRatio','IRIS_26596_UHDR_GAINMAP_CONTENT']:
 req(t in r,'Motion UHDR content contract '+t)
for t in ['motionV2GainMapFullHdrDisplayRatio','MotionV2UltraHdr.attachMotion','capacityMatchesActualGainPeak=true']:
 req(t in p,'PostPipeline UHDR ownership '+t)
for t in ['IRIS_26596_MOTION_UHDR_ACTUAL_CONTENT_CAPACITY','requestedFullHdrDisplayRatio','setDisplayRatioForFullHdr(fullHdrDisplayRatio)','capacityMatchesActualGainPeak=true']:
 req(t in u,'Motion UHDR metadata '+t)
# True2x must inherit native HDR content peak but keep ratioMax encoding denominator.
for t in ['true2xGainEncodingMax','true2xGainContentMax','attachedGainmap.getDisplayRatioForFullHdr()','IRIS_26596_TRUE2X_CONTENT_CAP=true','float true2xGainmapContentMaxRatio']:
 req(t in e,'true2x Java content cap '+t)
for t in ['uniform float uGainContentMax','contentMax=clamp(uGainContentMax,1.0,safeMax)','ratio=clamp((hdrY+off)/(sdrY+off),1.0,contentMax)','log2(ratio)/max(log2(safeMax),1.0e-6)','IRIS_26596_TRUE2X_GAIN_CONTENT_CAP']:
 req(t in n,'true2x native content cap '+t)
# Protected owners explicitly unchanged.
for rr in ['app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java']:
 req(H(b/rr)==H(c/rr),'protected owner changed '+rr)
# SR restored guide architecture carried unchanged from 26595.
for t in ['shortGuideOwner=EXACT_NATIVE_RGBA16F_RESTORE','true2xDetailEvidenceShort=false','frames, images, reconstructionEvidence, nativeHighlightAuthority26587, exportNormalStackedDng']:
 req(t in k,'SR restored-guide ownership '+t)
req('VERSION_NAME=0.9726596' in v and 'VERSION_BUILD=26596' in v,'version/build')
print('PASS exact eight-file runtime scope; DNG/ImageSaver/Hdrx and unrelated owners unchanged')
print('PASS phase-complete one-or-more-CFA sensor-loss SHORT ownership with per-clipped-phase proof')
print('PASS Motion UHDR body-unity + actual encoded content peak capacity metadata')
print('PASS true2x content cap matches native HDR authority while ratioMax encoding remains unchanged')
