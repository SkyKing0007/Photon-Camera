#!/usr/bin/env python3
"""26944 only seven source files; restore 26942 stationary HDRq/hold V5 ZSL/Vulkan."""
import re,sys
from pathlib import Path
from build_26944_incremental import R,scope,exact,fail,sha,REQUIRED
B='app/src/main/cpp/iris26864/bridge/'
def file(path,live):
 p=(R if live else R/'handoff_payload_26944')/path
 if not p.is_file():fail('missing new source '+path)
 return p.read_text()
def main():
 paths,old,new=scope();live='--live' in sys.argv
 if live:exact(R,'26944_EXPECTED_FULL_APP.sha256','current live all 2054 source')
 assert paths==REQUIRED
 mismatch=file(B+'Iris26888BOffHdrqMismatch.comp',live)
 recorder=file(B+'Iris26887BOffHdrqRecorder.cpp',live)
 merge=file(B+'Iris26887BOffHdrqMerge.comp',live)
 for label,cond in (
  ('26942 25th-percentile restored', 'clamp(worst16[15],0.0,1.0)' in mismatch and 'clamp(worst16[7],0.0,1.0)' not in mismatch),
  ('subpixel aligned per CFA noise support unchanged', 'pointSupport(t0 + local, t0)' in mismatch and 'sAlignedHalo[lane] = imageLoad(alignedRgba, q)' in mismatch),
  ('motion-min write only guarded with disabled uniform', 'if (p.motionEnabled != 0)' in mismatch and 'imageStore(motionMin,g' in mismatch and 'mp.motionEnabled = 0;' in recorder),
  ('motion-min no uninitialized clear', 'vkCmdClearColorImage(c,arena_.image("hdrq_motion_min")' not in recorder),
  ('no 26943 motion interior blend', 'BorderPc bd{std::int32_t(geometry_.rgbaWidth), std::int32_t(geometry_.rgbaHeight), -2.0f, 0};' in recorder),
  ('26942 Fourier denoise retained', 'float localMotion = p.uniformExposure == 0 ? 0.0 :' in merge and 'imageLoad(weightSum, t).x' in merge),
  ('conservative strong motion extra veto', 'float evidence = smoothstep(0.48, 0.82, 1.0 - independentSupport)' in merge and 'smoothstep(0.10, 0.27, mm)' in merge and 'if (evidence > 0.0)' in merge and 'reject = 1.0 - (1.0 - reject) * (1.0 - evidence);' in merge),
  ('no motion-veto bracketed', 'if (p.uniformExposure != 0) {' in merge),
  ('reference spectrum fallback unchanged','imageLoad(outFt, o) + sRefRe[lane]' in merge),
 ):
  if not cond:fail('missing exact 26944 runtime contract '+label)
 night=file('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java',live)
 render=file('app/src/main/assets/shaders/motionv2/render.glsl',live)
 java=file('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',live)
 if 'VERSION_BUILD=26944' not in file('app/version.properties',live):fail('wrong build version')
 if render.count('iris26944NightMatchedSdrEnabled')!=3:fail('Night GLSL matched function not guarded both primary paths')
 if java.count('glProg.setVar("iris26944NightMatchedSdrEnabled"')!=1:fail('Night GL owner not exactly once')
 if 'iris26903NightB' not in java or 'irisNightActive' not in java:fail('Night B and Night mode ownership incomplete')
 for x in ('oldRatio * (pre + UHDR_OFFSET)','(hdrIntent - 0.68) / 0.28','ratio = 1.0 + (ratio - 1.0) * highlightGate;'):
  if x not in night:fail('Night post-Jin gainmap gate incomplete '+x)
 if new['app/src/main/assets/shaders/motionv2/gainmap.glsl']!=old['app/src/main/assets/shaders/motionv2/gainmap.glsl']:fail('double Night shader gainmap gate forbidden')
 if old['app/src/main/cpp/iris26864/bridge/Iris26943BOffHdrqBorder.comp']!=new['app/src/main/cpp/iris26864/bridge/Iris26943BOffHdrqBorder.comp']:fail('V5 proven Vulkan border modified')
 if old['app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp']!=new['app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp']:fail('V5 corrected descriptor executor modified')
 if live:
  border=(R/B/'Iris26943BOffHdrqBorder.comp').read_text()
  executor=(R/B/'Iris26888BOffVulkanExecutor.cpp').read_text()
  for label,shader,binds in (('hdrq_mismatch',mismatch,range(6)),('hdrq_border',border,range(3))):
   for b in binds:
    if not re.search(r'layout\s*\(\s*set\s*=\s*0\s*,\s*binding\s*=\s*'+str(b)+r'\b',shader):fail('shader descriptor missing '+label+' '+str(b))
   if label not in executor:fail('real V5 executor missing '+label)
  ingress=(R/'app/src/main/cpp/iris26864/Iris26943RawAhbIngress.cpp').read_text()
  if 'AHardwareBuffer_lockPlanes(' in ingress or 'AHardwareBuffer_lock(' not in ingress:fail('26943 API26 regression')
 print('PASS 26944 exact seven-path source, 26942 stationary HDRq, B-only aligned RAW motion, Night isolated, V5 Vulkan/API26 protected')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
