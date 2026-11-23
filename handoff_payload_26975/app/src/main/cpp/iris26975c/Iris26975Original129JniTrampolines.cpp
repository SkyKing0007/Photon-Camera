// Photon 26975 V3 Experiment C ONLY: original pinned 1.29.0 native JNI name bridge.
// Source generation is mechanical; it changes no donor algorithm or CPU buffer mathematics.
// Every trampoline is a tail branch, preserving x0..x7, v0..v7, stack and x30.
// Fail closed on missing native entry, never fall back to A/B JNI.
#if !defined(__aarch64__)
#error "Pinned bjzhou 1.29.0 JNI bridge is ARM64 only"
#endif
// Deliberately self-contained native bridge: ABI declarations are identical
// to JNI and Android libdl, and allow native-object syntax checking off-device.
extern "C" void* dlopen(const char*, int);
extern "C" void* dlsym(void*, const char*);

extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_0 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_1 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_2 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_3 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_4 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_5 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_6 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_7 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_8 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_9 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_10 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_11 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_12 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_13 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_14 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_15 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_16 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_17 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_18 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_19 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_20 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_21 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_22 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_23 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_24 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_25 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_26 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_27 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_28 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_29 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_30 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_31 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_32 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_33 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_34 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_35 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_36 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_37 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_38 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_39 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_40 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_41 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_42 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_43 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_44 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_45 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_46 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_47 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_48 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_49 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_50 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_51 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_52 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_53 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_54 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_55 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_56 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_57 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_58 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_59 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_60 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_61 = nullptr; }
extern "C" { __attribute__((visibility("hidden"))) void* iris26975_native_target_62 = nullptr; }

extern "C" __attribute__((visibility("default"))) int JNI_OnLoad(void*, void*) {
    void* donor = dlopen("libiris26972c129.so", 2 /* RTLD_NOW */);
    if (!donor) return -1;
    iris26975_native_target_0 = dlsym(donor, "Java_com_hinnka_mycamera_gallery_Jpeg444ExportEncoder_encodeGainmapNative");
    if (!iris26975_native_target_0) return -1;
    iris26975_native_target_1 = dlsym(donor, "Java_com_hinnka_mycamera_gallery_Jpeg444ExportEncoder_isJpegRNative");
    if (!iris26975_native_target_1) return -1;
    iris26975_native_target_2 = dlsym(donor, "Java_com_hinnka_mycamera_gallery_Jpeg444ExportEncoder_packageJpegRNative");
    if (!iris26975_native_target_2) return -1;
    iris26975_native_target_3 = dlsym(donor, "Java_com_hinnka_mycamera_gallery_Jpeg444ExportEncoder_writeNative");
    if (!iris26975_native_target_3) return -1;
    iris26975_native_target_4 = dlsym(donor, "Java_com_hinnka_mycamera_lut_LutProcessor_resampleLutNative");
    if (!iris26975_native_target_4) return -1;
    iris26975_native_target_5 = dlsym(donor, "Java_com_hinnka_mycamera_lut_LutProcessor_resampleSizeNative");
    if (!iris26975_native_target_5) return -1;
    iris26975_native_target_6 = dlsym(donor, "Java_com_hinnka_mycamera_ml_AiDenoiser_readTileNative");
    if (!iris26975_native_target_6) return -1;
    iris26975_native_target_7 = dlsym(donor, "Java_com_hinnka_mycamera_ml_AiDenoiser_writeTileNative");
    if (!iris26975_native_target_7) return -1;
    iris26975_native_target_8 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesGpuTimerQuery_begin");
    if (!iris26975_native_target_8) return -1;
    iris26975_native_target_9 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesGpuTimerQuery_counterBits");
    if (!iris26975_native_target_9) return -1;
    iris26975_native_target_10 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesGpuTimerQuery_delete");
    if (!iris26975_native_target_10) return -1;
    iris26975_native_target_11 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesGpuTimerQuery_end");
    if (!iris26975_native_target_11) return -1;
    iris26975_native_target_12 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesGpuTimerQuery_isDisjoint");
    if (!iris26975_native_target_12) return -1;
    iris26975_native_target_13 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesGpuTimerQuery_poll");
    if (!iris26975_native_target_13) return -1;
    iris26975_native_target_14 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesHardwareBufferImage_bind");
    if (!iris26975_native_target_14) return -1;
    iris26975_native_target_15 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesHardwareBufferImage_bind2D");
    if (!iris26975_native_target_15) return -1;
    iris26975_native_target_16 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesHardwareBufferImage_create");
    if (!iris26975_native_target_16) return -1;
    iris26975_native_target_17 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesHardwareBufferImage_destroy");
    if (!iris26975_native_target_17) return -1;
    iris26975_native_target_18 = dlsym(donor, "Java_com_hinnka_mycamera_processor_GlesPixelBufferTransfer_uploadRgba16fPboToTexture");
    if (!iris26975_native_target_18) return -1;
    iris26975_native_target_19 = dlsym(donor, "Java_com_hinnka_mycamera_processor_MgcSpatialStrengthMapGenerator_nativeCompute");
    if (!iris26975_native_target_19) return -1;
    iris26975_native_target_20 = dlsym(donor, "Java_com_hinnka_mycamera_processor_MgcSpatialStrengthMapScaler_nativeScaleBilinearU16");
    if (!iris26975_native_target_20) return -1;
    iris26975_native_target_21 = dlsym(donor, "Java_com_hinnka_mycamera_raw_DcpNativeBridge_parseDcpToJson");
    if (!iris26975_native_target_21) return -1;
    iris26975_native_target_22 = dlsym(donor, "Java_com_hinnka_mycamera_raw_DngHdrNetProfileGainTableNative_nativeEvaluateDisplayLinearLumaGrid");
    if (!iris26975_native_target_22) return -1;
    iris26975_native_target_23 = dlsym(donor, "Java_com_hinnka_mycamera_raw_DngHdrNetProfileGainTableNative_nativeGenerateGains");
    if (!iris26975_native_target_23) return -1;
    iris26975_native_target_24 = dlsym(donor, "Java_com_hinnka_mycamera_raw_DngProfileGainTableValidation_validateGainsNative");
    if (!iris26975_native_target_24) return -1;
    iris26975_native_target_25 = dlsym(donor, "Java_com_hinnka_mycamera_raw_DngRawData_freeNativeBuffer");
    if (!iris26975_native_target_25) return -1;
    iris26975_native_target_26 = dlsym(donor, "Java_com_hinnka_mycamera_raw_MgcFullResolutionDenoise_nativeDenoiseRgba16f");
    if (!iris26975_native_target_26) return -1;
    iris26975_native_target_27 = dlsym(donor, "Java_com_hinnka_mycamera_raw_MgcFullResolutionDenoise_nativeLowFrequencyChromaCorrection");
    if (!iris26975_native_target_27) return -1;
    iris26975_native_target_28 = dlsym(donor, "Java_com_hinnka_mycamera_raw_MgcRaisrUpscale_nativeUpscaleBitmap");
    if (!iris26975_native_target_28) return -1;
    iris26975_native_target_29 = dlsym(donor, "Java_com_hinnka_mycamera_raw_MgcRaisrUpscale_nativeUpscaleTile");
    if (!iris26975_native_target_29) return -1;
    iris26975_native_target_30 = dlsym(donor, "Java_com_hinnka_mycamera_raw_Raw10Unpacker_unpackNative");
    if (!iris26975_native_target_30) return -1;
    iris26975_native_target_31 = dlsym(donor, "Java_com_hinnka_mycamera_raw_Raw10Unpacker_validateHardwareBufferNative");
    if (!iris26975_native_target_31) return -1;
    iris26975_native_target_32 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawDemosaicProcessor_estimateMgcReferenceSignalNative");
    if (!iris26975_native_target_32) return -1;
    iris26975_native_target_33 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawDemosaicProcessor_processDngNative");
    if (!iris26975_native_target_33) return -1;
    iris26975_native_target_34 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawFloatTextureTransfer_nativeUpload");
    if (!iris26975_native_target_34) return -1;
    iris26975_native_target_35 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawLegacyAutoExposureNativeBridge_legacyHdrNetReferencePixels");
    if (!iris26975_native_target_35) return -1;
    iris26975_native_target_36 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureExposureBounds");
    if (!iris26975_native_target_36) return -1;
    iris26975_native_target_37 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureHdrNetPriority");
    if (!iris26975_native_target_37) return -1;
    iris26975_native_target_38 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawLegacyAutoExposureNativeBridge_nativeCreate");
    if (!iris26975_native_target_38) return -1;
    iris26975_native_target_39 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawLegacyAutoExposureNativeBridge_nativeDestroy");
    if (!iris26975_native_target_39) return -1;
    iris26975_native_target_40 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawLegacyAutoExposureNativeBridge_nativeGetResultExposureEv");
    if (!iris26975_native_target_40) return -1;
    iris26975_native_target_41 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawLegacyAutoExposureNativeBridge_nativeNextExposureEv");
    if (!iris26975_native_target_41) return -1;
    iris26975_native_target_42 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawLegacyAutoExposureNativeBridge_nativeSolveSingleGridExposure");
    if (!iris26975_native_target_42) return -1;
    iris26975_native_target_43 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitCandidate");
    if (!iris26975_native_target_43) return -1;
    iris26975_native_target_44 = dlsym(donor, "Java_com_hinnka_mycamera_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitGridCandidate");
    if (!iris26975_native_target_44) return -1;
    iris26975_native_target_45 = dlsym(donor, "Java_com_hinnka_mycamera_raw_SpektrafilmNativeBridge_generate");
    if (!iris26975_native_target_45) return -1;
    iris26975_native_target_46 = dlsym(donor, "Java_com_hinnka_mycamera_raw_fotufilm_FotufilmNativeBridge_buildFrame");
    if (!iris26975_native_target_46) return -1;
    iris26975_native_target_47 = dlsym(donor, "Java_com_hinnka_mycamera_raw_fotufilm_FotufilmNativeBridge_catalogue");
    if (!iris26975_native_target_47) return -1;
    iris26975_native_target_48 = dlsym(donor, "Java_com_hinnka_mycamera_raw_fotufilm_FotufilmNativeBridge_install");
    if (!iris26975_native_target_48) return -1;
    iris26975_native_target_49 = dlsym(donor, "Java_com_hinnka_mycamera_raw_fotufilm_FotufilmNativeBridge_stocks");
    if (!iris26975_native_target_49) return -1;
    iris26975_native_target_50 = dlsym(donor, "Java_com_hinnka_mycamera_stabilization_MgcEisNativeBridge_create");
    if (!iris26975_native_target_50) return -1;
    iris26975_native_target_51 = dlsym(donor, "Java_com_hinnka_mycamera_stabilization_MgcEisNativeBridge_processFrame");
    if (!iris26975_native_target_51) return -1;
    iris26975_native_target_52 = dlsym(donor, "Java_com_hinnka_mycamera_stabilization_MgcEisNativeBridge_processGyro");
    if (!iris26975_native_target_52) return -1;
    iris26975_native_target_53 = dlsym(donor, "Java_com_hinnka_mycamera_stabilization_MgcEisNativeBridge_processLensIntrinsics");
    if (!iris26975_native_target_53) return -1;
    iris26975_native_target_54 = dlsym(donor, "Java_com_hinnka_mycamera_stabilization_MgcEisNativeBridge_processLensOffset");
    if (!iris26975_native_target_54) return -1;
    iris26975_native_target_55 = dlsym(donor, "Java_com_hinnka_mycamera_stabilization_MgcEisNativeBridge_release");
    if (!iris26975_native_target_55) return -1;
    iris26975_native_target_56 = dlsym(donor, "Java_com_hinnka_mycamera_utils_DirectBufferAllocator_allocateNative");
    if (!iris26975_native_target_56) return -1;
    iris26975_native_target_57 = dlsym(donor, "Java_com_hinnka_mycamera_utils_DirectBufferAllocator_freeNative");
    if (!iris26975_native_target_57) return -1;
    iris26975_native_target_58 = dlsym(donor, "Java_com_hinnka_mycamera_utils_DirectBufferPixelPacker_packRgba16fToRgb16");
    if (!iris26975_native_target_58) return -1;
    iris26975_native_target_59 = dlsym(donor, "Java_com_hinnka_mycamera_utils_DirectBufferPixelPacker_unpackRgba16TileToRgb16");
    if (!iris26975_native_target_59) return -1;
    iris26975_native_target_60 = dlsym(donor, "Java_com_hinnka_mycamera_utils_SuperResolutionDngWriter_encodeLosslessJpegNative");
    if (!iris26975_native_target_60) return -1;
    iris26975_native_target_61 = dlsym(donor, "Java_com_hinnka_mycamera_utils_YuvProcessor_processToBitmap");
    if (!iris26975_native_target_61) return -1;
    iris26975_native_target_62 = dlsym(donor, "Java_com_hinnka_mycamera_utils_YuvProcessor_processToFile");
    if (!iris26975_native_target_62) return -1;
    return 0x00010006; /* JNI_VERSION_1_6 */
}
// Targets are 8-byte aligned. Each thunk is a naked ARM64 branch to the original JNI
// preserving the JNIEnv*/receiver pair and ALL variable JNI method arguments.
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_encodeGainmapNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_encodeGainmapNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_encodeGainmapNative:
    adrp x16, iris26975_native_target_0
    ldr x16, [x16, :lo12:iris26975_native_target_0]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_encodeGainmapNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_encodeGainmapNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_isJpegRNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_isJpegRNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_isJpegRNative:
    adrp x16, iris26975_native_target_1
    ldr x16, [x16, :lo12:iris26975_native_target_1]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_isJpegRNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_isJpegRNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_packageJpegRNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_packageJpegRNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_packageJpegRNative:
    adrp x16, iris26975_native_target_2
    ldr x16, [x16, :lo12:iris26975_native_target_2]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_packageJpegRNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_packageJpegRNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_writeNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_writeNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_writeNative:
    adrp x16, iris26975_native_target_3
    ldr x16, [x16, :lo12:iris26975_native_target_3]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_writeNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_gallery_Jpeg444ExportEncoder_writeNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_lut_LutProcessor_resampleLutNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_lut_LutProcessor_resampleLutNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_lut_LutProcessor_resampleLutNative:
    adrp x16, iris26975_native_target_4
    ldr x16, [x16, :lo12:iris26975_native_target_4]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_lut_LutProcessor_resampleLutNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_lut_LutProcessor_resampleLutNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_lut_LutProcessor_resampleSizeNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_lut_LutProcessor_resampleSizeNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_lut_LutProcessor_resampleSizeNative:
    adrp x16, iris26975_native_target_5
    ldr x16, [x16, :lo12:iris26975_native_target_5]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_lut_LutProcessor_resampleSizeNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_lut_LutProcessor_resampleSizeNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_ml_AiDenoiser_readTileNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_ml_AiDenoiser_readTileNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_ml_AiDenoiser_readTileNative:
    adrp x16, iris26975_native_target_6
    ldr x16, [x16, :lo12:iris26975_native_target_6]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_ml_AiDenoiser_readTileNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_ml_AiDenoiser_readTileNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_ml_AiDenoiser_writeTileNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_ml_AiDenoiser_writeTileNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_ml_AiDenoiser_writeTileNative:
    adrp x16, iris26975_native_target_7
    ldr x16, [x16, :lo12:iris26975_native_target_7]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_ml_AiDenoiser_writeTileNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_ml_AiDenoiser_writeTileNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_begin
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_begin, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_begin:
    adrp x16, iris26975_native_target_8
    ldr x16, [x16, :lo12:iris26975_native_target_8]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_begin, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_begin
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_counterBits
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_counterBits, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_counterBits:
    adrp x16, iris26975_native_target_9
    ldr x16, [x16, :lo12:iris26975_native_target_9]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_counterBits, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_counterBits
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_delete
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_delete, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_delete:
    adrp x16, iris26975_native_target_10
    ldr x16, [x16, :lo12:iris26975_native_target_10]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_delete, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_delete
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_end
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_end, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_end:
    adrp x16, iris26975_native_target_11
    ldr x16, [x16, :lo12:iris26975_native_target_11]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_end, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_end
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_isDisjoint
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_isDisjoint, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_isDisjoint:
    adrp x16, iris26975_native_target_12
    ldr x16, [x16, :lo12:iris26975_native_target_12]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_isDisjoint, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_isDisjoint
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_poll
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_poll, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_poll:
    adrp x16, iris26975_native_target_13
    ldr x16, [x16, :lo12:iris26975_native_target_13]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_poll, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesGpuTimerQuery_poll
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_bind
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_bind, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_bind:
    adrp x16, iris26975_native_target_14
    ldr x16, [x16, :lo12:iris26975_native_target_14]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_bind, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_bind
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_bind2D
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_bind2D, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_bind2D:
    adrp x16, iris26975_native_target_15
    ldr x16, [x16, :lo12:iris26975_native_target_15]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_bind2D, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_bind2D
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_create
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_create, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_create:
    adrp x16, iris26975_native_target_16
    ldr x16, [x16, :lo12:iris26975_native_target_16]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_create, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_create
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_destroy
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_destroy, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_destroy:
    adrp x16, iris26975_native_target_17
    ldr x16, [x16, :lo12:iris26975_native_target_17]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_destroy, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesHardwareBufferImage_destroy
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesPixelBufferTransfer_uploadRgba16fPboToTexture
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesPixelBufferTransfer_uploadRgba16fPboToTexture, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesPixelBufferTransfer_uploadRgba16fPboToTexture:
    adrp x16, iris26975_native_target_18
    ldr x16, [x16, :lo12:iris26975_native_target_18]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesPixelBufferTransfer_uploadRgba16fPboToTexture, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_GlesPixelBufferTransfer_uploadRgba16fPboToTexture
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_MgcSpatialStrengthMapGenerator_nativeCompute
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_MgcSpatialStrengthMapGenerator_nativeCompute, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_MgcSpatialStrengthMapGenerator_nativeCompute:
    adrp x16, iris26975_native_target_19
    ldr x16, [x16, :lo12:iris26975_native_target_19]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_MgcSpatialStrengthMapGenerator_nativeCompute, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_MgcSpatialStrengthMapGenerator_nativeCompute
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_processor_MgcSpatialStrengthMapScaler_nativeScaleBilinearU16
.type Java_com_hinnka_mycamera_processor_experimentc_original129_processor_MgcSpatialStrengthMapScaler_nativeScaleBilinearU16, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_processor_MgcSpatialStrengthMapScaler_nativeScaleBilinearU16:
    adrp x16, iris26975_native_target_20
    ldr x16, [x16, :lo12:iris26975_native_target_20]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_processor_MgcSpatialStrengthMapScaler_nativeScaleBilinearU16, .-Java_com_hinnka_mycamera_processor_experimentc_original129_processor_MgcSpatialStrengthMapScaler_nativeScaleBilinearU16
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DcpNativeBridge_parseDcpToJson
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DcpNativeBridge_parseDcpToJson, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DcpNativeBridge_parseDcpToJson:
    adrp x16, iris26975_native_target_21
    ldr x16, [x16, :lo12:iris26975_native_target_21]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DcpNativeBridge_parseDcpToJson, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DcpNativeBridge_parseDcpToJson
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngHdrNetProfileGainTableNative_nativeEvaluateDisplayLinearLumaGrid
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngHdrNetProfileGainTableNative_nativeEvaluateDisplayLinearLumaGrid, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngHdrNetProfileGainTableNative_nativeEvaluateDisplayLinearLumaGrid:
    adrp x16, iris26975_native_target_22
    ldr x16, [x16, :lo12:iris26975_native_target_22]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngHdrNetProfileGainTableNative_nativeEvaluateDisplayLinearLumaGrid, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngHdrNetProfileGainTableNative_nativeEvaluateDisplayLinearLumaGrid
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngHdrNetProfileGainTableNative_nativeGenerateGains
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngHdrNetProfileGainTableNative_nativeGenerateGains, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngHdrNetProfileGainTableNative_nativeGenerateGains:
    adrp x16, iris26975_native_target_23
    ldr x16, [x16, :lo12:iris26975_native_target_23]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngHdrNetProfileGainTableNative_nativeGenerateGains, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngHdrNetProfileGainTableNative_nativeGenerateGains
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngProfileGainTableValidation_validateGainsNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngProfileGainTableValidation_validateGainsNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngProfileGainTableValidation_validateGainsNative:
    adrp x16, iris26975_native_target_24
    ldr x16, [x16, :lo12:iris26975_native_target_24]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngProfileGainTableValidation_validateGainsNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngProfileGainTableValidation_validateGainsNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngRawData_freeNativeBuffer
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngRawData_freeNativeBuffer, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngRawData_freeNativeBuffer:
    adrp x16, iris26975_native_target_25
    ldr x16, [x16, :lo12:iris26975_native_target_25]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngRawData_freeNativeBuffer, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_DngRawData_freeNativeBuffer
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcFullResolutionDenoise_nativeDenoiseRgba16f
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcFullResolutionDenoise_nativeDenoiseRgba16f, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcFullResolutionDenoise_nativeDenoiseRgba16f:
    adrp x16, iris26975_native_target_26
    ldr x16, [x16, :lo12:iris26975_native_target_26]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcFullResolutionDenoise_nativeDenoiseRgba16f, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcFullResolutionDenoise_nativeDenoiseRgba16f
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcFullResolutionDenoise_nativeLowFrequencyChromaCorrection
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcFullResolutionDenoise_nativeLowFrequencyChromaCorrection, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcFullResolutionDenoise_nativeLowFrequencyChromaCorrection:
    adrp x16, iris26975_native_target_27
    ldr x16, [x16, :lo12:iris26975_native_target_27]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcFullResolutionDenoise_nativeLowFrequencyChromaCorrection, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcFullResolutionDenoise_nativeLowFrequencyChromaCorrection
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcRaisrUpscale_nativeUpscaleBitmap
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcRaisrUpscale_nativeUpscaleBitmap, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcRaisrUpscale_nativeUpscaleBitmap:
    adrp x16, iris26975_native_target_28
    ldr x16, [x16, :lo12:iris26975_native_target_28]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcRaisrUpscale_nativeUpscaleBitmap, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcRaisrUpscale_nativeUpscaleBitmap
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcRaisrUpscale_nativeUpscaleTile
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcRaisrUpscale_nativeUpscaleTile, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcRaisrUpscale_nativeUpscaleTile:
    adrp x16, iris26975_native_target_29
    ldr x16, [x16, :lo12:iris26975_native_target_29]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcRaisrUpscale_nativeUpscaleTile, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_MgcRaisrUpscale_nativeUpscaleTile
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_Raw10Unpacker_unpackNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_Raw10Unpacker_unpackNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_Raw10Unpacker_unpackNative:
    adrp x16, iris26975_native_target_30
    ldr x16, [x16, :lo12:iris26975_native_target_30]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_Raw10Unpacker_unpackNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_Raw10Unpacker_unpackNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_Raw10Unpacker_validateHardwareBufferNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_Raw10Unpacker_validateHardwareBufferNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_Raw10Unpacker_validateHardwareBufferNative:
    adrp x16, iris26975_native_target_31
    ldr x16, [x16, :lo12:iris26975_native_target_31]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_Raw10Unpacker_validateHardwareBufferNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_Raw10Unpacker_validateHardwareBufferNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawDemosaicProcessor_estimateMgcReferenceSignalNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawDemosaicProcessor_estimateMgcReferenceSignalNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawDemosaicProcessor_estimateMgcReferenceSignalNative:
    adrp x16, iris26975_native_target_32
    ldr x16, [x16, :lo12:iris26975_native_target_32]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawDemosaicProcessor_estimateMgcReferenceSignalNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawDemosaicProcessor_estimateMgcReferenceSignalNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawDemosaicProcessor_processDngNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawDemosaicProcessor_processDngNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawDemosaicProcessor_processDngNative:
    adrp x16, iris26975_native_target_33
    ldr x16, [x16, :lo12:iris26975_native_target_33]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawDemosaicProcessor_processDngNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawDemosaicProcessor_processDngNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawFloatTextureTransfer_nativeUpload
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawFloatTextureTransfer_nativeUpload, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawFloatTextureTransfer_nativeUpload:
    adrp x16, iris26975_native_target_34
    ldr x16, [x16, :lo12:iris26975_native_target_34]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawFloatTextureTransfer_nativeUpload, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawFloatTextureTransfer_nativeUpload
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_legacyHdrNetReferencePixels
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_legacyHdrNetReferencePixels, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_legacyHdrNetReferencePixels:
    adrp x16, iris26975_native_target_35
    ldr x16, [x16, :lo12:iris26975_native_target_35]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_legacyHdrNetReferencePixels, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_legacyHdrNetReferencePixels
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureExposureBounds
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureExposureBounds, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureExposureBounds:
    adrp x16, iris26975_native_target_36
    ldr x16, [x16, :lo12:iris26975_native_target_36]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureExposureBounds, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureExposureBounds
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureHdrNetPriority
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureHdrNetPriority, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureHdrNetPriority:
    adrp x16, iris26975_native_target_37
    ldr x16, [x16, :lo12:iris26975_native_target_37]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureHdrNetPriority, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeConfigureHdrNetPriority
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeCreate
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeCreate, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeCreate:
    adrp x16, iris26975_native_target_38
    ldr x16, [x16, :lo12:iris26975_native_target_38]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeCreate, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeCreate
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeDestroy
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeDestroy, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeDestroy:
    adrp x16, iris26975_native_target_39
    ldr x16, [x16, :lo12:iris26975_native_target_39]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeDestroy, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeDestroy
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeGetResultExposureEv
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeGetResultExposureEv, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeGetResultExposureEv:
    adrp x16, iris26975_native_target_40
    ldr x16, [x16, :lo12:iris26975_native_target_40]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeGetResultExposureEv, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeGetResultExposureEv
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeNextExposureEv
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeNextExposureEv, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeNextExposureEv:
    adrp x16, iris26975_native_target_41
    ldr x16, [x16, :lo12:iris26975_native_target_41]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeNextExposureEv, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeNextExposureEv
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSolveSingleGridExposure
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSolveSingleGridExposure, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSolveSingleGridExposure:
    adrp x16, iris26975_native_target_42
    ldr x16, [x16, :lo12:iris26975_native_target_42]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSolveSingleGridExposure, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSolveSingleGridExposure
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitCandidate
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitCandidate, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitCandidate:
    adrp x16, iris26975_native_target_43
    ldr x16, [x16, :lo12:iris26975_native_target_43]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitCandidate, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitCandidate
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitGridCandidate
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitGridCandidate, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitGridCandidate:
    adrp x16, iris26975_native_target_44
    ldr x16, [x16, :lo12:iris26975_native_target_44]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitGridCandidate, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_RawLegacyAutoExposureNativeBridge_nativeSubmitGridCandidate
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_SpektrafilmNativeBridge_generate
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_SpektrafilmNativeBridge_generate, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_SpektrafilmNativeBridge_generate:
    adrp x16, iris26975_native_target_45
    ldr x16, [x16, :lo12:iris26975_native_target_45]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_SpektrafilmNativeBridge_generate, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_SpektrafilmNativeBridge_generate
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_buildFrame
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_buildFrame, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_buildFrame:
    adrp x16, iris26975_native_target_46
    ldr x16, [x16, :lo12:iris26975_native_target_46]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_buildFrame, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_buildFrame
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_catalogue
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_catalogue, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_catalogue:
    adrp x16, iris26975_native_target_47
    ldr x16, [x16, :lo12:iris26975_native_target_47]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_catalogue, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_catalogue
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_install
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_install, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_install:
    adrp x16, iris26975_native_target_48
    ldr x16, [x16, :lo12:iris26975_native_target_48]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_install, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_install
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_stocks
.type Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_stocks, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_stocks:
    adrp x16, iris26975_native_target_49
    ldr x16, [x16, :lo12:iris26975_native_target_49]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_stocks, .-Java_com_hinnka_mycamera_processor_experimentc_original129_raw_fotufilm_FotufilmNativeBridge_stocks
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_create
.type Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_create, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_create:
    adrp x16, iris26975_native_target_50
    ldr x16, [x16, :lo12:iris26975_native_target_50]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_create, .-Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_create
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processFrame
.type Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processFrame, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processFrame:
    adrp x16, iris26975_native_target_51
    ldr x16, [x16, :lo12:iris26975_native_target_51]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processFrame, .-Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processFrame
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processGyro
.type Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processGyro, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processGyro:
    adrp x16, iris26975_native_target_52
    ldr x16, [x16, :lo12:iris26975_native_target_52]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processGyro, .-Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processGyro
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processLensIntrinsics
.type Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processLensIntrinsics, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processLensIntrinsics:
    adrp x16, iris26975_native_target_53
    ldr x16, [x16, :lo12:iris26975_native_target_53]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processLensIntrinsics, .-Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processLensIntrinsics
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processLensOffset
.type Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processLensOffset, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processLensOffset:
    adrp x16, iris26975_native_target_54
    ldr x16, [x16, :lo12:iris26975_native_target_54]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processLensOffset, .-Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_processLensOffset
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_release
.type Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_release, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_release:
    adrp x16, iris26975_native_target_55
    ldr x16, [x16, :lo12:iris26975_native_target_55]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_release, .-Java_com_hinnka_mycamera_processor_experimentc_original129_stabilization_MgcEisNativeBridge_release
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferAllocator_allocateNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferAllocator_allocateNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferAllocator_allocateNative:
    adrp x16, iris26975_native_target_56
    ldr x16, [x16, :lo12:iris26975_native_target_56]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferAllocator_allocateNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferAllocator_allocateNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferAllocator_freeNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferAllocator_freeNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferAllocator_freeNative:
    adrp x16, iris26975_native_target_57
    ldr x16, [x16, :lo12:iris26975_native_target_57]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferAllocator_freeNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferAllocator_freeNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferPixelPacker_packRgba16fToRgb16
.type Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferPixelPacker_packRgba16fToRgb16, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferPixelPacker_packRgba16fToRgb16:
    adrp x16, iris26975_native_target_58
    ldr x16, [x16, :lo12:iris26975_native_target_58]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferPixelPacker_packRgba16fToRgb16, .-Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferPixelPacker_packRgba16fToRgb16
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferPixelPacker_unpackRgba16TileToRgb16
.type Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferPixelPacker_unpackRgba16TileToRgb16, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferPixelPacker_unpackRgba16TileToRgb16:
    adrp x16, iris26975_native_target_59
    ldr x16, [x16, :lo12:iris26975_native_target_59]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferPixelPacker_unpackRgba16TileToRgb16, .-Java_com_hinnka_mycamera_processor_experimentc_original129_utils_DirectBufferPixelPacker_unpackRgba16TileToRgb16
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_utils_SuperResolutionDngWriter_encodeLosslessJpegNative
.type Java_com_hinnka_mycamera_processor_experimentc_original129_utils_SuperResolutionDngWriter_encodeLosslessJpegNative, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_utils_SuperResolutionDngWriter_encodeLosslessJpegNative:
    adrp x16, iris26975_native_target_60
    ldr x16, [x16, :lo12:iris26975_native_target_60]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_utils_SuperResolutionDngWriter_encodeLosslessJpegNative, .-Java_com_hinnka_mycamera_processor_experimentc_original129_utils_SuperResolutionDngWriter_encodeLosslessJpegNative
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_utils_YuvProcessor_processToBitmap
.type Java_com_hinnka_mycamera_processor_experimentc_original129_utils_YuvProcessor_processToBitmap, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_utils_YuvProcessor_processToBitmap:
    adrp x16, iris26975_native_target_61
    ldr x16, [x16, :lo12:iris26975_native_target_61]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_utils_YuvProcessor_processToBitmap, .-Java_com_hinnka_mycamera_processor_experimentc_original129_utils_YuvProcessor_processToBitmap
)ASM");
__asm__(R"ASM(
.text
.p2align 2
.global Java_com_hinnka_mycamera_processor_experimentc_original129_utils_YuvProcessor_processToFile
.type Java_com_hinnka_mycamera_processor_experimentc_original129_utils_YuvProcessor_processToFile, %function
Java_com_hinnka_mycamera_processor_experimentc_original129_utils_YuvProcessor_processToFile:
    adrp x16, iris26975_native_target_62
    ldr x16, [x16, :lo12:iris26975_native_target_62]
    cbz x16, 1f
    br x16
1:
    brk #0
.size Java_com_hinnka_mycamera_processor_experimentc_original129_utils_YuvProcessor_processToFile, .-Java_com_hinnka_mycamera_processor_experimentc_original129_utils_YuvProcessor_processToFile
)ASM");
