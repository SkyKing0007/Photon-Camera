#!/usr/bin/env python3
"""26969 GLSL consumer/source active path, immutable processed routes and lifetime contracts."""
import pathlib,sys,re,hashlib
R=pathlib.Path(__file__).resolve().parent
root=R/'handoff_payload_26969' if '--payload' in sys.argv else R
k=root/'app/src/main/java/com/hinnka/mycamera/processor'
measure=(k/'GlesIris26969HdrqNoiseEven.kt').read_text()
consumer=(k/'GlesIris26870PostAmazeChroma.kt').read_text()
stack=(k/'GlesMgcRawSpatialStacker.kt').read_text()
for filename,text in [('measure',measure),('consumer',consumer)]:
 assert '#version 300 es' in text and text.count('void main()')==1,filename
 assert re.search(r'"""#version 300 es.*?"""\.trimIndent\(\)',text,re.S),filename
assert 'uIris26969CameraLinear' in measure and 'mean.x' in measure and 'v*0.0625' in measure
assert 'uIris26969NoiseEven' in consumer and 'iris26969Even(p,sourceRgb)' in consumer
assert 'if(uIris26924BOff!=0)' in consumer and 'oPostWbCameraRgb=vec4(rawrHighlightOff(sourceRgb),raw.a);' in consumer
assert 'GlesIris26969HdrqNoiseEven.measure' in stack and 'if (iris26969HdrqBOff)' in stack
assert stack.index('GlesIris26969HdrqNoiseEven.measure')<stack.index('bindTexture(applyProgram,"uIris26969NoiseVariance",4,iris26969NoiseVariance)')
assert 'releaseOwnedTexture(iris26969NoiseVariance' in stack
assert 'if(iris26969HdrqBOff) 1 else 0' in stack
assert 'rawrNativeReceipt26864 != null' in stack and 'iris26969HdrqBOff' in stack
assert 'var iris26969NoiseVariance = 0' in stack
assert 'uIris26969NoiseEven' not in (R/'26969_PROTECTED_SOURCE.sha256').read_text() # only hashing protected source paths
print('PASS 26969 real Kotlin GLSL container, post-AMaZE pre-WB B-OFF-only map and cleanup contracts')
