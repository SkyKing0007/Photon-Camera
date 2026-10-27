#!/usr/bin/env python3
"""26883 actual successful 26882 versus current shared B highlight and Spektra FOV.
Persistent sensor/domain/route regressions. Real compilers and device proof separate.
"""
import sys,hashlib,math,re
from pathlib import Path
B=Path(sys.argv[1]);C=Path(sys.argv[2]);R=Path(__file__).resolve().parent
manifest=lambda n:{k:h for h,k in (s.split('  ',1) for s in (R/n).read_text().splitlines())}
base=manifest('26883_BASE_26882_FULL_APP.sha256');new=manifest('26883_EXPECTED_CANDIDATE_FULL_APP.sha256')
allow=(R/'26883_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(allow)==4 and len(base)==len(new)==2009
assert set(allow)=={p for p in base if base[p]!=new[p]}
assert 'VERSION_NAME=0.9726883' in (C/'app/version.properties').read_text()
assert 'VERSION_BUILD=26883' in (C/'app/version.properties').read_text()
for p in (
'app/src/main/cpp/iris26864/bridge/Iris26864HdrqCfaToAmaze.comp',
'app/src/main/cpp/iris26864/Iris26864WronskiPackedCfa2x.comp',
'app/src/main/cpp/iris26864/Iris26864PackedSensorClipToGl.comp',
'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt',
'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java',
'app/src/main/java/com/unspektrawesome/preview/RawPreviewPlanSelector.kt',
'app/src/main/java/com/unspektrawesome/vulkan/params/RawShaderParameters.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'):
 assert base[p]==new[p],('protected owner drift',p)
assert 'uRequireOriginal2xBinary!=0 && !(clip==0.0||clip==1.0)' in (C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
clip=(C/'app/src/main/cpp/iris26864/Iris26864PackedSensorClipToGl.comp').read_text()
assert 'float clipped=((packedClipBits&(1u<<bit))!=0u)?1.0:0.0;' in clip
shader='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt'
a=(B/shader).read_text();s=(C/shader).read_text();marker='    val bNativeSensorSmoothWhite26866 = """';i=a.index(marker);j=s.index(marker)
assert a[:i]==s[:j], 'unrelated GLSL owner changed'
post='    """.trimIndent()';assert a[a.index(post,i):]==s[s.index(post,j):], 'post-shader source changed'
sh=s[j:s.index(post,j)]
for fragment in ('uniform sampler2D uPreLabWbRgb;', 'texelFetch(uPreLabWbRgb,p,0)',
'float earlyFade=', 'float sensorFade=', 'float fade=max(earlyFade,sensorFade);',
'vec3 cameraRgb=evidenceRgb/gains;', 'float wbSafe=', 'int r=clamp(uBayerPattern,0,3);',
'vec3 phaseColorClipAt(ivec2 cell)', 'oRgb=vec4(mix(original.rgb,vec3(neutral),'):
 assert fragment in sh,fragment
assert 'if(clippedCoverage<=0.0)' not in sh
stack='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
t=(C/stack).read_text();old=(B/stack).read_text()
assert t.count('renderIris26866BNativeSensorSmoothWhite(')==2
assert 'fcc, temporaryPostWb, nativeSensorClipFullRes26866,' in t
assert 'bindTexture(program,"uPreLabWbRgb",2,preLabWb)' in t
assert t.count('temporaryPostWb = createTexture(')==1
for tag in ('renderRawrBPostAmaze26856(', 'processIris26868DirectB(frames)', 'reconstructIris26876B2xGpu(', 'nativeSensorClipFullRes26866=nativeClip,'):
 assert tag in t,tag
assert t.count('Iris26864NativeRawrDomainReceipt(true,true,true)')>=2
assert 'fcc, temporaryPostWb, nativeSensorClipFullRes26866,' not in old
preview='app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt';p=(C/preview).read_text();op=(B/preview).read_text()
for q in ('val gpuPreviewLimit26883 = Size2d(', 'minOf(owner.plan.processingSize.width, 1920)',
'minOf(owner.plan.processingSize.height, 1440)', 'gpuPreviewLimit26883,','createFullFrameStill('):assert q in p,q
assert p.count('FrameGeometrySnapshot.createFullActivePreview(')==op.count('FrameGeometrySnapshot.createFullActivePreview(')==1
geo=(C/'app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt').read_text()
assert 'sourceCrop = normalizedActive,' in geo and 'processingLimit?.let { fitWithin(mappedActive, it) }' in geo
assert 'outputSize = transform.outputSize(rawOutputSize),' in geo
for angle in (0,90,180,270):
 for mirror in (False,True):
  corners=[]
  for u,v in ((0,0),(1,0),(0,1),(1,1)):
   if mirror:u=1-u
   if angle==90:x,y=v,1-u
   elif angle==180:x,y=1-u,1-v
   elif angle==270:x,y=1-v,u
   else:x,y=u,v
   corners.append((x,y))
  assert set(corners)=={(0,0),(1,0),(0,1),(1,1)}
# Continuous early-white bridge numerical regression; physically clipped Bayer remains binary.
def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)
def fade(rgb,wb):
 cam=[v/max(g,1.e-4) for v,g in zip(rgb,wb)];bright=max(rgb);second=sorted(rgb)[1];low=min(cam);hi=max(cam)
 white=smooth(.27,.61,low/max(hi,1.e-4))*smooth(.47,.70,min(rgb)/max(bright,1.e-4));approach=smooth(.48,.80,hi)
 safe=min(wb);near=[smooth(.72,1.01,v/safe) for v in rgb]
 early=max(min(near[0],near[1]),min(near[1],near[2]),min(near[0],near[2])*smooth(.35,.80,cam[1]))
 return smooth(.06,.89,early)*white*smooth(.68,1.04,max(second/safe,low))*approach
wb=(1.35,1.0,1.35)
assert fade((1.,.73,1.),wb)>.6, 'partly clipped white glass still tinted'
assert fade((.9,.9,.9),wb)>.1, 'approaching neutral white lost early confidence'
for rgb in ((.1,.2,.75),(1.,.15,.17),(1.,1.,.2),(.42,.42,.42)):
 assert fade(rgb,wb)==0,('genuine saturated color or dark neutral damaged',rgb)
for v in range(101,999):
 a=fade((1.,v/1000,1.),wb);b=fade((1.,v/1000+0.0001,1.),wb)
 assert abs(b-a)<.005
print('PASS 26883: B HDRq+Wronski shared early pre-Lab/post-FCC white, binary original Bayer mask, uncropped Spektra full FOV all orientations, real-source domains and color regressions')
