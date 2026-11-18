#!/usr/bin/env python3
"""26955 minimal scope audit: byte-exact 26954 rendering except requested +0.4 EV curve."""
import re,sys,hashlib
from pathlib import Path
from build_26955_incremental import R,fail,scope,exact
RENDER='app/src/main/assets/shaders/motionv2/render.glsl'
VER='app/version.properties'
GAIN='app/src/main/assets/shaders/motionv2/gainmap.glsl'
JAVA='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
ORIGINAL_RENDER_SHA='94ba7ff65284fcf6dbc01820edb70453dfe6b09908444863c21bd8cc45b0a1be'
ORIGINAL_GAIN_SHA='786cf74c84984c7f3a8331f5a8d7aa31104bd5209d36abc6f91df28742b8aada'
ORIGINAL_JAVA_SHA='11eca0ca754d107af2b5156429c07e517b69c8289ebd9315c49f35406fdd9405'
SCALE='1.3195079107728942'
CURVE='mappedPeak=((-0.2530536003804941*x-0.06645431039239985)*x+1.1545694219262823)*x+0.16493848884661177;'
def sha(b):return hashlib.sha256(b).hexdigest()
def validate():
 changed,added,old,new=scope()
 assert changed=={RENDER,VER} and not added
 assert old[RENDER]==ORIGINAL_RENDER_SHA and old[GAIN]==new[GAIN]==ORIGINAL_GAIN_SHA
 assert old[JAVA]==new[JAVA]==ORIGINAL_JAVA_SHA
 root=R if '--live' in sys.argv else R/'handoff_payload_26955'
 if '--live' in sys.argv:exact(root,'26955_EXPECTED_FULL_APP.sha256','actual 26955 2053 protected real source')
 r=(root/RENDER).read_text();v=(root/VER).read_text()
 for path,t in ((RENDER,r),(VER,v)):
  if sha(t.encode())!=new[path]:fail('source payload not exact verified compiled 26955 candidate '+path)
 if v.count('VERSION_BUILD=26955')!=1 or v.count('VERSION_NAME=0.9726955')!=1:fail('wrong version')
 for text in ('const float iris26954SdrExposureScale='+SCALE+';',CURVE,'if(peak<=0.125)',
              'float x=clamp((peak-0.125)/0.875,0.0,1.0);','float uniformScale=mappedPeak/max(peak,1.0e-6);',
              'linearSrgb=unexposed*uniformScale;'):
  if r.count(text)!=1:fail('current exposure diverged or duplicated '+text)
 if 'const float iris26954SdrExposureScale=2.0;' in r or 'mappedPeak=((0.5125*x-1.5125)*x+1.75)*x+0.25;' in r:fail('stale 26954 +1EV exposure remains')
 # Prove this is EXACTLY the successful 26954 shader with only new exposure constants,
 # dedicated comments, and no B ON/Night/A native/SDR/UHDR changes.
 reverted=r.replace('const float iris26954SdrExposureScale='+SCALE+';', 'const float iris26954SdrExposureScale=2.0;')
 reverted=reverted.replace(CURVE,'mappedPeak=((0.5125*x-1.5125)*x+1.75)*x+0.25;')
 reverted=reverted.replace('fixed +0.4 EV (approximately 1.32x) exposure step. Finite SDR cannot boost white;',
                           'fixed +1 EV (2x) presentation step. Finite SDR cannot double white;')
 reverted=reverted.replace('rolls the +0.4 EV exposure off to white without hard clipping.',
                           'rolls the 2x exposure off to white without hard 0.5->1.0 clipping.')
 reverted=reverted.replace('y(.125)=.164938489, dy/dpeak=1.31950791;', 'y(.125)=.25, dy/dpeak=2.0;')
 if sha(reverted.encode())!=ORIGINAL_RENDER_SHA:fail('unapproved or stale shader differences outside exactly global EV constant and shoulder')
 if r.count('uniform int iris26954BOffNight26940Sdr;')!=1 or r.count('if(iris26954BOffNight26940Sdr!=0)')!=3:fail('frozen B OFF all zoom/Night gate lost')
 if r.count('else if(iris26948BUniversalSdrEnabled!=0)')!=2:fail('B ON original protected route changed')
 if 'if(iris26954BOffNight26940Sdr!=0 || iris26948BUniversalSdrEnabled==0' not in r:fail('26952 rim guard on B OFF restored accidentally')
 if r.find('linearSrgb=iris26638UserSaturation(')>r.find('linearSrgb=unexposed*uniformScale;') or r.find('linearSrgb=unexposed*uniformScale;')>r.find('Output=clamp('):fail('global EV incorrectly inserted before 26940 color or after transfer')
 if '--live' in sys.argv:
  g=(root/GAIN).read_bytes();j=(root/JAVA).read_text()
  if sha(g)!=ORIGINAL_GAIN_SHA or sha(j.encode())!=ORIGINAL_JAVA_SHA:fail('gainmap/Java changed from published 26954 unexpectedly')
  if 'float hdrIntentY=sdr+matchedIntentDelta;' not in g.decode():fail('26940 original UHDR delta absent')
  if 'ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);' not in g.decode():fail('gainmap not normalized by new completed SDR')
  if j.count('glProg.setVar("iris26954BOffNight26940Sdr",')!=2:fail('render/gainmap uniform parity missing')
  if not all(q in j.split('final boolean iris26954BOffNight26940Sdr =',1)[1].split(';',1)[0] for q in
             ('iris26906ExperimentBSelected','!basePipeline.mParameters.motionV2SuperResOutputEnabled','motionV2Active','iris26903NightB')):fail('target ownership lost')
 print('PASS 26955 successful 26954 byte-exact except +0.4EV and app version; exactly two allowlisted; protected gainmap/Java; B OFF all zooms/Night; B ON/A unchanged')
if __name__=='__main__':
 try:validate()
 except Exception as e:print('26955 SOURCE BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
