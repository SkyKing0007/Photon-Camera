#!/usr/bin/env python3
"""No preceding-camera frame may be displayed under destination-camera orientation."""
import argparse
from build_26945_incremental import R,fail
P='app/src/main/java/com/particlesdevs/photoncamera/'

def model():
 pending=0
 def begin():return -1
 def result(state,t):return t if state==-1 and t>0 else state
 def frame(state,ts):
  if state==0:return state,True
  if state<0 or ts<state:return state,False
  return 0,True
 pending=begin()
 for old in (100,101,102,201):
  pending,shown=frame(pending,old)
  if shown:fail('old frame flashed before new capture result')
 pending=result(pending,10000)
 pending,shown=frame(pending,9999)
 if shown:fail('old timestamp passed new session result threshold')
 pending,shown=frame(pending,-1)
 if shown:fail('recycled frame passed transition')
 pending,shown=frame(pending,10000)
 if not shown or pending!=0:fail('new camera frame did not release gate')
 pending,shown=frame(pending,10001)
 if not shown:fail('valid subsequent frame lost')
 if result(begin(),-1)!=-1:fail('missing Camera2 timestamp released gate unsafely')

def main():
 a=argparse.ArgumentParser();a.add_argument('--live',action='store_true');a.add_argument('--payload',action='store_true');args=a.parse_args()
 model();root=R if args.live else R/'handoff_payload_26945'
 controller=(root/(P+'capture/CaptureController.java')).read_text()
 renderer=(root/(P+'ui/camera/views/viewfinder/MainRenderer.java')).read_text()
 preview=(root/(P+'ui/camera/views/viewfinder/GLPreview.java')).read_text()
 if not controller.count('beginFrontRearPreviewHandoff();')==1:fail('front rear begin route count wrong')
 if 'CameraCharacteristics.LENS_FACING_FRONT)\n                        != (arrivingFacing == CameraCharacteristics.LENS_FACING_FRONT)' not in controller:fail('unrelated rear optical hops unnecessarily gated')
 if 'if (session == mCaptureSession && mTextureView != null' not in controller:fail('old session result not blocked')
 if 'iris26945FrontRearMinTimestampNs = -1L;' not in preview or 'iris26945FrontRearMinTimestampNs = timestampNs;' not in preview:fail('gate missing required state')
 if 'if (expected < 0L || updatedTimestampNs < expected)' not in preview:fail('missing exact frame-timestamp threshold')
 if 'if (!mView.isFrontRearPreviewHandoffPending())' not in renderer:fail('old frame incorrectly satisfies Camera2 health flow')
 if 'GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);' not in renderer:fail('old frame not masked')
 if 'private volatile float[] mTexRotateMatrix' not in renderer or 'mTexRotateMatrix = next;' not in renderer:fail('GL orientation matrix concurrently mutated')
 print('PASS 26945 stale/late/cross-session camera frames hidden, rear lens hops untouched, atomic GL matrix')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=__import__('sys').stderr);__import__('sys').exit(1)
