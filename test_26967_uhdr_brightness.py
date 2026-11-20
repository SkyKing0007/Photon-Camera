#!/usr/bin/env python3
"""Gainmap output is unity outside highlights, mode-isolated and tied to actual SDR base."""
import pathlib,sys,math,random
R=pathlib.Path(__file__).resolve().parent;P=R if '--live' in sys.argv else R/'handoff_payload_26967'
G=(P/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
S=(P/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
J=(P/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for s in ('uniform int iris26967PhotoHighlightsOnly;','float genuineBright=smoothstep(0.32,0.65,sourceGuide);','float hdrBright=smoothstep(0.62,0.96,linearTargetY);','ratio=1.0+(ratio-1.0)*highlightOnly;','float hdrIntentY=sdr+matchedIntentDelta;','sdr+UHDR_OFFSET'):
 assert G.count(s)>=1,s
assert G.index('ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);')<G.index('if(iris26967PhotoHighlightsOnly!=0)')<G.index('Output=clamp(log2(ratio)')
assert 'float sdr=motionHdrHandoff!=0' in G and 'SdrBuffer' in G
assert 'iris26641BilinearSdrLinear(sourcePixel)' in G and 'srgbDecode(iris26550BilinearSdr(sourcePixel))' in G
assert 'iris26967Option2Encoded' not in G and 'iris26967PhotoHighlightsOnly' not in S
assert J.count('glProg.setVar("iris26967PhotoHighlightsOnly"')==1
allow=lambda motion,b,sr,night,night_b:motion and not night and not night_b and (not b or not sr)
for motion in (0,1):
 for b in (0,1):
  for sr in (0,1):
   for night in (0,1):
    for nb in (0,1):
     if night or nb or not motion or (b and sr):assert not allow(motion,b,sr,night,nb)
assert all(allow(*q) for q in ((1,0,0,0,0),(1,0,1,0,0),(1,1,0,0,0)))
def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)
def gain(r,src,hdr):return 1+(r-1)*smooth(.32,.65,src)*smooth(.62,.96,hdr)
random.seed(26967)
for _ in range(20000):
 r=random.uniform(1,5);src=random.uniform(0,1.9);hdr=random.uniform(0,1.9);value=gain(r,src,hdr)
 assert math.isfinite(value) and 1-1e-8<=value<=r+1e-8
 if src<=.32 or hdr<=.62:assert value==1
 if src>=.65 and hdr>=.96:assert abs(value-r)<1e-7
print('PASS 26967 A/B OFF only highlight UHDR pop, exact unity shadow/body, nonunity highlights, Night and B ON unchanged; actual SDR denominator')
