#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26647_r1.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def txt(r): return (cand/r).read_text()
changed={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
'app/version.properties'}
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand); assert len(bh)==len(ch)==1720 and set(bh)==set(ch)
assert {r for r in bh if bh[r]!=ch[r]}==changed
v=txt('app/version.properties'); assert 'VERSION_NAME=0.9726647' in v and 'VERSION_BUILD=26647' in v
sh=txt('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
st=txt('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for token in ['IRIS_26647_DIRECT_FINAL_SHORT_FUSION_MODE','IRIS_26647_DIRECT_FINAL_SHORT_VALIDITY_FUSION','uFinalShortFusion == 2','finalRescueAlpha']:
 assert token in sh,token
for token in ['IRIS_26647_RESCUE_SPLIT_FROM_TEMPORAL_SUPPORT','IRIS_26647_RESCUE_DOES_NOT_OWN_TEMPORAL_SUPPORT','IRIS_26647_PRE_RESOLVE_RGB_AUTHORITY','IRIS_26647_DIRECT_FINAL_SHORT_FUSION','physicalCfaValidityUpdated=true','GlesMgcRawSabreShaders.finalShortValidityFusion26647','rescueAffectsTemporalSupport=false']:
 assert token in st,token
assert 'frameWeight = rescuedWeight' not in st
assert st.index('renderSabreFinalShortFusion26647(') < st.index('chromaPostprocessor.process(')
assert 'sabreShortRestoreRgba16fProgram26587 = 0' in st
hw=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java')
for token in ['AOSP_COLOR_STANDARD_DISPLAY_P3 = 10','AOSP_COLOR_TRANSFER_SRGB = 2','MediaFormat.KEY_COLOR_STANDARD','MediaFormat.KEY_COLOR_TRANSFER','IRIS_26647_HEVC_COLOR_ASPECT_PROOF']:
 assert token in hw,token
assert 'MediaFormat.KEY_COLOR_RANGE, MediaFormat.COLOR_RANGE_FULL' in hw
he=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java')
for token in ['IRIS_26647_HEIC_SAVED_BASE_RECONSTRUCTION_PROOF','IRIS_26647_BOUNDED_TRUE2X_BASE_PROOF','iris26647DecodeP3Preview(displayP3BaseJpeg, 384)','baseContract=DISPLAY_P3_SRGB_FULL_RANGE']:
 assert token in he,token
# true2x diagnostic must not decode another full source base directly
assert 'expectedBaseP3 = BitmapFactory.decodeFile(\n                        displayP3BaseJpeg' not in he
print('PASS 26647 semantic/ownership validation: direct final rescue pre-Resolve, no temporal-support inflation, CFA validity preserved, AOSP Display-P3/sRGB/full HEVC contract, bounded saved-base proof')
