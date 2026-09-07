#!/usr/bin/env python3
from pathlib import Path
import math,re,sys

def fail(m): raise SystemExit('FAIL: '+m)
def need(s,t,l):
    if t not in s: fail(l+' missing '+t)
def forbid(s,t,l):
    if t in s: fail(l+' stale '+t)
def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))

def physical_rescue(ordinary,physical,rescue,target_loss):
    censored=min(physical,rescue)
    return (1.0-target_loss)*ordinary + target_loss*censored
# Hard protection-parity regressions: rescue never overrides physical protection.
if physical_rescue(.8,0.0,1.0,1.0)!=0.0: fail('full rescue bypassed physical rejection')
if abs(physical_rescue(.37,.9,1.0,0.0)-.37)>1e-9: fail('measurable boundary lost ordinary protection')
if physical_rescue(.9,.6,.9,1.0)>.600001: fail('censored core exceeded physical cap')
if physical_rescue(.2,.55,.95,.5)>.375001: fail('transition exceeded ordinary/physical convex bound')

def old_sdr(guide,gain):
    target=max(guide,0.0)*max(gain,1e-6)*.80
    knee=.40
    if target<=knee:return target
    reserve=.60;excess=target-knee
    return knee+reserve*excess/(excess+reserve)

def tone_plan(gain,p99,p998,strength=1.0):
    a=old_sdr(p99,gain); b=old_sdr(p998,gain)
    ha=p99*gain*.80; hb=p998*gain*.80
    st=clamp(strength)
    if not (a>.73 and b>a+.005 and hb>ha+.02): st=0.0
    return a,b,ha,hb,st

def stretch(old,a,b,st):
    start=.72
    if st<=0 or old<=start or not (b>a+.005 and a>start+.01):return old
    if old<=a:
        t=clamp((old-start)/(a-start)); target=start+t*(.88-start)
    elif old<=b:
        t=clamp((old-a)/(b-a)); target=.88+t*(.995-.88)
    else:
        t=clamp((old-b)/max(1.0-b,1e-6)); target=.995+t*(1.0-.995)
    target=clamp(target,old,1.0)
    return old+(target-old)*st

def hdr_map(v,a,b,st):
    if st<=0 or v<=0 or not (b>a+.02 and a>0):return v
    start=min(a,max(.80,a*.75)); boost=1.0
    if v>start and v<=a:
        t=clamp((v-start)/max(a-start,1e-6)); boost=1+t*(1.35-1)
    elif v>a and v<=b:
        t=clamp((v-a)/max(b-a,1e-6)); boost=1.35+t*(2.40-1.35)
    elif v>b: boost=2.40
    return v*(1+(boost-1)*st)
# Chandelier fixture derived from the supplied 26608 device telemetry.
gain=4.11548;p99=.7133789;p998=1.0
a,b,ha,hb,st=tone_plan(gain,p99,p998,1.0)
if abs(a-.85875)>.004 or abs(b-.89692)>.004: fail(f'chandelier old shoulder reference drift {a:.6f}/{b:.6f}')
na,nb=stretch(a,a,b,st),stretch(b,a,b,st)
if abs(na-.88)>.002 or abs(nb-.995)>.002: fail(f'chandelier SDR anchors {na:.6f}/{nb:.6f}')
if (nb-na) <= 2.5*(b-a): fail('SDR structured tail was not materially de-plateaued')
if stretch(.40,a,b,st)!=.40 or stretch(.70,a,b,st)!=.70: fail('body below tail anchor changed')
# Monotonic + never-darken over entire SDR domain.
prev=-1.0
for i in range(2001):
    x=i/2000
    y=stretch(x,a,b,st)
    if y+1e-7<x: fail('SDR stretch darkened old rendition')
    if y+1e-7<prev: fail('SDR stretch non-monotonic')
    prev=y
h99=hdr_map(ha,ha,hb,st); h998=hdr_map(hb,ha,hb,st)
if abs(h99-ha*1.35)>.005 or abs(h998-hb*2.40)>.01: fail('UHDR target anchors incorrect')
if h998>8.0+.02 or h998<7.8: fail(f'UHDR target does not use available 8x capacity safely: {h998:.4f}')
if (h998-h99) <= 2.0*(hb-ha): fail('UHDR structured highlight range not expanded')
# No semantic-scene production branch and path parity tokens.
if len(sys.argv)!=3: fail('usage base candidate')
b,c=map(Path,sys.argv[1:])
paths={
 'render':'app/src/main/assets/shaders/motionv2/render.glsl',
 'gain':'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'adaptive':'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
 'native':'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
 'java':'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'encoder':'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
 'sabre':'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
 'stacker':'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
}
s={k:(c/v).read_text() for k,v in paths.items()}
for t in ['IRIS_26609_SDR_P99_TARGET = 0.88f','IRIS_26609_SDR_P998_TARGET = 0.995f','IRIS_26609_HDR_P99_BOOST = 1.35f','IRIS_26609_HDR_P998_BOOST = 2.40f','IRIS_26592_MOTION_UHDR_MAX_RATIO = 8.0f']:
    need(s['java'],t,'1x rendition authority')
for t in ['targetP99=0.88','targetP998=0.995']:
    need(s['render'],t,'1x SDR shader')
for t in ['1.35','2.40','iris26609HdrP99Final','iris26609HdrP998Final']:
    need(s['gain'],t,'1x UHDR shader')
for t in ['targetP99=0.88','targetP998=0.995']:
    need(s['adaptive'],t,'adaptive predictor parity')
for t in ['targetP99=0.88','targetP998=0.995','mix(1.0,1.35,t)','mix(1.35,2.40,t)','iris26609MapHdrTarget(hdrBase)']:
    need(s['native'],t,'true2x GPU parity')
for t in ['targetP99=0.88f','targetP998=0.995f','1.35f','2.40f']:
    need(s['native'],t,'true2x CPU parity')
for t in ['iris26609Tone.oldP99Mapped','iris26609Tone.oldP998Mapped','iris26609Tone.hdrP99Final','iris26609Tone.hdrP998Final','iris26609Tone.strength']:
    need(s['encoder'],t,'SR Java tone-plan handoff')
# Exact protection contract and forbidden 26608 weaker active equation.
for t in ['oPhysicalReverseWeight = clamp(unblocker, 0.0, 1.0);','float censoredCoreWeight = min(physicalWeight, rescueConfidence);','float finalWeight = mix(ordinaryWeight, censoredCoreWeight, targetLoss);']:
    need(s['sabre'],t,'SHORT physical protection')
forbid(s['sabre'],'oWeight = clamp(mix(ordinaryWeight, rescueConfidence, targetLoss), 0.0, 1.0);','26608 direct rescue replacement')
for t in ['shortPhysicalReverseWeight26609','shortPhysicalWeight26609','renderDilation(shortPhysicalReverseWeight26609, shortPhysicalWeight26609)']:
    need(s['stacker'],t,'shared dilation protection')
# Working 26608 acquisition and preview owners are strict inherited bytes.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java']:
    if (b/rel).read_bytes()!=(c/rel).read_bytes(): fail('26608 acquisition/preview authority changed '+rel)
# Scan only new production-code scopes, excluding comments/strings, for scene classifiers.
code='\n'.join(s.values())
code=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',' ',code,flags=re.S).lower()
for word in ['chandelier','cloud','window','bulb','curtain','snow','reflection']:
    if re.search(r'\b'+word+r'\b',code): fail('scene-semantic production classifier '+word)
print('PASS SHORT protection parity regressions: full rescue remains physical-capped; measurable boundaries preserve ordinary protection')
print('PASS chandelier SDR fixture de-plateaus p99/p998 to 0.88/0.995 while preserving body and monotonicity')
print('PASS UHDR structured tail expands toward but not beyond the proven 8x Motion encoding capacity')
print('PASS 1x SDR/UHDR + adaptive predictor + true2x CPU/GPU share one non-semantic Iris rendition plan; SR OFF/ON parity locked')
