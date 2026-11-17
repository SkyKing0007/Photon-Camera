#!/usr/bin/env python3
"""26954 exact 26940 photo path, B/OFF all zoom + Night ownership and protected 26953 scope."""
import hashlib,re,sys
from build_26954_incremental import R,fail,scope,exact
PATHS={
 'render':'app/src/main/assets/shaders/motionv2/render.glsl',
 'gainmap':'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'java':'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'version':'app/version.properties',
}


# Frozen function-body hashes independently recovered from the ACTUAL successful
# 26940 published compiled-source TAR, not inferred from the 26953 handoff.
# These exact active SDR color, shadow, gamut, gamma and UHDR routines must
# survive after dropping the post-26941 presentation branches.
ORIGINAL_26940_SHADER_FUNCTION_SHA={
 'render':{
  'iris26704BodyToneGuide':'6690d4dabe76531b7ff77e1e056b2cc49182ec4a0a26627b2661f796a1129806',
  'iris26660ObjectColorGamma':'d26cec87a91bb02f7e018bc02fe9fe296f8467c807886e714b9cbed7aeca52a3',
  'iris26770MidtonePresentationTrim':'3bd10608551e978aa65a03b989457933b71e2003e0a7ff5059346532682d8089',
  'iris26892SdrAdaptiveGuide':'b812cf62828d95e39f3f8537516aaf31e86c4603e83130bc49c207fd53100405',
  'iris26906BVisualTone':'bfa4ac9e2c543e180a8ab6c45e2b8f06a30898548f222b451b23165051838547',
  'iris26932BOffSdrBridge':'8d9d01638353e425fa24f201c95b1b0fb25c2c505418dfc58502a350077d7f76',
  'mapFinalSdrGuide':'6e9157b5cf43881b80259a83f616e179b348414ecf1b28c270c16f139da6f2ad',
  'iris26638ApplyShadowFloorGuard':'0f7a1d47dbc752695fdb8504f9149762c4643aa1887c49c91f86530ade3f85d3',
  'fitDisplayGamut':'2bea5dae6c33853fdc6e7866546d3f89119e105af473f883dd636f8455d5aaf9',
  'iris26638UserSaturation':'7e194fe831f8128cfd9dadbd24d53ebef6920cf305a19811ae910db20f2db878',
  'srgbEncode':'924e4bba4654ac59df210d6f6eef3d9a228934a56dd709cbe3cb46b08349ad4b',
 },
 'gainmap':{
  'iris26932BOffSdrBridge':'8d9d01638353e425fa24f201c95b1b0fb25c2c505418dfc58502a350077d7f76',
  'iris26906BVisualTone':'bfa4ac9e2c543e180a8ab6c45e2b8f06a30898548f222b451b23165051838547',
  'srgbDecode':'3ba7257f30528fb7a2eb1688f0cff8a40127e7e56a724cd6f7c7e3260b21feec',
  'iris26653MapMotionSdrGuide':'a7d81292d9ed580aff9a84ae8782ee8013fbcdfcc9834a00331722112b0d3445',
 }
}

def original_function_sha(shader,name):
 m=re.search(r'(?m)^(?:float|vec3|vec4|void|int)\s+'+re.escape(name)+r'\s*\(',shader)
 if not m:fail('original 26940 operator missing '+name)
 start=m.start();i=shader.index('{',m.end())+1;depth=1
 while depth:
  if i>=len(shader):fail('unterminated 26940 operator '+name)
  depth+=(shader[i]=='{')-(shader[i]=='}')
  i+=1
 return hashlib.sha256(shader[start:i].encode()).hexdigest()


def main():
 changed,added,old,new=scope()
 root=R if '--live' in sys.argv else R/'handoff_payload_26954'
 if '--live' in sys.argv:exact(root,'26954_EXPECTED_FULL_APP.sha256','real current 26954 current source full inventory')
 body={k:(root/p).read_text() for k,p in PATHS.items()}
 for name,p in PATHS.items():
  if hashlib.sha256(body[name].encode()).hexdigest()!=new[p]:fail('26954 candidate SHA differs '+p)
 r,g,j,v=body['render'],body['gainmap'],body['java'],body['version']
 for shadername,shadertext in (('render',r),('gainmap',g)):
  for fname,want in ORIGINAL_26940_SHADER_FUNCTION_SHA[shadername].items():
   if original_function_sha(shadertext,fname)!=want:
    fail('actual 26940 original UHDR/SDR color/contrast/shadow operator changed: '+shadername+'/'+fname)

 if v.count('VERSION_BUILD=26954')!=1 or v.count('VERSION_NAME=0.9726954')!=1:fail('26954 wrong app version')
 for s,name in ((r,'render'),(g,'gainmap')):
  if s.count('uniform int iris26954BOffNight26940Sdr;')!=1:fail('missing 26954 shader scope uniform '+name)
  if s.count('iris26953BOffNightSafeBody(')!=0:fail('26953 +0.72EV competing SDR lift remains '+name)
  if s.count('if(iris26954BOffNight26940Sdr!=0)')!=(3 if name=='render' else 1):fail('26954 SDR+gainmap owner missing '+name)
  # Exact 26940 original B bridge body is preserved, not replaced with new local tone.
  # Exact source-derived bridge body SHA-256 from successful 26940 compiled
  # 26940 artifact 14170559036. Do not require a stale older source checkout.
  key='float iris26932BOffSdrBridge('
  bridge=s.split(key,1)[1].split('}',1)[0]
  if hashlib.sha256(bridge.encode()).hexdigest()!='37a3e25ebfe79f55c4f43679728107b6e8c132bc0ca0abbba94a4c4c1080cb5a':
   fail('successful 26940 SDR bridge changed '+name)
  for symbol in ('float iris26941BOffMatchedSdrPrimary(','float iris26948BMatchedSdrPrimary('):
   if s.count(symbol)!=1:fail('protected historical B ON shader branch omitted '+name+' '+symbol)
  if s.count('else if(iris26948BUniversalSdrEnabled!=0)')!=(2 if name=='render' else 1):fail('B ON original 26948 branch accidentally removed')
 if 'if(iris26954BOffNight26940Sdr!=0 || iris26948BUniversalSdrEnabled==0' not in r:fail('26952 halo rim still applies to B OFF')
 if r.count('const float iris26954SdrExposureScale=2.0;')!=1:fail('global +1EV exact single exposure missing')
 if 'float limitedExposure=min(iris26954SdrExposureScale,1.0/max(peak,1.0e-6));' in r:fail('REJECTED V1 hard 0.5..1.0 flat white cap still present')
 for expected in ('float mappedPeak;', 'if(peak<=0.125)', 'mappedPeak=iris26954SdrExposureScale*peak;',
                  'float x=clamp((peak-0.125)/0.875,0.0,1.0);',
                  'mappedPeak=((0.5125*x-1.5125)*x+1.75)*x+0.25;',
                  'float uniformScale=mappedPeak/max(peak,1.0e-6);',
                  'linearSrgb=unexposed*uniformScale;'):
  if r.count(expected)!=1:fail('strictly monotone fixed-EV exposure/shadow+white shoulder incomplete '+expected)
 if r.find('linearSrgb=iris26638UserSaturation(')>r.find('linearSrgb=unexposed*uniformScale;'):fail('+1EV wrongly before 26940 color/saturation')
 if r.find('linearSrgb=unexposed*uniformScale;')>r.find('Output=clamp('):fail('global editor EV comes after output transfer')
 if 'hdrIntentY=max(sdr,sdrModelY+matchedIntentDelta)' in g:fail('REJECTED V1 HDR numerator override still changes 26940 UHDR contrast')
 if g.count('float hdrIntentY=sdr+matchedIntentDelta;')!=1:fail('actual 26940 matched HDR intent delta not rebased onto actual new SDR')
 if g.count('iris26954BOffNight26940Sdr==0 && iris26941BOffHdrqLowZoom!=0')!=1:fail('26941 highlight-only gate leaks into B OFF')
 if g.count('ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);')!=1:fail('actual HDR/SDR adaptive gain denominator not matched')
 if j.count('glProg.setVar("iris26954BOffNight26940Sdr",')!=2:fail('both renderer and gainmap Java flags missing')
 block=j.split('final boolean iris26954BOffNight26940Sdr =',1)
 if len(block)!=2:fail('Java new single frozen mode gate absent')
 block=block[1].split(';',1)[0]
 for s in ('basePipeline.mParameters.iris26906ExperimentBSelected','!basePipeline.mParameters.motionV2SuperResOutputEnabled','basePipeline.mParameters.motionV2Active','basePipeline.mParameters.iris26903NightB'):
  if block.count(s)!=1:fail('wrong B OFF/Night scope '+s)
 if 'motionV2OutputZoom' in block or 'iris26941BOffHdrqLowZoom' in block or 'irisNightActive' in block:fail('B OFF + Night erroneously limited to zoom or inappropriate route')
 if 'iris26954BOffNight26940Sdr' not in r or 'iris26954BOffNight26940Sdr' not in g:fail('new route unused')
 print('PASS 26954 V2 15 EXACT successful 26940 original SDR/UHDR operator SHA; one +1EV C1 positive-slope white shoulder; exact original 26940 UHDR delta rebased on new SDR; B OFF all zoom/Night scope; B ON/A protected; 2051 protected')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26954 SOURCE BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
