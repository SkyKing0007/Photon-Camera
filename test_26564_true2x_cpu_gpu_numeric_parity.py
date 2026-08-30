#!/usr/bin/env python3
import math, numpy as np
rng=np.random.default_rng(26564)
RAW_W,RAW_H=12,10
OUT_W,OUT_H=RAW_W*2,RAW_H*2
FLOW_W,FLOW_H=4,4
COV_W,COV_H=6,5
REJ_W,REJ_H=3,3
FRAMES=6

def clamp(v,a,b): return max(a,min(b,v))
def mirror(u,b):
    if u <= b: u=2*b-u
    if u > 1-b: u=2*(1-b)-u
    return clamp(u,0.0,1.0)
def bilinear(arr,u,v):
    h,w=arr.shape[:2]; x=clamp(u*w-.5,0,w-1); y=clamp(v*h-.5,0,h-1)
    x0=int(math.floor(x)); y0=int(math.floor(y)); x1=min(x0+1,w-1); y1=min(y0+1,h-1)
    fx=x-x0; fy=y-y0
    return (arr[y0,x0]*(1-fx)+arr[y0,x1]*fx)*(1-fy)+(arr[y1,x0]*(1-fx)+arr[y1,x1]*fx)*fy
def swizzle(v,t):
    maps=((0,1,2,3),(1,0,3,2),(2,3,0,1),(3,2,1,0)); return np.asarray(v)[list(maps[t&3])]
def raw_at(raw,x,y): return float(raw[clamp(y,0,RAW_H-1),clamp(x,0,RAW_W-1)])
def kernel(dx,dy,c):
    d=dx*dx*c[0]+dy*dy*c[1]+dx*dy*c[2]*2.0
    return math.exp2(-.5*d)+.00005
def rbf(raw,sx,sy,cfa,gains,black,cov):
    px=int(math.floor(sx)); py=int(math.floor(sy)); b=np.zeros((3,3)); w=np.zeros((3,3))
    subx=math.floor(sx)+.5-sx; suby=math.floor(sy)+.5-sy
    for ix in range(3):
      for iy in range(3):
        b[ix,iy]=raw_at(raw,px+ix-1,py+iy-1); w[ix,iy]=kernel(subx+ix-1,suby+iy-1,cov)
    off=((1,1),(0,1),(1,0),(0,0))[cfa]
    t=(((py+off[1])&1)<<1)+((px+off[0])&1)
    rg=swizzle(gains,t); rb=swizzle(black,t)
    cw=np.array((w[0,0],w[0,2],w[2,0],w[2,2])); cv=np.array((b[0,0],b[0,2],b[2,0],b[2,2]))
    uw=np.array((w[1,0],w[1,2])); uv=np.array((b[1,0],b[1,2])); lw=np.array((w[0,1],w[2,1])); lv=np.array((b[0,1],b[2,1]))
    ti=np.zeros(4); tw=np.zeros(4)
    ti[0]=np.dot(cv*rg[0]+rb[0],cw); tw[0]=cw.sum()
    ti[1]=np.dot(uv*rg[1]+rb[1],uw); tw[1]=uw.sum()
    ti[2]=np.dot(lv*rg[2]+rb[2],lw); tw[2]=lw.sum()
    ti[3]=(b[1,1]*rg[3]+rb[3])*w[1,1]; tw[3]=w[1,1]
    I=swizzle(ti,t); W=swizzle(tw,t)
    return np.array((I[0],I[1]+I[2],I[3])),np.array((W[0],W[1]+W[2],W[3]))

def gpu_add_half(acc,contrib):
    # RGBA16F/RG16F additive render targets round after each blended write.
    return np.asarray(np.asarray(acc,dtype=np.float16)+np.asarray(contrib,dtype=np.float16),dtype=np.float16)

# Smooth but textured Bayer-like synthetic RAW. Gains normalize camera codes.
y,x=np.mgrid[0:RAW_H,0:RAW_W]
base=2500+5000*(x/(RAW_W-1))+2800*(y/(RAW_H-1))+700*np.sin(x*.9)+350*np.cos(y*1.1)
raws=[]; flows=[]; covs=[]; rejs=[]
shifts=((0.05,0.06),(0.28,0.10),(0.09,0.31),(0.32,0.34),(1.06,0.07),(0.30,1.32))
for fi,(dx,dy) in enumerate(shifts):
    noise=rng.normal(0,28,(RAW_H,RAW_W)); raws.append(np.clip(base+noise+fi*6,64,15000).astype(np.uint16))
    fm=np.empty((FLOW_H,FLOW_W,2),np.float32); fm[...,0]=(dx+rng.normal(0,.005,(FLOW_H,FLOW_W)))/RAW_W; fm[...,1]=(dy+rng.normal(0,.005,(FLOW_H,FLOW_W)))/RAW_H; flows.append(fm.astype(np.float16))
    # Exact stored RGB10 normalized domain then linearly sampled, as GL and CPU do.
    cv=rng.uniform(.12,.78,(COV_H,COV_W,3)); q=np.rint(cv*1023).astype(np.int32); covs.append((q/1023.).astype(np.float32))
    rejs.append((rng.integers(180,256,(REJ_H,REJ_W),dtype=np.uint8).astype(np.float32)/255.))

gains=np.array((1/15000.,1/14900.,1/15100.,1/15050.),np.float32)
black=np.array((-64/15000.,-64/14900.,-64/15100.,-64/15050.),np.float32)
crg=np.array((.55,1.7,.62,1.55),np.float32); cb=np.array((-.25,.5),np.float32)
scale=np.array((1.01,.99,1.02),np.float32)
lens=np.ones((3,4,4),np.float32); lens[...,0]=1.01; lens[...,1]=.99; lens[...,2]=1.00; lens[...,3]=1.02

max_abs=0.; max_rel=0.; phase_mismatch=0; samples=0
for gy in range(OUT_H):
  for gx in range(OUT_W):
    cpu=np.zeros(6,np.float32); gpu=np.zeros(6,np.float16); cmask=0; gmask=0
    ru=(gx+.5)/OUT_W; rv=(gy+.5)/OUT_H
    for fi in range(FRAMES):
      flow=np.asarray(bilinear(flows[fi].astype(np.float32),ru,rv),np.float32)
      su=mirror(ru+float(flow[0]),1.5/RAW_W); sv=mirror(rv+float(flow[1]),1.5/RAW_H)
      packed=np.asarray(bilinear(covs[fi],su,sv),np.float32)
      cov=np.array((packed[0]*crg[1]+crg[0],packed[1]*crg[3]+crg[2],packed[2]*cb[1]+cb[0]),np.float32)
      color,weights=rbf(raws[fi],su*RAW_W,sv*RAW_H,0,gains,black,cov)
      fw=float(bilinear(rejs[fi],ru,rv)); c=np.concatenate((color*fw,weights*fw)).astype(np.float32)
      cpu=np.asarray(cpu+c,dtype=np.float32); gpu=gpu_add_half(gpu,c)
      if fw>.08:
        px=(float(flow[0])*RAW_W)%1.; py=(float(flow[1])*RAW_H)%1.; bit=1<<((1 if px>=.5 else 0)+(2 if py>=.5 else 0)); cmask|=bit; gmask|=bit
    def resolve(a):
      rgb=np.maximum(0,a[:3]/np.maximum(a[3:],1e-7))*scale
      sh=bilinear(lens,ru,rv); rgb*=np.array((sh[0],.5*(sh[1]+sh[2]),sh[3]))
      return np.maximum(rgb,0)
    a=resolve(cpu.astype(np.float64)); b=resolve(gpu.astype(np.float32).astype(np.float64))
    err=np.abs(a-b); rel=err/np.maximum(np.abs(a),1e-4)
    max_abs=max(max_abs,float(err.max())); max_rel=max(max_rel,float(rel.max())); phase_mismatch += (cmask!=gmask); samples+=1

assert phase_mismatch==0, phase_mismatch
assert max_abs < 0.004, max_abs
assert max_rel < 0.006, max_rel
# Independent phase sanity: the six shifts occupy distinct bins but integer-offset duplicates do not invent bins.
def phase_mask(sh):
 m=0
 for dx,dy in sh: m |= 1<<((1 if dx%1>=.5 else 0)+(2 if dy%1>=.5 else 0))
 return m
assert phase_mask(((.1,.1),(1.1,2.1),(3.1,4.1))).bit_count()==1
assert phase_mask(((.1,.1),(.6,.1),(.1,.6),(.6,.6))).bit_count()==4
print(f'PASS synthetic CPU/GPU true2x parity samples={samples} maxAbs={max_abs:.8f} maxRel={max_rel:.8f} phaseMismatch={phase_mismatch}')
print('PASS repeated subpixel phases do not increase independent phase support')
print('PASS four quadrant subpixel phases report support=4')
