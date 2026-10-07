#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv)<3: raise SystemExit("usage: verify_26779_inherited_glsl.py BASE CAND [--compiler PATH] [--out DIR]")
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); compiler=None; out=None; i=3
while i<len(sys.argv):
 if sys.argv[i]=="--compiler": compiler=sys.argv[i+1]; i+=2
 elif sys.argv[i]=="--out": out=Path(sys.argv[i+1]); i+=2
 else: raise SystemExit("unknown arg "+sys.argv[i])
IRIS=Path("app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt")
STACK=Path("app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt")
for rel in (IRIS,STACK):
 assert hashlib.sha256((base/rel).read_bytes()).digest()==hashlib.sha256((cand/rel).read_bytes()).digest(),f"shader carrier changed: {rel}"
def assets(r):
 rr=Path(r)/"app/src/main/assets/shaders"
 return {str(p.relative_to(rr)):hashlib.sha256(p.read_bytes()).hexdigest() for p in rr.rglob("*") if p.is_file()}
a,b=assets(base),assets(cand); assert a==b,(len(a),len(b))
print(f"PASS 26779 inherited asset shader universe byte-identical: {len(a)} files")
def vals(root,rel):
 text=(root/rel).read_text()
 return {m.group(1):textwrap.dedent(m.group(2)).strip("\n")+"\n" for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
iv=vals(cand,IRIS); sv=vals(cand,STACK)
common=iv["common"]
shaders={
 "bipolarColorTrust26769":iv["bipolarColorTrust26769"].replace("$common",common),
 "seed":iv["seed"].replace("$common",common),
 "EDGE_FALSE_COLOR_SUPPRESSOR_26778":sv["EDGE_FALSE_COLOR_SUPPRESSOR_26778"],
}
decl=re.compile(r'\b(?:void|bool|int|uint|float|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler\w*|usampler\w*|image\w*|uimage\w*)\s+([A-Za-z_]\w*)')
for name,src in shaders.items():
 bad=[x for x in decl.findall(src) if x.startswith("gl_") or "__" in x or (len(x)>1 and x[0]=="_" and x[1].isupper())]
 assert not bad,(name,bad)
 print(f"PASS 26779 inherited reserved-identifier scan {name}: declarations={len(decl.findall(src))} sha256={hashlib.sha256(src.encode()).hexdigest()}")
if out:
 out.mkdir(parents=True,exist_ok=True)
 for n,s in shaders.items(): (out/f"{n}.comp").write_text(s)
if compiler:
 c=Path(compiler); assert c.exists()
 with tempfile.TemporaryDirectory(prefix="iris26779_glsl_") as td:
  td=Path(td)
  for n,s in shaders.items():
   f=td/f"{n}.comp"; f.write_text(s)
   p=subprocess.run([str(c),"-S","comp",str(f)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   print(p.stdout,end="")
   if p.returncode: raise SystemExit(f"glslang failed: {n}")
   print(f"PASS 26779 pinned real glslang recompile inherited shader: {n}")
print("PASS 26779 shader ownership: zero modified runtime-expanded shaders; exact 26778 carriers/assets preserved")
