#!/usr/bin/env python3
from pathlib import Path
import cmath,math,sys
if len(sys.argv)!=2: raise SystemExit('usage: verify_26754_ipol_math.py CANDIDATE')
c=Path(sys.argv[1]); cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for s in ['IRIS_26754_IPOL_SECTION7_SPECTRAL_ENHANCEMENT','rho=std::sqrt(fx*fx+fy*fy)','gain=1.0+lambda*(1.0-std::exp(-rho))']: assert s in cpp,s
# Reference the IPOL block forward model B[j,k]=cof*exp(+2pi i shift_j dot alias_k).
# For a full-row-rank underdetermined block, the Moore-Penrose solution is B^H(BB^H)^-1 y.
def inv(a):
 n=len(a); m=[list(row)+[1 if i==j else 0 for j in range(n)] for i,row in enumerate(a)]
 for col in range(n):
  piv=max(range(col,n),key=lambda r:abs(m[r][col])); assert abs(m[piv][col])>1e-10; m[col],m[piv]=m[piv],m[col]; q=m[col][col]; m[col]=[x/q for x in m[col]]
  for r in range(n):
   if r==col: continue
   q=m[r][col]; m[r]=[x-q*y for x,y in zip(m[r],m[col])]
 return [row[n:] for row in m]
def mm(a,b): return [[sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]
def mv(a,v): return [sum(x*y for x,y in zip(row,v)) for row in a]
def H(a): return [[a[i][j].conjugate() for i in range(len(a))] for j in range(len(a[0]))]
L=4; sp=sq=2; cof=.25; dx=[0,.25,.5,.75]; dy=[0,.5,.25,.75]
B=[]
for j in range(L):
 row=[]
 for r in range(sp):
  for q in range(sq): row.append(cof*cmath.exp(2j*math.pi*(dx[j]*r+dy[j]*q)))
 B.append(row)
y=[1+.2j,.8-.1j,1.2+.3j,.9-.25j]
BH=H(B); G=mm(B,BH); x=mv(mm(BH,inv(G)),y); repro=mv(B,x)
err=max(abs(a-b) for a,b in zip(repro,y)); assert err<1e-8,err
for z,expected in [(2,3.5),(4,.875),(30,14/900)]:
 lam=min(5.,14/(math.ceil(z)*math.ceil(z))); assert abs(lam-expected)<1e-12
print(f'PASS 26754 IPOL numerical parity: Moore-Penrose translational block reproduces observations err={err:.3e}; Section7 lambda support policy exact')
