#!/usr/bin/env python3
"""26974 V3 actual javac Camera2 API regression: no nonexistent CaptureRequest.getTargets()."""
from pathlib import Path
import hashlib,subprocess,tempfile,sys,re
R=Path(__file__).resolve().parent
P=(R if '--live' in sys.argv else R/'handoff_payload_26974')
path=P/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
s=path.read_text()
start=s.index('    private boolean iris26974CResumePreviewOnly(')
br=s.index('{',start);depth=0;end=None
for i in range(br,len(s)):
 if s[i]=='{':depth+=1
 if s[i]=='}':
  depth-=1
  if depth==0:end=i+1;break
assert end
method=s[start:end]
assert 'getTargets(' not in method, 'CaptureRequest.getTargets() is not Android API'
assert 'mIris26974PreviewTargetOwner != builder' in method
assert 'ownedReader != mImageReaderRaw' in method
assert 'mIris26974PreviewRawTargetAdded' in method
assert 'builder.removeTarget(rawSurface)' in method
assert 'builder.addTarget(rawSurface)' in method
assert 'setRepeatingRequest(onlyPreview' in method
assert s.count('mIris26974PreviewTargetOwner = mPreviewRequestBuilder;')==1
assert s.count('mIris26974PreviewRawTargetAdded = false;')>=1
assert s.count('mIris26974PreviewRawTargetAdded = true;')==1
assert 'mPreviewRequestBuilder.addTarget(surface);' in s
assert 'mPreviewRequestBuilder.addTarget(mImageReaderRaw.getSurface());' in s
java="""import java.util.*;
class Check {
 static class Surface {boolean isValid(){return true;}}
 static class Handler {}
 static class CameraDevice {}
 static class ImageReader {final Surface src; ImageReader(Surface s){src=s;} Surface getSurface(){return src;}}
 static class CaptureRequest {
  final Set<Surface> targets;
  CaptureRequest(Set<Surface> s){targets=new HashSet<>(s);}
  static class Builder {
   final Set<Surface> targets=new HashSet<>();
   void addTarget(Surface s){targets.add(s);}
   void removeTarget(Surface s){targets.remove(s);}
   CaptureRequest build(){return new CaptureRequest(targets);}
  }
 }
 static class CameraCaptureSession {
  CaptureRequest last; boolean fail;
  void setRepeatingRequest(CaptureRequest r,Object callback,Handler handler) throws Exception {
   if(fail)throw new Exception("simulated HAL failure");
   last=r;
  }
 }
 static class Log {static void i(String t,String v){} static void e(String t,String v){} static void e(String t,String v,Exception e){}}
 static final String TAG="test";
 Object mIris26972CShutterSession=new Object();
 CameraCaptureSession mCaptureSession;
 CaptureRequest.Builder mPreviewRequestBuilder;
 Handler mBackgroundHandler=new Handler();
 CameraDevice mCameraDevice=new CameraDevice();
 Surface surface=new Surface();
 Object mCaptureCallback=new Object();
 ImageReader mImageReaderRaw;
 CaptureRequest.Builder mIris26974PreviewTargetOwner;
 boolean mIris26974PreviewRawTargetAdded;
 METHOD
 static void go(boolean raw) {
  Check c=new Check();c.mCaptureSession=new CameraCaptureSession();
  Surface rawSurface=new Surface();c.mImageReaderRaw=new ImageReader(rawSurface);
  c.mPreviewRequestBuilder=new CaptureRequest.Builder();c.mPreviewRequestBuilder.addTarget(c.surface);
  if(raw)c.mPreviewRequestBuilder.addTarget(rawSurface);
  c.mIris26974PreviewTargetOwner=c.mPreviewRequestBuilder;c.mIris26974PreviewRawTargetAdded=raw;
  if(!c.iris26974CResumePreviewOnly(c.mCaptureSession,c.mImageReaderRaw))throw new AssertionError("failed");
  if(!c.mCaptureSession.last.targets.contains(c.surface)||c.mCaptureSession.last.targets.contains(rawSurface))throw new AssertionError("preview RAW topology");
  if(c.mPreviewRequestBuilder.targets.contains(rawSurface)!=raw)throw new AssertionError("builder restored RAW ownership");
  CameraCaptureSession unrelated=new CameraCaptureSession();
  if(c.iris26974CResumePreviewOnly(unrelated,c.mImageReaderRaw))throw new AssertionError("stale session accepted");
  ImageReader unrelatedReader=new ImageReader(new Surface());
  if(c.iris26974CResumePreviewOnly(c.mCaptureSession,unrelatedReader))throw new AssertionError("wrong reader accepted");
  c.mCaptureSession.fail=true;
  if(c.iris26974CResumePreviewOnly(c.mCaptureSession,c.mImageReaderRaw))throw new AssertionError("HAL failure accepted");
  if(c.mPreviewRequestBuilder.targets.contains(rawSurface)!=raw)throw new AssertionError("failure did not restore builder");
 }
 public static void main(String[] args){go(true);go(false);System.out.println("PASS javac 26974 preview-only target membership, A/B restore, stale session, wrong RAW reader, HAL failure");}
}
""".replace(' METHOD',method.replace('android.media.ImageReader','ImageReader'))
with tempfile.TemporaryDirectory(prefix='p26974_v3_android_api_') as tmp:
 tmp=Path(tmp);(tmp/'Check.java').write_text(java)
 p=subprocess.run(['javac','-Xlint:all','-d',str(tmp),(tmp/'Check.java').as_posix()],capture_output=True,text=True)
 if p.returncode:raise RuntimeError('real javac API fixture failed: '+p.stderr)
 p=subprocess.run(['java','-cp',str(tmp),'Check'],capture_output=True,text=True,check=True)
 print(p.stdout.strip())
 # Negative regression: reproduce the *exact* nonexistent Android API invocation.
 bad=java.replace('final CaptureRequest onlyPreview = builder.build();','final CaptureRequest onlyPreview = builder.build();\n                onlyPreview.getTargets();')
 assert bad!=java
 (tmp/'Check.java').write_text(bad)
 p=subprocess.run(['javac','-d',str(tmp),(tmp/'Check.java').as_posix()],capture_output=True,text=True)
 assert p.returncode!=0 and 'cannot find symbol' in p.stderr and 'getTargets' in p.stderr, p.stderr
 print('PASS real javac negative: CaptureRequest.getTargets() rejected as unavailable Android API')
