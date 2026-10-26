#!/usr/bin/env python3
"""Exact original UnspektrAwesome 1.2.5 native JNI registration carrier proof.
No extra/missing native methods or restored 1.1.2 render/warmup overloads.
Original DEX application values for cadence/temporal and original library SHA.
"""
import re,hashlib,json,sys
from pathlib import Path
R=Path(sys.argv[1]).resolve() # app/ input
P=Path(__file__).resolve().parent
ref=json.loads((P/'26880_SPEKTRA_125_NATIVE_ABI.json').read_text())
methods=ref['native_methods']
assert len(methods)==37
lib=R/'src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so'
assert hashlib.sha256(lib.read_bytes()).hexdigest()==ref['original_64_bit_so_sha256']
java=R/'src/main/java/com/unspektrawesome'
classes={'VulkanRenderer':'vulkan/VulkanRenderer.kt','VulkanBridge':'vulkan/VulkanBridge.kt','RawUpload':'vulkan/RawUpload.kt','RawUploadPool':'vulkan/RawUploadPool.kt','RecordingRawBuffer':'preview/RecordingRawBuffer.kt','SpektraFilmRenderer':'spektra/SpektraFilmRenderer.kt'}
types={'Long':'J','Int':'I','Float':'F','Double':'D','Boolean':'Z','Unit':'V','String':'Ljava/lang/String;',
       'HardwareBuffer':'Landroid/hardware/HardwareBuffer;','Bitmap':'Landroid/graphics/Bitmap;',
       'Surface':'Landroid/view/Surface;','ByteBuffer':'Ljava/nio/ByteBuffer;','Any':'Ljava/lang/Object;',
       'IntArray':'[I','LongArray':'[J'}
for cname,relative in classes.items():
 original=(java/relative).read_text()
 s=re.sub(r'/\*.*?\*/','',original,flags=re.S);s=re.sub(r'//[^\n]*','',s)
 found=[]
 for m in re.finditer(r'\bexternal\s+fun\s+(\w+)\s*\(',s):
  depth=1;start=m.end();i=start
  while depth:
   if s[i]=='(':depth+=1
   elif s[i]==')':depth-=1
   i+=1
  ps=s[start:i-1];tail=s[i:];rt=re.match(r'\s*:\s*(\w+\??)',tail)
  return_type=(rt.group(1) if rt else 'Unit').replace('?','')
  args=[x.split(':',1)[1].strip().split('=')[0].strip().replace('?','') for x in ps.split(',') if x.strip()]
  d='('+''.join(types[t] for t in args)+')'+types[return_type]
  stat=bool(re.search(r'@JvmStatic\s+private\s+external\s+fun\s+'+re.escape(m.group(1))+r'\b',s))
  found.append((m.group(1),d,stat))
 expected={(x['method'],x['descriptor'],x['static']) for x in methods if x['class'].endswith('/'+cname+';')}
 assert set(found)==expected,(cname,sorted(expected-set(found)),sorted(set(found)-expected))
 assert len(found)==len(expected),('duplicate JNI declarations',cname)
vulkan=(java/'vulkan/VulkanRenderer.kt').read_text()
preview=(java/'preview/RawVulkanPreviewController.kt').read_text()
assert 'nativeRawUploads(current)' in vulkan and 'nativeRender(' in vulkan
assert 'renderer.renderOriginal125(' in preview and 'renderer.original125Uploads().copy(' in preview
assert 'original125Cadence.reset()' in preview and 'Original125Cadence' in preview
assert 'getFloat("temporal_strength", 0.3f)' in preview
assert 'getInt("temporal_frames", 4)' in preview
assert 'upload?.close()' in preview and 'finally {' in preview
assert 'renderer.render(' not in preview
assert 'RawPreviewQuality.FULL' in (R/'src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java').read_text()
assert 'renderer.warmUp(preview, step, part)' in (R/'src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPipelineWarmup.java').read_text()
assert 'val DEFAULT_PARAMS = SpektraFilmParams.exact125Default()' in (java/'spektra/SpektraState.kt').read_text()
assert 'Bitmap.Config.ARGB_8888' in preview and 'renderer.captureRcd(' in preview
assert 'jpegWriter.write(' in preview and 'image.recycle()' in preview
assert 'firstFrameListener?.run()' in preview and 'if (rendered)' in preview
print('PASS exact original 1.2.5 APK native arm64 SHA and ALL 37 JNI descriptors/staticness, RAW pool lifetime, source-level frame cadence, JPEG, viewfinder owners')
