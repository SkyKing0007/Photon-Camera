#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[x for x in '''app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java
app/version.properties'''.splitlines() if x]
def fail(x):raise SystemExit('FAIL: '+x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(r):return {p.relative_to(r).as_posix():sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def section(s,a,b):
 if a not in s or b not in s:fail('section anchors '+a+' / '+b)
 return s[s.index(a):s.index(b,s.index(a)+len(a))]
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);a,d=amap(b),amap(c)
 if len(a)!=1708 or len(d)!=1708:fail(f'universe {len(a)}/{len(d)}')
 diff=sorted(k for k in set(a)|set(d) if a.get(k)!=d.get(k))
 if diff!=sorted(CHANGED):fail('allowlist '+repr(diff))
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726592','version');need(v,'VERSION_BUILD=26592','version')
 for r,h in a.items():
  if r not in CHANGED and d.get(r)!=h:fail('protected owner '+r)
 # Explicitly freeze capture and body/viewfinder authorities.
 cap='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java';vfpath='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
 if a[cap]!=d[cap]:fail('capture exposure policy changed')
 if a[vfpath]!=d[vfpath]:fail('viewfinder/body meter changed')
 sabre=(c/CHANGED[2]).read_text();stack=(c/CHANGED[3]).read_text();render=(c/CHANGED[4]).read_text();enc=(c/CHANGED[5]).read_text();uhdr=(c/CHANGED[6]).read_text();glsl=(c/CHANGED[0]).read_text();cpp=(c/CHANGED[1]).read_text()
 # SHORT trust remains same Sabre geometry, but trust no longer owns opacity.
 for t in ['IRIS_26592_TRUST_GATED_RADIOMETRIC_SHORT_HANDOFF','const float handoffStart = 0.90;','const float trustGate = 0.60;','referenceSecondHighestSignal','shortNeighborhoodHasHeadroom','vec2 shortUv = clamp(referenceUv + flow.xy','uShortWeightThreshold','uNormalCoverageThreshold','uFlowVariationThreshold','uUnblockerThreshold','evidence < 3','meanError >= uConsistencyThreshold','if (trustConfidence < trustGate) { oMask = 0.0; return; }','oMask = smoothstep(handoffStart, uReferenceNearClipThreshold, referenceSecond);','IRIS_26592_RGBA16F_WHOLE_RGB_RADIOMETRIC_SHORT_HANDOFF','mix(normalRgb.rgb, restoredShort, confidence)']:
  need(sabre,t,'SHORT handoff')
 if 'oMask = trustConfidence' in sabre:fail('alignment trust reused as blend opacity')
 for t in ['uniform1f(program, "uReferenceNearClipThreshold", 0.98f)','uniform1f(program, "uShortHeadroomThreshold", 0.90f)','GLES30.GL_R8, GLES30.GL_NEAREST','handoffStart=0.90 fullShortAt=0.98 trustGate=0.60 shortHeadroomThreshold=0.90','trustSeparatedFromBlend=true sameSabreFlow=true wholeRgb=true maskFilter=NEAREST','IRIS_26592_SHORT_HANDOFF_EFFECT']:
  need(stack,t,'SHORT stack')
 # Final Motion tail: unbounded coordinate, strictly monotonic asymptotic mapping; Night retains 26591 branch.
 for t in ['IRIS_26592_UNBOUNDED_MONOTONIC_HIGHLIGHT_TAIL','IRIS_26592_TAIL_LOG_SHAPE = 3.0f','IRIS_26592_TANH_SCALE = 1.2020679f','IRIS_26592_MOTION_UHDR_MAX_RATIO = 8.0f','iris26592MapHeadroom','glProg.setVar("iris26592MotionHdrHandoff", basePipeline.mParameters.motionV2Active ? 1 : 0)']:
  need(render,t,'Motion render')
 rsec=section(render,'static float iris26592MapHeadroom','static float iris26582AdaptiveStrength')
 need(rsec,'float u = Math.max(','Motion Java unbounded coordinate');need(rsec,'Math.tanh(IRIS_26592_TANH_SCALE * logCoordinate)','Motion Java tanh tail')
 gsec=section(glsl,'float mapHeadroomLuminance','vec3 mapExtendedLinearHeadroom')
 for t in ['float u=max(','if(iris26592MotionHdrHandoff!=0)','float logCoordinate=log(1.0+logShape*u)/log(1.0+logShape);','shaped=tanh(tanhScale*logCoordinate);','float x=clamp(u,0.0,1.0);']:
  need(gsec,t,'Motion/Night GLSL split')
 # True2x publication uses same Motion map and explicit mode flag; Night keeps prior native path.
 for t in ['bool motionHdrHandoff=false','if(p.motionHdrHandoff){float logCoordinate=std::log(1.f+3.f*u)/std::log(4.f);shaped=std::tanh(1.2020679f*logCoordinate);}','else {float x=clampf(u,0.f,1.f);shaped=std::log(1.f+6.f*x)/std::log(7.f);}','uniform int uMotionHdrHandoff;','if(uMotionHdrHandoff!=0){float logCoordinate=log(1.0+3.0*u)/log(4.0);shaped=tanh(1.2020679*logCoordinate);}','glUniform1i(loc("uMotionHdrHandoff"),params->motionHdrHandoff?1:0)','jboolean motionHdrHandoff']:
  need(cpp,t,'true2x Motion/Night parity')
 for t in ['parameters.motionV2ToneAdaptiveSceneWhite, parameters.motionV2Active','float exposureEv, float shadows, float contrast, float sceneWhite, boolean motionHdrHandoff']:
  need(enc,t,'Java/JNI true2x bridge')
 # Motion gain-map metadata can represent existing -2.5 EV physical SHORT headroom; actual per-pixel quotient still owns gain.
 for t in ['IRIS_26592_MOTION_UHDR_RECOVERED_HEADROOM_RANGE','Math.min(8.0f, maxRatio)','gainmap.setRatioMax(safeMax, safeMax, safeMax)']:
  need(uhdr,t,'UltraHDR range')
 # DNG/SR/Night/capture owners are outside allowlist; this is already enforced byte-for-byte above.
 print('PASS exact successful-26591 authority -> exact eight-file 26592 architectural HDR handoff allowlist')
 print('PASS capture exposure and viewfinder/body meter byte-identical to successful 26591')
 print('PASS SHORT trust separated from radiometric whole-RGB handoff; same Sabre geometry/anti-smear gates and NEAREST mask retained')
 print('PASS Motion 1x + true2x use unbounded log+tanh tail; Night retains prior finite branches; Motion UHDR ratio metadata capacity=8x')
 print('PASS all 1700 non-allowlisted app files byte-identical to successful 26591')
if __name__=='__main__':main()
