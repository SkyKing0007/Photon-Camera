#!/usr/bin/env python3
"""Permanent 26874 on-device failures against exact previous and candidate sources.

Capture 1: B normal 14 NORMAL+1 LONG, eight-strip JPEG encoded 39ms but
IRIS_26874_B_JPEG_PUBLICATION published=false; no saved file. Capture 2:
B true2x 14 NORMAL+1 LONG rejected four-element Camera2 WB by RGB3 JNI.
The B true2x sensor-clip output consumer was unreachable under !B outer guard.
"""
from pathlib import Path
import sys, re
prior, now = (Path(x)/'app' for x in sys.argv[1:3])
bridge='src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
writer='src/main/cpp/iris26874_b_jpeg_writer.cpp'
pb= (prior/bridge).read_text(); nb=(now/bridge).read_text()
pw= (prior/writer).read_text(); nw=(now/writer).read_text()
assert 'frozen,\n                                wb, lsc, lscWidth' in pb
assert 'frozen,\n                                wb, lsc, lscWidth' not in nb
callback=nb.split('iris26864NativeWronski2x =',1)[1].split('iris26856RawrColor =',1)[0]
assert 'GlesIris26856RawrColorContract.freeze(' in callback
assert '.amazeWhiteBalance,' in callback
assert 'wb, lsc, lscWidth' not in callback
assert 'val amazeWhiteBalance: FloatArray' in (now/'src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrColorContract.kt').read_text()
mask_marker='IRIS_26864_B_ONLY_WRONSKI_2X_CLIP_FINAL_CONSUMER'
old=pb.split('IRIS_26837_DEVICE_SAFE_TRUE_FINAL_CLIP_ZONE_CHROMA_OWNER',1)[1].split('IRIS_26726_UNIVERSAL',1)[0]
new=nb.split('IRIS_26837_DEVICE_SAFE_TRUE_FINAL_CLIP_ZONE_CHROMA_OWNER',1)[1].split('IRIS_26726_UNIVERSAL',1)[0]
assert old.index('experiment26856 != Iris26856ABSettings.Mode.AMAZE_26855') < old.index(mask_marker) < old.index('} else if (clipZoneMaskTexture26836')
assert new.index('} else if (clipZoneMaskTexture26836') < new.index('IRIS_26875_B_TRUE2X_SENSOR_CLIP_CONSUMER_REACHABLE')
assert new.index('IRIS_26875_B_TRUE2X_SENSOR_CLIP_CONSUMER_REACHABLE') < new.rindex('GLES30.glDeleteTextures')
assert new.count('IRIS_26864_B_ONLY_WRONSKI_2X_CLIP_CONSUMED') == 1
assert 'checkNotNull(stacked.iris26864BTrue2xClipBitsPath)' in new
assert 'return writeAtomic(path' in pw and '.26874-pending' in pw
assert 'std::string(path)+".26874-pending"' not in nw and 'writeOwnedJpeg(' in nw
assert 'uhdr_set_base' in nw and 'uhdr_set_gain' in nw and 'uhdr_encode' in nw and 'write_open errno=' in nw
assert 'stripParserRetry=' in nw and 'private_turbo_encode' in nw
assert 'parallelStrips(' in nw and 'fitAndRemapMap(' not in nw
assert 'GlesIris26856RawrColorContract.freeze' in nb
for path in ['src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
 'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
 'src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26874BJpegPublisher.java',
 'src/main/cpp/CMakeLists.txt']:
 assert (prior/path).read_bytes()==(now/path).read_bytes(), 'A/shared or B routing changed: '+path
assert (now/'version.properties').read_text().count('VERSION_BUILD=26875')==1
print('PASS 26875 real 26874 WB4->RGB3; B final mask reachable; B JPEG publication per-stage reporting; A routing byte-invariant')
