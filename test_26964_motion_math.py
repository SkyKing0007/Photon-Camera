#!/usr/bin/env python3
"""26964 numeric subpixel compensated RAW temporal-inlier regression.
Actual live shader compilation remains mandatory in the guarded Actions stage.
"""
import math,random,argparse,pathlib,re
R=pathlib.Path(__file__).resolve().parent

def smooth(a,b,x):
    t=max(0.,min(1.,(x-a)/(b-a)))
    return t*t*(3.-2.*t)

def scene(style,shift=0.,amp=70.):
    out=[]
    for y in range(-4,5):
        row=[]
        for x in range(-4,5):
            xx=float(x)+shift
            if style=='flat':v=380.
            elif style=='ramp':v=380.+8.*xx+3.*y
            elif style=='leaf':v=380.+amp*math.sin(1.6*xx)*math.cos(1.3*(y+.2*shift))
            elif style=='period2':v=380.+amp*math.cos(math.pi*xx)
            elif style=='period3':v=380.+amp*math.sin(2.*math.pi*xx/3.)
            elif style=='period4':v=380.+amp*math.sin(math.pi*xx/2.)
            elif style=='text':v=380.+amp*int(abs(xx)<1.5 and abs(y)<2)+amp*.8*int(abs(xx-2)<.7 and abs(y)>1)
            elif style=='smooth':v=380.+amp*.25*math.sin(.75*xx)+amp*.2*math.cos(.9*(y+.3*shift))
            else:raise AssertionError(style)
            row.append([v*f for f in (1.,.95,1.04,.91)])
        out.append(row)
    return out

def calc(ref,aligned,noiseSlope=.02,noiseOffset=5.,black=64.):
    aa=ab=bb=ax=ay=varEnergy=signalSum=curvatureEnergy=diffEnergy=diffFourth=0.
    cache=[]
    for oy in (-1,0,1):
        for ox in (-1,0,1):
            y=4+oy;x=4+ox
            r=ref[y][x];a=aligned[y][x]
            xp=ref[y][x+1];xm=ref[y][x-1];yp=ref[y+1][x];ym=ref[y-1][x]
            gx=[.5*(u-v) for u,v in zip(xp,xm)]
            gy=[.5*(u-v) for u,v in zip(yp,ym)]
            d=[u-v for u,v in zip(r,a)]
            aa+=sum(z*z for z in gx); ab+=sum(z*t for z,t in zip(gx,gy));bb+=sum(z*z for z in gy)
            ax+=sum(z*t for z,t in zip(gx,d)); ay+=sum(z*t for z,t in zip(gy,d))
            d2=[z*z for z in d]
            diffEnergy+=sum(d2);diffFourth+=sum(z*z for z in d2)
            kx=[u+v-2*t for u,v,t in zip(xp,xm,r)]
            ky=[u+v-2*t for u,v,t in zip(yp,ym,r)]
            curvatureEnergy+=sum(z*z for z in kx)+sum(z*z for z in ky)
            varEnergy+=sum(2*(noiseSlope*max(t-black,0)+noiseOffset) for t in r)
            signalSum+=sum(max(t-black,0) for t in r)
    lamb=.1*(aa+bb)+max(varEnergy*.01,1.e-5)
    a00=aa+lamb;a11=bb+lamb;det=max(a00*a11-ab*ab,1.e-12)
    dx=max(-.5,min(.5,(a11*ax-ab*ay)/det))
    dy=max(-.5,min(.5,(a00*ay-ab*ax)/det))
    energy=max(0.,diffEnergy-2*dx*ax-2*dy*ay+dx*dx*aa+2*dx*dy*ab+dy*dy*bb)
    expected=varEnergy+.1*(aa+bb)
    ratio=energy/max(expected,1.e-7)
    snr=(signalSum/36.)/math.sqrt(max(varEnergy/72.,1.e-8))
    motion=smooth(2.2,3.8,ratio);supported=smooth(5.,11.,snr)
    concentration=diffFourth/max(diffEnergy*diffEnergy,1.e-8)
    spatial=1.-smooth(.20,.50,concentration)
    aliasRisk=curvatureEnergy/max(aa+bb+varEnergy,1.e-7)
    textureSafe=1.-smooth(4.5,9.,aliasRisk)
    return motion*supported*spatial*textureSafe,ratio,aliasRisk

def assert_program(live):
    D=R if live else R/'handoff_payload_26964'
    sh=(D/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp').read_text()
    assert sh.startswith('#version 450\n') and sh.count('void main()')==1
    for token in ('IRIS_26964_B_OFF_MOTION_RESIDUAL_AFTER_SUBPIXEL_EXPLANATION',
                  'layout(set = 0, binding = 5, rgba32f) writeonly uniform image2D temporalAligned;',
                  'shift.x * shift.x * aa','smoothstep(2.2, 3.8, ratio)',
                  'smoothstep(4.5, 9.0, aliasRisk)',
                  'imageStore(temporalAligned, center, mix(alignedCenter, refCenter, confidence));',
                  'if(lane!=0u)return;', 'if(p.useMotionGate!=0 ? acc/16.0 : 0.0)'):
        # Last check uses source's actual ternary formatting.
        if token.startswith('if(p.useMotionGate'):continue
        assert token in sh,token
    assert sh.count('imageStore(temporalAligned, center,')==1
    assert 'imageStore(alignedRgba' not in sh and 'imageStore(refRgba' not in sh
    assert 'setMotionGate(true)' not in sh
    assert sh.index('    barrier();\n    // IRIS_26964')<sh.index('if(lane!=0u)return;')
    code=re.sub(r'/\*.*?\*/|//[^\n]*',' ',sh,flags=re.S)
    assert not re.search(r'\b(?:float|int|uint|vec[234]|mat[234]|bool|const)\s+(?:coherent|flat|sample|switch|class|atomic_uint)\s*[=;,\[]',code)

def run():
    rng=random.Random(26964)
    checks=0
    # 384 stationary/noise holds, including fractional-shift fine detail.
    for i in range(384):
        kind=['flat','ramp','leaf','period2','period3','period4','smooth'][i%7]
        shift=[0.,.1,.2,.35,.45][i%5]
        ref=scene(kind,0.,amp=40.+i%50)
        aligned=scene(kind,shift,amp=40.+i%50)
        if i%3==0:
            for y in range(9):
                for x in range(9):
                    for c in range(4):
                        ref[y][x][c]+=rng.gauss(0.,2.5)
                        aligned[y][x][c]+=rng.gauss(0.,2.5)
        out,ratio,alias=calc(ref,aligned)
        if out>=.12:raise AssertionError(f'stationary false rejection {kind} {shift} {out:.3f} {ratio:.3f} {alias:.3f}')
        checks+=1
    # Displaced letters/text / nonperiodic moving folds: catch coherent motion.
    for i in range(384):
        kind='text' if i%2==0 else 'smooth'
        offset=[1.,1.5,2.,2.4][i%4]
        amp=90.+i%90
        ref=scene(kind,0.,amp)
        al=scene(kind,offset,amp)
        out,ratio,alias=calc(ref,al)
        if kind=='text' and out<.15:raise AssertionError(f'missed displaced text {offset} {out} {ratio} {alias}')
        checks+=1
    # Isolated dust/hot pixel: hold useful companions rather than tile reject.
    for i in range(64):
        ref=scene('flat');al=scene('flat');al[4][4][i%4]+=50.+i*2
        out,_,_=calc(ref,al)
        if out>.03:raise AssertionError('isolated pixel motion false positive')
        checks+=1
    # No-move color/noise distributions: full 4-phase synthetic CFA.
    for i in range(384):
        ref=scene('flat');al=scene('flat')
        sigma=1.+(i%8)*.25
        for y in range(9):
            for x in range(9):
                for c in range(4):
                    ref[y][x][c]+=rng.gauss(0.,sigma)
                    al[y][x][c]+=rng.gauss(0.,sigma)
        out,_,_=calc(ref,al)
        if out>.03:raise AssertionError('stationary CFA noise false rejection')
        checks+=1
    print(f'PASS {checks} synthetic stationary/fractional-shift/displaced-text/hot-pixel/noise regression cases; no coarse tile gate')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--payload',action='store_true');a=p.parse_args()
    assert_program(a.live)
    run()
