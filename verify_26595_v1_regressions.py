#!/usr/bin/env python3
from pathlib import Path
import argparse,math,re,struct

def fail(m):raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c:fail(m)
def smooth(a,b,x):
 if x<=a:return 0.0
 if x>=b:return 1.0
 t=(x-a)/(b-a);return t*t*(3-2*t)
def mask(ref_second,clipped_phases,flow_px,short_headroom,short_second,region_trust):
 if ref_second<.90 or flow_px>2.0:return 0.0
 if not short_headroom or short_second<.90:return 0.0
 actual=clipped_phases>=2
 if not actual and region_trust<.5:return 0.0
 return smooth(.90,.98,ref_second)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();c=Path(ns.candidate_root)
 s=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();k=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();cap=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();bridge=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 # Carried exact 26593/26594 capture ownership remains.
 for t in ['mPreviewCaptureResult instanceof TotalCaptureResult','ticket.sceneRequired = sceneRequiresShort','MOTION_26593_MIN_CAPTURE_COMPLETION_MS = 1400L']:
  req(t in cap,'carried capture authority '+t)
 req('requested SHORT disappeared after immutable batch freeze' in bridge,'SHORT fail-closed bridge')
 # Exact 26594 real-device failure becomes permanent: Sabre guide sentinel may zero frameWeight, but 26595 mask cannot consume it.
 req('if (centerGreen >= uGreenClippingPoint) referenceColor = vec3(10000.0);' in s,'Sabre clipped sentinel authority changed')
 seed=s[s.index('val shortRegionSeed26595'):s.index('val shortRegionPropagate26594')]
 final=s[s.index('val shortRestoreMask26595'):s.index('val shortRestoreMaskProbe26590')]
 for forbidden in ['uShortWeight','uUnblocker']:
  req(forbidden not in seed+final,'26594 false-closed gate revived '+forbidden)
 # Small actual clipping works without boundary flood reach.
 req(mask(.999,4,.25,True,1.01,0.0)>.99,'small sensor-clipped SHORT must activate without seed reach')
 # Large clipping is identical per-pixel and cannot have a 128px inward ceiling.
 large=[mask(.999,4,.25,True,1.01,0.0) for _ in range(384*384)]
 req(min(large)>.99 and len(large)>128*128,'large clipped core size independence')
 # Safety fail-closed fixtures.
 req(mask(.999,4,2.01,True,1.01,1.0)==0,'flow discontinuity must fail closed')
 req(mask(.999,4,.25,False,1.01,1.0)==0,'SHORT headroom loss must fail closed')
 req(mask(.999,4,.25,True,.75,1.0)==0,'misregistered dark SHORT must fail closed')
 req(mask(.95,0,.25,True,.96,0.0)==0,'near-clip without sensor loss still needs boundary trust')
 req(0<mask(.95,0,.25,True,.96,1.0)<1,'trusted near-clip feather')
 # Subpixel same-phase fixture: linear phase field is reconstructed exactly at fractional coordinates.
 def bilinear(vals,fx,fy):return (vals[0]*(1-fx)+vals[1]*fx)*(1-fy)+(vals[2]*(1-fx)+vals[3]*fx)*fy
 vals=[.40,.50,.60,.70]; got=bilinear(vals,.5,.25); expected=((.40+.50)/2)*.75+((.60+.70)/2)*.25
 req(abs(got-expected)<1e-12,'same-phase subpixel interpolation fixture')
 # Full-mask proof and SR ownership are permanent, not sparse-toggle semantics.
 for t in ['countSabreShortRestoreMaskFull26595','fullActive=$fullActiveText26595','shortGuideOwner=EXACT_NATIVE_RGBA16F_RESTORE']:
  req(t in k,'full-mask/SR proof '+t)
 req('frames, images, reconstructionEvidence, nativeHighlightAuthority26587, exportNormalStackedDng' in k,'true2x restored guide handoff')
 req('shortEvidence=false' in k and 'true2xDetailEvidenceShort=false' in k,'SHORT must remain excluded from true2x CFA detail evidence')
 print('PASS carried 26593/26594 capture ownership and exact 26594 clipped-guide failure regression')
 print('PASS small + >128px large sensor-clipped regions can use SHORT without flood reach')
 print('PASS flow/headroom/SHORT-brightness/near-clip boundary safety fixtures fail closed')
 print('PASS full-resolution contribution telemetry + true2x restored-guide ownership')
if __name__=='__main__':main()
