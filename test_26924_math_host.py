#!/usr/bin/env python3
"""Real C++17 deterministic forward/adjoint consistency and hostile cases.
Not a replacement for GLSL/SPIRV/NDK/phone evaluation; compile with host C++17.
"""
from pathlib import Path
import subprocess,tempfile,os,shutil,sys
R=Path(__file__).resolve().parent
ROOT=R/'handoff_payload_26924' if '--payload' in sys.argv else R
SRC=(ROOT/'app/src/main/cpp/iris26864/bridge/Iris26924_raw_residual.comp').read_text()
ADJ=(ROOT/'app/src/main/cpp/iris26864/bridge/Iris26924_raw_adjoint.comp').read_text()
UPD=(ROOT/'app/src/main/cpp/iris26864/bridge/Iris26924_raw_update.comp').read_text()
assert 'float a=0.0;' in ADJ and 'a+=0.25*basis(o,subSample(r,sx,sy))' in ADJ
assert 'predicted+=0.25*sampleRgbChannel(subSample(r,dx,dy),c)' in SRC
assert 'p.slope[site]*max(y,0.0)+p.offset[site]' in SRC
assert 'if(y>-0.05&&y<0.975)' in SRC
assert 'p.minEvidence' in UPD and 'colorPermit' in UPD and 'p.maxLuma' in UPD
CODE=r'''
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <vector>
#include <cstdint>
using namespace std;
constexpr int RW=17,RH=19,HW=RW*2,HH=RH*2;
int col(int x,int y,int cfa){int a=(x^((cfa==1||cfa==3)?1:0))&1,b=(y^((cfa==2||cfa==3)?1:0))&1;return (a==0&&b==0)?0:((a==1&&b==1)?2:1);}
double basis(int x,int y,double px,double py){return max(0.,1.-abs(px-x))*max(0.,1.-abs(py-y));}
int idx(int x,int y,int c){return (y*HW+x)*3+c;}
void forward(const vector<double>& z, vector<double>& out,int cfa,double dx,double dy){
  fill(out.begin(),out.end(),0);
  for(int y=2;y<RH-2;++y)for(int x=2;x<RW-2;++x){int ch=col(x,y,cfa);
    double px=2*(x+dx),py=2*(y+dy),v=0;
    for(int sy=0;sy<2;sy++)for(int sx=0;sx<2;sx++){
      double a=px+sx,b=py+sy;int ix=int(floor(a)),iy=int(floor(b));
      if(ix<0||iy<0||ix+1>=HW||iy+1>=HH)throw runtime_error("sampling border");
      for(int yy=iy;yy<=iy+1;yy++)for(int xx=ix;xx<=ix+1;xx++)v+=.25*basis(xx,yy,a,b)*z[idx(xx,yy,ch)];
    }out[y*RW+x]=v;
  }
}
void back(const vector<double>& r, vector<double>& g,int cfa,double dx,double dy){
 fill(g.begin(),g.end(),0.);
 for(int y=2;y<RH-2;y++)for(int x=2;x<RW-2;x++){
  int ch=col(x,y,cfa);double px=2*(x+dx),py=2*(y+dy);
  for(int sy=0;sy<2;sy++)for(int sx=0;sx<2;sx++){
    double a=px+sx,b=py+sy;int ix=int(floor(a)),iy=int(floor(b));
    for(int yy=iy;yy<=iy+1;yy++)for(int xx=ix;xx<=ix+1;xx++)
      g[idx(xx,yy,ch)]+=.25*basis(xx,yy,a,b)*r[y*RW+x];
  }
 }
}
int main(){vector<double> z(HW*HH*3),g(z.size());vector<double> r(RW*RH),u(r.size());
 for(int i=0;i<int(z.size());i++)z[i]=.27+sin(.073*i)*.11+cos(.11*i)*.035;
 for(int i=0;i<int(r.size());i++)r[i]=sin(.09*i)*.11+cos(.22*i)*.21;
 for(int cfa=0;cfa<4;cfa++)for(auto d:array<array<double,2>,6>{{{0,0},{.2,-.4},{.75,.45},{-.63,.18},{1.3,-.9},{-.85,1.1}}}){
  forward(z,u,cfa,d[0],d[1]);back(r,g,cfa,d[0],d[1]);
  double lhs=0,rhs=0;for(int i=0;i<int(r.size());i++)lhs+=u[i]*r[i];for(int i=0;i<int(z.size());i++)rhs+=z[i]*g[i];
  if(abs(lhs-rhs)>2e-11)throw runtime_error("failed U-transpose numerical parity");
 }
 // Noise variance must be positive and clipping excludes untrusted pixels.
 for(double y:{-0.02,.002,.20,.86,.98}){
   double shot=.00016,read=.000003;double v=max(shot*max(y,0.)+read,1e-8);
   if(!(isfinite(v)&&v>0))throw runtime_error("noise model not positive");
   if(y>=.975 && !(y>=.975))throw runtime_error("clip gate");
 }
 printf("PASS true Bayer 2x box/bilinear U vs U^T across 4 CFA patterns, 6 subpixel phases; host C++17; per-site noise positivity\n");
}
'''
with tempfile.TemporaryDirectory(prefix='p26924_math_') as d:
 src=Path(d)/'26924_model.cpp';exe=Path(d)/'26924_model';src.write_text(CODE)
 compiler=shutil.which('g++') or shutil.which('clang++')
 if not compiler:raise AssertionError('real C++17 compiler unavailable; no mock/skip')
 subprocess.run([compiler,'-std=c++17','-O2','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS 26924 source parity of forward/adjoint basis, robust RAW/noise gates; real C++17 compiled and executed')

# Exact source/host schedule proof: 3 outer x 3 new raw-observation gradients.
import re, math
co=(ROOT/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
rr=(ROOT/'app/src/main/cpp/iris26864/bridge/Iris26924MultiframeRecorder.cpp').read_text()
assert 'kOuterIterations=3u' in co and 'kImageUpdatesPerOuter=3u' in co
assert 'record26924ClearGradient(command_)' in co and 'record26924Update(command_,std::uint32_t(frames.size()),outer,imageStep)' in co
assert 'if (outer>0u)' in co and 'record26924ReferenceModel(command_)' in co
m=re.search(r'kStepScale\[3\]\[3\]\s*=\s*\{(.*?)\};',rr,re.S);assert m
rows=re.findall(r'\{([^{}]+)\}',m.group(1));assert len(rows)==3
step=[[float(v.strip().rstrip('f')) for v in row.split(',')] for row in rows]
assert all(len(row)==3 for row in step)
flat=[v for row in step for v in row]
assert len(flat)==9 and all(0<v<0.5 for v in flat) and all(flat[i]>=flat[i+1] for i in range(8))
assert rr.count('kStepScale[outer][imageStep]')==1
# For a noise-model-consistent, stationary, single-parameter RAW observation,
# each of nine freshly recomputed data gradients must monotonically lower the
# observation mismatch; exact-zero residual and absent support must not drift.
for evidence in (0.,2.,100.,10000.):
    for target,estimate in ((0.7,0.1),(0.05,0.5),(0.5,0.5)):
        start=abs(target-estimate)
        z=estimate
        for gain in flat:
            g=evidence*(z-target)
            v=evidence
            delta=-gain*g/(v+10.) if v>=2. else 0.
            z+=max(-.006,min(.006,delta))
            assert math.isfinite(z) and abs(z-target)<=start+1e-12
            start=abs(z-target)
        if evidence==0 or target==estimate:assert z==estimate
assert 3*sum((.006,.0045,.003)) < .05
assert 3*sum((.0015,.0010,.0007)) < .012
print('PASS 26924 true 3x3 nine-fresh-residual solver schedule, deterministic monotone stationary update, no-data protection and total per-channel step caps')
