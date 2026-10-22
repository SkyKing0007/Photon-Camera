#!/usr/bin/env python3
"""26866 B sensor-only fade + no extra Iris chroma owner on native B.\nConcrete regression for 26865 magenta JPEG and 26859 smooth-white ownership."""
from pathlib import Path
import sys, math, re
app=Path(sys.argv[1])
base=app/'src/main/java'
s=(base/'com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
h=(base/'com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt').read_text()
b=(base/'com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
assert s.count('nativeSensorClipFullRes26866 = nativeSensorClip26864')==1
assert s.count('nativeSensorClipFullRes26866 = nativeClip')==1
assert s.count('bRecovered26858 = renderIris26866BNativeSensorSmoothWhite(')==1
assert s.index('bRecovered26858 = renderIris26866BNativeSensorSmoothWhite(')<s.index('defringed = renderRawrLabDefringe26856(')<s.index('fcc = renderRawrFalseColor26856(')
assert 'if (rawrNativeReceipt26864 == null)' in s
assert 'bNoiseCorrected26863 = renderIris26863BPostLscChroma(' in s
assert s.count('nativeSensorClipFullRes26866')>=5
assert 'clipZoneProvenance26834 = if (edgeFalseColor26778.clipZoneEnabled &&\n                !iris26864RealRawrOwnsBurstNoise)' in s
start=b.index('if (iris26856BTextureForCleanup != 0) {',b.index('IRIS_26856_B_SEPARATE_RESULT_TRANSPORT'))
end=b.index('            resultTexture = gpu.textureId',start)
segment=b[start:end]
assert 'applyIris26837FinalClipZoneChroma(' not in segment
assert 'applyFinalNativeClipZoneChromaGuide26836(' not in segment
assert 'IRIS_26866_AB_B_NATIVE_SMOOTH_WHITE_ONLY' in segment
assert 'GLES30.glDeleteTextures(1, intArrayOf(iris26864BClipForCleanup), 0)' in segment
assert 'experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855 &&\n                clipZoneMaskTexture26836 != 0' in b
assert b.count('requireParity(lsc == null || stacked.lensShadingCorrectionApplied,')==1
assert 'if (iris26728ChromaFloor != null)' in b
assert 'experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855)' in b
assert 'smoothstep(0.0,1.0,clippedCoverage)' in h
assert 'float neutral=max(max(max(rgb.r,rgb.g),rgb.b),sharedSafeWhite)' in h
assert 'vec4(mix(original.rgb,vec3(neutral),fade),original.a)' in h
assert 'texelFetch(uNativeSensorClip,q,0).r' in h
assert 'float k[3]=float[3](1.0,2.0,1.0)' in h
assert 'gl_FragCoord.xy' in h
assert 'if(clippedCoverage<=0.0){oRgb=original;return;}' in h
# Pixel reference: B never changes an RGB sample without *nearby original RAW* clipping.
def response(clip,original,wb):
 hh=len(clip);ww=len(clip[0]); out=[]
 for y in range(hh):
  row=[]
  for x in range(ww):
   k=[1,2,1];support=sum(k[dx+1]*k[dy+1]*clip[min(hh-1,max(0,y+dy))][min(ww-1,max(0,x+dx))] for dy in (-1,0,1) for dx in (-1,0,1))/16
   col=original[y][x]; fade=(lambda t:t*t*(3-2*t))(max(0,min(1,support)))
   white=max(*col,min(wb))
   row.append(tuple(c*(1-fade)+white*fade for c in col))
  out.append(row)
 return out
z=[[(.4,.6,.5) for _ in range(9)] for _ in range(9)]
zero=[[0]*9 for _ in range(9)]
assert response(zero,z,[2,1.5,2.5])==z
full=[[1]*9 for _ in range(9)]
fullout=response(full,z,[2,1.5,2.5])
assert all(abs(v-1.5)<1e-10 for row in fullout for pixel in row for v in pixel)
site=[[0]*9 for _ in range(9)];site[4][4]=1
one=response(site,z,[2,1.5,2.5])
assert one[0][0]==z[0][0] and one[4][4][0]>z[4][4][0] and one[4][4][0]<1.5
assert one[4][4][0]>one[4][5][0]>one[4][6][0]==z[4][6][0]
# The result retains the known white target for every finite nonnegative WB/RAW triplet.
for c in (.001,.1,.75,1.5,5.0):
 for bw in (.8,1.0,2.0):
  r=response([[1]], [[(c,.5*c,1.4*c)]],[bw,bw*1.5,bw*2])[0][0]
  assert len(set(round(x,8) for x in r))==1 and r[0]>=max(c,1.4*c,bw)
print('PASS 26866 B native clipping-only 26859 smooth white at 1x+2x, 3x3 phase-safe mask, B-only and A+B no late Iris chroma, A/Night/LONG preserved; numerical clipping/no-clipping checks')
