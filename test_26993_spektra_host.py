from pathlib import Path
import tempfile,subprocess,argparse
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);a=ap.parse_args();roots={'authority':a.base.resolve(),'candidate':a.candidate.resolve()}
with tempfile.TemporaryDirectory() as td:
 t=Path(td);stub=t/'android/graphics/ImageFormat.java';stub.parent.mkdir(parents=True);stub.write_text('package android.graphics; public final class ImageFormat {public static final int RAW_SENSOR=32, RAW10=37, RAW12=38;}')
 state=t/'com/unspektrawesome/camera/session/Camera2RawSession.java';state.parent.mkdir(parents=True);state.write_text('package com.unspektrawesome.camera.session; public class Camera2RawSession {public enum State {STREAMING,STILL_CAPTURED,STILL_FAILED,IDLE}}')
 test=R/'SpektraHostTest.java';host=state.parent/'HostTest.java';host.write_bytes(test.read_bytes())
 for label in ['authority','candidate']:
  d=roots[label]/'app/src/main/java/com/unspektrawesome/camera';classes=t/label
  subprocess.run(['javac','--release','17','-d',str(classes),str(stub),str(state),str(host),*[str(d/x) for x in ['RawPreviewPolicy.java','RawOutput.java','RawFormat.java','Size2d.java','IntRange.java','session/StillCapturePlanner.java']]],check=True)
  result=subprocess.run(['java','-cp',str(classes),'com.unspektrawesome.camera.session.HostTest'],capture_output=True,text=True);assert (result.returncode==0)==(label=='candidate');print(result.stdout.strip() if label=='candidate' else 'PASS reproduced maximum-resolution selection on baseline: '+result.stderr.splitlines()[0])
