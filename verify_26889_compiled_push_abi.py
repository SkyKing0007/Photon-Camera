#!/usr/bin/env python3
"""REPLAY REAL successful 26888 shader push-constant ABI vs current C++.

Negative historical 26888 60-byte host must fail; 26889 corrected 64-byte
host must compile and match all SPIR-V Offsets. This is not new shader compile.
"""
import pathlib,re,struct,subprocess,tempfile,sys
assert len(sys.argv)==4,'USAGE actual-26888-prod.spv base-root candidate-root'
spv,base,cand=map(pathlib.Path,sys.argv[1:])
assert spv.is_file() and spv.stat().st_size>100
raw=spv.read_bytes();assert len(raw)%4==0
w=struct.unpack('<%dI'%(len(raw)//4),raw);assert w[0]==0x07230203
names={};ofs={};blocks=set();i=5
while i<len(w):
 op=w[i]&65535;wc=w[i]>>16;v=w[i+1:i+wc];assert wc>=1
 if op==6 and len(v)>2:
  names[v[0],v[1]]=b''.join(struct.pack('<I',x) for x in v[2:]).split(b'\0')[0].decode(errors='replace')
 elif op==72 and len(v)>3 and v[2]==35:ofs[v[0],v[1]]=v[3]
 elif op==71 and len(v)>1 and v[1]==2:blocks.add(v[0])
 i+=wc
fields={'tiles':0,'robustnessNorm':8,'readNoise':12,'maxMotionNorm':16,'uniformExposure':20,'frameWeight':24,'alignTiles':32,'alignHalfTile':40,'cropX':44,'cropY':48,'offsetX':52,'offsetY':56,'supportMeasured':60}
observed={s:ofs[k] for k,s in names.items() if k in ofs and k[0] in blocks and s in fields}
assert observed==fields,(observed,fields)
rel='app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp'
for old,root in ((True,base),(False,cand)):
 s=(root/rel).read_text()
 m=re.search(r'(struct FreqMergePc\s*\{.*?\};)',s,re.S);assert m
 snippet=m.group(1)
 c='#include <cstdint>\n#include <cstddef>\n'+snippet+'\n'
 for name,pos in fields.items():
  if name=='tiles':continue
  cp='alignTilesX' if name=='alignTiles' else name
  c+=f'static_assert(offsetof(FreqMergePc,{cp})=={pos},"compiled SPV offset {name}");\n'
 c+='static_assert(sizeof(FreqMergePc)==64,"compiled SPV push total");\nint main(){return 0;}\n'
 with tempfile.TemporaryDirectory() as td:
  p=pathlib.Path(td)/'check.cpp';p.write_text(c)
  r=subprocess.run(['c++','-std=c++17','-Wall','-Wextra','-Werror','-fsyntax-only',str(p)],capture_output=True,text=True)
  if old:
   assert r.returncode!=0 and 'static assertion failed' in r.stderr,'26888 broken 60-byte host incorrectly passed compiled ABI test'
  else:assert r.returncode==0,(r.stdout,r.stderr)
print('PASS 26888 actual compiled production SPIR-V offset negative original 60-byte host and positive exact 26889 64-byte host')
