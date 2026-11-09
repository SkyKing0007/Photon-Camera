#!/usr/bin/env python3
"""26914 actual source / physical noise / highlight / UI / native regression.
No static check substitutes for real pinned shaders + two-ABI Android build in Actions.
"""
import hashlib,os,pathlib,re,subprocess,sys,tempfile,shutil
R=pathlib.Path(__file__).resolve().parent
BRIDGE26914='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def must(ok,msg):
 if not ok:raise AssertionError('26914 '+msg)
def manifest(path):
 d={}
 for row in path.read_text().splitlines():
  h,p=row.split('  ',1)
  must(re.fullmatch(r'[0-9a-f]{64}',h) and p.startswith('app/') and p not in d and '..' not in pathlib.PurePosixPath(p).parts,'invalid source manifest')
  d[p]=h
 return d

def actual(root):
 d={}
 for p in (root/'app/src').rglob('*'):
  must(not p.is_symlink(),'source symlink '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 for p in ('app/build.gradle','app/version.properties'):
  d[p]=sha(root/p)
 return d

def source_checks(root):
 j=root/'app/src/main/java';res=root/'app/src/main/res';cpp=root/'app/src/main/cpp'
 s=(j/'com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text()
 xml=(res/'xml/preferences.xml').read_text()
 must(xml.count('ns0:key="pref_iris_custom_noise_model"')==1 and xml.count('ns0:key="pref_iris_import_noise_model"')==1,'original noise toggle/import not unique')
 for bad in ['iris_26912_b_off_import_','iris_26912_b_off_noise_','Imported noise profile — B Super Res OFF','pref_iris_alternative_highlight_recovery','pref_show_roundedge_key']:
  must(bad not in s and bad not in xml,'retired duplicate/menu reference '+bad)
 must('irisNoiseModelImportLauncher' in s and 'importBOffForPhysical(mContext, uri, physicalLens)' in s,'existing picker not wired to lens importer')
 must('IrisNoiseProfileStore.setBOffEnabled(mContext, lens, enable)' in s,'existing custom switch not wired to lens')
 must('hasValidStoredBOffForPhysical(mContext, lens)' in s,'invalid lens profile must fail')
 must('cameraMode != CameraMode.NIGHT' in s,'Night original controls hidden')
 must('iris26914ImportLensId = PreferenceKeys.getCameraID();' in s,'lens identity not frozen at picker selection')
 must('Iris26912PerLensHighlightSwitch' not in s+''.join(xml),'retired highlight switch reference')
 must(not (j/'com/particlesdevs/photoncamera/ui/settings/custompreferences/Iris26912PerLensHighlightSwitch.java').exists(),'unused highlight class survived')
 defaults=(res/'values/default_prefs.xml').read_text()
 must('<bool name="pref_camera_sounds_default">false</bool>' in defaults,'camera sounds new-install default not OFF')
 must(xml.count('pref_camera_sounds_key')==1,'camera sound toggle removed')
 must('return false; // 26914 permanently disabled' in (j/'com/particlesdevs/photoncamera/settings/PreferenceKeys.java').read_text(),'saved legacy rounded edges still active')
 must('drawRoundEdges(canvas)' not in (j/'com/particlesdevs/photoncamera/ui/camera/views/viewfinder/SurfaceViewOverViewfinder.java').read_text(),'rounded-edge draw still active')
 h=(j/'com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java').read_text()
 must('return true;' in h[h.index('public static boolean alternativeHighlight'):h.index('public static void write')],'highlight not permanently ON')
 must('HIGHLIGHT_PREFIX' not in h,'stale per-lens saved OFF preference still read')
 c=(j/'com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
 must('final boolean iris26912AltHighlightAtPress =' in c and '!PreferenceKeys.isIrisSuperResOn()' not in c[c.index('final boolean iris26912AltHighlightAtPress'):c.index('final boolean iris26593SessionReady')],'Super Res ON capture highlight blocked')
 b=(j/'com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 must('private fun iris26914BNoiseForPhysical' in b and b.count('iris26914BNoiseForPhysical(')==3,'both B noise paths missing')
 must('GlesIris26912HighlightReference.select(' in b and b.count('GlesIris26912HighlightReference.select(')==2,'both B highlight paths missing')
 must('parameters.iris26903NightB' in b and 'normal' in b,'Night B path missing')
 must('if (bNight26914) 1.0f' in b and 'staticSafe26889' in b and 'stable26914' in b,'Night highlight lacks real RAW static trust gate')
 must('IrisNoiseProfileStore.loadBOffForPhysical(' in b,'physical profile loader not used')
 must('nativeReferenceIndex].sensitivityIso' in b and 'normals[refIndex].sensitivityIso' in b,'actual ISO provenance missing')
 java=(j/'com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java').read_text()
 must('(wronskiTrue2x ||' not in java and 'bOffNoiseByPhase.length != 8' in java,'JNI still bans SR .c')
 inc=(cpp/'iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
 must('if(bOffNoise.size()!=8u)' in inc and 'if(sr||bOffNoise.size()!=8u)' not in inc,'native JNI rejects SR custom model')
 native=(cpp/'iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
 for k in ('wronski.estimateNoiseFromBurst=!(sr && frozen.hasBOffCustomNoise)',
           'wronski.sensorNoiseProfile=model','result.estimatedNoise=*wronski.sensorNoiseProfile',
           'result.noiseEstimated=true','if (!sr && frozen.hasBOffCustomNoise)'):
  must(k in native,'native 2x model/wavelet ownership missing '+k)
 must('freezeNormalOnlyB(' in (j/'com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java').read_text(),'Night normal-only selector missing')
 night=(j/'com/particlesdevs/photoncamera/processing/processor/IrisNightBProcessor26903.java').read_text()
 for k in ('batch.superResEnabled','batch.frameBudget','batch.longFrameCount != 0','configureIris26903NightB','false, /* permanent 26704'):
  must(k in night,'Night capture contract changed '+k)
 assert 'VERSION_BUILD=26914' in (root/'app/version.properties').read_text()
 return j,cpp,b

def java_grammar(j):
 source=R/'tests_26914/SourceGrammar26914.java'
 paths=['com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java','com/particlesdevs/photoncamera/settings/PreferenceKeys.java','com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java','com/particlesdevs/photoncamera/capture/CaptureController.java','com/particlesdevs/photoncamera/ui/camera/views/viewfinder/SurfaceViewOverViewfinder.java','com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java']
 with tempfile.TemporaryDirectory(prefix='26914_javac_') as d:
  subprocess.run(['javac','--release','17','-d',d,str(source)],check=True,stdout=subprocess.DEVNULL)
  subprocess.run(['java','-cp',d,'SourceGrammar26914',*[str(j/p) for p in paths]],check=True)

def kotlin_map(b):
 # Compile the exact production helper body (not a reimplementation) with minimal
 # fake Android context/profile types. The real project compilation remains Actions.
 start=b.index('    private fun iris26914BNoiseForPhysical(')
 opening=b.index('{',start);depth=0;end=None
 for i in range(opening,len(b)):
  if b[i]=='{':depth+=1
  if b[i]=='}':
   depth-=1
   if depth==0:end=i+1;break
 must(end is not None,'Kotlin helper unterminated')
 helper=b[start:end].replace('private fun','fun',1)
 code='''class Model(val shotNoise: FloatArray,val readNoise: FloatArray)
class Profile(val model:Model) { fun evaluate(iso:Int):Model? = if(iso>0) model else null }
object PhotonCamera { fun getApplicationContextStatic():Any = Any() }
object IrisNoiseProfileStore {
 val selected=mutableMapOf<String,Profile>()
 fun loadBOffForPhysical(c:Any,physical:String):Profile?=selected[physical]
}
object UnderTest {\n'''+helper+'''\n}
fun main() {
 val model=Model(floatArrayOf(.01f,.02f,.03f,.04f),floatArrayOf(.001f,.002f,.003f,.004f))
 IrisNoiseProfileStore.selected["physical-5"]=Profile(model)
 val mapping=arrayOf(intArrayOf(0,1,2,3),intArrayOf(1,0,3,2),intArrayOf(2,3,0,1),intArrayOf(3,2,1,0))
 for(cfa in 0..3) {
  val got=UnderTest.iris26914BNoiseForPhysical("physical-5",200,cfa) ?: error("missing model")
  for(i in 0..3) {
   check(got[i*2]==model.shotNoise[mapping[cfa][i]])
   check(got[i*2+1]==model.readNoise[mapping[cfa][i]])
  }
 }
 check(UnderTest.iris26914BNoiseForPhysical("other-lens",200,0)==null)
 check(UnderTest.iris26914BNoiseForPhysical("physical-5",-1,0)==null)
 IrisNoiseProfileStore.selected["physical-5"]=Profile(Model(floatArrayOf(.01f,.02f,Float.NaN,.04f),floatArrayOf(.001f,.002f,.003f,.004f)))
 check(UnderTest.iris26914BNoiseForPhysical("physical-5",200,0)==null)
 println("PASS 26914 actual Kotlin physical-lens 4-CFA-site mapping, missing/invalid fallback")
}
'''
 with tempfile.TemporaryDirectory(prefix='26914_kotlin_') as d:
  f=pathlib.Path(d)/'Main.kt';f.write_text(code);jar=pathlib.Path(d)/'check.jar'
  subprocess.run(['kotlinc',str(f),'-include-runtime','-d',str(jar)],check=True,stdout=subprocess.DEVNULL)
  subprocess.run(['java','-jar',str(jar)],check=True)

def cpp_model(cpp):
 src=R/'tests_26914/NativeNoiseModel26914.cpp';include=cpp/'iris26864/vendor/rawr/native/multiframe/merge_wronski/include'
 with tempfile.TemporaryDirectory(prefix='26914_cpp_') as d:
  out=pathlib.Path(d)/'test'
  subprocess.run(['g++','-std=c++17','-Werror','-Wall','-Wextra','-I'+str(include),str(src),'-o',str(out)],check=True)
  subprocess.run([str(out)],check=True)

def patch_replay(base,candidate):
 # No repository commit/branch/push. Use git --no-index full-index byte patch,
 # deterministic at three core.abbrev settings, forward and reverse fuzz=0.
 with tempfile.TemporaryDirectory(prefix='26914_patches_') as d:
  root=pathlib.Path(d);(root/'a').mkdir();(root/'b').mkdir()
  shutil.copytree(base/'app',root/'a/app');shutil.copytree(candidate/'app',root/'b/app')
  hashes=[]
  for abbrev in (7,12,40):
   command=['git','-c','core.abbrev='+str(abbrev),'diff','--no-index','--binary','--full-index','--','a/app','b/app']
   p=subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   must(p.returncode==1,'git diff failure '+p.stderr.decode(errors='replace')[:300])
   diff=p.stdout.replace(b'a/a/app/',b'a/app/').replace(b'b/b/app/',b'b/app/')
   must(b'index ' in diff and b'@@' in diff,'full index patch absent')
   hashes.append(hashlib.sha256(diff).hexdigest())
   patch=root/'candidate.patch';patch.write_bytes(diff)
   replay=root/'replay'
   if replay.exists():shutil.rmtree(replay)
   replay.mkdir();shutil.copytree(base/'app',replay/'app')
   for args in (['--check'],[],['--reverse','--check'],['--reverse']):
    subprocess.run(['git','apply',*args,str(patch)],cwd=replay,check=True,stdout=subprocess.DEVNULL)
   # Forward+rollback unchanged baseline and independently forward replay candidate.
   must(actual(replay)==actual(base),'rollback lost base bytes')
   subprocess.run(['git','apply',str(patch)],cwd=replay,check=True,stdout=subprocess.DEVNULL)
   must(actual(replay)==actual(candidate),'forward full-index patch changed candidate')
  must(len(set(hashes))==1,'core.abbrev changes full-index patch bytes')
  print('PASS 26914 actual full-index deterministic patch at 7/12/40, forward/rollback, fuzz=0 SHA',hashes[0])

def run(mode):
 base=manifest(R/'26914_BASE_26913_FULL_APP.sha256');end=manifest(R/'26914_V2_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=(R/'26914_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines();deleted=(R/'26914_DELETED_RUNTIME_PATHS.txt').read_text().splitlines()
 must(len(base)==2036 and len(end)==2035 and len(changed)==14 and len(set(changed))==14,'wrong source universe/allowlist')
 must(len(deleted)==1 and deleted[0] in changed and set(base)-set(end)==set(deleted) and not set(end)-set(base),'bad removed-file proof')
 must({p for p in base if p in end and base[p]!=end[p]}==set(changed)-set(deleted),'unapproved changed source')
 must(len(base)-len(changed)==2022,'protected count incorrect')
 for p in base:
  if p.startswith(('app/src/main/assets/','app/src/main/jniLibs/','app/src/main/cpp/iris26864/vendor/')):
   must(p in end and end[p]==base[p],'native/vendor/shader alteration '+p)
 for p in changed:
  if p not in deleted:must(sha(R/('handoff_payload_26914_v2' if p == BRIDGE26914 else 'handoff_payload_26914')/p)==end[p],'wrong overlay '+p)
 if mode=='payload':
  # Independent candidate reconstruction from exact staged modified files plus
  # actually recovered 26913 source is performed in Actions builder prepare.
  root=R/'handoff_payload_26914'
  # Compare semantics using known local candidate reconstruction if available;
  # for a clean upload source checks run AFTER authority reconstruction.
  must('app/version.properties' in changed,'version not allowlisted')
  print('PASS 26914 V2 pre-stage 2036->2035, 14 exact paths, 2022 protected, one deletion, immutable shaders/vendor')
 else:
  root=R
  must(actual(root)==end,'live candidate is not exact compiled source')
  j,cpp,b=source_checks(root);java_grammar(j);kotlin_map(b);cpp_model(cpp)
  from test_26914_kotlin_owner import compile_actual
  compile_actual(R/'handoff_payload_26914'/BRIDGE26914,expect_failure=True)
  compile_actual(root/BRIDGE26914)
  base_dir=pathlib.Path(os.getenv('PHOTON_26914_BASE_DIR',str(R/'.photon_26914_work/authority_26913')))
  if base_dir.is_dir():
   must(actual(base_dir)==base,'prior successful 26913 source corrupted')
   patch_replay(base_dir,root)
  else:raise AssertionError('26914 exact predecessor source absent: patch replay cannot be skipped')
  print('PASS 26914 source ownership/live grammar and model, Night B ON/OFF, settings/highlight/sounds/round-edge')
if __name__=='__main__':run(sys.argv[1].lstrip('-') if len(sys.argv)==2 else 'payload')
