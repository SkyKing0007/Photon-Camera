#!/usr/bin/env python3
import argparse,pathlib,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);a=p.parse_args();r=a.root/'src/main/java/com/particlesdevs/photoncamera/processing/experimentc'
source=r/'Iris26979CExposureTracking.java';pub=(r/'Iris26975CDonorMediaStorePublisher.java').read_text();name=pub[pub.index('    static boolean validDisplayName('):pub.index('    private static void validateSource(')]
java='''import com.particlesdevs.photoncamera.processing.experimentc.Iris26979CExposureTracking;
import com.particlesdevs.photoncamera.processing.experimentc.Iris26975CRawHighlightMeter;
public class Host26979 {
'''+name+'''
static int n;static void ok(boolean b){++n;if(!b)throw new AssertionError("check "+n);}
public static void main(String[] args){
var t=new Iris26979CExposureTracking();t.selectLens("0");
float step=1f/3f;int lo=-12,hi=12;
// Bright scene: coherent clipped RAW drives HAL AE compensation, even with flicker.
ok(t.observeProtection(.8f,1f,.03f,0f,step,0,lo,hi));int bias=t.compensation(0,lo,hi,step);ok(bias==-2);
// Never reset protection to zero simply because request or AE cycle changed.
for(int i=0;i<100;i++){t.resetRequest();t.selectLens("0");ok(t.compensation(0,lo,hi,step)==bias);ok(!t.observeProtection(0f,.65f,0f,2*step,step,0,lo,hi));ok(!t.observeProtection(0f,.64f,0f,2*step,step,0,lo,hi));ok(t.compensation(0,lo,hi,step)==bias);}
// A dark transition releases protection on two independent samples with unprotected headroom.
ok(!t.observeProtection(0f,.22f,0f,2*step,step,0,lo,hi));ok(t.observeProtection(0f,.23f,0f,2*step,step,0,lo,hi));ok(t.compensation(0,lo,hi,step)==0);
// User EV is separate and bounded; changing lens or manual mode invalidates bias.
ok(t.observeProtection(.8f,1f,.03f,0f,step,2,lo,hi));ok(t.compensation(2,lo,hi,step)==0);t.selectLens("1");ok(t.compensation(2,lo,hi,step)==2);
ok(t.observeProtection(.8f,1f,.03f,0f,step,0,lo,hi));t.clearProtection();ok(t.compensation(0,lo,hi,step)==0);ok(t.compensation(100,lo,hi,0)==hi);
// Large transitions react to the next 120ms probe, not 2x500ms; old/missing timestamps do not unlock.
long ts=1000000000L;ok(!t.observeLocked(ts,.02f,0f));ok(!t.shouldProbe(ts+110000000L));ok(t.observeLocked(ts+120000000L,.6f,.11f));t.resetRequest();ok(!t.observeLocked(ts,.6f,.11f));ok(t.observeLocked(ts+120000000L,.02f,0f));t.resetRequest();ok(!t.observeLocked(ts,Float.NaN,Float.NaN));ok(!t.shouldProbe(ts));
// Touch metering does not relock while searching or before settling. The exact physical pair must stabilize.
t.resetRequest();ok(!t.observeAuto(ts,30000000,6400,2,true));ok(!t.observeAuto(ts+120000000,30000000,6401,2,true));ok(!t.observeAuto(ts+350000000,30000000,5000,1,true));ok(!t.observeAuto(ts+470000000,30000000,3200,2,true));ok(t.observeAuto(ts+590000000,30000000,3201,2,true));ok(!t.observeAuto(ts+590000000,30000000,3201,2,true));
t.resetRequest();ok(!t.observeAuto(ts,8333000,1763,2,false));ok(t.observeAuto(ts+120000000,8333000,1764,2,false));
for(String prefix:new String[]{"IMG_","Iris ","旅行_","_",".camera","A"})ok(validDisplayName(prefix+"20261124_013900.jpg"));
for(String name:new String[]{"../x20261124_013900.jpg","a/b20261124_013900.jpg","a\\\\b20261124_013900.jpg","a:20261124_013900.jpg","a?20261124_013900.jpg","a\\n20261124_013900.jpg","..20261124_013900.jpg","a.png",""})ok(!validDisplayName(name));
ok(validDisplayName("IRIS_C_26975.jpg"));
// Compile and exercise actual RAW sampler, including the coherent high signal needed for bias release.
int w=512,h=384,white=4095;float[] black={64,64,64,64};
var raw=java.nio.ByteBuffer.allocate(w*h*2).order(java.nio.ByteOrder.nativeOrder());
for(int y=0;y<h;y++)for(int x=0;x<w;x++)raw.putShort(2*(y*w+x),(short)(x<w/4?white:250));
var bright=Iris26975CRawHighlightMeter.measure(raw,w*2,2,0,0,w,h,white,black);
ok(bright.protectionEv>=.35f);ok(bright.highlightSignal>.98f);ok(bright.clippedFraction>.20f);
for(int i=0;i<w*h;i++)raw.putShort(2*i,(short)250);
var dark=Iris26975CRawHighlightMeter.measure(raw,w*2,2,0,0,w,h,white,black);
ok(dark.protectionEv==0f);ok(dark.highlightSignal<.08f);ok(dark.clippedFraction==0f);
System.out.println("PASS "+n+" C exposure tracking, touch settle, flicker-safe compensation, non-ratcheting release and prefix assertions");}}
'''
with tempfile.TemporaryDirectory() as td:
 d=pathlib.Path(td);f=d/'Host26979.java';f.write_text(java);subprocess.run(['javac','-d',str(d),str(source),str(r/'Iris26975CRawHighlightMeter.java'),str(f)],check=True);subprocess.run(['java','-cp',str(d),'Host26979'],check=True)
