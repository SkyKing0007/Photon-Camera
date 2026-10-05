#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,math
if len(sys.argv)!=3: raise SystemExit('usage: validate_26768.py BASE26767 CAND26768')
base,cand=map(Path,sys.argv[1:]); root=Path(__file__).resolve().parent
expected=[p for p in (root/'26768_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if p]
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
a,b=H(base),H(cand); assert len(a)==len(b)==1823
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)); assert changed==sorted(expected),(changed,expected)
assert not(set(b)-set(a)) and not(set(a)-set(b))
print('PASS 26768 exact 2-file runtime allowlist / zero additions')

v=(cand/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726768' in v and 'VERSION_BUILD=26768' in v
print('PASS 26768 version/build')

rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
bs=(base/rel).read_text(); cs=(cand/rel).read_text()
def raw(src,name):
 for anchor in (f'val {name} = """',f'private val {name} = """'):
  if anchor in src:
   i=src.index(anchor)+len(anchor); j=src.index('""".trimIndent()',i); return src[i:j]
 raise AssertionError(name)
shader_names=['common','universalAdaptiveColor26561','seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb']
shader_changed=[n for n in shader_names if raw(bs,n)!=raw(cs,n)]
assert shader_changed==['iirRgb'],shader_changed
pins={
 'seed':'621a54fbdace51a1c38902d1ea3f058ae66dfac5b934333185e0e016fa48a532',
 'localMedian':'645888cf113955f8c5173b7b6f29da69a16c00c4bb0300474e26330ee522adeb',
 'directionalSmooth':'96a87bd3830bcdeed68843161934aca4d68f4e6c1c98173bcb80e75a3f61a3ee',
 'universalAdaptiveColor26561':'0a75e0e900e26769288d69947d4febe080f44a3a0b9551c96e08640ade554802',
 'finalCameraRgb':'2b2ae5bc776db6bbfeab5fb7ae9acf04d1d107976cd05d225b0caa0424977981',
}
for n,h in pins.items():
 assert hashlib.sha256(raw(bs,n).encode()).hexdigest()==h,(n,'base')
 assert hashlib.sha256(raw(cs,n).encode()).hexdigest()==h,(n,'candidate')
assert hashlib.sha256(raw(bs,'iirRgb').encode()).hexdigest()=='864514ec018e5bd826f08a28c0f4202656c8c9f4a757795fe5b9fe5b7f777086'
assert hashlib.sha256(raw(cs,'iirRgb').encode()).hexdigest()=='0a59d8f8953ce5b8ec1b0a69395ed54a578e8729b391602e6d0fa0bdd89cfbf5'
iir=raw(cs,'iirRgb')
for token in [
 'IRIS_26768_IIR3_CHROMA_OWNERSHIP_RESET',
 'layout(rgba16ui,binding=2) readonly uniform highp uimage2D uOwnership;',
 'if(i>0&&uFilterLuma==0&&highlightPreservePermission>0.5)',
 'ownerJump26768>0.35',
 'immediateSupport26768>=2.0||raySupport26768>0.70',
 'strongLumaBoundary||materialColorBoundary||iir3ChromaOwnershipBoundary26768',
]: assert token in iir,token
# IIR1 stays on the inherited path: new reset can execute only for terminal chroma-only IIR3.
assert iir.count('uFilterLuma==0')==1
# The host already owns and binds the frozen restored-direction YCCD as binding 2 for both IIR calls.
host=cs[cs.index('private fun runIirRgb'):cs.index('private fun bindSabreValidity')]
assert 'bindImage(2, ownership, GLES31.GL_READ_ONLY)' in host
assert cs.count('coefficients.pass1, filterLuma = true, "IIR1"')==1
assert cs.count('coefficients.pass3, filterLuma = false, "IIR3"')==1
print('PASS 26768 VGN scope: only iirRgb shader changed; IIR1 policy + 26767 topology/slider + all non-IIR VGN owners protected')

# Exact failure-class regression: pass3 has unity DC gain yet destroys small equal-luma color when
# no boundary reset occurs. New static ownership topology resets coherent >=3-pixel material while
# isolated and 2-pixel chroma remain unprotected.
A1=(0.0331984349,0.0663968697,0.0331984349); B1=(1.0,-1.61172712,0.744520843)
A2=(0.0281187538,0.0562375076,0.0281187538); B2=(1.0,-1.36511719,0.47759226)
def dc(a,b): return sum(a)/(1.0+b[1]+b[2])
assert abs(dc(A1,B1)-1.0)<2e-6 and abs(dc(A2,B2)-1.0)<2e-6
D=[(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]
def clampi(x,n): return max(0,min(n-1,x))
def coherent(owner,r,c):
 h=len(owner); w=len(owner[0]); val=owner[r][c]; immediate=0; ray=False
 for dr,dc_ in D:
  r1,c1=clampi(r+dr,h),clampi(c+dc_,w); r2,c2=clampi(r+2*dr,h),clampi(c+2*dc_,w)
  near=owner[r1][c1]==val; far=owner[r2][c2]==val
  immediate+=int(near); ray=ray or (near and far)
 return immediate>=2 or ray
def filt_line(line,coords,owner,reset):
 def steady(v,a,b): return v*sum(a)/(1+b[1]+b[2])
 def init(v):
  y1=steady(v,A1,B1); y2=steady(y1,A2,B2); return [v,v,y1,y1],[y1,y1,y2,y2]
 def apply(s,v,a,b):
  y=a[0]*v+a[1]*s[0]+a[2]*s[1]-b[1]*s[2]-b[2]*s[3]; s[1],s[3],s[0],s[2]=s[0],s[2],v,y; return y
 s1,s2=init(line[0]); out=[]; prev=None
 for i,v in enumerate(line):
  if reset and prev is not None:
   r,c=coords[i]; pr,pc=coords[prev]
   if owner[r][c]!=owner[pr][pc] and coherent(owner,r,c) and coherent(owner,pr,pc): s1,s2=init(v)
  y=apply(s1,v,A1,B1); y=apply(s2,y,A2,B2); out.append(y); prev=i
 return out
def pass_axis(img,owner,axis,reverse,reset):
 h=len(img);w=len(img[0]); out=[[0.0]*w for _ in range(h)]
 if axis==0:
  for r in range(h):
   inds=list(range(w-1,-1,-1) if reverse else range(w)); line=[img[r][c] for c in inds]; coords=[(r,c) for c in inds]; vals=filt_line(line,coords,owner,reset)
   for c,v in zip(inds,vals): out[r][c]=v
 else:
  for c in range(w):
   inds=list(range(h-1,-1,-1) if reverse else range(h)); line=[img[r][c] for r in inds]; coords=[(r,c) for r in inds]; vals=filt_line(line,coords,owner,reset)
   for r,v in zip(inds,vals): out[r][c]=v
 return out
def run(owner,reset):
 x=[[float(v) for v in row] for row in owner]
 for axis,rev in ((0,False),(0,True),(1,False),(1,True)): x=pass_axis(x,owner,axis,rev,reset)
 return x
N=31;c=N//2
def shape(points):
 o=[[0]*N for _ in range(N)]
 for dr,dc_ in points:o[c+dr][c+dc_]=1
 return o
single=shape([(0,0)]); pair=shape([(0,0),(0,1)]); line3=shape([(0,-1),(0,0),(0,1)]); square3=shape([(r,q) for r in (-1,0,1) for q in (-1,0,1)]); diag3=shape([(-1,-1),(0,0),(1,1)])
for o in (single,pair):
 old=run(o,False); new=run(o,True); vals_old=[old[r][q] for r in range(N) for q in range(N) if o[r][q]]; vals_new=[new[r][q] for r in range(N) for q in range(N) if o[r][q]]
 assert max(vals_new)<0.06 and max(abs(x-y) for x,y in zip(vals_old,vals_new))<1e-9
for o in (line3,square3,diag3):
 old=run(o,False); new=run(o,True); vals_old=[old[r][q] for r in range(N) for q in range(N) if o[r][q]]; vals_new=[new[r][q] for r in range(N) for q in range(N) if o[r][q]]
 assert sum(vals_old)/len(vals_old)<0.20
 assert min(vals_new)>0.999
print('PASS 26768 IIR3 regression: equal-luma coherent 3px line/square/diagonal retain unity; isolated + 2px false color remain recursively cleaned')

# New color-only reset is explicitly vetoed in bright/flattened highlight pairs.
assert 'highlightPreservePermission=1.0-smoothstep(47162.88,60263.68,max(currentY,previousY))' in iir
assert 'uFilterLuma==0&&highlightPreservePermission>0.5' in iir
print('PASS 26768 inherited highlight veto preserved')
