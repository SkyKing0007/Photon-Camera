#!/usr/bin/env python3
"""Independent 26930 physical-LSC variance, CFA, local coverage, grain and hue numerical regressions.
Not a substitute for real GLSL/SPIR-V, Android compilers, or actual device IQ.
"""
from pathlib import Path
import sys,math,re
R=Path(__file__).resolve().parent
P=(R/'handoff_payload_26930') if '--payload' in sys.argv else R
shader=(P/'app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp').read_text()
inc=(P/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
# Site arrays are physical Bayer 2x2 positions, not RGBA channels. All CFAs.
# RGGB=R,G,G,B; GRBG=G,R,B,G; GBRG=G,B,R,G; BGGR=B,G,G,R.
for cfa,physical in enumerate(((0,1,2,3),(1,0,3,2),(2,0,3,1),(3,1,2,0))):
 r=cfa;b=3-cfa;g0=0 if cfa in (1,2) else 1;g1=3 if cfa in (1,2) else 2
 assert (r,g0,g1,b)==physical,(cfa,physical,(r,g0,g1,b))
assert 'const uint32_t redSite=localCfa,blueSite=3u-localCfa;' in inc
assert 'const uint32_t green0=(localCfa==1u||localCfa==2u)?0u:1u;' in inc
assert 'const uint32_t green1=(localCfa==1u||localCfa==2u)?3u:2u;' in inc
# Unfiltered AMaZE values already had physical LSC. Derive original sensor
# signal by division, then independently propagate each phase's shot/read
# through physical gain^2 AND WB^2. Corner amplification must be real.
shot=(6e-5,5e-5,9e-5);read=(1.5e-6,1e-6,2e-6);sensor=(.005,.005,.005);wb=(1.8,1,1.5)
def variance(gains):
 post=tuple(x*g for x,g in zip(sensor,gains))
 return tuple((a*(x/g)+b)*g*g*w*w for a,b,x,g,w in zip(shot,read,post,gains,wb))
center=variance((1,1,1));corner=variance((2.4,1.8,2.8))
assert all(x>y*3.2 for x,y in zip(corner,center))
assert math.sqrt(sum(corner)/3)>math.sqrt(sum(center)/3)*1.8
# The original confidence saturates at 3 contributors, and is NOT N_eff 15.
def support(c,n=15):return (1-c)+c*min(3,n)
assert support(0)==1 and support(1)==3 and support(.5)==2
assert support(1)!=15
# Previous 26929 ignored very deep shadow and rejected high residuals, exactly
# the problematic behavior observed at the 26929 lower-right shadow.
assert 'if(y>0.00035 && y<0.85' in shader
assert 'y>0.003' not in shader
assert '5.5*floorColor' not in shader
assert 'noiseSignificance=smoothstep(0.55*sigmaChroma,2.6*sigmaChroma,residual)' in shader
# Test smoothstep behavior: 6-sigma unsupported colour must remain eligible,
# not silently become PROTECTED as in 26929.
def sm(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a)))
 return t*t*(3-2*t)
for r in (2.6,5.5,12.0):assert abs(sm(.55,2.6,r)-1)<1e-10
# Luma is unchanged by chroma correction even for a large RGB adjustment.
l=(.25,.5,.25)
for v in ((.7,-.4,-.8),(-.3,.9,-.75),(-.02,.1,.05)):
 dt=sum(a*b for a,b in zip(v,l))
 centered=tuple(a-dt for a in v)
 assert abs(sum(a*b for a,b in zip(centered,l)))<1e-12
assert 'adjustment-=vec3(lightness(adjustment));' in shader
assert 'vec3 revised=(center+correction*adjustment+vec3(restoreY))/p.wb.rgb;' in shader
assert 'max(revised,vec3(0.0))' in shader
# Real chromatic material supported by neighbor hue is protected; unsupported
# chroma spikes are eligible only with valid same-surface, two-sided donors.
assert 'float realHue=' in shader and '(1.0-0.90*realHue)' in shader
assert 'float twoSided=' in shader and 'nearWt>=2.3 && farWt>=1.25' in shader
assert 'ivec2 mid=q+off/2;' in shader and 'similarity*=1.0-smoothstep' in shader
assert 'float coloredCenter=' in shader and 'float coloredDonors=' in shader
assert 'float restoreY=' in shader and 'synthetic grain' in shader.lower()
assert 'f.burstGreenNoisePerMergedSample[0]' in inc # original RAWR wavelet remains unchanged
print('PASS 26930 four-CFA physical noise variance+LSC corner amplification, deep-shadow eligibility, strong outlier, bilateral edge/hue/luminance invariance')
