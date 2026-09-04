#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=[x for x in """app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
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
s=(c/CHANGED[0]).read_text();k=(c/CHANGED[1]).read_text();v=(c/CHANGED[2]).read_text();bs=(b/CHANGED[0]).read_text()
# Pure geometry + subpixel same-CFA phase ownership.
for t in ['IRIS_26595_PURE_FLOW_GEOMETRY_METRIC','localFlowVariationRawPixels = 2.0 * length(flowRangeBayerQuads)','IRIS_26595_SUBPIXEL_PHASE_SHORT_HANDOFF','val shortRegionSeed26595','samePhaseSupport','bilinearSamePhase','flow.w <= uFlowVariationPixelsThreshold','quadEvidence >= 3 && phaseEvidence >= 6','meanError < uConsistencyThreshold']:
 req(t in s,'shader contract '+t)
seed=s[s.index('val shortRegionSeed26595'):s.index('val shortRegionPropagate26594')]
for banned in ['uShortWeight','uUnblocker','uShortWeightThreshold','uUnblockerThreshold','shortWeight >=','unblocker <=']:
 req(banned not in seed,'photometric/unblocker seed veto survived '+banned)
mask=s[s.index('val shortRestoreMask26595'):s.index('val shortRestoreMaskProbe26590')]
for t in ['sensorClippedPhaseCount(referenceP) >= 2','shortSecondNormalized < handoffStart','!actualSensorLoss && regionTrust < 0.5','flow.w > uFlowVariationPixelsThreshold','oMask = smoothstep(handoffStart, uReferenceNearClipThreshold, referenceSecond);']:
 req(t in mask,'final mask contract '+t)
for banned in ['uShortWeight','uUnblocker','uShortWeightThreshold','uUnblockerThreshold']:
 req(banned not in mask,'photometric/unblocker final veto survived '+banned)
# Host uses exact new producers and permanent full-resolution count.
for t in ['renderSabreShortRegionSeed26595','renderSabreShortRestoreMask26595','uFlowVariationPixelsThreshold", 2.0f','IRIS_26595_FULL_MASK_CONTRIBUTION_PROOF','countSabreShortRestoreMaskFull26595','fullActive=$fullActiveText26595','actualSensorClipBypass=true','sabrePhotometricGate=false','unblockerGate=false']:
 req(t in k,'stacker contract '+t)
# SR: same restored native authority feeds true2x RGB/chroma/highlight guide; SHORT stays out of CFA detail evidence.
for t in ['val nativeHighlightAuthority26587 = if (highlightShortAdmitted26587)','frames, images, reconstructionEvidence, nativeHighlightAuthority26587, exportNormalStackedDng','shortEvidence=false shortNativeGuide=${highlightShortAdmitted26587}','shortGuideOwner=EXACT_NATIVE_RGBA16F_RESTORE','true2xDetailEvidenceShort=false']:
 req(t in k,'SR SHORT ownership '+t)
for t in ['bindTexture(program,"uNativeVgnGuide",2,nativeVgnGuideTexture)','highResLumaOwner=DIRECT_CFA_TEMPORAL','Native Sabre/VGN remains the sole RGB/chroma/highlight']:
 req(t in k+s,'SR guide/detail contract '+t)
# True2x shader math and whole-RGB restore remain byte-identical to successful 26594.
for name in ['true2xMerge26564','true2xResolve26564','true2xGuideRender26568','shortRestoreRgba16f26587','shortRestoreMaskProbe26590']:
 req(embedded(bs,name)==embedded(s,name),name+' unexpectedly changed')
req('VERSION_NAME=0.9726595' in v and 'VERSION_BUILD=26595' in v,'version/build')
print('PASS exact three-file runtime scope and 26595 phase-coherent SHORT ownership')
print('PASS clipped core size-independent sensor-loss path + subpixel same-CFA boundary radiometry')
print('PASS true2x consumes exact restored native SHORT guide while NORMAL-only CFA detail evidence is unchanged')
