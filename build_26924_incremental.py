#!/usr/bin/env python3
"""26924 exact authority-seeded three-stage Actions builder, no commit/push.
Inherits the successful 26923 V4 complete real shader/NDK/Kotlin/Java/assemble
and 26904 V1/V2/V3 + 26886/26887/26903 historical regressions.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, os, pathlib, shutil, subprocess, sys, tarfile, urllib.request, zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26924_work';OUT=R/'photon_26924_outputs'
ART=TMP/'26923-success.zip';BASE=TMP/'authority_26923';CAND=TMP/'candidate_26924'
RUN=43304249586; COMMIT='6513b326db863fd021da5796f9eefdf52a14b329'; ART_ID=13982773687
ART_SHA='01c7540122d067f52b18f8c7ce8b07228e20f2e87ec792d764b7a742b45571b2'
TAR_SHA='2bf46fadb145cb170091e692d52a0fc35e808e7cc8b4b73f18ddfe7d8cb4a71d'
BUILDER_SHA='cdfe07cf96dda90502ecf80a20a4747e3f3c27ea6973c0f6a2906973f09c20ff'
WORKFLOW_SHA='d86417c39d9879201191469233e693f270844f5f7f88c377eafebd9c79481d2c'
PRIOR_APK_SHA='1b2ff6d41c8a843c4f5894b452bbe8f3542b0bd63c1d73f26d6b295802cfaaf0'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
APKNAME='IrisCamera-0.9726924-26924-iris-rawr-debug.apk'
NBASE=2039; NFILES=2048; NCHANGE=9; NADD=9; NPROTECTED=2030

def fail(s):raise RuntimeError('26924 BLOCKED: '+str(s))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def parse(p):
 result={}
 for line in p.read_text().splitlines():
  h,name=line.split('  ',1)
  if len(h)!=64 or name in result or not name.startswith('app/') or '..' in pathlib.PurePosixPath(name).parts: fail('invalid source manifest entry '+line)
  result[name]=h
 return result
def listfiles(root):
 d={}
 for p in [*(root/'app/src').rglob('*'),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('source symlink '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 return d
def exact(root,manifest,label):
 e=parse(R/manifest);d=listfiles(root)
 if d!=e:fail(label+f' missing={list(e.keys()-d.keys())[:6]} extra={list(d.keys()-e.keys())[:6]} wrong={[x for x in e if d.get(x)!=e[x]][:6]}')
 print('PASS',label,len(d));return d
def scope():
 old=parse(R/'26924_BASE_26923_FULL_APP.sha256');new=parse(R/'26924_EXPECTED_FULL_APP.sha256')
 changes=set((R/'26924_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26924_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 removed=(R/'26924_DELETED_RUNTIME_PATHS.txt').read_text().strip()
 if len(old)!=NBASE or len(new)!=NFILES or len(changes)!=NCHANGE or len(added)!=NADD or removed:fail('runtime file count or deleted scope')
 if {x for x in old if new.get(x)!=old[x]}!=changes:fail('changed source differs from exact allowlist')
 if set(new)-set(old)!=added:fail('added runtime path differs')
 if set(old)-set(new):fail('protected runtime deletion')
 protected={x:h for x,h in old.items() if x not in changes}
 if parse(R/'26924_PROTECTED_SOURCE.sha256')!=protected or len(protected)!=NPROTECTED:fail('protected source drift')
 for p in changes|added:
  if p.startswith('app/src/main/cpp/iris26864/vendor/') or '/jniLibs/' in p or p.endswith('.so'):fail('native/vendor protected file in allowlist '+p)
 return changes,added,old,new
def seal():
 change,added,old,new=scope()
 lines=(R/'26924_HANDOFF_HASHES.sha256').read_text().splitlines()
 expected={}
 for line in lines:
  h,p=line.split('  ',1)
  if p in expected or not (R/p).is_file() or sha(R/p)!=h:fail('staged SHA mismatch or duplicate '+p)
  expected[p]=h
 need=set(change|added)
 if {p.removeprefix('handoff_payload_26924/') for p in expected if p.startswith('handoff_payload_26924/')}!=need:fail('overlay not exact runtime changed-file equality')
 for p in ['26924_FORWARD_FULLINDEX.patch','26924_ROLLBACK_FULLINDEX.patch','compile_26924_shaders.sh','compile_26924_hr_spirv.sh','compile_26924_lk_shaders.py','build_26924_incremental.py','test_26924_source.py','test_26924_math_host.py','test_26924_shader_shadow.py','test_26924_workflow_refs.py','test_26924_shader_contract.py','.github/workflows/build-26924-change-aware.yml','TRIGGER_26924.txt']:
  if p not in expected:fail('mandatory executable/trigger/mathematical or shader gate missing '+p)
 wf=(R/'.github/workflows/build-26924-change-aware.yml').read_text()
 for pin in ['TRIGGER_26924.txt','verify_26904_v3_safety.py','verify_26904_v2_safety.py','compile_26904_shaders_v2.sh','verify_26906_native_cache.py preflight','test_26923_source.py --payload','test_26924_shader_shadow.py --live --cmake','build_26924_incremental.py verify-compiled','build_26924_incremental.py finalize',':app:assembleDebug']:
  if pin not in wf:fail('successful verification gate lost '+pin)
 if 'test_26922_guard.py' in wf:fail('stale nonexistent tool reference')
 if wf.count('build_26923_incremental.py regress') != 1 or wf.index('build_26923_incremental.py regress') > wf.index('build_26924_incremental.py prepare'):fail('26923 historical regression must run only before 26924 source')
 if wf.count('actions/upload-artifact@v4')!=1:fail('publish once')
 file_roots=('handoff_payload_26924/',)
 actual_overlay={p.relative_to(R).as_posix() for p in (R/'handoff_payload_26924').rglob('*') if p.is_file()}
 listed_overlay={p for p in expected if p.startswith(file_roots)}
 if actual_overlay != listed_overlay:fail('extra or missing overlay files')
 if sha(R/'build_26924_incremental.py')!=expected['build_26924_incremental.py']:fail('runner mutated')
 print('PASS 26924 exact sealed source 2039->2048, 9 changed, 9 added, 2030 protected, no vendor mutation')
def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token:fail('Actions authentication unavailable')
 if os.getenv('GITHUB_REPOSITORY',REPO)!=REPO or os.getenv('GITHUB_REF_NAME',BRANCH)!=BRANCH:fail('wrong Actions repo/branch')
 def gh(path):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as x:return json.load(x)
 run=gh('actions/runs/'+str(RUN));art=gh('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26923 successful Actions runtime authority')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:fail('26923 published artifact digest')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('26923 Actions ZIP corrupt')
 print('PASS exact successful 26923 V4 run, published artifact and SHA-256')
def safe_tar(p,d):
 with tarfile.open(p,'r:gz') as t:
  for m in t:
   x=pathlib.PurePosixPath(m.name)
   if x.is_absolute() or '..' in x.parts or not x.parts or x.parts[0]!='app' or not(m.isfile() or m.isdir()):fail('unsafe authority tar '+m.name)
  t.extractall(d,filter='data')
def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('prior published Actions ZIP missing/corrupt')
 for d in (BASE,CAND):
  if d.exists():shutil.rmtree(d)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  def get(name):
   p='photon_26923_outputs/'+name
   if p not in z.namelist():fail('26923 required receipt missing '+p)
   return z.read(p)
  data=get('26923_candidate_app_source.tar.gz')
  if hashlib.sha256(data).hexdigest()!=TAR_SHA:fail('26923 compiled candidate TAR mismatch')
  if get('26923_PREBUILD_SEALED_APP.sha256')!=(R/'26924_BASE_26923_FULL_APP.sha256').read_bytes():fail('26923 executed compiled source manifest mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26923_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26923_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26923 actual executed builder missing')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26923-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26923_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26923 actual executed workflow changed')
  if PRIOR_APK_SHA not in get('26923_APK.sha256').decode():fail('26923 actual published APK SHA missing')
  for key in ['REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS']:
   if key not in get('26923_COMPILER_STATUS.txt').decode():fail('26923 baseline lacks '+key)
  (TMP/'26923_candidate.tar.gz').write_bytes(data)
 safe_tar(TMP/'26923_candidate.tar.gz',BASE)
 exact(BASE,'26924_BASE_26923_FULL_APP.sha256','actual successful 26923 compiled source')
 changes,added,_,_=scope()
 shutil.copytree(BASE,CAND)
 for p in sorted(changes|added):
  src=R/'handoff_payload_26924'/p;dst=CAND/p
  if not src.is_file() or (p in changes and not dst.is_file()) or (p in added and dst.exists()):fail('unsafe candidate overlay '+p)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 exact(CAND,'26924_EXPECTED_FULL_APP.sha256','frozen candidate-first 26924')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('GitHub checkout Gradle project missing')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'26924_EXPECTED_FULL_APP.sha256','real live Android candidate')
 OUT.mkdir(exist_ok=True)
 (OUT/'26924_SOURCE_SCOPE.txt').write_text(f'authority_run={RUN} commit={COMMIT} artifact={ART_ID} ZIP_SHA256={ART_SHA} TAR_SHA256={TAR_SHA}\nfiles={NFILES} changed={NCHANGE} added={NADD} protected={NPROTECTED} deleted=0\n'+'\n'.join(sorted(changes|added))+'\n')
 print('PASS 26924 source seeded solely from successful V4, no stale repo source substitution')
def regress():
 seal();exact(R,'26924_EXPECTED_FULL_APP.sha256','26924 live source')
 for cmd in [['python3','-S','test_26924_source.py','--live'],['python3','-S','test_26924_math_host.py','--live'],['python3','-S','test_26924_shader_shadow.py','--live']]:subprocess.run(cmd,cwd=R,check=True)
 print('PASS 26924 B-only owners, original RAW projection, preserved source/vendor and partial clip boundary constraints')
def verify_compiled():
 regress()
 for name in ('26924_CURRENT_GLSL_SPIRV_REAL_COMPILER.txt','26924_ORIGINAL_RAW_SPIRV_REAL_COMPILER.txt','26924_PINNED_LK_SPIRV_REAL_COMPILER.txt'):
  f=OUT/name
  if not f.is_file() or '16.5.0' not in f.read_text() or 'PASS' not in f.read_text():fail('real 26924 current pinned shader compiler receipt missing '+name)
 for name in ('26924_current_chroma_es300.frag','26924_current_fcc_median_es300.frag','26924_current_fcc_reconstruct_es300.frag'):
  if not (OUT/name).is_file():fail('full current expanded GLES shader not compiled '+name)
 for p in ['app/src/main/cpp/iris26864/bridge/Iris26924_raw_residual.comp','app/src/main/cpp/iris26864/bridge/Iris26924_raw_adjoint.comp','app/src/main/cpp/iris26864/bridge/Iris26924_raw_update.comp','app/src/main/cpp/iris26864/bridge/Iris26924_reference_model.comp','app/src/main/cpp/iris26864/bridge/Iris26924WronskiFinalize.comp']:
  if sha(R/p) not in (OUT/'26924_ORIGINAL_RAW_SPIRV_REAL_COMPILER.txt').read_text():fail('compiled source hash not proven '+p)
 (OUT/'26924_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26924_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS 26924 actual pinned shader/SPIR-V prebuild freeze and historical regressions')
def finalize():
 regress()
 if (OUT/'26924_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26924_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild source mutated')
 log=(OUT/'26924_gradle_assemble.log').read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL']
 for t in tasks:
  if t not in log:fail('real Android compiler/assembly gate missing '+t)
 subprocess.run(['python3','-S','test_26924_shader_shadow.py','--live','--cmake'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one APK required '+repr(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('APK suspiciously small')
 (OUT/'26924_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a, armeabi-v7a)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26924_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26924_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26924-change-aware.yml'
 (OUT/'26924_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26924_incremental.py')+'  build_26924_incremental.py\n')
 (OUT/'26924_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26924-change-aware.yml\n')
 (OUT/'26924_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','unknown')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','unknown')+'\n')
 for p in ['26924_BASE_26923_FULL_APP.sha256','26924_EXPECTED_FULL_APP.sha256','26924_PROTECTED_SOURCE.sha256','26924_CHANGED_RUNTIME_ALLOWLIST.txt','26924_ADDED_RUNTIME_PATHS.txt']:shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26924_incremental.py',OUT/'ACTUAL_EXECUTED_build_26924_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26924-change-aware.yml')
 with (OUT/'26924_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for p in sorted(parse(R/'26924_EXPECTED_FULL_APP.sha256')):
     src=R/p;info=t.gettarinfo(str(src),arcname=p);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
     with src.open('rb') as x:t.addfile(info,x)
 (OUT/'26924_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26924_candidate_app_source.tar.gz')+'  26924_candidate_app_source.tar.gz\n')
 print('PASS 26924 complete Android APK, source TAR, dual ABI compiled shadow shaders and published receipts ready')
if __name__=='__main__':
 try:
  arg=argparse.ArgumentParser();arg.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'));mode=arg.parse_args().command
  globals()[mode.replace('-','_')]()
 except Exception as e:print('ERROR '+str(e),file=sys.stderr);sys.exit(1)
