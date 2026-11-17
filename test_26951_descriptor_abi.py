#!/usr/bin/env python3
"""Exact 26950 shutter-press binding regression: RAWR SPIR-V/host/descriptor triplet, plus hostile negatives."""
import pathlib,re,sys
from build_26951_incremental import R,parse,sha,fail
APP='app/src/main/cpp/iris26864/'
STAGES={
 'HdrqMismatch':('bridge/Iris26888BOffHdrqMismatch.comp','hdrq_mismatch.comp','mp'),
 'HdrqMerge':('bridge/Iris26887BOffHdrqMerge.comp','hdrq_merge.comp','fm'),
 'HdrqBorder':('bridge/Iris26943BOffHdrqBorder.comp','hdrq_border.comp','bd'),
 'HdrqMismatchNorm':('bridge/Iris26887BOffHdrqMismatchNorm.comp','hdrq_mismatch_norm.comp','np'),
}
def spec(text,stage):
 name=re.sub(r'(?<!^)(?=[A-Z])','_',stage).lower()
 m=re.search(r'\{"'+name+r'",[\s\S]*?\n\s*(\{\{0, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE\}.*?\}\})',text)
 if not m:fail('missing native spec '+stage)
 return sorted((int(n),t) for n,t in re.findall(r'\{(\d+), VK_DESCRIPTOR_TYPE_STORAGE_(IMAGE|BUFFER)\}',m.group(1)))
def glsl(text):
 text=re.sub(r'/\*[\s\S]*?\*/|//[^\n]*','',text)
 rows=[]
 for m in re.finditer(r'layout\(([^)]*)\)\s*([^;\n]*?)(?:;|\{)',text):
  b=re.search(r'\bbinding\s*=\s*(\d+)',m.group(1))
  if b:
   tail=m.group(2);typ='BUFFER' if re.search(r'\bbuffer\b',tail) else 'IMAGE' if re.search(r'\bimage2D\b',tail) else None
   if not typ:fail('shader descriptor unsupported '+m.group())
   rows.append((int(b.group(1)),typ))
 if len(rows)!=len(set(rows)):fail('duplicate GLSL descriptor declarations')
 return sorted(rows)
def rec(text,stage,end):
 m=re.search(r'executor_\.record\(c, ShaderId::'+stage+r',([\s\S]*?)&'+end+r',',text)
 if not m:fail('missing recorder dispatch '+stage)
 t=m.group(1)
 return sorted([(int(n),'IMAGE') for n in re.findall(r'\bib\((\d+)\s*,',t)]+[(int(n),'BUFFER') for n in re.findall(r'\bbb\((\d+)\s*,',t)])
def check_triplet(shader,exe,host,stage,end):
 a=spec(exe,stage);b=glsl(shader);c=rec(host,stage,end)
 if a!=b or a!=c:fail('26950 native missing/duplicate required binding regression '+stage+f': spec={a} GLSL={b} recorded={c}')
def main():
 live='--live' in sys.argv;root=R if live else R/'handoff_payload_26951'
 exec=(root/(APP+'bridge/Iris26888BOffVulkanExecutor.cpp')).read_text()
 recode=(root/(APP+'bridge/Iris26887BOffHdrqRecorder.cpp')).read_text()
 prior=parse(R/'26951_BASE_26949_FULL_APP.sha256');curr=parse(R/'26951_EXPECTED_FULL_APP.sha256')
 for stage,(shader,donor,end) in STAGES.items():
  p=APP+shader
  if sha(root/p)!=curr[p]:fail('stage shader SHA not sealed '+p)
  s=(root/p).read_text();check_triplet(s,exec,recode,stage,end)
  # Donor must be protected SHA in successfully compiled 26949, NOT failed 26950.
  upstream=APP+'vendor/rawr/native/multiframe/merge_hdrplus/shaders/'+donor
  if curr[upstream]!=prior[upstream] or sha(root/p)!=prior[upstream]:fail('RAWR 26949 upstream shader diverged '+stage)
  if live:
   if sha(R/upstream)!=prior[upstream]:fail('restored vendor mismatch '+stage)
   vendor_exec=(R/(APP+'vendor/rawr/native/multiframe/pipeline/src/VulkanExecutor.cpp')).read_text()
   if spec(exec,stage)!=spec(vendor_exec,stage):fail('restored RAWR native descriptor mismatch '+stage)
  # Independent adversarial 26950 V4 regression: recreate each extra descriptor.
  if stage=='HdrqMismatch': extra=[(4,'IMAGE'),(5,'IMAGE')]
  elif stage=='HdrqMerge':extra=[(8,'BUFFER')]
  elif stage=='HdrqBorder':extra=[(2,'IMAGE')]
  else:extra=[]
  original=spec(exec,stage)
  if extra and (set(original+extra)==set(glsl(s))):fail('26950 legacy extra descriptors unexpectedly match original shader')
  # Fault injector tests the entire triple, not just precomputed pass labels.
  if extra and not set(extra).isdisjoint(original):fail('26950 missing/duplicate binding negative changed')
 for assertion in ('sizeof(MismatchNormPc)==12u','sizeof(FreqMergePc)==28u','sizeof(BorderPc)==12u'):
  if assertion not in recode:fail('RAWR C++ push ABI missing '+assertion)
 if 'hdrq_motion_min' in recode or 'bb(8,' in recode or 'ib(5, arena_.image("hdrq_motion_min"))' in recode:fail('stale removed shader bindings remain')
 print('PASS 26951 four shader + GPU recorder + Vulkan specs identical, 26950 extra-binding failure rejected')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
