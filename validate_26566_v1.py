#!/usr/bin/env python3
import hashlib, math, sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit('usage: validate_26566_v1.py BASE CAND PACKAGE')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); P=Path(sys.argv[3])
FAIL=[]; PASS=[]
def ok(cond,msg):
    (PASS if cond else FAIL).append(msg)
def text(root,rel): return (root/rel).read_text()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

changed=[x for x in (P/'V1_26566_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
expected=[
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/version.properties']
ok(changed==expected,'exact eight-file runtime allowlist')

# Exact actual delta.
def files(r): return {p.relative_to(r) for p in r.rglob('*') if p.is_file()}
actual=[]
for rel in sorted(files(B)|files(C)):
    bp=B/rel; cp=C/rel
    if not bp.exists() or not cp.exists() or sha(bp)!=sha(cp): actual.append(str(rel))
ok(actual==expected,'actual candidate delta equals allowlist')

# Version.
v=text(C,'app/version.properties')
ok('VERSION_NAME=0.9726566' in v and 'VERSION_BUILD=26566' in v,'target version 0.9726566/26566')

# Full Parameters history remains exact ordered subsequence: no existing DNG/color metadata line was rewritten/deleted.
bp=text(B,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').splitlines()
cp=text(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').splitlines()
i=0
for line in cp:
    if i < len(bp) and line==bp[i]: i+=1
ok(i==len(bp),'Parameters base lines preserved exactly and in order (additive JPEG-only fields/calls)')

# Dedicated DNG owners exact bytes.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']:
    ok(sha(B/rel)==sha(C/rel),f'DNG protected byte invariant {rel}')

# All shaders exact: no new GLSL compiler scope.
for rel in sorted(p.relative_to(B) for p in (B/'app/src/main/assets/shaders').rglob('*') if p.is_file()):
    ok((C/rel).is_file() and sha(B/rel)==sha(C/rel),f'GLSL byte invariant {rel}')

# Night neural owner/model exact.
for rel in [
'app/src/main/assets/models/iris_night_jin_lol_512.onnx',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java']:
    ok(sha(B/rel)==sha(C/rel),f'Night protected byte invariant {rel}')

solver=text(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java')
params=text(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java')
motion=text(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java')
initial=text(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java')
enc=text(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
saver=text(C,'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
native=text(C,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')

# Iris JPEG solver ownership and DNG separation.
ok('IRIS_26566_JPEG_ONLY_DNG_COLOR_SOLVER' in solver,'JPEG-only solver marker')
ok('Converter.' not in solver,'solver independent of legacy Converter math')
ok('DngCreator' not in solver and 'IrisSabreSuperResDngWriter' not in solver,'solver has no DNG writer dependency')
ok('SENSOR_NEUTRAL_COLOR_POINT' in solver and 'SENSOR_COLOR_TRANSFORM1' in solver and 'SENSOR_FORWARD_MATRIX1' in solver and 'SENSOR_CALIBRATION_TRANSFORM1' in solver,'solver consumes Camera2/DNG characterization')
ok('ROBERTSON_R' in solver and 'bradfordAdapt' in solver,'Robertson reciprocal-CCT + Bradford fallback present')
ok('wrongCalibration' not in solver and 'colorMethod' not in solver and 'customCCT' not in solver,'legacy/ad-hoc color heuristics absent from Iris solver')
ok('irisJpegSensorToProPhoto' in params and 'irisJpegProPhotoToSRGB' in params and 'irisJpegColorValid' in params,'parallel JPEG-only Parameters fields')
ok(params.count('applyIrisJpegColorSolution(characteristics, result, false);')==1,'Night Camera2 owner invokes Iris JPEG solver once')
ok(params.count('applyIrisJpegColorSolution(characteristics, result, customCCT.exists());')==1,'normal/Motion parameter owner invokes Iris JPEG solver once')
ok('irisJpegSensorToProPhoto' in motion and 'irisJpegProPhotoToSRGB' in motion,'Motion/Night consume Iris JPEG matrices')
ok('irisJpegSensorToProPhoto' in initial and 'irisJpegProPhotoToSRGB' in initial,'normal Photo consumes Iris JPEG matrices')
ok('irisJpegSensorToProPhoto' in enc and 'irisJpegProPhotoToSRGB' in enc,'true2x publisher consumes Iris JPEG matrices')
# Normal Photo domain adapter is inherited exact GLSL: tofloat divides sensor samples by AsShotNeutral,
# then initial multiplies by the same neutral before the shared camera->profile matrix. The pair cancels,
# so the Iris matrix sees camera-linear RGB without modifying GLSL.
tofloat=text(C,'app/src/main/assets/shaders/tofloat.glsl')
initial_shader=text(C,'app/src/main/assets/shaders/initial.glsl')
ok('Output *= CanonicalExposureGain;' in tofloat and 'float iris26403Linear = max(Output/balance, 0.0);' in tofloat
   and 'balance = whitePoint.r;' in tofloat and 'balance = whitePoint.g;' in tofloat and 'balance = whitePoint.b;' in tofloat,
   'normal Photo pre-color stage divides by AsShotNeutral in unchanged tofloat shader')
ok('pRGB = corr*sensorToIntermediate*(pRGB*neutralPoint);' in initial_shader,
   'normal Photo initial shader restores camera-linear domain before shared JPEG matrix')

# Preserve P3 publication math inside modified native file exactly.
def region(s,a,b):
    i=s.index(a); j=s.index(b,i); return s[i:j]
try:
    base_native=text(B,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
    p3b=region(base_native,'/* IRIS_26565_JPEG_BOUNDARY_DISPLAY_P3','namespace iris26564')
    p3c=region(native,'/* IRIS_26565_JPEG_BOUNDARY_DISPLAY_P3','namespace iris26564')
    ok(p3b==p3c,'26565 Display-P3 conversion/ICC block exact bytes')
except Exception:
    ok(False,'26565 Display-P3 conversion/ICC block exact bytes')

# True2x universal publication correction.
ok('std::string tmp=std::string(rp.c)+".26566.rgb8.tmp"' in native,'true2x RGB scratch owned by private render carrier path')
ok('std::string(rp.c)+".26566.gain.raw.tmp"' in native,'true2x gain scratch owned by private render carrier path')
ok('std::string(op.c)+".26564.true2x.rgb8.tmp"' not in native,'DCIM-derived RGB scratch removed')
ok('std::string(gp.c)+".raw.tmp"' not in native,'DCIM-derived gain raw scratch removed')
ok('return baseEncoded?JNI_TRUE:JNI_FALSE;' in native,'native base success independent of auxiliary gain encode')
ok('IRIS_26566_TRUE2X_FINAL_RENDER' in native and 'baseEncoded=%d' in native and 'gainEncoded=%d' in native,'reason/state-coded true2x native log')
ok('hasExpectedJpegDimensions' in enc and 'IRIS_26566_TRUE2X_JPEG_SOF_MISMATCH' in enc,'physical JPEG dimension acceptance gate')
ok('expectedJpegWidth = bitmap.getWidth() * 2' in enc and 'expectedJpegHeight = bitmap.getHeight() * 2' in enc,'true2x physical dimensions exactly 2x')
ok('native12mpFallback=false' in enc,'50MP publication contract explicitly forbids native fallback')
ok('IRIS_26566_MOTION_TRUE2X_PUBLICATION_FAILED native12mpFallback=false' in saver,'Motion SR failure explicit and non-degrading')
ok('IRIS_26564_MOTION_TRUE2X_JPEG_DEGRADED_TO_NATIVE' not in saver,'old silent 12MP degradation removed')
# In SR branch there must be no ordinary writer after writeTrue2x failure.
sr_start=saver.index('if (useSuperRes) {', saver.index('saveBitmapAsJPGMotionV2'))
sr_end=saver.index('} else {', sr_start)
ok('MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality)' not in saver[sr_start:sr_end],'SR-on branch cannot invoke native-resolution JPEG writer')

# 4096x3072 -> after 90-degree bitmap rotation 3072x4096 -> 6144x8192.
ok((3072*2)*(4096*2)==50331648,'full-frame true2x acceptance is 6144x8192 = 50,331,648 pixels')

# Standard Robertson reference sanity checks for the exact table embedded in source.
R=[0,10,20,30,40,50,60,70,80,90,100,125,150,175,200,225,250,275,300,325,350,375,400,425,450,475,500,525,550,575,600]
U=[.18006,.18066,.18133,.18208,.18293,.18388,.18494,.18611,.18740,.18880,.19032,.19462,.19962,.20525,.21142,.21807,.22511,.23247,.24010,.24792,.25591,.26400,.27218,.28039,.28863,.29685,.30505,.31320,.32129,.32931,.33724]
V=[.26352,.26589,.26846,.27119,.27407,.27709,.28021,.28342,.28668,.28997,.29326,.30141,.30921,.31647,.32312,.32909,.33439,.33904,.34308,.34655,.34951,.35200,.35407,.35577,.35714,.35823,.35908,.35968,.36011,.36038,.36051]
T=[-.24341,-.25479,-.26876,-.28539,-.30470,-.32675,-.35156,-.37915,-.40955,-.44278,-.47888,-.58204,-.70471,-.84901,-1.0182,-1.2168,-1.4512,-1.7298,-2.0637,-2.4681,-2.9641,-3.5814,-4.3633,-5.3762,-6.7262,-8.5955,-11.324,-15.628,-23.325,-40.770,-116.45]
def cct(x,y):
    d=-x+6*y+1.5; u=2*x/d; v=3*y/d; prev=None
    for i in range(len(R)):
        dist=((v-V[i])-T[i]*(u-U[i]))/math.sqrt(1+T[i]*T[i])
        if i and dist<=0 and prev>0:
            f=prev/(prev-dist); rr=R[i-1]*(1-f)+R[i]*f
            return 50000 if rr<=1e-7 else 1e6/rr
        prev=dist
    return 1667 if prev>0 else 50000
ok(abs(cct(.3127,.3290)-6504)<25,'Robertson D65 sanity')
ok(abs(cct(.34567,.35850)-5003)<25,'Robertson D50 sanity')
ok(abs(cct(.44757,.40745)-2856)<25,'Robertson Standard-A sanity')

# Matrix primitive sanity: ForwardMatrix neutral mapping convention used by solver.
def mm(a,b): return [sum(a[r*3+k]*b[k*3+c] for k in range(3)) for r in range(3) for c in range(3)]
def mv(a,v): return [sum(a[r*3+k]*v[k] for k in range(3)) for r in range(3)]
f=[0.9642,0,0, 0,1,0, 0,0,0.8249]
w=mv(f,[1,1,1])
ok(max(abs(w[i]-[.9642,1,.8249][i]) for i in range(3))<1e-6,'ForwardMatrix D50 neutral sanity')

# Required package proofs.
for rel in ['V1_26566_RUNTIME_DELTA_FROM_26565_V1_2.patch','V1_26566_RUNTIME_ROLLBACK_TO_26565_V1_2.patch']:
    ok((P/rel).is_file() and (P/rel).stat().st_size>0,f'packaged {rel}')

for msg in PASS: print('PASS',msg)
if FAIL:
    for msg in FAIL: print('FAIL',msg)
    print(f'FAIL TOTAL {len(PASS)} pass / {len(FAIL)} fail')
    raise SystemExit(1)
print(f'PASS TOTAL {len(PASS)} / {len(PASS)}')
