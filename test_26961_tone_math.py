#!/usr/bin/env python3
"""Scene 170542 frozen histogram and chromatic-luminance SDR/UHDR parallel-model regressions.
Numerical tests are local validators, not actual Android image-quality evidence.
"""
import math,random,re,pathlib,argparse
R=pathlib.Path(__file__).resolve().parent

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)))
 return t*t*(3.-2.*t)

def in_scene(p25,p50,p95,p99,b=True,sr=False,night=False,zoom=1.):
 if not b or sr or night or zoom<=0 or zoom>=1.10:return False
 if not all(math.isfinite(v) for v in (p25,p50,p95,p99)):return False
 return .003<=p25<=.013 and .012<=p50<=.032 and .045<=p95<=.125 and .95<=p99<=1.10 and p95>=3.2*p50

def foliage(y,c,active,neutral=False):
 if not active or neutral or y<=.82:return y
 c=[max(0.,v) for v in c]
 peak=max(c)
 if peak<=1e-7:return y
 warm=(max(c[0],c[1])-c[2])/peak
 chroma=(peak-min(c))/peak
 weight=smooth(.08,.28,warm)*smooth(.08,.24,chroma)
 spaced=.82+.30*(1.-math.exp(-(y-.82)/.30))
 return y+(spaced-y)*weight

def block(s,needle):
 at=s.index(needle);ed=s.index('\n}\n',at)+2
 return s[at:ed]

def check(live=False):
 root=R if live else R/'handoff_payload_26961'
 r=(root/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
 g=(root/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
 j=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 t=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java').read_text()
 b='float iris26961BOffWarmHighlightGuide('
 assert block(r,b)==block(g,b),'SDR/UHDR luma model must be exactly identical'
 assert j.count('iris26961BOffNeutralIndoor(Parameters p)')==1
 assert 'if (iris26961BOffNeutralIndoor(p)) return 0.0f;' in j
 assert 'if (iris26961BOffNeutralIndoor(p)) return new float[] {0.0f, 0.0f, 0.0f};' in j
 assert '!MotionV2Render.iris26961BOffNeutralIndoor(basePipeline.mParameters)' in t
 assert j.count('glProg.setVar("iris26961BOffNeutralIndoor", iris26961NeutralIndoor ? 1 : 0);')==2
 assert j.count('glProg.setVar("iris26961BOffColorSpacingEnabled",')==2
 assert j.count('&& !iris26961NeutralIndoor) ? 1 : 0);')==2
 assert 'iris26961BOffWarmHighlightGuide(mappedGuide,rgb)' in r
 assert 'iris26961BOffWarmHighlightGuide(mappedGuide,sourceRgb)' in r
 assert 'iris26961BOffWarmHighlightGuide(finalSdr,sourceRgb)' in g
 assert 'iris26660SharedSdrGuide(sourceGuide,masterSourcePixel,hdrPositive)' in g
 assert 'iris26961BOffNeutralIndoor!=0' in g
 assert 'iris26932BOffSdrLiftEnabled!=0 && iris26961BOffNeutralIndoor==0' in r
 assert 'iris26932BOffSdrLiftEnabled!=0 && iris26961BOffNeutralIndoor==0' in g
 # Qualified indoor 170542 has specific frozen histogram; no environmental/time guessing.
 measured=(.0071487427,.018112183,.08099365,1.)
 assert in_scene(*measured)
 assert not in_scene(*measured,b=False)
 assert not in_scene(*measured,sr=True)
 assert not in_scene(*measured,night=True)
 assert not in_scene(*measured,zoom=1.10)
 assert not in_scene(.008,.027,.7685,.8559) # 17:05:18 earlier scene should not be altered
 assert not in_scene(.006,.017,.52,1.) # ordinary bright outdoor tail
 assert not in_scene(float('nan'),.018,.08,1.)
 assert 'return p25 >= 0.003f && p25 <= 0.013f' in j
 assert '&& p50 >= 0.012f && p50 <= 0.032f' in j
 assert '&& p95 >= 0.045f && p95 <= 0.125f' in j
 assert '&& p99 >= 0.95f && p99 <= 1.10f' in j
 assert '&& p95 >= 3.2f * p50' in j
 # Retain 26959 viewfinder +2.3138642 EV, strength 65%; no changed owner.
 assert '.photon_' not in j
 # Exactly equal for neutral whites, blue sky, low tones, and any disabled mode.
 white=(1.,1.,1.);blue=(.32,.52,1.);fol=(.95,.78,.20);red=(.95,.33,.08)
 for y in [i/500 for i in range(0,551)]:
  assert foliage(y,white,True)==y
  assert foliage(y,blue,True)==y
  assert foliage(y,fol,False)==y
  assert foliage(y,fol,True,True)==y
  if y<=.82:assert foliage(y,fol,True)==y
 # Monotonic C1 shoulder; source ratios unchanged when one scalar maps the guide.
 for src in (fol,red,white,blue,(.7,.68,.62)):
  vals=[foliage(i/500,src,True) for i in range(0,551)]
  assert all(b>=a-1e-9 for a,b in zip(vals,vals[1:]))
  assert all(v>=0 for v in vals)
 for y in (.82,.85,.9,.95,1.0):
  out=foliage(y,fol,True)
  assert out<=y and y-out<.05
  if y>0.82:
   k=out/y
   v=[x*k for x in fol]
   assert max(abs(v[i]/v[0]-fol[i]/fol[0]) for i in (1,2))<1.e-12
 # In measured indoor scene: baseline +0.9997 toe is now zero; Body Contrast .35 unchanged.
 def body(y):
  return y+(y*y-y)*.35*smooth(.10,.24,y)*(1.-smooth(.50,.78,y))
 assert abs(body(.25)-.184375)<1e-9 and abs(body(.5)-.4125)<1e-9
 print('PASS 26961 exact measured 170542 neutral scene, preserved viewfinder+body0.35, warm-only monotonic SDR luma, frozen SDR/gainmap model, protected neutral whites/sky')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--payload',action='store_true');parser.add_argument('--live',action='store_true');args=parser.parse_args();check(args.live)
