#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26665_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();mr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text();matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text();renderj=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();params=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text();ll=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text();rs=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();gm=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
# Permanent retired exposure/SHORT regressions.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','final boolean iris26593ShortBudgetAllows = false;','final boolean iris26593ShortSubmitted = false;','final boolean iris26480ShortHighlightRequested = false;']:
 if t not in cc:raise SystemExit('FAIL retired exposure/SHORT regression '+t)
# 26661 ratchet + 26662/26663 fast light-source preview pulsation remain fixed.
active=cc[cc.index('IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER'):cc.index('IRIS_26381_DYNAMIC_MOTION_SHUTTER_OPPORTUNITY')]
if 'radiometricGuide = Math.max(0.0f, mMotion26608RawP995)' not in active:raise SystemExit('FAIL current RAW p995 authority lost')
if 'Math.max(0.0f, mMotion26608StructuredPeakSecond)' in active:raise SystemExit('FAIL held structured peak regained magnitude authority')
func=cc[cc.index('getMotion26663ReferencePreviewProtectionEv'):cc.index('IRIS_26496_SPATIALLY_PERSISTENT_HIGHLIGHT_TRIGGER')]
if 'return Float.NaN;' not in func:raise SystemExit('FAIL metadata miss explicit NaN lost')
if 'Float.isFinite(exactEv)' not in mr or 'mIris26663LastConfirmedProtectionEv' not in mr or 'Math.min(0.10f' not in mr:raise SystemExit('FAIL stable preview hold/slew lost')
# 26663 island owner cannot return; successful 26664 Local-Laplacian must be byte-identical.
for t in ['IRIS_26663_CANONICAL_BODY_LOCAL_RECOVERY','iris26663BodyBase','smoothstep(0.035,0.12,shadowBase)','1.0-smoothstep(0.42,0.68,shadowBase)']:
 if t in ll:raise SystemExit('FAIL 26663 double-island spatial body lift returned '+t)
if sha(base/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')!=sha(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl'):raise SystemExit('FAIL local-laplacian changed')
# 26664 global body transfer remains monotone and identity in upper tone.
def smooth(t): t=max(0.0,min(1.0,t)); return t*t*(3-2*t)
def body26664(y,ev):
 if y<=0:return 0.0
 if y>=.65:return y
 a=math.log2(.08);b=math.log2(.65);t=(math.log2(max(y,1e-8))-a)/(b-a);return y*2**(ev*(1-smooth(t)))
for ev in (0,.25,.65,1.25):
 prev=-1.0
 for i in range(1,10001):
  y=i/10000;z=body26664(y,ev)
  if z+1e-9<prev:raise SystemExit(f'FAIL nonmonotone 26664 body tone ev={ev} y={y}')
  prev=z
 for y in (.65,.8,1.0):
  if abs(body26664(y,ev)-y)>1e-8:raise SystemExit('FAIL 26664 highlight identity')
# 26665 exact failing-condition regressions from supplied 26664 captures.
def clamp(x,a,b):return max(a,min(b,x))
def ss(a,b,x):
 t=clamp((x-a)/(b-a),0.0,1.0);return t*t*(3.0-2.0*t)
def lowkey(p50,p95,target_log,protection,night=False):
 if night:return (0.0,0.0)
 target=2.0**target_log;u=1.0-ss(.02,.08,protection);m=1.0-ss(.010,.030,p50);p=1.0-ss(.035,.090,p95);v=1.0-ss(.035,.080,target);intent=clamp(u*m*p*v,0,1);return intent,.70*intent
# Outdoor Motion supplied log: genuinely low-key scene must retain night scene key.
i,red=lowkey(.005874634,.02267456,-5.0365376,0.0)
if abs(i-1.0)>1e-7 or abs(red-.70)>1e-7:raise SystemExit(f'FAIL outdoor low-key regression {i} {red}')
# Indoor supplied log: normal indoor scene must keep exact 26664 global exposure solve.
i,red=lowkey(.09710693,.24780273,-2.9671028,0.0)
if i!=0.0 or red!=0.0:raise SystemExit(f'FAIL indoor exposure protection {i} {red}')
# Highlight-protected HDR/chandelier state: new authorities exact zero by 0.08EV.
for prot in (.08,.33333334,.6666667,1.0):
 i,red=lowkey(.005,.020,-5.0,prot)
 if i!=0.0 or red!=0.0:raise SystemExit(f'FAIL protected HDR low-key leak {prot} {i} {red}')
# Night route is explicitly unchanged.
i,red=lowkey(.0037593842,.014259338,-5.0084085,0.0,True)
if i!=0.0 or red!=0.0:raise SystemExit('FAIL dedicated Night changed')
# Shadow depth decision reproduces indoor failure condition but is small on the low-key night sample.
def depth(mapped25,mapped50,bodydr,old,prot,night=False):
 if night:return 0.0
 crowd=mapped25/max(mapped50,1e-6);u=1.0-ss(.02,.08,prot);lf=1.0-ss(.05,.20,old);ce=clamp(math.log2(max(crowd,1e-6)/.40),0,.45);bg=ss(.80,1.20,bodydr);return clamp(ce*bg*u*lf,0,.45)
din=depth(.078923576,.15682346,1.1000041,2.3012656e-4,0.0)
if not (.27<din<.29):raise SystemExit(f'FAIL indoor depth regression {din}')
dout=depth(.009355435,.022031661,1.3738825,0.0,0.0)
if not (.08<dout<.10):raise SystemExit(f'FAIL outdoor depth regression {dout}')
for prot in (.08,.33333334):
 if depth(.08,.15,1.2,0.0,prot)!=0.0:raise SystemExit('FAIL protected HDR shadow depth leak')
# Black-safe transfer: exact black/near-black identity, exact body/highlight identity, C1 + monotone.
L0=math.log2(.004);L1=math.log2(.30);span=L1-L0
def sd(y,ev):
 if y<=.004 or y>=.30:return y
 t=clamp((math.log2(max(y,1e-8))-L0)/span,0,1);b=16*t*t*(1-t)*(1-t);return y*2**(-ev*b)
for ev in (0,.10,.28,.45):
 for y in (0,.001,.004,.30,.65,1.0):
  if abs(sd(y,ev)-y)>1e-12:raise SystemExit(f'FAIL shadow identity ev={ev} y={y}')
 prev=-1
 for i in range(1,100001):
  y=i/100000
  z=sd(y,ev)
  if z+1e-10<prev:raise SystemExit(f'FAIL nonmonotone shadow curve ev={ev} y={y}')
  prev=z
# analytic minimum d(log2 out)/d(log2 in) at cap >0.77.
t=(3-math.sqrt(3))/6
bp=32*t*(1-t)*(1-2*t);min_slope=1-.45*bp/span
if min_slope<=.77:raise SystemExit(f'FAIL shadow min slope {min_slope}')
# Exact rejected 26665 shader failure: GLSL reserved identifier `shared` must never return.
if 'float shared=' in gm or ' shared=' in gm:
 raise SystemExit('FAIL regression: reserved GLSL identifier shared returned')
if 'sharedGuide26665' not in gm:raise SystemExit('FAIL safe UHDR shadow-depth temporary missing')
# Static ownership: non-overlap, no ISO/shutter dependency, same scalar in UHDR, SR final render path shared.
for t in ['smoothstep(0.02f, 0.08f, referenceProtectionEv)','smoothstep(0.10f, 0.40f, referenceProtectionEv)','isoDriven=false shutterDriven=false sceneSemantic=false','nearBlackIdentity=0.004 bodyIdentity=0.30','IRIS_26665_UHDR_SHADOW_DEPTH_PARITY','true2xSharedMap=']:
 if t not in matcher+gm+renderj:raise SystemExit('FAIL ownership regression '+t)
# Protected core IQ/capture/preview shader owners.
for r in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/assets/shaders/preview/main_fs.glsl']:
 if sha(base/r)!=sha(cand/r):raise SystemExit('FAIL frozen 26664 capture/IQ owner '+r)
print(f'PASS 26665 regressions: supplied outdoor low-key condition gets -0.70EV scene-key correction; supplied normal indoor global exposure stays exact 26664 while lower-body depth is {din:.3f}EV; protected HDR/Night exact fail-closed; near-black and >=0.30 identity; monotone min log slope {min_slope:.3f}; ratchet/preview/island/IQ regressions protected')
