package com.hinnka.mycamera.processor.experimentc.original129.raw
import kotlin.math.abs
fun main() {
    val a=MgcRawMaxDenoiseTuning.atSnr(3.5f); val b=MgcRawMaxDenoiseTuning.atSnr(5f); val mid=MgcRawMaxDenoiseTuning.atSnr(4.25f)
    for (i in 0..4) {check(abs(mid.lumaStrength[i]-(a.lumaStrength[i]+b.lumaStrength[i])/2)<1e-5);check(abs(mid.chromaStrength[i]-(a.chromaStrength[i]+b.chromaStrength[i])/2)<1e-5)}
    check(MgcRawMaxDenoiseTuning.atSnr(0f).chromaStrength.contentEquals(a.chromaStrength));check(!MgcRawMaxDenoiseTuning.atSnr(36f).chromaStrength.contentEquals(a.chromaStrength))
    check(MgcRawStackNoiseObservation.fit(emptyList())==null)
    fun fit(v:Float)=checkNotNull(MgcRawStackNoiseObservation.fit((0..63).map {i->val sig=if(i<32) .04f else .2f;val variance=v*sig;MgcRawStackNoiseObservation.Tile(sig,floatArrayOf(variance,variance*2,variance*3),floatArrayOf(variance*2,variance*4,variance*6))}))
    val noisy=fit(.01f); val clean=fit(.0001f); check(clean.snr>noisy.snr);check(clean.tileCount==64);check(noisy.chroma.read.all{it.isFinite()&&it>0});check(noisy.luma.read.isFinite())
    println("PASS actual donor measured SNR fit, noise coefficients and five-band interpolation")
}
