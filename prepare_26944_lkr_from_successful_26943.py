#!/usr/bin/env python3
"""Pin and restore the exact unchanged RawLens 2.2.86 ELF libraries from 26943 V5 APK."""
import pathlib,zipfile,tempfile,hashlib,subprocess,shutil,sys
from build_26944_incremental import R,ART,ART_SHA,TAR_SHA,ART_ID,RUN,COMMIT,PRIOR_APK_SHA,OUT,fail,sha
APK_NAME='IrisCamera-0.9726943-26943-iris-rawr-debug.apk'
TARGET=R/'app/build/verified_rawlens26931/jniLibs'
RECEIPT=OUT/'26944_INHERITED_LKR_NATIVE_RECEIPT.txt'
LIBRARY_SHA={
 'arm64-v8a':{'liblkrpipeline.so':'af1d4caff00b3b189d23d1d53c7c9d11256f5b050af2590c5407191ce32cd39b',
              'libsrpipeline.so':'a91e0a33226db0e08b5355e2fac189cc9b91af7106530f6577d5084f1f39865d'},
 'armeabi-v7a':{'liblkrpipeline.so':'46de04ea3b1d37fbcc9bb380f94d56e7d7ad74d110e990e8413589e4e7eb8450',
                'libsrpipeline.so':'61fdaab8881684999c03bf6d9a3cbe1d9b3da63effe0f364eaca103f97efe78c'},
}
def main():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26943 V5 published archive unavailable')
 if TARGET.is_symlink() or any(TARGET.glob('**/*.so')):fail('preexisting or stale RawLens binaries at destination')
 OUT.mkdir(parents=True,exist_ok=True)
 report=[f'26944 native origin=SUCCESSFUL 26943 V5 Actions run={RUN} commit={COMMIT} artifact={ART_ID}',
  '26943 artifact sha256='+ART_SHA,'26943 compiled TAR sha256='+TAR_SHA,
  '26943 APK sha256='+PRIOR_APK_SHA,
  'mode=ORIGINAL_RAWLENS_2_2_86_EXACT_OFFLINE_VERIFIED_SUCCESSFUL_26943_V5_APK',
  'external GitHub release API/download=NOT USED','previous APK rebuild=NOT USED',
  'new 26944 actual Kotlin/Java/GLSL/NDK/CMake/dual-ABI/assemble=MANDATORY']
 with tempfile.TemporaryDirectory(prefix='26944_rawlens_') as d:
  apkfile=pathlib.Path(d)/APK_NAME
  with zipfile.ZipFile(ART) as art:
   if art.testzip() or APK_NAME not in art.namelist():fail('successful 26943 APK absent/invalid')
   with art.open(APK_NAME) as src,apkfile.open('wb') as dst:shutil.copyfileobj(src,dst,length=4*1024*1024)
   if PRIOR_APK_SHA not in art.read('photon_26943_outputs/26943_APK.sha256').decode():fail('26943 published APK receipt mismatch')
  if sha(apkfile)!=PRIOR_APK_SHA:fail('26943 APK bytes mismatch')
  with zipfile.ZipFile(apkfile) as apk:
   if apk.testzip():fail('26943 APK ZIP CRC failed')
   for abi,libs in LIBRARY_SHA.items():
    for name,want in libs.items():
     arc='lib/'+abi+'/'+name
     if arc not in apk.namelist():fail('original RawLens ABI missing '+arc)
     data=apk.read(arc)
     if hashlib.sha256(data).hexdigest()!=want:fail('original RawLens ELF mismatch '+arc)
     dst=TARGET/abi/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
     if sha(dst)!=want:fail('restored ABI checksum wrong '+arc)
     p=subprocess.run(['readelf','-h',str(dst)],capture_output=True,text=True)
     markers=('ELF64','AArch64') if abi=='arm64-v8a' else ('ELF32','ARM')
     if p.returncode or any(x not in p.stdout for x in markers):fail('wrong original RawLens ELF ABI '+arc)
     report.append(f'PASS original RawLens 2.2.86 {arc} sha256={want} bytes={len(data)}')
   if 'assets/licenses/rawlens_2_2_86_lkr_apache_notice.txt' not in apk.namelist():fail('original RawLens attribution missing')
 RECEIPT.write_text('\n'.join(report)+'\n')
 print('PASS exact successful 26943 V5 APK RawLens native binaries both ABIs and four source SHAs')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
