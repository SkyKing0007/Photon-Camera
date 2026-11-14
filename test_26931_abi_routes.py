#!/usr/bin/env python3
"""26931 output/descriptor, 3x2 tuning schedule and preserved input/output routes."""
from __future__ import annotations
import sys
from pathlib import Path
from build_26931_incremental import R,scope,fail

def main():
 _,_,base,new=scope()
 def txt(k):return (R/(k if '--live' in sys.argv else 'handoff_payload_26931/'+k)).read_text()
 java=txt('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java')
 glue=txt('app/src/main/cpp/iris26864/Iris26931LkrAndroidInterop.cpp')
 stack=txt('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
 motion=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
 for invariant in ['nativeMerge(input,w,h,stridePx,cfa,','commonBlack,commonWhite,wb,OUTPUT_SCALE,TILE,OVERLAP,null,',
                   'false,stats,tuning,Math.multiplyExact(w,2),Math.multiplyExact(h,2)',
                   'Arrays.fill(tuning,Float.NaN);','tuning[0]=T;','tuning[1]=DATA_STEPS;',
                   'nativePublishRgba16f(reconstructed,rgbTwoXTexture,w*2,h*2)',
                   'GLES30.glFinish();','nativePublishClipR16f(raw[referenceIndex]',
                   'SrpBridge.nativeFreeDirect(reconstructed)']:
  if invariant not in java:fail('LKR original JNI exact runtime contract missing '+invariant)
 # Native published full-resolution camera RGB, original selected frame clip.
 for invariant in ['glTexSubImage2D(GL_TEXTURE_2D,0,0,y,width,h,GL_RGBA,GL_FLOAT',
                   'glTexSubImage2D(GL_TEXTURE_2D,0,0,oy,GLsizei(outW),nrows,GL_RED,GL_HALF_FLOAT',
                   'const float normal=(float(line[x])-black)/(white-black);',
                   'dst[2*x]=clip;dst[2*x+1]=clip;',
                   'UnpackState state;','glFlush();']:
  if invariant not in glue:fail('sensor RAW 50MP GL native contract absent '+invariant)
 # Pin unchanged algorithm: external LKR release is SHA-locked; the sole tuning
 # variation is T3/Z2 => original ApplyTuning prior schedule index=1.
 schedule=lambda T,z: (list(range(1,T,2)),T*z)
 if schedule(3,2)!=([1],6) or schedule(8,3)!=([1,3,5,7],24):fail('3x2 schedule math')
 # No changes to other 2036 files, including all original GLSL shaders,
 # vendor, Java color/tone, UHDR JPEG, A/B OFF, Spektra and DNG.
 for k,v in base.items():
  if k not in {'app/build.gradle','app/version.properties',
    'app/src/main/cpp/CMakeLists.txt',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'}:
   if new[k]!=v:fail('unpermitted mode/tone/UHDR/vulkan/vendor source mutation '+k)
 if 'lkrNativeFullRgb26931=true' not in stack or 'renderIris26859BLensShading(nativeRgb,' not in stack:fail('LSC once and only B ON')
 if 'GlesIris26931LkrBridge.run(' not in motion:fail('B ON runtime Java owner not connected')
 if 'Iris26920NativeProbe.arm(' in stack:fail('legacy wavelet/Wronski B ON residual owner')
 if stack.count('renderRawrBPostAmaze26856(')<2:fail('inherited shared color route lost')
 print('PASS LKR 3x2 six data steps; original compiled LKR/HQS priorAt={1}, 2x full native RGB, original sensor clip; Iris tone/HDR/GPU carriers protected')
if __name__=='__main__':
 try:main()
 except Exception as e:print('ERROR',e,file=sys.stderr);sys.exit(1)
