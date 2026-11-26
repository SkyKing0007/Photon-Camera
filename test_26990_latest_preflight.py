#!/usr/bin/env python3
"""Latest successful authority only; historical C sparse fixtures replayed without reconstructing older runtime trees."""
import importlib.util,json,pathlib,shutil,subprocess,sys,tempfile
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26990_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
J='app/src/main/java/com/particlesdevs/photoncamera/';K='app/src/main/java/com/hinnka/mycamera/';C=K+'processor/experimentc/'
def run(*a):subprocess.run([sys.executable,'-S',*map(str,a)],cwd=R,check=True)
def cp(src,dst,want):
 assert b.sha(src)==want,(str(src),want);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert b.sha(dst)==want
if __name__=='__main__':
 before=b.exact(b.BASE,'26990_BASE_26989_FULL_APP.sha256','actual latest base');b.exact(R,'26990_BASE_26989_FULL_APP.sha256','actual latest live base');b.exact(b.CAND,'26990_EXPECTED_FULL_APP.sha256','frozen successor')
 run('test_26989_source.py','--live');run('test_26989_raw_memory_host.py','--live');run('test_26989_highlight_host.py','--live');run('test_26988_exposure_host.py');run('test_26986_crop_host.py');run('test_26987_color_host.py');run('verify_26989_v6_current_glsl.py','--audit');run('verify_26989_native_glsl.py','--audit')
 # Preserve original legacy and newer negative CPU regression on exact sparse native fixtures.
 native=pathlib.Path('app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp')
 prev=b.parse(R/'26988_BASE_26987_FULL_APP.sha256');legacy=b.parse(R/'26988_EXPECTED_FULL_APP.sha256')
 with tempfile.TemporaryDirectory(prefix='26990_legacy_fixture_') as td:
  t=pathlib.Path(td);oldroot=t/'.photon_26988_work/authority_26987'
  for src in sorted((b.CAND/native).rglob('*')):
   if not src.is_file():continue
   rel=src.relative_to(b.CAND);cp(src,t/rel,legacy[rel.as_posix()])
   if rel.as_posix() in prev:cp(b.BASE/rel,oldroot/rel,prev[rel.as_posix()])
  for n in ('test_26988_legacy_highlight_host.py','26988_BASE_26987_FULL_APP.sha256'):
   shutil.copyfile(R/n,t/n)
  subprocess.run([sys.executable,'-S',str(t/'test_26988_legacy_highlight_host.py'),'--live'],cwd=t,check=True)
 with tempfile.TemporaryDirectory(prefix='26990_sparse_history_') as td:
  t=pathlib.Path(td);v=t/'v10';files=sorted((b.BASE/C).rglob('*.kt'))
  for p in files:
   rel=p.relative_to(b.BASE).as_posix();cp(p,v/rel,before[rel])
  run('test_26983_v2_historical_replay.py','--base',v,'--historical',R/'handoff_payload_26975','--tests',R,'--candidate',b.CAND)
  f=t/'original_refs';g=t/'old_test_inputs';rec=json.loads((R/'26983_copy_records.json').read_text());post=json.loads((R/'26983_post_copy_records.json').read_text())['copies'];old=b.parse(R/'26985_BASE_26984_FULL_APP.sha256');prior83=b.parse(R/'26983_EXPECTED_FULL_APP.sha256');prior35=b.parse(R/'26935_EXPECTED_FULL_APP.sha256')
  refs={x['base'] for x in rec['copies']+rec['asset_copies']};refs.update('app/src/main/'+x['source'] for x in post)
  refs.update((J+'capture/Iris26909ShutterIsoMath.java',J+'capture/Iris26910CaptureSafety.java',J+'processing/opengl/postpipeline/MotionV2Render.java',J+'processing/opengl/postpipeline/PostPipeline.java',J+'processing/processor/PhotonMotionMgc1271Bridge.kt',J+'processing/ImageFrame.java',J+'processing/MotionBatch.java',J+'processing/render/Parameters.java',K+'processor/RawStackFrameCompat.kt',K+'model/SafeImage.kt','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag'))
  for rel in sorted(refs):
   if rel in (J+'capture/Iris26935BOnSession.java',J+'capture/Iris26935BOnProcessingRelay.java'):
    cp(R/'handoff_payload_26935'/rel,f/rel,prior35[rel])
   else:cp(b.BASE/rel,f/rel,before[rel])
  for rel in (R/'26983_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines():
   if rel.startswith('app/src/') and not rel.startswith('app/src/main/jniLibs/'):
    cp(R/'handoff_payload_26983'/rel,g/rel,prior83[rel])
  extra=[K+'processor/'+n+'.kt' for n in ('GlesGraphicsShader','RawStackFrameCompat')]+[J+'processing/ProcessingEventsListener.java',J+'processing/opengl/postpipeline/MotionV2Acr3Curve.java','app/src/main/cpp/iris26864/Iris26983COnGuidePack.h']
  for rel in extra:
   if not (g/rel).exists():cp(b.BASE/rel,g/rel,before[rel])
  assert not (g/'app/build.gradle').exists() and not (f/'app/build.gradle').exists()
  run('test_26983_integrated_host.py','--base',f,'--candidate',g)
 b.exact(b.BASE,'26990_BASE_26989_FULL_APP.sha256','authority unchanged');b.exact(R,'26990_BASE_26989_FULL_APP.sha256','live base unchanged');b.exact(b.CAND,'26990_EXPECTED_FULL_APP.sha256','frozen candidate unchanged')
 print('PASS latest authority and original sparse predecessor regression closure')
