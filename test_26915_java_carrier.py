#!/usr/bin/env python3
"""Compile the actual modified Android Java GPU carrier against type-only
Android API stubs, protecting Java-to-Kotlin-to-JNI function signatures.
These stubs are NOT runtime replacements; mandatory real Android Java+NDK
compilation remains in unchanged Gradle :app:assembleDebug Actions stage.
"""
from pathlib import Path
import subprocess,tempfile,shutil,sys
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
P=(R if (R/'app/src').is_dir() else R/'candidate_26915') if LIVE else R/'handoff_payload_26915'
real=P/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2SharedRgba16fCarrier.java'
assert real.is_file()
with tempfile.TemporaryDirectory(prefix='26915_java_realcarrier_') as td:
 t=Path(td)
 files={
 'android/hardware/HardwareBuffer.java':'''package android.hardware; public final class HardwareBuffer implements AutoCloseable {
 public static final int RGBA_FP16=22; public static final long USAGE_GPU_SAMPLED_IMAGE=1L,
 USAGE_GPU_COLOR_OUTPUT=2L,USAGE_CPU_READ_OFTEN=4L,USAGE_CPU_WRITE_OFTEN=8L;
 public static boolean isSupported(int w,int h,int f,int l,long u){return true;}
 public static HardwareBuffer create(int w,int h,int f,int l,long u){return new HardwareBuffer();}
 @Override public void close(){} }''',
 'android/os/Build.java':'''package android.os;public final class Build {public static final class VERSION {
 public static int SDK_INT=35;}}''',
 'com/particlesdevs/photoncamera/util/Allocator.java':'''package com.particlesdevs.photoncamera.util;
 public final class Allocator {public static java.nio.ByteBuffer allocateAndCopy(int n,java.nio.ByteBuffer b,int i){return b;}}''',
 'com/particlesdevs/photoncamera/util/Log.java':'''package com.particlesdevs.photoncamera.util;
 public final class Log {public static void w(String t,String s){}public static void e(String t,String s){}}''',
 }
 for name,s in files.items():
  f=t/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s)
 args=['javac','--release','17','-d',str(t/'classes'),str(real)]+[str(t/k) for k in files]
 subprocess.run(args,check=True)
 print('PASS 26915 complete production Java HardwareBuffer carrier javac type check and JNI declaration API')
