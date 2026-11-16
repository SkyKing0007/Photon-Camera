#!/usr/bin/env python3
"""Conservative motion shader and Night render binding/arity/descriptor contract."""
import re,sys
from build_26944_incremental import R,scope,fail,sha
BP='app/src/main/cpp/iris26864/bridge/'
def main():
 scope();live='--live' in sys.argv
 def read(p,modified=True):
  f=(R if live or not modified else R/'handoff_payload_26944')/p
  if not f.is_file():fail('missing current shader source '+p)
  return f.read_text()
 mm=read(BP+'Iris26888BOffHdrqMismatch.comp')
 merge=read(BP+'Iris26887BOffHdrqMerge.comp')
 render=read('app/src/main/assets/shaders/motionv2/render.glsl')
 for name,s in [('mismatch',mm),('frequency merge',merge),('render',render)]:
  clean=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
  if re.search(r'\b(?:float|int|vec[234]|uint|bool)\s+coherent\b',clean):fail('GLSL reserved coherent identifier '+name)
  if re.search(r'\b(?:readonly|writeonly|restrict|volatile)\s*=',clean):fail('GLSL reserved qualifier identifier '+name)
  if s.count('void main()')!=1:fail('GLSL main arity '+name)
 if not mm.startswith('#version 450') or not merge.startswith('#version 450') or '#version' in render:fail('shader version changed')
 if 'clamp(worst16[15],0.0,1.0)' not in mm or 'worst16[7]' in mm:fail('26942 motion percentile regression')
 if 'smoothstep(0.48, 0.82, 1.0 - independentSupport)' not in merge:fail('motion extra support veto missing')
 if merge.count('imageStore(outFt, o')<2:fail('frequency merge changed ref spectrum output')
 if render.count('iris26941BOffMatchedSdrPrimary(mappedGuide,')!=2:fail('successful 26941 matched SDR math not reused')
 if render.count('if(iris26941BOffHdrqLowZoom!=0 || iris26944NightMatchedSdrEnabled!=0)')!=2:fail('Night shader global/local tone branches diverge')
 if render.count('uniform int iris26944NightMatchedSdrEnabled;')!=1:fail('Night uniform ABI')
 if live:
  ex=read(BP+'Iris26888BOffVulkanExecutor.cpp',False)
  rec=read(BP+'Iris26887BOffHdrqRecorder.cpp')
  border=read(BP+'Iris26943BOffHdrqBorder.comp',False)
  for shader,bindingCount in ((mm,6),(border,3)):
   for b in range(bindingCount):
    if not re.search(r'layout\s*\(\s*set\s*=\s*0\s*,\s*binding\s*=\s*'+str(b)+r'\b',shader):fail('private GLSL descriptor layout mismatch')
  if 'sizeof(MismatchPc) == 100u' not in rec or 'sizeof(BorderPc)==16u' not in rec:fail('original Vulkan push ABI changed')
  if ex.count('mf_hdrq_mismatch_prod_spv')<1 or ex.count('mf_hdrq_border_prod_spv')<1:fail('actual V5 compiled shader symbol missing')
  if 'mp.motionEnabled = 0;' not in rec or 'BorderPc bd{' not in rec:fail('periodic motion restoration not removed')
 print('PASS native Vulkan shader binding, 26942 percentile, 26944 motion support, Night SDR global/local shader ABI, reserved-identifier negatives')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
