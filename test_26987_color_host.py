#!/usr/bin/env python3
"""Actual Kotlin calibration contract compile + Java AST parse; shader math host property tests, not GPU validation."""
from pathlib import Path
import subprocess,tempfile,random,math
R=Path(__file__).resolve().parent;K=R/'app/src/main/java/com/hinnka/mycamera/processor';F=R/'26985_host_fixtures'
with tempfile.TemporaryDirectory() as td:
 t=Path(td);src=t/'ColorTest.kt';src.write_text('''package com.hinnka.mycamera.processor
fun main(){
 val gains=floatArrayOf(2f,1f,1f,3f);val ccm=floatArrayOf(1f,0f,0f,0f,1f,0f,0f,0f,1f)
 val a=GlesIris26983COnColorContract.freeze(gains,ccm,true)
 check(a.amazeWhiteBalance.contentEquals(floatArrayOf(2f,1f,3f)))
 gains[0]=12f;ccm[0]=12f;check(a.amazeWhiteBalance[0]==2f && a.postWbCameraToSrgb[0]==1f)
 for(v in floatArrayOf(0f,.1f,1f,2f,4.79f,6.9f,32f))for(i in 0..2)check(kotlin.math.abs(v*a.amazeWhiteBalance[i]*a.inverseWhiteBalance[i]-v)<.0001f)
 check(runCatching{GlesIris26983COnColorContract.freeze(floatArrayOf(2f,1f,1f,3f),FloatArray(9),true)}.isFailure)
 check(runCatching{GlesIris26983COnColorContract.freeze(floatArrayOf(2f,1f,1f,3f),FloatArray(9),false)}.isFailure)
 println("PASS compiled exact color snapshot ownership, invalid calibration rejection, inverse WB over extended HDR values")
}''')
 subprocess.run(['kotlinc',str(K/'GlesIris26983COnColorContract.kt'),str(src),'-include-runtime','-d',str(t/'test.jar')],check=True);subprocess.run(['java','-jar',str(t/'test.jar')],check=True)
 subprocess.run(['javac','-d',str(t),str(F/'ParseJava.java')],check=True)
 changed=(R/'26987_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines();subprocess.run(['java','-cp',str(t),'ParseJava',*[str(R/p) for p in changed if p.endswith('.java')]],check=True)
# Mirror restored exact chroma-ratio arithmetic. Check unmasked pass-through, exposure scale, neutral luma and no HDR clamp.
def luma(x):return .25*x[0]+.5*x[1]+.25*x[2]
def fix(src,guide,mask,floor=.0001):
 if mask==0:return src
 ys=max(luma(src),floor);yg=max(luma(guide),floor);ds=[(src[i]-src[1])/ys for i in (0,2)];dg=[(guide[i]-guide[1])/yg for i in (0,2)]
 rg,bg=[((1-mask)*x+mask*y)*ys for x,y in zip(ds,dg)];g=luma(src)-.25*(rg+bg);return tuple(max(0,v) for v in (g+rg,g,g+bg))
r=random.Random(26987)
for _ in range(1000):
 src=tuple(r.uniform(.4,1.4) for i in range(3));guide=tuple(r.uniform(.5,1.3) for i in range(3));mask=r.random();f=fix(src,guide,mask)
 assert fix(src,guide,0)==src and abs(luma(f)-luma(src))<1e-9
 scale=r.uniform(1,8);assert max(abs(x-scale*y) for x,y in zip(fix(tuple(v*scale for v in src),tuple(v*scale for v in guide),mask),f))<1e-8
assert fix((4.,3.,2.),(3.,3.,3.),1)==(3.,3.,3.)
print('PASS restored clip host math: unmasked identity, luma preservation and extended exposure scaling (not GPU execution)')
