#!/usr/bin/env python3
"""Mandatory pure Java host regression: 26965 bad 39.1ms startup, full-cycle verified B manual, fail-closed cases."""
import pathlib,subprocess,tempfile,sys
R=pathlib.Path(__file__).resolve().parent
P=R if '--live' in sys.argv else R/'handoff_payload_26968'
java=P/'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java'
s=java.read_text(); assert 'isVerifiedPeriodLockedBPlan26968' in s
source=r"""package com.particlesdevs.photoncamera.capture;
public final class Photon26968FlickerMathTest {
 static void yes(boolean ok,String msg) {if(!ok) throw new AssertionError(msg);}
 public static void main(String[] args) {
  Iris26909ShutterIsoMath.Plan old=Iris26909ShutterIsoMath.solveSceneLensAware(
   8_333_000L,408,50,3200,100_000L,100_000_000L,100_000_000L,23.0,3200,true,false);
  yes(old!=null && old.shutterFirstUseful,"26965 8.33ms AE baseline must produce a candidate");
  yes(!Iris26909ShutterIsoMath.isVerifiedPeriodLockedBPlan26968(old,0L),"unknown frequency must never break AUTO");
  yes(!Iris26909ShutterIsoMath.isVerifiedPeriodLockedBPlan26968(old,8_333_333L),"39ms unsnapped B manual forbidden");
  Iris26909ShutterIsoMath.Plan sixty=Iris26909ShutterIsoMath.snapVerifiedBPlan(old,
   8_333_333L,100_000L,50,3200,100_000_000L);
  yes(Iris26909ShutterIsoMath.isVerifiedPeriodLockedBPlan26968(sixty,8_333_333L),"verified 120Hz full cycle required");
  yes(sixty.shutterNs%8_333_333L==0L && sixty.shutterNs<old.shutterNs,"safe snap preserves lower shutter");
  yes(!Iris26909ShutterIsoMath.isVerifiedPeriodLockedBPlan26968(sixty,10_000_000L),"cross-frequency manual forbidden");
  yes(!Iris26909ShutterIsoMath.isVerifiedPeriodLockedBPlan26968(sixty,9_000_000L),"PWM unknown frequency forbidden");
  Iris26909ShutterIsoMath.Plan fifty=Iris26909ShutterIsoMath.snapVerifiedBPlan(old,
   10_000_000L,100_000L,50,3200,100_000_000L);
  yes(Iris26909ShutterIsoMath.isVerifiedPeriodLockedBPlan26968(fifty,10_000_000L),"verified 100Hz full cycle required");
  Iris26909ShutterIsoMath.Plan impossible=Iris26909ShutterIsoMath.snapVerifiedBPlan(old,
   8_333_333L,100_000L,50,70,100_000_000L);
  yes(!Iris26909ShutterIsoMath.isVerifiedPeriodLockedBPlan26968(impossible,8_333_333L),"out-of-ISO safe period must not be guessed");
  yes(Iris26909ShutterIsoMath.verifiedMainsPeriodNs(1, 8_333_333L,1.)==8_333_333L,"physical 120Hz skew");
  yes(Iris26909ShutterIsoMath.verifiedMainsPeriodNs(1,10_000_000L,1.)==10_000_000L,"physical 100Hz skew");
  yes(Iris26909ShutterIsoMath.verifiedMainsPeriodNs(1,20_000_000L,1.)==0L,"do not guess 50Hz from raw period");
  yes(Iris26909ShutterIsoMath.verifiedMainsPeriodNs(1,0L,1.)==0L,"no sensor skew no confidence");
  yes(Iris26909ShutterIsoMath.verifiedMainsPeriodNs(1,8_333_333L,0.5)==0L,"incomplete RAW span invalid");
  System.out.println("PASS 26968 actual javac/java 26965 observed manual 39.1ms blocked unless exact verified 100/120Hz, unknown/PWM/unsnappable safe fallback");
 }
}"""
with tempfile.TemporaryDirectory(prefix='ph26968_javac_') as td:
 p=pathlib.Path(td);out=p/'Photon26968FlickerMathTest.java';out.write_text(source)
 subprocess.run(['javac','-encoding','UTF-8','-d',str(p),str(java),str(out)],check=True,stdout=subprocess.DEVNULL)
 subprocess.run(['java','-ea','-cp',str(p),'com.particlesdevs.photoncamera.capture.Photon26968FlickerMathTest'],check=True)
