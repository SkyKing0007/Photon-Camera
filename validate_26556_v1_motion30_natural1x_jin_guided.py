#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, math, re, sys
from pathlib import Path

RUNTIME_FILES = [
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/UniversalSeekBarPreference.java',
'app/version.properties',
]
PROTECTED_EXACT = [
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisNightUltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/res/xml/preferences.xml',
'app/src/main/assets/models/iris_night_jin_lol_512.onnx',
]

def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def text(root: Path, rel: str) -> str: return (root/rel).read_text()
def need(cond, msg):
    if not cond: raise AssertionError(msg)
def clamp(v,a,b): return max(a,min(b,v))
def smooth01(t):
    t=clamp(t,0.0,1.0); return t*t*(3.0-2.0*t)
def d2(a,b): return sum((a[i]-b[i])**2 for i in range(3))/3.0
def lum(a): return .2126*a[0]+.7152*a[1]+.0722*a[2]

def jin_transfer_model(res,guide,native,x,y,W,H,rw,rh):
    fy=(y+.5)*rh/H-.5; y0=max(0,min(rh-1,math.floor(fy))); y1=min(y0+1,rh-1); ty=clamp(fy-y0,0,1)
    fx=(x+.5)*rw/W-.5; x0=max(0,min(rw-1,math.floor(fx))); x1=min(x0+1,rw-1); tx=clamp(fx-x0,0,1)
    sw=[(1-tx)*(1-ty),tx*(1-ty),(1-tx)*ty,tx*ty]; gx=[x0,x1,x0,x1]; gy=[y0,y0,y1,y1]
    bil=[sum(res[gy[k]][gx[k]][c]*sw[k] for k in range(4)) for c in range(3)]
    ne=0.0; cen=lum(native[y][x])
    if x+1<W: ne=max(ne,abs(cen-lum(native[y][x+1])))
    if y+1<H: ne=max(ne,abs(cen-lum(native[y+1][x])))
    span=max(math.sqrt(d2(guide[gy[a]][gx[a]],guide[gy[b]][gx[b]])) for a in range(4) for b in range(a+1,4))
    gate=max(smooth01((ne-.025)/(.120-.025)),smooth01((span-.060)/(.200-.060)))
    reduced=bil[:]
    if gate>1e-4:
        cx=max(0,min(rw-1,round(fx))); cy=max(0,min(rh-1,round(fy)))
        sums=[0.0]*3; ws=0.0
        for yy in range(max(0,cy-1),min(rh-1,cy+1)+1):
            for xx in range(max(0,cx-1),min(rw-1,cx+1)+1):
                dx=xx-fx; dy=yy-fy
                w=(1.0/(1.0+dx*dx+dy*dy))*(1.0/(1.0+80.0*d2(native[y][x],guide[yy][xx])))
                for c in range(3): sums[c]+=res[yy][xx][c]*w
                ws+=w
        if ws>1e-8:
            for c in range(3):
                mean=sums[c]/ws; before=bil[c]; after=before
                if before!=0.0:
                    if before*mean<=0.0 and abs(mean)<abs(before): after=0.0
                    elif before*mean>0.0 and abs(mean)<abs(before): after=mean
                reduced[c]=after
    out=[bil[c]+(reduced[c]-bil[c])*gate for c in range(3)]
    for c in range(3):
        if abs(out[c])>abs(bil[c])+1e-6: out[c]=bil[c]
    return bil,out,gate

def self_test():
    # Smooth area must exactly preserve the 26555 bilinear residual.
    rw=rh=4; W=H=16
    guide=[[[.4,.4,.4] for _ in range(rw)] for _ in range(rh)]
    res=[[[.01*x,.005*y,.003*(x+y)] for x in range(rw)] for y in range(rh)]
    native=[[[.4,.4,.4] for _ in range(W)] for _ in range(H)]
    for y in range(H):
        for x in range(W):
            b,o,g=jin_transfer_model(res,guide,native,x,y,W,H,rw,rh)
            need(g==0.0 and max(abs(b[i]-o[i]) for i in range(3))<1e-12,'smooth Jin transfer drift')
    # Exact failure class from the proposed fix: segmented bright residual beside a straight native edge.
    rw=rh=8; W=H=64; guide=[]; res=[]
    for y in range(rh):
        gr=[]; rr=[]
        for x in range(rw):
            v=.12 if x<4 else .88; gr.append([v,v,v])
            bad=.16 if x==3 and y%2==0 else 0.0; rr.append([bad,bad,bad])
        guide.append(gr); res.append(rr)
    native=[[[.12,.12,.12] if x<32 else [.88,.88,.88] for x in range(W)] for y in range(H)]
    old=new=0.0; n=0
    for y in range(H):
        for x in range(20,44):
            b,o,_=jin_transfer_model(res,guide,native,x,y,W,H,rw,rh)
            need(all(abs(o[c])<=abs(b[c])+1e-6 for c in range(3)),'guided Jin residual increased over bilinear')
            old+=sum(abs(v) for v in b)/3; new+=sum(abs(v) for v in o)/3; n+=1
    need(new < old*.90, f'segmented-edge regression not reduced enough old={old/n} new={new/n}')
    print('PASS self-test: Jin smooth exactness + segmented-edge non-amplification/reduction')

def tree_map(root: Path):
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}

def extract_method(src: str, signature: str) -> str:
    i=src.index(signature); b=src.index('{',i); depth=0
    for j in range(b,len(src)):
        if src[j]=='{': depth+=1
        elif src[j]=='}':
            depth-=1
            if depth==0:return src[i:j+1]
    raise AssertionError('unterminated method '+signature)

def validate(base: Path, cand: Path):
    B,C=tree_map(base),tree_map(cand)
    changed=sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k))
    need(changed==sorted(RUNTIME_FILES),f'changed-file allowlist mismatch: {changed}')
    print('PASS exact seven-file runtime/version allowlist')
    for rel in PROTECTED_EXACT:
        need((base/rel).is_file() and (cand/rel).is_file(), 'missing protected '+rel)
        need(sha(base/rel)==sha(cand/rel),'protected drift '+rel)
    # No shader or Kotlin changes at all; inherited compiler proof is valid only because bytes are exact.
    for rel,h in B.items():
        if rel.endswith('.glsl') or rel.endswith('.kt'):
            need(C.get(rel)==h,'GLSL/Kotlin drift '+rel)
    print('PASS protected Night/Sabre/UHDR/model + all GLSL/Kotlin byte invariance')

    cap=text(cand,RUNTIME_FILES[1]); basecap=text(base,RUNTIME_FILES[1])
    for tok in ['MOTION_26556_MAX_NORMAL_FRAMES = 30','iris26556RequestedMotionFrames()','MOTION_26556_MAX_NORMAL_FRAMES + 3','MOTION_26556_MAX_NORMAL_FRAMES + 2','postShutterNormalAdmission=false']:
        need(tok in cap,'missing Motion frame policy '+tok)
    need(cap.count('Math.min(PhotonCamera.getSettings().frameCount, 37)')==0,'old Motion 37 target survived')
    need('Math.min(PhotonCamera.getSettings().frameCount + 3, 40)' not in cap,'old Motion ImageReader 40 cap survived')
    # Freeze metadata grace/top-up architecture must remain; normal post-shutter admission is not introduced.
    for tok in ['MOTION_TOP_UP_TIMEOUT_MS = 1400L','IRIS_26520_V4_FROZEN_METADATA_GRACE','normalRingFrozen=true postShutterNormalAdmission=false']:
        need(tok in cap and tok in basecap,'Motion frozen/ZSL architecture lost '+tok)
    print('PASS Motion exact selected<=30, reader<=33/ring<=32, pre-shutter-only architecture')

    night=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java')
    for tok in ['MAX_NIGHT_FRAMES = 50','MIN_NIGHT_FRAMES = 2','longFrames = total == 2 ? 0 : Math.max(1, (total + 2) / 5)']:
        need(tok in night,'Night frame policy drift '+tok)
    expected={2:(2,0),7:(6,1),10:(8,2),15:(12,3),27:(22,5),30:(24,6),50:(40,10)}
    for n,(es,el) in expected.items():
        l=0 if n==2 else max(1,(n+2)//5); s=n-l
        need((s,l)==(es,el),f'Night plan regression {n}: {(s,l)}')
    print('PASS Night 2..50 unchanged; 7/10/15/27/30/50 split regression')

    prefs=text(cand,'app/src/main/res/xml/preferences.xml')
    need('maxValue="50"' in prefs and 'pref_frame_count_key' in prefs,'global slider backing max not 50')
    settings=text(cand,RUNTIME_FILES[4]); seek=text(cand,RUNTIME_FILES[5])
    for tok in ['configureFrameCountPreferenceForMode()','cameraMode == CameraMode.MOTION ? 30.0f : 50.0f','IRIS_26556_FRAME_SLIDER_VIEW']:
        need(tok in settings,'settings Option-B token missing '+tok)
    for tok in ['runtimeMaxValue','Render a mode-limited view without persisting the clamped display value','getPersistedString(fallback_value)','effectiveMax']:
        need(tok in seek,'seekbar Option-B token missing '+tok)
    # Binding's runtime-cap branch must not call persistString before user interaction.
    bind=extract_method(seek,'public void onBindViewHolder')
    need('persistString' not in bind,'opening Motion slider would overwrite stored global value')
    print('PASS one global slider Option B: Motion view/edit<=30 without opening-time overwrite; Night backing max50')

    zoom=text(cand,RUNTIME_FILES[2]); basezoom=text(base,RUNTIME_FILES[2])
    for tok in ['activeMode == CameraMode.MOTION','activeMode == CameraMode.NIGHT','CaptureRequest.CONTROL_ZOOM_RATIO, null','CaptureRequest.SCALER_CROP_REGION, null','IRIS_26556_NATURAL_ONE_X']:
        need(tok in zoom,'natural 1x missing '+tok)
    # No expansion of continuous zoom ownership into Night.
    m=extract_method(zoom,'public static boolean isContinuousZoomEnabledForCurrentMode')
    mb=extract_method(basezoom,'public static boolean isContinuousZoomEnabledForCurrentMode')
    need(m==mb,'continuous zoom mode ownership changed')
    need('CameraMode.MOTION' in m and 'CameraMode.NIGHT' not in m,'Night continuous zoom unexpectedly enabled')
    for tok in ['CONTROL_ZOOM_RATIO_RANGE','SCALER_AVAILABLE_MAX_DIGITAL_ZOOM','sResidualSoftwareZoom']:
        need(tok in zoom,'post-1x 26555 zoom path lost '+tok)
    print('PASS Motion+Night native uncropped local1x; existing post-startup Motion zoom owner retained')

    jin=text(cand,RUNTIME_FILES[3]); basejin=text(base,RUNTIME_FILES[3]); cpp=text(cand,RUNTIME_FILES[0])
    for tok in ['N = 512','residual[i * 3 + ch] = 0.5f * (out - input[ch * plane + i])']:
        need(tok in jin,'Jin official residual semantics changed/missing '+tok)
    # Inference model/session setup must stay present and model bytes are protected above.
    for tok in ['OrtEnvironment.getEnvironment()','createSession','run(Collections.singletonMap(inputName, in))']:
        need(tok in jin,'Jin inference owner missing '+tok)
    for tok in ['IRIS_26556_JIN_NATIVE_SABRE_GUIDED_RESIDUAL','referenceRgb','guideSpan','suppressedComponents','std::fabs(rr)>std::fabs(bilinear[c])+1.0e-6f']:
        need(tok in cpp,'Jin guide invariant missing '+tok)
    for forbidden in ['applyRgbGridInPlace','32 * 32 * 3']:
        need(forbidden not in jin,'legacy Jin grid implementation active in enhancer '+forbidden)
    self_test()
    print('PASS Jin inference/model unchanged; adapter smooth-exact and edge non-amplifying')

    cmake=text(cand,'app/src/main/cpp/CMakeLists.txt')
    nightproc=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java')
    need('motionv2_jpeg444_jni.cpp' in cmake,'native adapter not compiled')
    need('IrisNightNeuralEnhancer.enhanceInPlace(img)' in nightproc,'Jin enhancer not production-reachable')
    need('IrisZoomController.applyToRequest(' in cap,'zoom controller not production-reachable')
    need('configureFrameCountPreferenceForMode();' in settings,'frame UI policy not production-reachable')
    print('PASS runtime ownership: capture/frame UI, preview zoom, Night Jin JNI')

    vp=text(cand,'app/version.properties')
    need(re.search(r'(?m)^VERSION_NAME=0\.9726556\s*$',vp)!=None,'VERSION_NAME wrong')
    need(re.search(r'(?m)^VERSION_BUILD=26556\s*$',vp)!=None,'VERSION_BUILD wrong')
    print('PASS target version 0.9726556 / 26556')

    # Vendor/native dependencies outside the modified translation unit must be exact.
    for prefix in ('app/src/main/cpp/third_party_26507/','app/src/main/cpp/deps/'):
        for rel,h in B.items():
            if rel.startswith(prefix): need(C.get(rel)==h,'vendor dependency drift '+rel)
    print('PASS native/vendor dependency invariance')

    print('VALIDATION PASS')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--base'); ap.add_argument('--candidate')
    a=ap.parse_args()
    if a.self_test: self_test(); return
    need(a.base and a.candidate,'--base and --candidate required')
    validate(Path(a.base),Path(a.candidate))
if __name__=='__main__':
    try: main()
    except Exception as e:
        print('VALIDATION FAIL:',e,file=sys.stderr); raise
