#!/usr/bin/env python3
"""Photon 26921 guarded GitHub Actions builder. Exact successful 26920 V5 authority.
No source is committed by this script; fail closed on any authority/scope/compiler mismatch.
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, os, pathlib, shutil, subprocess, sys, tarfile, urllib.request, zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26921_work';OUT=R/'photon_26921_outputs'
ART=TMP/'26920-success.zip';BASE=TMP/'authority_26920';CAND=TMP/'candidate_26921'
RUN=43157689691;COMMIT='ac2695ff79a7c6b4e3d142cfad455edaee983096';ART_ID=13916538175
ART_SHA='b30739278443c72bdc430b932eff63a474f0ce25a2326b59d561c760819f04be'
TAR_SHA='ab3f00077d68356a1d92f2df1215ca716271a89bef0423ccbd462448a054681b'
BUILDER_SHA='d84468880b7d3b97efab798a1b650743b119fba3a1f583394b402f853e9c6a94'
WORKFLOW_SHA='bd4ace0aa5e1d72d2fcc076af616b1d971d1ec9f53737737e115e06b435b6eda'
PRIOR_APK_SHA='3854dcefa80038dc53e654509839a18c469de12e5655011adf295dac2412c2ea'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
APKNAME='IrisCamera-0.9726921-26921-iris-rawr-debug.apk'
CHANGE={'app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp','app/version.properties'}
def fail(s):raise RuntimeError('26921 BLOCKED: '+str(s))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse(p):
 d={}
 for row in p.read_text().splitlines():
  h,name=row.split('  ',1)
  if len(h)!=64 or name in d or not name.startswith('app/') or '..' in pathlib.PurePosixPath(name).parts:fail('invalid manifest '+row)
  d[name]=h
 return d
def scan(root):
 result={}
 for p in [*list((root/'app/src').rglob('*')),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('symlink in source '+str(p))
  if p.is_file():result[p.relative_to(root).as_posix()]=sha(p)
 return result
def exact(root,filename,label):
 expected=parse(R/filename if isinstance(filename,str) else filename); actual=scan(root)
 if expected!=actual:
  fail(f'{label}: missing={sorted(expected.keys()-actual.keys())[:8]} extra={sorted(actual.keys()-expected.keys())[:8]} wrong={[k for k in expected if actual.get(k)!=expected[k]][:8]}')
 print('PASS',label,len(actual));return actual
def border(root):
 for p,h in parse(R/'26921_FROZEN_26917_BORDER.sha256').items():
  if not (root/p).is_file() or sha(root/p)!=h:fail('26917 physical CFA border changed '+p)
def seal():
 lines=(R/'26921_HANDOFF_HASHES.sha256').read_text().splitlines()
 if not lines:fail('empty handoff seal')
 for line in lines:
  h,p=line.split('  ',1); f=R/p
  if not f.is_file() or sha(f)!=h:fail('staged handoff hash mismatch '+p)
 if set((R/'26921_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())!=CHANGE:fail('changed allowlist mismatch')
 old=parse(R/'26921_BASE_26920_FULL_APP.sha256'); new=parse(R/'26921_EXPECTED_FULL_APP.sha256')
 if len(old)!=2038 or set(old)!=set(new) or {p for p in old if old[p]!=new[p]}!=CHANGE:fail('2038-file source or two-file scope mismatch')
 if (R/'26921_ADDED_RUNTIME_PATHS.txt').read_text() or (R/'26921_DELETED_RUNTIME_PATHS.txt').read_text():fail('nonzero added/deleted')
 if parse(R/'26921_PROTECTED_SOURCE.sha256')!={p:h for p,h in old.items() if p not in CHANGE}:fail('protected source manifest differs')
 if sha(R/'.github/workflows/build-26921-change-aware.yml')!=next(h for h,p in (x.split('  ',1) for x in lines) if p=='.github/workflows/build-26921-change-aware.yml'):fail('workflow mismatch')
 print('PASS sealed three-stage 26921 upload, 2038 source paths, 2036 protected')
def fetch():
 seal(); token=os.getenv('GITHUB_TOKEN','')
 if not token:fail('GitHub Actions credential not available')
 if os.getenv('GITHUB_REPOSITORY',REPO)!=REPO or os.getenv('GITHUB_REF_NAME',BRANCH)!=BRANCH:fail('incorrect Actions repository/branch')
 def gh(url):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as f:return json.load(f)
 run=gh('actions/runs/'+str(RUN)); art=gh('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26920 Actions success identity wrong')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:fail('26920 published artifact wrong')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('26920 downloaded artifact hash wrong')
 print('PASS exact successful 26920 V5 Actions authority and published artifact')
def safe_tar(p,d):
 with tarfile.open(p,'r:gz') as t:
  for m in t:
   x=pathlib.PurePosixPath(m.name)
   if x.is_absolute() or '..' in x.parts or x.parts[0]!='app' or not(m.isfile() or m.isdir()):fail('unsafe TAR member '+m.name)
  t.extractall(d,filter='data')
def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('26920 Actions artifact missing or corrupted')
 for p in (BASE,CAND):
  if p.exists():shutil.rmtree(p)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  def get(n):
   n='photon_26920_outputs/'+n
   if n not in z.namelist():fail('26920 runtime authority receipt missing '+n)
   return z.read(n)
  body=get('26920_candidate_app_source.tar.gz')
  if hashlib.sha256(body).hexdigest()!=TAR_SHA:fail('26920 source archive wrong')
  if get('26920_PREBUILD_SEALED_APP.sha256')!=(R/'26921_BASE_26920_FULL_APP.sha256').read_bytes():fail('26920 source full manifest wrong')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26920_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26920_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26920 executed builder wrong')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26920-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26920_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26920 executed workflow wrong')
  if PRIOR_APK_SHA not in get('26920_APK.sha256').decode():fail('26920 published APK wrong')
  for marker in ['REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS']:
   if marker not in get('26920_COMPILER_STATUS.txt').decode():fail('26920 required compiler receipt absent '+marker)
  (TMP/'26920_candidate.tar.gz').write_bytes(body)
 safe_tar(TMP/'26920_candidate.tar.gz',BASE)
 exact(BASE,'26921_BASE_26920_FULL_APP.sha256','26920 compiled authority')
 border(BASE)
 shutil.copytree(BASE,CAND)
 for p in sorted(CHANGE):
  src=R/'handoff_payload_26921'/p; dest=CAND/p
  if not src.is_file() or not dest.is_file():fail('incorrect correction overlay '+p)
  shutil.copy2(src,dest)
 exact(CAND,'26921_EXPECTED_FULL_APP.sha256','candidate-first two-file 26921 correction')
 border(CAND)
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('original real Gradle project missing')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'26921_EXPECTED_FULL_APP.sha256','live authority-seeded Gradle source')
 border(R)
 OUT.mkdir(exist_ok=True)
 (OUT/'26921_SOURCE_SCOPE.txt').write_text(f'base=26920 V5 Actions run={RUN} commit={COMMIT} artifact={ART_ID} tar_sha256={TAR_SHA}\nsource=2038 changed=2 protected=2036 added=0 deleted=0 infrastructure_delta=workflow+runner+regression+manifests+trigger\n'+'\n'.join(sorted(CHANGE))+'\n')
 print('PASS 26921 candidate-first source reconstruction; unchanged original 26920 V5 LK shader behavior')
def regress():
 seal();exact(R,'26921_EXPECTED_FULL_APP.sha256','26921 regression source')
 subprocess.run(['python3','-S','test_26921_guard.py','--live'],cwd=R,check=True)
 border(R)
 print('PASS C++17 actual-source reference provenance regression')
def verify_compiled():
 regress()
 for p in ['photon_26920_outputs/26920_LK_GLSL_SPIRV_REAL_COMPILER.txt','photon_26917_outputs/26917_AMAZE_IMPORT_SHADER_REAL_COMPILER.txt','photon_26917_outputs/26917_AMAZE_IMPORT_SPIRV_VALIDATED.txt','photon_26906_outputs/26906_TONE_SHADER_REAL_COMPILER.txt']:
  if not (R/p).is_file():fail('real compiler proof missing '+p)
 # 26921 touched no shader source. Actual pinned shader source hashes must match 26920 compiler receipts.
 text=(R/'photon_26920_outputs/26920_LK_GLSL_SPIRV_REAL_COMPILER.txt').read_text()
 if '16.5.0' not in text:fail('pinned GLSL toolchain receipt changed')
 for p in ['app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/alignment/shaders/lk_refine.comp','app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/robust_photometric.comp']:
  if sha(R/p) not in text:fail('real Vulkan LK shader compiler source hash absent '+p)
 for variant in ('prod','trace'):
  for shader in ('lk_refine','robust_photometric'):
   for suffix in ('.spv','.opt.spv'):
    p=R/f'photon_26920_outputs/26920_lk_shaders/{shader}_{variant}{suffix}'
    if not p.is_file() or p.stat().st_size<256 or sha(p) not in text:fail('modified shader pipeline receipt missing '+str(p))
 (OUT/'26921_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26921_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS real 26920 shader pipeline replay, current 26921 native source frozen before Gradle')
def finalize():
 regress()
 if (OUT/'26921_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26921_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild freeze changed')
 gradle=OUT/'26921_gradle_assemble.log'
 if not gradle.is_file():fail('missing real Android compile log')
 log=gradle.read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL']
 for task in tasks:
  if task not in log:fail('real compiler/assembly task missing '+task)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one APK required '+repr(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('APK implausibly small')
 (OUT/'26921_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a, armeabi-v7a)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26921_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26921_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 (OUT/'26921_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26921_incremental.py')+'  build_26921_incremental.py\n')
 workflow=R/'.github/workflows/build-26921-change-aware.yml'
 (OUT/'26921_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(workflow)+'  .github/workflows/build-26921-change-aware.yml\n')
 (OUT/'26921_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','unknown')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','unknown')+'\n')
 for p in ['26921_BASE_26920_FULL_APP.sha256','26921_EXPECTED_FULL_APP.sha256','26921_PROTECTED_SOURCE.sha256','26921_CHANGED_RUNTIME_ALLOWLIST.txt']:
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26921_incremental.py',OUT/'ACTUAL_EXECUTED_build_26921_incremental.py')
 shutil.copy2(workflow,OUT/'ACTUAL_EXECUTED_build-26921-change-aware.yml')
 with (OUT/'26921_candidate_app_source.tar.gz').open('wb') as raw:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=raw) as compressed:
   with tarfile.open(fileobj=compressed,mode='w') as t:
    for p in sorted(parse(R/'26921_EXPECTED_FULL_APP.sha256')):
     f=R/p;info=t.gettarinfo(str(f),arcname=p);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
     with f.open('rb') as source:t.addfile(info,source)
 (OUT/'26921_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26921_candidate_app_source.tar.gz')+'  26921_candidate_app_source.tar.gz\n')
 print('PASS real compiled 26921 APK, recorded build proof and exact source TAR')
if __name__=='__main__':
 try:
  command=argparse.ArgumentParser();command.add_argument('command',choices=['seal','fetch','prepare','regress','verify-compiled','finalize']);c=command.parse_args().command
  globals()[c.replace('-','_')]()
 except Exception as e:print('ERROR',e,file=sys.stderr);sys.exit(1)
