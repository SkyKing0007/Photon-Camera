#!/usr/bin/env python3
"""Compile actual B frozen shutter+ISO helper and the original 26905 selector
under a lean javac harness. Covers the 26914 1/16.6s vs 1/100s HAL repro.
Not a substitute for Actions project Java/NDK/Gradle gates.
"""
from pathlib import Path
import subprocess,tempfile,sys
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
P=(R if (R/'app/src').is_dir() else R/'candidate_26915') if LIVE else R/'handoff_payload_26915'
source=(P/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
helper=P/'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26910CaptureSafety.java'
assert helper.is_file()
assert source.count('Iris26910CaptureSafety.frozenNormalPairMatches(')==1
assert 'MOTION_26486_EXPOSURE_HALF_WINDOW_EV,\n                frozenExperimentB' in source
assert 'plan.normalTargetIso,\n                        plan.iris26906BOffAllNormal' in source
assert 'final boolean iris26593LongBudgetAllows = iris26593TotalTarget >= 2 && !iris26905BOffAllNormal' in source
assert 'iris26905BOffNormalOnly(\n                iris26856FrozenExperiment, mMotion26575SuperResAtShutter)' in source
start=source.index('    private static boolean iris26905BOffNormalOnly(')
end=source.index('\n    /* IRIS_26912_SHUTTER_FIRST_MANUAL_B',start)
selector=source[start:end]
assert selector.count('private static boolean')==1
stub='''package com.particlesdevs.photoncamera.settings;
public final class Iris26856ABSettings {
 public enum Mode { ORIGINAL_26850, AMAZE_26855, OTHER }
}
'''
run='''public final class Test26915 {
'''+selector+'''
 public static void main(String[] args) {
  var B=com.particlesdevs.photoncamera.settings.Iris26856ABSettings.Mode.AMAZE_26855;
  var A=com.particlesdevs.photoncamera.settings.Iris26856ABSettings.Mode.ORIGINAL_26850;
  if(!iris26905BOffNormalOnly(B,true)||!iris26905BOffNormalOnly(B,false))throw new AssertionError("B SR ON/OFF must be NORMAL-only");
  if(iris26905BOffNormalOnly(A,true)||iris26905BOffNormalOnly(A,false))throw new AssertionError("A protected");
  // Original 26914 tele repro: energy similar but physical shutter/ISO mismatched.
  if(com.particlesdevs.photoncamera.capture.Iris26910CaptureSafety.frozenNormalPairMatches(10_000_000,1464,60_000_000,240,0.15,true))throw new AssertionError("mismatched exposure mistakenly accepted");
  if(!com.particlesdevs.photoncamera.capture.Iris26910CaptureSafety.frozenNormalPairMatches(10_000_000,1464,60_000_000,240,0.15,false))throw new AssertionError("A energy-only changed");
  if(!com.particlesdevs.photoncamera.capture.Iris26910CaptureSafety.frozenNormalPairMatches(60_000_000,240,60_000_000,240,0.15,true))throw new AssertionError("exact frame rejected");
  if(!com.particlesdevs.photoncamera.capture.Iris26910CaptureSafety.frozenNormalPairMatches(61_000_000,238,60_000_000,240,0.15,true))throw new AssertionError("small real sensor variation rejected");
  if(com.particlesdevs.photoncamera.capture.Iris26910CaptureSafety.frozenNormalPairMatches(0,240,60_000_000,240,0.15,true))throw new AssertionError("zero admitted");
  if(com.particlesdevs.photoncamera.capture.Iris26910CaptureSafety.frozenNormalPairMatches(60_000_000,240,60_000_000,240,Double.NaN,true))throw new AssertionError("invalid window accepted");
  // Selector allocates zero auxiliary slots for B even when SR ON.
  for(boolean sr:new boolean[]{false,true}) {
   int requested=8;int aux=(requested>=2&&!iris26905BOffNormalOnly(B,sr))?1:0;
   if(aux!=0||requested-aux!=8)throw new AssertionError("B lost NORMAL contributor");
  }
  System.out.println("PASS 26915 original Java helper + real CaptureController B selector, 8/8 NORMAL, bad HAL pair rejection, A unchanged");
 }
}
'''
with tempfile.TemporaryDirectory() as td:
 t=Path(td);(t/'src/com/particlesdevs/photoncamera/settings').mkdir(parents=True)
 (t/'src/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java').write_text(stub)
 (t/'src/Test26915.java').write_text(run)
 args=['javac','--release','17','-d',str(t/'classes'),str(helper),str(t/'src/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java'),str(t/'src/Test26915.java')]
 subprocess.run(args,check=True)
 subprocess.run(['java','-cp',str(t/'classes'),'Test26915'],check=True)
