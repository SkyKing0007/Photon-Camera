#!/usr/bin/env python3
"""26917 genuine Bayer phase and complete B-OFF boundary ownership regressions.
No fake GLSL or native compilation claims; real gates remain mandatory.
"""
from pathlib import Path
import sys,hashlib
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
ROOT=R if LIVE else R/'handoff_payload_26917'
header=(ROOT/'app/src/main/cpp/iris26856/amaze/include/amaze/Amaze.hpp').read_text()
cpp=(ROOT/'app/src/main/cpp/iris26856/amaze/src/Pipeline.cpp').read_text()
shader=(ROOT/'app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp').read_text()
caller=(ROOT/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
assert 'bool phaseSafePhysicalHalo = false;' in header
java=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java').read_text()
kotlin=(ROOT/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
assert java.count('boolean photoBOffOnly')==2
assert 'photoBOffOnly && !wronskiTrue2x' in java
assert 'false, // Wronski B SR ON never owns physical-halo experiment.' in kotlin
assert '!parameters.iris26903NightB && !parameters.irisNightActive' in kotlin
assert 'config.phaseSafePhysicalHalo=(!sr && photoBOffOnly == JNI_TRUE);' in caller
assert 'kLocal = 16' in cpp and 'kTile = 160' in cpp and 'kMargin = 16' in cpp and 'kStep = kTile - 2 * kMargin' in cpp
assert 'const int s0 = phaseSafePhysicalHalo ? t : std::max(t, 0)' in cpp
assert 'const int s1 = phaseSafePhysicalHalo ? t + kTile : std::min(t + kTile, int(n))' in cpp
assert shader.count('int folded = v % period;')==1
assert 'int period = 2 * (count - 1);' in shader and 'folded < count ? folded : period - folded' in shader
assert 'ivec2 g = ivec2(int(tile.srcOriginX) + int(l.x),' in shader
assert 'if (tile.reserved > 0.5)' in shader
assert 'textureSize(packedInput, 0) * 2' in shader
assert 'source.words[TILE_SLOT * kSrcPix + l.y * tile.srcWidth + l.x]' in shader

def axis(n,halo):
 spans=[]
 for t in range(-16,n,128):
  if t+16>=n:break
  s0=t if halo else max(t,0)
  s1=t+160 if halo else min(t+160,n)
  o0=max(t+16,0);o1=min(t+144,n)
  spans.append((s0,s1-s0,o0,o1-o0))
 return spans

def reflect(v,n):
 period=2*(n-1);f=v%period
 return f if f<n else period-f
count=0
for n in (32,33,34,35,64,127,128,129,130,159,160,161,256,3070,3072,4080,4096,8192):
 for halo in (False,True):
  spans=axis(n,halo)
  coverage=[0]*n
  for start,length,out,output_length in spans:
   assert 0<length<=160 and 0<output_length<=128
   assert 0<=out-start and out+output_length-start<=length
   for i in range(out,out+output_length):coverage[i]+=1
   if halo:
    assert length==160
    for src in range(start,start+length):
     r=reflect(src,n)
     assert 0<=r<n and (src&1)==(r&1)
     count+=1
  assert all(v==1 for v in coverage),(n,halo)
 if n>=256:
  assert [s[2:] for s in axis(n,True)]==[s[2:] for s in axis(n,False)]
for w,h in ((4096,3072),(3070,4080),(32,34),(132,160)):
 X=axis(w,True);Y=axis(h,True)
 for sx,wx,_,_ in (X[0],X[-1]):
  for sy,wy,_,_ in (Y[0],Y[-1]):
   for y in range(sy,sy+wy):
    for x in range(sx,sx+wx):
     xx,yy=reflect(x,w),reflect(y,h)
     assert (xx&1,yy&1)==(x&1,y&1)
     for pattern in range(4):
      # Every four-color CFA phase (RGGB/GRBG/GBRG/BGGR) is preserved.
      assert ((xx&1)^pattern&1,(yy&1)^((pattern>>1)&1)) == ((x&1)^pattern&1,(y&1)^((pattern>>1)&1))
     count+=1
print('PASS 26917 '+('live' if LIVE else 'payload')+f' full border output ownership, all 4 corners and CFA patterns, {count} even-period reflection checks; no image masking/crop')
