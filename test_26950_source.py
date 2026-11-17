#!/usr/bin/env python3
"""Prove the exact *current* 26949 -> 26950 scope and byte-identical upstream HDRQ math."""
import hashlib,pathlib,sys,re,shutil,tempfile,subprocess
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
 # GitHub checkout is intentionally vendor-free before the authority TAR is seeded.
 # Payload-mode parity MUST use the SHA-sealed original vendor hashes, not a
 # live disk path that cannot exist before build_26950_incremental.py prepare.
 # Live-mode later checks the actual successfully-restored vendor bytes as well.
 protected=parse(R/'26950_PROTECTED_SOURCE.sha256')
 for dst,src in SHADERS.items():
  vendor_path=V+src; shader_path=B+dst
  if vendor_path not in old or vendor_path not in new or vendor_path not in protected:
   fail('sealed upstream RAWR vendor path missing '+vendor_path)
  upstream=protected[vendor_path]
  if old[vendor_path]!=upstream or new[vendor_path]!=upstream:
   fail('upstream RAWR vendor hash changed '+vendor_path)
  if sha(root/shader_path)!=upstream:
   fail('source SHA differs from original RAWR HDRQ vendor '+dst)
  if '--live' in sys.argv:
   original=R/vendor_path
   if not original.is_file() or sha(original)!=upstream or (root/shader_path).read_bytes()!=original.read_bytes():
    fail('not byte-exact upstream RAWR HDRQ shader '+dst)
  code=(root/shader_path).read_text()
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
def preseed():
 """Reproduce original 44102586828 vendor-free Actions checkout BEFORE fetch/prepare.

 This is deliberately executed against an isolated stage-only copy, so a
 previously reconstructed local app/src tree can never make this test pass.
 """
 ch,old,new=scope()
 with tempfile.TemporaryDirectory(prefix='26950_v3_unseeded_checkout_') as td:
  temp=pathlib.Path(td)
  required=('build_26950_incremental.py','test_26950_source.py',
   '26950_BASE_26949_FULL_APP.sha256','26950_EXPECTED_FULL_APP.sha256',
   '26950_PROTECTED_SOURCE.sha256','26950_CHANGED_RUNTIME_ALLOWLIST.txt',
   '26950_ADDED_RUNTIME_PATHS.txt','26950_DELETED_RUNTIME_PATHS.txt')
  for f in required:
   dst=temp/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/f,dst)
  for p in sorted(ch):
   dst=temp/'handoff_payload_26950'/p;dst.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(R/'handoff_payload_26950'/p,dst)
  if (temp/V/'hdrq_merge.comp').exists():fail('preseed fixture unexpectedly has vendor source')
  cmd=[sys.executable,'-S',str(temp/'test_26950_source.py'),'--payload']
  def run():return subprocess.run(cmd,cwd=temp,text=True,capture_output=True)
  result=run()
  if result.returncode!=0:
   fail('vendor-free Actions preseed positive test failed '+(result.stdout+result.stderr)[-700:])
  # Hostile reseal test: a changed upstream vendor hash cannot authenticate the
  # staged originals even when all three protected manifests are altered equally.
  vendor_path=V+'hdrq_merge.comp'
  original=old[vendor_path]
  fake='f'*64 if original!='f'*64 else 'e'*64
  for manifest in ('26950_BASE_26949_FULL_APP.sha256',
   '26950_EXPECTED_FULL_APP.sha256','26950_PROTECTED_SOURCE.sha256'):
   f=temp/manifest;text=f.read_text();line=original+'  '+vendor_path
   if text.count(line)!=1:fail('preseed negative cannot locate vendor SHA')
   f.write_text(text.replace(line,fake+'  '+vendor_path,1))
  bad=run()
  if bad.returncode==0 or 'source SHA differs from original RAWR HDRQ vendor' not in (bad.stdout+bad.stderr):
   fail('preseed resealed vendor mismatch escaped')
  print('PASS 26950 V3 original Actions vendor-free preseed, exact SHA-authenticated four original RAWR shaders, resealed donor mismatch rejected')

if __name__=='__main__':
 try:
  if '--preseed' in sys.argv:preseed()
  else:check()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
