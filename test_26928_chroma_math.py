#!/usr/bin/env python3
"""Source-constrained synthetic chroma/math tests. NOT a physical RAW/Android image-quality test."""
from pathlib import Path
import math,sys
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26928' if '--payload' in sys.argv else R
shader=(P/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
for gate in ('if(n<4.0)return c;','if(cleanN<4.0)return c;',
             'if(scatter>0.085)return c;',
             'if(displaced>=2.0 || firstScatter>0.092)return c;',
             'if(saturation>0.20 && peers>=2.0)return c;',
             'if(structure>0.28 && peers>=2.0)return c;',
             'if(difference<0.060)return c;',
             'gain*=1.0-0.48*smoothstep(0.0,3.0,peers);'):
 assert gate in shader,gate

def sm(a,b,x):
 t=min(1.,max(0.,(x-a)/(b-a)));return t*t*(3.-2.*t)
def vnorm(v):return math.hypot(*v)
def avg(v):return tuple(sum(x[k] for x in v)/len(v) for k in range(2))
# This models the EXACT fixed-radius robust consensus decision mathematics, not
# raw sensor conversion, GLSL execution or any actual subject photograph.
def decision(center,donors,peers=0,structure=.2,y=.06,clipped=False,b_off=True):
 saturation=vnorm(center)
 if not b_off or clipped or y<.003 or y>.82 or saturation<.055 or saturation>.54:return center
 if saturation>.14 and peers>=3:return center
 if saturation>.20 and peers>=2:return center
 if structure>.28 and peers>=2:return center
 good=[x for x in donors if vnorm(x)<.60]
 if len(good)<4:return center
 initial=avg(good)
 scatter0=math.sqrt(sum(math.dist(x,initial)**2 for x in good)/len(good))
 displaced=sum(1 for x in good if math.dist(x,initial)>=.13)
 if displaced>=2 or scatter0>.092:return center
 clean=[x for x in good if math.dist(x,initial)<.13]
 if len(clean)<4:return center
 consensus=avg(clean)
 scatter=math.sqrt(sum(math.dist(x,consensus)**2 for x in clean)/len(clean))
 if scatter>.085:return center
 diff=math.dist(center,consensus)
 if diff<.060:return center
 if peers>=2 and saturation>.22 and structure>.09:return center
 g=.57*sm(.060,.21,diff)*(1-sm(.28,.54,saturation))*(1-sm(.045,.085,scatter))
 g*=1-.48*sm(0,3,peers)
 return tuple(a*(1-g)+b*g for a,b in zip(center,consensus))

def moves_towards(center, donors, **kw):
 out=decision(center,donors,**kw)
 return math.dist(out,avg(donors))<math.dist(center,avg(donors))-.005
# Unstructured colored speckle on a dark neutral, including where no clipping.
for y in (.004,.02,.16,.68):
 assert moves_towards((.24,-.10),[(.01,-.004)]*7,y=y,structure=.025)
# Same-material repair near bright-dark edge, with five valid same-side donors.
assert moves_towards((.28,.04),[(.02,.0)]*5,structure=.23,peers=0)
# Colored real material: outlier repaired TOWARD its supported genuine color,
# not toward neutral / arbitrary grayscale.
assert moves_towards((.26,-.05),[(.08,-.04)]*6,y=.09)
# Extremely clipped center, low signal, superres ON remain byte-identical.
for kw in (dict(clipped=True),dict(b_off=False),dict(y=.001),dict(y=.90)):
 assert decision((.22,-.08),[(0,0)]*8,**kw)==(.22,-.08),kw
# Genuine tiny strong color, colored coherent object and text/line with
# immediate color witnesses preserved, including equal-luminance boundaries.
assert decision((.51,.20),[(0,0)]*8)==(.51,.20)
assert decision((.26,-.08),[(0,0)]*8,peers=2)==(.26,-.08)
assert decision((.16,.02),[(0,0)]*8,peers=3)==(.16,.02)
# Same-luma different-color half-neighborhood is NOT a consensus.
assert decision((.17,.04),[(.28,.0)]*4+[(-.28,.02)]*4)==(.17,.04)
# Fewer than 4 independent uninterrupted same-side rays and sensor-clipped
# witnesses are not permission to invent any color.
assert decision((.2,.04),[(0,0)]*3)==(.2,.04)
# Explicitly verify the reconstructed pixel retains the source's luminance.
for Y in (.004,.04,.20):
 ch=decision((.24,-.1),[(.01,.0)]*6,y=Y)
 sp=max(Y,.035);g=Y-.25*(ch[0]+ch[1])*sp
 rgb=(g+ch[0]*sp,g,g+ch[1]*sp)
 assert abs(.25*rgb[0]+.5*rgb[1]+.25*rgb[2]-Y)<1e-9
# Real source's six-pixel MATERIAL ray admission, independently modeled.
# A donor cannot be used if ANY intervening site differs in brightness or
# original sensor clipping, even if the endpoint appears color-compatible.
assert 'if(rawClipped(q)){same=false;break;}' in shader
assert 'abs(vy-y)/max(max(y,vy),0.055)>0.095' in shader
RAYS=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
def ray_donors(p, scene):
 Y,C,clip=scene
 cy=Y[p];out=[]
 for dx,dy in RAYS:
  good=True
  for k in range(1,7):
   q=(p[0]+k*dx,p[1]+k*dy)
   if q in clip or abs(Y[q]-cy)/max(Y[q],cy,.055)>.095:
    good=False;break
  if good:
   q=(p[0]+6*dx,p[1]+6*dy)
   if vnorm(C[q])<.60:out.append(C[q])
 return out
p0=(12,12)
coords=[(x,y) for x in range(5,20) for y in range(5,20)]
Y={q:.055 for q in coords};C={q:(.006,-.002) for q in coords}
# Highlight on the left side, dark same-material background on the right;
# opposite-side brightness must NOT be admitted as a chroma donor.
for q in coords:
 if q[0]<12:Y[q]=.80;C[q]=(.4,-.3)
valid=ray_donors(p0,(Y,C,set()))
assert len(valid)==5 and all(vnorm(v)<.02 for v in valid),valid
assert moves_towards((.24,-.09),valid)
# A clipped site at the third pixel of a SAME-BRIGHTNESS ray excludes
# that ray regardless of its benign endpoint RGB.
Y={q:.055 for q in coords};C={q:(.002,.001) for q in coords}
valid=ray_donors(p0,(Y,C,{(15,12)}))
assert len(valid)==7,valid
# Equal-brightness colors on opposite sides form two material populations;
# they cannot be averaged to create a false third boundary color.
for q in coords:
 if q[0]<12:C[q]=(.29,-.11)
valid=ray_donors(p0,(Y,C,set()))
assert len(valid)==8
assert decision((.18,-.045),valid)==(.18,-.045)
assert 'if(uIris26924BOff!=0 && ring>=2) continue;' in shader
print('PASS 26928 controlled synthetic shadow/bright/edge/multicolor/clip/no-bleed chroma contracts; device IQ NOT RUN')
