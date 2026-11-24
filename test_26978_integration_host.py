#!/usr/bin/env python3
"""Compile exact C-owned UI state methods with Java host models, plus output ingress source checks.
Android Canvas/Bitmap, EGL and native JPEG/R remain actual-device tests, not host proof.
"""
import argparse,pathlib,subprocess,tempfile,re
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);a=p.parse_args()
root=a.root/'src/main/java'
def get(n):
 q=list(root.rglob(n));assert len(q)==1,(n,q);return q[0].read_text()
s=get('CaptureController.java');f=get('Iris26978CFinalOutput.kt');e=get('Iris26975CPinnedDonorProEngine.kt')
# Extract the exact actual source owner state and methods; no reimplementation.
start=s.index('    private volatile com.hinnka.mycamera.processor.Iris26972CCamera2ShutterSession mIris26978CUiOwner;');end=s.index('    /* IRIS_26974_C_RAW_CALLBACK_IO_ISOLATION',start)
actual=s[start:end]
assert actual.count('CaptureController.isProcessing = true;')==1 and actual.count('CaptureController.isProcessing = false;')==1
host='''public class CaptureController {
public static boolean isProcessing;
private volatile com.hinnka.mycamera.processor.Iris26972CCamera2ShutterSession mIris26972CShutterSession;
'''+actual+'''
static int n;static void ok(boolean b){++n;if(!b)throw new AssertionError("check "+n);}
void reject(com.hinnka.mycamera.processor.Iris26972CCamera2ShutterSession o){try{iris26978CArmUi(o);throw new AssertionError("invalid arm accepted");}catch(IllegalStateException expected){ok(true);}}
public static void main(String[] x){
var c=new CaptureController();var stale=new com.hinnka.mycamera.processor.Iris26972CCamera2ShutterSession();
ok(!c.iris26978CIsUiBusy()&&!isProcessing);c.reject(stale);
for(int i=0;i<120;i++){
var active=new com.hinnka.mycamera.processor.Iris26972CCamera2ShutterSession();c.mIris26972CShutterSession=active;c.iris26978CArmUi(active);ok(c.iris26978CIsUiBusy()&&isProcessing);c.reject(active);c.reject(stale);ok(!c.iris26978CFinishUi(stale));ok(!c.iris26978CFinishUi(null));ok(c.iris26978CIsUiBusy()&&isProcessing);ok(c.iris26978CFinishUi(active));ok(!c.iris26978CIsUiBusy()&&!isProcessing);ok(!c.iris26978CFinishUi(active));stale=active;}
System.out.println("PASS "+n+" exact C UI arm, busy, stale terminal, duplicate terminal and release assertions");}}
'''
with tempfile.TemporaryDirectory() as td:
 r=pathlib.Path(td);src=r/'CaptureController.java';src.write_text(host);model=r/'com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.java';model.parent.mkdir(parents=True);model.write_text('package com.hinnka.mycamera.processor; public final class Iris26972CCamera2ShutterSession {}');subprocess.run(['javac','-d',str(r/'out'),str(src),str(model)],check=True);subprocess.run(['java','-cp',str(r/'out'),'CaptureController'],check=True)
# Confirm real output boundary contract not mere label reassignment, and same bitmap encoded.
assert 'Canvas(target).drawBitmap(source, bounds, bounds, null)' in f and 'setColorSpace(' not in f
assert 'sdr = finalSdr' in e and 'sdrBase = checkNotNull(sdr)' in e and 'Jpeg444ExportEncoder.write(\n                checkNotNull(sdr)' in e
assert 'HdrBuffer(hdrBitmap, HdrBufferEncoding.LINEAR_SRGB)' in e
print('PASS actual final output call-path guards; Android bitmap/gainmap/native execution NOT RUN')
