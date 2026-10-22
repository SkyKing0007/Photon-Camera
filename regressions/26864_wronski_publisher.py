"""Source-contract regression only: not a replacement for real Kotlin/Java/GLSL/native compilers."""
from pathlib import Path
import sys
assert len(sys.argv)==2, 'usage: regression_26864_wronski_publisher.py app_source_root'
R=Path(sys.argv[1])
s=(R/'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
b=(R/'src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
j=(R/'src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java').read_text()
n=(R/'src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
a=(R/'src/main/cpp/iris26856/amaze/src/AmazeGlVulkanJni.cpp').read_text()
c=(R/'src/main/cpp/CMakeLists.txt').read_text()
checks={
 'true2x_legacy_call_sites_disabled':s.count('= reconstructIris26856BTrue2xTiles(')==0,
 'b_and_ab_native_call_sites':s.count('= reconstructIris26864PinnedWronski2x(')==2,
 'native_wr_callback_owned_by_java':('iris26864NativeWronski2x = if (sabreSuperResEnabled' in b and 'GlesIris26864NativeRawr.run(' in b),
 'native_true2x_requested':('true, rgb2x, clip2x, physicalIdentity' in b),
 'jni_real_entry_exported':('Java_com_hinnka_mycamera_processor_GlesIris26864NativeRawr_nativeExecuteGpu(' in n),
 'jni_entry_compiled_through_amaze':('#include "../../../iris26864/Iris26864JniGpuInteropImpl.inc"' in a and 'src/AmazeGlVulkanJni.cpp' in c),
 'native_runtime_linkage':('target_link_libraries(iris26856amaze PRIVATE iris26864-native)' in c and 'target_link_libraries(iris26864-native PRIVATE raw_gpu_pipeline)' in c),
 'frozen_selected_reference':('it.frameNumber == mgcBase.motionV2FrameNumber' in b and 'it.sensorTimestampNs == referenceTimestamp' in b),
 'legacy_b_burst_noise_bypassed':s.count('!iris26864RealRawrOwnsBurstNoise')>=5,
 'b_only_clip_fails_closed':('26864 B-only true2x requires original selected-reference native clip mask' in b),
 'ab_clip_fails_closed_for_sr':('(sabreSuperResEnabled || localOutputZoom < 1.10f)' in b),
 'selected_ref_clip_applied_both':b.count('IrisTrue2xSrNative.applyFinalNativeClipZoneChromaGuide26836(')>=2,
 'receipt_does_not_claim_clip_consumption':('sensorClipConsumedByIrisHighlightOwner' not in s and 'sensorClipGeneratedForFinalIrisHighlightOwner' in s),
 'strict_no_legacy_true2x_fallback':('checkNotNull(iris26864NativeWronski2x)' in s),
 'real_gl_state_readback':('GL_READ_FRAMEBUFFER_BINDING' in s and 'GL_PIXEL_PACK_BUFFER_BINDING' in s),
}
for name,ok in checks.items():print(('PASS' if ok else 'FAIL'),name)
assert all(checks.values()),'26864 Wronski source regression failed'
print('PASS',len(checks),'source contracts; compilers NOT RUN')
