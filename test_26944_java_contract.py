#!/usr/bin/env python3
"""Night mode isolation, single shader uniform producer and UHDR post-Jin ordering."""
import sys,re
from build_26944_incremental import R,scope,fail
P='app/src/main/java/com/particlesdevs/photoncamera/'
def main():
 scope();live='--live' in sys.argv
 def src(p):
  from pathlib import Path
  f=(R if live else R/'handoff_payload_26944')/p
  if not f.is_file():fail('missing Night source '+p)
  return f.read_text()
 render=src(P+'processing/opengl/postpipeline/MotionV2Render.java')
 night=src(P+'processing/ultrahdr/IrisNightUltraHdr.java')
 if render.count('glProg.setVar("iris26944NightMatchedSdrEnabled"')!=1:fail('Night shader uniform double-mapped')
 b=render.index('glProg.setVar("iris26944NightMatchedSdrEnabled"')
 if 'basePipeline.mParameters.irisNightActive' not in render[b:b+245] or 'basePipeline.mParameters.iris26903NightB' not in render[b:b+245]:fail('ordinary Night and B Night mode gate missing')
 if 'iris26941BOffHdrqLowZoom' not in render[b-160:b] or 'iris26932BOffSdrLiftEnabled' not in render:fail('Photo B owners not retained')
 if render.count('glProg.setVar("iris26908NightPresentationLiftEnabled"')!=1:fail('Night original lift altered')
 for part in ('IrisNightUltraHdr','attachPostJin','sampleLinearLuma(finalSdr','oldRatio * (pre + UHDR_OFFSET)','ratio = 1.0 + (ratio - 1.0) * highlightGate;'):
  if part not in night:fail('Night post-Jin detached gain map authority missing '+part)
 gate=night.index('ratio = 1.0 + (ratio - 1.0) * highlightGate;');enc=night.index('int newCode = logMax')
 if not gate<enc:fail('Night highlight gate applied after encoding')
 if 'finalSdr.setPixels' in night or 'finalSdr.copyPixelsFromBuffer' in night:fail('Night Jin RGB source mutated in gainmap owner')
 if live:
  nightProc=(R/P/'processing/processor/IrisNightProcessor.java').read_text()
  hdrx=(R/P/'processing/processor/HdrxProcessor.java').read_text()
  if 'IrisNightUltraHdr.attachPostJin(' not in nightProc or 'IrisNightUltraHdr' not in hdrx or 'attachPostJin(img, nightBGain)' not in hdrx:fail('actual Night and Night B both use frozen post-Jin owner')
 print('PASS Night/Photo mode flags, one shader uniform, both Night post-Jin UHDR routes, no new Jin/RAW ownership')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
