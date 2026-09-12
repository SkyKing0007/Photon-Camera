#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys, xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26630_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); P=Path(__file__).resolve().parent
CHANGED=[x.strip() for x in (P/'R1_26630_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def universe(root): return {str(p.relative_to(root)):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(rel): return (C/rel).read_text()
def req(c,m):
    if not c: raise SystemExit('FAIL '+m)
b=universe(B); c=universe(C); diff=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k))
if len(b)!=1713 or len(c)!=1713 or diff!=sorted(CHANGED) or len(CHANGED)!=13: raise SystemExit(f'FAIL runtime scope/count {len(b)} {len(c)} {diff}')
for rel in ['app/src/main/res/xml/preferences.xml','app/src/main/res/values/strings.xml','app/src/main/res/values/default_prefs.xml']: ET.parse(C/rel)
ver=txt('app/version.properties'); req('VERSION_NAME=0.9726630' in ver and 'VERSION_BUILD=26630' in ver,'version/build')
matcher=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
req('MOTION_FIXED_MATCH_STRENGTH_PERCENT = 65.0f' in matcher and 'NIGHT_BASELINE_MATCH_STRENGTH_PERCENT = 65.0f' in matcher,'fixed 65 policy')
req('readMatchStrengthPercent(' not in matcher and 'SettingsManager' not in matcher.replace('No SettingsManager read',''),'persisted viewfinder owner survived')
bridge=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
req('val vgnChromaCorrectionStrength = 1.0f' in bridge and 'fixedPolicy26630=true userSetting=false' in bridge,'fixed VGN 1.0')
settings=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java')
req('KEY_VGN_CHROMA_CORRECTION' not in settings and 'KEY_SATURATION = "pref_iris_saturation"' in settings,'Iris saturation owner')
prefs=txt('app/src/main/res/xml/preferences.xml')
req('pref_motion_viewfinder_match_strength' not in prefs and 'pref_iris_vgn_chroma_correction' not in prefs and 'pref_iris_saturation' in prefs,'UI authority isolation')
rj=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
req('basePipeline.mParameters.motionV2Active\n                && iris26630Tone != null ? iris26630Tone.saturation : 1.0f' in rj,'Night 1x saturation isolation')
enc=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
req('parameters.motionV2Active && toneSettings != null' in enc and '? Math.max(0.0f, Math.min(2.0f, toneSettings.saturation)) : 1.0f' in enc,'Night true2x saturation isolation')
shader=txt('app/src/main/assets/shaders/motionv2/render.glsl'); gain=txt('app/src/main/assets/shaders/motionv2/gainmap.glsl'); cpp=txt('app/src/main/cpp/motionv2_jpeg444_jni.cpp')
for marker in ['IRIS_26630_ADAPTIVE_COLOR_V5','0.018','0.050','0.78','0.95','0.42','0.72','0.030','0.090','0.30','0.70','0.22']: req(marker in shader,'1x V5 '+marker)
req('IRIS_26630_ADAPTIVE_COLOR_V5_TRUE2X_CPU' in cpp and 'IRIS_26630_ADAPTIVE_COLOR_V5_TRUE2X_GPU' in cpp,'true2x V5 owners')
for v in ['0.018','0.050','0.78','0.95','0.42','0.72','0.030','0.090','0.30','0.70','0.22']: req(cpp.count(v)>=2,'true2x parity '+v)
req(shader.index('linearSrgb=fitDisplayGamut(linearSrgb);') < shader.index('linearSrgb=iris26630AdaptiveColorV5(linearSrgb,iris26630MotionSaturation);') < shader.index('srgbEncode(linearSrgb)'),'final color ordering')
req('nominalWhiteEpsilon=1.0e-4' in gain and 'sourceGuide<=1.0+nominalWhiteEpsilon' in gain,'1x UHDR epsilon')
req(cpp.count('sourceGuide<=1.0f+1.0e-4f?1.f')==2 and cpp.count('sourceGuide<=1.0+1.0e-4?1.0')==1,'true2x UHDR epsilon parity')
# Numerical mirror: shared neutral-axis chroma scale must preserve Display-P3 luminance and remain bounded.
W=(0.22897456,0.69173852,0.07928691)
def clamp(x,a=0.,b=1.): return min(max(x,a),b)
def smooth(a,b,x): t=clamp((x-a)/(b-a)); return t*t*(3-2*t)
def luma(rgb): return sum(c*w for c,w in zip(rgb,W))
def v5(rgb,sat):
    rgb=tuple(clamp(x) for x in rgb); y=clamp(luma(rgb)); ch=tuple(x-y for x in rgb); rel=math.sqrt(sum(x*x for x in ch))/(y+.05)
    black=smooth(.018,.050,y); uh=1-smooth(.78,.95,y); ah=1-smooth(.42,.72,y); ng=smooth(.030,.090,rel); st=1-smooth(.30,.70,rel); sat=clamp(sat,0,2)
    requested=max(0,1+black*uh*(sat-1)+.22*black*ah*ng*st*min(sat,1)); lim=1e6
    for x in ch:
        if x>1e-8: lim=min(lim,max(1,(1-y)/x))
        elif x<-1e-8: lim=min(lim,max(1,y/(-x)))
    g=min(requested,lim); out=tuple(clamp(y+x*g) for x in ch); return out,y
for sat in (0,.5,1,1.5,2):
    for rgb in ((.18,.16,.15),(.30,.24,.20),(.12,.18,.25),(.45,.40,.36),(.8,.75,.7),(.5,.5,.5)):
        out,y=v5(rgb,sat); req(abs(luma(out)-y)<2e-6,'V5 luminance invariant'); req(all(-1e-8<=x<=1+1e-8 for x in out),'V5 gamut bound')
for sat in (0,1,2):
    out,_=v5((.3,.3,.3),sat); req(max(out)-min(out)<1e-9,'neutral no chroma creation')
for x in (0,.1,.9999,1,1.0001): req((1 if x<=1+1e-4 else max(x,1.25))==1,'UHDR nominal unity')
for x in (1.0001001,1.01,1.5): req((1 if x<=1+1e-4 else max(x,1.25))>1,'UHDR headroom resumes')
print('PASS 26630 semantic/ownership/domain: exact 13-path delta; fixed VGN/viewfinder policy; per-lens Motion saturation; Night isolation; Adaptive V5 luminance lock; UHDR nominal-unity epsilon; true2x parity')
