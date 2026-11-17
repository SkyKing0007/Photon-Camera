#!/usr/bin/env python3
"""Current 26953 exact code-ownership, shader source and standalone payload protection."""
import hashlib,re,sys
from pathlib import Path
from build_26953_incremental import R,fail,scope,exact
CHANGES={
 'render':'app/src/main/assets/shaders/motionv2/render.glsl',
 'gainmap':'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'java':'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'version':'app/version.properties',
}

def main():
 live='--live' in sys.argv
 changed,added,old,new=scope()
 root=R if live else R/'handoff_payload_26953'
 if live:exact(root,'26953_EXPECTED_FULL_APP.sha256','real current 26953 source and 2051 protected')
 body={n:(root/p).read_text() for n,p in CHANGES.items()}
 for name in CHANGES:
  if hashlib.sha256(body[name].encode()).hexdigest()!=new[CHANGES[name]]:fail('actual changed source digest mismatches sealed manifest '+name)
 if body['version'].count('VERSION_NAME=0.9726953')!=1 or body['version'].count('VERSION_BUILD=26953')!=1:fail('wrong current app version')
 r,g,j=body['render'],body['gainmap'],body['java']
 for source,label in ((r,'render'),(g,'gainmap')):
  if source.count('uniform int iris26953BOffNightSdrEnabled;')!=1:fail('missing new SDR mirror flag '+label)
  if source.count('float iris26953BOffNightSafeBody(')!=1:fail('missing one new no-halo SDR map '+label)
  if source.count('float globalEv=clamp(0.40*log2(max(requested,1.0)),0.0,0.72);')!=1:fail('new global brightness has diverged '+label)
  if source.count('float lifted=prior*exposure/(1.0+(exposure-1.0)*prior);')!=1 or source.count('return mix(lifted,prior,whiteReturn);')!=1:fail('brightness mapping has changed '+label)
  seg=source.split('float iris26953BOffNightSafeBody(',1)[1].split('float iris26906BVisualTone(',1)[0]
  # Exactly 26940's bridge plus image-GLOBAL display gain; no new spatial luma sampling.
  for forbidden in ('texelFetch(', 'texture(', 'max(prior,linearIntent)', 'iris26948BHeadroomShoulder(', 'iris26952ConstrainRim(', 'smoothstep(0.68,0.96,brightIntent)'):
   if forbidden in seg:fail('retained per-pixel HDR-guide/halo operation in new SDR mapping '+label+' '+forbidden)
  if source.count('iris26953BOffNightSafeBody(')!=(3 if label=='render' else 2):fail('one or more real SDR branches not upgraded '+label)
  if source.count('if(iris26953BOffNightSdrEnabled!=0)')!=(2 if label=='render' else 1):fail('new SDR branch not prioritized above old 26948 '+label)
 for token in ('iris26953BOffNightSdrEnabled !=0','iris26953BOffNightSdrEnabled=0'):
  if token in r:fail('unexpected mode-gating syntax in render')
 # Explicit four independently controlled surfaces: low zoom, high zoom, B Night, B ON unmodified.
 start=j.split('final boolean iris26953BOffNightSdrEnabled =',1)
 if len(start)!=2:fail('new Java owner absent or duplicate')
 block=start[1].split(';',1)[0]
 for mark in ('basePipeline.mParameters.iris26906ExperimentBSelected',
              '!basePipeline.mParameters.motionV2SuperResOutputEnabled',
              'basePipeline.mParameters.motionV2Active',
              'basePipeline.mParameters.iris26903NightB'):
  if block.count(mark)!=1:fail('B OFF all zoom/Night gating missing '+mark)
 if 'motionV2OutputZoom' in block or 'iris26941BOffHdrqLowZoom' in block:fail('new owner improperly limited to 1.10x')
 if j.count('glProg.setVar("iris26953BOffNightSdrEnabled",')!=2:fail('both SDR render and gainmap program uniforms required')
 if 'iris26953LensRelativeZoom' in j or 'iris26953BOffNightSdrEnabled = iris26941BOffHdrqLowZoom' in j:fail('new SDR limited to zoom under 1.10x')
 if r.count('if(iris26953BOffNightSdrEnabled!=0 || iris26948BUniversalSdrEnabled==0')!=1:fail('26952 HALO EDGE SPATIAL GUARD still active for new B SDR')
 # Older 26941/26948 luminance source and 26952 suppression stay present for original B ON/A owners.
 for name,src in (('render',r),('gainmap',g)):
  for old_token in ('float iris26941BOffMatchedSdrPrimary(', 'float iris26948BMatchedSdrPrimary(', 'float iris26932BOffSdrBridge('):
   if src.count(old_token)!=1:fail('protected previous source missing '+name+' '+old_token)
 if 'VERSION_BUILD=26952' in body['version']:fail('stale version')
 # Renderer / gainmap exact shared formula but different always-existing exposure uniform owner.
 a=r.split('float iris26953BOffNightSafeBody(',1)[1].split('float iris26906BVisualTone(',1)[0]
 b=g.split('float iris26953BOffNightSafeBody(',1)[1].split('float iris26906BVisualTone(',1)[0]
 if a.replace('outputExposureScale','hdrExposureScale')!=b:fail('UHDR gainmap model differs from completed SDR tone transform')
 print('PASS 26953 exact 2051 protected; no-halo 26940 pointwise owner + HDR-body global exposure; all B OFF zoom, B Night, B ON exclusion and UHDR mirror')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26953 SOURCE BLOCKED: '+str(e),file=sys.stderr);sys.exit(1)
