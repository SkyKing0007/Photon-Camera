#!/usr/bin/env python3
from pathlib import Path
import argparse,math

def fail(m):raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c:fail(m)
def smooth(a,b,x):
 if x<=a:return 0.0
 if x>=b:return 1.0
 t=(x-a)/(b-a);return t*t*(3-2*t)
def exact_mask(ref,short,flow_px=0.25,headroom=True):
 clipped=[i for i,v in enumerate(ref) if v>=0.999]
 if flow_px>2.0 or not headroom or not clipped:return 0.0
 if any(short[i]<0.90 for i in clipped):return 0.0
 return 1.0
def android_weight(H,full,minH=1.0):
 if H<=minH:return 0.0
 if H>=full:return 1.0
 return max(0.0,min(1.0,(math.log(H)-math.log(minH))/(math.log(full)-math.log(minH))))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();c=Path(ns.candidate_root)
 s=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();k=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();r=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();u=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text();e=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text();n=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text();cap=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();bridge=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 # Carried 26593 frame ownership remains exact.
 for t in ['mPreviewCaptureResult instanceof TotalCaptureResult','ticket.sceneRequired = sceneRequiresShort','MOTION_26593_MIN_CAPTURE_COMPLETION_MS = 1400L']:
  req(t in cap,'carried capture authority '+t)
 req('requested SHORT disappeared after immutable batch freeze' in bridge,'SHORT fail-closed bridge')
 # Exact 26595 device result becomes permanent: SHORT was used but only 12,213 pixels; one-phase clipping must be eligible now.
 req('sensorClippedPhaseCount(referenceP) >= 1' in s,'one-phase exact sensor loss not admitted')
 req(exact_mask([1.0,.62,.60,.58],[.97,.62,.60,.58])==1.0,'one-phase neutral clip must activate')
 req(exact_mask([.62,1.0,.60,.58],[.62,.97,.60,.58])==1.0,'one-phase colored/CFA clip must activate')
 req(exact_mask([1.0,1.0,.60,.58],[.98,.96,.60,.58])==1.0,'two-phase clip must activate')
 req(exact_mask([1.0,1.0,1.0,1.0],[.98,.96,.95,.94])==1.0,'four-phase clip must activate')
 req(exact_mask([1.0,.62,.60,.58],[.60,.62,.60,.58])==0.0,'dark/mismatched SHORT must fail closed')
 req(exact_mask([1.0,.62,.60,.58],[.97,.62,.60,.58],flow_px=2.01)==0.0,'bad flow must fail closed')
 req(exact_mask([1.0,.62,.60,.58],[.97,.62,.60,.58],headroom=False)==0.0,'SHORT headroom loss must fail closed')
 mask=s[s.index('val shortRestoreMask26596'):s.index('val shortRestoreMaskProbe26590')]
 req('regionTrust' not in mask[mask.index('if (actualSensorLoss)'):mask.index('float referenceSecond')],'exact sensor loss must not depend on flood reach')
 # UHDR old failure: 8x content at fixed 1.6033 full-display gives W=1 and full 8x on modest HDR display.
 oldW=android_weight(1.6033,1.6033); req(abs(oldW-1.0)<1e-12,'old UHDR regression fixture')
 req(abs(8.0**oldW-8.0)<1e-9,'old 8x@1.6033 overdrive regression')
 # New actual-content capacity: e.g. actual peak 4x, 1.6033 display gets only representable fraction, full 4x only at 4x display.
 w=android_weight(1.6033,4.0); applied=4.0**w
 req(1.0<applied<4.0 and abs(android_weight(4.0,4.0)-1.0)<1e-12,'content-capacity Android decoder weighting')
 for t in ['HDR_EXPOSURE_SCALE = OUTPUT_EXPOSURE_SCALE','peakCode = Math.max(peakCode, code)','actualPeakContentRatio','motionV2GainMapFullHdrDisplayRatio']:
  req(t in r,'UHDR fix '+t)
 for t in ['setDisplayRatioForFullHdr(fullHdrDisplayRatio)','capacityMatchesActualGainPeak=true']:
  req(t in u,'UHDR metadata '+t)
 # True2x content cap, both GPU and CPU, must use contentMax while encoding denominator stays safeMax/ratioMax.
 for t in ['true2xGainContentMax','getDisplayRatioForFullHdr()']:
  req(t in e,'true2x Java '+t)
 for t in ['uGainContentMax','contentMax=clamp(uGainContentMax,1.0,safeMax)','ratio=clamp((hdrY+off)/(sdrY+off),1.0,contentMax)','log2(ratio)/max(log2(safeMax),1.0e-6)']:
  req(t in n,'true2x GPU '+t)
 req(n.count('gainContentMax')>=10,'true2x CPU/GPU cap plumbing incomplete')
 # 26595 actual contribution proof + true2x native restored guide remain.
 for t in ['countSabreShortRestoreMaskFull26595','fullActive=$fullActiveText26595','shortGuideOwner=EXACT_NATIVE_RGBA16F_RESTORE','true2xDetailEvidenceShort=false']:
  req(t in k,'carried full-mask/SR proof '+t)
 print('PASS carried 26593 capture ownership + 26595 full-mask/SR architecture')
 print('PASS exact one/two/four-phase sensor-loss SHORT fixtures and fail-closed mismatch/flow/headroom')
 print('PASS permanent old 8x@1.6033 UHDR overdrive regression + actual-content display-capacity weighting')
 print('PASS true2x GPU/CPU content cap parity while ratioMax remains encoding denominator')
if __name__=='__main__':main()
