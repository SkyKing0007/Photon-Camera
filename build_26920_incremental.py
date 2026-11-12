#!/usr/bin/env python3
"""26920 guarded active B SR ON LK refinement from exact compiled successful 26917.
Historical 26919 17-stage build mechanics, real compiler and artifact gates retained.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, shutil, subprocess, sys, tarfile, urllib.request, zipfile
R=pathlib.Path(__file__).resolve().parent
WORK=R/'.photon_26920_work';OUT=R/'photon_26920_outputs'
ART=WORK/'26917_success.zip';BASE=WORK/'authority_26917';CAND=WORK/'candidate_26920'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=42859946714;COMMIT='83ad93725baf8de8fa7653235e93e4fc0ffeaebb';ART_ID=13786011058
ART_SHA='ae09ca810fee66057f173ccc65efbe18772c2561b0c96e8931763da748b2e57b'
TAR_SHA='d82d550362b22a5486098335a41e3817b1417256205c356c6ef837aceb7d68a1'
BUILDER_SHA='31eebc26fa69a71da1c82bd7a304bd7d8c4e8158d598df12a92a5b8e21a535bf'
WORKFLOW_SHA='8d75c66c70ab0c2a6be029a5707e52fea05d3c4a1075ec8be70c04e27ea4afcb'
PRIOR_APK_SHA='3846787d39e59084098d1771f7b8084fd12c86e36157cc098c0961fdf9773c18'
APKNAME='IrisCamera-0.9726920-26920-iris-rawr-debug.apk'
PROTECTED_BORDER='26920_FROZEN_26917_BORDER.sha256'

def fail(message):raise RuntimeError('26920 BLOCKED: '+str(message))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(4*1024*1024),b''):h.update(x)
 return h.hexdigest()
def parse(p):
 result={}
 for line in p.read_text().splitlines():
  h,name=line.split('  ',1)
  if name in result or len(h)!=64 or not name.startswith('app/') or '..' in pathlib.PurePosixPath(name).parts:fail('invalid SHA manifest '+line)
  result[name]=h
 return result
def scan(root):
 d={}
 for p in [*list((root/'app/src').rglob('*')),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('symlink in protected runtime source '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 return d
def exact(root,manifest,label):
 expected=parse(manifest);actual=scan(root)
 if expected!=actual:
  fail(f'{label} missing={sorted(expected.keys()-actual.keys())[:6]} extra={sorted(actual.keys()-expected.keys())[:6]} wrong={[p for p in expected if actual.get(p)!=expected[p]][:10]}')
 print('PASS',label,len(expected));return expected
def border(root):
 expected=parse(R/PROTECTED_BORDER)
 if len(expected)!=7:fail('26917 physical CFA border seven-file contract missing')
 for p,h in expected.items():
  if not (root/p).is_file() or sha(root/p)!=h:fail('modified successful 26917 physical CFA border '+p)
def seal():
 from verify_26920_handoff import verify
 verify();print('PASS 26920 sealed staged handoff, 26917 authority, 2021 protected')
def gh(path,token):
 request=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,
  headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
 with urllib.request.urlopen(request,timeout=100) as response:return json.load(response)
def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token:fail('missing GitHub token for real successful 26917 artifact')
 if os.getenv('GITHUB_REPOSITORY',REPO)!=REPO or os.getenv('GITHUB_REF_NAME',BRANCH)!=BRANCH:fail('unexpected branch/repository')
 run=gh('actions/runs/'+str(RUN),token);art=gh('actions/artifacts/'+str(ART_ID),token)
 if run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH or run.get('id')!=RUN:fail('incorrect successful 26917 Actions runtime authority')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:fail('incorrect published artifact')
 WORK.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error',
    '-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',
    f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('26917 published ZIP hash mismatch')
 print('PASS 26917 exact successful Actions run, commit, artifact, digest')
def safe_tar(tar,dest):
 with tarfile.open(tar,'r:gz') as t:
  for member in t.getmembers():
   p=pathlib.PurePosixPath(member.name)
   if p.is_absolute() or not p.parts or p.parts[0]!='app' or '..' in p.parts or not(member.isfile() or member.isdir()):fail('unsafe candidate TAR member '+member.name)
  t.extractall(dest,filter='data')
def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('26917 successful Actions artifact missing or altered')
 for path in (BASE,CAND):
  if path.exists():shutil.rmtree(path)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  prefix='photon_26917_outputs/'
  def get(name):
   path=prefix+name
   if path not in z.namelist():fail('26917 missing actual compiler/source receipt '+path)
   return z.read(path)
  body=get('26917_candidate_app_source.tar.gz')
  if hashlib.sha256(body).hexdigest()!=TAR_SHA:fail('26917 compiled source TAR SHA mismatch')
  if get('26917_PREBUILD_SEALED_APP.sha256')!=(R/'26920_BASE_26917_FULL_APP.sha256').read_bytes():fail('26917 published compiled manifest mismatch')
  if BUILDER_SHA not in get('26917_ACTUAL_EXECUTED_BUILDER.sha256').decode() or hashlib.sha256(get('ACTUAL_EXECUTED_build_26917_incremental.py')).hexdigest()!=BUILDER_SHA:fail('26917 actual executed runner wrong')
  if WORKFLOW_SHA not in get('26917_ACTUAL_EXECUTED_WORKFLOW.sha256').decode() or hashlib.sha256(get('ACTUAL_EXECUTED_build-26917-change-aware.yml')).hexdigest()!=WORKFLOW_SHA:fail('26917 executed workflow wrong')
  if PRIOR_APK_SHA not in get('26917_APK.sha256').decode():fail('26917 published APK SHA wrong')
  for marker in ['REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS']:
   if marker not in get('26917_COMPILER_STATUS.txt').decode():fail('missing successful 26917 real compiler receipt '+marker)
  if 'REAL PINNED GLSL COMPILE: PASS' not in get('26917_AMAZE_IMPORT_SHADER_REAL_COMPILER.txt').decode():fail('26917 real shader compile absent')
  if 'REAL SPIR-V VALIDATION: PASS' not in get('26917_AMAZE_IMPORT_SPIRV_VALIDATED.txt').decode():fail('26917 shader validation absent')
  tmp=WORK/'26917_candidate.tar.gz';tmp.write_bytes(body)
 safe_tar(tmp,BASE)
 exact(BASE,R/'26920_BASE_26917_FULL_APP.sha256','actual successful 26917 compiled source')
 border(BASE)
 shutil.copytree(BASE,CAND)
 changed=(R/'26920_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=set((R/'26920_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 if len(changed)!=17 or len(set(changed))!=17 or len(added)!=2 or (R/'26920_DELETED_RUNTIME_PATHS.txt').read_text():fail('wrong 26920 source scope')
 for name in changed:
  dst=CAND/name;src=R/'handoff_payload_26920'/name
  if not src.is_file() or (name in added)==dst.exists():fail('overlay is not approved source '+name)
  dst.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(src,dst)
 before=parse(R/'26920_BASE_26917_FULL_APP.sha256')
 after=exact(CAND,R/'26920_PRECOMPILE_EXPECTED_FULL_APP.sha256','exact candidate-first seventeen-path transformation')
 if set(after)-set(before)!=added or set(before)-set(after) or {p for p in before if before[p]!=after[p]}!=set(changed)-added:fail('protected-source mutation')
 border(CAND)
 if not (R/'gradlew').is_file() or not (R/'app').is_dir():fail('real Android Gradle project unavailable')
 current=R/'app'
 if (current/'src').exists():shutil.rmtree(current/'src')
 shutil.copytree(CAND/'app/src',current/'src')
 shutil.copy2(CAND/'app/version.properties',current/'version.properties')
 shutil.copy2(CAND/'app/build.gradle',current/'build.gradle')
 exact(R,R/'26920_PRECOMPILE_EXPECTED_FULL_APP.sha256','authority-seeded live Android source')
 border(R)
 OUT.mkdir(exist_ok=True)
 (OUT/'26920_SOURCE_SCOPE.txt').write_text('BASE=26917-success run='+str(RUN)+' commit='+COMMIT+' artifact='+str(ART_ID)+'\nsource=2038 runtime_changed=17 added=2 protected=2021 deleted=0 border_frozen=7 mode=ACTIVE_PER_LENS_LK\nchanged='+'\n'.join(changed)+'\n')
 print('PASS recovered actual 26917, active 26920 per-physical-lens B SR ON LK shaders and actual MotionTrace dual logs; seven frozen physical border files unchanged')
def verify_compiled():
 seal()
 unchanged=exact(R,R/'26920_PRECOMPILE_EXPECTED_FULL_APP.sha256','26920 source unchanged after real shader and native precompile')
 border(R)
 tool=R/'.photon_26904_incremental_work/real_shader_tools/26917_amaze_import'
 shader=R/'app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp'
 incl=R/'app/src/main/cpp/iris26856/amaze/shaders/amaze_tile.glsl'
 expanded=shader.read_text().replace('#include "amaze_tile.glsl"','#line 1 20\n'+incl.read_text()+'\n#line 6 21')
 if (tool/'amaze_import_expanded.comp').read_text()!=expanded or (tool/'amaze_import.spv').read_bytes()!=(R/'app/src/main/assets/iris26856/rawr/amaze/spv/amaze_import.spv').read_bytes():fail('26917 pinned native import compiled source mismatch')
 glsl=R/'photon_26917_outputs/26917_AMAZE_IMPORT_SHADER_REAL_COMPILER.txt'
 valid=R/'photon_26917_outputs/26917_AMAZE_IMPORT_SPIRV_VALIDATED.txt'
 for path in [glsl,valid,tool/'amaze_import.opt.spv']:
  if not path.is_file() or path.stat().st_size<64:fail('missing current-run real Vulkan GLSL / SPIR-V receipt '+str(path))
 if ('16.5.0' not in glsl.read_text() or sha(tool/'amaze_import_expanded.comp') not in glsl.read_text() or
     sha(tool/'amaze_import.spv') not in glsl.read_text() or
     sha(tool/'amaze_import.opt.spv') not in valid.read_text()):fail('current-run compiled GLSL/opt/SPV receipts do not match')
 for path in [R/'photon_26907_outputs/26907_HUE_SHADER_REAL_COMPILER.txt',R/'photon_26907_outputs/26907_HUE_SHADER_SPIRV_VALIDATED.txt',
              R/'photon_26908_outputs/26908_RENDER_SHADER_REAL_COMPILER.txt',R/'photon_26908_outputs/26908_RENDER_SHADER_SPIRV_VALIDATED.txt']:
  if not path.is_file() or 'PASS' not in path.read_text():fail('inherited ESSL compiler receipt missing '+str(path))
 # Mandatory new real Vulkan shader compile and optimizer/validator receipt,
 # checked against actual compiled candidate source, not historical proof.
 lkreceipt=R/'photon_26920_outputs/26920_LK_GLSL_SPIRV_REAL_COMPILER.txt'
 if not lkreceipt.is_file():fail('26920 active LK shader compiler and SPIR-V proof missing')
 lktext=lkreceipt.read_text()
 if '16.5.0' not in lktext:fail('26920 not pinned 16.5.0')
 for name,path in [
  ('lk_refine','app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/alignment/shaders/lk_refine.comp'),
  ('robust_photometric','app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/robust_photometric.comp')]:
  if sha(R/path) not in lktext:fail('26920 modified GLSL not real compiled '+name)
  for variant in ('prod','trace'):
   for suffix in ('.spv','.opt.spv'):
    spv=R/f'photon_26920_outputs/26920_lk_shaders/{name}_{variant}{suffix}'
    if not spv.is_file() or spv.stat().st_size<256 or sha(spv) not in lktext:fail('26920 actual modified GLSL SPIR-V missing '+str(spv))
 for name in ['26904_GLSL_REAL_COMPILER.txt','26904_SPIRV_VALIDATED.txt','26904_SPEKTRA_GLSLANG_CMAKE_HANDOFF.txt']:
  if not (R/'photon_26904_incremental_outputs'/name).is_file():fail('26904 V1/V2/V3 real compiler/NDK evidence missing '+name)
 for name in ['26906_TONE_SHADER_REAL_COMPILER.txt','26906_TONE_SHADER_SPIRV_VALIDATED.txt']:
  if not (R/'photon_26906_outputs'/name).is_file():fail('26906 shader CMake regression receipt missing '+name)
 subprocess.run(['python3','-S','test_26920_source.py','--live'],cwd=R,check=True)
 subprocess.run(['python3','-S','test_26920_vulkan_abi.py','--live','--compiled'],cwd=R,check=True)
 subprocess.run(['python3','-S','test_26920_math_host.py'],cwd=R,check=True)
 OUT.mkdir(exist_ok=True)
 (OUT/'26920_PREBUILD_SEALED_APP.sha256').write_text(''.join(f'{unchanged[p]}  {p}\n' for p in sorted(unchanged)))
 print('PASS preserved pinned real shader and source protections; host C++ RAW math and runtime JNI source validated')
def finalize():
 expected=exact(R,OUT/'26920_PREBUILD_SEALED_APP.sha256','full assemble postbuild 26920 source immutable')
 border(R)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('26920 exactly one APK required '+repr(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('Android APK invalid/small')
 gradle=OUT/'26920_gradle_assemble.log'
 if not gradle.is_file():fail('real Android Gradle log missing')
 log=gradle.read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL']
 if any(t not in log for t in tasks):fail('real build missing mandatory task '+str([t for t in tasks if t not in log]))
 (OUT/'26920_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26920_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (26920 active LK Vulkan shaders plus 26917 B physical CFA and inherited 26904/06/07/08)\nREAL SPIR-V VALIDATION: PASS (26920 active LK GLSL production/trace val-opt-val, pinned 26917 and inherited 26904/06/07/08)\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a, armeabi-v7a, 26920 active VK shader/C++/JNI)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS\n26917 ORIGINAL PHYSICAL BORDER: PASS\n26920 LK ACTIVE per-lens Vulkan alignment and contributor refinement: PASS (IQ pending physical tests)\nAPK '+APKNAME+' SHA256 '+sha(R/APKNAME)+'\n')
 # The pinned GLSL compile above does not replace CMake's actual Vulkan
 # shaders generated for BOTH Android ABIs. Require the real embedded output.
 for variant in ('prod','trace'):
  for shader in ('lk_refine','robust_photometric'):
   for abi in ('arm64-v8a','armeabi-v7a'):
    output=list((R/'app/.cxx').glob(f'**/{abi}/**/generated/multiframe/{variant}/{shader}.spv'))
    if len(output)!=1 or any(f.stat().st_size<256 for f in output):
     fail(f'missing/ambiguous compiled 26920 native CMake {abi} {variant} {shader}')
 # Independent SPIR-V binary descriptor ABI proof for BOTH actual CMake Android ABIs.
 subprocess.run(['python3','-S','test_26920_vulkan_abi.py','--live','--cmake'],cwd=R,check=True)
 (OUT/'26920_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 (OUT/'26920_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26920_incremental.py')+'  build_26920_incremental.py\n')
 cache=R/'photon_26906_outputs/26906_NATIVE_CACHE_PATCH_REPLAY.json'
 if not cache.is_file():fail('native cache replay receipt missing')
 receipt=json.loads(cache.read_text())
 if receipt.get('script_sha256')!=sha(R/'verify_26906_native_cache.py') or receipt.get('mode') not in ('cold','cached-replay'):fail('native CMake replay receipt SHA invalid')
 if receipt['mode']=='cached-replay' and len(receipt.get('sources',[]))!=2:fail('invalid restored libheif replay')
 shutil.copy2(cache,OUT/'26920_NATIVE_CACHE_PATCH_REPLAY.json')
 (OUT/'26920_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','local')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','local')+'\ngithub_job='+os.getenv('GITHUB_JOB','local')+'\n')
 workflow=R/'.github/workflows/build-26920-change-aware.yml'
 shutil.copy2(R/'build_26920_incremental.py',OUT/'ACTUAL_EXECUTED_build_26920_incremental.py')
 shutil.copy2(workflow,OUT/'ACTUAL_EXECUTED_build-26920-change-aware.yml')
 (OUT/'26920_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(workflow)+'  .github/workflows/build-26920-change-aware.yml\n')
 before=parse(R/'26920_BASE_26917_FULL_APP.sha256');changed=set((R/'26920_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 (OUT/'26920_PROTECTED_SOURCE.sha256').write_text(''.join(f'{before[p]}  {p}\n' for p in sorted(before) if p not in changed))
 for n in ['26920_BASE_26917_FULL_APP.sha256','26920_CHANGED_RUNTIME_ALLOWLIST.txt','26920_FROZEN_26917_BORDER.sha256']:
  shutil.copy2(R/n,OUT/n)
 (OUT/'26920_VERSION.txt').write_text('VERSION_NAME=0.9726920\nVERSION_BUILD=26920\n')
 target=OUT/'26920_candidate_app_source.tar.gz'
 with tarfile.open(target,'w:gz',compresslevel=1) as t:
  for p in sorted(expected):
   f=R/p;info=t.gettarinfo(str(f),arcname=p)
   info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   with f.open('rb') as source:t.addfile(info,source)
 (OUT/'26920_candidate_app_source.tar.gz.sha256').write_text(sha(target)+'  26920_candidate_app_source.tar.gz\n')
 print('PASS genuine 26920 APK + published candidate receipts with protected 2021 and frozen 26917 baseline',sha(R/APKNAME))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['seal','fetch','prepare','verify-compiled','finalize']);args=parser.parse_args()
 try:globals()[args.command.replace('-','_')]()
 except Exception as err:print('ERROR',err,file=sys.stderr);sys.exit(1)
