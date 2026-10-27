#!/usr/bin/env python3
"""Independent 26885 non-device pattern controls. Not actual AMaZE/SPIR-V.
Checks mathematical B-ON chroma-evidence policy for universal high-frequency
patterns without semantic object masks. No source changes or user-settings.
"""
import _26885_vector_math as np
import math

def luminance(v):return float(np.dot(v,(.2126,.7152,.0722)))
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0.,1.)
    return float(t*t*(3-2*t))
def chroma(v):return v-luminance(v)
def strength(v):return np.linalg.norm(chroma(v))/max(luminance(v),.025)
def core(pix,guide,neighbor_color,clip_bits=0):
    a,b=luminance(pix),luminance(guide)
    if a<.012 or b<.012 or max(a,b)>8:return pix
    c,g=chroma(pix),chroma(guide)
    cn=strength(pix)
    mismatch=np.linalg.norm(c-g)/max(a,b,.035)
    if cn<.025 or mismatch<.035:return pix
    near=max(strength(guide),neighbor_color)
    w=.82*(1-smooth(.025,.110,near))*smooth(.025,.20,max(cn-near,0))*smooth(.035,.25,mismatch)
    w*=1. if clip_bits==0 else (.4 if clip_bits==1 else 0.)
    d=g-c
    for i in range(3):
        if d[i]<0:w=min(w,pix[i]/max(-d[i],1e-7))
    return pix+np.clip(w,0,.82)*d

shapes=(
 lambda x,y:(x//2)%2,
 lambda x,y:(x//3)%2,
 lambda x,y:(y//2)%2,
 lambda x,y:(y//5)%2,
 lambda x,y:((x+y)//2)%2,
 lambda x,y:((x-y+128)//3)%2,
 lambda x,y:((x//2)+(y//2))%2,
 lambda x,y:(int(math.hypot(x-15,y-17))//2)%2,
 lambda x,y: int((x*3+y*2)%7<3),
)
count=0
for mode,shape in enumerate(shapes):
 for phase_x,phase_y in ((0,0),(1,0),(0,1),(1,1)):
  for bright in (.18,.55,.89,.96):
   for y in range(5,26):
    for x in range(6,27):
     neutral=(.10+.85*shape(x+phase_x,y+phase_y))*bright
     guide=np.full(3,neutral)
     false=np.array((.12,-.063,.12)) if (x+y)%2 else np.array((-.094,.055,-.09))
     false-=luminance(false)
     amaze=np.maximum(guide+bright*false,0.)
     corrected=core(amaze,guide,0)
     before=np.linalg.norm(chroma(amaze))
     after=np.linalg.norm(chroma(corrected))
     if before>0.001 and neutral>.012:
      assert after<=before*.55+1e-8,(mode,phase_x,phase_y,x,y,before,after)
     assert abs(luminance(corrected)-luminance(amaze))<2e-11
     assert corrected.min()>=-1e-9
     # Colored hair-thin subpixel structures with actual guide evidence vetoed.
     hue=bright*np.array((.9,.06,.09)) if (x+y)%2 else bright*np.array((.04,.1,.93))
     assert np.array_equal(core(hue,hue,strength(hue)),hue)
     assert np.array_equal(core(amaze,guide,0,3),amaze)
     count+=1
print(f'PASS 26885 universal neutral high-frequency (9 structures, 4 CFA offsets, 4 brightness), colored-line and clipping/luma controls; {count:,} cases; actual AMaZE/real compilers NOT RUN')
