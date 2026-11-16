#!/usr/bin/env python3
"""26946 front-only actual final-shader gain geometry, rear/Night/preview invariance."""
import argparse,sys
from build_26946_incremental import R,REQUIRED,scope,sha,fail,exact
P='app/src/main/java/com/particlesdevs/photoncamera/'
def main():
 a=argparse.ArgumentParser();a.add_argument('--payload',action='store_true');a.add_argument('--live',action='store_true');a=a.parse_args()
 ch,old,new=scope()
 if ch!=REQUIRED:fail('front-only runtime allowlist changed')
 root=R if a.live else R/'handoff_payload_26946'
 def read(p):return (root/p).read_text()
 uhdr=read(P+'processing/ultrahdr/MotionV2UltraHdr.java')
 post=read(P+'processing/opengl/postpipeline/PostPipeline.java')
 version=read('app/version.properties')
 for snippet in (
 'final boolean mirrorFinalY = (rotation == 0 || rotation == 180);',
 'frontFinalMirror.setScale(mirrorFinalY ? 1.0f : -1.0f,',
 'mirrorFinalY ? -1.0f : 1.0f);',
 'final int top = gainHeight - height;',
 'final int left = (rotation == 180 || rotation == 270)',
 'shaderCropHighY=true shaderCropHighXAt180or270=true',
 'if (motionCapacityAuthority && mirrorFinalSdr)',
 'new Gainmap(oriented)',
 'sdrBase.setGainmap(gainmap)',
 'return attachMotion(sdrBase, unrotatedGainMap, rotationDegrees, maxRatio,',
 'fullHdrDisplayRatio, false);',
 'frozenNightDisplayRatio, false, false, 0, 0, 0, 0);'):
  if snippet not in uhdr:fail('missing real front UHDR pixel geometry or protected Night/rear API: '+snippet)
 if uhdr.count('if (motionCapacityAuthority && mirrorFinalSdr)')!=1:fail('front-only condition duplicated/removed')
 if 'frontFinalMirror.setScale(-1.0f, 1.0f)' in uhdr:fail('old 26945 unconditional final-X mirror resurrected')
 if post.count('mParameters.rawSize.x, mParameters.rawSize.y,\n                    cropSize.x, cropSize.y')!=1:fail('exact SDR crop not passed into front gain')
 if 'mParameters.mirror,' not in post:fail('front-camera gate missing')
 if 'VERSION_BUILD=26946' not in version or 'VERSION_NAME=0.9726946' not in version:fail('version not 26946')
 if any('/cpp/' in p or '/assets/' in p or '/vendor/' in p or '/jniLibs/' in p for p in ch):fail('rear/native/shader/vendor source altered')
 for p in ch:
  if sha(root/p)!=new[p]:fail('new runtime source bytes altered '+p)
 if a.live:exact(R,'26946_EXPECTED_FULL_APP.sha256','26946 live full source source-protected')
 print('PASS 26946 exact front-only rotation/crop changes, rear/Night/26945 preview unchanged, full-source protection')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
