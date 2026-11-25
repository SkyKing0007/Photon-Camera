#!/usr/bin/env python3
"""Run the previous successful live checks on 26983, with bounded historical test fixtures.
Only the actual published 26983 compiled source is an application source authority.
Older sealed payload files are used ONLY by their original historical tests, never installed.
"""
import importlib.util,json,pathlib,shutil,subprocess,sys,tempfile
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26984',R/'build_26984_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
J='app/src/main/java/com/particlesdevs/photoncamera/'
K='app/src/main/java/com/hinnka/mycamera/'
C=K+'processor/experimentc/'
B_FIXTURES={
 J+'capture/Iris26935BOnSession.java':'efa2306ba550ea90e256bdb5427d1fae3a1a533121e74f994a64f123896891fb',
 J+'capture/Iris26935BOnProcessingRelay.java':'a611759bacfecd02c40a0bde928c115d562436c477874bfd78cb5d35152cfdeb',
}
def run(*args):subprocess.run([sys.executable,'-S',*map(str,args)],cwd=R,check=True)
def copy_verified(source,dest,want):
 assert source.is_file() and b.sha(source)==want,('test fixture SHA mismatch',str(source))
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 assert b.sha(dest)==want

def main():
 before=b.exact(b.BASE,'26984_BASE_26983_FULL_APP.sha256','latest authority before test-only fixtures')
 b.exact(R,'26984_BASE_26983_FULL_APP.sha256','latest live predecessor before tests')
 b.exact(b.CAND,'26984_EXPECTED_FULL_APP.sha256','frozen successor before tests')
 # Actual original 26983 live source/controls, donor math and shader checks.
 run('test_26983_source.py','--live')
 run('test_26983_settings_host.py','--root',b.BASE/'app')
 run('test_26982_integration_host.py','--root',b.BASE/'app')
 run('verify_26983_v6_current_glsl.py','--audit')
 with tempfile.TemporaryDirectory(prefix='26984_sparse_test_fixtures_') as tmp:
  t=pathlib.Path(tmp)
  # Original V10 helper copies its supplied app subtree. Provide ONLY its C Kotlin
  # reference closure, not a historical app, native libraries, assets or build files.
  v=t/'v10_current_slice';files=sorted((b.BASE/C).rglob('*.kt'))
  for p in files:
   rel=p.relative_to(b.BASE).as_posix();copy_verified(p,v/rel,before[rel])
  assert files and not (v/'app/build.gradle').exists()
  run('test_26983_v2_historical_replay.py','--base',v,'--historical',R/'handoff_payload_26975','--tests',R,'--candidate',b.CAND)
  # Replay the exact successful 26983 integrated tests. Old copy-parity tests
  # need two original B classes since B session/relay were intentionally evolved
  # in 26983 itself. Those two original bytes are already sealed 26935 payloads.
  # Every other reference is taken directly from the latest successful artifact.
  f=t/'copy_reference_fixture'
  records=json.loads((R/'26983_copy_records.json').read_text())
  rows=records['copies']+records['asset_copies']
  refs={x['base'] for x in rows}
  refs.update('app/src/main/'+x['source'] for x in json.loads((R/'26983_post_copy_records.json').read_text())['copies'])
  refs.update((
   J+'capture/Iris26909ShutterIsoMath.java',J+'capture/Iris26910CaptureSafety.java',
   J+'processing/opengl/postpipeline/MotionV2Render.java',J+'processing/opengl/postpipeline/PostPipeline.java',
   J+'processing/processor/PhotonMotionMgc1271Bridge.kt',J+'processing/ImageFrame.java',J+'processing/MotionBatch.java',
   K+'processor/RawStackFrameCompat.kt',K+'model/SafeImage.kt',
   'app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',
  ))
  for rel in sorted(refs):
   if rel in B_FIXTURES:
    assert next(x['base_sha256'] for x in rows if x['base']==rel)==B_FIXTURES[rel]
    copy_verified(R/'handoff_payload_26935'/rel,f/rel,B_FIXTURES[rel])
   else:copy_verified(b.BASE/rel,f/rel,before[rel])
  assert len(refs)<100 and not (f/'app/build.gradle').exists(),len(refs)
  print('PASS only',len(refs),'integrated test reference files, including 2 sealed 26935 fixture files; no older source tree',flush=True)
  run('test_26983_integrated_host.py','--base',f,'--candidate',b.BASE)
 b.exact(b.BASE,'26984_BASE_26983_FULL_APP.sha256','latest artifact authority unchanged by historical tests')
 b.exact(R,'26984_BASE_26983_FULL_APP.sha256','latest live predecessor unchanged by historical tests')
 b.exact(b.CAND,'26984_EXPECTED_FULL_APP.sha256','frozen candidate unchanged by historical tests')
 print('PASS latest-only 26984 prepare-base historical fixture and predecessor regression closure',flush=True)
if __name__=='__main__':main()
