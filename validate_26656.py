#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26656.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(root,r): return (root/r).read_text()
def req(c,m):
 if not c: raise SystemExit('FAIL '+m)
bh,ch=H(base),H(cand); req(len(bh)==1721 and len(ch)==1726,'app count')
allow=set(Path(__file__).with_name('R1_26656_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())-{''}
added=set(Path(__file__).with_name('R1_26656_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines())-{''}
actual={r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r)}
req(len(allow)==11 and len(added)==5 and actual==allow,'exact 11-path allowlist')
req(all(r not in bh and r in ch for r in added),'five additions not base-absent')
# Exact capture/reconstruction/color/denoise/DNG owners remain outside scope.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java']
for r in protected: req(bh.get(r)==ch.get(r),'protected owner changed '+r)
# Motion graph: Photon exposure pre-color, Iris color, then Photon presentation. Night remains inherited 26655.
post=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
night=post[post.index('if(mParameters.irisNightActive){'):post.index('/* IRIS_26534_MOTION_RCD_DETOUR_FORBIDDEN */')]
req('new MotionV2PhotonHighlightCompression()' not in night,'Photon New leaked into Night')
for t in ['new MotionV2ColorTransform()','new MotionV2ViewfinderExposureMatcher()','new MotionV2DisplayExposure()','new MotionV2Render()']:
 req(t in night,'Night inherited stage missing '+t)
mstart=post.index('/* IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH */')
mend=post.index('        add(new Bayer2Float());',mstart)
motion=post[mstart:mend]
order=['add(new MotionV2PhotonHighlightCompression());','add(new MotionV2ColorTransform());','add(new MotionV2Render());']
pos=-1
for t in order:
 p=motion.find(t,pos+1); req(p>pos,'Motion owner order '+t); pos=p
for bad in ['add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2DisplayExposure());','add(new IrisMotionToneControls())']:
 req(bad not in motion[:motion.index('add(new MotionV2Render());')],'stale Motion tone owner '+bad)
for t in ['IRIS_26656_PHOTON_NEW_POST_CAPTURE_AUTHORITY','IRIS_26656_PHOTON_NEW_PRESENTATION_BOUNDARY','MotionV2Render[26656-PHOTON-NEW+8LEVEL-LOCAL-LAPLACIAN]']:
 req(t in motion,'Motion graph marker '+t)
# AutoExposureCurve bridge uses pre-color Sabre camera RGB and frozen Wronski S/O, not Photon NoiseModeler.
hc=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java')
for t in ['IRIS_26656_PHOTON_NEW_EXPOSURE_AUTHORITY','HIST_SIZE = 256','TARGET = 128.0f','NOISE_MAX = 0.05f','WHITE_APPLY = 0.8f','FILL_COEFFICIENT = 0.99f','APPLY_GAMMA_MIX = 0.05f','KNEE_MAX = 0.90f','KNEE_MIN = 0.55f','KNEE_REF = 0.10f','motionV2WronskiNoiseS','motionV2WronskiNoiseO','histogram.exposure[0] = 1.0f','motionv2/photon_new_precolor']:
 req(t in hc,'Photon AutoExposureCurve contract '+t)
hc_code=re.sub(r'/\*.*?\*/',' ',hc,flags=re.S); hc_code=re.sub(r'//.*',' ',hc_code)
req('NoiseModeler' not in hc_code,'Photon NoiseModeler revived')
pre=txt(cand,'app/src/main/assets/shaders/motionv2/photon_new_precolor.glsl')
for t in ['cameraRgb/max(neutralPoint,vec3(1.0e-6))','float scalar=mapped/(br+1.0e-3);','Output=(cameraRgb/aw)*scalar;']:
 req(t in pre,'pre-color exposure scalar contract '+t)
# ModernInitial local-white behavior is luminance/common-axis only, then exact 8-level Photon LocalLaplacian.
prep=txt(cand,'app/src/main/assets/shaders/motionv2/photon_new_prepare.glsl')
for t in ['textureBicubicHardware','float gainsVal=max(dot(gainRgb,vec3(1.0/3.0)),1.0);','reinhardExtended','rgb*=ty/y;','gammaEncode0','irisSaturate']:
 req(t in prep,'Photon ModernInitial bridge '+t)
render=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for t in ['IRIS_26656_PHOTON_NEW_PRESENTATION','final int maxLevels = 8','glProg.setVar("sigma", 0.5f);','glProg.setVar("shadows", 0.0f);','glProg.setVar("highlights", 0.0f);','glProg.setVar("clarity", 0.25f);','motionv2/photon_new_prepare','local_laplacian/downsample','local_laplacian/reconstruct','iris26656RunPhotonNewMotion']:
 req(t in render,'Photon New presentation contract '+t)
# Motion must return from the new owner before inherited 26655 B+R is reachable.
runpos=render.find('iris26656RunPhotonNewMotion')
req(runpos>=0,'Photon New run method missing')
req('old26655BPlusR=false' in render,'old 26655 owner not explicitly neutralized')
# Shared final SDR tone transport is rewritten only from completed Photon output for SR.
for t in ['p.motionV2LocalToneLogMap = null;','if (!p.motionV2SuperResOutputEnabled) return;','glProg.useAssetProgram("motionv2/photon_new_log_luma");','p.motionV2LocalToneLogMap = map;','superResSharedToneMap=']:
 req(t in render,'SR shared Photon tone contract '+t)
native=txt(cand,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
for t in ['IRIS_26656_PHOTON_NEW_TRUE2X','IRIS_26656_PHOTON_NEW_TRUE2X_GPU','localToneLogMap','uLocalToneLogMap','encodedY','iris26656Decode(encodedOut)']:
 req(t in native,'true2x Photon tone contract '+t)
# UHDR SDR denominator must be the actual Photon-New rendered SDR; HDR numerator remains pre-tone Iris linear P3.
gain=txt(cand,'app/src/main/assets/shaders/motionv2/gainmap.glsl')
for t in ['uniform int iris26656PhotonNewMotion;','IRIS_26656_PHOTON_NEW_UHDR','iris26656PhotonNewMotion!=0','srgbDecode']:
 req(t in gain,'UHDR Photon-New contract '+t)
for t in ['sdrDenominator=actualPhotonNewRenderedSdr','hdrNumerator=prePhotonToneIrisLinearP3']:
 req(t in render,'UHDR ownership log '+t)
# Exact uploaded Photon LocalLaplacian asset bytes are pinned.
exp={'app/src/main/assets/shaders/local_laplacian/downsample.glsl':'5760a18c5c4eabfa82f610f71972586ff0edf5f5e0e077c7e337282bc55b93a2','app/src/main/assets/shaders/local_laplacian/reconstruct.glsl':'e7408acbbce750ac4838867bfe65c625fa2e83260575efba89a2609e37e6916c'}
for r,h in exp.items(): req(hashlib.sha256((cand/r).read_bytes()).hexdigest()==h,'Photon APK Laplacian byte mismatch '+r)
ver=txt(cand,'app/version.properties'); req('VERSION_NAME=0.9726656' in ver and 'VERSION_BUILD=26656' in ver,'version')
# No capture-policy path is in the allowlist.
for r in allow:
 req('/capture/' not in r and 'CaptureController' not in r,'capture policy entered allowlist '+r)
print('PASS 26656 semantic/ownership: capture/Sabre/color/DNG protected; Motion=Photon AutoExposureCurve pre-color -> Iris color -> Photon ModernInitial luminance bridge + exact 8-level LocalLaplacian; Night inherited; SR shared Photon tone; UHDR Photon SDR denominator; old 26655 Motion tone owners bypassed')
