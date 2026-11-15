#!/usr/bin/env python3
"""Real Kotlin 17 front-end on actual changed shader; full project compiler mandatory in Actions."""
import shutil,subprocess,sys,tempfile
from pathlib import Path
from build_26939_incremental import R,scope,fail

def main():
 changed,added,old,new=scope()
 shader=(R if '--live' in sys.argv else R/'handoff_payload_26939')/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt'
 if not shader.is_file() or shader.read_text().count('"""')!=2:fail('actual current Kotlin shader missing')
 exe=shutil.which('kotlinc')
 if exe:
  with tempfile.TemporaryDirectory(prefix='26939_kotlin_') as t:
   p=subprocess.run([exe,'-jvm-target','17','-d',str(Path(t)/'classes'),str(shader)],capture_output=True,text=True,timeout=90)
   if p.returncode:fail('real current Kotlin 17 compiler failed '+p.stderr[-1100:])
  print('PASS original actual Kotlin shader source real Kotlin JVM 17 compile')
 else:print('NOT RUN host Kotlin (actual project Kotlin/Java compile remains mandatory Actions)')
 for k in ('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
           'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
           'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'):
  if old[k]!=new[k]:fail('26938 already successful shutter/preview/SR OFF source changed '+k)
 print('PASS 26939 exact protected shutter/preview/SR OFF source bytes')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26939 BLOCKED:',str(e),file=sys.stderr);sys.exit(1)
