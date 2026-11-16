#!/usr/bin/env python3
"""Bounded 26945 front-only source, dormant source protection and parity contracts."""
import argparse,pathlib,sys
from build_26945_incremental import R,REQUIRED,scope,sha,parse,fail
P='app/src/main/java/com/particlesdevs/photoncamera/'
def main():
 a=argparse.ArgumentParser();a.add_argument('--live',action='store_true');a.add_argument('--payload',action='store_true');args=a.parse_args()
 ch,old,new=scope();assert ch==REQUIRED
 root=R if args.live else R/'handoff_payload_26945'
 def read(short):
  path=root/(P+short)
  if not path.is_file():fail('missing 26945 source '+str(path))
  return path.read_text()
 post=read('processing/opengl/postpipeline/PostPipeline.java')
 uhdr=read('processing/ultrahdr/MotionV2UltraHdr.java')
 controller=read('capture/CaptureController.java')
 renderer=read('ui/camera/views/viewfinder/MainRenderer.java')
 preview=read('ui/camera/views/viewfinder/GLPreview.java')
 version=(root/'app/version.properties').read_text()
 if 'VERSION_BUILD=26945' not in version or 'VERSION_NAME=0.9726945' not in version:fail('wrong new version')
 if post.count('motionV2GainMapFullHdrDisplayRatio,\n                    mParameters.mirror')!=1:fail('front-specific final mirror not routed')
 if uhdr.count('if (motionCapacityAuthority && mirrorFinalSdr)')!=1:fail('rear-only front mirror containment missing')
 if 'return attachMotion(sdrBase, unrotatedGainMap, rotationDegrees, maxRatio,\n                fullHdrDisplayRatio, false);' not in uhdr:fail('old rear Motion UHDR overload changed')
 if 'frozenNightDisplayRatio, false, false);' not in uhdr:fail('Night original gain behavior changed')
 if 'frontFinalMirror.setScale(-1.0f, 1.0f)' not in uhdr:fail('wrong gainmap mirrored final-axis')
 if 'if (departingFacing != null && arrivingFacing != null' not in controller or 'beginFrontRearPreviewHandoff()' not in controller:fail('front-rear route gate missing')
 if 'session == mCaptureSession' not in controller or 'confirmFrontRearPreviewResult' not in controller:fail('old camera result could release preview')
 if 'mTextureView.setOrientation(mSensorOrientation+90);' not in controller:fail('original preview orientation policy removed')
 if 'private volatile float[] mTexRotateMatrix' not in renderer or 'float[] next = new float[16]' not in renderer:fail('matrix atomics not enforced')
 if 'if (!mView.shouldPresentFrontRearPreviewFrame(iris26553FrameTimestamp))' not in renderer:fail('old preview frame not blocked before render')
 if renderer.find('if (!mView.shouldPresentFrontRearPreviewFrame(') > renderer.find('GLES20.glUniformMatrix4fv(uTexRotateMatrix, 1, false, mTexRotateMatrix, 0);'):fail('orientation gate occurs after stale draw')
 if 'iris26945FrontRearMinTimestampNs = -1L;' not in preview or 'updatedTimestampNs < expected' not in preview:fail('preview frame timestamps are not sensor-owned')
 if 'iris26945FrontRearMinTimestampNs = 0L;' not in preview:fail('new preview cannot release')
 for path in ch:
  if sha(root/path)!=new[path]:fail('overlay/current runtime bytes changed '+path)
 assert all('/cpp/' not in p and '/assets/' not in p and '/vendor/' not in p and '/jniLibs/' not in p for p in ch)
 if args.live:
  # Full source accounting, including all 2048 protected, not just six changed paths.
  from build_26945_incremental import exact
  exact(R,'26945_EXPECTED_FULL_APP.sha256','strict unchanged rear/native/shader full-source protection')
 print('PASS 26945 front-only gain/preview behavior, successful 26941 SDR body untouched, rear processing protected')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
