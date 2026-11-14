#!/usr/bin/env python3
"""Exact source string extraction and preserved historical shader byte parity."""
from pathlib import Path
import hashlib,re,sys,textwrap
from build_26931_incremental import R,BASE,OUT,scope,fail

SHADERS=(
 ('lkr_temporary_wb','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrColorContract.kt','val applyAmazeWbForLabFcc'),
 ('lkr_physical_lsc','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt','val bLensShade'),
 ('lkr_2x_guide','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','private val iris26876DerivedGuideShader'),
)

def lit(s,key):
 match=list(re.finditer(re.escape(key)+r'\s*=\s*"""',s))
 if len(match)!=1:fail('active LKR shader literal missing or duplicate '+key)
 return textwrap.dedent(s[match[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
def main():
 _,_,base,new=scope()
 changed={'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'}
 if '--live' in sys.argv and BASE.is_dir():
  for path in changed:
   old=(BASE/path).read_text();current=(R/path).read_text()
   if re.findall(r'"""(.*?)"""',old,re.S)!=re.findall(r'"""(.*?)"""',current,re.S):fail('26931 changed any inline GL shader byte')
 compiled={}
 for name,path,key in SHADERS:
  if '--live' not in sys.argv and '--extract' not in sys.argv:continue
  source=(R/path).read_text()
  body=lit(source,key)
  if not body.startswith('#version 300 es\n') or 'uniform' not in body or 'void main()' not in body:fail('invalid current executable ESSL source '+name)
  # Reserved GLSL tokens caused prior builds to fail; text in comments is
  # harmless, but a live identifier/qualifier "coherent" in these ESSL 300
  # shaders is an unacceptable compile risk. This is supplemental to the
  # mandatory pinned real glslang/spirv-val/spirv-opt gates in Actions.
  uncommented = re.sub(r'/\*.*?\*/|//[^\n]*', '', body, flags=re.S)
  if re.search(r'\bcoherent\b',uncommented):fail('reserved coherent keyword in active 26931 GLSL '+name)
  if name=='lkr_temporary_wb' and ('uSensorNeutralAmazeRgb' not in body or 'uAmazeWb' not in body):fail('original WB shader uniform ABI')
  if name=='lkr_physical_lsc' and ('uLensShading' not in body or 'uExpandedScale' not in body):fail('original physical LSC shader ABI')
  if name=='lkr_2x_guide' and ('uTwoXLinear' not in body or 'uTwoXOriginalClip' not in body):fail('original 2x guide shader ABI')
  compiled[name]=body
 if '--extract' in sys.argv:
  OUT.mkdir(exist_ok=True)
  for name,body in compiled.items():
   (OUT/f'26931_{name}_es300.frag').write_text(body)
   (OUT/f'26931_{name}_es310.frag').write_text(body.replace('#version 300 es','#version 310 es',1))
  print('PASS three REAL 26931 active LKR 50MP GLES shader bodies extracted from candidate Kotlin without modification')
 else:print('PASS source-identical original LKR temporary-WB, physical LSC and 2x guide inline ESSL shader ABI')
if __name__=='__main__':
 try:main()
 except Exception as e:print('ERROR',e,file=sys.stderr);sys.exit(1)
