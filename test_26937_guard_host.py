#!/usr/bin/env python3
"""Host source ownership plus actual Kotlin compiler front-end for two changed shaders.
Complete Android Kotlin/Java linking and NDK/GLSL assemble stay mandatory in Actions.
"""
import shutil,subprocess,sys,tempfile
from pathlib import Path
from build_26937_incremental import R,scope,fail,sha

def main():
 ch,ad,old,new=scope()
 payload=R if '--live' in sys.argv else R/'handoff_payload_26937'
 root='app/src/main/java/com/hinnka/mycamera/processor/'
 shaders=[payload/(root+n) for n in ('GlesIris26932LkrSmoothWhite.kt','GlesIris26932RawLensMedian.kt')]
 for p in shaders:
  if not p.is_file():fail('shader source for real Kotlin compiler missing '+str(p))
  if p.read_text().count('"""')!=2:fail('bad GLSL string Kotlin delimiter')
 # CLI Kotlin compiler on the ACTUAL runtime files, not a mock parser or a retyped translation.
 exe=shutil.which('kotlinc')
 if exe:
  with tempfile.TemporaryDirectory(prefix='26937_kotlin_') as t:
   cmd=[exe,'-jvm-target','17','-d',str(Path(t)/'classes')]+list(map(str,shaders))
   p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90)
   if p.returncode:fail('real Kotlin compiler cannot parse current shader owners: '+p.stderr[-1100:])
  print('PASS actual Kotlin 17 compiler frontend shader owners')
 else:
  # The original Actions Kotlin compiler remains mandatory, and its absence
  # here is explicitly not a compiler PASS.
  print('NOT RUN local Kotlin frontend (runner full Android Kotlin required)')
 for path in (
   'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
   'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnSession.java',
   'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
   'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
   'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java'):
  if old[path]!=new[path]:fail('original 26936 shutter/preview/B OFF saturation source mutated '+path)
 print('PASS 26937 source safeguards; original 26936 preview/shutter/B OFF saturation byte-identical')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
