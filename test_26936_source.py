#!/usr/bin/env python3
"""Complete 26935-successful source ownership and precise 26936 7-path scope assertions."""
import re,sys
from build_26936_incremental import R,scope,sha,fail,exact

def main():
 changed,added,old,new=scope()
 if '--live' in sys.argv:
  root=R
  exact(R,'26936_EXPECTED_FULL_APP.sha256','actual live 26936 2050 source with 2043 immutable')
 else:
  root=R/'handoff_payload_26936'
  for path in changed:
   if sha(root/path)!=new[path]:fail('stage runtime bytes mismatched '+path)
 assert not added
 ver=(root/'app/version.properties').read_text()
 for key in ('VERSION_BUILD=26936','VERSION_NAME=0.9726936'):
  if key not in ver:fail('new version missing '+key)
 shader=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt').read_text()
 for flag in ('IRIS_26936_B_SRON_SENSOR_GUIDED_WHITE_ROLLOFF','uNativeSensorClip','uBayerPattern','uAmazeWb',
  'uInverseAmazeWb','float balanced=smoothstep','float allColors=min(phaseSupport.r',
  'float fade=clamp(max(visibleShoulder,sensorFade)','oRgb=vec4(corrected*uInverseAmazeWb,original.a);'):
  if flag not in shader:fail('B ON original physical clipping and new smooth color-preserving fade absent '+flag)
 for flag in ('whiteCurve=smoothstep(vec3(0.70)','visualFade=max(whiteCurve.r'):
  if flag in shader:fail('over-aggressive 26934 single-channel bleaching returned '+flag)
 motion=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 p3=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java').read_text()
 for s in (motion,p3):
  if 'IRIS_26936_B_OFF_SAT_102_ONLY' not in s or '!'+ 'params.motionV2SuperResOutputEnabled' not in s and '!basePipeline.mParameters.motionV2SuperResOutputEnabled' not in s:
   fail('B OFF saturation not isolated to SR OFF')
  if '!'+ 'params.irisNightActive' not in s and '!basePipeline.mParameters.irisNightActive' not in s:fail('Night saturation isolation absent')
  if '1.02f' not in s or '1.07f' not in s and 'IRIS_26824_MOTION_SATURATION_SCALE' not in s:fail('B OFF 1.02 or untouched other modes 1.07 absent')
 renderer=(root/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_text()
 for flag in ('IRIS_26936_B_ON_NONBLOCKING_PROBE','GLES30.glFenceSync','GLES30.glClientWaitSync','GLES30.glMapBufferRange',
  'GLES30.GL_PIXEL_PACK_BUFFER','GLES30.glReadPixels','GLES20.glFlush()',
  'currentTimestamp - ownedTimestamp <= 250_000_000L','ownedTimestamp','mIris26872Stripe.params()[3] > 0.0f',
  'iris26872Controller.iris26911DarkPreviewEvidence()','iris26872Probe(iris26553FrameTimestamp);',
  'iris26936DisposeAsyncProbe();','mIris26936Backpressure'):
  if flag not in renderer:fail('GL-context owned preview async safety or low-light/flicker protected fallback absent '+flag)
 if 'GLES20.glFinish(' in renderer or 'GLES30.glFinish(' in renderer:fail('preview introduced blocking glFinish')
 gl=(root/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java').read_text()
 for flag in ('EGL_IMG_context_priority','EGL_CONTEXT_PRIORITY_HIGH_IMG','egl.eglCreateContext','EGL10.EGL_NO_CONTEXT','legacyFallback=true'):
  if flag not in gl:fail('preview EGL optional high-priority hint and fallback absent '+flag)
 cap=(root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
 for flag in ('IRIS_26936_B_ON_CPU_QOS','Process.myTid()','Process.getThreadPriority','Process.setThreadPriority',
  'iris26935Relay != null','iris26936PriorityChanged','iris26936OriginalNice'):
  if flag not in cap:fail('B ON only reversible CPU QoS missing '+flag)
 for f in ('app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnSession.java',
  'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnProcessingRelay.java',
  'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
  'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java',
  'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'):
  if f not in old or old[f]!=new[f] or f in changed:fail('protected LKR 3x2 / shutter / 15 RAW path changed '+f)
 # Original shader file specific to B ON, and exact B OFF sources are the ONLY other color changes.
 if sum('GlesIris26932LkrSmoothWhite.kt' in x for x in changed)!=1:fail('shader owner changed')
 print('PASS 26936 explicit seven changed, zero added, 2043 protected, 15-frame LKR/shutter, B OFF SDR/UHDR saturation 1.02 only, preview QoS fallback')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
