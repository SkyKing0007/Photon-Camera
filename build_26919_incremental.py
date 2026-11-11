#!/usr/bin/env python3
"""26919 guarded successor: EXACT successful 26918 compiled candidate, 3-file
B Photo Super Res OFF-only CFA-clipping-aware FCC, untouched smooth-white WB.
The successful 26917 physical CFA halo and all original build gates are frozen.
"""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
WORK=R/'.photon_26919_work';OUT=R/'photon_26919_outputs'
ART=WORK/'26918_success.zip';BASE=WORK/'authority_26918';CAND=WORK/'candidate_26919'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=42895817879;COMMIT='00a22e03efa3ed4c5fc80a4e818046201d85760e';ART_ID=13800448678
ART_SHA='e44d33a2c238edeba39655c6a9ac56b9aadb76250a4684a6e940a9f45bddcb68'
TAR_SHA='fb229c8e275e3d52077be7f7e74c46ca8d52dce03184f231c5e88bedc528658c'
BUILDER_SHA='a0012a9bdeafcfe95917cfa43bc91ce84af6cf7132422dcc9f016f8c6e71320b'
WORKFLOW_SHA='66babec55970e4cbf341dc5e9a32a4f25215d681723f53a002b7da9725563c28'
PRIOR_APK_SHA='b93ba092f45dfada55cffb06fb9f9017afd15e03332c2ea8cdd8a532f6f27168'
APKNAME='IrisCamera-0.9726919-26919-iris-rawr-debug.apk'
PROTECTED_BORDER='26919_FROZEN_26917_BORDER.sha256'

def fail(msg):raise RuntimeError('26919 BLOCKED: '+str(msg))
def sha(p):
 d=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):d.update(b)
 return d.hexdigest()
def parse(p):
 d={}
 for ln in p.read_text().splitlines():
  h,name=ln.split('  ',1)
  if name in d or len(h)!=64 or not name.startswith('app/') or '..' in pathlib.PurePosixPath(name).parts:fail('bad SHA row '+ln)
  d[name]=h
 return d
def scan(src):
 d={};root=src/'app/src'
 if root.is_symlink() or not root.is_dir():fail('Android runtime source missing/symlinked')
 members=list(root.rglob('*'))+[src/'app/build.gradle',src/'app/version.properties']
 for p in members:
  if p.is_symlink():fail('runtime source symlink '+str(p))
  if p.is_file():d[p.relative_to(src).as_posix()]=sha(p)
 return d
def exact(src,manifest,title):
 expected=parse(manifest);actual=scan(src)
 if expected!=actual:
  miss=sorted(expected.keys()-actual.keys());extra=sorted(actual.keys()-expected.keys())
  wrong=sorted(p for p in expected.keys()&actual.keys() if expected[p]!=actual[p])
  fail(f'{title}: missing={miss[:5]} extra={extra[:5]} wrong={wrong[:9]}')
 print('PASS',title,len(expected),'source files');return expected
def border(src):
 expected=parse(R/PROTECTED_BORDER)
 if len(expected)!=7:fail('26917 border protection missing seven exact hashes')
 for p,h in expected.items():
  if not (src/p).is_file() or sha(src/p)!=h:fail('26917 physical-CFA-border invariant broken '+p)
 print('PASS 26917 physical-border exact 7-file source/SPV protection')
def seal():
 from verify_26919_handoff import verify
 verify();print('PASS sealed 26919 B OFF-only clipped-CFA cross-edge FCC isolation, immutable 26917 border and WB')
def gh(path,token):
 req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
 with urllib.request.urlopen(req,timeout=100) as q:return json.load(q)
def fetch():
 seal();tok=os.getenv('GITHUB_TOKEN','')
 if not tok:fail('missing GitHub token for actual successful 26918 artifact')
 if os.getenv('GITHUB_REPOSITORY',REPO)!=REPO or os.getenv('GITHUB_REF_NAME',BRANCH)!=BRANCH:fail('unexpected repo/branch')
 run=gh('actions/runs/'+str(RUN),tok);art=gh('actions/artifacts/'+str(ART_ID),tok)
 if run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH or run.get('id')!=RUN:fail('wrong last successful run')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:fail('wrong successful 26918 artifact')
 WORK.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error',
  '-H','Authorization: Bearer '+tok,'-H','Accept: application/vnd.github+json',
  f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('26918 ZIP hash mismatch')
 print('PASS actual successful 26918 Actions and published digest',ART_SHA)
def safe_tar(tarpath,dest):
 with tarfile.open(tarpath,'r:gz') as t:
  for m in t.getmembers():
   p=pathlib.PurePosixPath(m.name)
   if p.is_absolute() or not p.parts or p.parts[0]!='app' or '..' in p.parts or not(m.isfile() or m.isdir()):fail('bad TAR member '+m.name)
  t.extractall(dest,filter='data')
def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('26918 successfully published ZIP missing/hash mismatch')
 for x in (BASE,CAND):
  if x.exists():shutil.rmtree(x)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  prefix='photon_26918_outputs/'
  def get(n):
   p=prefix+n
   if p not in z.namelist():fail('missing actual 26918 receipt '+p)
   return z.read(p)
  b=get('26918_candidate_app_source.tar.gz')
  if hashlib.sha256(b).hexdigest()!=TAR_SHA:fail('26918 compiled TAR hash mismatch')
  if get('26918_PREBUILD_SEALED_APP.sha256')!=(R/'26919_BASE_26918_FULL_APP.sha256').read_bytes():fail('published 26918 full source manifest mismatch')
  if BUILDER_SHA not in get('26918_ACTUAL_EXECUTED_BUILDER.sha256').decode() or hashlib.sha256(get('ACTUAL_EXECUTED_build_26918_incremental.py')).hexdigest()!=BUILDER_SHA:fail('executed 26918 builder mismatch')
  if WORKFLOW_SHA not in get('26918_ACTUAL_EXECUTED_WORKFLOW.sha256').decode() or hashlib.sha256(get('ACTUAL_EXECUTED_build-26918-change-aware.yml')).hexdigest()!=WORKFLOW_SHA:fail('executed 26918 workflow mismatch')
  if PRIOR_APK_SHA not in get('26918_APK.sha256').decode():fail('26918 APK mismatch')
  for marker in ['REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS']:
   if marker not in get('26918_COMPILER_STATUS.txt').decode():fail('26918 successful compiler receipt missing '+marker)
  for marker in ['REAL PINNED GLSL COMPILE: PASS','16.5.0']:
   if marker not in get('26918_CHROMA_SHADER_REAL_COMPILER.txt').decode():fail('26918 actual ESSL300 shader receipt missing '+marker)
  if 'REAL SPIR-V VALIDATION: PASS' not in get('26918_CHROMA_SHADER_SPIRV_VALIDATED.txt').decode():fail('26918 actual ESSL310/SPIR-V historical missing')
  temp=WORK/'26918_candidate.tar.gz';temp.write_bytes(b)
 safe_tar(temp,BASE)
 exact(BASE,R/'26919_BASE_26918_FULL_APP.sha256','actual 26918 compiled source')
 border(BASE)
 shutil.copytree(BASE,CAND)
 changes=(R/'26919_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=set((R/'26919_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26919_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if len(changes)!=3 or len(set(changes))!=3 or added or deleted:fail('wrong 26919 runtime scope')
 for p in changes:
  target=CAND/p;overlay=R/'handoff_payload_26919'/p
  if not overlay.is_file() or not target.is_file():fail('wrong overlay/target '+p)
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(overlay,target)
 before=parse(R/'26919_BASE_26918_FULL_APP.sha256')
 after=exact(CAND,R/'26919_PRECOMPILE_EXPECTED_FULL_APP.sha256','26919 candidate-first exact transformation')
 if set(after)-set(before) or set(before)-set(after) or {p for p in before if before[p]!=after[p]}!=set(changes):fail('unexpected runtime source scope')
 border(CAND)
 if 'VERSION_BUILD=26919' not in (CAND/'app/version.properties').read_text():fail('wrong version')
 if not (R/'gradlew').is_file() or not (R/'app').is_dir():fail('Android Gradle project unavailable')
 live=R/'app'
 if (live/'src').exists():shutil.rmtree(live/'src')
 shutil.copytree(CAND/'app/src',live/'src')
 shutil.copy2(CAND/'app/version.properties',live/'version.properties')
 shutil.copy2(CAND/'app/build.gradle',live/'build.gradle')
 exact(R,R/'26919_PRECOMPILE_EXPECTED_FULL_APP.sha256','26919 authority-seeded live source')
 border(R)
 OUT.mkdir(exist_ok=True)
 (OUT/'26919_SOURCE_SCOPE.txt').write_text('BASE=26918-success run='+str(RUN)+' commit='+COMMIT+' artifact='+str(ART_ID)+'\nsource=2036 runtime_changed=3 protected=2033 added=0 deleted=0 border_frozen=7\nchanged='+'\n'.join(changes)+'\n')
 print('PASS exact successful 26918 runtime + 3-path B OFF-only clipped-CFA FCC guard')
def shader_runtime_source():
 kt=(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
 anchor='val shader="""';end='""".trimIndent()'
 if kt.count(anchor)!=1 or kt.count(end)!=1:fail('bad Kotlin raw GLSL extraction')
 raw=kt.split(anchor,1)[1].split(end,1)[0].splitlines()
 while raw and not raw[0].strip():raw.pop(0)
 while raw and not raw[-1].strip():raw.pop()
 minimum=min(len(line)-len(line.lstrip(' \t')) for line in raw if line.strip())
 return '\n'.join(line[minimum:] for line in raw)
def verify_compiled():
 seal();baseline=exact(R,R/'26919_PRECOMPILE_EXPECTED_FULL_APP.sha256','26919 post-real-GLSL full source immutability');border(R)
 # Preserve actual 26918 pinned import Vulkan compile, not only its old PASS receipt.
 target=R/'.photon_26904_incremental_work/real_shader_tools/26917_amaze_import'
 import_shader=R/'app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp'
 include=R/'app/src/main/cpp/iris26856/amaze/shaders/amaze_tile.glsl'
 expanded=import_shader.read_text().replace('#include "amaze_tile.glsl"','#line 1 20\n'+include.read_text()+'\n#line 6 21')
 if (target/'amaze_import_expanded.comp').read_text()!=expanded or (target/'amaze_import.spv').read_bytes()!=(R/'app/src/main/assets/iris26856/rawr/amaze/spv/amaze_import.spv').read_bytes():fail('26917 preserved AMaZE compiler input/SPV mismatch')
 # The inherited 26917 compiler is re-executed above, but its script still
 # writes receipts to photon_26917_outputs/ (not new 26919 output folder).
 # This gate verifies CURRENT-RUN native compiler evidence, never an assumed
 # old receipt or a synthetic PASS; the source and SPV were checked above.
 prior_native=R/'photon_26917_outputs'
 native_glsl=prior_native/'26917_AMAZE_IMPORT_SHADER_REAL_COMPILER.txt'
 native_spirv=prior_native/'26917_AMAZE_IMPORT_SPIRV_VALIDATED.txt'
 native_optimized=target/'amaze_import.opt.spv'
 for p in (native_glsl,native_spirv,native_optimized):
  if not p.is_file() or p.stat().st_size<64:fail('26917 real native SPV compiler gate absent: '+str(p))
 glsl_receipt=native_glsl.read_text()
 spirv_receipt=native_spirv.read_text()
 if ('REAL PINNED GLSL COMPILE: PASS' not in glsl_receipt or
     'glslang 16.5.0' not in glsl_receipt or
     sha(target/'amaze_import_expanded.comp') not in glsl_receipt or
     sha(target/'amaze_import.spv') not in glsl_receipt):
  fail('26917 pinned native compiler receipt does not match executed source and SPV')
 if ('REAL SPIR-V VALIDATION: PASS' not in spirv_receipt or
     'spirv-opt --target-env=vulkan1.1 -O' not in spirv_receipt or
     sha(target/'amaze_import.spv') not in spirv_receipt or
     sha(native_optimized) not in spirv_receipt):
  fail('26917 real Vulkan SPIR-V optimization/validation receipt mismatch')
 # New source is ESSL300. Compile exact runtime bytes as ESSL300; a second
 # semantically identical ESSL310 test variant runs genuine spirv-val/opt.
 c=R/'.photon_26904_incremental_work/real_shader_tools/26918_chroma'
 runtime=c/'post_amaze_exact_300.frag';spv=c/'post_amaze_310.spv';opt=c/'post_amaze_310.opt.spv'
 receipt=R/'photon_26918_outputs/26918_CHROMA_SHADER_REAL_COMPILER.txt';validation=R/'photon_26918_outputs/26918_CHROMA_SHADER_SPIRV_VALIDATED.txt'
 for p in [runtime,spv,opt,receipt,validation]:
  if not p.is_file() or p.stat().st_size<64:fail('missing inherited 26918 WB shader compiler file '+str(p))
 if runtime.read_text()!=shader_runtime_source()+'\n' or '16.5.0' not in receipt.read_text() or 'PASS' not in validation.read_text():fail('inherited 26918 runtime post-AMaZE shader differs')
 if spv.read_bytes()[:4]!=bytes.fromhex('03022307'):fail('inherited 26918 post-AMaZE SPIR-V invalid header')
 for path in (R/'photon_26907_outputs/26907_HUE_SHADER_REAL_COMPILER.txt',R/'photon_26907_outputs/26907_HUE_SHADER_SPIRV_VALIDATED.txt',R/'photon_26908_outputs/26908_RENDER_SHADER_REAL_COMPILER.txt',R/'photon_26908_outputs/26908_RENDER_SHADER_SPIRV_VALIDATED.txt'):
  if not path.is_file() or 'PASS' not in path.read_text():fail('historical real shader receipt missing '+str(path))
 for name in ('26904_GLSL_REAL_COMPILER.txt','26904_SPIRV_VALIDATED.txt','26904_SPEKTRA_GLSLANG_CMAKE_HANDOFF.txt'):
  if not (R/'photon_26904_incremental_outputs'/name).is_file():fail('historical SPIRV/CMake receipt missing '+name)
 for name in ('26906_TONE_SHADER_REAL_COMPILER.txt','26906_TONE_SHADER_SPIRV_VALIDATED.txt'):
  if not (R/'photon_26906_outputs'/name).is_file():fail('26906 historical shader receipt missing '+name)
 # Exact new 26919 FCC median AND reconstruction shaders MUST be compiled
 # using pinned glslang 16.5.0, validated before and after SPIR-V optimizer.
 fcc=R/'.photon_26904_incremental_work/real_shader_tools/26919_fcc'
 fcc_receipt=OUT/'26919_FCC_SHADER_REAL_COMPILER.txt'
 fcc_val=OUT/'26919_FCC_SHADER_SPIRV_VALIDATED.txt'
 kt=(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt').read_text()
 for field in ('medianChroma','reconstructChroma'):
  marker='val '+field+' = """';terminator='""".trimIndent()'
  if kt.count(marker)!=1:fail('26919 FCC Kotlin shader anchor absent/duplicated: '+field)
  frag=kt.split(marker,1)[1].split(terminator,1)[0].splitlines()
  while frag and not frag[0].strip():frag.pop(0)
  while frag and not frag[-1].strip():frag.pop()
  indent=min(len(l)-len(l.lstrip(' \t')) for l in frag if l.strip())
  src='\n'.join(l[indent:] for l in frag)+'\n'
  original=fcc/(field+'_exact_300.frag')
  compiled=fcc/(field+'.spv');optimized=fcc/(field+'.opt.spv')
  for p in [original,compiled,optimized]:
   if not p.is_file() or p.stat().st_size<128:fail('26919 real pinned FCC shader file missing '+str(p))
  if original.read_text()!=src or compiled.read_bytes()[:4]!=bytes.fromhex('03022307') or optimized.read_bytes()[:4]!=bytes.fromhex('03022307'):
   fail('26919 actual FCC source/compiler bytes mismatch '+field)
  for p in [original,compiled,optimized]:
   if sha(p) not in fcc_receipt.read_text() and sha(p) not in fcc_val.read_text():fail('26919 unsealed compiler source/SPIRV '+str(p))
 if not fcc_receipt.is_file() or not fcc_val.is_file():fail('26919 new compiler receipt missing')
 if '16.5.0' not in fcc_receipt.read_text() or 'REAL PINNED GLSL COMPILE: PASS' not in fcc_receipt.read_text() or 'REAL SPIR-V VALIDATION: PASS' not in fcc_val.read_text() or 'spirv-opt' not in fcc_val.read_text():fail('26919 real FCC GLSL/SPIRV compiler evidence invalid')
 (OUT/'26919_REAL_FCC_SOURCE_SHA256.txt').write_text(sha(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt')+'  GlesIris26856RawrFalseColor.kt\nREAL PINNED GLSL COMPILE: PASS\n')
 OUT.mkdir(exist_ok=True)
 (OUT/'26919_PREBUILD_SEALED_APP.sha256').write_text(''.join(f'{baseline[p]}  {p}\n' for p in sorted(baseline)))
 print('PASS 26919 pinned FCCx2 GLSL/SPIR-V validation plus inherited WB, immutable 26917 border')
def finalize():
 expected=exact(R,OUT/'26919_PREBUILD_SEALED_APP.sha256','26919 full assemble postbuild frozen source');border(R)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one APK required '+repr(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('APK invalid/small')
 gradle=OUT/'26919_gradle_assemble.log'
 if not gradle.is_file():fail('missing actual Gradle build log')
 log=gradle.read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL']
 if any(t not in log for t in tasks):fail('missing actual Kotlin/Java/NDK/assemble task '+str([t for t in tasks if t not in log]))
 if not (OUT/'26919_REAL_FCC_SOURCE_SHA256.txt').is_file():fail('26919 new FCC compiled shader receipt absent')
 (OUT/'26919_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26919_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (actual 26919 FCC ESSL300 x2 and inherited 26918/26917/26907/26908/26904)\nREAL SPIR-V VALIDATION: PASS (26919 FCC GLSL310 original/optimized, inherited original Vulkan)\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a and armeabi-v7a, 26917 physical-border unchanged)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS\n26917 PHYSICAL BORDER FROZEN: PASS\nAPK '+APKNAME+' SHA256 '+sha(R/APKNAME)+'\n')
 (OUT/'26919_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 (OUT/'26919_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26919_incremental.py')+'  build_26919_incremental.py\n')
 native_receipt=R/'photon_26906_outputs/26906_NATIVE_CACHE_PATCH_REPLAY.json'
 if not native_receipt.is_file():fail('native cache patch replay gate missing')
 native=json.loads(native_receipt.read_text())
 if native.get('script_sha256')!=sha(R/'verify_26906_native_cache.py') or native.get('mode') not in ('cold','cached-replay'):fail('native cache replay receipt mismatch')
 if native['mode']=='cached-replay' and len(native.get('sources',[]))!=2:fail('invalid native ABI replay')
 shutil.copy2(native_receipt,OUT/'26919_NATIVE_CACHE_PATCH_REPLAY.json')
 (OUT/'26919_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','local')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','local')+'\ngithub_job='+os.getenv('GITHUB_JOB','local')+'\n')
 workflow=R/'.github/workflows/build-26919-change-aware.yml'
 shutil.copy2(R/'build_26919_incremental.py',OUT/'ACTUAL_EXECUTED_build_26919_incremental.py')
 shutil.copy2(workflow,OUT/'ACTUAL_EXECUTED_build-26919-change-aware.yml')
 (OUT/'26919_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(workflow)+'  .github/workflows/build-26919-change-aware.yml\n')
 base=parse(R/'26919_BASE_26918_FULL_APP.sha256');changes=set((R/'26919_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 (OUT/'26919_PROTECTED_SOURCE.sha256').write_text(''.join(f'{base[p]}  {p}\n' for p in sorted(base) if p not in changes))
 shutil.copy2(R/'26919_FROZEN_26917_BORDER.sha256',OUT/'26919_FROZEN_26917_BORDER.sha256')
 shutil.copy2(R/'26919_BASE_26918_FULL_APP.sha256',OUT/'26919_BASE_26918_FULL_APP.sha256')
 shutil.copy2(R/'26919_CHANGED_RUNTIME_ALLOWLIST.txt',OUT/'26919_CHANGED_RUNTIME_ALLOWLIST.txt')
 (OUT/'26919_VERSION.txt').write_text('VERSION_NAME=0.9726919\nVERSION_BUILD=26919\n')
 tar=OUT/'26919_candidate_app_source.tar.gz'
 with tarfile.open(tar,'w:gz',compresslevel=1) as z:
  for p in sorted(expected):
   f=R/p;info=z.gettarinfo(str(f),arcname=p);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   with f.open('rb') as inp:z.addfile(info,inp)
 (OUT/'26919_candidate_app_source.tar.gz.sha256').write_text(sha(tar)+'  26919_candidate_app_source.tar.gz\n')
 print('PASS one actual 26919 APK, exact compiled source TAR, 2033 protected source hashes and immutable 26917 border',sha(R/APKNAME))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['seal','fetch','prepare','verify-compiled','finalize']);args=p.parse_args()
 try:globals()[args.command.replace('-','_')]()
 except Exception as e:print('ERROR',str(e),file=sys.stderr);sys.exit(1)
