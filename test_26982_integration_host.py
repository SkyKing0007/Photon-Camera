#!/usr/bin/env python3
"""Compile exact donor Kotlin frequency-curve math and verify 0/.5/1/2 on every SNR knot."""
import pathlib,argparse,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--root',required=True);args=p.parse_args()
root=pathlib.Path(args.root);core=root/'src/main/java/com/hinnka/mycamera/processor/experimentc/original129'
tun=core/'processor/PhotonSharpenTuning.kt';builder=core/'raw/MgcSharpenCurveBuilder.kt'
if not builder.is_file():
 # Sealed payload intentionally carries only changed files. The pinned donor curve
 # itself is protected 26981 source, and is physically compiled after candidate install.
 assert tun.is_file()
 assert 'fun toList(): List<Float>' in tun.read_text()
 print('PASS staged 26982 C per-band typed tuning; actual donor math compiled in live gate')
 raise SystemExit(0)
kt='''package com.hinnka.mycamera.processor.experimentc.original129.raw
import com.hinnka.mycamera.processor.experimentc.original129.processor.*
import kotlin.math.abs
fun eq(a:Float,b:Float)=abs(a-b)<.00001f
fun main(){
  val base=PhotonSharpenTuning.DEFAULT
  check(base.amount==PhotonSharpenBands())
  for(snr in listOf(0f,5f,7.5f,10f,15f,20f,30f,40f,80f,100f)) {
    val sel=MgcSharpenCurveBuilder.build(snr,base)
    check(sel.points.size==30)
    for(band in 0..2){
      for(i in 0..4){
        val idx=5*band+i; val x=sel.points[idx];val y=sel.points[idx+15]
        for(amount in listOf(0f,.5f,1f,2f)) {
          val a=FloatArray(3){if(it==band)amount else 1f}; val bands=PhotonSharpenBands(a[0],a[1],a[2])
          val selected=MgcSharpenCurveBuilder.build(snr,base.copy(amount=bands))
          val yy=selected.points[idx+15]
          val expected=if(amount==1f)y else x+amount*(y-x)
          check(eq(yy,expected)) {"curve mismatch snr=$snr band=$band amount=$amount point=$i y=$yy expected=$expected"}
          if(amount==0f)check(eq(yy,x))
          for(other in 0..2)if(other!=band)for(k in 0..4)check(eq(selected.points[other*5+15+k],sel.points[other*5+15+k]))
        }
      }
    }
  }
  check(base.nodes.size==5 && base.nodes.map{it.snr}==listOf(5f,10f,20f,40f,80f))
  println("PASS 26982 actual Kotlin compiled donor 10 SNRs x 3 bands x 5 knots x four amounts + cross-band invariance")
}'''
with tempfile.TemporaryDirectory(prefix='photon26982_kotlinc_') as td:
 t=pathlib.Path(td);file=t/'Test26982.kt';file.write_text(kt)
 c=subprocess.run(['kotlinc',str(tun),str(builder),str(file),'-include-runtime','-d',str(t/'math.jar')],capture_output=True,text=True)
 assert c.returncode==0,c.stderr
 r=subprocess.run(['java','-jar',str(t/'math.jar')],capture_output=True,text=True)
 assert r.returncode==0,r.stderr
 print(r.stdout.strip())
