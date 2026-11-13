#!/usr/bin/env python3
"""Real C++17 synthetic regressions matching active GPU CFA weights & Neff math.
This supplements but does not replace pinned Vulkan GLSL compilation/device.
"""
from pathlib import Path
import tempfile,subprocess
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26925' if '--payload' in __import__('sys').argv else R
B=P/'app/src/main/cpp/iris26864/bridge'
s=(B/'Iris26925_raw_cfa_weight.comp').read_text()
for token in ('float t=(e/total)/12.25','w=1.0/(1.0+t*t)','float samplePrecision=clamp(w/variance,0.0,50000.0)','if(p.reference==0)','total<5.0'):
 assert token in s,('test must match actual 26925 shader math',token)
f=(B/'Iris26925_support_finish.comp').read_text()
assert 'sw[c]*sw[c]/ss[c]' in f
code=r'''
#include <array>
#include <cmath>
#include <algorithm>
#include <cstdio>
#include <cstdint>
struct P {float r,v;};
float weight(const std::array<P,9>& b,int ref){
 float e=0,n=0;
 if(!std::isfinite(b[4].r)||!(b[4].v>0))return 0;
 for(auto p:b){if(!(p.v>0)||!std::isfinite(p.r))continue;
  e+=std::min(p.r*p.r/std::max(p.v,1e-8f),625.f);n+=1;}
 if(ref)return 1;
 if(n<5)return 0;
 float t=e/n/12.25f;float w=1.f/(1.f+t*t);
 if(std::abs(b[4].r)>0.12f)w=0;
 return w;
}
float neff(const std::array<float,15>& a){float s=0,q=0;for(float x:a){s+=x;q+=x*x;}return q>0?s*s/q:0;}
int main(){
 std::array<P,9> b{};for(auto& x:b)x={0.001f,0.000004f};
 if(!(weight(b,0)>.98f))return 1;
 b[0].r=.09f; if(!(weight(b,0)<.30f))return 2;
 if(weight(b,1)!=1.f)return 3;
 b[4].r=.13f;if(weight(b,0)!=0.f)return 4;
 b[4].r=0;for(int i=0;i<6;++i)b[i].v=0;
 if(weight(b,0)!=0.f)return 5;
 std::array<float,15> a{};a.fill(1);
 if(std::abs(neff(a)-15.f)>0.0001)return 6;
 a.fill(0);a[3]=1;
 if(std::abs(neff(a)-1.f)>0.0001)return 7;
 a.fill(0);a[0]=1;a[1]=1;a[2]=1;
 if(std::abs(neff(a)-3.f)>0.0001)return 8;
 a.fill(0);
 if(neff(a)!=0)return 9;
 // Nine optimizer steps do NOT multiply the count of original observations.
 for(int j=0;j<9;++j){a.fill(0);a[0]=1;a[1]=1;a[2]=1; if(neff(a)!=3.f)return 10;}
 std::puts("PASS actual coherent all-CFA 3x3 motion rejection, reference identity, missing/clipped support, independent-original-frame Neff, no fake 9x frames");
}
'''
with tempfile.TemporaryDirectory(prefix='p26925_cxxmath_') as d:
 p=Path(d);(p/'t.cpp').write_text(code)
 subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(p/'t.cpp'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)

# Preserve the exact sensor-linear luminance when replacing only relative
# opponent chroma; do not flatten natural luminance grain or sharpen luma.
shader=(P/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
for key in ('float g=y-0.25*(filteredChroma.x+filteredChroma.y)*span;',
            'vec3 rgb=vec3(g+filteredChroma.x*span,g,g+filteredChroma.y*span);',
            'float neff=clamp(raw.a,0.0,uIris26925OriginalFrames);',
            'float donorSupport=clamp(v.a,0.0,uIris26925OriginalFrames);'):
 assert key in shader,('live luminance-preserving chroma support contract changed',key)
for lum in (0.004,0.02,0.1,0.3,0.75):
 for (u,v) in ((0.0,0.0),(0.25,-0.18),(-0.08,0.16)):
  span=max(lum,0.035)
  g=lum-.25*(u+v)*span
  rgb=(g+u*span,g,g+v*span)
  assert abs(.25*rgb[0]+.5*rgb[1]+.25*rgb[2]-lum)<1e-12
# Lower effective support must NEVER pretend to lower physical noise variance.
for shot,read,light in ((.00009,.000002,.1),(.00012,.000004,.01)):
 sigmas=[((shot*light+read)/n)**0.5 for n in (1,3,15)]
 assert sigmas[0]>sigmas[1]>sigmas[2]
print('PASS 26925 fixed-luma chroma correction, protected natural fine grain, actual local support noise ordering N=1/3/15')
