#!/usr/bin/env python3
"""Photon 26916: compile actual pure Java estimator and numerical GLSL math.
No fixtures substitute for Android ESSL310/SPIR-V/NDK/assembly. The real compiler
stages are mandatory in the unchanged Actions workflow.
"""
from pathlib import Path
import math, subprocess, tempfile,sys,hashlib,re
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
ROOT=R if LIVE else R/'handoff_payload_26916'
java=ROOT/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PreviewHueCalibration.java'
shader=ROOT/'app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl'
s=shader.read_text();j=java.read_text()
for token in ['IRIS_26916','for(int i=0;i<12;i++)','float mid=0.5*(lo+hi);','delta*mid',
              'vec3 result=rotateHueWithoutTone(src,lab,delta);',
              'Output=max(result,vec3(0.0));','vec3 P3_Y','oldY/newY',
              'rgbToOklab','oklabToRgb','uniform sampler2D HueDeltas']:
    assert token in s,token
assert '0.5*delta' not in s and '#version' not in s,'obsolete stepped hue fallback or GLSL version prefix'
assert 'off=-1;off<=1;off++' in j and 'wrap(median[k]-median[j])' in j
assert 'float significance=smooth(' in j and 'MAX_HUE_CHANGE = 0.32f' in j
assert 'for(int off=-2;off<=2;off++)' not in j,'unsupported sector propagation retained'
with tempfile.TemporaryDirectory(prefix='photon26916_java_') as d:
    subprocess.run(['javac','--release','17','-d',d,str(java),
                  str(R/'tests_26916/Photon26916HueRegression.java')],check=True)
    subprocess.run(['java','-cp',d,'Photon26916HueRegression'],check=True)

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def p3_to_srgb(p):
    r,g,b=p;return (1.22494018*r-0.22494018*g, -0.04205695*r+1.04205695*g, -0.01963755*r-0.07863605*g+1.09827360*b)
def srgb_to_p3(p):
    r,g,b=p;return (0.8224621*r+0.1775379*g,0.0331941*r+0.9668059*g,0.0170827*r+0.0723974*g+0.9105199*b)
def lab(rgb):
    l=dot(rgb,(0.4122214708,0.5363325363,0.0514459929))
    m=dot(rgb,(0.2119034982,0.6806995451,0.1073969566))
    n=dot(rgb,(0.0883024619,0.2817188376,0.6299787005))
    l,m,n=(max(0,x)**(1/3) for x in (l,m,n))
    return (dot((l,m,n),(0.2104542553,0.7936177850,-0.0040720468)),
            dot((l,m,n),(1.9779984951,-2.4285922050,0.4505937099)),
            dot((l,m,n),(0.0259040371,0.7827717662,-0.8086757660)))
def invlab(c):
    L,a,b=c
    l=(L+0.3963377774*a+0.2158037573*b)**3
    m=(L-0.1055613458*a-0.0638541728*b)**3
    n=(L-0.0894841775*a-1.2914855480*b)**3
    return (dot((l,m,n),(4.0767416621,-3.3077115913,0.2309699292)),
            dot((l,m,n),(-1.2684380046,2.6097574011,-0.3413193965)),
            dot((l,m,n),(-0.0041960863,-0.7034186147,1.7076147010)))
Y=(0.22897456,0.69173852,0.07928691)
def rotate(src,labv,d):
    L,a,b=labv
    angle=math.atan2(b,a)+d
    C=math.hypot(a,b)
    r=srgb_to_p3(invlab((L,C*math.cos(angle),C*math.sin(angle))))
    yy=dot(r,Y)
    if yy<=1e-8:return src
    mul=dot(src,Y)/yy
    return tuple(c*mul for c in r)
def valid(c):return all(math.isfinite(x) and x>=-0.000005 for x in c)
def corrected(src,d):
    if min(src)<0 or any(not math.isfinite(x) for x in src):return src
    labv=lab(p3_to_srgb(src))
    if math.hypot(labv[1],labv[2])<.045 or labv[0]<.10 or labv[0]>.95 or abs(d)<.0001:return src
    target=rotate(src,labv,d)
    if not valid(target):
        lo,hi=0.,1.
        for _ in range(12):
            mid=(lo+hi)/2
            if valid(rotate(src,labv,d*mid)):lo=mid
            else:hi=mid
        if lo<.0002442:return src
        target=rotate(src,labv,d*lo)
        if not valid(target):return src
    return tuple(max(0,x) for x in target)

# Reference color patches from ALL sectors, not a yellow-specific conditional.
# Probe extreme P3 boundaries by moving a physically positive channel through 0.
labels=['red','orange','yellow','green','cyan','blue','magenta','violet','neutral']
colors=[(.50,.00005,.00005),(.50,.17,.00005),(.50,.40,.00005),(.00005,.50,.00005),
        (.00005,.50,.50),(.00005,.00005,.50),(.50,.00005,.50),(.28,.00005,.50),(.30,.30,.30)]
checks=0;maxjump=0.0
for name,src in zip(labels,colors):
    for delta in [-.32,-.20,-.10,.10,.20,.32]:
        reference=None
        for i in range(65):
            # Continuous material gradient across the near-zero channel.
            q=(src[0],src[1]+i*0.00005,src[2])
            c=corrected(q,delta)
            assert valid(c),(name,delta,i,c)
            # For all positive luma samples, unchanged perceptual luminance within arithmetic tolerance.
            assert abs(dot(c,Y)-dot(q,Y))<3.0e-5,(name,delta,i,c,q)
            if reference is not None:
                jump=max(abs(a-b) for a,b in zip(c,reference))
                maxjump=max(jump,maxjump)
                # Old full/half/identity has ~0.2 channel jump across <0.001 input.
                assert jump<0.035,(name,delta,i,jump)
            reference=c
            checks+=1
    # No correction to equal neutral primaries.
assert corrected(colors[-1],.32)==colors[-1]
assert checks==len(colors)*6*65
print(f'PASS 26916 gamut/hue regression: {checks} RGB patches, nine color families, 6 bounded signed hue shifts, maximum adjacent channel step {maxjump:.6f}, P3 luma preserved')
