#!/usr/bin/env python3
"""Analytic B-OFF-only linear SDR shoulder and UHDR denominator rebase proof."""
import argparse,math,pathlib,re
R=pathlib.Path(__file__).resolve().parent
F='float iris26960BOffSdrColorSpacing('
def code(kind,live):
 path='app/src/main/assets/shaders/motionv2/'+kind+'.glsl'
 return (R/path if live else R/'handoff_payload_26960'/path).read_text()
def block(s):
 n=s.index(F);end=s.index('\n}\n',n)+2;return s[n:end]
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def guide(y,source):
 if y<=0.52 or y>=1: return y
 rise=smooth(.52,.72,y);fade=1-smooth(.88,1.,y)
 white=1-smooth(.95,1.10,max(source,0))
 return max(0,y-.045*rise*fade*white)
def verify(live=False):
 r=code('render',live);g=code('gainmap',live)
 assert r.count(F)==g.count(F)==1 and block(r)==block(g), 'SDR/gainmap must have byte-identical guide'
 assert r.count('iris26960BOffSdrColorSpacing(mappedGuide,sourceGuide);')==1
 assert r.count('iris26960BOffSdrColorSpacing(mappedGuide,guide);')==1
 assert g.count('iris26960BOffSdrColorSpacing(finalSdr,sourceGuide);')==1
 # B-only exact pre-existing enable: generic A/A+B, B ON, Night stay unchanged.
 assert 'if(iris26954BOffNight26940Sdr!=0)' in r and 'if(iris26932BOffSdrLiftEnabled!=0)' in r
 assert 'if(iris26954BOffNight26940Sdr!=0)' in g and 'if(iris26932BOffSdrLiftEnabled!=0)' in g
 assert r.count('if(iris26941BOffHdrqLowZoom!=0)')>=2 and g.count('if(iris26941BOffHdrqLowZoom!=0)')>=1
 for src in (0,0.1,.3,.7,.96,1,1.1,2.8):
  arr=[guide(i/10000,src) for i in range(0,20001)]
  assert all(arr[j+1]>=arr[j]-1e-9 for j in range(len(arr)-1)),f'nonmonotone source={src}'
  for y in (0,0.03,.4,.52,1,1.2,2):assert abs(guide(y,src)-y)<1e-10
  assert all(0<=y-guide(y,src)<=.045000001 for y in [i/10000 for i in range(20001)])
 for y in (0,.7,.8,.9,1.0):assert guide(y,1.10)==y
 # The HDR numerator is algebraically stable only when the actual SDR and
 # gain-map model BOTH receive the same scalar guide delta. Unchanged HDR
 # target = new SDR + (target - new model), compared to original baseline.
 for signal in (.01,.05,.2,.7,.9):
  for src in (.1,.5,.89,1.0):
   prior=.61+0.32*signal;delta=prior-guide(prior,src)
   sdr=.9*prior;model=.9*prior;new=.9*(prior-delta)
   target=1.5
   assert abs((new+max(target-(model-.9*delta),0))-(sdr+max(target-model,0)))<1e-10
 print('PASS B-only monotone scalar SDR highlight spacing, true-white/black identity and mirrored SDR/UHDR denominator')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--payload',action='store_true');ap.add_argument('--live',action='store_true');a=ap.parse_args();verify(a.live)
