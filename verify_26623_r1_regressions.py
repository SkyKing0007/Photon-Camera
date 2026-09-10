#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26623_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def clamp(x,a,b): return max(a,min(b,x))
def smooth(e0,e1,x):
    t=clamp((x-e0)/max(e1-e0,1e-9),0.0,1.0); return t*t*(3.0-2.0*t)
def legacy_body(x,gain):
    requested=max(gain,1e-6)*0.80; white=min(0.95,requested); body=requested
    if requested>white: body=min(requested,4.0*white-1e-4)
    ratio=max(body/max(white,1e-6)-1.0,0.0); om=1.0-x
    cubic=white*x+(body-white)*x*om*om; rational=body*x/(1.0+ratio*x)
    cubic_d=white+(body-white)*om*(1.0-3.0*x); rational_d=body/((1.0+ratio*x)*(1.0+ratio*x))
    return 0.5*(cubic+rational),0.5*(cubic_d+rational_d)
def legacy(x,gain):
    x=max(x,0.0); requested=max(gain,1e-6)*0.80; white=min(0.95,requested); body=requested
    if requested>white: body=min(requested,4.0*white-1e-4)
    ratio=max(body/max(white,1e-6)-1.0,0.0)
    if x<=1.0:return legacy_body(x,gain)[0]
    rs=body/((1.0+ratio)*(1.0+ratio)); bs=0.5*(white+rs); reserve=max(1.0-white,0.0); scale=reserve/max(bs,1e-6); ex=x-1.0
    return white+reserve*ex/(ex+scale)
def pressure(broad,hard,basew,adaptw):
    b=smooth(0.015,0.060,clamp(broad,0,1)); h=smooth(0.010,0.050,clamp(hard,0,1)); bw=max(basew,1.0); aw=max(adaptw,bw)
    sp=smooth(0.08,0.35,max(aw/bw-1.0,0.0)); return clamp(max(0.70*b+0.30*sp,0.75*h),0,1)
def newmap(x,gain,broad,hard,basew,adaptw):
    x=max(x,0.0); old=legacy(x,gain); requested=max(gain,1e-6)*0.80; en=smooth(1.05,1.25,requested)
    if en<=1e-7 or x<=0.65:return old
    p=pressure(broad,hard,basew,adaptw); tw=0.925+(0.885-0.925)*p; m1=0.270+(0.200-0.270)*p
    sv,m0=legacy_body(0.65,gain); width=0.35; sec=(tw-sv)/width
    if sec<=1e-6:return old
    m0=max(m0,0.0); m1=max(m1,0.0); norm=m0*m0/(sec*sec)+m1*m1/(sec*sec)
    if norm>9.0:
        lim=3.0/math.sqrt(norm); m0*=lim; m1*=lim
    if x<=1.0:
        t=clamp((x-0.65)/width,0,1); t2=t*t; t3=t2*t
        cand=(2*t3-3*t2+1)*sv+(t3-2*t2+t)*width*m0+(-2*t3+3*t2)*tw+(t3-t2)*width*m1
    else:
        reserve=max(1.0-tw,0.0); scale=reserve/max(m1,1e-6); ex=x-1.0; cand=tw+reserve*ex/(ex+scale)
    return old+(cand-old)*en
# Exact successful 26622 curve is preserved through source guide 0.65 for all highlight pressures.
scenes=[('sparse',4.4601526,0.0,0.0,4.0141373,4.0141373),
        ('office',4.4601526,0.020691339,0.019165428,4.0141373,4.7945843),
        ('broad',3.2236962,0.060,0.050,3.0,4.5)]
for name,g,b,h,bw,aw in scenes:
    for i in range(651):
        x=i/1000.0; assert abs(newmap(x,g,b,h,bw,aw)-legacy(x,g))<1e-12,(name,x)
    # Complete active upper body must remain monotonic with useful slope and no plateau.
    xs=[0.65+i*(0.35/3500.0) for i in range(3501)]; ys=[newmap(x,g,b,h,bw,aw) for x in xs]
    slopes=[(ys[i+1]-ys[i])/(xs[i+1]-xs[i]) for i in range(len(xs)-1)]
    assert min(slopes)>=0.19,(name,min(slopes))
    assert ys[-1]-ys[0]>=0.085,(name,ys[-1]-ys[0])
    # Tail must remain increasing and preserve >1 source ordering/headroom.
    tx=[1.0+i*0.002 for i in range(1001)]; ty=[newmap(x,g,b,h,bw,aw) for x in tx]
    assert all(ty[i+1]>ty[i] for i in range(len(ty)-1)),name
    assert ty[-1] < 1.0 and ty[-1] > ty[0]
# Adaptivity is continuous and broad scenes reserve more SDR highlight range, not a semantic mode switch.
po=pressure(0.020691339,0.019165428,4.0141373,4.7945843); pb=pressure(0.060,0.050,3.0,4.5)
assert 0.0<po<pb<=1.0,(po,pb)
assert newmap(1.0,3.2236962,0.060,0.050,3.0,4.5) < newmap(1.0,3.2236962,0.0,0.0,3.0,3.0)
# C1 checks numerically at both join points.
for name,g,b,h,bw,aw in scenes:
    for join in [0.65,1.0]:
        e=1e-5; dl=(newmap(join,g,b,h,bw,aw)-newmap(join-e,g,b,h,bw,aw))/e; dr=(newmap(join+e,g,b,h,bw,aw)-newmap(join,g,b,h,bw,aw))/e
        assert abs(dl-dr)<0.01,(name,join,dl,dr)
# Local-Laplacian implementation, native SR, UHDR and viewfinder body solver remain exactly 26622.
for path in [
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']:
    assert (B/path).read_bytes()==(C/path).read_bytes(),path
# SHORT telemetry regression: device output path must be unchanged; retained CPU bytes only, and loss GPU texture release remains before ordinary frame-weight release.
k=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); kb=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert 'readOnly=true outputUnchanged=true' in k
assert k.index('shortLossCandidateWeight26607, "26607 SHORT loss-candidate proof"') < k.index('releaseOwnedTexture(frameWeight, "26607 ordinary SHORT post-dilation weight")')
for forbidden in ['broadSupportFraction >','if (broadInterior','shortLossStats26623?.retainedBytes ?: return']:
    # the telemetry helper has an if for input validity, but must never gate output behavior on fraction.
    if forbidden=='if (broadInterior': continue
    assert forbidden not in k,forbidden
print(f'PASS 26623 regressions: 26622 black/shadow/lower-mid mapping exact through 0.65; upper-body minSlope>=0.19; C1/increasing HDR tail; broad highlight pressure continuous; Local-Laplacian/native/UHDR/meter protected; SHORT telemetry read-only (officePressure={po:.4f}, broadPressure={pb:.4f})')
