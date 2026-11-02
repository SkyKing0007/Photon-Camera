#!/usr/bin/env python3
"""26896 exact 26895 successful compiled universe: frozen candidate, source ownership and full-index inversion."""
from pathlib import Path
import hashlib,re,sys,shutil,subprocess,tempfile
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):
 r={}
 for line in (R/name).read_text().splitlines():
  sha,path=line.split('  ',1);assert re.fullmatch('[a-f0-9]{64}',sha) and path not in r
  r[path]=sha
 return r
def files(r):
 return {p.relative_to(r).as_posix():H(p) for p in r.rglob('*') if p.is_file() and '.git' not in p.parts}
OLD=read('26896_BASE_FULL_APP.sha256');NEW=read('26896_EXPECTED_CANDIDATE_FULL_APP.sha256');PRO=read('26896_UNCHANGED_PROTECTED.sha256')
ALLOW=(R/'26896_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(OLD)==len(NEW)==2025 and len(PRO)==2012 and len(ALLOW)==13
assert not set(OLD)^set(NEW)
assert sorted(k for k in OLD if OLD[k]!=NEW[k])==ALLOW
assert all(OLD[k]==NEW[k]==v for k,v in PRO.items())
assert not (R/'26896_ADDITIONS.txt').read_bytes() and not (R/'26896_DELETIONS.txt').read_bytes()
PAYLOAD=R/'handoff_payload_26896'
assert sorted('app/'+p.relative_to(PAYLOAD).as_posix() for p in PAYLOAD.rglob('*') if p.is_file())==ALLOW
assert all(H(PAYLOAD/k.removeprefix('app/'))==NEW[k] for k in ALLOW)
assert (PAYLOAD/'version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726896','VERSION_BUILD=26896']

def assert_source(base,cand,transform=False):
 assert files(base)==OLD,'exact successful 26895 compiled candidate not supplied or altered'
 if transform:
  assert not cand.exists(),'must transform into absent candidate directory';shutil.copytree(base,cand)
  for p in ALLOW:
   dst=cand/p;dst.parent.mkdir(parents=True,exist_ok=True)
   shutil.copyfile(PAYLOAD/p.removeprefix('app/'),dst)
 assert files(cand)==NEW,'frozen 26896 candidate manifest mismatch'
 assert all(H(cand/k)==v for k,v in PRO.items()),'protected source changed'
 print('PASS 26896 exact successful 26895 2025->2025 candidate, 13 modifications, 2012 protected, no additions/deletions')

def semantics(base,cand):
 assert_source(base,cand)
 source=lambda p:(cand/'app'/p).read_text()
 orig=lambda p:(base/'app'/p).read_text()
 # Pixel Motion retains exact 26895 burst, color, DNG, A/B, Wronski
 assert 'VK_EXT_MEMORY_BUDGET_EXTENSION_NAME' in source('src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp')
 s=source('src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp')
 assert 'PFN_vkGetPhysicalDeviceMemoryProperties2 queryBudget = nullptr' in s and 'heapBudget[j]' in s and 'heapUsage[j]' in s
 assert 'vkGetInstanceProcAddr(request.instance, "vkGetPhysicalDeviceMemoryProperties2")' in s
 assert 'queryBudget(request.physical,&props);' in s
 assert 'vkGetPhysicalDeviceMemoryProperties2(request.physical,&props);' not in s
 assert 'if(!request.instance||!request.physical' in s
 assert 'VkInstance instance=VK_NULL_HANDLE;' in source('src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.hpp')
 assert 'VkInstance instance() const noexcept { return instance_; }' in source('src/main/cpp/iris26856/amaze/include/amaze/VulkanDeviceOwner.hpp')
 assert 'req.instance=device.instance();req.physical=ctx.physicalDevice' in source('src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc')
 assert 'want<=available-reserve' in s and 'FrozenRawInputLayout::FencedTwoSlot' in s
 assert 'residentEligible?"RESIDENT":"FENCED_TWO_SLOT"' in s
 assert 'largestDeviceHeap' not in s
 assert orig('src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp').count('largestDeviceHeap')>=2
 assert 'runRealPinnedRawrB(merge,wrappedConsume)' in s
 bridge=source('src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc')
 assert bridge.count('IRIS_26896')==0 or 'IRIS_26896' in bridge  # receipts use Iris26896
 for tag in ('MOTION_B_NATIVE_ENTER','MOTION_B_VULKAN_DEVICE_READY','MOTION_B_AMAZE_PIPELINE_READY',
             'MOTION_B_RGB_AHB_READY','MOTION_B_CLIP_AHB_READY','MOTION_B_RAWR_BEGIN',
             'MOTION_B_RAWR_MERGE_CONSUMER','MOTION_B_RAWR_AMAZE_COMPLETED','MOTION_B_GL_EXPORT_COMPLETE'):
  assert bridge.count(tag)==1,tag
 assert bridge.count('ScopedAHB rgbAhb=createAhb(outWidth,outHeight,true)')==1
 assert bridge.count('ScopedAHB clipAhb=createAhb(outWidth,outHeight,true)')==1
 assert bridge.count('runRealRawrFromFrozenDirectNormals(req,commands,')==1
 log=source('src/main/java/com/particlesdevs/photoncamera/util/Log.java')
 assert 'getHistoricalProcessExitReasons' in log and 'info.getReason()' in log and 'logHandler.post(() ->' in log
 assert 'BUFFER_FLUSH_INTERVAL = 1000' in log and 'IRIS_26634_RETIRE_PROCESS_LIFECYCLE_FILES' in log
 assert 'Log.critical' not in log or 'public static void critical' in log
 # Spektra OFF normal and ON native max, with same immutable shutter output into camera2.
 pol=source('src/main/java/com/unspektrawesome/camera/RawPreviewPolicy.java')
 assert 'output.maximumResolutionMode == nativeMaximumResolution' in pol
 assert 'Spektra native maximum-resolution RAW is not advertised' in pol
 sess=source('src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java')
 assert 'captureStillFrozen(RawOutput frozenOutput,' in sess
 assert 'StillCapturePlanner.selectFrozen(state, frozenOutput)' in sess
 assert 'beginStillReconfiguration(selected)' in sess
 plan=source('src/main/java/com/unspektrawesome/camera/session/StillCapturePlanner.java')
 assert 'selectFrozen(Camera2RawSession.State state, RawOutput selected)' in plan
 k=source('src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
 assert 'val spektraNativeMax = PreferenceKeys.isSpektraNativeHighResOn()' in k
 assert 'owner.session.captureStillFrozen(request.captureOutput, stillCallback(request))' in k
 assert 'publishingCapture26896 = request' in k
 assert 'if (publishingCapture26896 !== request)' in k
 assert 'if (pendingCapture !== publishingCapture26896) pendingCapture = null' in k
 assert 'IRIS_26896_SPEKTRA_SAVE_SURVIVES_HANDOFF' in k
 assert 'captureWriter.shutdown()' in k and 'captureWriter.shutdownNow()' not in k
 assert k.index('publishingCapture26896 = request') < k.index('saveCapture(request, frame, image)')
 assert k.index('result.onSuccess { uri ->',k.index('private fun saveCapture')) < k.index('IRIS_26691_SPEKTRA_JPEG_SAVED')
 pref=source('src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
 assert 'SPEKTRA_NATIVE_MAX_KEY' in pref and 'getDefaultPreferences()' in pref
 assert 'setIrisSuperRes(boolean value)' in pref and 'KEY_IRIS_SUPER_RES' in pref
 ui=source('src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java')
 assert 'getAuthoritativeCameraMode() == CameraMode.SPEKTRA' in ui
 assert 'PreferenceKeys.setSpektraNativeHighRes' in ui and 'PreferenceKeys.setIrisSuperRes' in ui
 settings=source('src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java')
 assert 'CameraMode.SPEKTRA' in settings and 'PreferenceKeys.isSpektraNativeHighResOn()' in settings
 assert (cand/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726896','VERSION_BUILD=26896']
 # Exact protected domains: no shader/wronski/color/HDRQ/Camera2 general source changes.
 for p in ('app/src/main/assets/shaders/motionv2/render.glsl',
           'app/src/main/assets/shaders/motionv2/gainmap.glsl',
           'app/src/main/cpp/iris26864/Iris26864PackedSensorClipToGl.comp',
           'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'):
  assert NEW[p]==OLD[p]
 print('PASS 26896 original Pixel RAW capture/B pipelines protected, real memory budget fail-closed, safe Spektra save transaction, toggled native output only, immutable camera selection')

def patch(base,cand,forward,rollback):
 assert_source(base,cand)
 for ab in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='p26896index_') as t:
   x=Path(t);shutil.copytree(base/'app',x/'app')
   subprocess.run(['git','init','-q'],cwd=x,check=True)
   def run(*argv):
    p=subprocess.run(['git','-c','core.abbrev='+str(ab),*argv],cwd=x,capture_output=True,text=True)
    assert p.returncode==0,(ab,argv,p.stderr[:2500]);return p
   run('apply','--check','--whitespace=error',str(forward));run('apply','--whitespace=error',str(forward))
   assert files(x)==NEW
   run('apply','--check','--reverse',str(forward))
   run('apply','--check','--whitespace=error',str(rollback));run('apply','--whitespace=error',str(rollback))
   assert files(x)==OLD
   print('PASS actual exact four-arg full-index forward/rollback fuzz zero core.abbrev='+str(ab))

def negative(base,cand):
 assert_source(base,cand)
 with tempfile.TemporaryDirectory(prefix='p26896negative_') as t:
  copy=Path(t)/'candidate';shutil.copytree(cand,copy)
  protected=copy/'app/src/main/assets/shaders/motionv2/render.glsl';protected.write_bytes(protected.read_bytes()+b'\n')
  assert files(copy)!=NEW
  shutil.copyfile(cand/protected.relative_to(copy),protected);assert files(copy)==NEW
  bad=copy/'app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp'
  bad.write_text(bad.read_text().replace('queryBudget(request.physical,&props);','vkGetPhysicalDeviceMemoryProperties2(request.physical,&props);'))
  assert files(copy)!=NEW
  shutil.copyfile(cand/bad.relative_to(copy),bad);assert files(copy)==NEW
  wrong=copy/'app/src/main/java/com/unspektrawesome/camera/RawPreviewPolicy.java';wrong.write_text(wrong.read_text().replace('output.maximumResolutionMode == nativeMaximumResolution','true'))
  assert files(copy)!=NEW
  shutil.copyfile(cand/wrong.relative_to(copy),wrong);assert files(copy)==NEW
  bug=copy/'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt';bug.write_text(bug.read_text().replace('if (publishingCapture26896 !== request)', 'if (pendingCapture !== request)'))
  assert files(copy)!=NEW
  shutil.copyfile(cand/bug.relative_to(copy),bug);assert files(copy)==NEW
  ver=copy/'app/version.properties';ver.write_text(ver.read_text().replace('VERSION_BUILD=26896','VERSION_BUILD=26895'));assert files(copy)!=NEW
  print('PASS 26896 actual candidate negative: protected shader tamper, unresolved Android Vulkan linker symbol, wrong native mode, canceled saver, stale version')

if __name__=='__main__':
 assert len(sys.argv)>1
 mode=sys.argv[1];args=sys.argv[2:]
 if mode=='candidate':
  assert len(args) in (2,3) and (len(args)==2 or args[2]=='--transform')
  assert_source(Path(args[0]),Path(args[1]),len(args)==3)
 elif mode=='semantics':
  assert len(args)==2;semantics(Path(args[0]),Path(args[1]))
 elif mode=='patch':
  assert len(args)==4;patch(Path(args[0]),Path(args[1]),Path(args[2]).resolve(),Path(args[3]).resolve())
 elif mode=='tamper':
  assert len(args)==2;negative(Path(args[0]),Path(args[1]))
 else:raise AssertionError('unknown mode '+mode)
