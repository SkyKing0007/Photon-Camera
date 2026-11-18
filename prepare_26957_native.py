#!/usr/bin/env python3
"""Reuse the four exact 26956 published RawLens 2.3.94 JNI libraries, read-only."""
import hashlib,io,subprocess,sys,zipfile
from build_26957_incremental import R,OUT,ART,ART_SHA,PRIOR_APK_NAME,PRIOR_APK_SHA,fail,sha
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
def inspect(abi,name,path):
 hdr=subprocess.run(['readelf','-h',str(path)],capture_output=True,text=True)
 if hdr.returncode or ('ELF64' if abi=='arm64-v8a' else 'ELF32') not in hdr.stdout or ('AArch64' if abi=='arm64-v8a' else 'ARM') not in hdr.stdout:fail('published native ELF wrong '+abi+'/'+name)
 symbols=subprocess.run(['readelf','-Ws',str(path)],capture_output=True,text=True)
 if symbols.returncode:fail('readelf -Ws failure '+str(path))
 if name=='liblkrpipeline.so':
  deps=subprocess.run(['readelf','-d',str(path)],capture_output=True,text=True)
  if deps.returncode or 'libsrpipeline.so' not in deps.stdout or 'libvulkan.so' not in deps.stdout:fail('original LKR dependencies changed')
  if any(x not in symbols.stdout for x in SYMBOLS):fail('published original LKR JNI export missing')
 elif 'Java_com_rawlens_srpipeline_SrpBridge_nativeFreeDirect' not in symbols.stdout:fail('original SR JNI export missing')
def from_success():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26956 artifact absent/altered')
 if TARGET.exists() and any(TARGET.rglob('*.so')):fail('stale native staged at output path')
 with zipfile.ZipFile(ART) as z:
  if z.testzip() or PRIOR_APK_NAME not in z.namelist():fail('26956 published APK missing')
  apk=z.read(PRIOR_APK_NAME)
  if hashlib.sha256(apk).hexdigest()!=PRIOR_APK_SHA:fail('26956 published APK differs')
  receipt=z.read('photon_26956_outputs/26956_EXACT_SUCCESSFUL_26955_LKR_NATIVE_RECEIPT.txt').decode()
  with zipfile.ZipFile(io.BytesIO(apk)) as compiled:
   if compiled.testzip():fail('26956 published APK CRC invalid')
   report=['PASS exact published 26956 previous APK original RawLens 2.3.94 four JNI; NO native rebuild/replacement',f'26956 artifact={ART_SHA}',f'26956 APK={PRIOR_APK_SHA}']
   for abi in ABIS:
    for name in LIBS:
     key=f'lib/{abi}/{name}'
     if key not in compiled.namelist():fail('26956 APK missing '+key)
     data=compiled.read(key);digest=hashlib.sha256(data).hexdigest()
     if digest!=EXPECTED[(abi,name)] or f'PASS {key} sha256={digest} bytes={len(data)}' not in receipt:fail('26956 published native receipt mismatch '+key)
     dst=TARGET/abi/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);inspect(abi,name,dst)
     report.append(f'PASS {key} sha256={digest} bytes={len(data)}')
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'26957_EXACT_SUCCESSFUL_26956_LKR_NATIVE_RECEIPT.txt').write_text('\n'.join(report)+'\n')
 print('PASS original four published 26956 native binaries both ABIs unchanged')
if __name__=='__main__':
 try:
  if sys.argv[1:]==['from-success']:from_success()
  else:fail('usage: prepare_26957_native.py from-success')
 except Exception as e:print('26957 NATIVE BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
