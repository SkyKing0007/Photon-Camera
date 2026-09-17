#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26656_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def same(r):
 a=base/r;b=cand/r
 return a.is_file() and b.is_file() and hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
def req(c,m):
 if not c: raise SystemExit('FAIL '+m)
# Permanent no-regression classes: acquisition, temporal Wronski/Sabre, color/DNG remain 26655 bytes.
for r in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java']:
 req(same(r),'protected 26655 owner changed '+r)
post=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
mstart=post.index('/* IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH */')
mend=post.index('        add(new Bayer2Float());',mstart)
motion=post[mstart:mend]
# Exact failure: double presentation authorities must never return on Motion.
pre_render=motion[:motion.index('add(new MotionV2Render());')]
for bad in ['add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2DisplayExposure());','add(new IrisMotionToneControls())']:
 req(bad not in pre_render,'double Motion presentation returned '+bad)
req(pre_render.index('add(new MotionV2PhotonHighlightCompression());') < pre_render.index('add(new MotionV2ColorTransform());'),'Photon exposure no longer pre-color')
# Exact failure: old 26655 B+R cannot be final Motion authority.
r=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
req('IRIS_26656_PHOTON_NEW_FINAL' in r and 'old26655BPlusR=false old26623Tone=false' in r,'old B+R authority not neutralized')
req('iris26656PublishTrue2xToneMap(WorkingTexture);' in r,'SR tone publication missing')
req(r.index('iris26656PublishTrue2xToneMap(WorkingTexture);') < r.index('iris26656BuildMotionGainMap(extendedLinearHdr, WorkingTexture, irisOutputZoom);'),'SR/UHDR publication order changed')
# Exact failure: SR must not silently use a stale 26655 map.
req('p.motionV2LocalToneLogMap = null;' in r and 'p.motionV2LocalToneLogMap = map;' in r,'SR map clear/rewrite missing')
n=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
req('IRIS_26656_PHOTON_NEW_TRUE2X' in n and 'IRIS_26656_PHOTON_NEW_TRUE2X_GPU' in n,'true2x shared tone missing')
# Exact failure: UHDR base must not use pre-Photon SDR denominator.
g=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
req('iris26656PhotonNewMotion!=0' in g and 'IRIS_26656_PHOTON_NEW_UHDR' in g,'Photon-New UHDR branch missing')
# Exact failure: local-white adjustment must not be per-channel and recreate pink/green/magenta boundaries.
p=(cand/'app/src/main/assets/shaders/motionv2/photon_new_prepare.glsl').read_text()
req('rgb*=ty/y;' in p,'common-axis local white scalar missing')
req('vec3 gainRgb=vec3(gains.r,(gains.g+gains.b)*0.5,gains.a);' in p,'Photon gain-map sampling changed')
# Exact Photon LocalLaplacian bytes must remain frozen.
for rel,h in [('app/src/main/assets/shaders/local_laplacian/downsample.glsl','5760a18c5c4eabfa82f610f71972586ff0edf5f5e0e077c7e337282bc55b93a2'),('app/src/main/assets/shaders/local_laplacian/reconstruct.glsl','e7408acbbce750ac4838867bfe65c625fa2e83260575efba89a2609e37e6916c')]:
 req(hashlib.sha256((cand/rel).read_bytes()).hexdigest()==h,'Photon Laplacian asset drift '+rel)
print('PASS 26656 permanent regressions: no capture/Sabre/color/DNG drift; no double Iris Motion presentation; no 26655 B+R final owner; SR map clear/rewrite + true2x consumer; Photon-New UHDR denominator; common-axis local white; exact Photon Laplacian assets')
