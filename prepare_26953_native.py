#!/usr/bin/env python3
"""Exact dual-ABI LK-R release native reuse from the latest SUCCESSFUL 26952 APK.
No upstream re-download, recompile, or older-version substitution.
"""
import hashlib,io,pathlib,subprocess,sys,zipfile
from build_26953_incremental import R,OUT,ART,ART_SHA,PRIOR_APK_NAME,PRIOR_APK_SHA,fail,sha
TARGET=R/'app/build/verified_rawlens26931/jniLibs'
ABIS=('arm64-v8a','armeabi-v7a');LIBS=('liblkrpipeline.so','libsrpipeline.so')
EXPECTED={
 ('arm64-v8a','liblkrpipeline.so'):'037a5f62649dcac7034c789c8e7ea2f250ca818d1c1c364e09a59f6897530105',
 ('arm64-v8a','libsrpipeline.so'):'f87cc70ad12a69345392a4eb73b6ec33739577ce8c39b7a4916180c344f67069',
 ('armeabi-v7a','liblkrpipeline.so'):'9297eb7c58ca242986bced32bf773dcc8d16c3beaa33c26142b152c585957b03',
 ('armeabi-v7a','libsrpipeline.so'):'48788035080e66efa63b693e35f0587d2f02e851b818c367f3915b6154b47d68',
}
SYMBOLS=('Java_com_matthew_rawlens_LkrBridge_nativeMerge',
 'Java_com_matthew_rawlens_LkrBridge_nativeSharpness',
 'Java_com_matthew_rawlens_LkrBridge_nativeTuningDefaults',
 'Java_com_matthew_rawlens_LkrBridge_nativeSetNoiseModel',
 'Java_com_matthew_rawlens_LkrBridge_nativeSetCacheDir')

def inspect(abi,name,p):
 hdr=subprocess.run(['readelf','-h',str(p)],capture_output=True,text=True)
 if hdr.returncode or ('ELF64' if abi=='arm64-v8a' else 'ELF32') not in hdr.stdout or ('AArch64' if abi=='arm64-v8a' else 'ARM') not in hdr.stdout:fail('actual ELF ABI wrong '+abi+'/'+name)
 symbols=subprocess.run(['readelf','-Ws',str(p)],capture_output=True,text=True)
 if symbols.returncode:fail('ELF symbol inspection failed '+str(p))
 if name=='liblkrpipeline.so':
  deps=subprocess.run(['readelf','-d',str(p)],capture_output=True,text=True)
  if deps.returncode or 'libsrpipeline.so' not in deps.stdout or 'libvulkan.so' not in deps.stdout:fail('original LKR dependencies changed')
  if any(x not in symbols.stdout for x in SYMBOLS):fail('original LK-R JNI ABI changed')
 else:
  if 'Java_com_rawlens_srpipeline_SrpBridge_nativeFreeDirect' not in symbols.stdout:fail('original LKR direct-buffer native free missing')

def from_success():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful published 26952 artifact not fetched')
 if TARGET.exists() and any(TARGET.rglob('*.so')):fail('stale Android native libraries already staged')
 with zipfile.ZipFile(ART) as z:
  if z.testzip() or PRIOR_APK_NAME not in z.namelist():fail('successful latest APK missing')
  apk=z.read(PRIOR_APK_NAME)
  if hashlib.sha256(apk).hexdigest()!=PRIOR_APK_SHA:fail('latest successful APK altered')
  receipt=z.read('photon_26952_outputs/26952_OFFICIAL_LKR_2_3_94_RECEIPT.txt').decode()
  with zipfile.ZipFile(io.BytesIO(apk)) as compiled:
   if compiled.testzip():fail('successful APK CRC invalid')
   report=['Exact successful published 26952 APK native reuse; NO predecessor older-source/native reconstruction',f'26952 artifact SHA256={ART_SHA}',f'26952 APK SHA256={PRIOR_APK_SHA}']
   for abi in ABIS:
    for name in LIBS:
     key=f'lib/{abi}/{name}'
     if key not in compiled.namelist():fail('actual successful APK missing native '+key)
     data=compiled.read(key);h=hashlib.sha256(data).hexdigest()
     if h!=EXPECTED[(abi,name)] or f'PASS {key} sha256={h} bytes={len(data)}' not in receipt:fail('published LK-R native does not match official release '+key)
     target=TARGET/abi/name;target.parent.mkdir(parents=True,exist_ok=True)
     target.write_bytes(data);inspect(abi,name,target)
     report.append(f'PASS {key} sha256={h} bytes={len(data)}')
 OUT.mkdir(exist_ok=True)
 (OUT/'26953_EXACT_SUCCESSFUL_26952_LKR_NATIVE_RECEIPT.txt').write_text('\n'.join(report)+'\n')
 print('PASS exact same 26952 published 2.3.94 native release both ABIs, original 3x2 JNI')
if __name__=='__main__':
 try:
  if sys.argv[1:]==['from-success']:from_success()
  else:fail('only: prepare_26953_native.py from-success')
 except Exception as e:print('26953 native BLOCKED: '+str(e),file=sys.stderr);sys.exit(1)
