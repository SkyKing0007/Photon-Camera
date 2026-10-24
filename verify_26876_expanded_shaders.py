#!/usr/bin/env python3
"""Extract EXACT runtime GLSL, scan expanded source, optionally compile via pinned glslang.
This validator never treats static-only checks as a real compiler pass.
"""
from pathlib import Path
import os,re,sys,subprocess,tempfile
base=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/26876_continuation')/'app'
source_only='--source-only' in sys.argv[2:]
kt=(base/'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
cpp=(base/'src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
asset=(base/'src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag').read_text()
match=re.search(r'private val iris26876DerivedGuideShader\s*=\s*"""(.*?)"""\.trimIndent\(\)',kt,re.S)
assert match,'missing B-only 2x to 1x guide shader'
lines=match.group(1).splitlines()
lines=[s[8:] if s.startswith(' '*8) else s for s in lines]
guide='\n'.join(lines).strip()+'\n'
def raw(name):
 m=re.search(r'constexpr const char\* '+name+r'=R"IRIS26876\((.*?)\)IRIS26876";',cpp,re.S)
 assert m,name
 return m.group(1).strip()+'\n'
files={
 'final_p3_gain.frag':asset,
 'wronski_derived_1x.frag':guide,
 'native_ahb_pack.frag':raw('kIris26876BPackFrag'),
 'native_ahb_pack.vert':raw('kIris26876BPackVertex'),
}
reserved=set('attribute varying precision highp mediump lowp layout flat smooth noperspective centroid patch sample uniform buffer readonly writeonly coherent volatile restrict shared in out inout const if else for while do switch case default break continue discard return struct true false namespace typedef template class union enum goto inline noinline public static extern external interface long short half fixed unsigned superp packed input output common partition active asm sizeOf'.split())
for fname,src in files.items():
 assert src.lstrip().startswith('#version '),fname
 src_nocom=re.sub(r'/\*.*?\*/|//[^\n]*','',src,flags=re.S)
 identifiers=re.findall(r'\b(?:float|vec[234]|ivec[234]|uvec[234]|uint|int|bool|mat[234]|sampler2D|image2D)\s+([A-Za-z_][A-Za-z0-9_]*)',src_nocom)
 assert not (set(identifiers)&reserved),(fname,set(identifiers)&reserved)
 assert len(src)>100,fname
exe=os.environ.get('IRIS_PINNED_GLSLANG_VALIDATOR')
if source_only:
 print('PASS complete exact-expanded B GLSL source and reserved identifier check (real compiler follows in inherited stage)')
elif exe:
 v=subprocess.run([exe,'--version'],capture_output=True,text=True,check=True)
 assert '16.5' in v.stdout,(exe,v.stdout)
 with tempfile.TemporaryDirectory(prefix='iris26876_expanded_glsl_') as td:
  for fn,src in files.items():
   p=Path(td)/fn;p.write_text(src)
   subprocess.run([exe,'-S',fn.rsplit('.',1)[-1],str(p)],check=True)
 print('PASS pinned glslang 16.5 compiled all four exact expanded shader sources')
else:
 print('BLOCKED pinned glslang 16.5 NOT RUN: four expanded shader source checks only; no compiler pass claimed')
 raise SystemExit(2)
