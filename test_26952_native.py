#!/usr/bin/env python3
"""Dual ABI release JNI, original 26931 native JNI adapter, and real APK exact bytes.
The historical test_26931_native_integrity.py --native is invoked before official upgrade.
"""
import hashlib,pathlib,subprocess,sys,zipfile
from build_26952_incremental import R,OUT,fail,sha,APKNAME
from prepare_26952_native import ABIS,LIBS,ARM_SHA,RELEASE_SHA,inspect,TARGET

def native():
 receipt=OUT/'26952_OFFICIAL_LKR_2_3_94_RECEIPT.txt'
 if not receipt.is_file() or 'official APK sha256='+RELEASE_SHA not in receipt.read_text():fail('actual official release source missing')
 for abi in ABIS:
  for name in LIBS:
   p=TARGET/abi/name
   if not p.is_file() or f'PASS lib/{abi}/{name} sha256={sha(p)} bytes=' not in receipt.read_text():fail('new native tampering or missing receipt '+str(p))
   if abi=='arm64-v8a' and sha(p)!=ARM_SHA[name]:fail('wrong supplied-arm64 matched release '+name)
   inspect(abi,name,p)
 s=(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java').read_text()
 if 'release=2.3.94 ' not in s or 'release=2.2.86' in s:fail('stale binary release labeling')
 for needle in ('T=3, DATA_STEPS=2, OUTPUT_SCALE=2','tuning[0]=T;', 'tuning[1]=DATA_STEPS;', 'LkrBridge.nativeMerge(input,w,h,stridePx,cfa,','Math.multiplyExact(w,2)','Math.multiplyExact(h,2)'):
  if needle not in s:fail('original 3x2/50MP Java reconstruction contract changed '+needle)
 if '8x4' in s or '8*4' in s:fail('old RawLens 8x4 must never replace 3x2')
 print('PASS 2.3.94 dual-ABI exact binaries from one SHA-pinned release, unchanged 3x2 JNI caller and 50MP')
def cmake():
 native()
 extra=('Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePrepare','Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePublishRgba16f','Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePublishClipR16f')
 for abi in ABIS:
  libs=list((R/'app/.cxx').glob('**/'+abi+'/libiris26856amaze.so'))+list((R/'app/build').glob('**/'+abi+'/libiris26856amaze.so'))
  if not libs:fail('no actually compiled NDK CMake JNI for '+abi)
  ok=False
  for lib in libs:
   text=subprocess.run(['readelf','-Ws',str(lib)],capture_output=True,text=True).stdout
   if all(symbol in text for symbol in extra):ok=True;break
  if not ok:fail('missing actual rebuilt 26931 JNI symbols for '+abi)
 print('PASS real Android NDK CMake native JNI two ABIs and official 2.3.94 dependencies')
def apk():
 cmake()
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('not one real assembled APK')
 p=R/APKNAME if (R/APKNAME).is_file() else apks[0]
 with zipfile.ZipFile(p) as z:
  if z.testzip():fail('real APK CRC failed')
  for abi in ABIS:
   for name in (*LIBS,'libiris26856amaze.so'):
    key='lib/'+abi+'/'+name
    if key not in z.namelist():fail('APK missing '+key)
    if name in LIBS and hashlib.sha256(z.read(key)).hexdigest()!=sha(TARGET/abi/name):fail('real APK packaged stale or altered LKR library '+key)
  if 'assets/licenses/rawlens_2_3_94_lkr_gpl_notice.txt' not in z.namelist():fail('new release GPL native notice not packaged')
 print('PASS real APK exact original 2.3.94 native release, both ABI JNI and GPL licence')
if __name__=='__main__':
 try:
  if sys.argv[1:]==['--native']:native()
  elif sys.argv[1:]==['--cmake']:cmake()
  elif sys.argv[1:]==['--apk']:apk()
  else:fail('usage --native|--cmake|--apk')
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
