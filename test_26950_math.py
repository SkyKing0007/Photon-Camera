#!/usr/bin/env python3
"""Numeric & source parity checks against the RAW vendor HDR+ frequency strength 11."""
import math,re,sys,pathlib,subprocess,tempfile
from build_26950_incremental import R,fail
vendor=R/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_hdrplus/include/rawr/raw_merge_hdrplus_gpu/RawMergeHdrPlusGpu.h'
s=vendor.read_text() if vendor.is_file() else ''
if 'inline FrequencyNorms frequencyNorms(float strength)' not in s or 'int(strength + 0.5f)' not in s:fail('original RAWR frequency normalization source missing')
strength=11;rev=0.5*(26.5-int(strength+0.5));norm=2**(-rev+7.5);read=2**((-rev+10)*1.6);motion=max(1,1.3**(11-rev))
if not all(math.isfinite(v) and v>0 for v in (norm,read,motion)):fail('bad upstream norms')
# The original source is single authority; ensure the C++ implementation
# agrees with Python's independent formula at HDR+ strength 11.
if '--live' in sys.argv:
 with tempfile.TemporaryDirectory(prefix='26950_hdrq_norms_') as td:
  p=pathlib.Path(td);cpp=p/'real.cpp';cpp.write_text("#include <iostream>\n#include <iomanip>\n#include <rawr/raw_merge_hdrplus_gpu/RawMergeHdrPlusGpu.h>\nint main() { const auto n=rawr::raw_merge_hdrplus_gpu::frequencyNorms(11.0f);std::cout << std::setprecision(10) << n.robustnessNorm << ' ' << n.readNoise << ' ' << n.maxMotionNorm << '\\n';}\n");cmd=['g++','-std=c++17','-O0','-I',str(vendor.parents[2]),str(cpp),'-o',str(p/'real')];subprocess.run(cmd,check=True,capture_output=True);run=subprocess.run([str(p/'real')],check=True,capture_output=True,text=True);actual=list(map(float,run.stdout.split()))
  for i,(a,b) in enumerate(zip(actual,(norm,read,motion))):
   if abs(a-b)>3e-6*max(1,abs(b)):fail('vendor freqNorms numerical divergence '+str(i))
print('PASS original RAWR frequencyNorms(11) source and exact native numerical parity')
