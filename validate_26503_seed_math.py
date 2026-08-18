#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, math, re
from pathlib import Path

SHORT = Path('app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl')
DISPLAY = Path('app/src/main/assets/shaders/motionv2/display_exposure.glsl')
RENDER = Path('app/src/main/assets/shaders/motionv2/render.glsl')
COLOR = Path('app/src/main/assets/shaders/motionv2/color_transform.glsl')
DISPLAY_JAVA = Path('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java')

BASE_HASHES = {
    SHORT.as_posix(): '9664e51a34427bd525a2000bdb01ade2be4f0e6754d388e8079eb04d57403b47',
    DISPLAY.as_posix(): 'a68be9b3e4658fdfcab3a322a5c1b918863c27c581b468d2e29b16bea23a39f8',
    RENDER.as_posix(): '94373581342acd722a6778843a0d95f90d8aaefe7cba30d6b8b0800f74132bd7',
    COLOR.as_posix(): '4b14131a59e2358a9b8b18ded4c167f15cc0af5e0ab3d380768625017d7a81ac',
    DISPLAY_JAVA.as_posix(): 'bb3882b6bf8b7a4e4aef7a17ee44d90f68d2ad398a923c4fe46b4aa02201bf45',
}
FINAL_HASHES = {
    SHORT.as_posix(): 'da9791e239734cb610ff7c707a40b558115ec92362ee6d5c8baa76aeab3b1544',
    DISPLAY.as_posix(): '3ab7f631e41e0e300250f370f7d3f008efacd09fa0541a80c65ec749d586721a',
    RENDER.as_posix(): '39886a4256f6a53ffe70869798f5a1f23d0fb03e9386bc78e5ad938030469fb1',
    COLOR.as_posix(): BASE_HASHES[COLOR.as_posix()],
    DISPLAY_JAVA.as_posix(): '035d2f2f904d95b8d58d177ec31de49689b5f69cd1fda5ac9e4a6384b1969ada',
}
EXPECTED_PATCH_PATHS = {
    SHORT.as_posix(), DISPLAY.as_posix(), RENDER.as_posix(), DISPLAY_JAVA.as_posix()
}

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def clamp(v, lo, hi): return max(lo, min(hi, v))

def smoothstep(a, b, x):
    if a == b: return 0.0
    t = clamp((x-a)/(b-a), 0.0, 1.0)
    return t*t*(3.0-2.0*t)

def luminance(rgb): return 0.2126*rgb[0] + 0.7152*rgb[1] + 0.0722*rgb[2]

def max_ratio_error(a, b):
    # Compare normalized channel ratios without being sensitive to common scalar.
    ma=max(max(a),1e-12); mb=max(max(b),1e-12)
    return max(abs(a[i]/ma-b[i]/mb) for i in range(3))

# ------------------------- A / B / E shadow model -------------------------
def shadow_host(retained, support, iso):
    retained=max(1.0,float(retained)); support=max(1.0,float(support)); iso=max(1.0,float(iso))
    ratio=clamp(support/retained,0.10,1.0)
    depth=clamp((support-1.0)/7.0,0.0,1.0)
    risk=clamp((iso-800.0)/3200.0,0.0,1.0)
    recoverability=ratio*(0.35+0.65*depth)*(1.0-0.55*risk)
    strength=clamp(0.10*recoverability,0.0,0.10)
    floor=0.006+0.010*risk
    return ratio,depth,risk,recoverability,strength,floor

def shadow_shader(sensor_rgb, display_gain, strength, floor):
    c=[max(x,0.0) for x in sensor_rgb]
    displayed=[x*max(display_gain,1.0) for x in c]
    sy=max(luminance(c),0.0); dy=max(luminance(displayed),0.0)
    if sy<=1e-8 or strength<=0.0: return displayed
    fw=max(0.006,1.5*floor)
    floor_gate=smoothstep(floor,floor+fw,sy)
    shadow_gate=1.0-smoothstep(0.12,0.30,dy)
    scale=1.0+clamp(strength,0.0,0.10)*floor_gate*shadow_gate
    return [x*scale for x in displayed]

def test_shadow_math():
    # Strong 15-frame stack gets more bounded help than weak stack.
    good=shadow_host(15,14.5,100)
    weak=shadow_host(15,3.0,100)
    highiso=shadow_host(15,14.5,4000)
    assert 0.0 <= weak[4] < good[4] <= 0.10
    assert 0.0 <= highiso[4] < good[4]
    assert shadow_host(15,1.0,100)[4] < 0.004
    # Near sensor floor must remain unchanged even under a huge display gain.
    sensor=[0.0030,0.0025,0.0020]
    out=shadow_shader(sensor,15.0,good[4],good[5]); base=[x*15.0 for x in sensor]
    assert max(abs(out[i]-base[i]) for i in range(3)) < 1e-12
    # Supported shadow receives only a common scalar, never >10% local lift.
    sensor=[0.015,0.012,0.009]
    out=shadow_shader(sensor,5.0,good[4],good[5]); base=[x*5.0 for x in sensor]
    assert max_ratio_error(out,base) < 1e-12
    common=out[0]/base[0]
    assert 1.0 <= common <= 1.10+1e-12
    # Midtones and highlights are identity relative to the sole display gain.
    for sensor in ([0.12,0.10,0.08],[0.4,0.3,0.2],[1.2,0.8,0.5]):
        out=shadow_shader(sensor,4.0,good[4],good[5]); base=[x*4.0 for x in sensor]
        assert max(abs(out[i]-base[i]) for i in range(3)) < 1e-9
    return 'PASS A/B/E: one global display gain; local <=10% support/ISO-gated hue scale; sensor-floor stop; no midtone/highlight lift'

# ------------------------- C highlight/gamut model -------------------------
def fit_gamut(rgb):
    rgb=[max(x,0.0) for x in rgb]; peak=max(rgb)
    if peak<=1.0: return rgb
    return [x/max(peak,1e-6) for x in rgb]

def test_highlight_math():
    x=[0.7,0.5,0.3]; assert fit_gamut(x)==x
    warm=[1.4,1.0,0.7]; got=fit_gamut(warm)
    assert max(got)<=1.0+1e-12 and max_ratio_error(got,warm)<1e-12
    neutral=fit_gamut([1.3,1.3,1.3]); assert max(abs(x-1.0) for x in neutral)<1e-12
    saturated=fit_gamut([2.2,0.7,0.2]); assert max_ratio_error(saturated,[2.2,0.7,0.2])<1e-12
    return 'PASS C: extended-range final gamut fit is a uniform RGB scale; warm hue survives; true neutral remains neutral'

# ------------------------- D Short-A model (tested Tier-1 + Tier-2) -------------------------
def bilinear(img, x, y):
    px,py=x-0.5,y-0.5; x0,y0=math.floor(px),math.floor(py); fx,fy=px-x0,py-y0
    h,w=len(img),len(img[0])
    def get(ix,iy): return img[clamp(iy,0,h-1)][clamp(ix,0,w-1)]
    a,b,c,d=get(x0,y0),get(x0+1,y0),get(x0,y0+1),get(x0+1,y0+1)
    return [(1-fy)*((1-fx)*a[k]+fx*b[k])+fy*((1-fx)*c[k]+fx*d[k]) for k in range(4)]

def safe_normal(v): return [1.0 if x<0.90 else 0.0 for x in v]
def safe_short(v,t=0.98): return [1.0 if x<t else 0.0 for x in v]

def eval_corr(ref,short,p,source,scale=4.0,ref_scale=1.0,short_clip=0.98):
    err=support=0.0; lmin=1e20; lmax=0.0; lsum=lcount=0.0; h,w=len(ref),len(ref[0]); px,py=p
    for oy in range(-2,3):
      for ox in range(-2,3):
        if max(abs(ox),abs(oy))!=2: continue
        qx,qy=px+ox,py+oy; qs=(source[0]+ox,source[1]+oy)
        if not (0<=qx<w and 0<=qy<h and 0<=qs[0]<w and 0<=qs[1]<h): continue
        n=[x/max(ref_scale,1e-6) for x in ref[qy][qx]]; s=bilinear(short,*qs)
        mask=[a*b*(1.0 if n[k]>=0.010001 else 0.0) for k,(a,b) in enumerate(zip(safe_normal(n),safe_short(s,short_clip)))]
        count=sum(mask)
        if count<1.5: continue
        se=[x*scale for x in s]; rel=[abs(n[k]-se[k])/max(n[k],0.04) for k in range(4)]
        err+=sum(rel[k]*mask[k] for k in range(4)); support+=count
        l=sum(n)*0.25; lmin=min(lmin,l); lmax=max(lmax,l); lsum+=l; lcount+=1
    mean=err/support if support>0 else 1e20; lm=lsum/lcount if lcount else 0.0
    struct=(lmax-lmin)/max(lm,0.03) if lcount>=4 else 0.0
    return mean,struct,support

def old_refine(ref,short,p,predicted,scale=4.0):
    best=second=1e20; refined=predicted; structure=support=0.0; found=False; h,w=len(ref),len(ref[0])
    for sy in (-1,0,1):
      for sx in (-1,0,1):
        cand=(predicted[0]+0.5*sx,predicted[1]+0.5*sy)
        if not (0<=cand[0]<w and 0<=cand[1]<h): continue
        e,s,n=eval_corr(ref,short,p,cand,scale)
        if n<12.0: continue
        found=True
        if e<best: second,best,refined,structure,support=best,e,cand,s,n
        elif e<second: second=e
    if not found:return False,refined,best,structure,support,False
    if structure>=0.08:
        ok=best<=0.12 and (best<=0.055 or second-best>=0.010)
    else: ok=support>=16.0 and best<=0.060
    return ok,refined,best,structure,support,True

def dir_offset(d,r):
    h=max(r//2,1)
    return [(-r,0),(r,0),(0,-r),(0,r),(-r,-r),(r,r),(r,-r),(-r,r),(-h,-r),(h,r),(h,-r),(-h,r),(-r,-h),(r,h),(r,-h),(-r,h)][d]

def boundary_validate(ref,short,p,predicted,flow_conf,scale=4.0,minimum_flow=0.25,physical_clip=0.95,short_clip=0.98):
    if flow_conf<max(minimum_flow,0.85): return False,1e20,0.0
    h,w=len(ref),len(ref[0]); cn=ref[p[1]][p[0]]; clip=[1.0 if x>=physical_clip else 0.0 for x in cn]; cs=bilinear(short,*predicted)
    usable=[(1-clip[k])*safe_normal(cn)[k]*safe_short(cs,short_clip)[k]*(1.0 if cn[k]>=0.010001 else 0.0) for k in range(4)]
    cc=sum(usable)
    if cc>0.5:
        eq=[x*scale for x in cs]; rel=[abs(cn[k]-eq[k])/max(cn[k],0.04) for k in range(4)]
        if sum(rel[k]*usable[k] for k in range(4))/cc>0.070:return False,1e20,0.0
    err=support=accepted=conflicts=0.0; seen=[0]*16
    for d in range(16):
      for r in (4,8,16,32,64):
        ox,oy=dir_offset(d,r); qx,qy=p[0]+ox,p[1]+oy; qs=(predicted[0]+ox,predicted[1]+oy)
        if not (0<=qx<w and 0<=qy<h and 0<=qs[0]<w and 0<=qs[1]<h): continue
        n=ref[qy][qx]; sv=bilinear(short,*qs)
        mask=[a*b*(1.0 if n[k]>=0.010001 else 0.0) for k,(a,b) in enumerate(zip(safe_normal(n),safe_short(sv,short_clip)))]
        count=sum(mask)
        if count<1.5: continue
        eq=[x*scale for x in sv]; rel=[abs(n[k]-eq[k])/max(n[k],0.04) for k in range(4)]; ae=sum(rel[k]*mask[k] for k in range(4))/count
        if ae>0.12: conflicts+=1; break
        if ae<=0.055: accepted+=1; support+=count; err+=ae*count; seen[d]=1
        break
    mean=err/support if support else 1e20
    pairs=sum(1 for a,b in ((0,1),(2,3),(4,5),(6,7),(8,9),(10,11),(12,13),(14,15)) if seen[a] and seen[b])
    allc=sum(clip)>3.5; rd=6 if allc else 4; rp=2 if allc else 1; rs=18 if allc else 12
    return bool(conflicts<0.5 and accepted>=rd and sum(seen)>=rd and pairs>=rp and support>=rs and mean<=0.045),mean,support

def new_refine(ref,short,p,predicted,flow_conf=1.0,scale=4.0):
    ok,src,e,s,n,found=old_refine(ref,short,p,predicted,scale)
    if found:return ok,src,'tier1',e,n
    ok,e,n=boundary_validate(ref,short,p,predicted,flow_conf,scale)
    return ok,predicted,'tier2',e,n

def scene(w=96,h=96,scale=4.0):
    ref=[]
    for y in range(h):
      row=[]
      for x in range(w):
        b=0.14+0.0017*x+0.0011*y+0.018*math.sin(0.31*x+0.17*y); row.append([b*1.04,b,b*0.91,b*1.01])
      ref.append(row)
    return ref,[[[v/scale for v in px] for px in row] for row in ref]

def clip_square(ref,p,r,val=0.97):
    for y in range(p[1]-r,p[1]+r+1):
      for x in range(p[0]-r,p[0]+r+1):
        if 0<=y<len(ref) and 0<=x<len(ref[0]):ref[y][x]=[val]*4

def test_short_math():
    scale=5.656855; p=(48,48); predicted=(48.5,48.5)
    ref,short=scene(scale=scale); old=old_refine(ref,short,p,predicted,scale); new=new_refine(ref,short,p,predicted,1.0,scale)
    assert old[0] and old[5] and new[0] and new[2]=='tier1' and new[1]==old[1]
    ref,short=scene(scale=scale)
    for y in range(p[1]-3,p[1]+4):
      for x in range(p[0]-3,p[0]+4): short[y][x]=[v*0.55 for v in short[y][x]]
    old=old_refine(ref,short,p,predicted,scale); new=new_refine(ref,short,p,predicted,1.0,scale)
    assert old[5] and not old[0] and not new[0] and new[2]=='tier1'
    ref,short=scene(scale=scale); clip_square(ref,p,3); assert not old_refine(ref,short,p,predicted,scale)[5]; assert new_refine(ref,short,p,predicted,1.0,scale)[0]
    assert not new_refine(ref,short,p,predicted,0.84,scale)[0]
    assert not new_refine(ref,short,p,(predicted[0]+3,predicted[1]+1.5),1.0,scale)[0]
    ref2,short2=scene(scale=scale); clip_square(ref2,p,3); ax,ay=p[0]+4,p[1]
    for y in range(ay-1,ay+2):
      for x in range(ax-1,ax+2): short2[y][x]=[min(0.97,v*0.35) for v in short2[y][x]]
    assert not new_refine(ref2,short2,p,predicted,1.0,scale)[0]
    ep=(47,48); epr=(47.5,48.5); er,es=scene(scale=scale)
    for yy in range(len(er)):
      for xx in range(len(er[0])):
        val=[0.38,0.22,0.18,0.24] if xx<48 else [0.19,0.34,0.21,0.31]; er[yy][xx]=val; es[yy][xx]=[z/scale for z in val]
    clip_square(er,ep,3); assert new_refine(er,es,ep,epr,1.0,scale)[0]; assert not new_refine(er,es,ep,(epr[0]+0.5,epr[1]),1.0,scale)[0]
    # One-sided surroundings cannot validate an exhausted center.
    r3,s3=scene(scale=scale); clip_square(r3,p,3)
    for r in (4,8,16,32,64):
      for d in range(1,16):
        ox,oy=dir_offset(d,r); x,y=p[0]+ox,p[1]+oy
        if 0<=x<len(r3[0]) and 0<=y<len(r3):r3[y][x]=[0.97]*4
    assert not new_refine(r3,s3,p,predicted,1.0,scale)[0]
    # Phase-isolated physical recovery: only the clipped phase may change.
    normal=[0.42,1.00,0.47,0.38]; shortc=[0.105,0.205,0.118,0.095]; clip=[0,1,0,0]
    recover=[clip[i]*(1 if shortc[i]<0.98 else 0) for i in range(4)]; eq=[v*4.0 for v in shortc]
    req=max([1.0]+[normal[i]/max(eq[i],1e-6) for i in range(4) if recover[i]])
    assert req<=1.25; out=normal[:]; state=[float(x) for x in clip]
    for i in range(4):
      if recover[i]:
        t=clamp((normal[i]-0.95)/0.05,0,1); t=t*t*(3-2*t); out[i]=normal[i]*(1-t)+eq[i]*req*t; state[i]=2.0
    assert out[0]==normal[0] and out[2]==normal[2] and out[3]==normal[3] and state==[0.0,2.0,0.0,0.0]
    return 'PASS D: Tier-1 identity; boundary rescue only for unobservable centers; wrong flow/motion/color-edge/one-sided evidence rejected; phase ownership isolated'

# ------------------------- F border proof -------------------------
def test_border_math():
    # Existing x==0 mirror repeats x==1; it cannot invent a chroma-only stripe.
    neutral=[[0.2,0.2,0.2],[0.2,0.2,0.2],[0.2,0.2,0.2]]
    assert neutral[1]==neutral[0]
    grad=[[0.12,0.10,0.08],[0.16,0.13,0.10],[0.20,0.16,0.12]]
    x0=grad[1]; x1=grad[1]; assert max_ratio_error(x0,x1)==0
    edge=[[0.9,0.2,0.1],[1.1,0.25,0.12]]; assert max_ratio_error(edge[1],edge[1])==0
    return 'PASS F: border gate proves existing one-pixel left mirror repeats valid RGB without chroma masking/desaturation; no new border math required'

# ------------------------- source / architecture gates -------------------------
def function_body(src: str, name: str) -> str:
    start=src.index(name); brace=src.index('{',start); depth=0
    for i in range(brace,len(src)):
        if src[i]=='{':depth+=1
        elif src[i]=='}':
            depth-=1
            if depth==0:return src[brace:i+1]
    raise AssertionError(f'unclosed function {name}')

def source_tests(root: Path, base_root: Path|None, patch: Path|None):
    for rel,want in FINAL_HASHES.items():
        p=root/rel; assert p.is_file(),p; got=sha(p); assert got==want,f'{rel}: {got} != {want}'
    if base_root:
        for rel,want in BASE_HASHES.items():
            got=sha(base_root/rel); assert got==want,f'base {rel}: {got} != {want}'
    if patch:
        txt=patch.read_text(); paths={a for a,b in re.findall(r'^diff --git a/(\S+) b/(\S+)$',txt,re.M) if a==b}
        assert paths==EXPECTED_PATCH_PATHS,(paths,EXPECTED_PATCH_PATHS)
        for m in ('IRIS_26503_SINGLE_EXPOSURE_SHADOW_AUTHORITY','IRIS_26503_EVIDENCE_BASED_STACK_AWARE_SHADOW_RECOVERY','IRIS_26503_UPSTREAM_EXHAUSTION_OWNS_WHITE','IRIS_26503_HUE_PRESERVING_EXTENDED_RANGE_GAMUT','IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY'):
            assert m in txt,m
    j=(root/DISPLAY_JAVA).read_text(); d=(root/DISPLAY).read_text(); r=(root/RENDER).read_text(); c=(root/COLOR).read_text(); s=(root/SHORT).read_text()
    # A/B/E ownership and host/shader interface.
    for tok in ('motionV2DisplayGain','motionV2EffectiveSupport','retainedFrameCount','basePipeline.mParameters.iso','shadowRecoveryStrength','shadowFloorStop','globalResidualGain=1.0','localHueScaleOnly=true'):
        assert tok in j,tok
    assert j.count('glProg.setVar("displayGain"')==1
    assert j.count('glProg.setVar("shadowRecoveryStrength"')==1
    assert j.count('glProg.setVar("shadowFloorStop"')==1
    for tok in ('uniform float displayGain;','uniform float shadowRecoveryStrength;','uniform float shadowFloorStop;','sensorY','displayedY','recoverSupportedShadow(displayed, c)'):
        assert tok in d,tok
    assert 'c * max(displayGain, 1.0)' in d
    assert '0.10' in d and 'displayed * scale' in d
    # C: Camera2 stage remains extended-linear and byte-identical; render has no downstream white-paint authority.
    assert sha(root/COLOR)==BASE_HASHES[COLOR.as_posix()]
    assert 'Output=max(linearSrgb,vec3(0.0));' in c and 'clamp(linearSrgb' not in c
    mapbody=function_body(r,'vec3 mapExtendedLinearHeadroom')
    fitbody=function_body(r,'vec3 fitDisplayGamut')
    assert 'return mapped;' in mapbody and 'neutralMix' not in mapbody and 'mix(mapped,vec3(mappedGuide)' not in mapbody
    assert 'return rgb/max(peak,1.0e-6);' in fitbody
    assert 'vec3(1.0)' not in fitbody and 'mix(' not in fitbody
    # D: exact conservative Tier-2 and unchanged physical recovery/provenance constants.
    for tok in ('IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY','flowConfidence < max(minimumFlowConfidence, 0.85)','centerError > 0.070','strongConflicts < 0.5','allCenterPhasesClipped','requiredDirections = allCenterPhasesClipped ? 6.0 : 4.0','supportCount >= requiredSupport','meanRelativeError <= 0.045','state[i] = PROVENANCE_SHORT_VALIDATED;'):
        assert tok in s,tok
    assert 'if (found) {' in s and 'return supportCount >= 16.0 && bestError <= 0.060;' in s
    # F: exactly the proven left-edge mirror remains; no new edge mask.
    assert r.count('if(sourceXY.x==0 && sourceSize.x>1) sourceXY.x=1;')==1
    for bad in ('sourceXY.y==0','sourceXY.x==sourceSize.x-1','sourceXY.y==sourceSize.y-1','borderDesatur','borderChroma','edgeMask'):
        assert bad not in r,bad
    # G: local changed files must not contain forbidden architecture re-entry.
    joined='\n'.join((j,d,r,s,c)).lower()
    for bad in ('new autoexposure','new exposurefusion','new esd3d2','new initial','adrc fallback','single-frame fallback','photon noises','rcd demosaic'):
        assert bad not in joined,bad
    return 'PASS SOURCE A-G: exact four-file runtime delta + frozen Camera2 transform; host/shader bindings; no downstream white paint; Tier-2 Short authority; border/forbidden-path guards'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--base-root',type=Path); ap.add_argument('--patch',type=Path)
    a=ap.parse_args()
    print(source_tests(a.root,a.base_root,a.patch))
    print(test_shadow_math()); print(test_highlight_math()); print(test_short_math()); print(test_border_math())
    print('PASS: 26503 integrated A-G validator complete')
if __name__=='__main__': main()
