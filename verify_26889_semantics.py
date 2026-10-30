#!/usr/bin/env python3
"""Runtime ownership, reference chronology, 60/64 ABI and LONG fail-closed contract."""
import pathlib,sys,re,hashlib
assert len(sys.argv)==3, 'USAGE base-root candidate-root'
A=pathlib.Path(sys.argv[1])/'app';B=pathlib.Path(sys.argv[2])/'app'
relative='src/main/java/com/hinnka/mycamera/processor/'
bridge=(B/'src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
selector=(B/relative/'GlesIris26870GpuSharpest.kt').read_text()
classifier=(B/relative/'GlesIris26889BOffSceneMotion.kt').read_text()
long=(B/relative/'GlesIris26868DirectLong.kt').read_text()
original=(A/relative/'GlesIris26868DirectLong.kt').read_text()
stacker=(B/relative/'GlesMgcRawSpatialStacker.kt').read_text()
fusion=(B/relative/'GlesMgcRawFusion.kt').read_text()
def shader(s,name):
 m=re.search(r'val '+name+r' = """(.*?)"""\.trimIndent\(\)',s,re.S);assert m,name
 return m.group(1)
for name in ('trustedShadowGain','packCalibratedLong'):
 assert shader(original,name)==shader(long,name),'changed existing B-ON LONG shader'
assert shader(long,'trustedShadowGainBOffMotionSafe').count('#version 300 es')==1
assert selector.count('eligibleIndices:Set<Int>?=null')==1 and selector.count('if(eligibleIndices!=null && i !in eligibleIndices)continue')==1
assert 'val nearest=frozen.buffers.indices.sortedWith' in classifier and 'frozen.timestampsNs' in classifier
assert 'val adjacent=nearest.take(min(3,nearest.size)).toSet()' in classifier
assert 'for(peer in peers)' in classifier and 'globalX=median(coherent.map { it.dx })' in classifier
assert 'val bOffLongStaticSafe26889 = AtomicBoolean(false)' in bridge
assert bridge.count('GlesIris26889BOffSceneMotion.classify(')==1
assert bridge.count('iris26889BOffLongAllowed = { bOffLongStaticSafe26889.get() }')==1
assert 'if(staticSafe26889) null else motion26889?.shutterAdjacent ?: setOf(nativeReferenceIndex)' in bridge
assert bridge.count('GlesIris26870GpuSharpest.select(')==2,'B ON must retain original selector'
assert fusion.count('iris26889BOffLongAllowed = iris26889BOffLongAllowed')==1
assert stacker.count('if (!iris26889BOffLongAllowed())')==1
assert stacker.count('bOffLongMotionSafe = true')==1
rec=(B/'src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp').read_text()
assert 'alignVectorPad = 0;' in rec and 'static_assert(sizeof(FreqMergePc) == 64u' in rec
assert (A/'src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text().count('GlesIris26870GpuSharpest.select(')==2
assert 'if (p.uniformExposure != 0 && p.supportMeasured == 0) {' in (B/'src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp').read_text()
assert 'return reliable >= 2 ? 0.0 : 1.0;' in (B/'src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp').read_text()
assert not re.search(r'\b(?:sample|namespace|output|input)\s*(?:=|;|\()',shader(long,'trustedShadowGainBOffMotionSafe'))
print('PASS 26889 B-OFF shutter/timestamp/early3/full-static-reference/LONG ownership and original B-ON invariance')
