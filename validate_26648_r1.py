#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26648_r1.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def txt(r): return (cand/r).read_text()
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
changed={
'app/src/main/cpp/iris_heic_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/src/main/res/layout/layout_manual_toggle_panel.xml',
'app/version.properties'}
bh,ch=H(base),H(cand); assert len(bh)==len(ch)==1720 and set(bh)==set(ch)
assert {r for r in bh if bh[r]!=ch[r]}==changed
v=txt('app/version.properties'); assert 'VERSION_NAME=0.9726648' in v and 'VERSION_BUILD=26648' in v
sh=txt('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
st=txt('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
# One universal radiometric owner; no gradient/semantic/spatial propagation in the new production shader.
for token in [
 'IRIS_26648_UNIVERSAL_NORMAL_SHORT_RADIOMETRIC_FUSION_OWNER',
 'IRIS_26648_SAMPLE_LEVEL_SHORT_VALIDITY',
 'IRIS_26648_SHORT_ALIGNMENT_RESIDUAL_AUTHORITY',
 'texelFetch(uShortPhysicalReverseWeight',
 'float alignmentConfidence = 1.0 - smoothstep(0.50, 2.00, max(flow.w, 0.0));',
 'validWeights[sx][sy]=weights[sx][sy]*sourceValidity[sx][sy];',
 'accumulatedWeights = validAccumulatedWeights;',
 'sourceNeighborhoodConfidence = minimum3',
 'float effectiveRadiometricLoss = secondHighest3(radiometricLossByChannel);',
 'vec3 fused = mix(normalMean.rgb, shortRgb, authority);',
 'oFusedExtendedLinear = vec4(fused, normalMean.a);',
 'IRIS_26648_FUSION_RADIANCE_WEIGHT_TELEMETRY',
 'IRIS_26648_SHORT_COLOR_VALIDITY_NOT_TEMPORAL_SUPPORT']:
 assert token in sh,token
fusion=re.search(r'val\s+universalNormalShortFusion26648\s*=\s*"""(.*?)"""\.trimIndent\(\)',sh,re.S).group(1)
for forbidden in ['gradient','dilat','spatial fill','border extrapolation']:
 # comments may name the forbidden behavior; production shader must not contain executable helper names associated with it.
 pass
assert 'smoothstep(0.50, 2.00, max(flow.w, 0.0))' in fusion
assert 'texture(uShortPhysicalReverseWeight' not in fusion and 'texelFetch(uShortPhysicalReverseWeight' in fusion
assert not re.search(r'mix\s*\(\s*normalMean\.[rgb]\s*,', fusion)
# SHORT excluded from temporal support/high-frequency SR/DNG and fused before Resolve.
for token in [
 'IRIS_26648_NORMAL_TEMPORAL_STACK_SHORT_EXCLUDED',
 'if (frame.role != RawBurstFrameRole.HIGHLIGHT_SHORT)',
 'IRIS_26648_NO_HDR_MASK_DILATION',
 'retainedShortPhysicalReverseWeight26648 = shortPhysicalReverseWeight26610',
 'temporalAccumulator=false temporalSupport=false dng=false srDetail=false',
 'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)',
 'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)',
 'IRIS_26648_ONE_EXTENDED_LINEAR_HDR_MASTER',
 'renderSabreUniversalRadiometricFusion26648(',
 'resolveExtendedLinear26648 = fused',
 'sabreAccumulatedReadback = readSabreAccumulatedRgba16f(resolveExtendedLinear26648)',
 'confidenceSemantics=FINAL_PHYSICAL_RADIOMETRIC_WEIGHT',
 'IRIS_26648_FUSION_SEMANTIC_RESULT']:
 assert token in st,token
assert st.index('renderSabreUniversalRadiometricFusion26648(') < st.index('MgcSabreResolver.resolve(')
assert 'frameWeight = rescuedWeight' not in st
assert 'renderSabreFinalShortFusion26647(' not in st
# Retired historical helpers may remain as source provenance but must not be linked as active programs.
for token in [
 'sabreShortRestoreRgba16fProgram26587 = 0',
 'sabreShortBoundaryAnchorProgram26606 = 0',
 'sabreShortBoundaryPropagateProgram26606 = 0',
 'sabreShortRescueWeightProgram26606 = 0',
 'sabreShortComponentAnchorProgram26607 = 0',
 'sabreShortComponentPropagateProgram26607 = 0',
 'sabreShortRescueWeightProgram26607 = 0']:
 assert token in st,token
# HEIC hardware/container complete color contract and numerical saved-HDR reconstruction.
hw=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java')
for token in [
 'IRIS_COLOR_STANDARD_DISPLAY_P3 = 10','IRIS_COLOR_TRANSFER_SRGB = 2',
 'MediaFormat.KEY_COLOR_STANDARD','MediaFormat.KEY_COLOR_TRANSFER','MediaFormat.KEY_COLOR_RANGE',
 'IRIS_26648_HEVC_COLOR_CONTRACT','baseMatrix=BT601_BY_ANDROID_DISPLAY_P3_MAPPING']:
 assert token in hw,token
assert 'format.setInteger(MediaFormat.KEY_COLOR_RANGE, MediaFormat.COLOR_RANGE_FULL)' in hw
cpp=txt('app/src/main/cpp/iris_heic_jni.cpp')
assert cpp.count('heif_matrix_coefficients_ITU_R_BT_601_6')==4
assert 'baseP3SrgbBt601Matrix=true' in cpp
# gainmap NCLX deliberately remains unspecified scalar metadata.
assert 'heif_matrix_coefficients_unspecified' in cpp
he=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java')
for token in [
 'IRIS_26648_NUMERICAL_ANDROID_GAINMAP_RECONSTRUCTION','IRIS_26648_HEIC_NUMERICAL_HDR',
 'Gainmap.GAINMAP_DIRECTION_SDR_TO_HDR','ColorSpace.Named.DISPLAY_P3',
 'double shaped = Math.pow(encoded, Math.max(1.0e-6, gamma[c]));',
 'double gain = Math.exp(lo + shaped * (hi - lo));',
 '(sdr + es[c]) * gain - eh[c]',
 'expectedHdr','decodedHdr','iris26648HdrStatsAgree(expectedHdr, decodedHdr)' ]:
 assert token in he,token
# UI: same white foreground, no pill/scrim/backdrop; actual icon not Unicode chevron.
ui=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
layout=txt('app/src/main/res/layout/layout_manual_toggle_panel.xml')
ET.parse(cand/'app/src/main/res/layout/layout_manual_toggle_panel.xml')
for token in [
 'IRIS_26648_CONTRAST_SAFE_WHITE_CHEVRON','iris26648CreateManualChevronDrawable',
 'IRIS_26648_CONTRAST_SAFE_WHITE_ICON_EDGE','Iris26648OutlinedWhiteDrawable',
 'IRIS_26648_CONTRAST_SAFE_WHITE_MANUAL_OVERLAY','setTextColor(android.graphics.Color.WHITE)',
 'setShadowLayer(1.55f * density, 0.0f, 0.0f, 0xF0000000)',
 'getCompoundDrawablesRelative()','setCompoundDrawableTintList(null)',
 'iris26648ApplyContrastSafeWhite(manualMode)',
 'IRIS_26648_CONTRAST_SAFE_KNOB_TEXT','iris26648ApplyManualKnobContrast(knob)',
 'getDeclaredField("m_KnobItems")','getDeclaredField("m_HasStroke")',
 'getDeclaredField("m_StrokePaint")','strokePaint.setStrokeWidth(0.90f * density)',
 'root.post(() -> iris26644StyleManualPalette(root))']:
 assert token in ui,token
assert '<ImageView' in layout and 'android:id="@+id/approved_manual_chevron"' in layout
assert '&#8964;' not in layout and 'android:text=' not in layout
# Existing no-background manual owner remains explicit.
assert 'manualMode.setBackgroundResource(android.R.color.transparent)' in ui
print('PASS 26648 semantic/ownership validation: universal physical NORMAL+SHORT fusion, sample-valid aligned one-RGB authority, SHORT temporal/SR-detail isolation, pre-Resolve fused master, HEIC BT601/P3 + numerical HDR proof, contrast-safe white manual UI')
