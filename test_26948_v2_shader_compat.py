#!/usr/bin/env python3
"""26948 V2: pre-fetch actual historical 26941-26944 GLSL ABI vs submitted candidate.

Does NOT weaken/replace the existing historical shader validators or their mandatory
pinned glslang/spirv-val/spirv-opt Android Actions compiler gates.
"""
import hashlib,re,sys
from pathlib import Path
from build_26948_incremental import R,fail
FILES=(
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
)
HIST_FN_SHA={
 'render.glsl':'555cf6465c6c3f90a6918ed6f9a0402ada22a355af4ee2e0b4eec2d260a28a11',
 'gainmap.glsl':'5ced8442b0eff562f4db7bfebd51938ee7d462fe62eca12f22358c24b380bef0',
}
# Original 26941/26942/26943 live shader ABI, re-confirmed from the actual
# GitHub source at failed commit aa1a357d110db20f79a6be446c8c804c7726f01d.
HIST_MARKERS=(
 'uniform int iris26941BOffHdrqLowZoom;',
 'float iris26941BOffMatchedSdrPrimary(float priorGuide,float sourceGuide)',
 'if(target<=0.82)return target;',
)
FUNC_RE=r'float iris26941BOffMatchedSdrPrimary\(float priorGuide,float sourceGuide\)\{\n[^}]*\n\}'
MODERN='if (target <= 0.82) return target;'
NEW_FN='float iris26948BHeadroomShoulder(float target){'
HIST_44=('iris26941BOffMatchedSdrPrimary(mappedGuide,',
         'if(iris26941BOffHdrqLowZoom!=0 || iris26944NightMatchedSdrEnabled!=0)')
# Git blob hashes of the original 26941-26944 official live validators;
# obtained from the actual failed 26948 commit. This additionally catches
# substituted, stale, or silently weakened historical gate scripts in Actions.
HIST_VALIDATOR_BLOBS={
 'test_26941_shader_contract.py':'66eaa1213f7f8d9d832df1e41377e7c89dad49eb',
 'test_26942_shader_contract.py':'a0657f6918d3a44c4e5f3d402d36bd20a61637f6',
 'test_26943_shader_contract.py':'9c885f00d61952b9d85ada7b2022cd0ba3e4bb2f',
 'test_26944_shader_contract.py':'b4d1dd674c6168b1ced2ce68db1a99b70265bcf9',
}
def git_blob(path):
 b=path.read_bytes()
 return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def verify(render,gain):
 for name,src in [('render.glsl',render),('gainmap.glsl',gain)]:
  for marker in HIST_MARKERS:
   if src.count(marker)!=1:fail('26941/26942/26943 stale/duplicate/missing historical shader ABI: '+name+' '+marker+' observed='+str(src.count(marker)))
  f=re.search(FUNC_RE,src)
  if f is None or hashlib.sha256(f.group().encode()).hexdigest()!=HIST_FN_SHA[name]:
   fail('original 26941 smooth-white shoulder modified: '+name)
  if src.count(NEW_FN)!=1 or src.count(MODERN)!=1:
   fail('26948 corrected shader legacy-token collision or missing new helper '+name)
  modern=src.split(NEW_FN,1)[1].split('\n}',1)[0]
  if modern.count(MODERN)!=1 or 'smoothstep(1.50,2.70,target)' not in modern:
   fail('26948 V2 smooth-white shoulder math/gate modified: '+name)
  if 'uniform int iris26948BUniversalSdrEnabled;' not in src:
   fail('26948 B-only shader control missing '+name)
 if render.count(HIST_44[0])!=2 or render.count(HIST_44[1])!=2:
  fail('26944 global/local Night B SDR historical render shader ABI broken')
 for marker in ('float hdrHighlightGate=smoothstep(0.68,0.96,brightIntent);',
                'ratio=1.0+(ratio-1.0)*hdrHighlightGate;'):
  if gain.count(marker)!=1:fail('26941/42/43 gain-map highlight/ratio gate modified: '+marker)
 if render.count('iris26948BMatchedSdrPrimary(')<2 or gain.count('iris26948BMatchedSdrPrimary(')<2:
  fail('new B-only SDR/gain parity missing')
def negatives(render,gain):
 # Regression 26948 V1 exactly duplicated the historic token. Prove fail-closed.
 scenarios=[('repeat old token in render',render.replace(MODERN,HIST_MARKERS[2],1),gain),
            ('repeat old token in gainmap',render,gain.replace(MODERN,HIST_MARKERS[2],1)),
            ('alter old 26941 white function',render.replace('if(target<=0.82)return target;','if(target<=0.83)return target;',1),gain),
            ('strip modern B helper',render.replace(NEW_FN,'float staleHelper(float target){',1),gain),
            ('alter smooth-white join',render.replace('smoothstep(1.50,2.70,target)','smoothstep(1.50,2.75,target)',1),gain),
            ('remove 26941 gain gate',render,gain.replace('ratio=1.0+(ratio-1.0)*hdrHighlightGate;', 'ratio=ratio;',1)),
            ('remove 26944 Night branch',render.replace(HIST_44[1], 'if(false)',1),gain)]
 for label,r,g in scenarios:
  try:verify(r,g)
  except RuntimeError:continue
  fail('historical shader regression negative escaped: '+label)
 return len(scenarios)
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--payload',action='store_true');p.add_argument('--on-actions',action='store_true');a=p.parse_args()
 if a.live==a.payload:fail('choose exactly one live or payload')
 prefix=R if a.live else R/'handoff_payload_26948'
 r=(prefix/FILES[0]).read_text();g=(prefix/FILES[1]).read_text()
 verify(r,g)
 n=negatives(r,g)
 if a.on_actions:
  for path,h in HIST_VALIDATOR_BLOBS.items():
   f=R/path
   if not f.is_file() or git_blob(f)!=h:fail('missing/stale/modified inherited original shader validator '+path)
 print('PASS 26948 V2 full historical 26941/42/43/44 shader ABI actual source, intact clipped-white, 7 V1 duplicate/stale negatives'+(' and four authentic legacy validator git blobs' if a.on_actions else ''))
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
