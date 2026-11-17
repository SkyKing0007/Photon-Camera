#!/usr/bin/env python3
"""Compile the *current 26952* five-shader set with the original 26939/41/42
pinned real GLSL/SPIR-V compiler bodies. The obsolete historical source
contracts run against their sealed historical payload; never against 26952.
No older APK, old app source reconstruction, native build or stale candidate.
"""
import hashlib,pathlib,re,subprocess,sys,textwrap
from build_26952_incremental import R,parse,sha,fail

HISTORICAL={
 '39':('compile_26939_shaders.sh','1d5b72ca3b815a44f9ebd907f6d60737df00af99',
       'python3 -S test_26939_shader_contract.py --live --extract',
       'python3 -S test_26939_shader_contract.py --payload'),
 '41':('compile_26941_shaders.sh','b9590e3891ff1eeb8f622239967ee3f17039703a',
       'python3 -S test_26941_shader_contract.py --live --extract',
       'python3 -S test_26941_shader_contract.py --payload'),
 '42':('compile_26942_shaders.sh','7aaef0de4202005e686caa4ed53a37e18b7bc591',
       'python3 -S test_26942_shader_contract.py --live --extract',
       'python3 -S test_26942_shader_contract.py --payload'),
}
SHADERS={
 'raw_lens_median':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt',True),
 'lkr_smooth_white':('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt',True),
 'motion_render':('app/src/main/assets/shaders/motionv2/render.glsl',False),
 'motion_gainmap':('app/src/main/assets/shaders/motionv2/gainmap.glsl',False),
 'b_native_final':('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',False),
}
ARITY={'max':2,'min':2,'clamp':3,'smoothstep':3,'mix':3,'dot':2,'pow':2,'step':2,'texelFetch':3}
def gitblob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def validate_arity(code,name):
 clean=re.sub(r'/\*.*?\*/|//[^\n]*','',code,flags=re.S)
 for m in re.finditer(r'\b('+'|'.join(ARITY)+r')\s*\(',clean):
  n=1;depth=0;done=False
  for c in clean[m.end()-1:]:
   if c=='(':depth+=1
   elif c==')':
    depth-=1
    if depth==0:done=True;break
   elif c==',' and depth==1:n+=1
  if not done or n!=ARITY[m.group(1)]:fail('current 26952 illegal GLSL builtin arity '+name+' '+m.group(1)+' '+str(n))
 # The successful 26951 compiler accepts legit qualifiers but not GLSL
 # reserved keywords accidentally used as declarations. This caught the
 # 26952 V3 `float flat=...` failure before the actual Actions compiler.
 reserved={'flat','coherent','volatile','restrict','readonly','writeonly',
           'attribute','varying','centroid','smooth','noperspective','patch',
           'sample','invariant','precise','layout','buffer','shared','subroutine',
           'atomic_uint','input','output','partition','active','superp'}
 typed=r'(?:float|int|uint|bool|double|[ibdu]?vec[234]|d?mat[234](?:x[234])?|sampler\w*|image\w*)'
 for decl in re.finditer(r'\b'+typed+r'\s+([A-Za-z_][A-Za-z0-9_]*)\b',clean):
  if decl.group(1) in reserved:fail('26952 V3 real GLSL reserved identifier '+name+' '+decl.group(1))
 # `flat` must not occur anywhere in these five current fragment programs;
 # its only prior occurrence was an invalid local variable, never a qualifier.
 if re.search(r'\bflat\b',clean):fail('26952 V3 unexpected FLAT in current fragment '+name)

 if re.search(r'\b(?:readonly|writeonly|restrict|volatile)\s*=',clean):
  fail('reserved GLSL token assigned in '+name)

def reserved_identifier_self_test():
 for src in ('float flat=abs(a-b);','float coherent=1.0;',
             'vec3 restrict=vec3(1.0);','highp float flat=1.0;'):
  try:validate_arity(src,'EXPECTED_NEGATIVE_RESERVED')
  except RuntimeError:continue
  fail('reserved GLSL keyword negative escaped: '+src)
 validate_arity('float plateauDelta=abs(a-b);','VALID_RENAMED_GLSL')

def current_inputs(label):
 cur=parse(R/'26952_EXPECTED_FULL_APP.sha256')
 old=parse(R/'26952_BASE_26951_FULL_APP.sha256')
 output={}
 for name,(path,embedded) in SHADERS.items():
  src=R/path
  if not src.is_file() or sha(src)!=cur[path]:fail('26952 current-source shader identity failed '+name)
  if name in ('lkr_smooth_white','motion_gainmap','b_native_final') and cur[path]!=old[path]:
   fail('26951 successful protected shader modified '+name)
  body=src.read_text()
  if embedded:
   matches=list(re.finditer(r'\bval\s+shader\s*=\s*"""',body))
   if len(matches)!=1 or body[matches[0].end():].count('""".trimIndent()')!=1:
    fail('current Kotlin shader embedding malformed '+name)
   body=textwrap.dedent(body[matches[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
  validate_arity(body,name)
  if name=='b_native_final':
   if not body.startswith('#version 310 es'):fail('current B native final ESSL310 version invalid')
  elif embedded:
   if not body.startswith('#version 300 es') or body.count('void main()')!=1:fail('current inline ESSL300 invalid '+name)
  elif '#version' in re.sub(r'//[^\n]*|/\*.*?\*/','',body,flags=re.S):
   fail('current motion shader duplicates #version '+name)
  output[name]=body
 if 'cc_median(p,m0,1)' not in output['raw_lens_median'] or 'cc_median(p,m0,2)' not in output['raw_lens_median']:
  fail('current median changed back to 26939 single-radius output')
 if 'iris26952ConstrainRim(sourceXY,linearSrgb);' not in output['motion_render']:
  fail('current 26952 SDR rim missing')
 out=R/f'photon_269{label}_outputs';out.mkdir(parents=True,exist_ok=True)
 for name,body in output.items():
  if name=='b_native_final':(out/f'269{label}_{name}_es310.frag').write_text(body)
  else:
   es300=body if body.startswith('#version 300 es') else '#version 300 es\n#line 1\n'+body
   (out/f'269{label}_{name}_es300.frag').write_text(es300)
   (out/f'269{label}_{name}_es310.frag').write_text(es300.replace('#version 300 es','#version 310 es',1))
 print('PASS 26952 LIVE five-shader 269'+label+' extractor, all source SHA, four historic arity regressions, reserved keywords')

def main():
 if len(sys.argv)<2 or sys.argv[1] not in HISTORICAL or sys.argv[2:] not in ([],['--extract-only']):
  fail('usage: replay_26952_current_legacy_glsl.py 39|41|42 [--extract-only]')
 label=sys.argv[1]
 reserved_identifier_self_test()
 if sys.argv[2:]==['--extract-only']:
  current_inputs(label);return
 file,expect,oldcall,history=HISTORICAL[label]
 script=R/file
 if not script.is_file() or gitblob(script.read_bytes())!=expect:fail('original pinned real compiler source SHA changed '+file)
 txt=script.read_text()
 newcall='python3 -S replay_26952_current_legacy_glsl.py '+label+' --extract-only'
 if txt.count(oldcall)!=1 or newcall in txt:fail('original compiler old-live preflight changed '+file)
 out=txt.replace(oldcall,newcall,1)
 # 26939 additional 26939-only highlight assertions are intentionally run on
 # the exact 26939 historical payload, not on current 26952 two-radius code.
 if label=='39':
  oldmath='python3 -S test_26939_highlight_math.py --live'
  newmath='python3 -S test_26939_highlight_math.py --payload'
  if txt.count(oldmath)!=1 or newmath in txt:fail('original 26939 math gate changed')
  out=out.replace(oldmath,newmath,1)
  if out.replace(newmath,oldmath,1).replace(newcall,oldcall,1)!=txt:fail('historical real compiler body was altered')
 else:
  if out.replace(newcall,oldcall,1)!=txt:fail('historical real compiler body was altered')
 # Retain source regression coverage independently, using the old sealed test
 # inputs exactly as those tests intended; never treat them as live 26952.
 subprocess.run([sys.executable,'-S',history.split()[2],'--payload'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26952_source.py','--live'],cwd=R,check=True)
 subprocess.run(['bash','-c',out,str(script)],cwd=R,check=True)
 receipt=R/f'photon_269{label}_outputs/269{label}_REAL_GLSL_SPIRV_COMPILER.txt'
 if not receipt.is_file() or f'PASS actual 269{label}' not in receipt.read_text():
  if label!='41' and label!='42':fail('current-source real compiler receipt absent '+file)
  if 'PASS 269'+label not in receipt.read_text():fail('current-source real compiler receipt absent '+file)
 print('PASS exact SHA-pinned 269'+label+' real glslang / SPIR-V compiler body on CURRENT 26952 live shaders')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
