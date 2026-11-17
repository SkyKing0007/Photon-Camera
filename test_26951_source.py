#!/usr/bin/env python3
"""Read-only SHA and RAWR shader/source contracts, including vendor-free checkout preseed."""
import hashlib,pathlib,re,shutil,subprocess,sys,tempfile
from build_26951_incremental import R,parse,scope,sha,fail
B='app/src/main/cpp/iris26864/bridge/'
V='app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_hdrplus/shaders/'
SHADERS={'Iris26887BOffHdrqMerge.comp':'hdrq_merge.comp',
 'Iris26888BOffHdrqMismatch.comp':'hdrq_mismatch.comp',
 'Iris26887BOffHdrqMismatchNorm.comp':'hdrq_mismatch_norm.comp',
 'Iris26943BOffHdrqBorder.comp':'hdrq_border.comp'}
REST={'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
 B+'Iris26887BOffHdrqRecorder.cpp', B+'Iris26888BOffVulkanExecutor.cpp',
 'app/version.properties','app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'}

def bare_glsl(src):
 # Strip strings and both comment types before lexical checks of reserved identifiers.
 return re.sub(r'"(?:\\.|[^"\\])*"|/\*[\s\S]*?\*/|//[^\n]*',' ',src)

def check():
 changed,old,new=scope()
 if changed!=set(B+p for p in SHADERS)|REST:fail('26951 exact 11 source allowlist mismatch')
 live='--live' in sys.argv
 root=R if live else R/'handoff_payload_26951'
 for p in changed:
  if not (root/p).is_file() or sha(root/p)!=new[p]:fail('overlay/current source missing or SHA mismatch '+p)
 if live:
  for p,h in new.items():
   if not (R/p).is_file() or sha(R/p)!=h:fail('26951 live source changed '+p)
 protected=parse(R/'26951_PROTECTED_SOURCE.sha256')
 for dst,src in SHADERS.items():
  donor=V+src;target=B+dst
  if donor not in old or donor not in new or donor not in protected:fail('sealed upstream vendor missing '+donor)
  expected=protected[donor]
  if old[donor]!=expected or new[donor]!=expected or sha(root/target)!=expected:fail('upstream RAWR 26949 donor/source mismatch '+dst)
  if live and ((not (R/donor).is_file()) or sha(R/donor)!=expected or (root/target).read_bytes()!=(R/donor).read_bytes()):fail('live RAWR original shader not byte exact '+dst)
  # All six modified runtime GPU shaders must never use GLSL's reserved `coherent` as an identifier.
  cleaned=bare_glsl((root/target).read_text())
  if re.search(r'\bcoherent\b',cleaned):fail('reserved GLSL token coherent present in active shader '+dst)
  if re.search(r'\b(?:volatile|restrict|goto|namespace|packed)\b',cleaned):fail('reserved GLSL token in active shader '+dst)
  if re.search(r'\b(?:float|int|uint|vec[234]|ivec[234]|bool)\s+gl_[A-Za-z0-9_]+',cleaned):fail('reserved gl_ identifier declaration')
 for name in ('render','gainmap'):
  source=(root/f'app/src/main/assets/shaders/motionv2/{name}.glsl').read_text()
  clean=bare_glsl(source)
  if re.search(r'\bcoherent\b',clean):fail('reserved GLSL coherent active code '+name)
  if re.search(r'\b(?:volatile|restrict|goto|namespace|packed)\b',clean):fail('GLSL reserved token active code '+name)
  if '#version' in clean or clean.count('void main()')!=1:fail('invalid runtime expanded '+name)
 c=(root/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
 if 'if (!sr) hdrq.strength = 11.0f;' not in c or 'sr?MergeAlgorithm::Wronski:MergeAlgorithm::HdrPlusFrequency' not in c:fail('B OFF/Night HDRQ 11 owner routing missing')
 p=(root/B/'Iris26887BOffHdrqRecorder.cpp').read_text()
 for token in ('static_assert(sizeof(MismatchNormPc)==12u', 'static_assert(sizeof(FreqMergePc)==28u',
  'static_assert(sizeof(BorderPc)==12u', 'hdrq_weight_sum', 'HdrqDeconvolute', '&fm, sizeof(fm), tx, ty'):
  if token not in p:fail('upstream HDRQ recorder missing '+token)
 if any(x in p for x in ('hdrq_motion_min','ib(2,arena_.image("hdrq_motion_min"))','rawNoiseMeasured_ ? 1 : 0')):fail('old local HDRQ descriptor or support branch remains')
 if '{bb(5, arena_.buffer("hdrq_shift_table"))}}' not in p:fail('expected RAWR Fourier binding absent')
 if 'VERSION_BUILD=26951' not in (root/'app/version.properties').read_text() or 'VERSION_NAME=0.9726951' not in (root/'app/version.properties').read_text():fail('wrong 26951 version')
 print('PASS 26951 exact 11-file source/GLSL reserved-id/4 pinned original RAWR shaders, 2043 protected')

def preseed():
 """Vendor-free Actions runner simulation; must not depend on reconstructed app/src."""
 ch,old,new=scope()
 with tempfile.TemporaryDirectory(prefix='26951_vendorfree_') as td:
  tmp=pathlib.Path(td)
  names=['build_26951_incremental.py','test_26951_source.py','26951_BASE_26949_FULL_APP.sha256',
   '26951_EXPECTED_FULL_APP.sha256','26951_PROTECTED_SOURCE.sha256',
   '26951_CHANGED_RUNTIME_ALLOWLIST.txt','26951_ADDED_RUNTIME_PATHS.txt','26951_DELETED_RUNTIME_PATHS.txt']
  for f in names:
   p=tmp/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/f,p)
  for p in ch:
   target=tmp/'handoff_payload_26951'/p;target.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(R/'handoff_payload_26951'/p,target)
  if (tmp/V/'hdrq_merge.comp').exists():fail('vendor-free simulation contaminated')
  cmd=[sys.executable,'-S',str(tmp/'test_26951_source.py'),'--payload']
  good=subprocess.run(cmd,cwd=tmp,capture_output=True,text=True)
  if good.returncode:fail('unseeded preflight failed: '+(good.stdout+good.stderr)[-800:])
  # Historical 26950 V3 failed preseed due to reading unprepared vendor paths.
  # Negative: fully rewritten both manifests cannot impersonate the original RAWR shader SHA.
  donor=V+'hdrq_merge.comp';oldhash=old[donor];fake='f'*64 if oldhash!='f'*64 else 'e'*64
  for f in ('26951_BASE_26949_FULL_APP.sha256','26951_EXPECTED_FULL_APP.sha256','26951_PROTECTED_SOURCE.sha256'):
   p=tmp/f;s=p.read_text();needle=oldhash+'  '+donor
   if s.count(needle)!=1:fail('preseed negative donor not in sealed sources')
   p.write_text(s.replace(needle,fake+'  '+donor,1))
  bad=subprocess.run(cmd,cwd=tmp,capture_output=True,text=True)
  if bad.returncode==0 or 'upstream RAWR 26949 donor/source mismatch' not in bad.stderr:fail('resealed vendor spoofing passed preseed')
  print('PASS 26951 vendor-free positive checkout and hostile vendor-hash negative')

if __name__=='__main__':
 try:
  if '--preseed' in sys.argv:preseed()
  else:check()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
