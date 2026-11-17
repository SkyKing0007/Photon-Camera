#!/usr/bin/env python3
"""Historical original LK-R from successful 26951 APK, then exact official RawLens 2.3.94 dual-ABI.
The two modes deliberately separate old mandatory regression from current native release override.
"""
import hashlib,io,pathlib,shutil,subprocess,sys,zipfile
from build_26952_incremental import R,ART,ART_SHA,RUN,COMMIT,ART_ID,PRIOR_APK_SHA,PRIOR_APK_NAME,TMP,OUT,fail,sha
TARGET=R/'app/build/verified_rawlens26931/jniLibs'
RELEASE='https://github.com/matthew777777/RawLens/releases/download/2.3.94/RawLens-2.3.94-release.apk'
RELEASE_SHA='6996d936c22e116f2f6083efe8402b4513310b48266f1efda6d18a162b5710b6'
ARM_SHA={'liblkrpipeline.so':'037a5f62649dcac7034c789c8e7ea2f250ca818d1c1c364e09a59f6897530105','libsrpipeline.so':'f87cc70ad12a69345392a4eb73b6ec33739577ce8c39b7a4916180c344f67069'}
OLD_ARM={'liblkrpipeline.so':'af1d4caff00b3b189d23d1d53c7c9d11256f5b050af2590c5407191ce32cd39b','libsrpipeline.so':'a91e0a33226db0e08b5355e2fac189cc9b91af7106530f6577d5084f1f39865d'}
ABIS=('arm64-v8a','armeabi-v7a');LIBS=('liblkrpipeline.so','libsrpipeline.so')
SYMBOLS=('Java_com_matthew_rawlens_LkrBridge_nativeMerge','Java_com_matthew_rawlens_LkrBridge_nativeSharpness','Java_com_matthew_rawlens_LkrBridge_nativeTuningDefaults','Java_com_matthew_rawlens_LkrBridge_nativeSetNoiseModel','Java_com_matthew_rawlens_LkrBridge_nativeSetCacheDir')

def inspect(abi,name,src):
 hdr=subprocess.run(['readelf','-h',str(src)],capture_output=True,text=True)
 if hdr.returncode or ('ELF64' if abi=='arm64-v8a' else 'ELF32') not in hdr.stdout or ('AArch64' if abi=='arm64-v8a' else 'ARM') not in hdr.stdout:fail('native ABI identity incorrect '+abi+'/'+name)
 if name=='liblkrpipeline.so':
  dyn=subprocess.run(['readelf','-d',str(src)],capture_output=True,text=True).stdout
  if 'libsrpipeline.so' not in dyn or 'libvulkan.so' not in dyn:fail('new LKR dependencies changed '+abi)
  symbols=subprocess.run(['readelf','-Ws',str(src)],capture_output=True,text=True).stdout
  for symbol in SYMBOLS:
   if symbol not in symbols:fail('native JNI symbol absent '+abi+' '+symbol)
 else:
  symbols=subprocess.run(['readelf','-Ws',str(src)],capture_output=True,text=True).stdout
  if 'Java_com_rawlens_srpipeline_SrpBridge_nativeFreeDirect' not in symbols:fail('native buffer release ABI absent '+abi)

def original():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26951 authority ZIP unavailable')
 if TARGET.exists() and list(TARGET.rglob('*.so')):fail('stale native ELF preexisting before original seeding')
 OUT.mkdir(exist_ok=True,parents=True)
 with zipfile.ZipFile(ART) as z:
  if z.testzip() or PRIOR_APK_NAME not in z.namelist():fail('successful 26951 APK unavailable')
  apk=z.read(PRIOR_APK_NAME)
  if hashlib.sha256(apk).hexdigest()!=PRIOR_APK_SHA:fail('successful 26951 APK actual SHA mismatch')
  with zipfile.ZipFile(io.BytesIO(apk)) as src:
   if src.testzip():fail('26951 APK CRC')
   report=[f'SUCCESSFUL 26951 Actions run={RUN} commit={COMMIT} published artifact={ART_ID}',f'actual published artifact sha256={ART_SHA}',f'original APK sha256={PRIOR_APK_SHA}', 'EXACT PRE-26952 RawLens 2.2.86 historical native proof']
   for abi in ABIS:
    for name in LIBS:
     arc='lib/'+abi+'/'+name
     if arc not in src.namelist():fail('historical native library absent '+arc)
     dst=TARGET/abi/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read(arc))
     inspect(abi,name,dst)
     if abi=='arm64-v8a' and sha(dst)!=OLD_ARM[name]:fail('prior original native wrong '+name)
     report.append(f'PASS {arc} sha256={sha(dst)}')
 (OUT/'26952_ORIGINAL_NATIVE_26951_RECEIPT.txt').write_text('\n'.join(report)+'\n')
 print('PASS original published 26951 APK native, both ABIs original 2.2.86 JNI; historical gate available')

def official():
 if not (OUT/'26952_ORIGINAL_NATIVE_26951_RECEIPT.txt').is_file():fail('historical 26951 native proof must run before official upgrade')
 for abi in ABIS:
  for name in LIBS:
   if not (TARGET/abi/name).is_file():fail('historical native missing before replacement')
 TMP.mkdir(exist_ok=True,parents=True)
 apkfile=TMP/'RawLens-2.3.94-release-pinned.apk'
 if apkfile.is_file() and sha(apkfile)!=RELEASE_SHA:apkfile.unlink()
 if not apkfile.exists():
  # Official public RawLens release is a large, cross-host redirected GitHub
  # asset. Use the same pinned curl -L discipline as the successful 26951
  # Actions artifact, not urllib redirect streaming; fail closed on HTTP and SHA.
  subprocess.run(['curl','--fail','--location','--retry','3',
   '--silent','--show-error','-A','Photon-26952-Actions-verified-source-port',
   '--connect-timeout','30','--max-time','600',RELEASE,'-o',str(apkfile)],check=True)
 if sha(apkfile)!=RELEASE_SHA:fail('official 2.3.94 APK SHA-256 mismatches GitHub release digest')
 with zipfile.ZipFile(apkfile) as z:
  if z.testzip():fail('official release APK CRC')
  expected={f'lib/{abi}/{name}' for abi in ABIS for name in LIBS}
  if not expected<=set(z.namelist()):fail('official 2.3.94 dual-ABI native release incomplete')
  report=['Source=official RawLens 2.3.94 tagged GitHub release',f'URL={RELEASE}',f'official APK sha256={RELEASE_SHA}','Binary changes limited to four explicitly SHA-recorded jniLibs','Algorithm schedule controlled by unchanged Iris Java T=3, data_steps=2, output_scale=2']
  for abi in ABIS:
   for name in LIBS:
    dst=TARGET/abi/name
    new=z.read('lib/'+abi+'/'+name)
    dst.write_bytes(new)
    inspect(abi,name,dst)
    digest=sha(dst)
    if abi=='arm64-v8a' and digest!=ARM_SHA[name]:fail('official RawLens release arm64 library differs from supplied APK '+name)
    report.append(f'PASS lib/{abi}/{name} sha256={digest} bytes={len(new)}')
 (OUT/'26952_OFFICIAL_LKR_2_3_94_RECEIPT.txt').write_text('\n'.join(report)+'\n')
 print('PASS original official 2.3.94 release dual ABI, pinned entire APK digest, runtime native symbol/dependency/arch contracts')
if __name__=='__main__':
 try:
  if sys.argv[1:]==['original']:original()
  elif sys.argv[1:]==['official']:official()
  else:fail('usage: python3 -S prepare_26952_native.py original|official')
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
