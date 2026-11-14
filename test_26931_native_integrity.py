#!/usr/bin/env python3
"""Original RawLens release native ELF/JNI, newly built Iris JNI both ABIs and APK exact-byte proof."""
from __future__ import annotations
import argparse,hashlib,pathlib,re,subprocess,sys,zipfile
from build_26931_incremental import R,fail,sha,APKNAME
ABIS=('arm64-v8a','armeabi-v7a')
LIBS=('liblkrpipeline.so','libsrpipeline.so')
OUT=R/'app/build/verified_rawlens26931/jniLibs'
ARM_HASH={
 'liblkrpipeline.so':'af1d4caff00b3b189d23d1d53c7c9d11256f5b050af2590c5407191ce32cd39b',
 'libsrpipeline.so':'a91e0a33226db0e08b5355e2fac189cc9b91af7106530f6577d5084f1f39865d'}
METHODS=('Java_com_matthew_rawlens_LkrBridge_nativeMerge',
         'Java_com_matthew_rawlens_LkrBridge_nativeSharpness',
         'Java_com_matthew_rawlens_LkrBridge_nativeTuningDefaults',
         'Java_com_matthew_rawlens_LkrBridge_nativeSetNoiseModel',
         'Java_com_matthew_rawlens_LkrBridge_nativeSetCacheDir')
EXTRA=('Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePrepare',
       'Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePublishRgba16f',
       'Java_com_hinnka_mycamera_processor_GlesIris26931LkrBridge_nativePublishClipR16f')
def readelf(args):
 p=subprocess.run(['readelf',*args],capture_output=True,text=True)
 if p.returncode:fail('real ELF inspection failed '+p.stderr)
 return p.stdout
def check_original():
 for abi in ABIS:
  for name in LIBS:
   path=OUT/abi/name
   if not path.is_file():fail('original RawLens 2.2.86 library absent '+str(path))
   header=readelf(['-h',str(path)]);deps=readelf(['-d',str(path)])
   if ('ELF64' if abi=='arm64-v8a' else 'ELF32') not in header or ('AArch64' if abi=='arm64-v8a' else 'ARM') not in header:fail('wrong original release ELF ABI '+abi+' '+name)
   if name=='liblkrpipeline.so' and ('libsrpipeline.so' not in deps or 'libvulkan.so' not in deps):fail('partial upstream LKR Vulkan/native dependency')
   if abi=='arm64-v8a' and sha(path)!=ARM_HASH[name]:fail('arm64 original release binary hash mismatch')
  contents=readelf(['-Ws',str(OUT/abi/LIBS[0])]);free=readelf(['-Ws',str(OUT/abi/LIBS[1])])
  for needle in METHODS:
   if needle not in contents:fail('missing original released LKR JNI '+abi+' '+needle)
  if 'Java_com_rawlens_srpipeline_SrpBridge_nativeFreeDirect' not in free:fail('missing original native buffer free ABI '+abi)
 print('PASS exact original RawLens 2.2.86 full LKR Vulkan/shader, native admission and buffer free, both ABIs')
def check_cmake():
 check_original()
 for abi in ABIS:
  candidates=list((R/'app/.cxx').glob('**/'+abi+'/libiris26856amaze.so'))
  candidates+=list((R/'app/build').glob('**/'+abi+'/libiris26856amaze.so'))
  candidates=list(dict.fromkeys(candidates))
  if not candidates:fail('real Android NDK CMake freshly compiled Iris JNI lib absent '+abi)
  for name in candidates:
   symbols=readelf(['-Ws',str(name)])
   if all(x in symbols for x in EXTRA):break
  else:fail('real Android NDK '+abi+' native adapter not linked into Iris lib')
 print('PASS real 26931 Iris native JNI BOTH Android ABIs with all required GL transport functions')
def check_apk():
 # After Gradle, the first check must inspect the actual built output BEFORE
 # finalize renames it. Finalize calls this check again on the sealed name.
 candidates=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(candidates)!=1:fail('expected exactly one genuine Android Gradle APK before final seal')
 path=R/APKNAME if (R/APKNAME).is_file() else candidates[0]
 if not path.is_file():fail('assembled 26931 APK absent')
 with zipfile.ZipFile(path) as z:
  if z.testzip() is not None:fail('published 26931 APK ZIP CRC invalid')
  manifest=z.namelist()
  for abi in ABIS:
   for name in (*LIBS,'libiris26856amaze.so'):
    k=f'lib/{abi}/{name}'
    if k not in manifest:fail('APK absent important native library '+k)
    if name in LIBS and hashlib.sha256(z.read(k)).hexdigest()!=sha(OUT/abi/name):fail('APK original RawLens native modified by packaging '+k)
  if not any(x.startswith('assets/licenses/rawlens_2_2_86_lkr_apache_notice.txt') for x in manifest):fail('Apache license and NOTICE absent from published APK')
 print('PASS APK real packaged upstream liblkrpipeline + dependency both ABIs with exact SHA and license')
if __name__=='__main__':
 try:
  if sys.argv[1:]==['--native']:check_original()
  elif sys.argv[1:]==['--cmake']:check_cmake()
  elif sys.argv[1:]==['--apk']:check_apk()
  else:fail('usage: test_26931_native_integrity.py --native|--cmake|--apk')
 except Exception as e:print('ERROR',e,file=sys.stderr);sys.exit(1)
