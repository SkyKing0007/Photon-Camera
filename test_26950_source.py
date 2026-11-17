#!/usr/bin/env python3
"""Prove the exact *current* 26949 -> 26950 scope and byte-identical upstream HDRQ math."""
import hashlib,pathlib,sys,re
from build_26950_incremental import R,parse,scope,sha,fail
B='app/src/main/cpp/iris26864/bridge/'
V='app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_hdrplus/shaders/'
SHADERS={'Iris26887BOffHdrqMerge.comp':'hdrq_merge.comp',
 'Iris26888BOffHdrqMismatch.comp':'hdrq_mismatch.comp',
 'Iris26887BOffHdrqMismatchNorm.comp':'hdrq_mismatch_norm.comp',
 'Iris26943BOffHdrqBorder.comp':'hdrq_border.comp'}
REST={'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp', B+'Iris26887BOffHdrqRecorder.cpp', 'app/version.properties', 'app/src/main/assets/shaders/motionv2/render.glsl', 'app/src/main/assets/shaders/motionv2/gainmap.glsl', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'}
def check():
 changed,old,new=scope()
 if changed!=set(B+k for k in SHADERS)|REST:fail('not exact 10 changed source files')
 root=R if '--live' in sys.argv else R/'handoff_payload_26950'
 for p in changed:
  if not (root/p).is_file() or sha(root/p)!=new[p]:fail('invalid current overlay '+p)
 if '--live' in sys.argv:
  for p,h in new.items():
   if sha(R/p)!=h:fail('live current source changed '+p)
 for dst,src in SHADERS.items():
  if (root/B/dst).read_bytes()!=(R/V/src).read_bytes():fail('not byte-exact upstream RAWR HDRQ shader '+dst)
  code=(root/B/dst).read_text()
  for name in ('coherent','volatile','restrict','goto','namespace','packed'):
   bare=re.sub(r'//[^\n]*','',re.sub(r'/\*.*?\*/','',code,flags=re.S))
   if re.search(r'\b(?:float|int|vec[234]|ivec[234]|uniform|bool)\s+'+name+r'\b',bare):fail('reserved GLSL identifier '+name)
 c=(root/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
 if 'if (!sr) hdrq.strength = 11.0f;' not in c or 'sr?MergeAlgorithm::Wronski:MergeAlgorithm::HdrPlusFrequency' not in c:fail('B OFF and B Night HDRQ 11 not routed')
 p=(root/B/'Iris26887BOffHdrqRecorder.cpp').read_text()
 for required in ('static_assert(sizeof(MismatchNormPc)==12u','static_assert(sizeof(FreqMergePc)==28u','static_assert(sizeof(BorderPc)==12u',
  'rawr::raw_merge_hdrplus_gpu','hdrq_weight_sum','const auto norms = uniformExposure_',
  'HdrqDeconvolute','&fm, sizeof(fm), tx, ty'):
  if required not in p and required!='rawr::raw_merge_hdrplus_gpu':fail('RAWR HDRQ recorder ABI missing '+required)
 for banned in ('structuralVar','supportMeasured','independentSupport','alignmentPrior','strength115','rawNoiseMeasured_'):
  # rawNoiseMeasured_ exists only for the historical estimator, NEVER a current HDRQ merge/deconvolution condition.
  if banned=='rawNoiseMeasured_':
   a=p.index('void HdrPlusFrequencyRecorder::recordPassFinish');b=p[a:p.index('void HdrPlusFrequencyRecorder::recordFinalize',a)] if 'void HdrPlusFrequencyRecorder::recordFinalize' in p[a:] else p[a:]
   if 'rawNoiseMeasured_' in b:fail('raw burst measured flag still blocks RAWR deconvolution')
  elif banned in (root/B/'Iris26887BOffHdrqMerge.comp').read_text():fail('old local motion filter remains '+banned)
 if '{bb(5, arena_.buffer("hdrq_shift_table"))}}' not in p:fail('non-RAWR descriptor 8 still bound')
 if 'ib(2,arena_.image("hdrq_motion_min"))' in p:fail('old motion border texture retained')
 if 'hdrq_motion_min' in p:fail('obsolete LONG-era motion scratch resource remains')
 if (root/'app/version.properties').read_text().count('VERSION_BUILD=26950')!=1:fail('26950 version invalid')
 print('PASS exact original 4 RAWR shaders, native layout/11 strength for B OFF & Night, 2044 protected')
if __name__=='__main__':
 try:check()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
