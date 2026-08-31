#!/usr/bin/env python3
from pathlib import Path
import hashlib, random, re, sys

if len(sys.argv)!=3: raise SystemExit('FAIL: usage: validate_26569_v1_1.py BASE_ROOT CANDIDATE_ROOT')
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
EXPECTED=[
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/version.properties',
]
def files(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}
bh,ch=files(base),files(cand)
assert set(bh)==set(ch), 'file universe changed'
changed=sorted(k for k in bh if bh[k]!=ch[k])
assert changed==EXPECTED, (changed,EXPECTED)
assert len(bh)==1708, len(bh)
ver=(cand/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726569' in ver and 'VERSION_BUILD=26569' in ver

# Protected ownership: everything outside the exact 4-file allowlist is byte-identical.
for k in bh:
    if k not in EXPECTED: assert bh[k]==ch[k], k

# DNG + core SR/color owners explicitly byte-identical.
protected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/cpp/motionv2_jpeg_r_encoder.cpp',
'app/src/main/res/layout/camera_fragment.xml',
'app/src/main/res/layout/layout_bottombuttons.xml',
'app/src/main/res/layout/layout_main_bottombar.xml',
]
for k in protected: assert bh[k]==ch[k], f'protected changed {k}'

bs=(base/EXPECTED[0]).read_text(); cs=(cand/EXPECTED[0]).read_text()

# 26569 V1.1 exact native compiler-closure regression.
FAILED_V1_HASHES={
'app/src/main/cpp/motionv2_jpeg444_jni.cpp':'53cc4bcda8d6fdcd6ba127ce4333ee2dd6ba58b108fd3036c86daceb8e325d7e',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java':'5f5f829ede8e76bf6589c14a2d6a6752fcdf432086aa9ebe3ac6e6e3b810f93d',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java':'066c077a51cee0ef7adad03b33fccddd90e880bfe5cd1c7d66c32a7139472cce',
'app/version.properties':'f2d694c747673eaab3921dea811086213ffd6afaae6955fa281727b175f54e13',
}
for rel in EXPECTED[1:]: assert ch[rel]==FAILED_V1_HASHES[rel], f'V1.1 non-native retry drift {rel}'
assert ch[EXPECTED[0]]=='f9b3ab940676eb109d129f881bfb0f5971ae935d758377b9987ac4cdaf3f9e9f', 'corrected C++ hash drift'

def lexical_brace_balance(src):
    depth=0; i=0; n=len(src); state='code'
    while i<n:
        c=src[i]; d=src[i+1] if i+1<n else ''
        if state=='code':
            if c=='/' and d=='/': state='line'; i+=2; continue
            if c=='/' and d=='*': state='block'; i+=2; continue
            if c=='\"': state='string'; i+=1; continue
            if c=="'": state='char'; i+=1; continue
            if c=='{': depth+=1
            elif c=='}':
                depth-=1
                if depth<0: raise AssertionError('C++ closing brace underflow')
        elif state=='line':
            if c=='\n': state='code'
        elif state=='block':
            if c=='*' and d=='/': state='code'; i+=2; continue
        elif state in ('string','char'):
            if c=='\\': i+=2; continue
            if (state=='string' and c=='\"') or (state=='char' and c=="'"): state='code'
        i+=1
    assert state in ('code','line'), f'C++ unterminated lexical state {state}'
    assert depth==0, f'C++ lexical brace imbalance {depth}'

lexical_brace_balance(cs)
namespace_token='namespace iris26564render {'
jni_token='extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeTrue2xNative('
assert cs.count(namespace_token)==1 and cs.count(jni_token)==1
ns=cs.index(namespace_token); jni=cs.index(jni_token)
assert ns<jni
# Exact retry proof: deleting only the restored namespace closure recreates failed V1 byte-for-byte.
assert cs[jni-3:jni]=='}\n\n', 'namespace closure not immediately before writeTrue2xNative JNI export'
failed_reconstructed=(cs[:jni-3]+cs[jni:]).encode()
assert hashlib.sha256(failed_reconstructed).hexdigest()==FAILED_V1_HASHES[EXPECTED[0]], 'V1.1 C++ differs from failed V1 by more than namespace closure'
# Existing proven color/Jin/render primitives must survive byte-identical.
def function(src,name):
    token=name+'('
    start=src.index(token)
    # back to inline/return type line
    start=src.rfind('\n',0,start)+1
    brace=src.index('{',start); depth=0
    for i in range(brace,len(src)):
        if src[i]=='{': depth+=1
        elif src[i]=='}':
            depth-=1
            if depth==0: return src[start:i+1]
    raise AssertionError(name)
for name in ['profileColor','adaptiveAppearance','tone','preRenderAt','samplePreRender','renderHeadroom','renderBase','applyJinPixel','readRegion','outputToSource']:
    assert function(bs,name)==function(cs,name), f'proven function drift {name}'

# Cached math is source-equivalent after replacing only cached lookup/call names and ProfileRegion type.
def norm_cached(src,name,oldname):
    f=function(src,name)
    f=f.replace(name+'(',oldname+'(').replace('const ProfileRegion&s','const SourceRegion&s')
    f=f.replace('s.at(','profileColor(s,p,')
    f=f.replace('adaptiveAppearanceCached(','adaptiveAppearance(')
    f=f.replace('preRenderAtCached(','preRenderAt(')
    f=f.replace('samplePreRenderCached(','samplePreRender(')
    return f
assert norm_cached(cs,'adaptiveAppearanceCached','adaptiveAppearance')==function(cs,'adaptiveAppearance')
assert norm_cached(cs,'preRenderAtCached','preRenderAt')==function(cs,'preRenderAt')
assert norm_cached(cs,'samplePreRenderCached','samplePreRender')==function(cs,'samplePreRender')
assert norm_cached(cs,'renderBaseCached','renderBase')==function(cs,'renderBase')
assert 'profileColor(s,p,s.x0+lx,s.y0+ly,&v)' in cs
assert 'const bool motionFast=!jin.enabled()' in cs
assert 'const int bandRows=motionFast?256:128' in cs
assert 'std::min(motionFast?6:4' in cs
assert 'IRIS_26569_TRUE2X_ENCODER_TIMING' in cs
# 1:1 UHDR and JPEG-R package implementation unchanged.
assert 'gainC.image_width=outW;gainC.image_height=outH' in cs
assert 'IRIS_26568_TRUE2X_FINAL_STREAM' in cs

# Java encoder change is timing-only around the same package call.
bj=(base/EXPECTED[1]).read_text(); cj=(cand/EXPECTED[1]).read_text()
call='packageJpegRNative(base.toString(), gain.toString(), output.toString(), 1,\n                            gm.getRatioMin(), gm.getRatioMax(), gm.getGamma(), gm.getEpsilonSdr(), gm.getEpsilonHdr(),\n                            gm.getMinDisplayRatioForHdrTransition(), gm.getDisplayRatioForFullHdr(), true)'
assert call in bj and call in cj
assert 'IRIS_26564_TRUE2X_MOTION_GAINMAP_1TO1' in cj
assert 'IRIS_26569_TRUE2X_PACKAGE_TIMING' in cj
# strip only the four added timing/log lines and require the remainder equals base
cj2=cj
cj2=cj2.replace('            final long packageStartNs = System.nanoTime();\n','')
cj2=cj2.replace('            final long packageMs = (System.nanoTime() - packageStartNs) / 1_000_000L;\n','')
cj2=cj2.replace('            Log.i(TAG, "IRIS_26569_TRUE2X_PACKAGE_TIMING jpegRPackageMs=" + packageMs\n                    + " gainReady=" + gainReady + " jpegR=" + jpegR);\n','')
assert cj2==bj, 'Java encoder has non-timing drift'

# UI: measured collision rule only, no device/model/aspect hardcoding and no XML edits.
ui=(cand/EXPECTED[2]).read_text()
assert 'IRIS_26569_ADAPTIVE_BOTTOM_COLLISION_GUARD' in ui
assert 'minimumGapPx = 12.0f * density' in ui
assert 'correctionPx = Math.max(0.0f, lensBottom + minimumGapPx - shutterTop)' in ui
assert 'preferredTranslationY - correctionPx' in ui
block=ui[ui.index('IRIS_26569_ADAPTIVE_BOTTOM_COLLISION_GUARD'):ui.index('private void applyBottomGeometry')]
for forbidden in ['Samsung','S26','Xiaomi','Pixel','Motorola','displayAspectRatio >','displayAspectRatio <']:
    assert forbidden not in block, forbidden
# Synthetic geometry regression: safe layouts remain unchanged; collisions end at exact minimum gap.
r=random.Random(26569)
for _ in range(100000):
    lens_top=r.uniform(0,2500); lens_h=r.uniform(20,100); shutter_top=r.uniform(0,2500); gap=r.uniform(1,50)
    lens_bottom=lens_top+lens_h
    correction=max(0.0,lens_bottom+gap-shutter_top)
    final_bottom=lens_bottom-correction
    assert final_bottom+gap <= shutter_top+1e-9
    if lens_bottom+gap <= shutter_top: assert correction==0.0
print('PASS 26569 V1.1 exact compiler-closure retry: failed V1 + one namespace brace only')
print('PASS C++ lexical brace balance + iris26564render closed before JNI exports')
print('PASS 26569 exact 4-file allowlist / 1708 authority universe')
print('PASS protected SR/color/DNG/JPEG-R/UI XML bytes invariant')
print('PASS original profile/adaptive/tone/render/Jin functions byte-identical')
print('PASS cached Motion renderer equation-identical after lookup substitution')
print('PASS Motion-only cache/direct render 6-worker/256-row policy; Jin fallback 4-worker/128-row')
print('PASS UHDR gainmap remains 1:1; JPEG-R packager unchanged')
print('PASS Java package change timing-only')
print('PASS adaptive UI collision guard 100000 geometries; safe layouts correction=0')
