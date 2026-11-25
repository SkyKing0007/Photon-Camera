#!/usr/bin/env python3
import argparse,hashlib,json,pathlib,re,subprocess,sys,tempfile,importlib.util
R=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,default=R);p.add_argument('--inventory',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--compile',action='store_true');o=p.parse_args()
root=o.root.resolve();native=root/'app/src/main/cpp/iris26985c_lkr2420';lk=native/'tools/lkr-lite/src/main/cpp';srp=native/'tools/sr-pipeline/src/main/cpp';cm=(lk/'CMakeLists.txt').read_text()
rows=[]
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def add(name,src,inc,defs=()):
 files={}
 def walk(f):
  rel=f.relative_to(root).as_posix()
  if rel in files:return
  files[rel]=sha(f)
  for include in re.findall(r'^\s*#\s*include\s+"([^"\n]+)"',f.read_text(),re.M):
   path=f.parent/include
   if not path.is_file():path=inc/include
   walk(path.resolve())
 walk(src)
 assert re.search(r'^#version',src.read_text(),re.M),src
 rows.append(dict(name=name,source=src.relative_to(root).as_posix(),include=inc.relative_to(root).as_posix(),defines=list(defs),files=files))
for n in re.search(r'set\(LKRL_SHADERS (.*?)\)',cm).group(1).split():add(n,lk/'shaders'/f'{n}.comp',lk/'shaders')
for i in (1,2):add('adj_s'+str(i),lk/'shaders/adj.comp',lk/'shaders',[f'ADJ_SCALE={i}'])
for n in re.search(r'foreach\(sh (resid weight_tdet .*?)\)',cm).group(1).split():add('lkr_'+n,lk/'shaders/lkr'/f'{n}.comp',lk/'shaders/lkr')
add('srp_align',srp/'shaders/align.comp',srp/'shaders')
assert len(rows)==len({x['name'] for x in rows})==47,len(rows)
manifest={'cmake_sha256':sha(lk/'CMakeLists.txt'),'variants':rows}
f=R/'26987_NATIVE_SHADER_INVENTORY.json'
if o.inventory:f.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
else:assert json.loads(f.read_text())==manifest,'native shader inventory drift'
spec=importlib.util.spec_from_file_location('identifier_audit',R/'verify_26987_v6_current_glsl.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
for f in sorted({f for x in rows for f in x['files']}):audit.lexical_check((root/f).read_text(),f)
print(f'PASS {len(rows)} exact native Vulkan CMake variants, recursive include SHA hashes and reserved identifier audit')
if o.compile:
 tools=R/'.photon_26904_incremental_work/real_shader_tools/glslang';compiler=next(x for x in tools.rglob('*') if x.is_file() and x.name in ('glslang','glslangValidator'))
 assert '16.5.0' in subprocess.check_output([str(compiler),'--version'],text=True)
 out=R/'photon_26987_outputs';out.mkdir(exist_ok=True);failures=[]
 with (out/'26987_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').open('w') as log,tempfile.TemporaryDirectory() as t:
  for cmd in ([str(compiler),'--version'],['spirv-val','--version'],['spirv-opt','--version']):subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
  for x in rows:
   spv=pathlib.Path(t)/f"{x['name']}.spv";opt=spv.with_suffix('.opt.spv')
   commands=[[str(compiler),'-V','--target-env','vulkan1.1','-S','comp','-I'+str(root/x['include']),*('-D'+v for v in x['defines']),'-o',str(spv),str(root/x['source'])],['spirv-val','--target-env','vulkan1.1',str(spv)],['spirv-opt','--target-env=vulkan1.1','-O',str(spv),'-o',str(opt)],['spirv-val','--target-env','vulkan1.1',str(opt)]]
   for cmd in commands:
    log.write('RUN '+' '.join(cmd)+'\n');log.flush();r=subprocess.run(cmd,capture_output=True,text=True);log.write(r.stdout+r.stderr);log.flush()
    if r.returncode:print(x['name'],r.stdout,r.stderr,flush=True);failures.append(x['name']);break
   else:log.write(f"PASS {x['name']} {sha(spv)} {sha(opt)}\n")
  assert not failures,failures
  log.write(f'PASS {len(rows)}/{len(rows)} private Vulkan variants real compile/opt/val\n')
