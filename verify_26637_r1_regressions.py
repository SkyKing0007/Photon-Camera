#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26637_r1_regressions.py BASE CANDIDATE')
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
cpp=(cand/'app/src/main/cpp/iris_heic_jni.cpp').read_text(); java=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java').read_text()
# Permanent container regressions from real 26636 samples.
fb=cpp[cpp.index('static bool iris26636FillBaseImage'):cpp.index('static bool iris26636FillGainmapImage')]
assert 'heif_chroma_interleaved_RGB' in fb and 'heif_chroma_interleaved_RGBA' not in fb
assert 'IRIS_26637_OPAQUE_RGB_HEIC_BASE_OWNER' in fb
assert 'heif_transfer_characteristic_IEC_61966_2_1' in cpp
assert 'IccHelper::writeIccProfile(UHDR_CT_SRGB, UHDR_CG_DISPLAY_P3)' in cpp
assert 'save_two_colr_boxes_when_ICC_and_nclx_available = 1' in cpp
# Existing gain-map authority remains intact.
for needle in ['metadata.hdr_capacity_min = minDisplayRatio','metadata.hdr_capacity_max = fullDisplayRatio','metadata.use_base_cg = 1','heif_encoder_set_lossy_quality(encoder, 95)','heif_context_encode_gain_map_image']:
 assert needle in cpp, needle
# Hardware path stays 8-bit 4:2:0 and hardware-only; capability proof is diagnostic only.
for needle in ['heif_chroma_420','encodeI420','IRIS_26637_HEVC_ACTUAL_OUTPUT_PROOF']:
 assert needle in cpp, needle
for needle in ['info.isHardwareAccelerated()','COLOR_FormatYUV420Flexible','softwareFallback=false','dedicatedHeicCodec=false','IRIS_26637_HEVC_CAPABILITY_PROOF']:
 assert needle in java, needle
assert 'YUV422' not in java and 'YUV444' not in java
print('PASS 26637 regressions: no-alpha base, P3+sRGB color agreement, gain-map/3-stop authority frozen, hardware 8-bit 4:2:0 behavior unchanged')
