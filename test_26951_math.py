#!/usr/bin/env python3
"""Real upstream RAWR strength=11 normalization and original mathematical ownership."""
import math,pathlib,subprocess,sys,tempfile
from build_26951_incremental import R,fail
vendor=R/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_hdrplus/include/rawr/raw_merge_hdrplus_gpu/RawMergeHdrPlusGpu.h'
# This check requires successfully seeded 26949 compiled source, not untrusted default-branch vendor.
s=vendor.read_text() if vendor.is_file() else ''
if 'inline FrequencyNorms frequencyNorms(float strength)' not in s or 'int(strength + 0.5f)' not in s:fail('original RAWR frequency normalization source missing')
strength=11.0;rev=0.5*(26.5-int(strength+0.5));norm=2**(-rev+7.5);read=2**((-rev+10)*1.6);motion=max(1.,1.3**(11-rev))
if not all(math.isfinite(v) and v>0 for v in (norm,read,motion)):fail('bad upstream norms')
if '--live' in sys.argv:
 with tempfile.TemporaryDirectory(prefix='26951_hdrq_norms_') as td:
  p=pathlib.Path(td);cpp=p/'real.cpp'
  cpp.write_text('#include <iostream>\n#include <iomanip>\n#include <rawr/raw_merge_hdrplus_gpu/RawMergeHdrPlusGpu.h>\nint main() { const auto n=rawr::raw_merge_hdrplus_gpu::frequencyNorms(11.0f); std::cout << std::setprecision(10) << n.robustnessNorm << " " << n.readNoise << " " << n.maxMotionNorm << "\\n";}\n')
  subprocess.run(['g++','-std=c++17','-O0','-I',str(vendor.parents[2]),str(cpp),'-o',str(p/'real')],check=True,capture_output=True)
  run=subprocess.run([str(p/'real')],check=True,capture_output=True,text=True)
  actual=list(map(float,run.stdout.split()))
  if len(actual)!=3:fail('upstream norm C++ returned incomplete result')
  for i,(a,b) in enumerate(zip(actual,(norm,read,motion))):
   if abs(a-b)>3e-6*max(1,abs(b)):fail('upstream RAWR frequencyNorms divergence '+str(i))
print('PASS original 26949 pinned RAWR frequencyNorms(11), B OFF / B Night frequency reconstruction')
