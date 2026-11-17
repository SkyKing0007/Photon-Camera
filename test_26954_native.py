#!/usr/bin/env python3
"""Last successful compiled 26953 native ABI and current actual dual-ABI Android proof."""
import hashlib,sys,subprocess,zipfile
from build_26954_incremental import R,OUT,fail,sha,APKNAME
from prepare_26954_native import TARGET,ABIS,LIBS,EXPECTED,inspect
def native():
 receipt=OUT/'26954_EXACT_SUCCESSFUL_26953_LKR_NATIVE_RECEIPT.txt'
 if not receipt.is_file():fail('26953 native reuse receipt absent')
 for abi in ABIS:
  for name in LIBS:
   path=TARGET/abi/name
   if not path.is_file() or sha(path)!=EXPECTED[(abi,name)]:fail('native binary changed '+str(path))
   inspect(abi,name,path)
   if f'PASS lib/{abi}/{name} sha256={sha(path)}' not in receipt.read_text():fail('native receipt corrupted')
 bridge=(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java').read_text()
 for token in ('T=3, DATA_STEPS=2, OUTPUT_SCALE=2','tuning[0]=T;','tuning[1]=DATA_STEPS;','Math.multiplyExact(w,2)','Math.multiplyExact(h,2)','release=2.3.94 '):
  if token not in bridge:fail('B ON protected JNI 3x2 compatibility changed '+token)
 if '8x4' in bridge:fail('unexpected LK-R 8x4')
 print('PASS original 26953 exact four published JNI and RawLens 3x2 source')
def cmake():
 native();exports=('Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePrepare','Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePublishRgba16f','Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePublishClipR16f')
 for abi in ABIS:
  libs=list((R/'app/.cxx').glob('**/'+abi+'/libiris26856amaze.so'))+list((R/'app/build').glob('**/'+abi+'/libiris26856amaze.so'))
  if not libs:fail('26954 actual real NDK CMake missing '+abi)
  if not any(all(x in subprocess.run(['readelf','-Ws',str(p)],capture_output=True,text=True).stdout for x in exports) for p in libs):fail('26954 compiled JNI exports missing '+abi)
 print('PASS actual native NDK/CMake both ABIs JNI symbols')
def apk():
 cmake();paths=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(paths)!=1:fail('expected exactly one Android APK')
 path=R/APKNAME if (R/APKNAME).is_file() else paths[0]
 with zipfile.ZipFile(path) as z:
  if z.testzip():fail('26954 actual APK CRC')
  for abi in ABIS:
   for name in (*LIBS,'libiris26856amaze.so'):
    key=f'lib/{abi}/{name}'
    if key not in z.namelist():fail('26954 real APK missing JNI '+key)
    if name in LIBS and hashlib.sha256(z.read(key)).hexdigest()!=EXPECTED[(abi,name)]:fail('26954 APK changed original native '+key)
  if 'assets/licenses/rawlens_2_3_94_lkr_gpl_notice.txt' not in z.namelist():fail('original RawLens license absent')
 print('PASS 26954 one actual assembled APK and original two ABI native')
if __name__=='__main__':
 try:
  if sys.argv[1:]==['--native']:native()
  elif sys.argv[1:]==['--cmake']:cmake()
  elif sys.argv[1:]==['--apk']:apk()
  else:fail('usage --native|--cmake|--apk')
 except Exception as e:print('26954 NATIVE TEST BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
