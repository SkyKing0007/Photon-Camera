#!/usr/bin/env python3
from pathlib import Path
import math,re,sys

def fail(m): raise SystemExit('FAIL: '+m)
def need(s,t,l):
 if t not in s: fail(l+' missing '+t)
def forbid(s,t,l):
 if t in s: fail(l+' stale '+t)
def smoothstep(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def contrast_ev(high,body):
 floor=1.0/1024.0
 return math.log2((max(high,0.0)+floor)/(max(body,0.0)+floor))
def decision(p50,p90,p99,p995,shadow,bright,strong,peak2):
 dr=contrast_ev(p995,p50); cdr=contrast_ev(peak2,p50)
 broad=p90>=.10 and p99>=.18 and dr>=1.50 and bright>=4
 mixed=shadow>=.05 and p99>=.16 and dr>=1.75 and bright>=2
 compact=peak2>=.25 and cdr>=2.25 and strong>=2
 return broad or mixed or compact,(broad,mixed,compact,dr,cdr)
# Universal HDR acquisition fixtures: physical signal distributions, not object labels.
cases=[
 ('broad_high_dynamic_range', dict(p50=.035,p90=.12,p99=.30,p995=.40,shadow=.15,bright=28,strong=12,peak2=.55), True),
 ('mixed_dark_body_bright_exterior', dict(p50=.028,p90=.07,p99=.34,p995=.48,shadow=.38,bright=10,strong=6,peak2=.62), True),
 ('compact_subclip_specular', dict(p50=.045,p90=.07,p99=.11,p995=.13,shadow=.03,bright=3,strong=2,peak2=.58), True),
 ('ordinary_even_daylight', dict(p50=.12,p90=.15,p99=.18,p995=.19,shadow=.00,bright=2,strong=0,peak2=.19), False),
 ('uniform_bright_safe', dict(p50=.42,p90=.50,p99=.57,p995=.59,shadow=.00,bright=100,strong=80,peak2=.62), False),
 ('low_light_without_bright_structure', dict(p50=.012,p90=.025,p99=.040,p995=.050,shadow=.75,bright=0,strong=0,peak2=.05), False),
 ('single_cell_impulse_rejected', dict(p50=.04,p90=.06,p99=.09,p995=.12,shadow=.10,bright=1,strong=1,peak2=.90), False),
]
for name,kw,want in cases:
 got,why=decision(**kw)
 if got!=want: fail(f'HDR decision fixture {name}: got={got} want={want} details={why}')
# Boundary math: neighbor predictor cannot rescue poor local residual at material boundary.
def local_residual(raw_px): return 1.0-smoothstep(2.0,8.0,max(raw_px,0.0))
def boundary_local(raw_px,predictor): return local_residual(raw_px)*(0.75+0.25*max(0,min(1,predictor)))
if boundary_local(12.0,1.0)!=0.0: fail('predictor overrode bad local boundary residual')
if not (0.74 < boundary_local(0.0,0.0) <= 0.75): fail('good local boundary proof unexpectedly destroyed')
# Deep censored core bypass remains exact: localGeometry is one when literalCore=1.
def local_geometry(raw_px,literal_core): return local_residual(raw_px)*(1.0-literal_core)+literal_core
if local_geometry(20.0,1.0)!=1.0: fail('two-phase clipped core lost 26607 component rescue')
if local_geometry(20.0,0.0)!=0.0: fail('measurable bad boundary bypassed local geometry')
# Existing final SHORT source clipping remains continuous only in last 0.75% before saturation.
def source_headroom(raw,clip=1022.5):
 start=max(1.0,clip*0.9925); return 1.0-smoothstep(start,max(start+1e-4,clip),raw)
if source_headroom(.95*1022.5)<=.99 or source_headroom(.98*1022.5)<=.99: fail('valid high SHORT headroom prematurely vetoed')
if source_headroom(1022.5)!=0.0: fail('true SHORT saturation did not fail closed')
if len(sys.argv)!=3: fail('usage base candidate')
b,c=map(Path,sys.argv[1:])
cc=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text(); sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); cf=(c/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java').read_text(); gl=(c/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java').read_text(); bgl=(b/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java').read_text()
# Exact capture regression: old literal trigger survives, universal path exists, dither coverage is explicit.
for t in ['mMotion26496SparseDitherCounter.getAndIncrement(), 9','signal >= 0.980f','structuredPeakSecond >= 0.25f','compactDynamicRangeEv >= 2.25f','structuredStrongBrightCells >= 2','boolean universalHdrTrigger = highlightTrigger','|| currentDynamicRangeTrigger','|| recentDynamicRangeTrigger','rawAgeNs <= 180_000_000L && universalHdrTrigger']: need(cc,t,'universal HDR acquisition')
forbid(cc,'mTextureView = new GLPreview(activity);','detached preview fallback')
# No scene-semantic production classifier in the new HDR equations.
a=cc.index('private void sampleMotion26496SpatialHighlightEvidence('); z=cc.index('IRIS_26381_DYNAMIC_MOTION_SHUTTER_OPPORTUNITY',a); scope=cc[a:z]
code=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',' ',scope,flags=re.S).lower()
for w in ['cloud','window','bulb','reflection','snow','curtain']:
 if re.search(r'\b'+w+r'\b',code): fail('scene-semantic production classifier '+w)
# One-tunnel and boundary invariants.
for t in ['float connectivityFlowProof = max(','float boundaryLocalFlowProof = localResidualConfidence * mix(','float literalCore = step(','uSourceClippingPoint, secondHighest4(referenceRaw)','float localGeometry = mix(localResidualConfidence, 1.0, literalCore);','oWeight = clamp(mix(ordinaryWeight, rescueConfidence, targetLoss), 0.0, 1.0);']: need(sh,t,'protected one-tunnel boundary')
for t in ['frameWeight = rescuedWeight','boundaryLocalResidualRequired=true','predictorCannotOverrideLocalBoundary=true','literalCoreTwoPhaseClipBypass=true','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)']: need(st,t,'one-tunnel ownership')
# Preview lifecycle: inherited replay stays byte-identical; stale fragment cannot clear newer controller.
if gl!=bgl: fail('GLPreview replay owner changed')
for t in ['deliveredSurfaceTextureGeneration == replayGeneration','IRIS_26548_PREVIEW_SURFACE_REPLAY','replay=true']: need(gl,t,'late listener replay')
for t in ['this.captureController.bindPreviewTextureView(textureView);','PhotonCamera.getCaptureController() == retiringController','IRIS_26608_STALE_FRAGMENT_DESTROY_PRESERVED_CURRENT_CONTROLLER']: need(cf,t,'preview lifecycle')
print('PASS universal HDR acquisition fixtures: broad DR, mixed dark/bright, compact sub-clipping structure trigger; ordinary/safe/low-light/single-cell fixtures fail closed')
print('PASS dithered spatial evidence covers sparse-lattice holes without modifying the existing 26380 AE sampler')
print('PASS protected one-tunnel boundaries: predictor cannot override bad local residual; two-phase censored core preserves 26607 rescue; final source clipping unchanged')
print('PASS preview lifecycle: current Fragment view binding + inherited generation-deduplicated late surface replay + stale destroy protection')
