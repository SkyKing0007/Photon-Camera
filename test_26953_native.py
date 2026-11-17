#!/usr/bin/env python3
"""Actual published 26952 native exact-byte, NDK both ABI compiled JNI and real 26953 APK proof."""
import hashlib,sys,subprocess,zipfile
from build_26953_incremental import R,OUT,fail,sha,APKNAME
from prepare_26953_native import TARGET,ABIS,LIBS,EXPECTED,inspect

def native():
 receipt=OUT/'26953_EXACT_SUCCESSFUL_26952_LKR_NATIVE_RECEIPT.txt'
 if not receipt.is_file():fail('no exact successful 26952 JNI receipt')
 for abi in ABIS:
  for name in LIBS:
   path=TARGET/abi/name
   if not path.is_file() or sha(path)!=EXPECTED[(abi,name)]:fail('native binary mutated '+str(path))
   inspect(abi,name,path)
   if f'PASS lib/{abi}/{name} sha256={sha(path)}' not in receipt.read_text():fail('latest published native receipt missing')
 bridge=(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java').read_text()
 for s in ('T=3, DATA_STEPS=2, OUTPUT_SCALE=2','tuning[0]=T;', 'tuning[1]=DATA_STEPS;', 'Math.multiplyExact(w,2)','Math.multiplyExact(h,2)','release=2.3.94 '):
  if s not in bridge:fail('26952 3x2, 50MP, official native integration modified')
 if '8x4' in bridge:fail('wrong RawLens 8x4 integration')
 print('PASS original exact 26952 2.3.94 LKR JNI and 3x2 untouched across arm64/v7a')
def cmake():
 native()
 extra=('Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePrepare','Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePublishRgba16f','Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePublishClipR16f')
 for abi in ABIS:
  libs=list((R/'app/.cxx').glob('**/'+abi+'/libiris26856amaze.so'))+list((R/'app/build').glob('**/'+abi+'/libiris26856amaze.so'))
  if not libs:fail('real Android NDK CMake JNI not compiled '+abi)
  if not any(all(s in subprocess.run(['readelf','-Ws',str(p)],capture_output=True,text=True).stdout for s in extra) for p in libs):fail('real NDK compiled JNI missing '+abi)
 print('PASS original both real NDK compiled JNI ABIs')
def apk():
 cmake()
 paths=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(paths)!=1:fail('real assembled current APK missing/duplicate')
 p=R/APKNAME if (R/APKNAME).is_file() else paths[0]
 with zipfile.ZipFile(p) as z:
  if z.testzip():fail('real 26953 packaged APK CRC invalid')
  for abi in ABIS:
   for name in (*LIBS,'libiris26856amaze.so'):
    key='lib/'+abi+'/'+name
    if key not in z.namelist():fail('real APK JNI missing '+key)
    if name in LIBS and hashlib.sha256(z.read(key)).hexdigest()!=EXPECTED[(abi,name)]:fail('APK does not contain byte-identical published 26952 native '+key)
  if 'assets/licenses/rawlens_2_3_94_lkr_gpl_notice.txt' not in z.namelist():fail('published APK GPL notice missing')
 print('PASS real 26953 APK actual identical latest successful 26952 dual ABI native and GPL notice')
if __name__=='__main__':
 try:
  if sys.argv[1:]==['--native']:native()
  elif sys.argv[1:]==['--cmake']:cmake()
  elif sys.argv[1:]==['--apk']:apk()
  else:fail('usage --native|--cmake|--apk')
 except Exception as e:print('26953 NATIVE TEST BLOCKED: '+str(e),file=sys.stderr);sys.exit(1)
