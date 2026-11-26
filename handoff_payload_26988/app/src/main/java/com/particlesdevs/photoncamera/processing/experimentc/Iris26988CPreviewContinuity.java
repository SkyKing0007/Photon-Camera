package com.particlesdevs.photoncamera.processing.experimentc;

import java.nio.ByteBuffer;
import java.util.Arrays;
import java.util.LinkedHashMap;

/** C-private display-only matching of the last settled HAL body brightness to
 * the new protected/manual ISP frame. Every comparison requires an exact sensor
 * timestamp AND the current immutable request. No synthetic exposure evidence,
 * no Camera2 writes, and no use of the displayed (already compensated) image. */
public final class Iris26988CPreviewContinuity {
    private static final long WAIT_NS=280_000_000L, PROBE_NS=1_000_000_000L;
    private static final int MAX=32;
    private Object owner;
    private boolean manual;
    private long firstEvidence,firstApplied,lastEvidence,lastSample,transitionTs;
    private int matches;
    private float anchor=Float.NaN, anchorMean=Float.NaN, gain=1f;
    private double anchorEnergy;
    private final LinkedHashMap<Long,Float> samples=new LinkedHashMap<>();
    private final LinkedHashMap<Long,Evidence> evidence=new LinkedHashMap<>();
    private static final class Evidence {
        final float mean;final double energy;
        Evidence(float m,double e){mean=m;energy=e;}
    }
    public synchronized void reset(){owner=null;manual=false;anchor=anchorMean=Float.NaN;anchorEnergy=0;transitionTs=0;clearSamples();}
    private void clearSamples(){firstEvidence=firstApplied=lastEvidence=lastSample=0;matches=0;gain=1f;samples.clear();evidence.clear();}
    public synchronized boolean owns(Object request){return request!=null&&request==owner;}
    public synchronized void beginAuto(Object request,boolean keepAnchor){
        if(!keepAnchor)reset();else clearSamples();
        owner=request;manual=false;transitionTs=0;
    }
    public synchronized void beginManual(Object oldRequest,Object newRequest,long ts){
        if(!owns(oldRequest))reset();else clearSamples();
        owner=newRequest;manual=true;transitionTs=ts;
    }
    public synchronized boolean anchorReady(){return Float.isFinite(anchor)&&anchor>0f;}
    public synchronized boolean observe(Object request,long ts,long shutter,int iso,float rawMean){
        if(!owns(request)||ts<=lastEvidence||ts<=0||shutter<=0||iso<=0||!Float.isFinite(rawMean)||rawMean<0f)return false;
        lastEvidence=ts;if(firstEvidence==0)firstEvidence=ts;
        evidence.put(ts,new Evidence(rawMean,(double)shutter*iso));trim(evidence);
        match(ts);
        return anchorReady() && matches>=1 || ts-firstEvidence>=WAIT_NS;
    }
    public synchronized boolean wantsSample(Object request,long ts){
        if(!owns(request)||ts<=0||ts<=lastSample)return false;
        if(manual)return anchorReady()&&matches<2&&transitionTs>0&&ts>=transitionTs&&ts-transitionTs<=PROBE_NS;
        if(matches>=2)return false;
        return firstEvidence==0||ts-firstEvidence<=PROBE_NS;
    }
    public synchronized void sample(Object request,long ts,float level){
        if(!wantsSample(request,ts))return;
        lastSample=ts;
        if(!Float.isFinite(level)||level<=.0002f||level>=.85f)return;
        samples.put(ts,level);trim(samples);match(ts);
    }
    private static void trim(LinkedHashMap<?,?> m){while(m.size()>MAX)m.remove(m.keySet().iterator().next());}
    private void match(long ts){
        Evidence e=evidence.get(ts);Float y=samples.get(ts);
        if(e==null||y==null)return;
        evidence.remove(ts);samples.remove(ts);
        if(!anchorReady()){
            if(manual)return;
            anchor=y;anchorMean=e.mean;anchorEnergy=e.energy;matches=1;return;
        }
        double predicted=anchorMean*e.energy/anchorEnergy;
        // A true scene transition cannot be relabelled an ISP exposure change.
        double ratio=(e.mean+.002)/(predicted+.002);
        if(!Double.isFinite(ratio)||ratio<.67||ratio>1.50){gain=1f;firstApplied=0;return;}
        float next=matchGain(anchor,y);
        if(matches==0||firstApplied==0){gain=next;firstApplied=ts;}
        else gain=(float)Math.sqrt(gain*next);
        matches++;
    }
    public synchronized float gain(Object request,long ts){return !owns(request)?Float.NaN:firstApplied>0&&ts>=firstApplied?gain:1f;}
    public static float matchGain(float target,float actual){
        if(!Float.isFinite(target)||!Float.isFinite(actual)||target<=0f||target>=1f||actual<=0f||actual>=1f)return 1f;
        return (float)Math.max(.25,Math.min(8.0,(double)target*(1-actual)/(actual*(1-target))));
    }
    public static float whiteAnchored(float x,float g){return g*x/(1f+(g-1f)*x);}
    // The existing preview shader uses max(linear RGB) as the white-anchored guide.
    // Use the SAME guide in its original, uncompensated 12x96 OES sample.
    public static float medianGuide(ByteBuffer rgba){
        if(rgba==null)return Float.NaN;
        ByteBuffer b=rgba.duplicate();b.rewind();int n=b.remaining()/4;
        if(n!=12*96||b.remaining()!=4*n)return Float.NaN;
        float[] a=new float[n];int k=0;
        for(int i=0;i<n;i++){
            int peak=Math.max(b.get()&255,Math.max(b.get()&255,b.get()&255));b.get();
            float e=peak/255f;if(e>=.90f)continue;
            float y=e<=.04045f?e/12.92f:(float)Math.pow((e+.055f)/1.055f,2.4);
            if(y>.0002f)a[k++]=y;
        }
        if(k<n/4)return Float.NaN;Arrays.sort(a,0,k);return a[k/2];
    }
}
