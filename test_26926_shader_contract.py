#!/usr/bin/env python3
"""26925 V1 reserved ESSL coherent, V2 Vulkan precision, V3 JNI ABI reproduction."""
from pathlib import Path
import sys,re,textwrap,subprocess
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26926' if '--payload' in sys.argv else R
j=P/'app/src/main/java/com/hinnka/mycamera/processor'
c=P/'app/src/main/cpp/iris26864'
def shader(file,name):
 s=(j/file).read_text();m=list(re.finditer(re.escape(name)+r'\s*=\s*"""',s))
 assert len(m)==1,(file,name,len(m))
 t=textwrap.dedent(s[m[0].end():].split('""".trimIndent()',1)[0]).strip()+'\n'
 assert t.startswith('#version 300 es') and t.count('void main()')==1
 return t
reserved={'coherent','precision','restrict','volatile','readonly','writeonly','shared','sample','subroutine','filter','attribute','varying','uniform','layout','invariant','centroid','flat','smooth','patch','buffer','struct','const','in','out','inout'}
def illegal(s):
 s=re.sub(r'/\*.*?\*/',' ',s,flags=re.S);s=re.sub(r'//[^\n]*','',s)
 return [m.group(1) for m in re.finditer(r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234])\s+([A-Za-z_][A-Za-z0-9_]*)\b',s) if m.group(1) in reserved]
for file,name in [('GlesIris26870PostAmazeChroma.kt','val shader'),('GlesIris26856RawrFalseColor.kt','val medianChroma'),('GlesIris26856RawrFalseColor.kt','val reconstructChroma')]:
 s=shader(file,name)
 assert not illegal(s),(file,name,illegal(s))
 assert illegal(re.sub(r'void\s+main\s*\(\s*\)\s*\{','void main(){ float coherent=0.; ',s,count=1))==['coherent']
 assert illegal(re.sub(r'void\s+main\s*\(\s*\)\s*\{','void main(){ float precision=0.; ',s,count=1))==['precision']
for name in ['bridge/Iris26923WronskiFinalize.comp','Iris26885WronskiChromaGuide.comp','Iris26880WaveletCopy.comp']:
 s=(c/name).read_text();assert s.startswith('#version 450') and not illegal(s),(name,illegal(s))
 assert illegal(re.sub(r'void\s+main\s*\(\s*\)\s*\{','void main(){ float precision=1.; ',s,count=1))==['precision']
cpp=(c/'Iris26864FrozenDirectRawrRunner.cpp').read_text()
assert 'iris26920ArmWasPresent' in cpp and 'iris26926Fallback' in cpp
for f in ('compile_26926_shaders.sh','compile_26926_hr_spirv.sh'):
 src=(R/f).read_text(); assert '16.5.0' in src and 'spirv-val' in src and 'spirv-opt' in src
 subprocess.run(['bash','-n',str(R/f)],check=True)
print('PASS 26926 current 3 ESSL, 3 Vulkan static syntax/reserved names; 26925 V1 coherent/V2 precision negative controls; real compiler scripts intact')
