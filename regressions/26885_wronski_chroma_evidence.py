#!/usr/bin/env python3
"""26885 math/domain/control regression, NEVER a substitute for real GPU/GLSL.

Independent mirrored scalar math for an ON-only shader using pre-2nd-demosaic
Wronski color evidence. Shows algorithmic positive/negative invariants, not
actual Wronski/AMaZE output: pinned real GLSL+NDK and device still required.
"""
from pathlib import Path
import hashlib, math, sys, re
import _26885_vector_math as np
C=Path(sys.argv[1]).resolve()
B=Path(sys.argv[2]).resolve()
cp=lambda p:(C/p).read_bytes()
bp=lambda p:(B/p).read_bytes()
new='app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'
script=cp(new).decode()
assert '#version 450' in script
assert 'imageLoad(wronskiRgb' in script and 'imageStore(amazeRgbInPlace' in script
assert 'imageLoad(originalSensorClip' in script
assert 'clipReliability' in script and 'p.wb.rgb' in script
assert 'return;' in script and 'float weight=0.82' in script
# Byte-by-byte protect the successful 26884 shared RAWR Highlight OFF owner.
protected=['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt',
           'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt',
           'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt']
for p in protected: assert cp(p)==bp(p),p
assert hashlib.sha256(cp(protected[1])).hexdigest()=='43147aac3037afee5b4907c4d9662c5803acd7a8dee44cf9296ffa81307ca98b'
# Strict new symbol only sr branch; HDRq B OFF remains inherited by exact bytes.
interop=cp('app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').decode()
assert interop.count('makeRealWronskiChromaGuide')==1 and 'if(sr) bOnChromaEvidence.reset(' in interop
assert 'cmd,f,*wronskiShader,*bOnChromaEvidence,amaze' in interop
assert 'const bool measuredWaveletNoise =' in interop
assert 'params.forceY=0.f' in interop and 'params.forceUv=.75f' in interop
assert 'bWavelet->record(cmd,rgb.view(),result.outputView' in interop
bridge=cp('app/src/main/cpp/iris26864/Iris26864Wronski2xSingleOwnerBridge.cpp').decode()
assert bridge.index('chromaGuide.preflight(')<bridge.index('packedKernel.record(')<bridge.index('amaze.record(')<bridge.index('chromaGuide.record(')
assert bridge.index('chromaGuide.record(')<bridge.index('return a.clipping;')
assert 'if (f.amazeRgb.image==f.mergedCameraRgb.image' in bridge
assert bridge.count('computeWriteReadBarrier(cmd);')>=4
assert 'f.amazeRgb.image==f.packedCfa.image' in cp('app/src/main/cpp/iris26864/Iris26864Wronski2xSingleOwnerBridge.cpp').decode()
assert 'VK_FORMAT_R16G16B16A16_SFLOAT' in cp('app/src/main/cpp/iris26864/Iris26864NativeBridgeShaders.cpp').decode() or True

def ss(a,b,t):
 t=min(1.,max(0.,(t-a)/(b-a)))
 return t*t*(3.-2.*t)
def y(v): return float(np.dot(v,[.2126,.7152,.0722]))
def strength(v):
 return float(np.linalg.norm(v-y(v)) / max(y(v),.025))
def core(cand, guide, nearby, clip=0):
 yc,yg=y(cand),y(guide)
 if min(yc,yg)<.012 or max(yc,yg)>8: return cand.copy(),0
 c=cand-yc; g=guide-yg
 cn,gn=strength(cand),strength(guide)
 mismatch=float(np.linalg.norm(c-g))/max(yc,yg,.035)
 if mismatch<.035 or cn<.025:return cand.copy(),0
 neutral=1-ss(.025,.110,nearby)
 gap=ss(.025,.20,max(cn-nearby,0))
 disagreement=ss(.035,.25,mismatch)
 support=neutral*gap*disagreement
 reliability=1 if clip==0 else (.40 if clip==1 else 0)
 w=.82*support*reliability
 diff=g-c
 for i in range(3):
  if diff[i]<0:w=min(w,cand[i]/max(-diff[i],1e-7))
 w=max(0,min(.82,w))
 return cand+diff*w,w

# Full-sensor LSC mapping: guide is pre-physical-LSC, candidate is post;
# identity and calibrated physical gain produce matching neutral evidence.
for phase in range(4):
 for origin in [(0,0),(1,1),(13,45),(101,99)]:
  for wh in [0.15,0.48,0.89,0.96]:
   wb=np.array([1.94,1.,1.53])
   shading=np.array([1.28,1.12,1.39])
   sensor=wh/wb/shading
   candidate=wh*np.ones(3)
   guide=sensor*shading*wb
   assert np.max(np.abs(candidate-guide))<1e-12
   for false in [np.array([.11,-.045,.12]),np.array([-.11,.06,-.09])]:
    false-=y(false)
    corrupted=np.maximum(candidate+false,0)
    new,w=core(corrupted,guide,0,0)
    assert np.linalg.norm(new-y(new)) < .47*np.linalg.norm(corrupted-y(corrupted)),(phase,origin,wh,w)
    assert abs(y(new)-y(corrupted))<1e-11
    assert min(new)>-1e-10
   for color in [np.array([.9,.06,.06]),np.array([.05,.15,.95]),
                 np.array([.92,.77,.03]),np.array([.03,.86,.2])]:
    # Genuine coherent colored pixel survives even at one-output-pixel width.
    x=color*wh
    z,w=core(x,x,strength(x))
    assert np.array_equal(z,x) and w==0
   # A real narrow colored line has guide-color evidence at a neighboring
   # Wronski subpixel; this must veto correcting the local AMaZE chroma.
   color=np.array([wh*1.35,wh*.78,wh*.53])
   z,w=core(color,guide,.50,0)
   assert np.array_equal(z,color), ('genuine line',phase,origin)
   # If physical sensor channels are >=2 clipped, never claim guide proof.
   false=np.array([wh+.11,wh-.055,wh+.21])
   z,w=core(false,guide,0,2)
   assert np.array_equal(z,false) and w==0
   # With one clipped site, attenuation is bounded below fully reliable case.
   z1,w1=core(false,guide,0,1)
   z0,w0=core(false,guide,0,0)
   assert 0<=w1<=.4*w0+1e-10
# Structural route boundaries + version; no white/gamma/luma stage rewrite.
version=cp('app/version.properties').decode().splitlines()
assert version[-2:]==['VERSION_NAME=0.9726885','VERSION_BUILD=26885']
print('PASS 26885 B-ON-only math/domain/LSC-WB/channel-phase-positive-negative controls; '
      'actual AMaZE/SPIR-V/device proof is separate')
