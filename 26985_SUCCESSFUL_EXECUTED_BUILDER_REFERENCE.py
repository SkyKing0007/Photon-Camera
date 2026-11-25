#!/usr/bin/env python3
"""26985 guarded successor to successful 26984 V2. C-only private RawLens 2.4.20; real compiler gates retained."""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
SHADER_COUNT=151 # exact current 26985 physical required shader inventory; not skip
TMP=R/'.photon_26985_work';OUT=R/'photon_26985_outputs'
ART=TMP/'26984-success.zip';BASE=TMP/'authority_26984';CAND=TMP/'candidate_26985'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=45536386600;COMMIT='83bd1f8ac46fe24245af11efb14c1b8e187b29f8';ART_ID=14987424135
ART_SHA='d2d318009e879e7540dd53c65db22a49de19d78e1c17a526d35c78908b554f23'
TAR_SHA='25ad6c36f536232b24b0f5e4e11abf451c7378c919d52dcbb719634e2ca35082'
BUILDER_SHA='fb223768c134a6cc53e6becd5b6b2ddde358d3646c8939d13945105552bd54c1'
WORKFLOW_SHA='3391c48796155cf8b0e73df125d05f3f81be7cd4b75d6ab6ef3630f899242396'
PRIOR_APK_SHA='71fe83e98a44fa577a700e839f0cdba97f6e9c2ba42592552b9bf417dd743abb'
PRIOR_APK_NAME='IrisCamera-0.9726984-26984-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726985-26985-iris-rawr-debug.apk'
NBASE=2486;NFILES=2649;NCHANGE=175;NADDED=163;NMODIFIED=12;NDELETED=0;NPROTECTED=2474
NATIVE_SHA={
 'lib/arm64-v8a/liblkrpipeline.so':'037a5f62649dcac7034c789c8e7ea2f250ca818d1c1c364e09a59f6897530105',
 'lib/arm64-v8a/libsrpipeline.so':'f87cc70ad12a69345392a4eb73b6ec33739577ce8c39b7a4916180c344f67069',
 'lib/armeabi-v7a/liblkrpipeline.so':'9297eb7c58ca242986bced32bf773dcc8d16c3beaa33c26142b152c585957b03',
 'lib/armeabi-v7a/libsrpipeline.so':'48788035080e66efa63b693e35f0587d2f02e851b818c367f3915b6154b47d68',
}
DONOR_SHA={
 'lib/arm64-v8a/libiris26972c129.so':'a70ba1b1e4e8c856b07c828bef4141d0097d19013a49f77c1f59e41ee0a52cae',
 'lib/arm64-v8a/libi72.so':'ab0698a4a7006564e22447402468a9e1ca349a9017180bc7767c4feec58e0331',
}
FILES=['26984_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py', '26984_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml', '26985_ADDED_RUNTIME_PATHS.txt', '26985_AUTHORITY_AND_SCOPE.json', '26985_BASE_26984_FULL_APP.sha256', '26985_CHANGED_RUNTIME_ALLOWLIST.txt', '26985_COMMIT_MESSAGE.txt', '26985_CON_SHADER_INVENTORY.json', '26985_DELETED_RUNTIME_PATHS.txt', '26985_EXPECTED_ACTION_EXECUTABLES.txt', '26985_EXPECTED_FULL_APP.sha256', '26985_FORWARD_FULLINDEX.patch', '26985_LOCAL_VERIFICATION.txt', '26985_MODIFIED_ORIGINAL_PATHS.txt', '26985_NATIVE_SHADER_INVENTORY.json', '26985_PROTECTED_SOURCE.sha256', '26985_ROLLBACK_FULLINDEX.patch', '26985_STAGE_1_UPLOAD_PATHS.txt', '26985_STAGE_2_UPLOAD_PATHS.txt', '26985_STAGE_3_UPLOAD_PATHS.txt', '26985_V6_CURRENT_SHADER_INVENTORY.json', '26985_hdr_donor_provenance.json', '26985_host_fixtures/Full50Test.kt', '26985_host_fixtures/HdrTest.kt', '26985_host_fixtures/ParseJava.java', '26985_host_fixtures/WriterTest.kt', '26985_host_fixtures/stubs/Build.kt', '26985_host_fixtures/stubs/ExifInterface.kt', '26985_host_fixtures/stubs/Location.kt', '26985_host_fixtures/update_stability.cpp', '26985_native_donor_provenance.json', '26985_post_copy_records.json', '26985_writer_donor_provenance.json', 'README_PHOTON_26985.md', 'build_26985_incremental.py', 'compile_26985_con_shaders.sh', 'compile_26985_shaders.sh', 'test_26985_latest_preflight.py', 'test_26985_native_host.py', 'test_26985_patches.py', 'test_26985_predecessor_settings.py', 'test_26985_sealed_negatives.py', 'test_26985_source.py', 'test_26985_workflow_refs.py', 'verify_26985_con_glsl.py', 'verify_26985_native_glsl.py', 'verify_26985_v6_current_glsl.py']
ALLOWED_MODIFIED=['app/src/main/cpp/CMakeLists.txt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnFrozenRawIngress.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnGpuMerge.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnLkrBridge.java', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnMotionIngress.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnPipeline.kt', 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/Iris26983COnBatchPublication.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/Iris26983COnCapturePreparation.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/Iris26983COnPhotoPublication.java', 'app/version.properties']
ALLOWED_ADDED=['app/src/main/cpp/iris26985c_lkr2420/LICENSE', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/LICENSE', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/README.rawlens.md', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/UPSTREAM.json', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/miniz.LICENSE', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/rawlens.patch', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/td_internal.h', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tiny_dng_ljpeg92_v2.c', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tiny_dng_ljpeg92_v2.h', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tinydng.h', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tinydng_api.c', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tinydng_codec.c', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tinydng_dng.c', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tinydng_io.c', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tinydng_psd.c', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tinydng_psd_write.c', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tinydng_tiff.c', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/deps/tinydng/tinydng_write.c', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/raw_dng_stream.h', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/tinydng_jni.cpp', 'app/src/main/cpp/iris26985c_lkr2420/app/src/main/cpp/wavelet/noise_model.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/LICENSE', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/CMakeLists.txt', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_adapter.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_api.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_blocksearch.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_blocksearch.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_finish.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_full.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_full.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_gpu.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_gpu.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_gpulk.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_gpulk.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_host.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_host.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_image.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_image.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_jni.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_lfc.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_lfc.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_mhc.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_mhc.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_pack.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_parallel.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_prior.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_prior.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_resample.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_sharpness.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_solver.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_solver.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_spv.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_tuning.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/adj.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/adj_wg.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/axn_apply.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/canc_apply.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/cdupd.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/dln_apply.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/edgeshift.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/fin.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/gcf_apply.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/gstats.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/hyb.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/jac.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/jacblk.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/le_apply.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/le_blur.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/le_tensor.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lite_common.glsl', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkfit.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/README.md', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/dct_x.glsl', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/dct_x_old.glsl', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/dct_x_u.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/dct_x_v.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/dct_x_y.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/dct_xo_u.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/dct_xo_v.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/dct_xo_y.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/dct_yuv.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/guide_stats.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/lkr_common.glsl', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/resid.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/weight_guide.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/weight_min.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/weight_minh.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/weight_t.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/weight_td.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/weight_tdet.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/weight_th.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/lkr/weight_tv.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/prior_conv.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/rcd_start.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/resid.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/solveblk.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/wavg.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/werr.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/wguide.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/wminh.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/wminv.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/wvalid.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/shaders/zupd.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/resources/prior/prior_fb.bin', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/resources/prior/prior_v2.bin', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/CMakeLists.txt', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/align.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/align_wg.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/ca_warp.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/corr.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/corr_argmin_wg.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/corr_direct.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/corr_l2_fused.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/demosaic.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/divide.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/fft.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/flow_pick.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/gat.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/grad.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/grey_fft.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/grey_fir.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/ica.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/ica_wg.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/kernels.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/merge_accumulate.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/merge_polynomial.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/merge_splat.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/merge_twoband.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/noise_acc.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/noise_even.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/passthrough.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/pyr_down.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/rob_feather.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/robustness.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/twoband_dct.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/twoband_resolve.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/shaders/twoband_tensor.comp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/srp_context.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/srp_context.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/srp_dispatch.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/srp_dng.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/srp_dng.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/srp_fft.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/srp_fft.h', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/srp_jni.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/srp_pipeline.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/sr-pipeline/src/main/cpp/srp_pipeline.h', 'app/src/main/java/com/hinnka/mycamera/processor/Iris26985CLinearOutput.kt', 'app/src/main/java/com/hinnka/mycamera/processor/Iris26985CLkrNative.java', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/BayerPattern.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/DngExifDirectory.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/DngNoiseProfile.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/GpsLocation.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/HdrPlusSceneNoise.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/Iris26985CHdrAuto.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/LensShadingModel.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/LinearRgbDngWriter.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/LkrHdrDecision.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/LkrLensShading.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/RawFrameMetadata.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/ShardWorkers.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/TiffFields.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/lkr2420/TinyDngImageWriter.kt']

def fail(msg):raise RuntimeError('26985 BLOCKED: '+str(msg))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse(path):
 d={}
 for line in path.read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad manifest '+str(path))
  if not re.fullmatch('[0-9a-f]{64}',h) or not p.startswith('app/') or '..' in pathlib.PurePosixPath(p).parts or p in d:fail('malformed/duplicate manifest '+p)
  d[p]=h
 return d
def scan(root):
 src=root/'app/src';required=[root/'app/build.gradle',root/'app/version.properties']
 if not src.is_dir() or not all(x.is_file() for x in required):fail('missing complete app/source/Gradle '+str(root))
 d={}
 for p in [*src.rglob('*'),*required]:
  if p.is_symlink():fail('source symlink '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 return d
def exact(root,file,label):
 want=parse(R/file);got=scan(root)
 if got!=want:fail(label+f' missing={sorted(set(want)-set(got))[:8]} extra={sorted(set(got)-set(want))[:8]} mismatched={[p for p in want.keys()&got.keys() if want[p]!=got[p]][:8]}')
 print('PASS '+label+f': {len(got)} physical files')
 return got

def scope():
 a=parse(R/'26985_BASE_26984_FULL_APP.sha256');b=parse(R/'26985_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26985_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26985_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 modified=set((R/'26985_MODIFIED_ORIGINAL_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26985_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(a),len(b),len(changed),len(added),len(modified),len(deleted))!=(NBASE,NFILES,NCHANGE,NADDED,NMODIFIED,NDELETED):fail('count/protected source regression')
 if changed!=added|modified or added&set(a) or modified-set(a) or set(b)!=(set(a)|added) or deleted:fail('unexpected runtime change/deletion')
 if {p for p in set(a)&set(b) if a[p]!=b[p]}!=modified:fail('original source edits outside allowlist')
 protected={p:h for p,h in a.items() if p not in changed}
 if len(protected)!=NPROTECTED or protected!=parse(R/'26985_PROTECTED_SOURCE.sha256'):fail('protected source failed')
 if sha(R/'26984_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA or sha(R/'26984_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py')!=BUILDER_SHA:fail('26984 actual executed reference changed')
 if (R/'handoff_payload_26985/app/version.properties').read_text()!='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726985\nVERSION_BUILD=26985\n':fail('26985 version not exact')
 allowed_modified=set(json.loads((R/'26985_AUTHORITY_AND_SCOPE.json').read_text())['allowed_modified_exact'])
 if allowed_modified!=modified:fail('changed original paths not explicit')
 if modified!=set(ALLOWED_MODIFIED) or added!=set(ALLOWED_ADDED):fail('new scope not exact')
 if a['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']!=b['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']:fail('A/B gallery changed')
 return changed,a,b

def seal():
 changed,a,b=scope();wf='.github/workflows/build-26985-change-aware.yml';trigger='TRIGGER_26985.txt'
 expect=set(FILES)|{wf,trigger}|{'handoff_payload_26985/'+p for p in changed}
 sealed={}
 for line in (R/'26985_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad handoff hash seal')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered handoff file '+p)
  sealed[p]=h
 if set(sealed)!=expect:fail('missing/extra handoff file set '+str(sorted(set(sealed)^expect)[:10]))
 stages=[(R/f'26985_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((expect|{'26985_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three upload stages not strict')
 payload=R/'handoff_payload_26985'
 if {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}!=changed:fail('payload missing/extra')
 for p in changed:
  if sha(payload/p)!=b[p]:fail('source input tampering '+p)
 if sha(R/'.github/workflows/build-26985-change-aware.yml')!=sealed[wf]:fail('workflow after seal changed')
 subprocess.run([sys.executable,'-S','test_26985_workflow_refs.py'],cwd=R,check=True)
 print(f'PASS 26985 three-stage SHA seal, {NPROTECTED} protected, {NCHANGE} source delta')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions credentials/target branch unavailable')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26984 Actions run not successful/exact')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (RUN,None):fail('26984 artifact identity/published digest')
 TMP.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded successful 26984 ZIP mismatch')
 print('PASS exact successful 26984 Actions artifact fetched')

def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26984 ZIP inaccessible or wrong hash')
 return zipfile.ZipFile(ART)
def safe_extract_tar(data,dest):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   path=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not path.parts or path.parts[0]!='app' or path.is_absolute() or '..' in path.parts or m.issym() or m.islnk():fail('unsafe 26984 compiled TAR entry '+m.name)
  t.extractall(dest,filter='data')

def recover():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('26984 ZIP CRC invalid')
  def get(name):
   p='photon_26984_outputs/'+name
   if p not in z.namelist():fail('26984 successful compiled receipt missing '+p)
   return z.read(p)
  src=get('26984_candidate_app_source.tar.gz')
  if hashlib.sha256(src).hexdigest()!=TAR_SHA or get('26984_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26984_candidate_app_source.tar.gz\n'.encode():fail('26984 actual compiled TAR mismatch')
  if get('26984_EXPECTED_FULL_APP.sha256')!=(R/'26985_BASE_26984_FULL_APP.sha256').read_bytes() or get('26984_PREBUILD_SEALED_APP.sha256')!=(R/'26985_BASE_26984_FULL_APP.sha256').read_bytes():fail('compiled source manifest authority differs')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26984_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26984_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('successful executed builder not pinned')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26984-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26984_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('successful executed workflow not pinned')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26984_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('successful 26984 APK identity')
  identity=get('26984_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in identity or 'github_run_id='+str(RUN) not in identity:fail('26984 Actions job identity')
  compiler=get('26984_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26984 compiler proof absent: '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26984_REAL_GRADLE_TASKS.txt').decode():fail('26984 predecessor Gradle task absent: '+task)
  safe_extract_tar(src,BASE)
 exact(BASE,'26985_BASE_26984_FULL_APP.sha256','actual successful 26984 compiled source')
 shutil.copytree(BASE,CAND)
 changed,_,b=scope()
 for p in sorted(changed):
  dest=CAND/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26985'/p,dest)
 exact(CAND,'26985_EXPECTED_FULL_APP.sha256','exact 26985 isolated candidate')
 print('PASS actual 26984 compiled authority and isolated 26985 candidate recovered')

def restore_live(root):
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('live checkout missing real Gradle')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(root/'app/src',R/'app/src')
 shutil.copyfile(root/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(root/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')

def prepare_base():
 # Single latest compiled runtime authority. No previous source reconstruction.
 recover();restore_live(BASE)
 exact(R,'26985_BASE_26984_FULL_APP.sha256','actual 26984 live predecessor restored')
 subprocess.run([sys.executable,'-S','test_26985_latest_preflight.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26985_predecessor_settings.py',str(BASE),str(CAND)],cwd=R,check=True)
 OUT.mkdir(parents=True,exist_ok=True)
 changed,_,_=scope()
 (OUT/'26985_SOURCE_SCOPE.txt').write_text(f'26984 V2 Actions={RUN} commit={COMMIT} artifact={ART_ID} artifact_zip_sha={ART_SHA} actual_compiled_source_tar_sha={TAR_SHA}\nactual_runner_sha={BUILDER_SHA} actual_workflow_sha={WORKFLOW_SHA} prior_apk_sha={PRIOR_APK_SHA}\nbase={NBASE} candidate={NFILES} changes={NCHANGE} modified={NMODIFIED} added={NADDED} protected={NPROTECTED} deleted={NDELETED}\n'+''.join(p+'\n' for p in sorted(changed)))
 print('PASS latest-only 26984 V2 authority, sparse historical fixtures and predecessor settings and source tests')

def install():
 seal();exact(BASE,'26985_BASE_26984_FULL_APP.sha256','26984 baseline before install')
 exact(CAND,'26985_EXPECTED_FULL_APP.sha256','26985 frozen candidate before install')
 old=OUT/'26984_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 # Historical 26904 checks have been run; require predecessor successful Actions compiler receipt too.
 with prior_zip() as z:
  source=z.read('photon_26984_outputs/26984_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS actual 26974 24/24 C GLES' not in source or 'PASS inherited historical 24/24 and actual current 151/151 26984 donor/Iris C shader compilation' not in source:fail('26984 real pinned GLSL/SPIR-V receipt missing')
 (OUT/'26984_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt').write_text(source)
 with prior_zip() as z:
  con=z.read('photon_26984_outputs/26984_CON_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS 26984 C ON 13/13 static shader stages real GLSL/SPIR-V opt/val' not in con:fail('26984 real C ON shader proof absent')
 (OUT/'26984_SUCCESSFUL_CON_REAL_GLSL_SPIRV_COMPILER.txt').write_text(con)
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copyfile(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'26985_EXPECTED_FULL_APP.sha256','live installed 26985 SHA source')
 print('PASS installed exact 26985 C private RawLens 2.4.20 source; production unapproved')

def regress():
 seal();exact(R,'26985_EXPECTED_FULL_APP.sha256','26985 live protected runtime')
 subprocess.run([sys.executable,'-S','test_26985_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26982_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26985_predecessor_settings.py',str(BASE),str(R)],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26981_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26979_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26978_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26977_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26976_capture_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_gallery_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26985_v6_current_glsl.py','--audit'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26985_native_glsl.py','--audit'],cwd=R,check=True)
 print('PASS live independent C exposure optimizer, exact frame replacement, tuning, protected A/B source invariance')

def stage_native():
 seal()
 with prior_zip() as z:
  with zipfile.ZipFile(io.BytesIO(z.read(PRIOR_APK_NAME))) as apk:
   if apk.testzip():fail('26984 published APK CRC')
   for p,want in NATIVE_SHA.items():
    data=apk.read(p)
    if hashlib.sha256(data).hexdigest()!=want:fail('successful native ABI hash regression '+p)
    dest=R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    if sha(dest)!=want:fail('staged native binary differs '+p)
 print('PASS exact successful 26984 dual ABI RawLens native binaries')

def verify_compiled():
 regress();success=OUT/'26984_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 current=OUT/'26985_REAL_GLSL_SPIRV_COMPILER.txt'
 if 'PASS 26984 C ON 13/13 static shader stages real GLSL/SPIR-V opt/val' not in (OUT/'26984_SUCCESSFUL_CON_REAL_GLSL_SPIRV_COMPILER.txt').read_text():fail('26984 predecessor C ON shader receipt missing')
 if not success.is_file() or 'PASS actual 26974 24/24 C GLES' not in success.read_text() or 'PASS inherited historical 24/24 and actual current 151/151 26984 donor/Iris C shader compilation' not in success.read_text():fail('26984 actual successful shader proof missing')
 if not current.is_file() or 'PASS actual 26974 24/24 C GLES' not in current.read_text() or 'PASS inherited historical 24/24 and actual current {SHADER_COUNT}/{SHADER_COUNT} 26985 donor/Iris C shader compilation'.format(SHADER_COUNT=SHADER_COUNT) not in current.read_text():fail('current Actions 24/24 + 26985 151/151 shader recompilation proof missing')
 con=OUT/'26985_CON_REAL_GLSL_SPIRV_COMPILER.txt'
 if not con.is_file() or 'PASS 26985 C ON 13/13 static shader stages real GLSL/SPIR-V opt/val' not in con.read_text():fail('new C ON real shader compiler proof missing')
 v6=OUT/'26985_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt'
 if not v6.is_file() or f'PASS 26985 physical current {SHADER_COUNT}/{SHADER_COUNT} static donor/Iris C ESSL GLSL + SPIR-V opt/val' not in v6.read_text():fail('current C shader parser and SPIR-V optimizer must actually pass')
 for p,want in NATIVE_SHA.items():
  if sha(R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/'))!=want:fail('staged dual ABI LKR mismatch')
 for p,want in DONOR_SHA.items():
  if sha(R/'app/src/main/jniLibs'/p.removeprefix('lib/'))!=want:fail('original pinned donor sidecar mismatch')
 OUT.mkdir(exist_ok=True)
 (OUT/'26985_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26985_EXPECTED_FULL_APP.sha256').read_bytes())
 if 'PASS 47/47 private Vulkan variants real compile/opt/val' not in (OUT/'26985_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').read_text():fail('missing actual private Vulkan compiler proof')
 print('PASS prebuild source seal + current actual pinned SPIR-V/GLSL + dual ABI native input')

def finalize():
 regress()
 if (OUT/'26985_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26985_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild SHA seal absent')
 log=(OUT/'26985_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for task in tasks:
  if task not in log:fail('not proven actual Gradle task '+task)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one newly assembled Android APK required')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('suspicious APK size')
 with zipfile.ZipFile(R/APKNAME) as apk:
  if apk.testzip() or not {'AndroidManifest.xml','classes.dex'}<=set(apk.namelist()):fail('invalid Android output APK archive')
  for p,want in {**NATIVE_SHA,**DONOR_SHA}.items():
   if hashlib.sha256(apk.read(p)).hexdigest()!=want:fail('assembled APK native binary hash mismatch '+p)
  if not any(x.startswith('lib/arm64-v8a/libiris26972c.so') for x in apk.namelist()):fail('original C native library not linked')
  for abi in ('arm64-v8a','armeabi-v7a'):
   for lib in ('libiris26983conlkr.so','libiris26983conjpeg.so','libiris26985clkr2420.so'):
    if f'lib/{abi}/{lib}' not in apk.namelist():fail('C ON native link missing '+abi+'/'+lib)
   import tempfile
   with tempfile.TemporaryDirectory() as td:
    so=pathlib.Path(td)/'private.so';so.write_bytes(apk.read(f'lib/{abi}/libiris26985clkr2420.so'))
    deps=subprocess.check_output(['readelf','-d',str(so)],text=True)
    if any(lib in deps for lib in ('liblkrpipeline.so','libsrpipeline.so','libneuralnetworks.so')):fail('C native isolation failure '+abi)
    syms=subprocess.check_output(['readelf','-Ws',str(so)],text=True)
    if 'Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativeMerge' not in syms:fail('private JNI missing '+abi)
 exact(R,'26985_EXPECTED_FULL_APP.sha256','actual assembled 26985 source unchanged')
 OUT.mkdir(exist_ok=True)
 (OUT/'26985_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2474 protected, 12 modified, 163 added)\nEXPERIMENT C CONTROLLED DEVICE TRIAL: ENABLED\nEXPERIMENT C PRODUCTION READY: NO\nDEVICE IQ VALIDATION: NOT RUN\n')
 (OUT/'26985_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+p+'\n' for p in tasks))
 (OUT/'26985_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26985-change-aware.yml'
 (OUT/'26985_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26985_incremental.py')+'  build_26985_incremental.py\n')
 (OUT/'26985_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'26985_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for item in ('26985_BASE_26984_FULL_APP.sha256','26985_EXPECTED_FULL_APP.sha256','26985_PROTECTED_SOURCE.sha256','26985_CHANGED_RUNTIME_ALLOWLIST.txt','26985_ADDED_RUNTIME_PATHS.txt','26985_MODIFIED_ORIGINAL_PATHS.txt','26985_DELETED_RUNTIME_PATHS.txt','26985_AUTHORITY_AND_SCOPE.json'):
  shutil.copy2(R/item,OUT/item)
 shutil.copy2(R/'build_26985_incremental.py',OUT/'ACTUAL_EXECUTED_build_26985_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26985-change-aware.yml')
 with (OUT/'26985_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for rel in sorted(parse(R/'26985_EXPECTED_FULL_APP.sha256')):
     path=R/rel;m=t.gettarinfo(str(path),arcname=rel);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with path.open('rb') as opened:t.addfile(m,opened)
 (OUT/'26985_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26985_candidate_app_source.tar.gz')+'  26985_candidate_app_source.tar.gz\n')
 print('PASS real compiled 26985 source/APK SHA proof; IQ not proven until on-device')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','stage-native','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('26985 BUILD ERROR:',e,file=sys.stderr);sys.exit(1)
