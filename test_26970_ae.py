#!/usr/bin/env python3
"""Actual javac/java 26970 solver test, and preview/rolling-flicker policy guards."""
from pathlib import Path
import tempfile,subprocess,sys
R=Path(__file__).resolve().parent;P=R if '--live' in sys.argv else R/'handoff_payload_26970'
j=P/'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java'
src=r"""package com.particlesdevs.photoncamera.capture;
public final class Photon26970AutoExposureTest {
 static void yes(boolean x,String msg){if(!x)throw new AssertionError(msg);}
 static Iris26909ShutterIsoMath.Plan plan(double light,long period,boolean moving) {
  return Iris26909ShutterIsoMath.solve26970(30_303_030L,12800,50,16000,
   100_000L,100_000_000L,100_000_000L,34.0,true,moving,(float)light,0.001f,period);
 }
 public static void main(String[] args) {
  yes(Iris26909ShutterIsoMath.MAX_26970_AUTO_SHUTTER_NS==71_428_571L,"1/14s cap");
  Iris26909ShutterIsoMath.Plan dark=plan(0.04,0L,false), bright=plan(0.30,0L,false);
  yes(dark!=null && bright!=null,"both scenes compute");
  yes(dark.shutterNs<=71_428_571L && bright.shutterNs<=71_428_571L,"cannot exceed 1/14 cap");
  yes(dark.shutterNs>30_303_030L && bright.shutterNs>30_303_030L,"lower ISO is possible");
  yes(dark.iso<12800 && bright.iso<12800,"noise priority");
  yes(dark.iso>0 && bright.iso>0,"positive ISO");
  for(long ns:new long[]{10_000_000L,8_333_333L}) {
   Iris26909ShutterIsoMath.Plan f=plan(0.05,ns,false);
   yes(f!=null && f.shutterNs%ns==0L,"complete mains period");
   yes(Iris26909ShutterIsoMath.isVerifiedPeriodLockedBPlan26968(f,ns),"guard reuse");
  }
  yes(Iris26909ShutterIsoMath.solve26970(0,100,50,16000,100_000,100_000_000,100_000_000,35,false,false,.1f,0,0)==null,"invalid HAL shutter fails closed");
  yes(Iris26909ShutterIsoMath.solve26970(100_000_000L,16000,50,16000,100_000,100_000_000,100_000_000,35,false,false,.1f,0,0)==null,"energy beyond 1/14 maximum fails closed");
  yes(!Iris26909ShutterIsoMath.rawSceneRemeter26970(.04f,.2f,0,2),"3 raw observations required");
  yes(Iris26909ShutterIsoMath.rawSceneRemeter26970(.04f,.2f,0,3),"3 raw observations can remeter");
  yes(!Iris26909ShutterIsoMath.rawSceneRemeter26970(.04f,.04f,0,3),"do not remeter unchanged scene");
  System.out.println("PASS 26970 actual javac/java 1/14 cap, real shutter/ISO candidate, mains 100/120Hz and fail closed");
 }
}"""
with tempfile.TemporaryDirectory(prefix='ph26970_ae_') as d:
 p=Path(d);s=p/'Photon26970AutoExposureTest.java';s.write_text(src)
 subprocess.run(['javac','-encoding','UTF-8','-d',d,str(j),str(s)],check=True)
 subprocess.run(['java','-ea','-cp',d,'com.particlesdevs.photoncamera.capture.Photon26970AutoExposureTest'],check=True)
